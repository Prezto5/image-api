from flask import Flask, request, send_file
from PIL import Image, ImageDraw, ImageFont
import io
import logging
import os
import sys

app = Flask(__name__)

# Настройка расширенного логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Константы
CANVAS_WIDTH = 1958
CANVAS_HEIGHT = 1785
BORDER_COLOR = "#C6C6C6"
BORDER_WIDTH = 2
SPACING = 20
LOGO_SIZE = (200, 100)  # Размер для логотипа
SIGNATURE_HEIGHT = 40   # Высота для подписи

def check_assets():
    """Проверяет наличие и доступность файлов ассетов"""
    assets = ['logo.png', 'Signature.png']
    missing = []
    for asset in assets:
        path = os.path.join('assets', asset)
        if not os.path.exists(path):
            missing.append(asset)
        else:
            logger.info(f"Asset found: {path}")
    return missing

def add_logo_and_signature(canvas):
    """Добавляет логотип и подпись на холст"""
    try:
        # Проверяем наличие ассетов
        missing_assets = check_assets()
        if missing_assets:
            raise FileNotFoundError(f"Missing assets: {', '.join(missing_assets)}")

        logger.info("Starting to add logo")
        # Загрузка и размещение логотипа
        logo_path = os.path.join('assets', 'logo.png')
        logo = Image.open(logo_path)
        logger.info(f"Logo loaded successfully: {logo.size}, mode: {logo.mode}")
        
        logo = logo.resize(LOGO_SIZE, Image.Resampling.LANCZOS)
        logo_pos = (CANVAS_WIDTH - LOGO_SIZE[0] - SPACING, CANVAS_HEIGHT - LOGO_SIZE[1] - SPACING)
        
        # Конвертируем логотип в RGBA если нужно
        if logo.mode != 'RGBA':
            logo = logo.convert('RGBA')
            logger.info("Converted logo to RGBA mode")
            
        canvas.paste(logo, logo_pos, logo)
        logger.info("Logo placed successfully")
        
        logger.info("Starting to add signature")
        # Загрузка и размещение подписи
        signature_path = os.path.join('assets', 'Signature.png')
        signature = Image.open(signature_path)
        logger.info(f"Signature loaded successfully: {signature.size}, mode: {signature.mode}")
        
        # Масштабируем подпись, сохраняя пропорции
        signature_width = 200  # желаемая ширина
        signature_height = int(signature.height * (signature_width / signature.width))
        signature = signature.resize((signature_width, signature_height), Image.Resampling.LANCZOS)
        
        # Конвертируем подпись в RGBA если нужно
        if signature.mode != 'RGBA':
            signature = signature.convert('RGBA')
            logger.info("Converted signature to RGBA mode")
            
        # Размещаем подпись в левом нижнем углу
        signature_pos = (SPACING, CANVAS_HEIGHT - signature_height - SPACING)
        canvas.paste(signature, signature_pos, signature)
        logger.info("Signature placed successfully")
        
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

        logger.info("Creating canvas")
        # Создаем белый холст
        canvas = Image.new('RGB', (CANVAS_WIDTH, CANVAS_HEIGHT), 'white')
        
        # Вычисляем размеры для фотографий (2 ряда по 3 фото)
        photo_width = (CANVAS_WIDTH - (4 * SPACING)) // 3
        photo_height = (CANVAS_HEIGHT - (4 * SPACING) - LOGO_SIZE[1]) // 2

        logger.info(f"Processing {len(photos)} photos")
        # Размещаем фотографии на холсте
        for i, photo in enumerate(photos):
            logger.info(f"Processing photo {i+1}")
            img = Image.open(photo)
            img = img.convert('RGB')
            
            # Сохраняем пропорции при ресайзе
            img.thumbnail((photo_width, photo_height), Image.Resampling.LANCZOS)
            
            # Вычисляем позицию для фото
            row = i // 3
            col = i % 3
            x = SPACING + col * (photo_width + SPACING)
            y = SPACING + row * (photo_height + SPACING)
            
            # Добавляем рамку
            bordered_img = Image.new('RGB', (img.width + 2*BORDER_WIDTH, img.height + 2*BORDER_WIDTH), BORDER_COLOR)
            bordered_img.paste(img, (BORDER_WIDTH, BORDER_WIDTH))
            
            # Размещаем фото на холсте
            canvas.paste(bordered_img, (x, y))
            logger.info(f"Photo {i+1} placed successfully")

        logger.info("Adding logo and signature")
        # Добавляем логотип и подпись
        add_logo_and_signature(canvas)

        logger.info("Saving result")
        # Сохраняем результат
        output = io.BytesIO()
        canvas.save(output, format='JPEG', quality=95)
        output.seek(0)
        
        logger.info("Sending response")
        return send_file(output, mimetype='image/jpeg')

    except Exception as e:
        logger.error(f"Error processing images: {str(e)}")
        return {'error': str(e)}, 500

if __name__ == '__main__':
    # Проверяем ассеты при запуске
    missing_assets = check_assets()
    if missing_assets:
        logger.warning(f"Missing assets: {', '.join(missing_assets)}")
    app.run(host='0.0.0.0', port=80) 