"""
빅카인즈 API 클라이언트

실제 BigKinds OpenAPI 스펙에 맞춘 구현:
- 올바른 요청/응답 형식
- 필드 선택 기능 (fields)
- 서울경제신문 필터링
- 에러 처리 및 재시도 로직
- 키워드 기반 타임라인 및 상세 검색 기능
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
# 서울경제신문 코드만 설정해도 되는가?
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
###### 빅카인즈 서비스 클래스
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
        """빅카인즈 API 요청 실행 (노트북 성공 사례 기반)
        
        Args:
            endpoint: API 엔드포인트
            argument: 요청 argument 데이터
            
        Returns:
            API 응답 데이터
        """
        url = f"{self.base_url}{endpoint}"
        
        # 빅카인즈 가이드라인에 따른 올바른 요청 구조 (노트북 성공 사례 기반)
        request_data = {
            "access_key": self.api_key,
            "argument": argument
        }
        
        headers = {
            "Content-Type": "application/json"
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
            self.logger.debug(f"응답 데이터: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            # result 값 확인 (0=성공, 그 외=오류)
            if result.get("result") != 0:
                error_msg = f"BigKinds API 오류: result={result.get('result')}, reason={result.get('reason', '')}"
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
    
    def get_keyword_news(
        self,
        keyword: str,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        return_size: int = 30
    ) -> Dict[str, Any]:
        """키워드 기반 뉴스 검색
        
        Args:
            keyword: 검색 키워드
            date_from: 시작일
            date_to: 종료일
            return_size: 반환할 결과 수
            
        Returns:
            키워드 관련 뉴스 검색 결과
        """
        # 키워드로 검색, 모든 언론사 대상
        return self.search_news(
            query=keyword,
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
    
    def get_news_detail(self, news_id: str) -> Dict[str, Any]:
        """단일 뉴스 ID로 상세 정보 조회 및 포맷팅
        
        Args:
            news_id: 뉴스 ID
            
        Returns:
            포맷팅된 뉴스 상세 정보
        """
        result = self.get_news_by_ids([news_id])
        formatted_result = self.format_news_response(result)
        
        if not formatted_result.get("documents"):
            return {
                "success": False,
                "error": "뉴스를 찾을 수 없습니다",
                "news": None
            }
        
        news = formatted_result.get("documents")[0]
        has_original_link = bool(news.get("url"))
        
        return {
            "success": True,
            "news": news,
            "has_original_link": has_original_link
        }
    
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
        """이슈 랭킹 조회 - 실제 API 스펙 기반 수정
        
        Args:
            date: 조회 날짜 (YYYY-MM-DD) - 필수값, 없으면 오늘 날짜 사용
            provider: 언론사 필터 - 선택사항
            
        Returns:
            이슈 랭킹 결과
        """
        # date는 필수 파라미터이므로 기본값 설정 (오늘 날짜)
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        # 빅카인즈 이슈 랭킹 필수 파라미터
        argument = {
            "date": date
        }
        
        # 언론사 필터가 있는 경우만 추가
        if provider and len(provider) > 0:
            argument["provider"] = provider
        
        self.logger.info(f"이슈 랭킹 요청 - date: {date}, provider: {provider}")
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
    
    def get_word_cloud(self, query: str, date_from: Optional[str] = None, date_to: Optional[str] = None) -> Dict[str, Any]:
        """워드 클라우드(연관어 분석) API 호출
        
        Args:
            query: 검색 키워드
            date_from: 시작일
            date_to: 종료일
            
        Returns:
            연관 키워드 목록
        """
        if not date_from:
            date_from = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not date_to:
            date_to = datetime.now().strftime("%Y-%m-%d")
        
        argument = {
            "query": query,
            "published_at": {
                "from": date_from,
                "until": date_to
            }
        }
        
        return self._make_request(API_ENDPOINTS["word_cloud"], argument)
    
    def get_time_line(
        self, 
        query: str, 
        date_from: Optional[str] = None, 
        date_to: Optional[str] = None,
        interval: str = "month",
        normalize: bool = False
    ) -> Dict[str, Any]:
        """키워드 트렌드(뉴스 타임라인) API 호출
        
        Args:
            query: 검색 키워드
            date_from: 시작일
            date_to: 종료일
            interval: 집계 간격 (day, month, year)
            normalize: 정규화 여부
            
        Returns:
            시간별 뉴스 통계
        """
        if not date_from:
            date_from = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")  # 1년
        if not date_to:
            date_to = datetime.now().strftime("%Y-%m-%d")
        
        argument = {
            "query": query,
            "published_at": {
                "from": date_from,
                "until": date_to
            },
            "interval": interval,
            "normalize": str(normalize).lower()
        }
        
        return self._make_request(API_ENDPOINTS["time_line"], argument)
    
    def get_today_category_keyword(self) -> Dict[str, Any]:
        """오늘의 카테고리별 키워드 조회
        
        Returns:
            카테고리별 키워드 결과
        """
        argument = {}
        
        return self._make_request(API_ENDPOINTS["today_category_keyword"], argument)
    
    def search_quotations(
        self,
        query: str,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        provider: Optional[List[str]] = None,
        category: Optional[List[str]] = None,
        fields: Optional[List[str]] = None,
        return_size: int = 10
    ) -> Dict[str, Any]:
        """뉴스 인용문 검색
        
        Args:
            query: 검색 키워드
            date_from: 시작일
            date_to: 종료일
            provider: 언론사 목록
            category: 카테고리 목록
            fields: 반환할 필드 목록
            return_size: 반환할 결과 수
            
        Returns:
            인용문 검색 결과
        """
        if not date_from:
            date_from = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not date_to:
            date_to = datetime.now().strftime("%Y-%m-%d")
        
        if not fields:
            fields = [
                "news_id",
                "title",
                "published_at",
                "provider",
                "source",
                "quotation"
            ]
        
        argument = {
            "query": query,
            "published_at": {
                "from": date_from,
                "until": date_to
            },
            "return_size": return_size,
            "fields": fields
        }
        
        if provider:
            argument["provider"] = provider
        
        if category:
            argument["category"] = category
        
        return self._make_request(API_ENDPOINTS["quotation_search"], argument)
    
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
        """이슈 랭킹 API 응답을 topics 구조로 변환 - 실제 API 구조 기반
        
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
        # 실제 API 응답은 topics 배열을 직접 반환
        raw_topics = return_object.get("topics", [])
        
        # topics 구조로 변환 - 실제 API 필드명 사용
        topics = []
        for idx, topic_data in enumerate(raw_topics):
            topic = {
                "topic_id": f"topic_{idx+1}",  # API에는 topic_id가 없으므로 생성
                "topic_name": topic_data.get("topic", ""),  # 실제 필드명: 'topic'
                "rank": topic_data.get("topic_rank", idx + 1),  # 실제 필드명: 'topic_rank'
                "score": topic_data.get("topic_rank", idx + 1),  # rank를 score로 사용
                "news_cluster": topic_data.get("news_cluster", []),  # 실제 필드명: 'news_cluster'
                "keywords": topic_data.get("topic_keyword", "").split(",") if topic_data.get("topic_keyword") else [],  # 실제 필드명: 'topic_keyword'
                # 원본 필드도 그대로 보존 (프론트 요구)
                "topic": topic_data.get("topic", ""),
                "topic_rank": topic_data.get("topic_rank", idx + 1),
                "topic_keyword": topic_data.get("topic_keyword", ""),
            }
            topics.append(topic)
        
        return {
            "success": True,
            "topics": topics
        }
    
    def format_quotation_response(self, api_response: Dict[str, Any]) -> Dict[str, Any]:
        """인용문 검색 API 응답을 포맷팅
        
        Args:
            api_response: BigKinds quotation_search API 응답
            
        Returns:
            포맷팅된 인용문 검색 결과
        """
        if api_response.get("result") != 0:
            return {
                "success": False,
                "error": "인용문 검색 실패",
                "quotations": []
            }
        
        return_object = api_response.get("return_object", {})
        documents = return_object.get("documents", [])
        
        # 인용문 구조로 변환
        quotations = []
        for doc in documents:
            quotation = {
                "id": doc.get("news_id", ""),
                "title": doc.get("title", ""),
                "published_at": doc.get("published_at", ""),
                "provider": doc.get("provider", ""),
                "source": doc.get("source", ""),  # 인용 출처
                "quotation": doc.get("quotation", "")  # 인용문
            }
            quotations.append(quotation)
        
        return {
            "success": True,
            "total_hits": return_object.get("total_hits", 0),
            "quotations": quotations
        }
    
    def get_keyword_news_timeline(
        self,
        keyword: str,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        return_size: int = 50
    ) -> Dict[str, Any]:
        """키워드 기반 뉴스 타임라인 구성
        
        Args:
            keyword: 검색 키워드
            date_from: 시작일
            date_to: 종료일
            return_size: 반환할 결과 수
            
        Returns:
            일자별 뉴스 목록
        """
        # 키워드로 뉴스 검색
        news_response = self.get_keyword_news(
            keyword=keyword,
            date_from=date_from,
            date_to=date_to,
            return_size=return_size
        )
        
        # 응답 포맷팅
        formatted_response = self.format_news_response(news_response)
        
        # 날짜별로 뉴스 그룹화
        timeline = {}
        for doc in formatted_response.get("documents", []):
            # published_at에서 날짜 부분만 추출
            published_at = doc.get("published_at", "")
            date_str = published_at[:10] if published_at else ""  # YYYY-MM-DD 형식
            
            if date_str and date_str not in timeline:
                timeline[date_str] = []
            
            if date_str:
                timeline[date_str].append(doc)
        
        # 날짜 기준 내림차순 정렬
        sorted_timeline = []
        for date_str in sorted(timeline.keys(), reverse=True):
            sorted_timeline.append({
                "date": date_str,
                "articles": timeline[date_str],
                "count": len(timeline[date_str])
            })
        
        return {
            "success": True,
            "keyword": keyword,
            "period": {
                "from": date_from,
                "to": date_to
            },
            "total_count": len(formatted_response.get("documents", [])),
            "timeline": sorted_timeline
        }
    
    def get_company_news_timeline(
        self,
        company_name: str,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        return_size: int = 30
    ) -> Dict[str, Any]:
        """기업별 뉴스 타임라인 조회
        
        Args:
            company_name: 기업명
            date_from: 시작일
            date_to: 종료일
            return_size: 반환할 결과 수
            
        Returns:
            일자별 뉴스 목록
        """
        # 종료일에 +1일 추가 (오늘 데이터 포함)
        if date_to:
            # 이미 date_to가 설정된 경우 +1일
            dt_obj = datetime.strptime(date_to, "%Y-%m-%d")
            date_to = (dt_obj + timedelta(days=1)).strftime("%Y-%m-%d")
        
        # 기업 관련 뉴스 검색
        news_response = self.get_company_news(
            company_name=company_name,
            date_from=date_from,
            date_to=date_to,
            return_size=return_size
        )
        
        # 응답 포맷팅
        formatted_response = self.format_news_response(news_response)
        
        # 날짜별로 뉴스 그룹화
        timeline = {}
        for doc in formatted_response.get("documents", []):
            # published_at에서 날짜 부분만 추출
            published_at = doc.get("published_at", "")
            date_str = published_at[:10] if published_at else ""  # YYYY-MM-DD 형식
            
            if date_str and date_str not in timeline:
                timeline[date_str] = []
            
            if date_str:
                timeline[date_str].append(doc)
        
        # 날짜 기준 내림차순 정렬
        sorted_timeline = []
        for date_str in sorted(timeline.keys(), reverse=True):
            sorted_timeline.append({
                "date": date_str,
                "articles": timeline[date_str],
                "count": len(timeline[date_str])
            })
        
        return {
            "success": True,
            "company": company_name,
            "period": {
                "from": date_from,
                "to": date_to
            },
            "total_count": len(formatted_response.get("documents", [])),
            "timeline": sorted_timeline
        }
    
    def get_company_news_for_summary(
        self,
        company_name: str,
        days: int = 7,
        limit: int = 5
    ) -> Dict[str, Any]:
        """기업의 최근 뉴스를 요약용으로 가져오기
        
        Args:
            company_name: 기업명
            days: 최근 며칠간 (기본값: 7일)
            limit: 가져올 기사 수 (기본값: 5개)
            
        Returns:
            요약용 뉴스 데이터 (제목, 내용 포함)
        """
        # 날짜 범위 설정
        end_date = datetime.now()
        # until은 오늘 날짜 +1일로 설정 (오늘 데이터 포함 위해)
        end_date_plus_one = end_date + timedelta(days=1)
        start_date = end_date - timedelta(days=days)
        
        date_from = start_date.strftime("%Y-%m-%d")
        date_to = end_date_plus_one.strftime("%Y-%m-%d")
        
        # 기업 뉴스 검색 - content 필드 반드시 포함
        search_result = self.get_company_news(
            company_name=company_name,
            date_from=date_from,
            date_to=date_to,
            return_size=limit
        )
        
        # 응답 포맷팅
        formatted_result = self.format_news_response(search_result)
        
        return {
            "success": formatted_result.get("success", False),
            "company": company_name,
            "period": {"from": date_from, "to": date_to},
            "articles": formatted_result.get("documents", []),
            "total_found": formatted_result.get("total_hits", 0)
        }
    
    def get_company_news_report(
        self,
        company_name: str,
        report_type: str,
        reference_date: Optional[str] = None,
        max_articles: int = 100
    ) -> Dict[str, Any]:
        """기업 기간별 뉴스 레포트 생성
        
        Args:
            company_name: 기업명
            report_type: 레포트 타입 (daily, weekly, monthly, quarterly, yearly)
            reference_date: 기준 날짜 (None이면 오늘 날짜 사용)
            max_articles: 최대 기사 수
            
        Returns:
            기간별 뉴스 레포트 데이터
        """
        if not reference_date:
            reference_date = datetime.now().strftime("%Y-%m-%d")
        
        end_date = datetime.strptime(reference_date, "%Y-%m-%d")
        
        # 레포트 타입에 따라 시작 날짜 계산
        if report_type == "daily":
            start_date = end_date
        elif report_type == "weekly":
            start_date = end_date - timedelta(days=7)
        elif report_type == "monthly":
            start_date = end_date - timedelta(days=30)
        elif report_type == "quarterly":
            start_date = end_date - timedelta(days=90)
        elif report_type == "yearly":
            start_date = end_date - timedelta(days=365)
        else:
            raise ValueError(f"지원하지 않는 레포트 타입: {report_type}")
        
        date_from = start_date.strftime("%Y-%m-%d")
        date_to = (end_date + timedelta(days=1)).strftime("%Y-%m-%d")  # 종료일 +1일 (포함)
        
        # 기간에 맞는 뉴스 검색
        news_response = self.get_company_news(
            company_name=company_name,
            date_from=date_from,
            date_to=date_to,
            return_size=max_articles
        )
        
        # 응답 포맷팅
        formatted_response = self.format_news_response(news_response)
        articles = formatted_response.get("documents", [])
        
        # 기간별 메타데이터 생성
        period_names = {
            "daily": "일간",
            "weekly": "주간",
            "monthly": "월간",
            "quarterly": "분기별",
            "yearly": "연간"
        }
        
        return {
            "success": True,
            "company": company_name,
            "report_type": report_type,
            "report_type_kr": period_names.get(report_type, report_type),
            "reference_date": reference_date,
            "period": {
                "from": date_from,
                "to": end_date.strftime("%Y-%m-%d")  # 원래 종료일
            },
            "total_articles": len(articles),
            "articles": articles
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
    
    def get_popular_keywords(self, days: int = 1, limit: int = 10) -> Dict[str, Any]:
        """전체 인기 검색어 랭킹 조회 - 실제 API 응답 구조 기반
        
        Args:
            days: 조회 기간 (일수, 기본값: 1일)
            limit: 상위 몇 개 (기본값: 10개)
            
        Returns:
            전체 인기 검색어 랭킹 결과 (queries 배열 구조)
        """
        # 기간 설정 (어제부터 오늘까지)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        from_date = start_date.strftime("%Y-%m-%d")
        until_date = end_date.strftime("%Y-%m-%d")
        
        # 빅카인즈 query_rank API 파라미터 구조
        argument = {
            "from": from_date,
            "until": until_date,
            "offset": limit,
            "target_access_key": ""
        }
        
        self.logger.info(f"인기 키워드 요청 - from: {from_date}, until: {until_date}, limit: {limit}")
        result = self._make_request(API_ENDPOINTS["query_rank"], argument)
        
        # 응답 구조 변환하여 반환
        if result.get("result") == 0:
            return_object = result.get("return_object", {})
            queries = return_object.get("queries", [])
            
            # 프론트엔드 친화적 구조로 변환
            formatted_keywords = []
            for idx, query_data in enumerate(queries[:limit]):
                formatted_keywords.append({
                    "rank": idx + 1,
                    "keyword": query_data.get("query", ""),
                    "count": query_data.get("count", 0),
                    "date": query_data.get("date", ""),
                    "trend": "stable"  # 기본값
                })
            
            # 원본 응답에 포맷팅된 데이터 추가
            result["formatted_keywords"] = formatted_keywords
            
        return result
    
    def get_popular_keywords_for_date(
        self, 
        from_date: str, 
        until_date: str, 
        limit: int = 10
    ) -> Dict[str, Any]:
        """특정 날짜 범위의 인기 검색어 랭킹 조회
        
        Args:
            from_date: 시작일 (YYYY-MM-DD)
            until_date: 종료일 (YYYY-MM-DD)
            limit: 상위 몇 개 (기본값: 10개)
            
        Returns:
            인기 검색어 랭킹 결과
        """
        # 빅카인즈 query_rank API 파라미터 구조
        argument = {
            "from": from_date,
            "until": until_date,
            "offset": limit,
            "target_access_key": ""
        }
        
        self.logger.info(f"특정 날짜 인기 키워드 요청 - from: {from_date}, until: {until_date}, limit: {limit}")
        return self._make_request(API_ENDPOINTS["query_rank"], argument)