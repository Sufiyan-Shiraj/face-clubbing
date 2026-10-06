import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json

sug = json.load(open('export/.cache/suggestions.json'))
people_data = json.load(open('export/people.json'))
people_by_id = {p['id']: p for p in people_data['people']}

all_links = []
for g in sug['maybe_groups']:
    all_links.extend(g['links'])

print(f"Total links: {len(all_links)}")

bins = {
    '0.50-0.52': [],
    '0.52-0.55': [],
    '0.55-0.58': [],
    '0.58-0.60': [],
}

for link in all_links:
    d = link['distance']
    if 0.50 <= d < 0.52:
        bins['0.50-0.52'].append(link)
    elif 0.52 <= d < 0.55:
        bins['0.52-0.55'].append(link)
    elif 0.55 <= d < 0.58:
        bins['0.55-0.58'].append(link)
    elif 0.58 <= d <= 0.60:
        bins['0.58-0.60'].append(link)
    else:
        print("Out of range:", link)

for bname, blinks in bins.items():
    print(f"Bin {bname}: {len(blinks)} links")

print("\nLinks in 0.58-0.60:")
for l in bins['0.58-0.60']:
    ca = l['cluster_a']
    cb = l['cluster_b']
    pa = people_by_id[ca]
    pb = people_by_id[cb]
    print(f"  {ca} ({len(pa['photos'])} photos, {len(pa['faces'])} faces) <-> {cb} ({len(pb['photos'])} photos, {len(pb['faces'])} faces) | dist: {l['distance']:.4f}")
    # Show faces and filenames for both sides
    fa_info = [(f['face_id'], f['file_name']) for f in pa['faces']]
    fb_info = [(f['face_id'], f['file_name']) for f in pb['faces']]
    print(f"    Side A ({ca}): {fa_info}")
    print(f"    Side B ({cb}): {fb_info}")
