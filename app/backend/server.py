"""
AI NOVA 백엔드 서버

FastAPI 기반의 AI NOVA 백엔드 서버
"""

import os
import sys
from pathlib import Path
import asyncio
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv
from pydantic import BaseModel, Field
import logging
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# 프로젝트 루트 디렉토리 찾기
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 환경 변수 로드
env_path = PROJECT_ROOT / "config" / ".env"
load_dotenv(dotenv_path=env_path)

from src.modules.ainova_engine import AINOVAEngine
from src.utils.logger import setup_logger
from src.modules.content_creator.api import router as content_creator_router, init_app

# 로거 설정
logger = setup_logger("ainova.api")

# FastAPI 앱 생성
app = FastAPI(
    title="AI NOVA API",
    description="AI NOVA (키워드 중심 뉴스 클러스터링 및 종합 요약 시스템) API",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 배포에서는 명시적인 도메인 목록으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 서빙 설정 - 이미지 및 내보내기 파일 접근용
output_dir = os.path.join(PROJECT_ROOT, "output")
os.makedirs(output_dir, exist_ok=True)
app.mount("/output", StaticFiles(directory=output_dir), name="output")

# AI NOVA 엔진 인스턴스
ainova_instance = None

# 요청 모델
class SearchRequest(BaseModel):
    query: str = Field(..., description="검색어")
    start_date: str = Field(..., description="시작 날짜 (YYYY-MM-DD)")
    end_date: str = Field(..., description="종료 날짜 (YYYY-MM-DD)")
    provider: Optional[List[str]] = Field(None, description="언론사 코드 목록")
    category: Optional[List[str]] = Field(None, description="카테고리 코드 목록")
    max_results: int = Field(100, description="최대 검색 결과 수")

# AI NOVA 엔진 의존성
async def get_ainova_engine():
    global ainova_instance
    if ainova_instance is None:
        api_key = os.environ.get("BIGKINDS_API_KEY")
        if not api_key:
            logger.error("BIGKINDS_API_KEY가 설정되지 않았습니다.")
            raise HTTPException(
                status_code=500,
                detail="API 키 설정 오류"
            )
        
        ainova_instance = AINOVAEngine(api_key)
    
    return ainova_instance

# 콘텐츠 제작자 API 라우터 추가
app.include_router(content_creator_router)

# 다운로드 엔드포인트
@app.get("/download/{file_path:path}", response_class=FileResponse)
async def download_file(file_path: str):
    """파일 다운로드"""
    # 보안을 위해 경로 검증 및 제한
    full_path = os.path.join(output_dir, file_path)
    
    # 파일이 output_dir 내에 있는지 확인 (경로 탈출 방지)
    if not os.path.commonpath([full_path, output_dir]) == output_dir:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다")
    
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다")
    
    return FileResponse(full_path)

# 루트 경로
@app.get("/")
async def root():
    return {"message": "AI NOVA API에 오신 것을 환영합니다", "version": "1.0.0"}

# 서버 상태 확인
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "AI NOVA API"}

# 오늘의 이슈 API
@app.get("/api/today-issues")
async def get_today_issues(
    date: Optional[str] = None,
    top_n: int = Query(5, description="반환할 이슈 수"),
    ainova: AINOVAEngine = Depends(get_ainova_engine)
):
    """오늘의 주요 이슈 조회"""
    try:
        issues = await ainova.get_top_issues(date, top_n)
        return {"issues": issues, "count": len(issues)}
    except Exception as e:
        logger.error(f"오늘의 이슈 조회 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"오늘의 이슈 조회 중 오류가 발생했습니다: {str(e)}"
        )

# 오늘의 키워드 API
@app.get("/api/today-keywords")
async def get_today_keywords(
    ainova: AINOVAEngine = Depends(get_ainova_engine)
):
    """오늘의 키워드 조회"""
    try:
        keywords = await ainova.get_today_keywords()
        return keywords
    except Exception as e:
        logger.error(f"오늘의 키워드 조회 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"오늘의 키워드 조회 중 오류가 발생했습니다: {str(e)}"
        )

# 뉴스 검색 API
@app.post("/api/search")
async def search_news(
    request: SearchRequest,
    ainova: AINOVAEngine = Depends(get_ainova_engine)
):
    """뉴스 검색"""
    try:
        news_list = await ainova.search_news(
            query=request.query,
            start_date=request.start_date,
            end_date=request.end_date,
            provider=request.provider,
            category=request.category,
            max_results=request.max_results
        )
        
        return {"news": news_list, "count": len(news_list)}
    except Exception as e:
        logger.error(f"뉴스 검색 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"뉴스 검색 중 오류가 발생했습니다: {str(e)}"
        )

# 이슈 분석 API
@app.post("/api/analyze")
async def analyze_issue(
    request: SearchRequest,
    ainova: AINOVAEngine = Depends(get_ainova_engine)
):
    """이슈 종합 분석"""
    try:
        result = await ainova.analyze_issue(
            query=request.query,
            start_date=request.start_date,
            end_date=request.end_date,
            provider=request.provider,
            category=request.category,
            max_results=request.max_results
        )
        
        if "error" in result:
            raise HTTPException(
                status_code=400,
                detail=result["error"]
            )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"이슈 분석 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"이슈 분석 중 오류가 발생했습니다: {str(e)}"
        )

# 앱 실행
if __name__ == "__main__":
    host = os.environ.get("SERVER_HOST", "0.0.0.0")
    port = int(os.environ.get("SERVER_PORT", "8000"))
    
    uvicorn.run(
        "server:app",
        host=host,
        port=port,
        reload=True
    )