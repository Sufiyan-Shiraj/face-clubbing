"""Test ensuring that eval and test routines do not modify export/ or export.work/."""

import hashlib
import os
from pathlib import Path

from eval.verify_api import run_live_export_verification

REPO_ROOT = Path(__file__).resolve().parent.parent


def _compute_tree_hash(dir_path: Path) -> dict[str, str]:
    if not dir_path.exists():
        return {}
    hashes = {}
    for p in dir_path.rglob("*"):
        if p.is_file():
            rel = p.relative_to(dir_path).as_posix()
            h = hashlib.sha256(p.read_bytes()).hexdigest()
            hashes[rel] = h
    return hashes


def test_checks_do_not_modify_export_or_work():
    export_dir = REPO_ROOT / "export"
    work_dir = REPO_ROOT / "export.work"

    before_export = _compute_tree_hash(export_dir)
    before_work = _compute_tree_hash(work_dir)

    # 1. Run verify_api export mode against isolated baseline
    api_ok = run_live_export_verification()
    assert api_ok is True, "verify_api export mode failed"

    # 2. Run verify_export against baseline if not already inside a verify_export sub-run
    if not os.environ.get("IN_VERIFY_EXPORT"):
        from eval.verify_export import run_verification

        export_ok = run_verification(export_dir="eval/baseline", work_dir="eval/baseline")
        assert export_ok is True, "verify_export failed"

    after_export = _compute_tree_hash(export_dir)
    after_work = _compute_tree_hash(work_dir)

    # Check for additions, deletions, or modifications
    assert before_export == after_export, (
        f"export/ was modified during checks! Diff: "
        f"added={set(after_export) - set(before_export)}, "
        f"removed={set(before_export) - set(after_export)}, "
        f"changed={[k for k in before_export if before_export[k] != after_export.get(k)]}"
    )

    assert before_work == after_work, (
        f"export.work/ was modified during checks! Diff: "
        f"added={set(after_work) - set(before_work)}, "
        f"removed={set(before_work) - set(after_work)}, "
        f"changed={[k for k in before_work if before_work[k] != after_work.get(k)]}"
    )
