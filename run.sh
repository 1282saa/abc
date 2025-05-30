#!/bin/bash

# AI NOVA 실행 스크립트

# 실행 모드 선택
if [ "$1" = "backend" ]; then
    echo "백엔드 서버 실행..."
    cd app/backend
    python server.py
elif [ "$1" = "frontend" ]; then
    echo "프론트엔드 서버 실행..."
    cd app/frontend
    streamlit run app.py
elif [ "$1" = "setup" ]; then
    echo "환경 설정..."
    
    # 가상환경 생성
    echo "가상환경 생성..."
    python -m venv venv
    
    # 가상환경 활성화
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    elif [ -f "venv/Scripts/activate" ]; then
        source venv/Scripts/activate
    else
        echo "가상환경 활성화 실패. 수동으로 활성화해주세요."
        exit 1
    fi
    
    # 의존성 설치
    echo "의존성 설치..."
    pip install --upgrade pip
    pip install -r requirements.txt
    pip install -r app/frontend/requirements.txt
    
    # 캐시 디렉터리 생성
    mkdir -p cache
    mkdir -p logs/api
    
    echo "환경 설정 완료!"
else
    echo "사용법: ./run.sh [backend|frontend|setup]"
    echo "  backend: 백엔드 서버 실행"
    echo "  frontend: 프론트엔드 서버 실행"
    echo "  setup: 환경 설정"
fi