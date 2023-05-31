FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY data ./data

RUN useradd --create-home bot && mkdir outbox && chown bot outbox
USER bot

EXPOSE 8000
CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
ENV TRANSFORM_DATA=true
ENV WARM_CACHE=true
ENV CHECK_STATUS=true
ENV TRANSFORM_DATA=true
ENV WARM_CACHE=true