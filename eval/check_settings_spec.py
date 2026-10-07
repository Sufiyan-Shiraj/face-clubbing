#!/usr/bin/env python3
"""
Verify that the Settings slider defaults and backend models map exactly to SPEC 6.2 defaults.
Checks:
1. backend.api.models.SettingsModel default values
2. backend.engine.pipeline.EngineConfig default values
3. frontend/src/components/SettingsScreen.tsx initial React state defaults
"""

import sys
import re
from pathlib import Path

# SPEC 6.2 Reference Ground Truth Defaults
SPEC_DEFAULTS = {
    "distance_threshold": 0.50,
    "min_det_score": 0.50,
    "min_face_size": 64,
    "max_yaw": 70.0,
    "seed_min_det_score": 0.70,
    "seed_min_face_size": 64,
    "seed_max_yaw": 60.0,
    "attach_distance_cap": 0.45,
    "second_pass_merge": True,
    "merge_threshold": 0.50,
    "maybe_threshold": 0.65,
    "same_photo_merge_max": 0.40,
    "flip_average": False,
    "thumb_size": 400,
    "face_crop_size": 256,
}

def verify_spec_defaults():
    repo_root = Path(__file__).resolve().parent.parent
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    all_ok = True

    print("=" * 80)
    print("VERIFYING CLUSTERING SETTINGS SLIDER DEFAULTS AGAINST SPEC 6.2")
    print("=" * 80)

    # 1. Check SettingsModel (backend/api/models.py)
    try:
        from backend.api.models import SettingsModel
        model_instance = SettingsModel()
        print("\n[CHECK 1] backend.api.models.SettingsModel Defaults:")
        for key, expected in SPEC_DEFAULTS.items():
            actual = getattr(model_instance, key, None)
            if actual == expected:
                print(f"  [PASS] {key}: {actual} == {expected}")
            else:
                print(f"  [FAIL] {key}: actual={actual} != expected={expected}")
                all_ok = False
    except Exception as e:
        print(f"  [ERROR] Failed to import/inspect SettingsModel: {e}")
        all_ok = False

    # 2. Check EngineConfig (backend/engine/pipeline.py)
    try:
        from backend.engine.pipeline import EngineConfig
        config_instance = EngineConfig(input_path="dummy")
        print("\n[CHECK 2] backend.engine.pipeline.EngineConfig Defaults:")
        for key, expected in SPEC_DEFAULTS.items():
            actual = getattr(config_instance, key, None)
            if actual == expected:
                print(f"  [PASS] {key}: {actual} == {expected}")
            else:
                print(f"  [FAIL] {key}: actual={actual} != expected={expected}")
                all_ok = False
    except Exception as e:
        print(f"  [ERROR] Failed to import/inspect EngineConfig: {e}")
        all_ok = False

    # 3. Check SettingsScreen.tsx (frontend/src/components/SettingsScreen.tsx)
    settings_tsx = repo_root / "frontend" / "src" / "components" / "SettingsScreen.tsx"
    print("\n[CHECK 3] frontend/src/components/SettingsScreen.tsx React State Defaults:")
    if not settings_tsx.exists():
        print(f"  [FAIL] File not found: {settings_tsx}")
        all_ok = False
    else:
        text = settings_tsx.read_text(encoding="utf-8")
        # Extract initial state dictionary
        for key, expected in SPEC_DEFAULTS.items():
            if isinstance(expected, bool):
                val_str = "true" if expected else "false"
                pattern = rf"{key}\s*:\s*{val_str}"
            elif isinstance(expected, float):
                # e.g. 0.5 or 0.50 or 70 / 70.0
                int_part = int(expected) if expected == int(expected) else None
                if int_part is not None:
                    pattern = rf"{key}\s*:\s*{expected:.2f}|{key}\s*:\s*{expected}|{key}\s*:\s*{int_part}\b"
                else:
                    pattern = rf"{key}\s*:\s*{expected:.2f}|{key}\s*:\s*{expected}"
            else:
                pattern = rf"{key}\s*:\s*{expected}"
            
            if re.search(pattern, text):
                print(f"  [PASS] {key} defaults to {expected}")
            else:
                print(f"  [FAIL] {key} not found matching default {expected}")
                all_ok = False

    print("\n" + "=" * 80)
    if all_ok:
        print("ALL SETTINGS SLIDER AND ENGINE CONFIG DEFAULTS MATCH SPEC 6.2 (100% OK)")
    else:
        print("FAILURES DETECTED IN SETTINGS DEFAULTS")
    print("=" * 80)
    return all_ok

if __name__ == "__main__":
    success = verify_spec_defaults()
    sys.exit(0 if success else 1)
