from flask import Flask, request, send_file, abort
from PIL import Image
import io
import sys

app = Flask(__name__)

@app.before_request
def check_file_size():
    if request.content_length and request.content_length > 5 * 1024 * 1024:
        print(f"[ERROR] File too large: {request.content_length} bytes", file=sys.stderr)
        abort(413, "File too large")

@app.route('/resize', methods=['POST'])
def resize_image():
    if 'image' not in request.files:
        print("[ERROR] No image provided", file=sys.stderr)
        return {"error": "No image provided"}, 400
    file = request.files['image']
    try:
        img = Image.open(file.stream)
        allowed_formats = ['JPEG', 'PNG', 'WEBP']
        if img.format not in allowed_formats:
            print(f"[ERROR] Unsupported format: {img.format}", file=sys.stderr)
            return {"error": "Unsupported format"}, 415
        img.thumbnail((500, 500))
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        print(f"[INFO] Image processed successfully: {img.format}, size: {img.size}", file=sys.stderr)
        return send_file(img_bytes, mimetype='image/png')
    except Exception as e:
        print(f"[ERROR] Exception: {str(e)}", file=sys.stderr)
        return {"error": str(e)}, 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000) 