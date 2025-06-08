"""
BigKinds API 클라이언트 메인 모듈

BigKindsClient 클래스는 빅카인즈 OpenAPI와 통신하는 핵심 기능을 제공합니다.
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

from .constants import API_BASE_URL, API_ENDPOINTS, SEOUL_ECONOMIC, DEFAULT_NEWS_FIELDS
from .formatters import format_news_response, format_issue_ranking_response, format_quotation_response
from backend.utils.logger import setup_logger

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
        
    def _make_request(self, method: str, endpoint: str, argument: Dict[str, Any] = None, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """빅카인즈 API 요청 실행
        
        Args:
            method: HTTP 메서드 (GET, POST)
            endpoint: API 엔드포인트
            argument: POST 요청 시 사용할 argument 데이터
            params: GET 요청 시 사용할 쿼리 파라미터
            
        Returns:
            API 응답 데이터
        """
        url = f"{self.base_url}{endpoint}"
        
        # GET 요청 처리 (params 사용)
        if method == "GET" and params:
            self.logger.info(f"BigKinds API GET 요청: {url}")
            self.logger.debug(f"요청 파라미터: {params}")
            
            try:
                # params에 access_key 추가
                params["access_key"] = self.api_key
                
                response = requests.get(
                    url,
                    params=params,
                    timeout=self.timeout
                )
                response.raise_for_status()
                
                result = response.json()
                self.logger.info(f"API 응답 성공: {url}")
                
                return result
                
            except requests.exceptions.RequestException as e:
                self.logger.error(f"API GET 요청 실패: {e}")
                raise Exception(f"BigKinds API 요청 실패: {str(e)}")
            except json.JSONDecodeError as e:
                self.logger.error(f"JSON 디코딩 실패: {e}")
                raise Exception(f"API 응답 파싱 실패: {str(e)}")
        
        # POST 요청 처리 (기존 로직)
        else:
            # 빅카인즈 가이드라인에 따른 올바른 요청 구조
            request_data = {
                "access_key": self.api_key,
                "argument": argument or {}
            }
            
            headers = {
                "Content-Type": "application/json"
            }
            
            self.logger.info(f"BigKinds API POST 요청: {endpoint}")
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
            # BigKinds API의 until은 exclusive이므로 하루 더 추가
            date_to = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
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
        
        return self._make_request("POST", API_ENDPOINTS["news_search"], argument=argument)
    
    def get_issue_ranking(
        self,
        date: Optional[str] = None,
        category_code: Optional[str] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """오늘의 이슈 랭킹 조회
        
        Args:
            date: 날짜 (YYYY-MM-DD, 기본값: 오늘)
            category_code: 카테고리 코드
            limit: 반환할 이슈 수
            
        Returns:
            이슈 랭킹 정보
        """
        # 올바른 엔드포인트 사용 (constants.py에 정의된 값 사용)
        endpoint = API_ENDPOINTS["issue_ranking"]
        
        # 날짜 기본값 설정
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        argument = {
            "date": date,
            "limit": limit
        }
        
        if category_code:
            argument["category"] = category_code
        
        response = self._make_request("POST", endpoint, argument=argument)
        
        return response
    
    def get_related_keywords(
        self,
        keyword: str,
        max_count: int = 20,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> List[str]:
        """키워드와 연관된 단어 목록 조회
        
        Args:
            keyword: 검색할 키워드
            max_count: 최대 반환 개수
            date_from: 시작일 (YYYY-MM-DD)
            date_to: 종료일 (YYYY-MM-DD)
            
        Returns:
            연관 키워드 목록
        """
        endpoint = f"{self.base_url}/word/related"
        
        # 날짜 기본값 설정
        if not date_from:
            date_from = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not date_to:
            # BigKinds API의 date_to는 inclusive이므로 오늘 날짜 사용
            date_to = datetime.now().strftime("%Y-%m-%d")
            
        params = {
            "query": keyword,
            "max": max_count,
            "date_from": date_from,
            "date_to": date_to
        }
        
        response = self._make_request("GET", endpoint, params=params)
        if response.get("success", False):
            # 연관어 결과 추출 및 가공
            related_words = response.get("result", {}).get("words", [])
            # 단어만 추출 (가중치나 기타 메타데이터 제외)
            return [word.get("word") for word in related_words]
        return []
    
    def get_keyword_topn(
        self,
        keyword: str,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        limit: int = 20
    ) -> List[str]:
        """키워드 관련 빈출 단어 조회
        
        Args:
            keyword: 검색 키워드
            date_from: 시작일 (YYYY-MM-DD)
            date_to: 종료일 (YYYY-MM-DD)
            limit: 반환할 단어 수
            
        Returns:
            빈출 단어 목록
        """
        # TopN API 호출
        endpoint = f"{self.base_url}/word/topn"
        
        # 날짜 기본값 설정
        if not date_from:
            date_from = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not date_to:
            # BigKinds API의 date_to는 inclusive이므로 오늘 날짜 사용
            date_to = datetime.now().strftime("%Y-%m-%d")
            
        params = {
            "query": keyword,
            "limit": limit,
            "date_from": date_from,
            "date_to": date_to
        }
        
        response = self._make_request("GET", endpoint, params=params)
        if response.get("success", False):
            # TopN 결과 추출 및 가공
            topn_words = response.get("result", {}).get("words", [])
            # 단어만 추출
            return [word.get("word") for word in topn_words]
        return []
    
    def get_popular_keywords(
        self,
        days: int = 1,
        limit: int = 10
    ) -> Dict[str, Any]:
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
        # BigKinds API의 until은 exclusive이므로 하루 더 추가
        until_date = (end_date + timedelta(days=1)).strftime("%Y-%m-%d")
        
        # 빅카인즈 query_rank API 파라미터 구조
        argument = {
            "from": from_date,
            "until": until_date,
            "offset": limit
        }
        
        self.logger.info(f"인기 키워드 요청 - from: {from_date}, until: {until_date}, limit: {limit}")
        result = self._make_request("POST", API_ENDPOINTS["query_rank"], argument=argument)
        
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
    
    def get_news_detail(self, news_id: str) -> Dict[str, Any]:
        """단일 뉴스 ID로 상세 정보 조회 및 포맷팅
        
        Args:
            news_id: 뉴스 ID
            
        Returns:
            포맷팅된 뉴스 상세 정보
        """
        # news_ids로 검색
        result = self.search_news(
            news_ids=[news_id],
            fields=DEFAULT_NEWS_FIELDS
        )
        
        # 응답 포맷팅
        formatted_result = format_news_response(result)
        
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
        # 날짜 기본값 설정
        if not date_from:
            date_from = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not date_to:
            # BigKinds API의 until은 exclusive이므로 하루 더 추가
            date_to = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

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
        # 날짜 기본값 설정
        if not date_from:
            date_from = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not date_to:
            # BigKinds API의 until은 exclusive이므로 하루 더 추가
            date_to = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            
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
        # 날짜 기본값 설정
        if not date_from:
            date_from = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        # date_to 처리
        if date_to:
            # 사용자가 직접 지정한 경우, +1일 추가 (exclusive 처리)
            try:
                dt_to = datetime.strptime(date_to, "%Y-%m-%d")
                adjusted_date_to = (dt_to + timedelta(days=1)).strftime("%Y-%m-%d")
            except ValueError:
                adjusted_date_to = date_to
        else:
            # 기본값으로 오늘+1일 설정
            adjusted_date_to = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            
        # 키워드로 뉴스 검색
        news_response = self.get_keyword_news(
            keyword=keyword,
            date_from=date_from,
            date_to=adjusted_date_to,  # 조정된 값 사용
            return_size=return_size
        )
        
        # 응답 포맷팅
        formatted_response = format_news_response(news_response)
        
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
        
        # UI 표시용 date_to (원래 값 사용)
        display_date_to = date_to or datetime.now().strftime("%Y-%m-%d")
            
        return {
            "success": True,
            "keyword": keyword,
            "period": {
                "from": date_from,
                "to": display_date_to
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
        # 날짜 기본값 설정
        if not date_from:
            date_from = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        # date_to 처리
        if date_to:
            # 사용자가 직접 지정한 경우, +1일 추가 (exclusive 처리)
            try:
                dt_to = datetime.strptime(date_to, "%Y-%m-%d")
                adjusted_date_to = (dt_to + timedelta(days=1)).strftime("%Y-%m-%d")
            except ValueError:
                adjusted_date_to = date_to
        else:
            # 기본값으로 오늘+1일 설정
            adjusted_date_to = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            
        # 기업 관련 뉴스 검색
        news_response = self.get_company_news(
            company_name=company_name,
            date_from=date_from,
            date_to=adjusted_date_to,  # 조정된 값 사용
            return_size=return_size
        )
        
        # 응답 포맷팅
        formatted_response = format_news_response(news_response)
        
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
        
        # UI 표시용 date_to (원래 값 사용)
        display_date_to = date_to or datetime.now().strftime("%Y-%m-%d")
            
        return {
            "success": True,
            "company": company_name,
            "period": {
                "from": date_from,
                "to": display_date_to
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
        start_date = end_date - timedelta(days=days)
        
        date_from = start_date.strftime("%Y-%m-%d")
        # BigKinds API의 until은 exclusive이므로 하루 더 추가
        date_to = (end_date + timedelta(days=1)).strftime("%Y-%m-%d")
        
        # 기업 뉴스 검색
        search_result = self.get_company_news(
            company_name=company_name,
            date_from=date_from,
            date_to=date_to,
            return_size=limit
        )
        
        # 응답 포맷팅
        formatted_result = format_news_response(search_result)
        
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
        reference_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """기업 기간별 뉴스 레포트 데이터 조회
        
        Args:
            company_name: 기업명
            report_type: 레포트 타입 (daily, weekly, monthly, quarterly, yearly)
            reference_date: 기준 날짜 (YYYY-MM-DD), 없으면 오늘 날짜 사용
            
        Returns:
            기간별 뉴스 레포트 데이터
        """
        # 기준 날짜 설정
        if not reference_date:
            reference_date = datetime.now().strftime("%Y-%m-%d")
        
        # 기준 날짜를 datetime 객체로 변환
        ref_date = datetime.strptime(reference_date, "%Y-%m-%d")
        
        # 레포트 타입에 따른 기간 설정
        # BigKinds API의 until은 exclusive이므로 하루 더 추가
        date_to = (ref_date + timedelta(days=1)).strftime("%Y-%m-%d")
        
        if report_type == "daily":
            date_from = ref_date.strftime("%Y-%m-%d")
            report_type_kr = "일일"
            limit = 20  # 하루 기사는 많지 않을 것으로 예상
        elif report_type == "weekly":
            date_from = (ref_date - timedelta(days=7)).strftime("%Y-%m-%d")
            report_type_kr = "주간"
            limit = 30
        elif report_type == "monthly":
            date_from = (ref_date - timedelta(days=30)).strftime("%Y-%m-%d")
            report_type_kr = "월간"
            limit = 50
        elif report_type == "quarterly":
            date_from = (ref_date - timedelta(days=90)).strftime("%Y-%m-%d")
            report_type_kr = "분기"
            limit = 70
        elif report_type == "yearly":
            date_from = (ref_date - timedelta(days=365)).strftime("%Y-%m-%d")
            report_type_kr = "연간"
            limit = 100
        else:
            # 기본값은 weekly
            date_from = (ref_date - timedelta(days=7)).strftime("%Y-%m-%d")
            report_type_kr = "주간"
            limit = 30
        
        # 기업 뉴스 검색
        search_result = self.get_company_news(
            company_name=company_name,
            date_from=date_from,
            date_to=date_to,
            return_size=limit
        )
        
        # 응답 포맷팅
        formatted_result = format_news_response(search_result)
        
        return {
            "success": True,
            "company": company_name,
            "report_type": report_type,
            "report_type_kr": report_type_kr,
            "reference_date": reference_date,
            "period": {
                "from": date_from,
                "to": date_to
            },
            "articles": formatted_result.get("documents", []),
            "total_found": formatted_result.get("total_hits", 0)
        }
    
    # 호환성을 위한 래퍼 메소드들
    def search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """기존 코드 호환성을 위한 래퍼 메소드"""
        return self.search_news(**params)
    
    def issue_ranking(self, date: str, provider: Optional[List[str]] = None) -> Dict[str, Any]:
        """기존 코드 호환성을 위한 래퍼 메소드"""
        # 카테고리 코드 전달 (provider 파라미터가 있는 경우)
        category_code = None
        if provider and len(provider) > 0:
            # 첫 번째 provider 코드를 카테고리 코드로 사용
            category_code = provider[0]
        
        return self.get_issue_ranking(date=date, category_code=category_code)
    
    def today_category_keyword(self) -> Dict[str, Any]:
        """기존 코드 호환성을 위한 래퍼 메소드"""
        response = self._make_request("GET", API_ENDPOINTS["today_category_keyword"], params={})
        return response
    
    # 포맷팅 메서드들 추가
    def format_news_response(self, api_response: Dict[str, Any]) -> Dict[str, Any]:
        """뉴스 검색 API 응답 포맷팅"""
        return format_news_response(api_response)
    
    def format_issue_ranking_response(self, api_response: Dict[str, Any]) -> Dict[str, Any]:
        """이슈 랭킹 API 응답 포맷팅"""
        return format_issue_ranking_response(api_response)
    
    def format_quotation_response(self, api_response: Dict[str, Any]) -> Dict[str, Any]:
        """인용문 검색 API 응답 포맷팅"""
        return format_quotation_response(api_response)
    
    def generate_related_questions(
        self,
        keyword: str,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        max_questions: int = 10,
        cluster_count: int = 5,
        max_recursion_depth: int = 2,
        min_articles_per_query: int = 3
    ) -> List[Dict[str, Any]]:
        """키워드 기반 연관 질문 생성
        
        Args:
            keyword: 초기 검색 키워드
            date_from: 시작일 (YYYY-MM-DD)
            date_to: 종료일 (YYYY-MM-DD)
            max_questions: 생성할 최대 질문 수
            cluster_count: 키워드 클러스터링 그룹 수
            max_recursion_depth: 쿼리 확장 최대 재귀 깊이
            min_articles_per_query: 유효한 쿼리로 판단할 최소 기사 수
            
        Returns:
            생성된 연관 질문 목록
        """
        import numpy as np
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.cluster import KMeans
        from sklearn.metrics.pairwise import cosine_similarity
        import re
        
        self.logger.info(f"'{keyword}' 키워드 기반 연관 질문 생성 시작")
        
        # 1. 키워드 수집 & 초기 검색
        # 1-1. 초기 뉴스 검색
        news_result = self.search_news(
            query=keyword,
            date_from=date_from,
            date_to=date_to,
            return_size=30
        )
        formatted_news = format_news_response(news_result)
        
        if not formatted_news.get("documents"):
            self.logger.warning(f"'{keyword}' 검색 결과 없음")
            return []
        
        # 1-2. 연관 키워드 수집
        related_keywords = self.get_related_keywords(
            keyword=keyword,
            date_from=date_from,
            date_to=date_to,
            max_count=30
        )
        
        # 1-3. TopN 키워드 수집
        topn_keywords = self.get_keyword_topn(
            keyword=keyword,
            date_from=date_from,
            date_to=date_to,
            limit=30
        )
        
        # 1-4. 인기 검색어 수집 (참고용)
        popular_keywords_result = self.get_popular_keywords(days=7, limit=20)
        popular_keywords = []
        if popular_keywords_result.get("formatted_keywords"):
            popular_keywords = [item.get("keyword") for item in popular_keywords_result.get("formatted_keywords", [])]
        
        # 2. 키워드 필터링 & 점수화
        # 2-1. 모든 키워드 병합 및 중복 제거
        all_keywords = []
        # 연관어 키워드 (가중치: 1.5)
        for idx, kw in enumerate(related_keywords):
            all_keywords.append({
                "keyword": kw,
                "source": "related",
                "rank": idx + 1,
                "weight": 1.5 * (1.0 / (idx + 1)),
                "has_original": keyword.lower() in kw.lower()
            })
        
        # TopN 키워드 (가중치: 1.2)
        for idx, kw in enumerate(topn_keywords):
            all_keywords.append({
                "keyword": kw,
                "source": "topn",
                "rank": idx + 1,
                "weight": 1.2 * (1.0 / (idx + 1)),
                "has_original": keyword.lower() in kw.lower()
            })
        
        # 인기 검색어 (가중치: 1.0)
        for idx, kw in enumerate(popular_keywords):
            all_keywords.append({
                "keyword": kw,
                "source": "popular",
                "rank": idx + 1,
                "weight": 1.0 * (1.0 / (idx + 1)),
                "has_original": keyword.lower() in kw.lower()
            })
        
        # 2-2. 키워드 필터링
        # - 최소 길이 2자 이상
        # - 숫자만으로 구성된 키워드 제외
        # - 특수문자만으로 구성된 키워드 제외
        filtered_keywords = []
        seen_keywords = set()
        
        for kw_data in all_keywords:
            kw = kw_data["keyword"]
            
            # 이미 처리한 키워드 건너뛰기
            if kw.lower() in seen_keywords:
                continue
                
            # 필터링 조건
            if len(kw) < 2:
                continue
            if re.match(r'^\d+$', kw):
                continue
            if re.match(r'^[^\w\s가-힣]+$', kw):
                continue
                
            # 원래 키워드와 동일한 경우 (대소문자 무시)
            if kw.lower() == keyword.lower():
                continue
                
            # 통과한 키워드 추가
            filtered_keywords.append(kw_data)
            seen_keywords.add(kw.lower())
        
        # 키워드가 없으면 빈 결과 반환
        if not filtered_keywords:
            self.logger.warning(f"'{keyword}' 관련 필터링된 키워드 없음")
            return []
            
        # 2-3. 키워드 가중치 추가 점수화
        # - 원본 키워드 포함 시 보너스
        # - 중복 출현 시 보너스
        scored_keywords = []
        keyword_scores = {}
        
        for kw_data in filtered_keywords:
            kw = kw_data["keyword"]
            score = kw_data["weight"]
            
            # 원본 키워드 포함 보너스
            if kw_data["has_original"]:
                score *= 1.3
                
            # 키워드 점수 누적
            if kw in keyword_scores:
                keyword_scores[kw] += score
            else:
                keyword_scores[kw] = score
        
        # 점수화된 키워드 목록 생성
        for kw, score in keyword_scores.items():
            scored_keywords.append({
                "keyword": kw,
                "score": score
            })
            
        # 점수 기준 내림차순 정렬
        scored_keywords.sort(key=lambda x: x["score"], reverse=True)
        
        # 상위 키워드만 선택 (클러스터링 효율성 위해)
        top_keywords = scored_keywords[:min(50, len(scored_keywords))]
        
        # 3. 클러스터링으로 대표 키워드 선정
        # 3-1. 텍스트 벡터화
        keyword_texts = [item["keyword"] for item in top_keywords]
        
        # 데이터가 충분하지 않으면 클러스터링 건너뛰기
        if len(keyword_texts) < cluster_count:
            representative_keywords = keyword_texts
        else:
            try:
                # TF-IDF 벡터화
                vectorizer = TfidfVectorizer()
                X = vectorizer.fit_transform(keyword_texts)
                
                # K-means 클러스터링
                actual_clusters = min(cluster_count, len(keyword_texts))
                kmeans = KMeans(n_clusters=actual_clusters, random_state=42)
                kmeans.fit(X)
                
                # 각 클러스터 중심에 가장 가까운 키워드 선택
                centers = kmeans.cluster_centers_
                representative_keywords = []
                
                for i in range(actual_clusters):
                    # 현재 클러스터에 속한 키워드 인덱스
                    cluster_indices = np.where(kmeans.labels_ == i)[0]
                    
                    if len(cluster_indices) > 0:
                        # 클러스터 내 각 키워드와 중심 간의 유사도 계산
                        cluster_vectors = X[cluster_indices]
                        center_vector = centers[i].reshape(1, -1)
                        similarities = cosine_similarity(cluster_vectors, center_vector)
                        
                        # 가장 유사한 키워드 선택
                        most_similar_idx = cluster_indices[np.argmax(similarities)]
                        representative_keywords.append(keyword_texts[most_similar_idx])
                        
                        # 충분히 큰 클러스터면 두 번째로 유사한 키워드도 추가
                        if len(cluster_indices) >= 5 and len(representative_keywords) < max_questions:
                            # 이미 선택된 인덱스 제외
                            remaining_indices = [idx for idx in cluster_indices if idx != most_similar_idx]
                            if remaining_indices:
                                remaining_vectors = X[remaining_indices]
                                second_similarities = cosine_similarity(remaining_vectors, center_vector)
                                second_similar_idx = remaining_indices[np.argmax(second_similarities)]
                                representative_keywords.append(keyword_texts[second_similar_idx])
            except Exception as e:
                self.logger.error(f"클러스터링 오류: {str(e)}")
                # 오류 발생 시 점수 기준 상위 키워드 사용
                representative_keywords = [item["keyword"] for item in top_keywords[:cluster_count]]
        
        # 4. 쿼리 변형 & 재귀 확장 탐색
        # 4-1. 쿼리 변형 생성 함수
        def generate_query_variants(base_keyword, expand_keyword):
            variants = []
            
            # 정교화(AND) 변형
            variants.append({
                "type": "AND",
                "query": f"{base_keyword} {expand_keyword}",
                "description": f"{base_keyword}와(과) {expand_keyword}에 관한"
            })
            
            # 확장(OR) 변형
            variants.append({
                "type": "OR",
                "query": f"{base_keyword} OR {expand_keyword}",
                "description": f"{base_keyword} 또는 {expand_keyword}에 관한"
            })
            
            # 제외(NOT) 변형 - base_keyword와 expand_keyword가 충분히 다른 경우만
            if base_keyword.lower() not in expand_keyword.lower() and expand_keyword.lower() not in base_keyword.lower():
                variants.append({
                    "type": "NOT",
                    "query": f"{base_keyword} NOT {expand_keyword}",
                    "description": f"{expand_keyword}을(를) 제외한 {base_keyword}에 관한"
                })
                
            return variants
        
        # 4-2. 재귀 확장 탐색 함수
        def explore_queries(base_keyword, keywords, depth=0, results=None):
            if results is None:
                results = []
                
            # 최대 재귀 깊이 초과 시 중단
            if depth >= max_recursion_depth:
                return results
                
            # 결과 수 제한 도달 시 중단
            if len(results) >= max_questions:
                return results[:max_questions]
                
            for kw in keywords:
                # 이미 충분한 결과가 있으면 중단
                if len(results) >= max_questions:
                    break
                    
                # 쿼리 변형 생성
                variants = generate_query_variants(base_keyword, kw)
                
                for variant in variants:
                    # 결과 제한 확인
                    if len(results) >= max_questions:
                        break
                        
                    # 이미 동일한 쿼리가 있는지 확인
                    if any(r["query"] == variant["query"] for r in results):
                        continue
                    
                    # 변형 쿼리로 뉴스 검색
                    search_result = self.search_news(
                        query=variant["query"],
                        date_from=date_from,
                        date_to=date_to,
                        return_size=min_articles_per_query
                    )
                    
                    formatted_result = format_news_response(search_result)
                    article_count = len(formatted_result.get("documents", []))
                    
                    # 최소 기사 수 이상인 경우만 유효한 쿼리로 간주
                    if article_count >= min_articles_per_query:
                        # 관련 기사 제목 추출 (질문 생성 참고용)
                        titles = [doc.get("title", "") for doc in formatted_result.get("documents", [])[:3]]
                        
                        result_item = {
                            "query": variant["query"],
                            "type": variant["type"],
                            "description": variant["description"],
                            "article_count": article_count,
                            "depth": depth,
                            "reference_titles": titles,
                            "question": ""  # 나중에 채워질 필드
                        }
                        
                        results.append(result_item)
                        
                        # 재귀 호출 (깊이 증가)
                        if depth < max_recursion_depth - 1 and len(results) < max_questions:
                            # 재귀 호출은 결과가 적은 경우만 수행
                            if article_count < 50:
                                # 이 쿼리 결과에서 키워드 추출
                                sub_keywords = []
                                try:
                                    sub_topn = self.get_keyword_topn(
                                        keyword=variant["query"],
                                        date_from=date_from,
                                        date_to=date_to,
                                        limit=5
                                    )
                                    sub_keywords = sub_topn[:2]  # 상위 2개만 사용
                                except:
                                    pass
                                
                                if sub_keywords:
                                    explore_queries(variant["query"], sub_keywords, depth+1, results)
            
            return results
        
        # 4-3. 쿼리 확장 실행
        expanded_queries = explore_queries(keyword, representative_keywords)
        
        # 5. 질문 생성 & 순위 매기기
        # 5-1. 질문 템플릿 정의
        question_templates = [
            "{keyword}의 최근 동향은?",
            "{keyword}에 대해 알려주세요",
            "{keyword}에 관한 최신 뉴스는?",
            "{keyword}의 주요 이슈는?",
            "{keyword}의 핵심 내용은?",
            "{keyword}에 대한 분석이 필요합니다",
            "{keyword}에 대해 더 자세히 알고 싶어요",
            "{keyword}의 영향은 무엇인가요?",
            "{keyword}와 관련된 중요 사항은?",
            "{keyword}에 대한 전문가 의견은?"
        ]
        
        # 5-2. 각 쿼리에 대한 질문 생성
        final_questions = []
        
        for query_data in expanded_queries:
            # 쿼리 유형에 따라 다른 템플릿 선택
            if query_data["type"] == "AND":
                template = "{keyword}에 대해 알려주세요"
            elif query_data["type"] == "OR":
                template = "{keyword}의 최근 동향은?"
            elif query_data["type"] == "NOT":
                template = "{keyword}에 관한 최신 뉴스는?"
            else:
                # 랜덤 템플릿 선택
                import random
                template = random.choice(question_templates)
            
            # 질문 생성
            question = template.format(keyword=query_data["description"])
            
            # 유니크한 질문인지 확인
            if not any(q["question"] == question for q in final_questions):
                query_data["question"] = question
                final_questions.append(query_data)
        
        # 5-3. 질문 점수화 및 정렬
        # - 기사 수가 많을수록 높은 점수
        # - 깊이가 낮을수록 높은 점수
        for q in final_questions:
            # 기사 수 정규화 (로그 스케일)
            article_score = np.log1p(q["article_count"]) / 10  # 0~1 범위로 정규화
            
            # 깊이 역수 (깊이가 낮을수록 높은 점수)
            depth_score = 1.0 / (q["depth"] + 1)
            
            # 최종 점수
            q["score"] = (0.7 * article_score) + (0.3 * depth_score)
        
        # 점수 기준 정렬
        final_questions.sort(key=lambda x: x["score"], reverse=True)
        
        # 최종 결과 형식 정리
        result_questions = []
        for idx, q in enumerate(final_questions[:max_questions]):
            result_questions.append({
                "id": idx + 1,
                "question": q["question"],
                "query": q["query"],
                "count": q["article_count"],
                "score": q["score"],
                "description": q["description"]
            })
        
        self.logger.info(f"'{keyword}' 키워드 관련 질문 {len(result_questions)}개 생성 완료")
        return result_questions 