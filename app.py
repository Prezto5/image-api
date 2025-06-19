from flask import Flask, request, send_file
from PIL import Image
import io
import logging
import os
import sys

app = Flask(__name__)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Константы для холста
CANVAS_WIDTH = 1958
CANVAS_HEIGHT = 1785

# Отступы для фотографий
PHOTO_MARGIN_LEFT = 107  # отступ слева
PHOTO_MARGIN_TOP = 85    # отступ сверху
PHOTO_MARGIN_BOTTOM = 97 # отступ между рядами
PHOTO_GAP = 166         # отступ между фото

# Отступы для лого и подписи
LEFT_MARGIN = 369  # отступ слева для лого
BOTTOM_MARGIN = 206  # отступ снизу для лого
RIGHT_TEXT_MARGIN = 144  # отступ справа от лого до текста
BOTTOM_TEXT_MARGIN = 265  # отступ снизу для текста

# Получаем абсолютный путь к директории приложения
APP_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(APP_DIR, 'assets')

def add_logo_and_signature(canvas):
    """Добавляет логотип и подпись на холст"""
    try:
        # Загрузка логотипа
        logo = Image.open(os.path.join(ASSETS_DIR, 'logo.png'))
        if logo.mode != 'RGBA':
            logo = logo.convert('RGBA')
            
        # Размещаем логотип с учетом отступов слева и снизу
        logo_pos = (LEFT_MARGIN, CANVAS_HEIGHT - logo.height - BOTTOM_MARGIN)
        canvas.paste(logo, logo_pos, logo)
        
        # Загрузка подписи
        signature = Image.open(os.path.join(ASSETS_DIR, 'Signature.png'))
        if signature.mode != 'RGBA':
            signature = signature.convert('RGBA')
            
        # Размещаем подпись справа от логотипа
        signature_x = logo_pos[0] + logo.width + RIGHT_TEXT_MARGIN
        signature_y = CANVAS_HEIGHT - signature.height - BOTTOM_TEXT_MARGIN
        canvas.paste(signature, (signature_x, signature_y), signature)
        
    except Exception as e:
        logger.error(f"Error adding logo and signature: {str(e)}")
        raise

@app.route('/resize', methods=['POST'])
def resize_images():
    try:
        if 'photos' not in request.files:
            return {'error': 'No photos provided'}, 400
            
        photos = request.files.getlist('photos')
        if len(photos) != 6:
            return {'error': 'Exactly 6 photos required'}, 400

        # Создаем белый холст
        canvas = Image.new('RGB', (CANVAS_WIDTH, CANVAS_HEIGHT), 'white')
        
        # Размещаем фотографии на холсте
        for i, photo in enumerate(photos):
            img = Image.open(photo)
            img = img.convert('RGB')
            
            # Вычисляем позицию для фото
            row = i // 3
            col = i % 3
            
            # Вычисляем координаты для размещения фото
            x = PHOTO_MARGIN_LEFT + col * (img.width + PHOTO_GAP)
            y = PHOTO_MARGIN_TOP + row * (img.height + PHOTO_MARGIN_BOTTOM)
            
            # Размещаем фото на холсте
            canvas.paste(img, (x, y))

        # Добавляем логотип и подпись
        add_logo_and_signature(canvas)

        # Сохраняем результат
        output = io.BytesIO()
        canvas.save(output, format='JPEG', quality=95)
        output.seek(0)
        
        return send_file(output, mimetype='image/jpeg')

    except Exception as e:
        logger.error(f"Error processing images: {str(e)}")
        return {'error': str(e)}, 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80) 