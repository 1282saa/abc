"""
빅카인즈 API 클라이언트

고급 API 클라이언트 기능:
- 논리 연산자 지원 (AND, OR, NOT)
- hilight, fields 파라미터 지원
- 고급 정렬 옵션
- 중복 제거 및 필터링
"""

import os
import json
import time
import logging
import requests
from typing import Dict, List, Optional, Union, Any, Tuple
from pathlib import Path
from functools import lru_cache
from datetime import datetime, timedelta
import hashlib

# 프로젝트 루트 디렉토리 찾기
PROJECT_ROOT = Path(__file__).parent.parent.parent

import sys
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import API_BASE_URL, API_ENDPOINTS, PERFORMANCE

# 환경 변수에서 API 키 로드
API_KEY = os.environ.get("BIGKINDS_API_KEY", "")

# 서울경제신문 언론사 코드
SEOUL_ECONOMIC_DAILY_CODE = "02100311"

class BigKindsClient:
    """빅카인즈 API와 상호작용하는 고급 클라이언트 클래스"""
    
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
        
        # 중복 제거를 위한 해시 세트
        self._seen_news_ids = set()
        
    def _build_query(self, query: str, use_exact_match: bool = False) -> str:
        """검색 쿼리 최적화
        
        Args:
            query: 원본 검색어
            use_exact_match: 정확한 구문 매칭 사용 여부
            
        Returns:
            최적화된 쿼리 문자열
        """
        if use_exact_match and ' ' in query:
            # 정확한 구문 검색을 위해 따옴표로 감싸기
            return f'"{query}"'
        
        # 기본적으로 공백을 AND로 처리
        words = query.split()
        if len(words) > 1:
            return ' AND '.join(words)
        
        return query
    
    def _apply_filters(self, news_list: List[Dict[str, Any]], 
                      remove_duplicates: bool = True,
                      min_content_length: int = 100) -> List[Dict[str, Any]]:
        """뉴스 결과 필터링 및 후처리
        
        Args:
            news_list: 원본 뉴스 목록
            remove_duplicates: 중복 제거 여부
            min_content_length: 최소 본문 길이
            
        Returns:
            필터링된 뉴스 목록
        """
        filtered_news = []
        
        for news in news_list:
            # 중복 체크
            news_id = news.get('NEWS_ID', news.get('news_id', ''))
            if remove_duplicates and news_id in self._seen_news_ids:
                continue
            
            # 최소 본문 길이 체크
            content = news.get('CONTENT', news.get('content', ''))
            if len(content) < min_content_length:
                continue
            
            # 인사, 부고, 동정 등 제외
            title = news.get('TITLE', news.get('title', '')).lower()
            exclude_keywords = ['인사', '부고', '동정', '포토', '사진']
            if any(keyword in title for keyword in exclude_keywords):
                continue
            
            # 중복 제거용 ID 저장
            if remove_duplicates:
                self._seen_news_ids.add(news_id)
            
            filtered_news.append(news)
        
        return filtered_news
    
    def _make_request(self, endpoint: str, params: Dict[str, Any], 
                     retry_count: int = 3, backoff_factor: float = 2.0) -> Dict[str, Any]:
        """API 엔드포인트에 요청을 보내고 응답을 반환 (재시도 로직 포함)
        
        Args:
            endpoint: API 엔드포인트 경로
            params: 요청 파라미터
            retry_count: 최대 재시도 횟수
            backoff_factor: 백오프 배수
            
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
        
        for attempt in range(retry_count):
            try:
                self.logger.debug(f"API 요청 (시도 {attempt + 1}/{retry_count}): {url}")
                response = requests.post(url, json=params, headers=headers, timeout=self.timeout)
                
                # 429 (Rate Limit) 처리
                if response.status_code == 429:
                    wait_time = min(60, backoff_factor ** attempt)
                    retry_after = response.headers.get('Retry-After')
                    if retry_after:
                        wait_time = int(retry_after)
                    
                    self.logger.warning(f"Rate limit 도달. {wait_time}초 대기 후 재시도...")
                    time.sleep(wait_time)
                    continue
                
                response.raise_for_status()
                result = response.json()
                return result
            
            except requests.exceptions.RequestException as e:
                if attempt == retry_count - 1:
                    self.logger.error(f"API 요청 최종 실패: {e}")
                    raise
                
                wait_time = backoff_factor ** attempt
                self.logger.warning(f"API 요청 실패. {wait_time}초 후 재시도... ({e})")
                time.sleep(wait_time)
    
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
    
    def news_search_advanced(self, query: str, start_date: str, end_date: str,
                           provider: Optional[List[str]] = None,
                           category: Optional[List[str]] = None,
                           category_incident: Optional[List[str]] = None,
                           subject_info: Optional[List[str]] = None,
                           sort: Union[str, Dict[str, str]] = "date",
                           hilight: int = 200,
                           fields: Optional[List[str]] = None,
                           size: int = 10,
                           page: int = 1,
                           use_seoul_economic: bool = False,
                           use_exact_match: bool = False) -> Dict[str, Any]:
        """고급 뉴스 검색 API 호출
        
        Args:
            query: 검색어 (AND, OR, NOT 연산자 지원)
            start_date: 시작 날짜 (YYYY-MM-DD)
            end_date: 종료 날짜 (YYYY-MM-DD)
            provider: 언론사 코드 리스트
            category: 카테고리 코드 리스트
            category_incident: 사건/사고 카테고리 코드 리스트
            subject_info: 주제어 태그 필터
            sort: 정렬 기준 (date, rank) 또는 다중 정렬 딕셔너리
            hilight: 하이라이트 문자 수
            fields: 반환할 필드 리스트
            size: 페이지 크기
            page: 페이지 번호
            use_seoul_economic: 서울경제신문만 검색 여부
            use_exact_match: 정확한 구문 매칭 사용 여부
            
        Returns:
            뉴스 검색 결과
        """
        # 쿼리 최적화
        optimized_query = self._build_query(query, use_exact_match)
        
        params = {
            "query": optimized_query,
            "published_at": {
                "from": start_date,
                "until": end_date
            },
            "return_from": (page - 1) * size,
            "return_size": size,
            "hilight": hilight
        }
        
        # 서울경제신문만 검색
        if use_seoul_economic:
            params["provider"] = [SEOUL_ECONOMIC_DAILY_CODE]
        elif provider:
            params["provider"] = provider
        
        # 카테고리 필터
        if category:
            params["category"] = category
        
        if category_incident:
            params["category_incident"] = category_incident
        
        # 주제어 필터
        if subject_info:
            params["subject_info"] = subject_info
        
        # 정렬 설정
        if isinstance(sort, str):
            params["sort"] = {"date": "desc" if sort == "date" else "asc"}
        else:
            params["sort"] = sort
        
        # 필드 선택
        if fields:
            params["fields"] = fields
        else:
            # 기본 필드 세트
            params["fields"] = [
                "NEWS_ID", "TITLE", "CONTENT", "URL",
                "PROVIDER_CODE", "PROVIDER_NAME", 
                "PROVIDER_LINK_PAGE", "PUBLISHED_AT",
                "REPORTER", "IMAGES", "CATEGORY",
                "CATEGORY_INCIDENT", "BYLINE",
                "TOPIC_RANK"
            ]
        
        result = self._make_request(API_ENDPOINTS["news_search"], params)
        
        # 결과 필터링 적용
        if result.get("result") == "success" and "return_object" in result:
            documents = result["return_object"].get("documents", [])
            filtered_docs = self._apply_filters(documents)
            result["return_object"]["documents"] = filtered_docs
            result["return_object"]["filtered_count"] = len(filtered_docs)
        
        return result
    
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
    
    def get_news_timeline(self, query: str, start_date: str, end_date: str,
                         interval: str = "day") -> List[Tuple[str, int]]:
        """뉴스 타임라인 데이터 조회 (키워드 빈도 추이)
        
        Args:
            query: 검색어
            start_date: 시작 날짜
            end_date: 종료 날짜
            interval: 시간 단위 (hour, day, week, month)
            
        Returns:
            [(날짜, 기사수)] 형태의 리스트
        """
        result = self.time_line(query, start_date, end_date, interval=interval)
        
        if result.get("result") != "success":
            return []
        
        timeline_data = []
        time_data = result.get("return_object", {}).get("plot", [])
        
        for point in time_data:
            date = point.get("date", "")
            count = point.get("count", 0)
            timeline_data.append((date, count))
        
        return timeline_data
    
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
    
    def find_peak_periods(self, query: str, start_date: str, end_date: str,
                         threshold_multiplier: float = 2.0) -> List[Dict[str, Any]]:
        """키워드 빈도 피크 기간 찾기
        
        Args:
            query: 검색어
            start_date: 시작 날짜
            end_date: 종료 날짜
            threshold_multiplier: 평균 대비 피크 판단 배수
            
        Returns:
            피크 기간 정보 리스트
        """
        timeline = self.get_news_timeline(query, start_date, end_date)
        
        if not timeline:
            return []
        
        # 평균 계산
        counts = [count for _, count in timeline]
        avg_count = sum(counts) / len(counts) if counts else 0
        threshold = avg_count * threshold_multiplier
        
        # 피크 찾기
        peaks = []
        for i, (date, count) in enumerate(timeline):
            if count >= threshold:
                # 피크 시작
                peak_start = date
                peak_end = date
                peak_count = count
                
                # 연속된 피크 찾기
                j = i + 1
                while j < len(timeline) and timeline[j][1] >= threshold:
                    peak_end = timeline[j][0]
                    peak_count = max(peak_count, timeline[j][1])
                    j += 1
                
                peaks.append({
                    "start_date": peak_start,
                    "end_date": peak_end,
                    "peak_count": peak_count,
                    "avg_multiplier": peak_count / avg_count if avg_count > 0 else 0
                })
        
        return peaks
    
    def get_representative_news(self, query: str, date: str, 
                              top_n: int = 5) -> List[Dict[str, Any]]:
        """특정 날짜의 대표 뉴스 가져오기
        
        Args:
            query: 검색어
            date: 날짜 (YYYY-MM-DD)
            top_n: 상위 뉴스 개수
            
        Returns:
            대표 뉴스 리스트
        """
        # 정확도순 + 최신순 정렬로 대표 뉴스 선정
        result = self.news_search_advanced(
            query=query,
            start_date=date,
            end_date=date,
            sort=[{"_score": "desc"}, {"date": "desc"}],
            size=top_n * 2  # 필터링을 고려해 여유있게 가져오기
        )
        
        if result.get("result") != "success":
            return []
        
        documents = result.get("return_object", {}).get("documents", [])
        return documents[:top_n]
    
    def clear_duplicate_cache(self):
        """중복 제거용 캐시 초기화"""
        self._seen_news_ids.clear()


# 사용 예제
if __name__ == "__main__":
    # 로깅 설정
    logging.basicConfig(level=logging.INFO)
    
    # 클라이언트 생성
    client = BigKindsClient()
    
    # 고급 검색 테스트
    try:
        # 삼성전자 AND 반도체 검색 (서울경제신문만)
        result = client.news_search_advanced(
            query="삼성전자 AND 반도체",
            start_date="2024-01-01",
            end_date="2024-01-31",
            use_seoul_economic=True,
            hilight=300,
            size=10
        )
        
        if result.get("result") == "success":
            docs = result.get("return_object", {}).get("documents", [])
            print(f"검색 결과: {len(docs)}건")
            
            for doc in docs[:3]:
                print(f"\n제목: {doc.get('TITLE')}")
                print(f"언론사: {doc.get('PROVIDER_NAME')}")
                print(f"날짜: {doc.get('PUBLISHED_AT')}")
        
        # 피크 기간 찾기
        peaks = client.find_peak_periods(
            query="삼성전자",
            start_date="2024-01-01",
            end_date="2024-12-31"
        )
        
        print(f"\n피크 기간: {len(peaks)}개")
        for peak in peaks:
            print(f"- {peak['start_date']} ~ {peak['end_date']}: {peak['peak_count']}건")
            
    except Exception as e:
        print(f"테스트 실패: {e}") 