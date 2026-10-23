import argparse
import json
import os
from src.pipeline import JigsawPipeline

def main():
    parser = argparse.ArgumentParser(description="Jigsaw Puzzle Contour & Assembly Solver")
    parser.add_argument("--image", type=str, default="dataset/raw/6pieces1.png", help="Path to puzzle image")
    parser.add_argument("--output", type=str, default="results", help="Directory to save results")
    args = parser.parse_args()
    
    print(f"=== Running Jigsaw Puzzle Solver on {args.image} ===")
    pipeline = JigsawPipeline(output_dir=args.output)
    result = pipeline.process_image(args.image)
    
    if result["success"]:
        print(f"[OK] Solved in {result['elapsed_seconds']}s!")
        print(f"Pieces detected: {result['piece_count']}")
        print(f"Roles: {result['roles_summary']}")
        print(f"Grid Layout: {result['solver']['rows']} rows x {result['solver']['cols']} cols")
        for r, row in enumerate(result['solver']['grid']):
            row_str = " | ".join([f"Piece #{c['piece_id']} (rot={c['rotation_deg']}°)" for c in row])
            print(f"  Row {r}: {row_str}")
        print(f"Montage saved to: {result['artifacts']['montage_path']}")
        print(f"Assembled solution saved to: {result['artifacts']['assembly_path']}")
    else:
        print(f"[ERROR] Failed: {result.get('error', 'Unknown error')}")
        
    # Save JSON report
    report_path = os.path.join(args.output, f"{os.path.splitext(os.path.basename(args.image))[0]}_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        # Convert non-serializable elements
        json.dump(result, f, indent=2)
    print(f"Report JSON saved to: {report_path}")

if __name__ == "__main__":
    main()
