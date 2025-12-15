# Используйте официальный образ Python 3.14 (как только появится)
FROM python:3.14-slim

WORKDIR /app

# Копируем зависимости отдельно — для кэширования слоя
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# (Опционально) создаем непривилегированного пользователя
# RUN useradd --create-home --shell /bin/bash appuser && chown -R appuser:appuser /app
# USER appuser

#CMD ["python", "run_server.py"]