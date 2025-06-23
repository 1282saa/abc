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
from backend.utils.query_processor import preprocess_query

class BigKindsClient:
    """빅카인즈 API 클라이언트"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """빅카인즈 API 클라이언트 초기화
        
        Args:
            api_key: 빅카인즈 API 키
            base_url: API 기본 URL
        """
        # 단일 API 키 설정
        self.api_key = api_key or os.environ.get("BIGKINDS_KEY", "")
        
        # API 키 존재 여부 확인 (없으면 경고만 출력)
        if not self.api_key:
            self.logger.warning("BigKinds API 키가 설정되지 않았습니다. 제한된 기능만 사용할 수 있습니다.")
            self.api_key = "NO_API_KEY"  # 기본값 설정
        
        self.base_url = base_url or API_BASE_URL
        self.logger = setup_logger("api.bigkinds")
        self.timeout = 30
        
        # API 키 상태 로깅
        self.logger.info("BigKinds API 키가 설정되었습니다.")
        
    def _make_request(self, method: str, endpoint: str, argument: Dict[str, Any] = None, params: Dict[str, Any] = None, provider: Optional[List[str]] = None) -> Dict[str, Any]:
        """빅카인즈 API 요청 실행
        
        Args:
            method: HTTP 메서드 (GET, POST)
            endpoint: API 엔드포인트
            argument: POST 요청 시 사용할 argument 데이터
            params: GET 요청 시 사용할 쿼리 파라미터
            provider: 언론사 목록 (현재는 사용되지 않음)
            
        Returns:
            API 응답 데이터
        """
        api_key = self.api_key
        
        # URL 올바르게 구성 (중복 슬래시 방지)
        if self.base_url.endswith('/') and endpoint.startswith('/'):
            url = f"{self.base_url}{endpoint[1:]}"
        elif not self.base_url.endswith('/') and not endpoint.startswith('/'):
            url = f"{self.base_url}/{endpoint}"
        else:
            url = f"{self.base_url}{endpoint}"
        
        # GET 요청 처리 (params 사용)
        if method == "GET" and params:
            self.logger.info(f"BigKinds API GET 요청: {url}")
            self.logger.debug(f"요청 파라미터: {params}")
            
            try:
                # params에 access_key 추가
                params["access_key"] = api_key
                
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
                "access_key": api_key,
                "argument": argument or {}
            }
            
            headers = {
                "Content-Type": "application/json"
            }
            
            self.logger.info(f"BigKinds API POST 요청: {endpoint}")
            self.logger.info(f"전체 URL: {url}")
            self.logger.info(f"API 키: {api_key}")
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
                self.logger.info(f"응답 상태: {response.status_code}")
                self.logger.info(f"응답 내용 (첫 200자): {str(result)[:200]}")
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
    
    def search_news_with_fallback(
        self,
        keyword: str,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        return_from: int = 0,
        return_size: int = 10,
        sort: Union[Dict, List[Dict]] = {"_score": "desc"},
        provider: Optional[List[str]] = None,
        category: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        빅카인즈 API 최적화된 다단계 폴백 검색
        
        사용자 의도에 맞는 최적의 검색 결과를 제공하기 위해:
        1. 키워드 전처리 및 의도 분석
        2. 정확도 우선 → 범위 확대 순으로 다단계 검색
        3. 실시간성 요구 시 최신 날짜 범위 조정
        
        Args:
            keyword: 사용자 원본 질문 (예: "네이버 주가 실황")
            date_from: 시작일 (YYYY-MM-DD)  
            date_to: 종료일 (YYYY-MM-DD)
            return_size: 반환할 결과 수
            sort: 정렬 기준 (기본: _score 내림차순)
            provider: 언론사 목록
            category: 카테고리 목록
            
        Returns:
            검색 결과
        """
        from backend.utils.query_processor import (
            preprocess_query, create_fallback_queries, analyze_query_intent
        )
        
        # 1. 사용자 질문 분석
        intent = analyze_query_intent(keyword)
        self.logger.info(f"질문 분석: {keyword} → {intent}")
        
        # 2. 키워드 추출
        keywords = preprocess_query(keyword)
        if not keywords:
            self.logger.warning(f"'{keyword}'에서 유효한 키워드를 추출할 수 없습니다.")
            return {"result": -1, "reason": "검색할 키워드가 없습니다.", "return_object": {}}
        
        self.logger.info(f"추출된 키워드: {keywords}")
        
        # 3. 실시간성 요구 시 날짜 범위 조정
        if intent.get("time_sensitive") and not date_from:
            # 실시간/최신 요구 시 최근 3일로 제한
            date_from = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
            self.logger.info(f"실시간성 요구로 날짜 범위 조정: {date_from} ~ {date_to}")
        
        # 4. 다단계 폴백 쿼리 생성
        fallback_queries = create_fallback_queries(keywords)
        
        # 5. 단계별 검색 실행
        for i, (query, description) in enumerate(fallback_queries, 1):
            self.logger.info(f"검색 {i}단계 시도: {description}")
            self.logger.info(f"쿼리: {query}")
            
            try:
                results = self.search_news(
                    query=query,
                    date_from=date_from,
                    date_to=date_to,
                    return_from=return_from,
                    return_size=return_size,
                    sort=sort,
                    provider=provider,
                    category=category
                )
                
                total_hits = results.get("return_object", {}).get("total_hits", 0)
                
                if total_hits > 0:
                    self.logger.info(f"✅ {i}단계 검색 성공: {total_hits}개 결과")
                    return results
                else:
                    self.logger.warning(f"❌ {i}단계 검색 결과 없음")
                    
            except Exception as e:
                self.logger.error(f"❌ {i}단계 검색 중 오류: {str(e)}")
                continue
        
        # 6. 모든 검색 실패 시
        self.logger.error(f"모든 폴백 검색 실패: '{keyword}' → {keywords}")
        return {
            "result": -1, 
            "reason": f"'{keyword}'에 대한 검색 결과가 없습니다. 다른 키워드로 시도해보세요.",
            "return_object": {"total_hits": 0, "documents": []}
        }

    def search_news(
        self,
        query: str = "",
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        provider: Optional[List[str]] = None,
        category: Optional[List[str]] = None,
        fields: Optional[List[str]] = None,
        sort: Union[Dict, List[Dict]] = {"_score": "desc"},
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
            sort: 정렬 기준
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
            "sort": sort,
            "return_from": return_from,
            "return_size": return_size,
            "fields": fields,
            "hilight": 1  # 하이라이트 정보 요청
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
        
        return self._make_request("POST", API_ENDPOINTS["news_search"], argument=argument, provider=provider)
    
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
        endpoint = API_ENDPOINTS["word_related"]
        
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
        
        try:
            response = self._make_request("GET", endpoint, params=params)
            self.logger.debug(f"연관어 API 응답: {response}")
            
            if response.get("success", False):
                # 연관어 결과 추출 및 가공
                related_words = response.get("result", {}).get("words", [])
                # 단어만 추출 (가중치나 기타 메타데이터 제외)
                result = []
                for word in related_words:
                    if isinstance(word, dict) and "word" in word:
                        result.append(word["word"])
                    elif isinstance(word, str):
                        result.append(word)
                return result
            return []
        except Exception as e:
            self.logger.error(f"연관어 조회 오류: {e}")
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
        endpoint = API_ENDPOINTS["word_topn"]
        
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
        
        try:
            response = self._make_request("GET", endpoint, params=params)
            self.logger.debug(f"TopN API 응답: {response}")
            
            if response.get("success", False):
                # TopN 결과 추출 및 가공
                topn_words = response.get("result", {}).get("words", [])
                # 단어만 추출
                result = []
                for word in topn_words:
                    if isinstance(word, dict) and "word" in word:
                        result.append(word["word"])
                    elif isinstance(word, str):
                        result.append(word)
                return result
            return []
        except Exception as e:
            self.logger.error(f"TopN 조회 오류: {e}")
            return []
    
    def get_word_cloud_keywords(
        self,
        keyword: str,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        limit: int = 30
    ) -> List[Dict[str, Any]]:
        """BigKinds 연관어 분석 API (TOPIC RANK 알고리즘)를 사용한 키워드 추출
        
        Args:
            keyword: 검색할 키워드
            date_from: 시작일 (YYYY-MM-DD)
            date_to: 종료일 (YYYY-MM-DD)
            limit: 반환할 키워드 수
            
        Returns:
            연관어 목록 (키워드, 가중치 포함)
        """
        endpoint = API_ENDPOINTS["word_cloud"]
        
        # 날짜 기본값 설정
        if not date_from:
            date_from = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not date_to:
            date_to = datetime.now().strftime("%Y-%m-%d")
            
        # BigKinds word_cloud API는 POST 방식을 사용
        argument = {
            "query": keyword,
            "max": limit,
            "published_at": {
                "from": date_from,
                "until": date_to
            }
        }
        
        try:
            response = self._make_request("POST", endpoint, argument=argument)
            self.logger.debug(f"Word Cloud API 응답: {response}")
            
            # BigKinds API는 result=0이 성공
            if response.get("result") == 0:
                # 연관어 결과 추출 및 가공 (실제 응답 구조: nodes 배열)
                return_object = response.get("return_object", {})
                nodes = return_object.get("nodes", [])
                result = []
                
                for node in nodes:
                    if isinstance(node, dict):
                        # BigKinds word_cloud API의 실제 응답 구조
                        word = node.get("name", "")
                        weight = node.get("weight", 0.0)
                        level = node.get("level", 1)  # 키워드 레벨 (1=핵심, 2=중요, 3=연관)
                        
                        if word and len(word) >= 2:  # 2글자 이상만 허용
                            result.append({
                                "keyword": word,
                                "weight": float(weight),
                                "count": int(weight),  # weight를 count로 사용
                                "level": level  # 키워드 중요도 레벨
                            })
                
                # 가중치 정규화 (최대값을 1.0으로)
                if result:
                    max_weight = max(item["weight"] for item in result)
                    if max_weight > 0:
                        for item in result:
                            item["weight"] = item["weight"] / max_weight
                
                # 가중치 기준 내림차순 정렬하여 상위 limit개만 반환
                result.sort(key=lambda x: x["weight"], reverse=True)
                return result[:limit]
            else:
                self.logger.warning(f"Word Cloud API 응답 실패: result={response.get('result')}, reason={response.get('reason', '')}")
                return []
                
        except Exception as e:
            self.logger.error(f"Word Cloud API 조회 오류: {e}")
            return []
    
    def extract_keywords(
        self,
        title: str = "",
        sub_title: str = "",
        content: str = ""
    ) -> Dict[str, List[str]]:
        """기사 내용에서 키워드 추출
        
        Args:
            title: 기사 제목
            sub_title: 부제목
            content: 기사 본문
            
        Returns:
            각 필드별 추출된 키워드 목록
        """
        argument = {
            "title": title,
            "sub_title": sub_title,
            "content": content
        }
        
        result = self._make_request("POST", API_ENDPOINTS["keyword"], argument=argument)
        
        if result.get("result") == 0:
            return_obj = result.get("return_object", {}).get("result", {})
            return {
                "title": return_obj.get("title", "").split() if return_obj.get("title") else [],
                "sub_title": return_obj.get("sub_title", "").split() if return_obj.get("sub_title") else [],
                "content": return_obj.get("content", "").split() if return_obj.get("content") else []
            }
        
        return {"title": [], "sub_title": [], "content": []}
    
    def extract_features(
        self,
        title: str = "",
        sub_title: str = "",
        content: str = ""
    ) -> Dict[str, List[Dict[str, Any]]]:
        """기사 내용에서 키워드와 중요도 점수 추출
        
        Args:
            title: 기사 제목
            sub_title: 부제목
            content: 기사 본문
            
        Returns:
            각 필드별 추출된 키워드와 점수 목록
        """
        argument = {
            "title": title,
            "sub_title": sub_title,
            "content": content
        }
        
        result = self._make_request("POST", API_ENDPOINTS["feature"], argument=argument)
        
        if result.get("result") == 0:
            return_obj = result.get("return_object", {}).get("result", {})
            formatted_result = {}
            
            for field in ["title", "sub_title", "content"]:
                field_data = return_obj.get(field, "")
                keywords = []
                
                if field_data:
                    # "키워드|점수" 형식을 파싱
                    for item in field_data.split():
                        if "|" in item:
                            keyword, score = item.split("|", 1)
                            keywords.append({
                                "keyword": keyword,
                                "score": float(score)
                            })
                
                formatted_result[field] = keywords
            
            return formatted_result
        
        return {"title": [], "sub_title": [], "content": []}
    
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
        return_size: int = 20,
        provider: Optional[List[str]] = None,
        exclude_prism: bool = True
    ) -> Dict[str, Any]:
        """기업 관련 뉴스 검색
        
        Args:
            company_name: 기업명
            date_from: 시작일
            date_to: 종료일
            return_size: 반환할 결과 수
            provider: 언론사 필터 (예: ["서울경제"])
            exclude_prism: PRISM 기사 제외 여부
            
        Returns:
            기업 뉴스 검색 결과
        """
        # 날짜 기본값 설정
        if not date_from:
            date_from = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not date_to:
            # BigKinds API의 until은 exclusive이므로 하루 더 추가
            date_to = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

        # 검색 쿼리 처리: 이미 따옴표와 괄호가 포함된 쿼리는 그대로 사용
        if company_name.startswith('(') and ('"' in company_name or "'" in company_name):
            enhanced_query = company_name
            self.logger.debug(f"확장된 쿼리 그대로 사용: {enhanced_query}")
        else:
            # preprocess_query를 사용하여 핵심 키워드 검색으로 변경
            keywords = preprocess_query(company_name)
            enhanced_query = ' AND '.join([f'"{k}"' for k in keywords])
            self.logger.debug(f"핵심 키워드 AND 검색: {enhanced_query}")
        
        # PRISM 기사 제외 (서울경제의 경우)
        if exclude_prism and provider and "서울경제" in provider:
            # 이미 PRISM 제외 조건이 있는지 확인
            if 'AND NOT "PRISM"' not in enhanced_query:
                enhanced_query += ' AND NOT "PRISM"'
                self.logger.debug(f"PRISM 제외 조건 추가: {enhanced_query}")

        self.logger.info(f"최종 검색 쿼리: {enhanced_query}")

        # 기업명으로 검색 (search_news를 직접 호출하도록 변경)
        return self.search_news(
            query=enhanced_query,
            date_from=date_from,
            date_to=date_to,
            provider=provider,  # 언론사 필터 추가
            fields=[
                "news_id",
                "title",
                "content", 
                "published_at",
                "category",
                "provider_name",
                "provider_code",  # 언론사 코드 추가
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
        """키워드 기반 뉴스 검색 (Fallback 로직 적용)
        
        Args:
            keyword: 검색 키워드 또는 질문
            date_from: 시작일
            date_to: 종료일
            return_size: 반환할 결과 수
            
        Returns:
            키워드 관련 뉴스 검색 결과
        """
        return self.search_news_with_fallback(
            keyword=keyword,
            date_from=date_from,
            date_to=date_to,
            return_size=return_size,
            sort=[{"date": "desc"}, {"_score": "desc"}] # 최신순 + 정확도순 정렬
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
    
    def get_news_by_ids(self, news_ids: List[str]) -> Dict[str, Any]:
        """뉴스 ID로 뉴스 목록 조회
        
        여러 뉴스 ID로 뉴스 내용을 조회
        
        Args:
            news_ids: 뉴스 ID 목록
            
        Returns:
            뉴스 목록
        """
        # 뉴스 ID로 검색
        return self.search_news(
            news_ids=news_ids,
            fields=DEFAULT_NEWS_FIELDS,
            return_size=len(news_ids)
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
        return_size: int = 30,
        provider: Optional[List[str]] = None,
        exclude_prism: bool = True
    ) -> Dict[str, Any]:
        """기업별 뉴스 타임라인 조회
        
        Args:
            company_name: 기업명
            date_from: 시작일
            date_to: 종료일
            return_size: 반환할 결과 수
            provider: 언론사 필터 (예: ["서울경제"])
            exclude_prism: PRISM 기사 제외 여부
            
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
            return_size=return_size,
            provider=provider,  # 언론사 필터 추가
            exclude_prism=exclude_prism  # PRISM 기사 제외 옵션 추가
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
    
    def quick_count(
        self,
        query: str,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> int:
        """검색 결과 갯수만 빠르게 확인 (return_size=0)
        
        Args:
            query: 검색 쿼리
            date_from: 시작일 (YYYY-MM-DD)
            date_to: 종료일 (YYYY-MM-DD)
            
        Returns:
            검색 결과 갯수
        """
        # 기본 날짜 설정 (최근 30일)
        if not date_from:
            date_from = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not date_to:
            # BigKinds API의 until은 exclusive이므로 하루 더 추가
            date_to = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        # 결과 수만 확인하기 위한 최소 요청
        argument = {
            "published_at": {
                "from": date_from,
                "until": date_to
            },
            "query": query,
            "return_size": 0  # 결과는 필요 없음
        }
        
        result = self._make_request("POST", API_ENDPOINTS["news_search"], argument=argument)
        if result.get("result") == 0:
            return int(result.get("return_object", {}).get("total_hits", 0))
        return 0

    async def build_related_questions(
        self,
        keyword: str,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        max_questions: int = 7
    ) -> List[Dict[str, Any]]:
        """새로운 "AND 우선, 부족하면 OR" 전략을 사용한 연관 질문 생성
        
        Args:
            keyword: 검색 키워드
            date_from: 시작일 (YYYY-MM-DD)
            date_to: 종료일 (YYYY-MM-DD)
            max_questions: 반환할 최대 질문 수
            
        Returns:
            생성된 질문 목록
        """
        from backend.services.news.question_builder import build_questions
        
        self.logger.info(f"키워드 '{keyword}' 연관 질문 생성 (새 알고리즘)")
        
        # 기본 날짜 설정
        if not date_from:
            date_from = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not date_to:
            # BigKinds API의 until은 exclusive이므로 하루 더 추가
            date_to = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        # 질문 빌더 호출
        questions = await build_questions(
            base=keyword,
            client=self,
            date_from=date_from,
            date_until=date_to
        )
        
        return questions[:max_questions] 