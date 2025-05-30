#!/bin/bash

# Docker 컨테이너 엔트리포인트 스크립트

# 디렉토리 생성
mkdir -p cache
mkdir -p logs/api

# 모드 확인
MODE=${MODE:-"all"}

# 종료 시 자식 프로세스 종료 설정
trap 'kill $(jobs -p)' EXIT

# 모드에 따른 서비스 실행
if [ "$MODE" = "backend" ] || [ "$MODE" = "all" ]; then
    echo "Starting backend server..."
    cd app/backend
    python server.py &
    cd ../..
fi

if [ "$MODE" = "frontend" ] || [ "$MODE" = "all" ]; then
    echo "Starting frontend server..."
    cd app/frontend
    streamlit run app.py --server.address=0.0.0.0 --server.port=8501 &
    cd ../..
fi

# 모든 백그라운드 프로세스 대기
wait