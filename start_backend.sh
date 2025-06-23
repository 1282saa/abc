#!/bin/bash

# 백엔드 서버 시작 스크립트

echo "AI NOVA 백엔드 서버를 시작합니다..."

# 스크립트가 실행되는 디렉토리로 이동
cd "$(dirname "$0")"

# Python 가상 환경이 있다면 활성화
if [ -d "venv" ]; then
    echo "가상 환경을 활성화합니다..."
    source venv/bin/activate
elif [ -d ".venv" ]; then
    echo "가상 환경을 활성화합니다..."
    source .venv/bin/activate
fi

# 필요한 환경 변수 확인
if [ ! -f ".env" ]; then
    echo "⚠️  .env 파일이 없습니다!"
    echo "📝 .env.example을 복사하여 .env 파일을 생성하고 API 키를 설정해주세요:"
    echo "   cp .env.example .env"
    exit 1
fi

# 백엔드 서버 실행
echo "🚀 백엔드 서버를 포트 8080에서 시작합니다..."
python backend/server.py