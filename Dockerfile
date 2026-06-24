FROM python:3.13-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY . .
RUN pip install -e .
EXPOSE 8000
CMD alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}