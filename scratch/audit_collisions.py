import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
from collections import defaultdict
from backend.engine.cache import EmbeddingCache
import numpy as np

data = json.load(open('export/people.json'))
cache = EmbeddingCache('export/.cache')
records = cache.load_all()

target_clusters = ['p014', 'p041', 'p062']
for p in data['people']:
    if p['id'] in target_clusters:
        cid = p['id']
        photos_count = len(p['photos'])
        faces_count = len(p['faces'])
        print(f"=== Cluster {cid} (photos: {photos_count}, faces: {faces_count}) ===")
        by_photo = defaultdict(list)
        for f in p['faces']:
            by_photo[f['photo_id']].append(f)
        for pid, flist in by_photo.items():
            if len(flist) > 1:
                fname = flist[0]['file_name']
                print(f"  Photo {pid} ({fname}): {len(flist)} faces")
                for f in flist:
                    print(f"    Face ID: {f['face_id']}, bbox: {[round(x, 1) for x in f['bbox']]}, score: {f['det_score']:.4f}")
                for i in range(len(flist)):
                    for j in range(i+1, len(flist)):
                        f1 = next(cf for cf in records[pid].faces if cf.face_id == flist[i]['face_id'])
                        f2 = next(cf for cf in records[pid].faces if cf.face_id == flist[j]['face_id'])
                        d = float(1.0 - np.dot(f1.embedding, f2.embedding))
                        print(f"    Distance between {flist[i]['face_id']} and {flist[j]['face_id']}: {d:.4f}")
