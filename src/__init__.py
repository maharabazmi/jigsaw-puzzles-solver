"""
Jigsaw Contour & Assembly Solver Package
"""

from .preprocessor import segment_jigsaw_pieces
from .edge_extractor import extract_piece_edges, classify_edge
from .matcher import match_edge_profiles, compute_compatibility_matrix
from .solver import solve_puzzle_grid
from .visualizer import render_assembly, create_pieces_montage
from .pipeline import JigsawPipeline

__all__ = [
    "segment_jigsaw_pieces",
    "extract_piece_edges",
    "classify_edge",
    "match_edge_profiles",
    "compute_compatibility_matrix",
    "solve_puzzle_grid",
    "render_assembly",
    "create_pieces_montage",
    "JigsawPipeline",
]
