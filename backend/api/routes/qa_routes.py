"""
질의응답 시스템 API 라우트

질의응답, 요약, 타임라인 생성 등 뉴스 질의응답 시스템의 API 엔드포인트를 정의합니다.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, validator
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, date
import asyncio
from pathlib import Path
import os
import sys
import json

# 프로젝트 루트 디렉토리 찾기
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.utils.logger import setup_logger
from backend.services.qa import QAEngine

# 모델 정의
class SearchParams(BaseModel):
    """검색 파라미터 모델"""
    date_range: Optional[List[str]] = Field(
        default=None, 
        description="검색 날짜 범위 ['시작일', '종료일'] (YYYY-MM-DD 형식)"
    )
    provider: Optional[List[str]] = Field(
        default=None, 
        description="언론사 코드 또는 이름 리스트"
    )
    category: Optional[List[str]] = Field(
        default=None, 
        description="카테고리 코드 리스트"
    )
    n_results: Optional[int] = Field(
        default=5, 
        description="검색 결과 수",
        ge=1, 
        le=50
    )
    
    @validator('date_range')
    def validate_date_range(cls, v):
        """날짜 범위 유효성 검사"""
        if v is None:
            return v
        
        if len(v) != 2:
            raise ValueError("date_range는 [시작일, 종료일] 형식이어야 합니다")
        
        for date_str in v:
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                raise ValueError(f"날짜 형식 오류: {date_str}. YYYY-MM-DD 형식이어야 합니다")
        
        return v

class QueryRequest(BaseModel):
    """질의 요청 모델"""
    query: str = Field(..., description="사용자 질의")
    search_params: Optional[SearchParams] = Field(
        default_factory=SearchParams, 
        description="검색 파라미터"
    )
    stream: Optional[bool] = Field(
        default=False, 
        description="스트리밍 응답 여부"
    )

# API 라우터 생성
router = APIRouter(prefix="/api/qa", tags=["질의응답"])

# QA 엔진 인스턴스 (FastAPI Depends로 사용 가능하게)
def get_qa_engine():
    """QA 엔진 인스턴스 가져오기"""
    return QAEngine()

# 엔드포인트 정의
@router.post("/query")
async def query_endpoint(
    request: QueryRequest,
    qa_engine: QAEngine = Depends(get_qa_engine)
):
    """질의응답 API 엔드포인트
    
    사용자 질의를 처리하고 관련 뉴스 기사를 기반으로 응답을 생성합니다.
    """
    logger = setup_logger("api.qa.query")
    logger.info(f"질의 받음: '{request.query}'")
    
    try:
        if request.stream:
            # 스트리밍 응답 처리
            async def stream_response():
                async for chunk in qa_engine.process_query(
                    query=request.query,
                    stream=True,
                    search_params=request.search_params.dict(exclude_none=True)
                ):
                    yield f"data: {json.dumps({'chunk': chunk})}\n\n"
            
            return StreamingResponse(
                stream_response(),
                media_type="text/event-stream"
            )
        else:
            # 일반 응답 처리
            result = await qa_engine.process_query(
                query=request.query,
                stream=False,
                search_params=request.search_params.dict(exclude_none=True)
            )
            
            return result
            
    except Exception as e:
        logger.error(f"질의 처리 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"질의 처리 중 오류 발생: {str(e)}")

@router.post("/summarize")
async def summarize_endpoint(
    request: QueryRequest,
    qa_engine: QAEngine = Depends(get_qa_engine)
):
    """뉴스 요약 API 엔드포인트
    
    주제 또는 키워드에 대한 뉴스 기사들을 종합적으로 요약합니다.
    """
    logger = setup_logger("api.qa.summarize")
    logger.info(f"요약 요청 받음: '{request.query}'")
    
    try:
        result = await qa_engine.generate_summary(
            query=request.query,
            search_params=request.search_params.dict(exclude_none=True)
        )
        
        return result
            
    except Exception as e:
        logger.error(f"요약 생성 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"요약 생성 중 오류 발생: {str(e)}")

@router.post("/timeline")
async def timeline_endpoint(
    request: QueryRequest,
    qa_engine: QAEngine = Depends(get_qa_engine)
):
    """타임라인 생성 API 엔드포인트
    
    주제 또는 이슈에 대한 시간 순서별 발전 과정을 분석하여 타임라인을 생성합니다.
    """
    logger = setup_logger("api.qa.timeline")
    logger.info(f"타임라인 요청 받음: '{request.query}'")
    
    try:
        result = await qa_engine.generate_timeline(
            query=request.query,
            search_params=request.search_params.dict(exclude_none=True)
        )
        
        return result
            
    except Exception as e:
        logger.error(f"타임라인 생성 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"타임라인 생성 중 오류 발생: {str(e)}")

@router.get("/status")
async def status_endpoint(qa_engine: QAEngine = Depends(get_qa_engine)):
    """시스템 상태 API 엔드포인트
    
    QA 시스템의 현재 상태와 통계를 조회합니다.
    """
    try:
        # 벡터 DB 상태 가져오기
        vector_db_status = qa_engine.get_vector_db_status()
        
        return {
            "status": "running",
            "vector_db": vector_db_status,
            "timestamp": datetime.now().isoformat()
        }
            
    except Exception as e:
        logger = setup_logger("api.qa.status")
        logger.error(f"상태 조회 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"상태 조회 중 오류 발생: {str(e)}") 