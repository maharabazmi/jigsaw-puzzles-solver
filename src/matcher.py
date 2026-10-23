import numpy as np
from typing import Dict, List, Any, Optional, Tuple

def match_edge_profiles(prof_a: np.ndarray, type_a: str, prof_b: np.ndarray, type_b: str) -> Tuple[bool, float, float]:
    """
    Computes compatibility and shape distance between two edges.
    Returns:
        (is_compatible, mse, similarity)
    """
    if (type_a == "TAB" and type_b == "GAP") or (type_a == "GAP" and type_b == "TAB"):
        dev_b_flipped = -prof_b[::-1]
        mse = float(np.mean((prof_a - dev_b_flipped) ** 2))
        similarity = float(1.0 / (1.0 + mse / 100.0))
        return True, mse, similarity
    elif type_a == "FLAT" and type_b == "FLAT":
        # Two flat edges can't lock together internally
        return False, float('inf'), 0.0
    else:
        return False, float('inf'), 0.0

def compute_compatibility_matrix(pieces_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Computes all pairwise edge matching scores across all pieces.
    """
    sides = ["TOP", "RIGHT", "BOTTOM", "LEFT"]
    matrix = []
    
    for i, p_a in enumerate(pieces_data):
        for side_a in sides:
            prof_a = p_a["profiles"][side_a]
            type_a = p_a["types"][side_a]
            
            for j, p_b in enumerate(pieces_data):
                if i == j:
                    continue
                for side_b in sides:
                    prof_b = p_b["profiles"][side_b]
                    type_b = p_b["types"][side_b]
                    
                    compatible, mse, sim = match_edge_profiles(prof_a, type_a, prof_b, type_b)
                    if compatible:
                        matrix.append({
                            "piece_a": p_a["id"],
                            "side_a": side_a,
                            "type_a": type_a,
                            "piece_b": p_b["id"],
                            "side_b": side_b,
                            "type_b": type_b,
                            "mse": round(mse, 2),
                            "similarity": round(sim, 4)
                        })
                        
    matrix.sort(key=lambda x: x["mse"])
    return {"matches": matrix}
