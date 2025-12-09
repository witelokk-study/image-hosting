FROM python:3.14-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir \
    "aio-pika>=9.4.1,<10.0.0" \
    "minio>=7.2.7,<8.0.0" \
    "pillow>=10.4.0,<11.0.0" \
    "pydantic-settings>=2.6.1,<3.0.0"

COPY preview ./preview

CMD ["python", "-m", "preview.main"]
