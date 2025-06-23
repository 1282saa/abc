"""
AI NOVA 백엔드 서버

FastAPI 기반 뉴스 질의응답 시스템 API 서버를 제공합니다.
"""

import os
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import logging
import httpx

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
from backend.api.routes.briefing_routes import router as briefing_router
from backend.api.routes.dashboard_routes import router as dashboard_router
# TODO: 다음 분리된 라우터들도 추가
# from backend.api.routes.company_news_routes import router as company_news_router
# from backend.api.routes.search_routes import router as search_routes_router
from backend.api.routes.related_questions_routes import router as related_questions_router
from backend.api.routes.proxy_routes import router as proxy_routes
from backend.api.routes.entity_routes import router as entity_router
from backend.api.routes.report_routes import router as report_router
from backend.api.routes.period_report_routes import router as period_report_router
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
app.include_router(briefing_router)
app.include_router(dashboard_router)
# TODO: 분리된 라우터들도 추가
# app.include_router(company_news_router)
# app.include_router(search_routes_router)
app.include_router(related_questions_router)
app.include_router(proxy_routes)
app.include_router(entity_router)
app.include_router(report_router)
app.include_router(period_report_router)
# app.include_router(ai_summary_router)
# app.include_router(watchlist_router)

# 예외 처리기
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception occurred")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "message": str(exc)},
    )

@app.get("/api/health")
async def health_check():
    """서버 상태 체크 API"""
    return {
        "status": "ok",
        "version": app.version,
    }

# 정적 파일 서빙 설정 (프론트엔드 빌드 결과물)
frontend_path = PROJECT_ROOT / "frontend" / "dist"
if frontend_path.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_path / "assets")), name="static")
    
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """프론트엔드 라우팅을 위한 모든 경로 처리"""
        # API 경로는 처리하지 않음
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not Found")
            
        # 정적 파일 경로 확인
        requested_path = frontend_path / full_path
        if requested_path.exists() and requested_path.is_file():
            return FileResponse(str(requested_path))
            
        # 존재하지 않는 경로는 index.html로 리다이렉트 (SPA 라우팅)
        return FileResponse(str(frontend_path / "index.html"))
else:
    logger.warning(f"프론트엔드 빌드 경로를 찾을 수 없습니다: {frontend_path}")
    
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