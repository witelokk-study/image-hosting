FROM python:3.14-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

RUN pip install --no-cache-dir "poetry>=1.7,<2.0"
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root --only main

COPY storage ./storage

EXPOSE 8000

CMD ["uvicorn", "storage.main:app", "--host", "0.0.0.0", "--port", "8000"]
