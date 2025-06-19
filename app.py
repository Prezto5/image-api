from flask import Flask, request, send_file, abort
from PIL import Image, ImageDraw
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
        # Жёстко заданные параметры по макету
        canvas_w, canvas_h = 1958, 1785
        photo_w, photo_h = 413, 531
        border = 2
        border_color = (198, 198, 198)  # C6C6C6
        # Отступы
        left_margin = 85
        top_margin = 83
        col_gap = 86
        row_gap = 134
        # Считаем координаты для 6 фото (3x2)
        positions = []
        for row in range(2):
            for col in range(3):
                x = left_margin + col * (photo_w + col_gap)
                y = top_margin + row * (photo_h + row_gap)
                positions.append((x, y))
        # Подгоняем фото под размер
        img = img.convert('RGB')
        img = img.copy()
        img.thumbnail((photo_w - 2*border, photo_h - 2*border))
        # Создаём холст
        canvas = Image.new('RGB', (canvas_w, canvas_h), (255, 255, 255))
        for x, y in positions:
            # Ячейка для фото с рамкой
            frame = Image.new('RGB', (photo_w, photo_h), (255, 255, 255))
            # Центрируем фото внутри рамки
            px = (photo_w - img.width) // 2
            py = (photo_h - img.height) // 2
            frame.paste(img, (px, py))
            # Рисуем рамку
            draw = ImageDraw.Draw(frame)
            for b in range(border):
                draw.rectangle([b, b, photo_w-1-b, photo_h-1-b], outline=border_color)
            # Вставляем на холст
            canvas.paste(frame, (x, y))
        img_bytes = io.BytesIO()
        canvas.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        print(f"[INFO] 6 images placed on canvas {canvas_w}x{canvas_h} as in Figma layout", file=sys.stderr)
        return send_file(img_bytes, mimetype='image/png')
    except Exception as e:
        print(f"[ERROR] Exception: {str(e)}", file=sys.stderr)
        return {"error": str(e)}, 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000) 