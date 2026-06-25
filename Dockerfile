FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Asia/Shanghai

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

EXPOSE 80

CMD ["gunicorn", "--preload", "--bind", "0.0.0.0:80", "--workers", "2", "--threads", "4", "--timeout", "60", "run:app"]
