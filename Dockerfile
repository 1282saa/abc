# Multi-stage build: Frontend
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend

# 프론트엔드 종속성 복사 및 설치
COPY frontend/package*.json ./
RUN npm ci --only=production

# 프론트엔드 소스 복사 및 빌드
COPY frontend/ ./
RUN npm run build

# Multi-stage build: Backend
FROM python:3.11-slim

WORKDIR /app

# 시스템 종속성 설치 (curl 포함 - health check용)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 백엔드 종속성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 백엔드 코드 복사
COPY backend/ ./backend/

# 프론트엔드 빌드 결과물 복사
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# 환경 변수 설정 (Cloud Run용)
ENV PORT=8080
ENV HOST=0.0.0.0
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 로그 디렉토리 생성
RUN mkdir -p logs

# Health check 추가
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/api/health || exit 1

# 포트 노출
EXPOSE 8080

# 서버 실행
CMD ["python", "-m", "backend.server"] 