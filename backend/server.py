"""
AI NOVA 백엔드 서버

FastAPI 기반 뉴스 질의응답 시스템 API 서버를 제공합니다.
"""

import os
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv

# 프로젝트 루트 디렉토리 찾기
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 환경변수 로드 (프로젝트 루트의 .env 파일)
load_dotenv(PROJECT_ROOT / ".env")

from backend.utils.logger import setup_logger
from backend.api.routes.stock_calendar_routes import router as stock_calendar_router
# 기존 전체 라우터 (향후 삭제 예정)
from backend.api.routes.news_routes import router as news_router

# 분리된 새 라우터들
from backend.api.routes.latest_news_routes import router as latest_news_router
# TODO: 다음 분리된 라우터들도 추가
# from backend.api.routes.company_news_routes import router as company_news_router
# from backend.api.routes.search_routes import router as search_routes_router
# from backend.api.routes.related_questions_routes import router as related_questions_router
# from backend.api.routes.ai_summary_routes import router as ai_summary_router
# from backend.api.routes.watchlist_routes import router as watchlist_router

# 로거 설정
logger = setup_logger("server")

# 앱 인스턴스 생성
app = FastAPI(
    title="AI NOVA API",
    description="빅카인즈 기반 뉴스 질의응답 시스템 API",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인으로 제한해야 합니다
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(stock_calendar_router)

# 기존 전체 라우터 등록 (향후 모든 기능이 분리되면 삭제)
app.include_router(news_router)

# 분리된 새 라우터들 등록
app.include_router(latest_news_router)
# TODO: 분리된 라우터들도 추가
# app.include_router(company_news_router)
# app.include_router(search_routes_router)
# app.include_router(related_questions_router)
# app.include_router(ai_summary_router)
# app.include_router(watchlist_router)

@app.get("/api/health")
async def health_check():
    """서버 상태 체크 API"""
    return {
        "status": "ok",
        "version": app.version,
    }

@app.get("/")
async def root():
    """루트 경로 리디렉션"""
    return {"message": "AI NOVA API 서버에 오신 것을 환영합니다. API 문서는 /api/docs에서 확인하세요."}

def start():
    """서버 시작 함수"""
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    
    logger.info(f"서버 시작 중... (host: {host}, port: {port})")
    
    # 서버 시작
    uvicorn.run(
        "backend.server:app",
        host=host,
        port=port,
        reload=True,
        log_level="info",
    )

if __name__ == "__main__":
    # 직접 실행 시 서버 시작
    start() 