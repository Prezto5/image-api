from flask import Flask, jsonify, send_file, request
from PIL import Image
import io
import logging
import os

app = Flask(__name__)

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@app.route('/resize', methods=['POST'])
def resize_image():
    try:
        logger.debug("Получен запрос на /resize")
        
        if 'photo' not in request.files:
            logger.error("Файл не найден в запросе")
            return jsonify({'error': 'No file provided'}), 400
            
        photo = request.files['photo']
        logger.debug(f"Получен файл: {photo.filename}")
        
        # Открываем изображение
        img = Image.open(photo)
        logger.debug(f"Изображение открыто, размер: {img.size}")
        
        # Изменяем размер
        resized_img = img.resize((800, 600))
        logger.debug("Изображение изменено")
        
        # Сохраняем в буфер
        img_io = io.BytesIO()
        resized_img.save(img_io, 'JPEG')
        img_io.seek(0)
        logger.debug("Изображение сохранено в буфер")
        
        # Возвращаем JSON с информацией
        return jsonify({
            'success': True,
            'message': 'Image resized successfully',
            'data': {
                'width': 800,
                'height': 600
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