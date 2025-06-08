"""
연관 질문 관련 API 라우터

키워드 기반 연관 질문 생성 및 조회 API를 제공합니다.
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta

from backend.api.dependencies.bigkinds import get_bigkinds_client
from backend.api.clients.bigkinds import BigKindsClient
from backend.utils.logger import setup_logger

logger = setup_logger("api.related_questions")
router = APIRouter(
    prefix="/api/related-questions",
    tags=["관련 질문"],
    responses={404: {"description": "Not found"}}
)

@router.get("/")
async def get_related_questions(
    keyword: str,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    max_questions: int = Query(10, ge=1, le=20),
    client: BigKindsClient = Depends(get_bigkinds_client)
):
    """
    키워드 기반 연관 질문 조회
    
    키워드 및 날짜 범위를 기반으로 의미 있는 연관 질문 목록을 생성합니다.
    
    Args:
        keyword: 검색 키워드
        date_from: 시작일 (YYYY-MM-DD)
        date_to: 종료일 (YYYY-MM-DD)
        max_questions: 반환할 최대 질문 수
        
    Returns:
        연관 질문 목록
    """
    logger.info(f"키워드 '{keyword}'에 대한 연관 질문 요청 - date_from: {date_from}, date_to: {date_to}")
    
    try:
        # 날짜 기본값 설정
        if not date_from:
            # 기본적으로 최근 30일
            date_from = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            
        if not date_to:
            # 기본적으로 오늘
            date_to = datetime.now().strftime("%Y-%m-%d")
        
        # 연관 질문 생성
        questions = client.generate_related_questions(
            keyword=keyword,
            date_from=date_from,
            date_to=date_to,
            max_questions=max_questions,
            cluster_count=5,
            max_recursion_depth=2,
            min_articles_per_query=3
        )
        
        return {
            "success": True,
            "keyword": keyword,
            "period": {
                "from": date_from,
                "to": date_to
            },
            "total_count": len(questions),
            "questions": questions
        }
    
    except Exception as e:
        logger.error(f"연관 질문 생성 오류: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"연관 질문 생성 중 오류가 발생했습니다: {str(e)}"
        ) 