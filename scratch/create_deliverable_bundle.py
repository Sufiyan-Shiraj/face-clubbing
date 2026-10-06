import zipfile
from pathlib import Path

def create_bundle():
    zip_path = Path("fixup_round_deliverable_bundle.zip")
    if zip_path.exists():
        zip_path.unlink()

    files_to_include = [
        ("REPORT.md", "REPORT.md"),
        ("suggestions.json", "suggestions.json"),
        ("export/people.json", "export/people.json"),
        ("export/config.json", "export/config.json"),
        ("id_map.json", "id_map.json"),
        ("scratch/verify_final.py", "scratch/verify_final.py"),
        ("scratch/generate_section_12_4.py", "scratch/generate_section_12_4.py"),
        ("scratch/generate_new_sheets.py", "scratch/generate_new_sheets.py"),
        ("report_assets_v4/contact_sheet_split_pairs_reconciliation.jpg", "report_assets_v4/contact_sheet_split_pairs_reconciliation.jpg"),
        ("report_assets_v4/contact_sheet_collision_audit.jpg", "report_assets_v4/contact_sheet_collision_audit.jpg"),
        ("report_assets_v4/contact_sheet_maybe_bin_0.58_0.60.jpg", "report_assets_v4/contact_sheet_maybe_bin_0.58_0.60.jpg"),
        ("report_assets_v4/contact_sheet_merge_bins_v4.jpg", "report_assets_v4/contact_sheet_merge_bins_v4.jpg"),
        ("report_assets_v4/contact_sheet_top10_worst_fitting.jpg", "report_assets_v4/contact_sheet_top10_worst_fitting.jpg"),
        ("report_assets_v4/contact_sheet_enlarged_old_pairs.jpg", "report_assets_v4/contact_sheet_enlarged_old_pairs.jpg"),
    ]

    print(f"Creating bundle: {zip_path}")
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for src_path_str, arcname in files_to_include:
            p = Path(src_path_str)
            if p.exists():
                zf.write(p, arcname)
                print(f"  Added: {arcname} ({p.stat().st_size:,} bytes)")
            else:
                print(f"  WARNING: File missing: {src_path_str}")

    print(f"\nBundle created successfully: {zip_path.stat().st_size:,} bytes")
    return zip_path

if __name__ == "__main__":
    create_bundle()
