FROM python:3.9-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Установка зависимостей Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Создаем директорию assets и копируем файлы
COPY assets /app/assets/

# Копируем файл приложения
COPY app.py .

# Проверяем наличие файлов
RUN ls -la /app/assets/

# Устанавливаем шрифт DejaVu Sans (стандартный шрифт, который часто доступен в Linux)
RUN apt-get update && apt-get install -y \
    fonts-dejavu \
    && rm -rf /var/lib/apt/lists/*

# Копируем путь к шрифту в переменную окружения
ENV FONT_PATH=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf

# Переменная окружения для порта
ENV PORT=8080

# Открываем порт
EXPOSE ${PORT}

# Запускаем приложение через gunicorn
CMD gunicorn --bind 0.0.0.0:${PORT} app:app 