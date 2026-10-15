# --- Build the web UI -------------------------------------------------------
FROM node:22-slim AS web
WORKDIR /web
COPY apps/web/package.json apps/web/package-lock.json ./
RUN npm ci
COPY apps/web/ ./
RUN npm run build

# --- API + static UI in one service -----------------------------------------
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/apps/api
WORKDIR /app
RUN pip install --no-cache-dir "numpy>=1.26,<3" "pydantic>=2,<3" "fastapi>=0.110.0" "uvicorn[standard]>=0.28.0"
COPY apps/api/ apps/api/
COPY datasets/ datasets/
COPY --from=web /web/dist apps/web/dist
RUN useradd --create-home app && mkdir -p data && chown app data
USER app
EXPOSE 8000
CMD ["sh", "-c", "uvicorn parallax.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
