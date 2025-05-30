"""
QA 시스템 API 라우트

QA 시스템을 위한 FastAPI 라우트를 제공합니다.
질의응답, 요약, 타임라인 생성 등의 엔드포인트를 포함합니다.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Body, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional, Union
import asyncio
import json
from datetime import datetime, timedelta
import time
import os
from functools import lru_cache

# 프로젝트 루트 디렉토리 찾기
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.logger import setup_logger
from src.modules.qa_system import QAEngine, VectorDB, EmbeddingService, DocumentProcessor

# 모델 정의
class QueryRequest(BaseModel):
    """질의 요청 모델"""
    query: str = Field(..., description="사용자 질문")
    query_type: Optional[str] = Field(None, description="질의 유형 (qa, summarize, timeline)")
    stream: bool = Field(False, description="스트리밍 응답 여부")
    search_params: Optional[Dict[str, Any]] = Field(None, description="검색 파라미터")

class DateRangeRequest(BaseModel):
    """날짜 범위 요청 모델"""
    start_date: str = Field(..., description="시작 날짜 (YYYY-MM-DD)")
    end_date: str = Field(..., description="종료 날짜 (YYYY-MM-DD)")

class NewsDocument(BaseModel):
    """뉴스 문서 모델"""
    news_id: Optional[str] = Field(None, description="뉴스 ID")
    title: str = Field(..., description="뉴스 제목")
    content: str = Field(..., description="뉴스 내용")
    provider: Optional[str] = Field(None, description="뉴스 제공자")
    date: Optional[str] = Field(None, description="뉴스 날짜 (YYYY-MM-DD)")
    url: Optional[str] = Field(None, description="뉴스 URL")
    category: Optional[str] = Field(None, description="뉴스 카테고리")

class DocumentsRequest(BaseModel):
    """문서 추가 요청 모델"""
    documents: List[NewsDocument] = Field(..., description="추가할 뉴스 문서 리스트")

logger = setup_logger("qa.routes")

# QA 엔진 싱글턴 생성
@lru_cache()
def get_qa_engine():
    """QA 엔진 싱글턴 반환"""
    logger.info("QA 엔진 싱글턴 생성")
    
    # 설정 로드
    # TODO: 설정 파일에서 로드하는 방식으로 변경
    config = {
        "default_search_results": 5,
        "max_context_items": 8
    }
    
    # 모듈 생성
    vector_db = VectorDB()
    embedding_service = EmbeddingService()
    document_processor = DocumentProcessor()
    
    # QA 엔진 생성
    qa_engine = QAEngine(
        vector_db=vector_db,
        embedding_service=embedding_service,
        document_processor=document_processor,
        config=config
    )
    
    return qa_engine

# 라우터 생성
router = APIRouter(
    prefix="/api/qa",
    tags=["qa"],
    responses={404: {"description": "Not found"}}
)

@router.post("/query")
async def process_query(request: QueryRequest):
    """
    질의에 대한 응답 생성
    
    질의 유형에 따라 다른 처리가 적용됩니다:
    - qa: 일반 질의응답
    - summarize: 뉴스 요약
    - timeline: 시간순 타임라인 생성
    """
    qa_engine = get_qa_engine()
    
    start_time = time.time()
    logger.info(f"질의 API 호출: '{request.query}', 유형: {request.query_type or '자동'}")
    
    try:
        # 스트리밍 응답
        if request.stream:
            async def stream_response():
                response_generator = await qa_engine.process_query(
                    query=request.query,
                    stream=True,
                    query_type=request.query_type,
                    search_params=request.search_params
                )
                
                # 스트리밍 시작 마커
                yield "data: {\"status\": \"started\"}\n\n"
                
                async for chunk in response_generator:
                    if chunk:
                        # 응답 청크를 SSE 형식으로 전송
                        yield f"data: {json.dumps({'chunk': chunk})}\n\n"
                
                # 스트리밍 종료 마커
                elapsed_time = time.time() - start_time
                yield f"data: {json.dumps({'status': 'completed', 'time': elapsed_time})}\n\n"
            
            return StreamingResponse(
                stream_response(),
                media_type="text/event-stream"
            )
        
        # 일반 응답
        else:
            result = await qa_engine.process_query(
                query=request.query,
                stream=False,
                query_type=request.query_type,
                search_params=request.search_params
            )
            
            # 처리 시간 추가
            elapsed_time = time.time() - start_time
            result["processing_time"] = elapsed_time
            
            return result
            
    except Exception as e:
        logger.error(f"질의 처리 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"질의 처리 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/summarize")
async def generate_summary(request: QueryRequest):
    """뉴스 요약 생성"""
    qa_engine = get_qa_engine()
    
    # 요약 유형으로 설정
    request.query_type = "summarize"
    
    try:
        result = await qa_engine.generate_summary(
            query=request.query,
            search_params=request.search_params
        )
        return result
        
    except Exception as e:
        logger.error(f"요약 생성 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"요약 생성 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/timeline")
async def generate_timeline(request: QueryRequest):
    """시간순 타임라인 생성"""
    qa_engine = get_qa_engine()
    
    # 타임라인 유형으로 설정
    request.query_type = "timeline"
    
    try:
        result = await qa_engine.generate_timeline(
            query=request.query,
            search_params=request.search_params
        )
        return result
        
    except Exception as e:
        logger.error(f"타임라인 생성 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"타임라인 생성 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/documents")
async def add_documents(request: DocumentsRequest):
    """뉴스 문서 추가"""
    qa_engine = get_qa_engine()
    
    try:
        # 문서 형식 변환
        documents = [doc.dict() for doc in request.documents]
        
        # 문서 추가
        added_count = await qa_engine.add_documents(documents)
        
        return {
            "status": "success",
            "message": f"{added_count}개 문서가 추가되었습니다.",
            "added_count": added_count
        }
        
    except Exception as e:
        logger.error(f"문서 추가 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"문서 추가 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/status")
async def get_status():
    """QA 시스템 상태 조회"""
    qa_engine = get_qa_engine()
    
    try:
        # 벡터 DB 상태 조회
        vector_db_status = qa_engine.get_vector_db_status()
        
        return {
            "status": "available",
            "vector_db": vector_db_status,
            "version": "0.1.0"
        }
        
    except Exception as e:
        logger.error(f"상태 조회 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"상태 조회 중 오류가 발생했습니다: {str(e)}"
        ) 