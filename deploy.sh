#!/bin/bash

# Google Cloud Run 배포 스크립트
set -e

# 설정 변수
PROJECT_ID="your-project-id"  # 실제 프로젝트 ID로 변경하세요
SERVICE_NAME="ainova-app"
REGION="asia-northeast3"  # 서울 리전
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

echo "🚀 Google Cloud Run 배포 시작..."

# 1. 프로젝트 설정
echo "📋 프로젝트 설정 중..."
gcloud config set project $PROJECT_ID

# 2. 필요한 API 활성화
echo "🔧 필요한 API 활성화 중..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

# 3. 이미지 빌드 및 푸시
echo "🏗️ Docker 이미지 빌드 중..."
gcloud builds submit --tag $IMAGE_NAME

# 4. 환경변수 파일 확인
if [ ! -f ".env.cloud" ]; then
    echo "❌ .env.cloud 파일이 없습니다. 먼저 환경변수 파일을 생성하세요."
    echo "예시: cp .env.example .env.cloud && vi .env.cloud"
    exit 1
fi

# 5. Cloud Run 배포
echo "☁️ Cloud Run에 배포 중..."
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --port 8080 \
  --memory 2Gi \
  --cpu 2 \
  --max-instances 10 \
  --env-vars-file .env.cloud

# 6. 배포 결과 확인
echo "✅ 배포 완료!"
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(status.url)')
echo "🌐 서비스 URL: $SERVICE_URL"
echo "🔍 Health Check: $SERVICE_URL/api/health"

# 7. 보안을 위해 환경변수 파일 삭제
read -p "환경변수 파일(.env.cloud)을 삭제하시겠습니까? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm .env.cloud
    echo "🗑️ 환경변수 파일이 삭제되었습니다."
fi

echo "🎉 배포가 성공적으로 완료되었습니다!"
echo "📖 API 문서: $SERVICE_URL/api/docs"