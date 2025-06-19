from flask import Flask, request, send_file, jsonify, make_response
from PIL import Image
import io
import logging
import os
import sys
from flask_cors import CORS
import requests
import parse
from parse.connection import register
import uuid
import json
from functools import wraps

# Конфигурация Back4App
BACK4APP_CONFIG = {
    'APP_ID': os.getenv('BACK4APP_APP_ID'),
    'CLIENT_KEY': os.getenv('BACK4APP_CLIENT_KEY'),
    'MASTER_KEY': os.getenv('BACK4APP_MASTER_KEY'),
    'SERVER_URL': 'https://parseapi.back4app.com'
}

app = Flask(__name__)
CORS(app)

# Настройка Parse
parse.initialize(
    BACK4APP_CONFIG['APP_ID'],
    BACK4APP_CONFIG['CLIENT_KEY'],
    master_key=BACK4APP_CONFIG['MASTER_KEY']
)
parse.serverURL = BACK4APP_CONFIG['SERVER_URL']

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Константы для путей
RESULTS_DIR = '/app/results'  # Изменено на абсолютный путь в корне контейнера
logger.info(f"Results directory path: {RESULTS_DIR}")

try:
    if not os.path.exists(RESULTS_DIR):
        os.makedirs(RESULTS_DIR, mode=0o777)
        logger.info(f"Created results directory at {RESULTS_DIR}")
    else:
        logger.info(f"Results directory already exists at {RESULTS_DIR}")
except Exception as e:
    logger.error(f"Error creating results directory: {str(e)}")
    # Попробуем создать в текущей директории
    RESULTS_DIR = os.path.join(os.getcwd(), 'results')
    logger.info(f"Falling back to current directory: {RESULTS_DIR}")
    if not os.path.exists(RESULTS_DIR):
        os.makedirs(RESULTS_DIR, mode=0o777)

# Константы для холста
CANVAS_HEIGHT = 1958  # высота холста
CANVAS_WIDTH = 1785   # ширина холста

# Отступы для фотографий (обновлено 2024)
PHOTO_MARGIN_LEFT = 107  # отступ слева
PHOTO_MARGIN_TOP = 85    # отступ сверху
PHOTO_GAP_HORIZONTAL = 166  # отступ между фото по горизонтали
PHOTO_GAP_VERTICAL = 252    # отступ между фото по вертикали

# Отступы для лого и подписи
LOGO_MARGIN_LEFT = 462    # отступ слева для лого
LOGO_TO_BOTTOM_PHOTO = 204  # отступ от нижнего фото до лого
TEXT_MARGIN_LEFT = 144    # отступ между лого и текстом
TEXT_TO_BOTTOM_PHOTO = 200  # отступ от нижнего фото до подписи

# Получаем абсолютный путь к директории приложения
APP_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(APP_DIR, 'assets')

def calculate_bottom_photo_y(photo_height):
    """Вычисляет Y-координату нижнего ряда фотографий"""
    return PHOTO_MARGIN_TOP + photo_height + PHOTO_GAP_VERTICAL + photo_height

def add_logo_and_signature(canvas, bottom_photo_y, photo_height):
    """Добавляет логотип и подпись на холст"""
    try:
        # Загрузка логотипа
        logo = Image.open(os.path.join(ASSETS_DIR, 'logo.png'))
        if logo.mode != 'RGBA':
            logo = logo.convert('RGBA')
            
        # Размещаем логотип относительно нижнего ряда фотографий
        logo_y = bottom_photo_y + LOGO_TO_BOTTOM_PHOTO
        logo_pos = (LOGO_MARGIN_LEFT, logo_y)
        canvas.paste(logo, logo_pos, logo)
        
        # Загрузка подписи
        signature = Image.open(os.path.join(ASSETS_DIR, 'Signature.png'))
        if signature.mode != 'RGBA':
            signature = signature.convert('RGBA')
            
        # Размещаем подпись справа от логотипа и относительно нижнего ряда фотографий
        signature_x = logo_pos[0] + logo.width + TEXT_MARGIN_LEFT
        signature_y = bottom_photo_y + TEXT_TO_BOTTOM_PHOTO
        canvas.paste(signature, (signature_x, signature_y), signature)
        
    except Exception as e:
        logger.error(f"Error adding logo and signature: {str(e)}")
        raise

def force_json_response(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        response = f(*args, **kwargs)
        # Если ответ уже является кортежем (response, status_code)
        if isinstance(response, tuple):
            data, status_code = response
            response = jsonify(data)
            response.status_code = status_code
        # Если ответ является словарем
        elif isinstance(response, dict):
            response = jsonify(response)
        # Принудительно устанавливаем тип контента
        response.headers['Content-Type'] = 'application/json'
        return response
    return decorated_function

@app.route('/create', methods=['POST'])
def create_image():
    try:
        image_data = None
        
        if 'photo' in request.files:
            photo = request.files['photo']
            image_data = photo.read()
            logger.info(f"Received photo from file: {photo.filename}")
        elif 'photo_url' in request.form:
            photo_url = request.form['photo_url']
            logger.info(f"Downloading photo from URL: {photo_url}")
            response = requests.get(photo_url)
            if response.status_code == 200:
                image_data = response.content
            else:
                return jsonify({'error': f'Failed to download image from URL: {response.status_code}'}), 400
        else:
            return jsonify({'error': 'No photo or photo_url provided'}), 400
            
        # Создаем объект изображения из данных
        img_buffer = io.BytesIO(image_data)
        img = Image.open(img_buffer).convert('RGB')
        img_width = img.width
        img_height = img.height
        logger.info(f"Image dimensions: {img_width}x{img_height}")
        
        # Создаем белый холст
        canvas = Image.new('RGB', (CANVAS_WIDTH, CANVAS_HEIGHT), 'white')
        
        # Вычисляем Y-координату нижнего ряда фотографий
        bottom_photo_y = calculate_bottom_photo_y(img_height)
        
        # Размещаем фотографии на холсте
        for i in range(6):
            row = i // 3
            col = i % 3
            x = PHOTO_MARGIN_LEFT + col * (img_width + PHOTO_GAP_HORIZONTAL)
            y = PHOTO_MARGIN_TOP + row * (img_height + PHOTO_GAP_VERTICAL)
            canvas.paste(img, (x, y))
            logger.info(f"Placed photo {i+1} at position ({x}, {y})")

        # Добавляем логотип и подпись
        add_logo_and_signature(canvas, bottom_photo_y, img_height)
        logger.info("Added logo and signature")

        try:
            # Генерируем уникальное имя файла
            filename = f"{uuid.uuid4()}.jpg"
            filepath = os.path.join(RESULTS_DIR, filename)
            logger.info(f"Saving file to: {filepath}")
            
            # Проверяем права на запись
            if not os.access(os.path.dirname(filepath), os.W_OK):
                logger.error(f"No write access to directory: {os.path.dirname(filepath)}")
                return jsonify({'error': 'No write access to results directory'}), 500
            
            # Сохраняем результат
            canvas.save(filepath, format='JPEG', quality=95)
            logger.info(f"Successfully saved result to {filepath}")
            
            # Формируем публичный URL
            public_url = f"https://imageapi-nrkypima.b4a.run/image/{filename}"
            logger.info(f"Generated public URL: {public_url}")
            
            return jsonify({
                'url': public_url,
                'status': 'success',
                'filepath': filepath
            })

        except Exception as e:
            logger.error(f"Error saving file: {str(e)}")
            return jsonify({'error': f'Failed to save file: {str(e)}'}), 500

    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/image/<filename>')
def get_image(filename):
    try:
        filepath = os.path.join(RESULTS_DIR, filename)
        logger.info(f"Requested file: {filepath}")
        
        if not os.path.exists(filepath):
            logger.error(f"File not found: {filepath}")
            return jsonify({'error': 'File not found'}), 404
            
        if not os.access(filepath, os.R_OK):
            logger.error(f"No read access to file: {filepath}")
            return jsonify({'error': 'No read access to file'}), 403
            
        response = make_response(send_file(filepath, mimetype='image/jpeg'))
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
        
    except Exception as e:
        logger.error(f"Error serving result file: {str(e)}")
        return jsonify({'error': f'Error serving file: {str(e)}'}), 500

@app.route('/resize', methods=['POST'])
def resize_images():
    try:
        image_data = None
        
        if 'photo' in request.files:
            photo = request.files['photo']
            image_data = photo.read()
            logger.info(f"Received photo from file: {photo.filename}")
        elif 'photo_url' in request.form:
            photo_url = request.form['photo_url']
            logger.info(f"Downloading photo from URL: {photo_url}")
            response = requests.get(photo_url)
            if response.status_code == 200:
                image_data = response.content
            else:
                response = make_response(json.dumps({
                    'error': f'Failed to download image from URL: {response.status_code}'
                }))
                response.headers['Content-Type'] = 'application/json'
                response.status_code = 400
                return response
        else:
            response = make_response(json.dumps({
                'error': 'No photo or photo_url provided'
            }))
            response.headers['Content-Type'] = 'application/json'
            response.status_code = 400
            return response
            
        # Создаем объект изображения из данных
        img_buffer = io.BytesIO(image_data)
        img = Image.open(img_buffer).convert('RGB')
        img_width = img.width
        img_height = img.height
        logger.info(f"Image dimensions: {img_width}x{img_height}")
        
        # Создаем белый холст
        canvas = Image.new('RGB', (CANVAS_WIDTH, CANVAS_HEIGHT), 'white')
        
        # Вычисляем Y-координату нижнего ряда фотографий
        bottom_photo_y = calculate_bottom_photo_y(img_height)
        
        # Размещаем фотографии на холсте
        for i in range(6):
            row = i // 3
            col = i % 3
            x = PHOTO_MARGIN_LEFT + col * (img_width + PHOTO_GAP_HORIZONTAL)
            y = PHOTO_MARGIN_TOP + row * (img_height + PHOTO_GAP_VERTICAL)
            canvas.paste(img, (x, y))
            logger.info(f"Placed photo {i+1} at position ({x}, {y})")

        # Добавляем логотип и подпись
        add_logo_and_signature(canvas, bottom_photo_y, img_height)
        logger.info("Added logo and signature")

        try:
            # Генерируем уникальное имя файла
            filename = f"{uuid.uuid4()}.jpg"
            filepath = os.path.join(RESULTS_DIR, filename)
            logger.info(f"Saving file to: {filepath}")
            
            # Проверяем права на запись
            if not os.access(os.path.dirname(filepath), os.W_OK):
                logger.error(f"No write access to directory: {os.path.dirname(filepath)}")
                response = make_response(json.dumps({
                    'error': 'No write access to results directory'
                }))
                response.headers['Content-Type'] = 'application/json'
                response.status_code = 500
                return response
            
            # Сохраняем результат
            canvas.save(filepath, format='JPEG', quality=95)
            logger.info(f"Successfully saved result to {filepath}")
            
            # Формируем публичный URL
            public_url = f"https://imageapi-nrkypima.b4a.run/results/{filename}"
            logger.info(f"Generated public URL: {public_url}")
            
            # Создаем ответ
            response = make_response(json.dumps({
                'url': public_url,
                'status': 'success',
                'filepath': filepath
            }))
            response.headers['Content-Type'] = 'application/json'
            return response

        except Exception as e:
            logger.error(f"Error saving file: {str(e)}")
            response = make_response(json.dumps({
                'error': f'Failed to save file: {str(e)}'
            }))
            response.headers['Content-Type'] = 'application/json'
            response.status_code = 500
            return response

    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        response = make_response(json.dumps({
            'error': str(e)
        }))
        response.headers['Content-Type'] = 'application/json'
        response.status_code = 500
        return response

@app.route('/results/<filename>')
def get_result(filename):
    try:
        filepath = os.path.join(RESULTS_DIR, filename)
        logger.info(f"Requested file: {filepath}")
        
        if not os.path.exists(filepath):
            logger.error(f"File not found: {filepath}")
            return jsonify({'error': 'File not found'}), 404
            
        if not os.access(filepath, os.R_OK):
            logger.error(f"No read access to file: {filepath}")
            return jsonify({'error': 'No read access to file'}), 403
            
        response = make_response(send_file(filepath, mimetype='image/jpeg'))
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
        
    except Exception as e:
        logger.error(f"Error serving result file: {str(e)}")
        return jsonify({'error': f'Error serving file: {str(e)}'}), 500

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    response.headers.add('User-Agent', 'PhotoAPI/1.0')
    return response

if __name__ == '__main__':
    # Выводим информацию о текущей директории и правах доступа при запуске
    logger.info(f"Current working directory: {os.getcwd()}")
    logger.info(f"Results directory: {RESULTS_DIR}")
    logger.info(f"Can write to results directory: {os.access(RESULTS_DIR, os.W_OK)}")
    app.run(host='0.0.0.0', port=80) 