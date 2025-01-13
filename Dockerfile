# Базовый образ Python
FROM python:3.11

# Устанавливаем зависимости системы
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем requirements.txt и устанавливаем зависимости Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY handlers/ ./handlers
COPY keyboards/ ./keyboards
COPY database/ ./database
COPY .env .
COPY docker-compose.yml .
COPY Dockerfile .
COPY bot.py .
COPY database.py .
COPY utils.py .

# Устанавливаем переменные окружения
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Указываем команду запуска
CMD ["python", "bot.py"]