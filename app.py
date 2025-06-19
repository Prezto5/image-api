from flask import Flask, jsonify, request, send_file
from PIL import Image
import io
import logging
import os
import uuid
import requests
from urllib.parse import urlparse

app = Flask(__name__)

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Константы
UPLOAD_FOLDER = '/app/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return jsonify({
        'message': 'Image Processing API',
        'version': '1.0',
        'endpoints': {
            'resize': '/resize (POST)',
            'image': '/image/<filename> (GET)'
        }
    })

@app.route('/resize', methods=['POST'])
def resize_image():
    try:
        logger.debug("Получен запрос на /resize")
        
        # Проверяем, получили ли мы URL изображения
        photo_url = request.form.get('photo_url')
        if photo_url:
            logger.debug(f"Получен URL изображения: {photo_url}")
            # Загружаем изображение по URL
            response = requests.get(photo_url)
            if response.status_code != 200:
                return jsonify({'error': 'Failed to download image from URL'}), 400
            img = Image.open(io.BytesIO(response.content))
        elif 'photo' in request.files:
            photo = request.files['photo']
            logger.debug(f"Получен файл: {photo.filename}")
            img = Image.open(photo)
        else:
            logger.error("Ни файл, ни URL не предоставлены")
            return jsonify({'error': 'No file or URL provided'}), 400
            
        logger.debug(f"Изображение открыто, размер: {img.size}")
        
        # Создаем новое изображение с белым фоном
        background = Image.new('RGB', (800, 600), 'white')
        
        # Изменяем размер изображения с сохранением пропорций
        img.thumbnail((700, 500))
        
        # Вычисляем позицию для центрирования
        x = (800 - img.width) // 2
        y = (600 - img.height) // 2
        
        # Вставляем изображение на фон
        background.paste(img, (x, y))
        
        # Генерируем уникальное имя файла
        filename = f"{uuid.uuid4()}.jpg"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        # Сохраняем файл
        background.save(filepath, 'JPEG')
        logger.debug(f"Файл сохранен как {filepath}")
        
        # Формируем URL
        url = f"/image/{filename}"
        
        return jsonify({
            'success': True,
            'message': 'Image processed successfully',
            'data': {
                'url': url,
                'width': background.width,
                'height': background.height,
                'original_size': img.size
            }
        })
        
    except Exception as e:
        logger.error(f"Ошибка при обработке изображения: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/image/<filename>')
def get_image(filename):
    try:
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
        return send_file(filepath, mimetype='image/jpeg')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port) 