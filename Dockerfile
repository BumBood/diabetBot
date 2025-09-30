FROM python:3.12-alpine

WORKDIR /app


# Копируем requirements и устанавливаем зависимости
COPY requirements.txt .
RUN pip install -r requirements.txt

# Копируем код приложения
COPY . .

# Команда по умолчанию
CMD ["python", "main.py"]
