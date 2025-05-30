#!/bin/bash

# AI NOVA 콘텐츠 제작자 시스템 시작 스크립트

# 환경 변수 로드
if [ -f "./config/.env" ]; then
    export $(grep -v '^#' ./config/.env | xargs)
fi

# 필요한 디렉토리 생성
mkdir -p output
mkdir -p workflows
mkdir -p workflows/templates
mkdir -p cache
mkdir -p logs

# 서버 시작
echo "Starting AI NOVA backend server..."
cd app/backend
python server.py &
SERVER_PID=$!
cd ../..

# 서버가 시작될 때까지 잠시 대기
sleep 3

# 프론트엔드 시작
echo "Starting Content Creator frontend..."
cd app/frontend
streamlit run content_creator_app.py --server.port 8501 --server.address 0.0.0.0 &
FRONTEND_PID=$!
cd ../..

echo "AI NOVA Content Creator is running!"
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop both services"

# 종료 처리
function cleanup {
    echo "Stopping services..."
    kill $SERVER_PID
    kill $FRONTEND_PID
    echo "Services stopped"
    exit 0
}

trap cleanup SIGINT

# 메인 프로세스 유지
wait