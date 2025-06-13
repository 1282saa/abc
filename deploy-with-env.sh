#!/bin/bash

# .env 파일에서 모든 환경변수를 읽어서 Cloud Run에 배포하는 스크립트
set -e

# 설정 변수
PROJECT_ID="your-project-id"  # 실제 프로젝트 ID로 변경하세요
SERVICE_NAME="ainova-app"
REGION="asia-northeast3"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

echo "🚀 .env 파일 기반 Cloud Run 배포 시작..."

# .env 파일 확인
if [ ! -f ".env" ]; then
    echo "❌ .env 파일이 없습니다."
    exit 1
fi

# 1. .env 파일을 source로 로드
echo "📋 .env 파일에서 환경변수 로드 중..."
set -a  # 모든 변수를 자동으로 export
source .env
set +a

# 2. .env 파일에서 환경변수 문자열 생성
echo "🔧 환경변수 문자열 생성 중..."
ENV_VARS=""
while IFS='=' read -r key value || [ -n "$key" ]; do
    # 주석과 빈 줄 스킵
    if [[ $key =~ ^[[:space:]]*# ]] || [[ -z "$key" ]]; then
        continue
    fi
    
    # 앞뒤 공백 제거
    key=$(echo "$key" | xargs)
    value=$(echo "$value" | xargs)
    
    # 따옴표 제거
    value=${value#\"}
    value=${value%\"}
    
    # ENV_VARS 문자열에 추가
    if [ -z "$ENV_VARS" ]; then
        ENV_VARS="$key=$value"
    else
        ENV_VARS="$ENV_VARS,$key=$value"
    fi
    
    echo "  ✓ $key=***"  # 값은 보안상 숨김
done < .env

echo "📦 총 $(echo "$ENV_VARS" | tr ',' '\n' | wc -l | xargs)개의 환경변수 준비됨"

# 3. 프로젝트 설정
echo "📋 프로젝트 설정 중..."
gcloud config set project $PROJECT_ID

# 4. 이미지 빌드
echo "🏗️ Docker 이미지 빌드 중..."
gcloud builds submit --tag $IMAGE_NAME

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
  --set-env-vars "$ENV_VARS"

# 6. 배포 결과
echo "✅ 배포 완료!"
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(status.url)')
echo "🌐 서비스 URL: $SERVICE_URL"
echo "🔍 Health Check: $SERVICE_URL/api/health"
echo "📖 API 문서: $SERVICE_URL/api/docs"

echo "🎉 배포가 성공적으로 완료되었습니다!"