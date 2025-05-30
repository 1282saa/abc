# AI NOVA Docker 이미지

# 베이스 이미지
FROM python:3.10-slim

# 작업 디렉토리 설정
WORKDIR /app

# 필요한 패키지 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# 환경변수 설정
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=UTF-8 \
    TZ=Asia/Seoul

# 의존성 설치
COPY requirements.txt .
COPY app/frontend/requirements.txt ./frontend-requirements.txt
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir -r frontend-requirements.txt

# 소스 코드 복사
COPY . .

# 기본 포트 노출
EXPOSE 8000 8501

# 시작 스크립트 설정
COPY ./entrypoint.sh .
RUN chmod +x ./entrypoint.sh

# 컨테이너 실행 명령
ENTRYPOINT ["./entrypoint.sh"]