"""
데이터 처리 유틸리티 모듈

API 응답 데이터 처리, 캐싱, 전처리 등의 유틸리티 함수를 제공
"""

import json
import hashlib
import redis
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import os

# 프로젝트 루트 디렉토리 찾기
PROJECT_ROOT = Path(__file__).parent.parent.parent

import sys
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import CACHE

# 로거 설정
logger = logging.getLogger(__name__)

class DataProcessor:
    """데이터 처리 유틸리티 클래스"""
    
    def __init__(self, use_cache: bool = True):
        """데이터 처리기 초기화
        
        Args:
            use_cache: 캐싱 사용 여부
        """
        self.use_cache = use_cache
        self.cache = None
        
        if use_cache:
            try:
                self.cache = redis.Redis(
                    host=os.environ.get('CACHE_HOST', CACHE.get('host', 'localhost')),
                    port=int(os.environ.get('CACHE_PORT', CACHE.get('port', 6379))),
                    db=0
                )
                self.cache.ping()  # 연결 테스트
                self.cache_ttl = int(os.environ.get('CACHE_TTL', CACHE.get('ttl', 3600)))
                logger.info("Redis 캐시 연결 성공")
            except Exception as e:
                logger.warning(f"Redis 캐시 연결 실패: {e}")
                logger.warning("로컬 파일 캐싱으로 대체됩니다.")
                self.cache = None
    
    def get_cached_data(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """캐시에서 데이터 가져오기
        
        Args:
            cache_key: 캐시 키
            
        Returns:
            캐시된 데이터 또는 None
        """
        if not self.use_cache:
            return None
        
        # Redis 캐시가 있는 경우
        if self.cache:
            try:
                cached_data = self.cache.get(cache_key)
                if cached_data:
                    return json.loads(cached_data)
            except Exception as e:
                logger.error(f"캐시 읽기 오류: {e}")
        
        # 파일 기반 캐시 시도
        cache_dir = PROJECT_ROOT / "cache"
        cache_file = cache_dir / f"{cache_key}.json"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    
                # 캐시 만료 확인
                if 'timestamp' in cache_data:
                    cache_time = datetime.fromisoformat(cache_data['timestamp'])
                    if datetime.now() - cache_time < timedelta(seconds=self.cache_ttl):
                        return cache_data['data']
            except Exception as e:
                logger.error(f"파일 캐시 읽기 오류: {e}")
        
        return None
    
    def set_cached_data(self, cache_key: str, data: Dict[str, Any]) -> bool:
        """데이터를 캐시에 저장
        
        Args:
            cache_key: 캐시 키
            data: 저장할 데이터
            
        Returns:
            저장 성공 여부
        """
        if not self.use_cache:
            return False
        
        # Redis 캐시가 있는 경우
        if self.cache:
            try:
                self.cache.setex(
                    cache_key,
                    self.cache_ttl,
                    json.dumps(data, ensure_ascii=False)
                )
                return True
            except Exception as e:
                logger.error(f"캐시 저장 오류: {e}")
        
        # 파일 기반 캐시 사용
        try:
            cache_dir = PROJECT_ROOT / "cache"
            cache_dir.mkdir(exist_ok=True)
            
            cache_file = cache_dir / f"{cache_key}.json"
            
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'data': data
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
                
            return True
        except Exception as e:
            logger.error(f"파일 캐시 저장 오류: {e}")
            return False
    
    def generate_cache_key(self, prefix: str, params: Dict[str, Any]) -> str:
        """API 파라미터를 기반으로 캐시 키 생성
        
        Args:
            prefix: 캐시 키 접두사
            params: API 요청 파라미터
            
        Returns:
            캐시 키
        """
        # 파라미터를 정렬하여 일관된 키 생성
        param_str = json.dumps(params, sort_keys=True)
        hash_object = hashlib.md5(param_str.encode())
        hash_str = hash_object.hexdigest()
        
        return f"{prefix}_{hash_str}"
    
    def normalize_news_data(self, api_response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """API 응답에서 뉴스 데이터 정규화
        
        Args:
            api_response: 빅카인즈 API 응답
            
        Returns:
            정규화된 뉴스 데이터 목록
        """
        news_list = []
        
        try:
            documents = api_response.get('documents', [])
            for doc in documents:
                news = {
                    'news_id': doc.get('news_id', ''),
                    'title': doc.get('title', ''),
                    'content': doc.get('content', ''),
                    'published_at': doc.get('published_at', ''),
                    'provider': doc.get('provider', ''),
                    'category': doc.get('category', ''),
                    'byline': doc.get('byline', ''),
                    'provider_link_page': doc.get('provider_link_page', ''),
                    'images': doc.get('images', []),
                    'keywords': self._extract_keywords_from_doc(doc)
                }
                news_list.append(news)
        except Exception as e:
            logger.error(f"뉴스 데이터 정규화 오류: {e}")
        
        return news_list
    
    def _extract_keywords_from_doc(self, doc: Dict[str, Any]) -> List[str]:
        """문서에서 키워드 추출
        
        Args:
            doc: 뉴스 문서 데이터
            
        Returns:
            키워드 목록
        """
        keywords = []
        
        # 분석된 개체명 추출
        if 'analyzed_information' in doc:
            info = doc.get('analyzed_information', {})
            
            # 인물 개체명
            for person in info.get('persons', []):
                keywords.append(person.get('name', ''))
            
            # 장소 개체명
            for location in info.get('locations', []):
                keywords.append(location.get('name', ''))
            
            # 기관 개체명
            for organization in info.get('organizations', []):
                keywords.append(organization.get('name', ''))
            
            # 키워드 필드
            for keyword in info.get('keywords', []):
                keywords.append(keyword.get('name', ''))
        
        # 중복 제거 및 빈 문자열 제거
        return list(set([k for k in keywords if k]))
    
    def convert_timeline_data(self, api_response: Dict[str, Any]) -> Dict[str, Any]:
        """타임라인 API 응답 데이터 변환
        
        Args:
            api_response: 빅카인즈 타임라인 API 응답
            
        Returns:
            변환된 타임라인 데이터
        """
        result = {
            'total_count': 0,
            'dates': [],
            'counts': []
        }
        
        try:
            timeline = api_response.get('timeline', {})
            
            # 날짜순으로 정렬
            sorted_dates = sorted(timeline.keys())
            
            result['dates'] = sorted_dates
            result['counts'] = [timeline[date] for date in sorted_dates]
            result['total_count'] = sum(result['counts'])
        except Exception as e:
            logger.error(f"타임라인 데이터 변환 오류: {e}")
        
        return result
    
    def normalize_quotation_data(self, api_response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """인용문 API 응답 데이터 정규화
        
        Args:
            api_response: 빅카인즈 인용문 API 응답
            
        Returns:
            정규화된 인용문 데이터 목록
        """
        quotations = []
        
        try:
            docs = api_response.get('documents', [])
            for doc in docs:
                for quote in doc.get('quotations', []):
                    quotation = {
                        'news_id': doc.get('news_id', ''),
                        'title': doc.get('title', ''),
                        'source': quote.get('source', ''),
                        'quotation': quote.get('quotation', ''),
                        'published_at': doc.get('published_at', ''),
                        'provider': doc.get('provider', '')
                    }
                    quotations.append(quotation)
        except Exception as e:
            logger.error(f"인용문 데이터 정규화 오류: {e}")
        
        return quotations