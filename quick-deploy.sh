#!/bin/bash

# 가장 간단한 .env 기반 배포 스크립트
set -e

PROJECT_ID="your-project-id"  # 실제 프로젝트 ID로 변경
SERVICE_NAME="ainova-app"
REGION="asia-northeast3"

echo "🚀 Quick Deploy with .env..."

# .env 파일을 gcloud 형식으로 변환
ENV_VARS=$(grep -v '^#' .env | grep -v '^$' | tr '\n' ',' | sed 's/,$//')

echo "📦 환경변수: $(echo "$ENV_VARS" | tr ',' '\n' | wc -l | xargs)개"

# 빌드 및 배포
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --port 8080 \
  --memory 2Gi \
  --cpu 2 \
  --set-env-vars "$ENV_VARS"

echo "✅ 배포 완료! URL: $(gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(status.url)')"