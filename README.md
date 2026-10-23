# Jigsaw Contour & Assembly AI

An automated end-to-end computer vision and constraint satisfaction system that detects, segments, classifies, matches, and solves disassembled jigsaw puzzles from images — coupled with an interactive cross-platform **Flutter** application.

---

## Architecture Overview

```
jigsaw-contour-project/
├── dataset/raw/             # Raw puzzle images (6-piece and 9-piece puzzles)
├── src/                     # Core Python Computer Vision & Solver Package
│   ├── preprocessor.py      # Step 1: Adaptive background subtraction & hole-filled segmentation
│   ├── edge_extractor.py    # Step 1 & 2: 4-edge decomposition & normal deviation curves (N=100)
│   ├── matcher.py           # Step 2: Shape distance (MSE) & pairwise compatibility matrix
│   ├── solver.py            # Step 3: Constraint-satisfaction backtracking grid solver
│   ├── visualizer.py        # Step 3: Piece montage & interlocking puzzle stitcher
│   ├── pipeline.py          # Unified pipeline orchestrator
│   └── api.py               # REST API server for the Flutter client
├── flutter_app/             # Modern Flutter Application (Web & Desktop)
│   ├── lib/main.dart        # Full UI with puzzle picker, live solver & inspection tabs
│   └── pubspec.yaml         # Flutter dependencies
├── results/                 # Output montages, stitched puzzle images, and JSON reports
├── run_pipeline.py          # Command-line interface runner
└── notebooks/               # Jupyter notebook exploration
```

---

## 1. What Has Been Implemented

### Step 1: Robust Perception & Segmentation
- **Adaptive Background Detection**: Automatically analyzes perimeter border samples to detect whether the background is dark (e.g., `6pieces2.png`) or light (e.g., `6pieces1.png`, `9pieces3.png`).
- **Hole-Filled Binary Masking**: Computes maximum color distance to background, applies morphological closing, and flood-fills interior holes so internal artwork doesn't cause piece fracturing.
- **Canonical 4-Edge Extraction**: Identifies the 4 true geometric corners (TL, TR, BR, BL) and traces the contour in clockwise order to produce standard `TOP`, `RIGHT`, `BOTTOM`, and `LEFT` edges.
- **Arc-Length Resampling**: Computes outward normal deviations along each edge using `cv2.fitLine` and resamples uniformly onto $N=100$ points ($s \in [0, 1]$).

### Step 2: Feature Engineering & Edge Classification
- **Discrete Classification**: Categorizes every edge into `FLAT` (puzzle border), `TAB` (protrusion), or `GAP` (indentation).
- **Piece Role Classification**:
  - `CORNER`: $\ge 2$ FLAT edges (placed at the 4 grid corners).
  - `BORDER`: Exactly 1 FLAT edge (placed along outer borders).
  - `INTERIOR`: 0 FLAT edges (placed in the puzzle core).
- **Inverted Curve Matching**: Compares non-flat edges by reversing spatial direction ($[::-1]$) and negating deviation sign ($-d$) to measure Mean Squared Error (MSE).

### Step 3: Global Grid Solver & Visual Stitcher
- **Constraint Satisfaction Backtracking Search**: Finds the optimal grid assignment ($2 \times 3$, $3 \times 2$, or $3 \times 3$) and rotation ($0^\circ, 90^\circ, 180^\circ, 270^\circ$) by enforcing external flat border constraints and minimizing internal edge MSE.
- **Interlocking Piece Stitcher**: Rotates and overlaps pieces by the tab depth into an assembled canvas saved under `results/`.

### Flutter Application
- Complete Material 3 dark-themed Flutter application with:
  - **Sample Puzzle Selector**: Choose any image from the dataset.
  - **Live Solver**: Triggers the AI pipeline and displays real-time progress.
  - **Assembled View**: Displays the solved puzzle, piece rotation angles, and grid coordinates.
  - **Segmentation View**: Displays the piece montage and contour metrics.
  - **Classification View**: Displays piece roles and colored edge chips (`TAB`, `GAP`, `FLAT`).

---

## 2. Quickstart & Usage

### Running the Python Pipeline via CLI
Run on any puzzle image:
```powershell
.\venv\Scripts\python.exe run_pipeline.py --image dataset/raw/6pieces1.png
.\venv\Scripts\python.exe run_pipeline.py --image dataset/raw/6pieces2.png
.\venv\Scripts\python.exe run_pipeline.py --image dataset/raw/9pieces3.png
```
Outputs:
- Assembled image: `results/<name>_assembly.png`
- Piece montage: `results/<name>_pieces.png`
- Structured report: `results/<name>_report.json`

---

### Running the API & Flutter App

#### 1. Start the Python Vision API:
```powershell
.\venv\Scripts\python.exe -m src.api
```
*(Runs on `http://127.0.0.1:8000` with CORS enabled)*

#### 2. Run the Flutter App:
```powershell
cd flutter_app
flutter run -d chrome
```
*(Or test on Edge: `flutter run -d edge`)*
