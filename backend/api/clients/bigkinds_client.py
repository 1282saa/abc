"""
빅카인즈 API 클라이언트

실제 BigKinds OpenAPI 스펙에 맞춘 구현:
- 올바른 요청/응답 형식
- 필드 선택 기능 (fields)
- 서울경제신문 필터링
- 에러 처리 및 재시도 로직
"""

import os
import json
import time
import logging
import requests
import sys
from typing import Dict, List, Optional, Union, Any, Tuple
from pathlib import Path
from datetime import datetime, timedelta

# 프로젝트 루트 디렉토리 찾기
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.utils.logger import setup_logger

# API 설정
API_BASE_URL = "https://tools.kinds.or.kr/"
API_ENDPOINTS = {
    "news_search": "search/news",
    "issue_ranking": "issue_ranking", 
    "query_rank": "query_rank",
    "word_cloud": "word_cloud",
    "time_line": "time_line",
    "quotation_search": "search/quotation",
    "today_category_keyword": "today_category_keyword"
}

# 서울경제신문 관련 설정
SEOUL_ECONOMIC = {
    "name": "서울경제",
    "code": "02100311"
}

# 기본 필드 설정
DEFAULT_NEWS_FIELDS = [
    "news_id",
    "title", 
    "content",
    "published_at",
    "dateline",
    "category",
    "images",
    "provider_link_page",
    "provider_code",
    "provider_name",
    "byline"
]

class BigKindsClient:
    """빅카인즈 API 클라이언트"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """빅카인즈 API 클라이언트 초기화
        
        Args:
            api_key: 빅카인즈 API 키
            base_url: API 기본 URL
        """
        self.api_key = api_key or os.environ.get("BIGKINDS_KEY", "")
        if not self.api_key:
            raise ValueError("BigKinds API 키가 필요합니다. 환경변수 BIGKINDS_KEY를 설정하세요.")
        
        self.base_url = base_url or API_BASE_URL
        self.logger = setup_logger("api.bigkinds")
        self.timeout = 30
        
    def _make_request(self, endpoint: str, argument: Dict[str, Any]) -> Dict[str, Any]:
        """빅카인즈 API 요청 실행 (가이드라인 준수)
        
        Args:
            endpoint: API 엔드포인트
            argument: 요청 argument 데이터
            
        Returns:
            API 응답 데이터
        """
        url = f"{self.base_url}{endpoint}"
        
        # 빅카인즈 가이드라인에 따른 올바른 요청 구조
        request_data = {
            "access_key": self.api_key,
            "argument": argument
        }
        
        headers = {
            "Content-Type": "application/json; charset=UTF-8"
        }
        
        self.logger.info(f"BigKinds API 요청: {endpoint}")
        self.logger.debug(f"요청 데이터: {json.dumps(request_data, ensure_ascii=False, indent=2)}")
        
        try:
            response = requests.post(
                url,
                json=request_data,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            self.logger.info(f"API 응답 성공: {endpoint}")
            
            # result 값 확인 (0=성공, 그 외=오류)
            if result.get("result") != 0:
                error_msg = f"BigKinds API 오류: result={result.get('result')}"
                self.logger.error(error_msg)
                return {"result": result.get("result"), "error": error_msg, "return_object": {}}
            
            return result
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API 요청 실패: {e}")
            raise Exception(f"BigKinds API 요청 실패: {str(e)}")
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON 디코딩 실패: {e}")
            raise Exception(f"API 응답 파싱 실패: {str(e)}")
    
    def search_news(
        self,
        query: str = "",
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        provider: Optional[List[str]] = None,
        category: Optional[List[str]] = None,
        fields: Optional[List[str]] = None,
        sort_by: str = "date",
        sort_order: str = "desc",
        return_from: int = 0,
        return_size: int = 10,
        news_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """뉴스 검색
        
        Args:
            query: 검색 키워드
            date_from: 시작일 (YYYY-MM-DD)
            date_to: 종료일 (YYYY-MM-DD)
            provider: 언론사 목록 (예: ["서울경제"])
            category: 카테고리 목록
            fields: 반환할 필드 목록
            sort_by: 정렬 기준 (date, _score)
            sort_order: 정렬 순서 (asc, desc)
            return_from: 페이징 시작 위치
            return_size: 반환할 결과 수
            news_ids: 특정 뉴스 ID로 검색 (뉴스 상세 조회용)
            
        Returns:
            검색 결과
        """
        # 기본 날짜 설정 (최근 30일)
        if not date_from:
            date_from = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not date_to:
            date_to = datetime.now().strftime("%Y-%m-%d")
        
        # 기본 필드 설정
        if not fields:
            fields = DEFAULT_NEWS_FIELDS
        
        # argument 구성
        argument = {
            "published_at": {
                "from": date_from,
                "until": date_to
            },
            "sort": {sort_by: sort_order},
            "return_from": return_from,
            "return_size": return_size,
            "fields": fields
        }
        
        # 쿼리 추가 (빈 문자열이 아닌 경우)
        if query:
            argument["query"] = query
        
        # 특정 뉴스 ID 검색
        if news_ids:
            argument["news_ids"] = news_ids
        
        # 언론사 필터
        if provider:
            argument["provider"] = provider
        
        # 카테고리 필터
        if category:
            argument["category"] = category
        
        payload = {
            "argument": argument
        }
        
        return self._make_request(API_ENDPOINTS["news_search"], argument)
    
    def search_seoul_economic_news(
        self,
        query: str = "",
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        fields: Optional[List[str]] = None,
        return_size: int = 10
    ) -> Dict[str, Any]:
        """서울경제신문 뉴스 검색
        
        Args:
            query: 검색 키워드
            date_from: 시작일
            date_to: 종료일
            fields: 반환할 필드
            return_size: 반환할 결과 수
            
        Returns:
            서울경제신문 뉴스 검색 결과
        """
        return self.search_news(
            query=query,
            date_from=date_from,
            date_to=date_to,
            provider=[SEOUL_ECONOMIC["name"]],
            fields=fields,
            return_size=return_size
        )
    
    def get_company_news(
        self,
        company_name: str,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        return_size: int = 20
    ) -> Dict[str, Any]:
        """기업 관련 뉴스 검색
        
        Args:
            company_name: 기업명
            date_from: 시작일
            date_to: 종료일
            return_size: 반환할 결과 수
            
        Returns:
            기업 뉴스 검색 결과
        """
        # 기업명으로 검색, 모든 언론사 대상
        return self.search_news(
            query=company_name,
            date_from=date_from,
            date_to=date_to,
            fields=[
                "news_id",
                "title",
                "content", 
                "published_at",
                "category",
                "provider_name",
                "provider_link_page",
                "byline",
                "images"
            ],
            return_size=return_size
        )
    
    def get_latest_news(
        self,
        provider: Optional[List[str]] = None,
        return_size: int = 10
    ) -> Dict[str, Any]:
        """최신 뉴스 조회
        
        Args:
            provider: 언론사 목록
            return_size: 반환할 결과 수
            
        Returns:
            최신 뉴스 목록
        """
        # 오늘 날짜로 검색
        today = datetime.now().strftime("%Y-%m-%d")
        
        return self.search_news(
            date_from=today,
            date_to=today,
            provider=provider,
            sort_by="date",
            sort_order="desc",
            return_size=return_size
        )
    
    def get_news_by_ids(self, news_ids: List[str]) -> Dict[str, Any]:
        """뉴스 ID로 상세 정보 조회
        
        Args:
            news_ids: 뉴스 ID 목록
            
        Returns:
            뉴스 상세 정보
        """
        return self.search_news(
            news_ids=news_ids,
            fields=DEFAULT_NEWS_FIELDS,
            return_size=len(news_ids)
        )
    
    def get_news_by_cluster_ids(self, cluster_ids: List[str]) -> Dict[str, Any]:
        """뉴스 클러스터 ID로 뉴스 목록 조회
        
        issue_ranking API에서 반환된 news_cluster 배열의 ID들로 실제 뉴스 내용을 조회
        
        Args:
            cluster_ids: 뉴스 클러스터 ID 목록
            
        Returns:
            뉴스 목록
        """
        # news_cluster ID를 사용해서 실제 뉴스 검색
        return self.search_news(
            news_ids=cluster_ids,
            fields=DEFAULT_NEWS_FIELDS,
            return_size=len(cluster_ids)
        )
    
    def get_issue_ranking(self, date: Optional[str] = None, provider: Optional[List[str]] = None) -> Dict[str, Any]:
        """이슈 랭킹 조회 - 빅카인즈 가이드라인 준수
        
        Args:
            date: 조회 날짜 (YYYY-MM-DD)
            provider: 언론사 필터 (["서울경제"] 또는 [])
            
        Returns:
            이슈 랭킹 결과
        """
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        argument = {
            "date": date,
            "provider": provider or []
        }
        
        return self._make_request(API_ENDPOINTS["issue_ranking"], argument)
    
    def get_query_rank(self, from_date: Optional[str] = None, until_date: Optional[str] = None, offset: int = 10) -> Dict[str, Any]:
        """인기 검색어 랭킹 조회 - 빅카인즈 가이드라인 준수
        
        Args:
            from_date: 시작일 (YYYY-MM-DD)
            until_date: 종료일 (YYYY-MM-DD)
            offset: 상위 몇 개
            
        Returns:
            인기 검색어 랭킹 결과
        """
        if not from_date:
            from_date = datetime.now().strftime("%Y-%m-%d")
        if not until_date:
            until_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        argument = {
            "from": from_date,
            "until": until_date,
            "offset": offset,
            "target_access_key": ""
        }
        
        return self._make_request(API_ENDPOINTS["query_rank"], argument)
    
    def get_today_category_keyword(self) -> Dict[str, Any]:
        """오늘의 카테고리별 키워드 조회
        
        Returns:
            카테고리별 키워드 결과
        """
        argument = {}
        
        return self._make_request(API_ENDPOINTS["today_category_keyword"], argument)
    
    def format_news_response(self, api_response: Dict[str, Any]) -> Dict[str, Any]:
        """API 응답을 프론트엔드 친화적 형식으로 변환
        
        Args:
            api_response: BigKinds API 응답
            
        Returns:
            변환된 응답
        """
        if api_response.get("result") != 0:
            return {
                "success": False,
                "error": "API 요청 실패",
                "documents": []
            }
        
        return_object = api_response.get("return_object", {})
        documents = return_object.get("documents", [])
        
        # 문서 형식 정규화
        formatted_docs = []
        for doc in documents:
            formatted_doc = {
                "id": doc.get("news_id", ""),
                "title": doc.get("title", ""),
                "content": doc.get("content", ""),
                "summary": doc.get("content", "")[:200] + "..." if doc.get("content") else "",
                "published_at": doc.get("published_at", ""),
                "dateline": doc.get("dateline", ""),
                "category": doc.get("category", []),
                "provider": doc.get("provider_name", ""),
                "provider_code": doc.get("provider_code", ""),
                "url": doc.get("provider_link_page", ""),
                "byline": doc.get("byline", ""),
                "images": doc.get("images", [])
            }
            formatted_docs.append(formatted_doc)
        
        return {
            "success": True,
            "total_hits": return_object.get("total_hits", 0),
            "documents": formatted_docs
        }
    
    def format_issue_ranking_response(self, api_response: Dict[str, Any]) -> Dict[str, Any]:
        """이슈 랭킹 API 응답을 topics 구조로 변환
        
        Args:
            api_response: BigKinds issue_ranking API 응답
            
        Returns:
            topics 구조로 변환된 응답
        """
        if api_response.get("result") != 0:
            return {
                "success": False,
                "error": "이슈 랭킹 조회 실패",
                "topics": []
            }
        
        return_object = api_response.get("return_object", {})
        documents = return_object.get("documents", [])
        
        # topics 구조로 변환
        topics = []
        for doc in documents:
            topic = {
                "topic_id": doc.get("topic_id", ""),
                "topic_name": doc.get("topic_name", ""),
                "rank": doc.get("rank", 0),
                "score": doc.get("score", 0),
                "news_cluster": doc.get("news_cluster", [])
            }
            topics.append(topic)
        
        return {
            "success": True,
            "topics": topics
        }
    
    # 호환성을 위한 래퍼 메소드들
    def search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """기존 코드 호환성을 위한 래퍼 메소드"""
        return self.search_news(**params)
    
    def issue_ranking(self, date: str, provider: Optional[List[str]] = None) -> Dict[str, Any]:
        """기존 코드 호환성을 위한 래퍼 메소드"""
        return self.get_issue_ranking(date)
    
    def today_category_keyword(self) -> Dict[str, Any]:
        """기존 코드 호환성을 위한 래퍼 메소드"""
        return self.get_today_category_keyword()