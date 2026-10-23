import numpy as np
from typing import Dict, List, Tuple, Any, Optional

def get_possible_grid_shapes(num_pieces: int) -> List[Tuple[int, int]]:
    """
    Returns plausible (rows, cols) for a given piece count.
    """
    if num_pieces == 6:
        return [(2, 3), (3, 2)]
    elif num_pieces == 9:
        return [(3, 3)]
    elif num_pieces == 12:
        return [(3, 4), (4, 3)]
    elif num_pieces == 16:
        return [(4, 4)]
    else:
        # Default factors
        shapes = []
        for r in range(1, int(np.sqrt(num_pieces)) + 1):
            if num_pieces % r == 0:
                shapes.append((r, num_pieces // r))
                if r != num_pieces // r:
                    shapes.append((num_pieces // r, r))
        return sorted(shapes, key=lambda s: abs(s[0] - s[1]))

def solve_puzzle_grid(pieces_data: List[Dict[str, Any]], target_shape: Optional[Tuple[int, int]] = None) -> Dict[str, Any]:
    """
    Constraint-satisfaction backtracking solver that determines the optimal
    grid placement and orientation for every jigsaw piece.
    """
    num_pieces = len(pieces_data)
    shapes = [target_shape] if target_shape else get_possible_grid_shapes(num_pieces)
    
    side_order = ["TOP", "RIGHT", "BOTTOM", "LEFT"]
    
    # Pre-generate 4 rotation variants for each piece
    variants_by_piece = {}
    for p in pieces_data:
        pid = p["id"]
        variants_by_piece[pid] = []
        for rot in range(4):
            # rot: 0=0 deg, 1=90 deg CW, 2=180 deg CW, 3=270 deg CW
            # When rotated clockwise by rot, the new TOP is the old side at (0 - rot) % 4
            rot_types = {}
            rot_profs = {}
            for i, side in enumerate(side_order):
                src_side = side_order[(i - rot) % 4]
                rot_types[side] = p["types"][src_side]
                rot_profs[side] = p["profiles"][src_side]
                
            variants_by_piece[pid].append({
                "id": pid,
                "rot": rot,
                "angle": rot * 90,
                "types": rot_types,
                "profiles": rot_profs
            })

    def match_edges(prof_a, type_a, prof_b, type_b):
        if type_a != "FLAT" and type_b != "FLAT":
            dev_b_flipped = -prof_b[::-1]
            mse = float(np.mean((prof_a - dev_b_flipped) ** 2))
            if mse < 1200.0:
                return mse
        return float('inf')

    all_variants = [v for v_list in variants_by_piece.values() for v in v_list]
    
    best_overall_solution = None
    best_overall_shape = None
    min_overall_cost = float('inf')

    for rows, cols in shapes:
        if rows * cols != num_pieces:
            continue
            
        cells = [(r, c) for r in range(rows) for c in range(cols)]
        
        # Define external border constraints for this shape
        border_rules = {}
        for r in range(rows):
            for c in range(cols):
                border_rules[(r, c)] = {
                    "TOP": "FLAT" if r == 0 else "NON_FLAT",
                    "BOTTOM": "FLAT" if r == rows - 1 else "NON_FLAT",
                    "LEFT": "FLAT" if c == 0 else "NON_FLAT",
                    "RIGHT": "FLAT" if c == cols - 1 else "NON_FLAT"
                }

        solutions = []

        def backtrack(cell_idx, current_grid, used_ids, current_cost):
            if cell_idx == len(cells):
                solutions.append((current_cost, dict(current_grid)))
                return
                
            r, c = cells[cell_idx]
            rules = border_rules[(r, c)]
            
            for v in all_variants:
                if v["id"] in used_ids:
                    continue
                    
                # 1. Enforce external flat borders
                valid_borders = True
                for side, rule in rules.items():
                    if rule == "FLAT" and v["types"][side] != "FLAT":
                        valid_borders = False
                        break
                    elif rule == "NON_FLAT" and v["types"][side] == "FLAT":
                        valid_borders = False
                        break
                if not valid_borders:
                    continue
                    
                cost_increment = 0.0
                
                # 2. Check Top neighbor
                if r > 0:
                    top_neighbor = current_grid[(r - 1, c)]
                    score = match_edges(
                        v["profiles"]["TOP"], v["types"]["TOP"],
                        top_neighbor["profiles"]["BOTTOM"], top_neighbor["types"]["BOTTOM"]
                    )
                    if score == float('inf'):
                        continue
                    cost_increment += score
                    
                # 3. Check Left neighbor
                if c > 0:
                    left_neighbor = current_grid[(r, c - 1)]
                    score = match_edges(
                        v["profiles"]["LEFT"], v["types"]["LEFT"],
                        left_neighbor["profiles"]["RIGHT"], left_neighbor["types"]["RIGHT"]
                    )
                    if score == float('inf'):
                        continue
                    cost_increment += score
                    
                # Place and recurse
                current_grid[(r, c)] = v
                used_ids.add(v["id"])
                
                backtrack(cell_idx + 1, current_grid, used_ids, current_cost + cost_increment)
                
                used_ids.remove(v["id"])
                del current_grid[(r, c)]

        backtrack(0, {}, set(), 0.0)
        
        if solutions:
            solutions.sort(key=lambda x: x[0])
            best_cost, best_grid = solutions[0]
            if best_cost < min_overall_cost:
                min_overall_cost = best_cost
                best_overall_solution = best_grid
                best_overall_shape = (rows, cols)

    if best_overall_solution is None:
        return {
            "success": False,
            "error": "No valid assembly found satisfying all boundary and interlocking constraints."
        }
        
    rows, cols = best_overall_shape
    grid_layout = []
    for r in range(rows):
        row_items = []
        for c in range(cols):
            cell_data = best_overall_solution[(r, c)]
            row_items.append({
                "piece_id": cell_data["id"],
                "rotation_deg": cell_data["angle"],
                "row": r,
                "col": c,
                "types": cell_data["types"]
            })
        grid_layout.append(row_items)
        
    return {
        "success": True,
        "rows": rows,
        "cols": cols,
        "total_cost": round(min_overall_cost, 2),
        "confidence": round(1.0 / (1.0 + min_overall_cost / (rows * cols * 50.0)), 4),
        "grid": grid_layout
    }
