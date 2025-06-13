#!/bin/bash

# 안전한 .env 기반 배포 스크립트 (검증 포함)
set -e

PROJECT_ID="your-project-id"  # 실제 프로젝트 ID로 변경
SERVICE_NAME="ainova-app"
REGION="asia-northeast3"

echo "🚀 Safe Deploy with Environment Validation..."

# 필수 환경변수 목록
REQUIRED_VARS=(
    "BIGKINDS_KEY_GENERAL"
    "BIGKINDS_KEY_SEOUL"
    "OPENAI_API_KEY"
    "HOST"
    "PORT"
)

# .env 파일 존재 확인
if [ ! -f ".env" ]; then
    echo "❌ .env 파일이 없습니다."
    exit 1
fi

# .env 파일 로드
echo "📋 환경변수 로드 중..."
set -a
source .env
set +a

# 필수 환경변수 검증
echo "🔍 필수 환경변수 검증 중..."
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ 필수 환경변수 $var 가 설정되지 않았습니다."
        exit 1
    else
        echo "  ✓ $var"
    fi
done

# API 키 형식 검증
if [[ ! $BIGKINDS_KEY_GENERAL =~ ^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$ ]]; then
    echo "❌ BIGKINDS_KEY_GENERAL 형식이 올바르지 않습니다."
    exit 1
fi

if [[ ! $BIGKINDS_KEY_SEOUL =~ ^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$ ]]; then
    echo "❌ BIGKINDS_KEY_SEOUL 형식이 올바르지 않습니다."
    exit 1
fi

echo "✅ 환경변수 검증 완료!"

# .env 파일을 gcloud 형식으로 변환 (주석 및 빈 줄 제외)
ENV_VARS=$(grep -v '^#' .env | grep -v '^$' | sed 's/[[:space:]]*=[[:space:]]*/=/' | tr '\n' ',' | sed 's/,$//')

echo "📦 환경변수 개수: $(echo "$ENV_VARS" | tr ',' '\n' | wc -l | xargs)개"

# 프로젝트 설정
gcloud config set project $PROJECT_ID

# Docker 이미지 빌드
echo "🏗️ Docker 이미지 빌드 중..."
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME

# Cloud Run 배포
echo "☁️ Cloud Run 배포 중..."
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --port 8080 \
  --memory 2Gi \
  --cpu 2 \
  --max-instances 10 \
  --set-env-vars "$ENV_VARS"

# 배포 후 Health Check
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(status.url)')
echo "🌐 서비스 URL: $SERVICE_URL"

echo "🔍 Health Check 수행 중..."
if curl -f "$SERVICE_URL/api/health" > /dev/null 2>&1; then
    echo "✅ Health Check 성공!"
else
    echo "⚠️ Health Check 실패 - 로그를 확인하세요."
fi

echo "📖 API 문서: $SERVICE_URL/api/docs"
echo "🎉 배포가 성공적으로 완료되었습니다!"