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
CANVAS_HEIGHT = 1958  # высота холста
CANVAS_WIDTH = 1785   # ширина холста

# Отступы для фотографий
PHOTO_MARGIN_LEFT = 107  # отступ слева
PHOTO_MARGIN_TOP = 85    # отступ сверху
PHOTO_GAP_HORIZONTAL = 166  # отступ между фото по горизонтали
PHOTO_GAP_VERTICAL = 252    # отступ между фото по вертикали

# Отступы для лого и подписи
LOGO_MARGIN_LEFT = 462    # отступ слева для лого
LOGO_TO_BOTTOM_PHOTO = 204  # отступ от нижнего фото до лого
TEXT_MARGIN_LEFT = 144    # отступ между лого и текстом
TEXT_TO_BOTTOM_PHOTO = 252  # отступ от нижнего фото до подписи

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
            
        # Открываем первое фото для получения размеров
        first_photo = Image.open(photos[0]).convert('RGB')
        img_width = first_photo.width
        img_height = first_photo.height
        
        # Вычисляем позицию последнего ряда фотографий
        last_row_y = PHOTO_MARGIN_TOP + (img_height + PHOTO_GAP_VERTICAL)  # Y-координата второго ряда
        
        # Размещаем логотип относительно нижнего ряда фотографий
        logo_y = last_row_y + img_height + LOGO_TO_BOTTOM_PHOTO
        logo_pos = (LOGO_MARGIN_LEFT, logo_y)
        canvas.paste(logo, logo_pos, logo)
        
        # Загрузка подписи
        signature = Image.open(os.path.join(ASSETS_DIR, 'Signature.png'))
        if signature.mode != 'RGBA':
            signature = signature.convert('RGBA')
            
        # Размещаем подпись справа от логотипа и относительно нижнего ряда фотографий
        signature_x = logo_pos[0] + logo.width + TEXT_MARGIN_LEFT
        signature_y = last_row_y + img_height + TEXT_TO_BOTTOM_PHOTO
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
        
        # Открываем первое фото для получения размеров
        first_photo = Image.open(photos[0]).convert('RGB')
        img_width = first_photo.width
        img_height = first_photo.height
        
        # Размещаем фотографии на холсте
        for i, photo in enumerate(photos):
            img = Image.open(photo)
            img = img.convert('RGB')
            
            # Вычисляем позицию для фото
            row = i // 3
            col = i % 3
            
            # Вычисляем координаты для размещения фото
            x = PHOTO_MARGIN_LEFT + col * (img_width + PHOTO_GAP_HORIZONTAL)
            y = PHOTO_MARGIN_TOP + row * (img_height + PHOTO_GAP_VERTICAL)
            
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