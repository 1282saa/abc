"""
빅카인즈 API 클라이언트

빅카인즈 Open API에 대한 요청을 처리하고 응답을 반환하는 클라이언트 클래스
"""

import os
import json
import time
import logging
import requests
from typing import Dict, List, Optional, Union, Any
from pathlib import Path
from functools import lru_cache

# 프로젝트 루트 디렉토리 찾기
PROJECT_ROOT = Path(__file__).parent.parent.parent

import sys
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import API_BASE_URL, API_ENDPOINTS, PERFORMANCE

# 환경 변수에서 API 키 로드
API_KEY = os.environ.get("BIGKINDS_API_KEY", "")

class BigKindsClient:
    """빅카인즈 API와 상호작용하는 클라이언트 클래스"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """빅카인즈 API 클라이언트 초기화
        
        Args:
            api_key: 빅카인즈 API 접근 키. 없으면 환경변수에서 로드
            base_url: API 기본 URL. 없으면 설정에서 로드
        """
        self.api_key = api_key or API_KEY
        if not self.api_key:
            raise ValueError("API 키가 필요합니다. 환경변수 BIGKINDS_API_KEY를 설정하거나 초기화 시 제공하세요.")
        
        self.base_url = base_url or API_BASE_URL
        self.logger = logging.getLogger(__name__)
        self.timeout = PERFORMANCE.get("request_timeout", 30)
        
    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """API 엔드포인트에 요청을 보내고 응답을 반환
        
        Args:
            endpoint: API 엔드포인트 경로
            params: 요청 파라미터
            
        Returns:
            API 응답 (JSON)
        """
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        
        # API 키 추가
        params["access_key"] = self.api_key
        
        try:
            self.logger.debug(f"API 요청: {url}, 파라미터: {params}")
            response = requests.post(url, json=params, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            result = response.json()
            self.logger.debug(f"API 응답: {result}")
            return result
        
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API 요청 실패: {e}")
            if hasattr(e.response, "text"):
                self.logger.error(f"응답 내용: {e.response.text}")
            raise
    
    def news_search(self, query: str, start_date: str, end_date: str, 
                   provider: Optional[List[str]] = None,
                   category: Optional[List[str]] = None,
                   sort: str = "date",
                   size: int = 10,
                   page: int = 1) -> Dict[str, Any]:
        """뉴스 검색 API 호출
        
        Args:
            query: 검색어
            start_date: 시작 날짜 (YYYY-MM-DD)
            end_date: 종료 날짜 (YYYY-MM-DD)
            provider: 언론사 코드 리스트
            category: 카테고리 코드 리스트
            sort: 정렬 기준 (date, rank)
            size: 페이지 크기
            page: 페이지 번호
            
        Returns:
            뉴스 검색 결과
        """
        params = {
            "query": query,
            "published_at": {
                "from": start_date,
                "until": end_date
            },
            "sort": {"date": "desc" if sort == "date" else "asc"},
            "return_from": (page - 1) * size,
            "return_size": size
        }
        
        if provider:
            params["provider"] = provider
        
        if category:
            params["category"] = category
        
        return self._make_request(API_ENDPOINTS["news_search"], params)
    
    def issue_ranking(self, date: str, provider: Optional[List[str]] = None) -> Dict[str, Any]:
        """오늘의 이슈 API 호출
        
        Args:
            date: 날짜 (YYYY-MM-DD)
            provider: 언론사 코드 리스트
            
        Returns:
            이슈 랭킹 결과
        """
        params = {"date": date}
        
        if provider:
            params["provider"] = provider
        
        return self._make_request(API_ENDPOINTS["issue_ranking"], params)
    
    def word_cloud(self, query: str, start_date: str, end_date: str,
                  provider: Optional[List[str]] = None,
                  category: Optional[List[str]] = None,
                  display_count: int = 20) -> Dict[str, Any]:
        """연관어 분석 API 호출
        
        Args:
            query: 검색어
            start_date: 시작 날짜 (YYYY-MM-DD)
            end_date: 종료 날짜 (YYYY-MM-DD)
            provider: 언론사 코드 리스트
            category: 카테고리 코드 리스트
            display_count: 표시할 연관어 수
            
        Returns:
            연관어 분석 결과
        """
        params = {
            "query": query,
            "published_at": {
                "from": start_date,
                "until": end_date
            },
            "display_count": display_count
        }
        
        if provider:
            params["provider"] = provider
        
        if category:
            params["category"] = category
        
        return self._make_request(API_ENDPOINTS["word_cloud"], params)
    
    def time_line(self, query: str, start_date: str, end_date: str,
                 provider: Optional[List[str]] = None,
                 category: Optional[List[str]] = None,
                 interval: str = "day") -> Dict[str, Any]:
        """키워드 트렌드 API 호출
        
        Args:
            query: 검색어
            start_date: 시작 날짜 (YYYY-MM-DD)
            end_date: 종료 날짜 (YYYY-MM-DD)
            provider: 언론사 코드 리스트
            category: 카테고리 코드 리스트
            interval: 시간 단위 (hour, day, month, year)
            
        Returns:
            키워드 트렌드 결과
        """
        params = {
            "query": query,
            "published_at": {
                "from": start_date,
                "until": end_date
            },
            "interval": interval
        }
        
        if provider:
            params["provider"] = provider
        
        if category:
            params["category"] = category
        
        return self._make_request(API_ENDPOINTS["time_line"], params)
    
    def quotation_search(self, query: str, start_date: str, end_date: str,
                        provider: Optional[List[str]] = None,
                        category: Optional[List[str]] = None,
                        size: int = 10,
                        page: int = 1) -> Dict[str, Any]:
        """뉴스 인용문 검색 API 호출
        
        Args:
            query: 검색어
            start_date: 시작 날짜 (YYYY-MM-DD)
            end_date: 종료 날짜 (YYYY-MM-DD)
            provider: 언론사 코드 리스트
            category: 카테고리 코드 리스트
            size: 페이지 크기
            page: 페이지 번호
            
        Returns:
            인용문 검색 결과
        """
        params = {
            "query": query,
            "published_at": {
                "from": start_date,
                "until": end_date
            },
            "return_from": (page - 1) * size,
            "return_size": size
        }
        
        if provider:
            params["provider"] = provider
        
        if category:
            params["category"] = category
        
        return self._make_request(API_ENDPOINTS["quotation_search"], params)
    
    def today_category_keyword(self) -> Dict[str, Any]:
        """오늘의 키워드 API 호출
        
        Returns:
            카테고리별 키워드 분석 결과
        """
        return self._make_request(API_ENDPOINTS["today_category_keyword"], {})
    
    def feature(self, title: str, content: str, sub_title: Optional[str] = None) -> Dict[str, Any]:
        """특성 추출 API 호출
        
        Args:
            title: 제목
            content: 본문
            sub_title: 부제목
            
        Returns:
            특성 추출 결과
        """
        params = {
            "title": title,
            "content": content
        }
        
        if sub_title:
            params["sub_title"] = sub_title
        
        return self._make_request(API_ENDPOINTS["feature"], params)
    
    def keyword(self, title: str, content: str, sub_title: Optional[str] = None) -> Dict[str, Any]:
        """키워드 추출 API 호출
        
        Args:
            title: 제목
            content: 본문
            sub_title: 부제목
            
        Returns:
            키워드 추출 결과
        """
        params = {
            "title": title,
            "content": content
        }
        
        if sub_title:
            params["sub_title"] = sub_title
        
        return self._make_request(API_ENDPOINTS["keyword"], params)
    
    def topn_keyword(self, date_hour: str, 
                    query: Optional[str] = None,
                    start_date: Optional[str] = None, 
                    end_date: Optional[str] = None,
                    provider: Optional[List[str]] = None,
                    category: Optional[List[str]] = None,
                    top_n: int = 30) -> Dict[str, Any]:
        """TopN 키워드 API 호출
        
        Args:
            date_hour: 날짜 시간 (YYYY-MM-DD HH)
            query: 검색어
            start_date: 시작 날짜 (YYYY-MM-DD)
            end_date: 종료 날짜 (YYYY-MM-DD)
            provider: 언론사 코드 리스트
            category: 카테고리 코드 리스트
            top_n: 상위 키워드 수
            
        Returns:
            상위 키워드 결과
        """
        params = {
            "date_hour": date_hour,
            "topn": top_n
        }
        
        if query:
            params["query"] = query
        
        if start_date and end_date:
            params["published_at"] = {
                "from": start_date,
                "until": end_date
            }
        
        if provider:
            params["provider"] = provider
        
        if category:
            params["category"] = category
        
        return self._make_request(API_ENDPOINTS["topn_keyword"], params)
    
    def query_rank(self, start_date: str, end_date: str, size: int = 10) -> Dict[str, Any]:
        """인기검색어 API 호출
        
        Args:
            start_date: 시작 날짜 (YYYY-MM-DD)
            end_date: 종료 날짜 (YYYY-MM-DD)
            size: 결과 수
            
        Returns:
            인기 검색어 결과
        """
        params = {
            "from": start_date,
            "until": end_date,
            "offset": size
        }
        
        return self._make_request(API_ENDPOINTS["query_rank"], params)


# 모듈 사용 예제
if __name__ == "__main__":
    # 로깅 설정
    logging.basicConfig(level=logging.INFO)
    
    # API 키 테스트용
    test_api_key = os.environ.get("BIGKINDS_API_KEY", "")
    
    # 클라이언트 생성
    client = BigKindsClient(api_key=test_api_key)
    
    # API 테스트
    try:
        # 오늘의 키워드 API 테스트 (파라미터 없음)
        result = client.today_category_keyword()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"API 테스트 실패: {e}")