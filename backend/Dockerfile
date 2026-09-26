# Backend: Flask API serving the serialized SuperKart model
FROM python:3.9-slim

WORKDIR /app

# Install dependencies first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code + serialized model
COPY . .

EXPOSE 7860

# Gunicorn: production WSGI server, 4 workers
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:7860", "app:superkart_api"]
