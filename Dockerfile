# ---------- Frontend ----------
FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci --only=production || npm install --only=production
COPY frontend/ ./
RUN npm run build

# ---------- Backend ----------
FROM python:3.11-slim AS final
WORKDIR /app

RUN apt-get update && apt-get install -y build-essential curl \
    && rm -rf /var/lib/apt/lists/* && apt-get clean

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

RUN mkdir -p logs

ENV HOST=0.0.0.0 \
    PYTHONPATH=/app \
    PYTHONUNBUFFERED=1

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/api/health || exit 1

EXPOSE 8080
CMD ["python", "-m", "backend.server"]
