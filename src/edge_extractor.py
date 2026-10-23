import cv2
import numpy as np
from typing import Dict, List, Tuple, Any

def extract_piece_edges(contour: np.ndarray, num_samples: int = 100, flat_threshold: float = 14.0) -> Dict[str, Any]:
    """
    Extracts canonical 4 edges (TOP, RIGHT, BOTTOM, LEFT) in clockwise order,
    computes normal deviation profiles, and classifies each edge.
    """
    pts = contour.reshape(-1, 2)
    x, y, w, h = cv2.boundingRect(contour)
    center = (x + w / 2.0, y + h / 2.0)
    
    # 4 geometric corner targets: TL, TR, BR, BL
    targets = {
        "TL": np.array([x, y]),
        "TR": np.array([x + w, y]),
        "BR": np.array([x + w, y + h]),
        "BL": np.array([x, y + h])
    }
    
    idxs = {}
    for name, tgt in targets.items():
        idxs[name] = int(np.argmin(np.linalg.norm(pts - tgt, axis=1)))
        
    tl, tr, br, bl = idxs["TL"], idxs["TR"], idxs["BR"], idxs["BL"]
    n_pts = len(pts)
    
    def get_slice(start: int, end: int) -> np.ndarray:
        if start <= end:
            return pts[start:end+1]
        else:
            return np.vstack([pts[start:], pts[:end+1]])

    # Determine contour traversal direction
    fwd_len = (tr - tl) % n_pts
    rev_len = (tl - tr) % n_pts
    
    if fwd_len < rev_len:
        raw_edges = {
            "TOP": get_slice(tl, tr),
            "RIGHT": get_slice(tr, br),
            "BOTTOM": get_slice(br, bl),
            "LEFT": get_slice(bl, tl)
        }
    else:
        raw_edges = {
            "TOP": get_slice(tr, tl)[::-1],
            "RIGHT": get_slice(br, tr)[::-1],
            "BOTTOM": get_slice(bl, br)[::-1],
            "LEFT": get_slice(tl, bl)[::-1]
        }
        
    profiles = {}
    types = {}
    deviations_dict = {}
    
    for side, edge in raw_edges.items():
        if len(edge) < 5:
            profiles[side] = np.zeros(num_samples)
            types[side] = "FLAT"
            continue
            
        [vx, vy, x0, y0] = cv2.fitLine(edge, cv2.DIST_L2, 0, 0.01, 0.01)
        tangent = np.array([float(vx[0]), float(vy[0])])
        normal = np.array([-float(vy[0]), float(vx[0])])
        
        edge_center = np.mean(edge, axis=0)
        if np.dot(normal, edge_center - center) < 0:
            normal = -normal
            
        devs = [np.dot(p - [x0[0], y0[0]], normal) for p in edge]
        poss = [np.dot(p - [x0[0], y0[0]], tangent) for p in edge]
        
        order = np.argsort(poss)
        poss = np.array(poss)[order]
        devs = np.array(devs)[order]
        
        span = poss.max() - poss.min()
        if span == 0:
            profiles[side] = np.zeros(num_samples)
            types[side] = "FLAT"
            continue
            
        norm_pos = (poss - poss.min()) / span
        resampled_devs = np.interp(np.linspace(0, 1, num_samples), norm_pos, devs)
        
        edge_type = classify_edge(resampled_devs, flat_threshold)
        
        profiles[side] = resampled_devs
        types[side] = edge_type
        deviations_dict[side] = {
            "max_pos": float(np.max(resampled_devs)),
            "max_neg": float(np.min(resampled_devs)),
            "mean": float(np.mean(resampled_devs))
        }

    flat_count = list(types.values()).count("FLAT")
    if flat_count >= 2:
        piece_role = "CORNER"
    elif flat_count == 1:
        piece_role = "BORDER"
    else:
        piece_role = "INTERIOR"
        
    return {
        "raw_edges": raw_edges,
        "profiles": profiles,
        "types": types,
        "role": piece_role,
        "deviations": deviations_dict,
        "bbox": (x, y, w, h),
        "center": center
    }

def classify_edge(profile: np.ndarray, flat_threshold: float = 14.0) -> str:
    """
    Classifies an edge profile into FLAT, TAB, or GAP.
    """
    if profile is None or len(profile) == 0:
        return "UNKNOWN"
        
    max_pos = float(np.max(profile))
    max_neg = float(np.min(profile))
    
    if max(max_pos, abs(max_neg)) < flat_threshold:
        return "FLAT"
    elif max_pos > abs(max_neg):
        return "TAB"
    else:
        return "GAP"
