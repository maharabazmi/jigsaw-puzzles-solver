import cv2
import numpy as np
import os
from typing import Dict, List, Any

def rotate_image(image: np.ndarray, angle_deg: int) -> np.ndarray:
    """
    Rotates image by 0, 90, 180, or 270 degrees clockwise.
    """
    angle = angle_deg % 360
    if angle == 90:
        return cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
    elif angle == 180:
        return cv2.rotate(image, cv2.ROTATE_180)
    elif angle == 270:
        return cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
    return image.copy()

def create_pieces_montage(original_image: np.ndarray, pieces_data: List[Dict[str, Any]], output_path: str = None) -> np.ndarray:
    """
    Creates an annotated visual summary of all detected pieces with their roles and edges.
    """
    n = len(pieces_data)
    cols = min(3, n)
    rows = (n + cols - 1) // cols
    
    cell_w, cell_h = 320, 320
    canvas = np.zeros((rows * cell_h, cols * cell_w, 3), dtype=np.uint8) + 248
    
    role_colors = {
        "CORNER": (0, 140, 255),  # Orange
        "BORDER": (200, 120, 0),  # Blue
        "INTERIOR": (0, 180, 0)   # Green
    }
    
    for idx, p in enumerate(pieces_data):
        r = idx // cols
        c = idx % cols
        x0 = c * cell_w
        y0 = r * cell_h
        
        crop = p["crop"]
        ch, cw = crop.shape[:2]
        
        # Scale down if piece exceeds available cell size
        scale = min(1.0, (cell_w - 60) / cw, (cell_h - 80) / ch)
        if scale < 1.0:
            crop_resized = cv2.resize(crop, (int(cw * scale), int(ch * scale)), interpolation=cv2.INTER_AREA)
        else:
            crop_resized = crop
            
        rch, rcw = crop_resized.shape[:2]
        px = x0 + (cell_w - rcw) // 2
        py = y0 + 40 + (cell_h - 70 - rch) // 2
        
        # Overlay piece
        for y in range(rch):
            for x in range(rcw):
                if not np.all(crop_resized[y, x] > 240):
                    canvas[py + y, px + x] = crop_resized[y, x]
                    
        # Labels
        role = p["role"]
        color = role_colors.get(role, (50, 50, 50))
        cv2.putText(canvas, f"Piece #{p['id']} [{role}]", (x0 + 15, y0 + 26),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, color, 2)
                    
        # Edge tags
        types = p["types"]
        tags = f"T:{types['TOP']} R:{types['RIGHT']} B:{types['BOTTOM']} L:{types['LEFT']}"
        cv2.putText(canvas, tags, (x0 + 15, y0 + cell_h - 12),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, (80, 80, 80), 1)

    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        cv2.imwrite(output_path, canvas)
        
    return canvas

def render_assembly(pieces_dict: Dict[int, Dict[str, Any]], solver_result: Dict[str, Any], output_path: str = None) -> np.ndarray:
    """
    Renders the solved jigsaw puzzle by rotating and interlocking pieces into a canvas.
    """
    if not solver_result.get("success"):
        return None
        
    rows = solver_result["rows"]
    cols = solver_result["cols"]
    grid = solver_result["grid"]
    
    crops = {pid: p["crop"] for pid, p in pieces_dict.items()}
    
    max_h = max(c.shape[0] for c in crops.values())
    max_w = max(c.shape[1] for c in crops.values())
    
    # Interlocking puzzle pieces overlap by their tab depth (~20-25% of piece dimension)
    step_x = int(max_w * 0.77)
    step_y = int(max_h * 0.77)
    
    canvas_h = (rows - 1) * step_y + max_h + 40
    canvas_w = (cols - 1) * step_x + max_w + 40
    canvas = np.zeros((canvas_h, canvas_w, 3), dtype=np.uint8) + 255
    
    margin = 20
    
    for r in range(rows):
        for c in range(cols):
            cell_data = grid[r][c]
            pid = cell_data["piece_id"]
            rot_deg = cell_data["rotation_deg"]
            
            crop = crops[pid]
            rotated = rotate_image(crop, rot_deg)
            rh, rw = rotated.shape[:2]
            
            y0 = margin + r * step_y
            x0 = margin + c * step_x
            
            for y in range(rh):
                for x in range(rw):
                    if not np.all(rotated[y, x] > 240):
                        cy = y0 + y
                        cx = x0 + x
                        if 0 <= cy < canvas_h and 0 <= cx < canvas_w:
                            canvas[cy, cx] = rotated[y, x]

    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        cv2.imwrite(output_path, canvas)
        
    return canvas
