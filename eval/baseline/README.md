# Pinned Baseline Fixture (PhotoSorter Phase 1b)

This directory contains the canonical, pinned Phase 1b baseline dataset for the 271-photo (259 unique photos / 1,701 detected faces) test suite.

## Files Included
- `people.json`: Canonical Phase 1b public cluster file (192 people, 1,256 clustered faces, 445 unrecognized faces in 168 photos, 4 no-face photos).
- `config.json`: Canonical event configuration (`{"title": "Event Gallery", "hide_single_photo_default": false, "include_maybe": false}`).
- `id_map.json`: Canonical pre-merge (242) to final (192) cluster ID mapping.
- `suggestions.json`: Canonical maybe-band groups (28 connected maybe groups in the [0.50, 0.65] distance band).
- `edits.json`: Empty baseline edits file (`{"version": 1, "edits": []}`).

## Regeneration from CLI

To regenerate this baseline from source photos using the CLI:

```bash
# 1. Create a clean temporary directory and copy cached embeddings if available
mkdir tmp_baseline.work
cp export.work/*.json tmp_baseline.work/
rm -f tmp_baseline.work/edits.json tmp_baseline.work/suggestions.json tmp_baseline.work/id_map.json
cp -r export.work/crops tmp_baseline.work/
cp -r export.work/thumbs tmp_baseline.work/

# 2. Run PhotoSorter Engine CLI with no live organizer edits
python -m backend.engine --input test_photos --out tmp_baseline --cache-dir tmp_baseline.work

# 3. Copy canonical baseline artifacts into eval/baseline/
cp tmp_baseline/people.json eval/baseline/people.json
cp tmp_baseline/config.json eval/baseline/config.json
cp tmp_baseline.work/id_map.json eval/baseline/id_map.json
cp tmp_baseline.work/suggestions.json eval/baseline/suggestions.json
echo '{"version": 1, "edits": []}' > eval/baseline/edits.json

# 4. Clean up temporary directory
rm -rf tmp_baseline tmp_baseline.work
```

## Clean Checkout Regeneration (Embeddings Cache)

On a fresh, clean checkout without `export.work/`:
1. Ensure `test_photos/` exists.
2. Run `python -m backend.engine --input test_photos --out tmp_baseline`.
3. The engine will download `buffalo_l` models (if not already cached under `~/.insightface/models/buffalo_l`) and compute all 259 photo embeddings and face crops from scratch using InsightFace.
4. Output will be generated into `tmp_baseline/` and `tmp_baseline.work/`.
