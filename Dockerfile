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

# Копирование кода приложения
COPY . .

# Переменная окружения для порта
ENV PORT=8080

# Открываем порт
EXPOSE ${PORT}

# Запускаем приложение через gunicorn с worker_class=sync
CMD gunicorn --bind 0.0.0.0:${PORT} --worker-class=sync app:app 