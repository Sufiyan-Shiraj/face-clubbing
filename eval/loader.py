from pathlib import Path
from typing import Dict, List, Tuple, Set, Optional
import json

class GroundTruth:
    def __init__(self, sets: Dict[str, List[str]], different: List[List[str]], unconfirmed: Optional[List[str]] = None):
        self.sets: Dict[str, List[str]] = sets
        self.different: List[Tuple[str, str]] = [tuple(p) for p in different]
        self.unconfirmed: Set[str] = set(unconfirmed or [])

    def get_true_pairs(self, exclude_unconfirmed: bool = False) -> List[Tuple[str, str, str]]:
        """
        Returns list of (set_name, face_id_1, face_id_2) pairs for all combinations in sets.
        If exclude_unconfirmed is True, excludes any pair involving an unconfirmed face ID.
        """
        pairs = []
        for s_name, f_list in self.sets.items():
            n = len(f_list)
            for i in range(n):
                for j in range(i + 1, n):
                    f1 = f_list[i]
                    f2 = f_list[j]
                    if exclude_unconfirmed and (f1 in self.unconfirmed or f2 in self.unconfirmed):
                        continue
                    pairs.append((s_name, f1, f2))
        return pairs

    def get_different_pairs(self) -> List[Tuple[str, str]]:
        """Returns listed negative pairs from 'different'."""
        return list(self.different)

def load_ground_truth(path: Optional[str] = None) -> GroundTruth:
    if path is None:
        p = Path(__file__).parent / "ground_truth.json"
    else:
        p = Path(path)
    
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)

    return GroundTruth(
        sets=data.get("sets", {}),
        different=data.get("different", []),
        unconfirmed=data.get("unconfirmed", [])
    )
