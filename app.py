from flask import Flask, request, jsonify, send_file
from PIL import Image
import io
import logging
import os
import uuid

app = Flask(__name__)

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Константы
UPLOAD_FOLDER = '/app/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/resize', methods=['POST'])
def resize_image():
    try:
        logger.info("Получен запрос на /resize")
        
        if 'photo' not in request.files:
            logger.error("Файл не найден в запросе")
            return jsonify({'error': 'No file provided'}), 400
            
        photo = request.files['photo']
        logger.info(f"Получен файл: {photo.filename}")
        
        # Открываем изображение
        img = Image.open(photo)
        logger.info(f"Изображение открыто, размер: {img.size}")
        
        # Изменяем размер
        img = img.resize((800, 600))
        logger.info("Размер изображения изменен")
        
        # Генерируем уникальное имя файла
        filename = f"{uuid.uuid4()}.jpg"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        # Сохраняем файл
        img.save(filepath, 'JPEG')
        logger.info(f"Файл сохранен как {filepath}")
        
        # Формируем URL
        url = f"https://imageapi-nrkypima.b4a.run/image/{filename}"
        
        # Возвращаем JSON с URL
        return jsonify({
            'success': True,
            'message': 'Image resized successfully',
            'url': url
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
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000))) 