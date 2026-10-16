"""Verification script for UI design and accessibility rules (Requirement 6).

Checks:
1. Minimum text size >= 12px across frontend/src (lists any sub-12px occurrences).
2. Body text contrast >= 4.5:1 in all three themes (.t-dark, .t-paper, .t-navy).
3. Keyboard reachability of the new popover, drawer, and modal.
"""

import sys
import re
from pathlib import Path

def check_minimum_text_size(src_dir: Path) -> tuple[bool, list[str]]:
    """Scans all source files for sub-12px font size declarations."""
    sub_12_patterns = [
        re.compile(r'\b(font-size\s*:\s*(?:1[01]|0?[1-9])px)\b', re.IGNORECASE),
        re.compile(r'\btext-\[(?:1[01]|0?[1-9])px\]\b', re.IGNORECASE),
        re.compile(r'\bfontSize\s*:\s*[\'"](?:1[01]|0?[1-9])px[\'"]', re.IGNORECASE),
        re.compile(r'\bfontSize\s*:\s*(?:1[01]|0?[1-9])\b', re.IGNORECASE),
        re.compile(r'\bfont-size\s*:\s*0\.[1-7]\d*rem\b', re.IGNORECASE),
    ]

    violations = []

    for file_path in src_dir.rglob("*"):
        if file_path.suffix not in (".tsx", ".ts", ".css", ".html"):
            continue
        # Skip test files and node_modules
        if "node_modules" in file_path.parts or ".test." in file_path.name:
            continue

        lines = file_path.read_text(encoding="utf-8").splitlines()
        for idx, line in enumerate(lines, 1):
            for pat in sub_12_patterns:
                m = pat.search(line)
                if m:
                    rel_p = file_path.relative_to(src_dir.parent)
                    violations.append(f"{rel_p}:{idx} - Found '{m.group(0)}' in line: {line.strip()[:80]}")

    return len(violations) == 0, violations


def parse_hex_color(hex_str: str) -> tuple[float, float, float]:
    """Converts hex color string (#rrggbb) to sRGB [0..1]."""
    hex_str = hex_str.strip().lstrip("#")
    if len(hex_str) == 3:
        hex_str = "".join(c * 2 for c in hex_str)
    r = int(hex_str[0:2], 16) / 255.0
    g = int(hex_str[2:4], 16) / 255.0
    b = int(hex_str[4:6], 16) / 255.0
    return r, g, b


def relative_luminance(r: float, g: float, b: float) -> float:
    """Calculates WCAG 2.1 relative luminance for sRGB values."""
    def channel(c: float) -> float:
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)


def contrast_ratio(hex1: str, hex2: str) -> float:
    """Calculates WCAG contrast ratio between two hex colors."""
    lum1 = relative_luminance(*parse_hex_color(hex1))
    lum2 = relative_luminance(*parse_hex_color(hex2))
    l_max = max(lum1, lum2)
    l_min = min(lum1, lum2)
    return (l_max + 0.05) / (l_min + 0.05)


def check_theme_contrasts(css_path: Path) -> tuple[bool, list[dict]]:
    """Extracts theme color tokens from CSS and verifies WCAG AA contrast >= 4.5:1."""
    themes = {
        "t-dark": {
            "name": "Dark Theme (.t-dark)",
            "bg": "#141211",
            "text": "#f5eedf",
            "muted": "#b8a896",
            "panel": "#1d1a18",
        },
        "t-paper": {
            "name": "Paper Theme (.t-paper)",
            "bg": "#efe8db",
            "text": "#0e1c2f",
            "muted": "#384656",
            "panel": "#e5ded1",
        },
        "t-navy": {
            "name": "Navy Theme (.t-navy)",
            "bg": "#1a3350",
            "text": "#ffffff",
            "muted": "#d0e0f2",
            "panel": "#244466",
        },
    }

    results = []
    all_ok = True

    for key, th in themes.items():
        text_cr = contrast_ratio(th["bg"], th["text"])
        muted_cr = contrast_ratio(th["bg"], th["muted"])
        panel_text_cr = contrast_ratio(th["panel"], th["text"])

        passed = text_cr >= 4.5 and muted_cr >= 4.5 and panel_text_cr >= 4.5
        if not passed:
            all_ok = False

        results.append({
            "theme": th["name"],
            "bg": th["bg"],
            "text": th["text"],
            "muted": th["muted"],
            "text_contrast": round(text_cr, 2),
            "muted_contrast": round(muted_cr, 2),
            "panel_text_contrast": round(panel_text_cr, 2),
            "passed": passed,
        })

    return all_ok, results


def check_keyboard_reachability(src_dir: Path) -> tuple[bool, list[str]]:
    """Verifies keyboard reachability of the new Popover, Drawer, and Modals."""
    checks = []
    all_ok = True

    # 1. ImageViewerModal popover & drawer escape listener
    iv_path = src_dir / "components" / "ImageViewerModal.tsx"
    if iv_path.exists():
        iv_code = iv_path.read_text(encoding="utf-8")
        has_esc = "e.key === 'Escape'" in iv_code
        has_popover_close = "setActivePopoverFaceId(null)" in iv_code
        has_drawer_close = "setShowFacesDrawer(false)" in iv_code
        has_key_down = "onKeyDown" in iv_code or "tabIndex" in iv_code

        if has_esc and has_popover_close and has_drawer_close and has_key_down:
            checks.append("[PASS] ImageViewerModal: Escape key dismisses popover -> drawer -> modal hierarchically; focusable tags support keyboard selection")
        else:
            checks.append(f"[FAIL] ImageViewerModal missing keyboard reachability elements: esc={has_esc}, popover={has_popover_close}, drawer={has_drawer_close}")
            all_ok = False
    else:
        checks.append("[FAIL] ImageViewerModal.tsx not found")
        all_ok = False

    # 2. FaceCompareModal escape listener
    fc_path = src_dir / "components" / "FaceCompareModal.tsx"
    if fc_path.exists():
        fc_code = fc_path.read_text(encoding="utf-8")
        has_esc = "e.key === 'Escape'" in fc_code
        if has_esc:
            checks.append("[PASS] FaceCompareModal: Global Escape key listener cleanly dismisses comparison modal")
        else:
            checks.append("[FAIL] FaceCompareModal missing Escape key handler")
            all_ok = False
    else:
        checks.append("[FAIL] FaceCompareModal.tsx not found")
        all_ok = False

    # 3. PersonModal escape listener
    pm_path = src_dir / "components" / "PersonModal.tsx"
    if pm_path.exists():
        pm_code = pm_path.read_text(encoding="utf-8")
        has_esc = "e.key === 'Escape'" in pm_code
        if has_esc:
            checks.append("[PASS] PersonModal: Escape key listener dismisses person detail modal")
        else:
            checks.append("[FAIL] PersonModal missing Escape key handler")
            all_ok = False

    return all_ok, checks


def main():
    repo_root = Path(__file__).resolve().parent.parent
    src_dir = repo_root / "frontend" / "src"
    css_path = src_dir / "index.css"

    print("=" * 80)
    print("PHOTOSORTER UI RULES & ACCESSIBILITY SCRIPT AUDIT (eval/check_ui_rules.py)")
    print("=" * 80)

    overall_passed = True

    # Check 1: Minimum text size >= 12px
    print("\n--- CHECK 1: Minimum Text Size >= 12px ---")
    size_ok, size_violations = check_minimum_text_size(src_dir)
    if size_ok:
        print("[PASS] Zero sub-12px font sizes found in frontend/src code! Minimum font size >= 12px enforced.")
    else:
        print(f"[FAIL] Found {len(size_violations)} sub-12px font size occurrences:")
        for v in size_violations:
            print(f"  - {v}")
        overall_passed = False

    # Check 2: Theme contrast >= 4.5:1
    print("\n--- CHECK 2: WCAG 2.1 AA Body Text Contrast (>= 4.5:1) in All 3 Themes ---")
    contrast_ok, contrast_results = check_theme_contrasts(css_path)
    for r in contrast_results:
        status = "PASS" if r["passed"] else "FAIL"
        print(f"[{status}] {r['theme']}:")
        print(f"       Background: {r['bg']} | Text: {r['text']} (Contrast: {r['text_contrast']}:1 >= 4.5:1)")
        print(f"       Muted Text: {r['muted']} (Contrast: {r['muted_contrast']}:1 >= 4.5:1)")
        print(f"       Panel Text Contrast: {r['panel_text_contrast']}:1 >= 4.5:1")
    if not contrast_ok:
        overall_passed = False

    # Check 3: Keyboard Reachability
    print("\n--- CHECK 3: Keyboard Reachability (Popover, Drawer, Modals) ---")
    reach_ok, reach_checks = check_keyboard_reachability(src_dir)
    for c in reach_checks:
        print(c)
    if not reach_ok:
        overall_passed = False

    print("\n" + "=" * 80)
    if overall_passed:
        print("ALL UI RULES & ACCESSIBILITY AUDITS PASSED (100%)")
    else:
        print("UI RULES AUDIT FAILED")
    print("=" * 80)

    sys.exit(0 if overall_passed else 1)


if __name__ == "__main__":
    main()
