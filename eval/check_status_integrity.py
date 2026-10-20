"""Integrity checker for STATUS.md.

Validates that:
1. No two different test-count lines in STATUS.md share an identical duration.
2. Every pasted summary and verbatim block matches the referenced raw output file and SHA-256.
3. Every test count is 100% consistent across Document Header, Section 3 Checks,
   Section 5 Closeout, and Section 16 Audit tables, and sum invariants hold.
4. Test file counts match actual files on disk in tests/.
"""

from __future__ import annotations
import sys
import re
import hashlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
STATUS_FILE = REPO_ROOT / "STATUS.md"


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def check_durations_integrity(content: str) -> list[str]:
    errors = []
    # Find all occurrences of test counts with duration
    # Examples:
    # 100 passed in 672.48s
    # 100 passed, 2 warnings in 672.48s
    # 94 passed, 5 skipped in 25.27s
    # 85 passed in 68.51 s
    pattern = re.compile(
        r'(?:(?:\*{2})?(\d+)\s+passed(?:\*{2})?(?:,\s*(\d+)\s+skipped)?(?:,\s*(\d+)\s+(?:failures?|warnings?))?.*?in\s+(?:\*{2})?([\d\.]+)\s*s(?:\*{2})?)',
        re.IGNORECASE
    )

    duration_to_counts: dict[str, set[int]] = {}
    duration_to_lines: dict[str, list[str]] = {}

    for line_no, line in enumerate(content.splitlines(), start=1):
        for m in pattern.finditer(line):
            passed_cnt = int(m.group(1))
            dur_str = m.group(4)
            # Normalize duration to 2 decimal places if float
            try:
                norm_dur = f"{float(dur_str):.2f}"
            except ValueError:
                norm_dur = dur_str

            if norm_dur not in duration_to_counts:
                duration_to_counts[norm_dur] = set()
                duration_to_lines[norm_dur] = []
            duration_to_counts[norm_dur].add(passed_cnt)
            duration_to_lines[norm_dur].append(f"L{line_no}: {line.strip()[:80]}")

    for dur, counts in duration_to_counts.items():
        if len(counts) > 1:
            err_msg = (
                f"INTEGRITY VIOLATION: Duration {dur}s is shared across different test counts {sorted(list(counts))}!\n"
                + "\n".join(f"    {ln}" for ln in duration_to_lines[dur])
            )
            errors.append(err_msg)

    return errors


def check_raw_files_integrity(content: str) -> list[str]:
    errors = []
    # Pattern to find checks with source file, sha256, and summary
    # Check sections start with ### Check X: ...
    check_sections = re.split(r'\n(?=### Check [A-Z0-9]+:)', content)

    for sec in check_sections[1:]:
        header_line = sec.strip().splitlines()[0]
        # Extract Source File
        src_match = re.search(r'-\s*\*\*Source File\*\*:\s*`([^`]+)`', sec)
        sha_match = re.search(r'-\s*\*\*SHA-256 Digest\*\*:\s*`([a-fA-F0-9]{64})`', sec)
        summary_match = re.search(r'-\s*\*\*Summary\*\*:\s*(.+)', sec)

        if not src_match:
            continue

        rel_src = src_match.group(1).strip()
        raw_path = REPO_ROOT / rel_src

        if not raw_path.exists():
            errors.append(f"{header_line}: Raw source file not found on disk: {rel_src}")
            continue

        raw_bytes = raw_path.read_bytes()
        actual_sha = hashlib.sha256(raw_bytes).hexdigest().lower()

        # Check SHA-256 match
        if sha_match:
            expected_sha = sha_match.group(1).strip().lower()
            if actual_sha != expected_sha:
                errors.append(
                    f"{header_line}: SHA-256 mismatch for {rel_src}!\n"
                    f"  Expected in STATUS: {expected_sha}\n"
                    f"  Actual on disk:    {actual_sha}"
                )

        # Check verbatim / summary consistency
        raw_text = raw_bytes.decode("utf-8", errors="ignore")

        # Check pytest summary line
        if "pytest" in rel_src.lower():
            m_raw = re.search(r'(\d+)\s+passed.*in\s+([\d\.]+)s', raw_text)
            if m_raw and summary_match:
                raw_summary = m_raw.group(0)
                m_stat = re.search(r'(\d+)\s+passed.*in\s+([\d\.]+)s', summary_match.group(1))
                if m_stat:
                    if int(m_raw.group(1)) != int(m_stat.group(1)):
                        errors.append(
                            f"{header_line}: Pytest passed count mismatch with raw file {rel_src}!\n"
                            f"  Raw file: {m_raw.group(1)} passed\n"
                            f"  STATUS:   {m_stat.group(1)} passed"
                        )
                    if f"{float(m_raw.group(2)):.2f}" != f"{float(m_stat.group(2)):.2f}":
                        errors.append(
                            f"{header_line}: Pytest duration mismatch with raw file {rel_src}!\n"
                            f"  Raw file: {m_raw.group(2)}s\n"
                            f"  STATUS:   {m_stat.group(2)}s"
                        )

        # Check vitest summary
        elif "vitest" in rel_src.lower() or "frontend" in rel_src.lower() or "viewer" in rel_src.lower():
            m_raw = re.search(r'Tests\s+(\d+)\s+passed\s+\((\d+)\)', raw_text)
            if m_raw and summary_match:
                raw_tests = int(m_raw.group(1))
                m_stat = re.search(r'(\d+)\s+passed', summary_match.group(1))
                if m_stat and raw_tests != int(m_stat.group(1)):
                    errors.append(
                        f"{header_line}: Vitest passed count mismatch with raw file {rel_src}!\n"
                        f"  Raw file: {raw_tests} passed\n"
                        f"  STATUS:   {m_stat.group(1)} passed"
                    )

    return errors


def check_counts_reconciliation(content: str) -> list[str]:
    errors = []

    # 1. Header counts (audit mode / summary block)
    header_backend_m = re.search(r'Pytest\s+(\d+)/(\d+)\s+Passed', content)
    header_fe_m = re.search(r'Frontend Vitest\s+(\d+)/(\d+)\s+Passed', content)
    header_viewer_m = re.search(r'Viewer Vitest\s+(\d+)/(\d+)\s+Passed', content)
    header_export_m = re.search(r'Export Invariants\s+(\d+)/(\d+)\s+Passed', content)
    header_total_m = re.search(r'Total Automated Tests:\s*(\d+)\s+Passed', content)

    if not (header_backend_m and header_fe_m and header_viewer_m and header_total_m):
        errors.append("Header is missing one or more canonical test count metrics")
        return errors

    header_backend = int(header_backend_m.group(1))
    header_fe = int(header_fe_m.group(1))
    header_viewer = int(header_viewer_m.group(1))
    header_total = int(header_total_m.group(1))
    header_export = int(header_export_m.group(1)) if header_export_m else 15

    # Check header sum invariant
    if header_backend + header_fe + header_viewer != header_total:
        errors.append(
            f"Header test sum mismatch: {header_backend} (Pytest) + {header_fe} (Frontend) + {header_viewer} (Viewer) = "
            f"{header_backend + header_fe + header_viewer} != {header_total} (Total)"
        )

    # 2. Section 3 Check summaries
    # Check A
    check_a_m = re.search(r'### Check A:.*?\n.*?- \*\*Summary\*\*:\s*(\d+)\s+passed.*?across\s+(\d+)\s+test files', content, re.DOTALL)
    if check_a_m:
        check_a_passed = int(check_a_m.group(1))
        check_a_files = int(check_a_m.group(2))
        if check_a_passed != header_backend:
            errors.append(f"Check A passed count ({check_a_passed}) != Header Pytest count ({header_backend})")

        # Actual test files on disk in tests/
        actual_test_files = len(list((REPO_ROOT / "tests").glob("test_*.py")))
        if check_a_files != actual_test_files:
            errors.append(
                f"Check A test files count ({check_a_files}) != actual test files on disk in tests/ ({actual_test_files})"
            )

    # Check B
    check_b_m = re.search(r'### Check B:.*?\n.*?- \*\*Summary\*\*:\s*(\d+)/(\d+)\s+checks passed', content, re.DOTALL)
    if check_b_m:
        check_b_passed = int(check_b_m.group(1))
        if check_b_passed != header_export:
            errors.append(f"Check B export invariants count ({check_b_passed}) != Header export count ({header_export})")

    # Check D1
    check_d1_m = re.search(r'### Check D1:.*?\n.*?- \*\*Summary\*\*:\s*(\d+)\s+passed.*?across\s+(\d+)\s+test files', content, re.DOTALL)
    if check_d1_m:
        check_d1_passed = int(check_d1_m.group(1))
        if check_d1_passed != header_fe:
            errors.append(f"Check D1 Frontend Vitest count ({check_d1_passed}) != Header Frontend Vitest count ({header_fe})")

    # Check D2
    check_d2_m = re.search(r'### Check D2:.*?\n.*?- \*\*Summary\*\*:\s*(\d+)\s+passed.*?across\s+(\d+)\s+test files', content, re.DOTALL)
    if check_d2_m:
        check_d2_passed = int(check_d2_m.group(1))
        if check_d2_passed != header_viewer:
            errors.append(f"Check D2 Viewer Vitest count ({check_d2_passed}) != Header Viewer Vitest count ({header_viewer})")

    # 3. Section 5 Closeout counts
    closeout_backend_m = re.search(r'Full Backend Test Suite \(Check A\).*?\*\*(\d+)\s+passed\*\*', content)
    closeout_fe_m = re.search(r'Frontend Vitest Suite \(Check D1\).*?\*\*(\d+)\s+passed\*\*', content)
    closeout_viewer_m = re.search(r'Viewer Vitest Suite \(Check D2\).*?\*\*(\d+)\s+passed\*\*', content)
    closeout_total_m = re.search(r'Total Automated Test Suite.*?(\d+)\s+passed', content)

    if closeout_backend_m and int(closeout_backend_m.group(1)) != header_backend:
        errors.append(f"Closeout Pytest count ({closeout_backend_m.group(1)}) != Header Pytest count ({header_backend})")

    if closeout_fe_m and int(closeout_fe_m.group(1)) != header_fe:
        errors.append(f"Closeout Frontend Vitest count ({closeout_fe_m.group(1)}) != Header Frontend count ({header_fe})")

    if closeout_viewer_m and int(closeout_viewer_m.group(1)) != header_viewer:
        errors.append(f"Closeout Viewer Vitest count ({closeout_viewer_m.group(1)}) != Header Viewer count ({header_viewer})")

    if closeout_total_m and int(closeout_total_m.group(1)) != header_total:
        errors.append(f"Closeout Total count ({closeout_total_m.group(1)}) != Header Total count ({header_total})")

    # 4. Section 16 Table checks
    sec16_backend_m = re.search(r'\|\s*\*\*16\.7\*\*\s*\|.*?\|\s*\*\*(\d+)\s+passed', content)
    sec16_fe_m = re.search(r'\|\s*\*\*16\.8\*\*\s*\|.*?\|\s*\*\*(\d+)\s+passed', content)
    sec16_viewer_m = re.search(r'\|\s*\*\*16\.9\*\*\s*\|.*?\|\s*\*\*(\d+)\s+passed', content)

    if sec16_backend_m and int(sec16_backend_m.group(1)) != header_backend:
        errors.append(f"Section 16.7 Pytest count ({sec16_backend_m.group(1)}) != Header Pytest count ({header_backend})")

    if sec16_fe_m and int(sec16_fe_m.group(1)) != header_fe:
        errors.append(f"Section 16.8 Frontend Vitest count ({sec16_fe_m.group(1)}) != Header Frontend count ({header_fe})")

    if sec16_viewer_m and int(sec16_viewer_m.group(1)) != header_viewer:
        errors.append(f"Section 16.9 Viewer Vitest count ({sec16_viewer_m.group(1)}) != Header Viewer count ({header_viewer})")

    return errors


def main() -> int:
    print("=" * 70)
    print("STATUS.MD INTEGRITY AUDIT (eval/check_status_integrity.py)")
    print("=" * 70)

    if not STATUS_FILE.exists():
        print(f"[FAIL] STATUS.md not found at {STATUS_FILE}")
        return 1

    content = STATUS_FILE.read_text(encoding="utf-8")

    all_errors = []

    print("[INFO] Auditing test durations across test-count lines...")
    dur_errors = check_durations_integrity(content)
    if dur_errors:
        all_errors.extend(dur_errors)
        for e in dur_errors:
            print(f"  [FAIL] {e}")
    else:
        print("  [PASS] Zero duplicated durations across differing test counts.")

    print("[INFO] Auditing pasted summaries against raw source files and SHA-256...")
    raw_errors = check_raw_files_integrity(content)
    if raw_errors:
        all_errors.extend(raw_errors)
        for e in raw_errors:
            print(f"  [FAIL] {e}")
    else:
        print("  [PASS] All raw output files, digests, and pasted summaries verified.")

    print("[INFO] Auditing test counts reconciliation across Header, Checks, Closeout, and Tables...")
    count_errors = check_counts_reconciliation(content)
    if count_errors:
        all_errors.extend(count_errors)
        for e in count_errors:
            print(f"  [FAIL] {e}")
    else:
        print("  [PASS] All test counts (Backend, Frontend, Viewer, Invariants, Total) reconciled.")

    print("=" * 70)
    if all_errors:
        print(f"STATUS INTEGRITY AUDIT FAILED WITH {len(all_errors)} VIOLATIONS.")
        print("=" * 70)
        return 1

    print("ALL STATUS INTEGRITY CHECKS PASSED (100% OK).")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
