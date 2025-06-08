"""
BigKinds API 클라이언트 패키지

실제 BigKinds OpenAPI 스펙에 맞춘 구현:
- 올바른 요청/응답 형식
- 필드 선택 기능 (fields)
- 서울경제신문 필터링
- 에러 처리 및 재시도 로직
- 키워드 기반 타임라인 및 상세 검색 기능
"""

from .client import BigKindsClient
from .constants import API_BASE_URL, API_ENDPOINTS, SEOUL_ECONOMIC, DEFAULT_NEWS_FIELDS

__all__ = [
    'BigKindsClient',
    'API_BASE_URL',
    'API_ENDPOINTS',
    'SEOUL_ECONOMIC',
    'DEFAULT_NEWS_FIELDS',
] 