import http.server
import socketserver
import json
import os
import urllib.parse
import mimetypes
import base64
from typing import Dict, Any

from .pipeline import JigsawPipeline

PORT = 8000
DATASET_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "dataset", "raw"))
RESULTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "results"))

pipeline = JigsawPipeline(output_dir=RESULTS_DIR)

class JigsawAPIHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Enable CORS for Flutter Web / Desktop
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path == "/" or path == "/api/health":
            self.send_json({"status": "running", "engine": "Jigsaw Contour & Assembly AI"})
        elif path == "/api/samples":
            samples = []
            if os.path.exists(DATASET_DIR):
                for f in sorted(os.listdir(DATASET_DIR)):
                    if f.endswith('.png') or f.endswith('.jpg'):
                        samples.append({
                            "name": f,
                            "path": os.path.join(DATASET_DIR, f),
                            "pieces": 6 if "6" in f else 9
                        })
            self.send_json({"samples": samples})
        elif path == "/api/image":
            img_path = query.get("path", [None])[0]
            if not img_path or not os.path.exists(img_path):
                self.send_error(404, "Image not found")
                return
            mime_type, _ = mimetypes.guess_type(img_path)
            self.send_response(200)
            self.send_header("Content-Type", mime_type or "image/png")
            self.end_headers()
            with open(img_path, "rb") as f:
                self.wfile.write(f.read())
        else:
            self.send_error(404, "Endpoint not found")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/solve":
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body) if body else {}

            img_path = data.get("image_path")
            if not img_path:
                img_name = data.get("sample_name")
                if img_name:
                    img_path = os.path.join(DATASET_DIR, img_name)

            if not img_path or not os.path.exists(img_path):
                self.send_json({"success": False, "error": f"Invalid image path: {img_path}"}, status=400)
                return

            result = pipeline.process_image(img_path)

            # Add Base64 encoded previews for ease of direct Flutter rendering
            if result.get("success") and result.get("artifacts", {}).get("assembly_path"):
                asm_path = result["artifacts"]["assembly_path"]
                if os.path.exists(asm_path):
                    with open(asm_path, "rb") as f:
                        result["assembly_base64"] = base64.b64encode(f.read()).decode("utf-8")
                        
            if result.get("artifacts", {}).get("montage_path"):
                mnt_path = result["artifacts"]["montage_path"]
                if os.path.exists(mnt_path):
                    with open(mnt_path, "rb") as f:
                        result["montage_base64"] = base64.b64encode(f.read()).decode("utf-8")

            self.send_json(result)
        else:
            self.send_error(404, "Endpoint not found")

    def send_json(self, payload: Dict[str, Any], status: int = 200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

def start_server():
    server = socketserver.TCPServer(("0.0.0.0", PORT), JigsawAPIHandler)
    print(f"Jigsaw AI Solver API running on http://127.0.0.1:{PORT}")
    server.serve_forever()

if __name__ == "__main__":
    start_server()
