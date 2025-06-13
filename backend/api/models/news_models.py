"""
뉴스 관련 API 모델

뉴스 API 엔드포인트에서 사용하는 요청 및 응답 모델을 정의합니다.
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime

class LatestNewsResponse(BaseModel):
    """최신 뉴스 응답 모델"""
    today_issues: List[Dict[str, Any]] = Field(description="오늘의 이슈 (빅카인즈 이슈 랭킹)")
    popular_keywords: List[Dict[str, Any]] = Field(description="인기 키워드")
    timestamp: str = Field(description="응답 시간")

class CompanyNewsRequest(BaseModel):
    """기업 뉴스 요청 모델"""
    company_name: str = Field(..., description="기업명")
    date_from: Optional[str] = Field(None, description="시작일 (YYYY-MM-DD)")
    date_to: Optional[str] = Field(None, description="종료일 (YYYY-MM-DD)")
    limit: Optional[int] = Field(default=20, description="가져올 기사 수", ge=1, le=100)

class KeywordNewsRequest(BaseModel):
    """키워드 뉴스 요청 모델"""
    keyword: str = Field(..., description="검색 키워드")
    date_from: Optional[str] = Field(None, description="시작일 (YYYY-MM-DD)")
    date_to: Optional[str] = Field(None, description="종료일 (YYYY-MM-DD)")
    limit: Optional[int] = Field(default=30, description="가져올 기사 수", ge=1, le=100)

class AISummaryRequest(BaseModel):
    """AI 요약 요청 모델"""
    news_ids: List[str] = Field(..., description="요약할 뉴스 ID 리스트 (최대 5개)", max_items=5) 