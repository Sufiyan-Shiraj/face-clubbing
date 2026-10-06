import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.engine.cache import EmbeddingCache
from backend.engine.clusterer import FaceClusterer
import json

cache = EmbeddingCache("export/.cache")
records = cache.load_all()
cl = FaceClusterer(second_pass_merge=True)
people, _ = cl.cluster(records)
exp_data = json.load(open("export/people.json"))
exp_people = exp_data["people"]

mismatches = 0
for i in range(len(people)):
    p1 = people[i]
    p2 = exp_people[i]
    if set(p1.photo_ids) != set(p2["photo_ids"]):
        mismatches += 1
        print(f"Mismatch at index {i}: cl={p1.id} (len {len(p1.photo_ids)}) vs exp={p2['id']} (len {len(p2['photo_ids'])})")
        for j, p2_other in enumerate(exp_people):
            if set(p1.photo_ids) == set(p2_other["photo_ids"]):
                print(f"  cl index {i} matches exp index {j} ({p2_other['id']})")
                break
        if mismatches > 5:
            break
if mismatches == 0:
    print("ALL 189 CLUSTERS MATCH EXACTLY!")
