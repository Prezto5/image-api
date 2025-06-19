from flask import Flask, request, jsonify
from PIL import Image
import io
import logging
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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
        
        # Сохраняем в буфер
        img_io = io.BytesIO()
        img.save(img_io, 'JPEG')
        img_io.seek(0)
        
        # Возвращаем результат
        return jsonify({
            'success': True,
            'message': 'Image resized successfully',
            'data': img_io.getvalue().decode('latin1')
        })

    except Exception as e:
        logger.error(f"Ошибка при обработке изображения: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000))) 