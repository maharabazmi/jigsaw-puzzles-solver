import cv2
import numpy as np
import os
import time
from typing import Dict, Any, Optional

from .preprocessor import segment_jigsaw_pieces
from .edge_extractor import extract_piece_edges
from .matcher import compute_compatibility_matrix
from .solver import solve_puzzle_grid
from .visualizer import render_assembly, create_pieces_montage

class JigsawPipeline:
    def __init__(self, output_dir: str = "results"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
    def process_image(self, image_path: str, target_shape: Optional[tuple] = None) -> Dict[str, Any]:
        """
        Runs the end-to-end jigsaw puzzle perception, edge extraction,
        matching, and assembly solver.
        """
        start_time = time.time()
        
        if not os.path.exists(image_path):
            return {"success": False, "error": f"Image file not found: {image_path}"}
            
        image = cv2.imread(image_path)
        if image is None:
            return {"success": False, "error": f"Failed to decode image from {image_path}"}
            
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        
        # Step 1: Adaptive Segmentation
        mask, contours, bg_color = segment_jigsaw_pieces(image)
        if len(contours) == 0:
            return {"success": False, "error": "No puzzle pieces detected in image."}
            
        # Step 2: Extract Pieces & Canonical Edges
        pieces_data = []
        pieces_dict = {}
        
        for idx, cnt in enumerate(contours):
            edge_info = extract_piece_edges(cnt)
            x, y, w, h = edge_info["bbox"]
            
            crop = image[y:y+h, x:x+w].copy()
            mask_crop = mask[y:y+h, x:x+w].copy()
            crop[mask_crop == 0] = 255
            
            piece_obj = {
                "id": idx,
                "crop": crop,
                "bbox": (x, y, w, h),
                "role": edge_info["role"],
                "types": edge_info["types"],
                "profiles": edge_info["profiles"],
                "deviations": edge_info["deviations"]
            }
            pieces_data.append(piece_obj)
            pieces_dict[idx] = piece_obj
            
        # Step 3: Pairwise Compatibility Matrix
        comp_matrix = compute_compatibility_matrix(pieces_data)
        
        # Step 4: Constraint Satisfaction Grid Solver
        solver_res = solve_puzzle_grid(pieces_data, target_shape=target_shape)
        
        # Step 5: Render Visualizations
        montage_path = os.path.join(self.output_dir, f"{base_name}_pieces.png")
        create_pieces_montage(image, pieces_data, output_path=montage_path)
        
        assembly_path = os.path.join(self.output_dir, f"{base_name}_assembly.png")
        rendered = render_assembly(pieces_dict, solver_res, output_path=assembly_path)
        
        elapsed = time.time() - start_time
        
        return {
            "success": solver_res.get("success", False),
            "image_name": os.path.basename(image_path),
            "piece_count": len(pieces_data),
            "roles_summary": {
                "corners": sum(1 for p in pieces_data if p["role"] == "CORNER"),
                "borders": sum(1 for p in pieces_data if p["role"] == "BORDER"),
                "interiors": sum(1 for p in pieces_data if p["role"] == "INTERIOR")
            },
            "pieces": [
                {
                    "id": p["id"],
                    "role": p["role"],
                    "bbox": p["bbox"],
                    "types": p["types"],
                    "deviations": p["deviations"]
                }
                for p in pieces_data
            ],
            "solver": solver_res,
            "artifacts": {
                "montage_path": montage_path,
                "assembly_path": assembly_path if solver_res.get("success") else None
            },
            "elapsed_seconds": round(elapsed, 3)
        }
