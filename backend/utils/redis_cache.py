"""
Redis 캐싱 유틸리티

이 모듈은 Redis를 사용한 캐싱 기능을 제공합니다.
"""

import json
import os
from typing import Any, Optional, Union, Callable
from functools import wraps
import hashlib
import logging

# 로거 설정
logger = logging.getLogger(__name__)

# Redis 라이브러리 선택적 임포트
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    logger.warning("Redis 라이브러리가 설치되지 않았습니다. 캐싱이 비활성화됩니다.")
    REDIS_AVAILABLE = False

# Redis 클라이언트 인스턴스
_redis_client = None

def get_redis_client() -> Optional['redis.Redis']:
    """Redis 클라이언트 인스턴스를 반환합니다."""
    global _redis_client
    
    # Redis 라이브러리가 없으면 None 반환
    if not REDIS_AVAILABLE:
        return None
        
    if _redis_client is None:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        try:
            _redis_client = redis.Redis.from_url(
                redis_url, 
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5
            )
            _redis_client.ping()
            logger.info("Redis 연결 성공")
        except Exception as e:
            logger.warning(f"Redis 연결 실패: {str(e)}, 캐싱이 비활성화됩니다")
            _redis_client = None
    return _redis_client

def cache_set(key: str, value: Any, expire_seconds: int = 21600) -> bool:
    """
    Redis에 키-값 쌍을 저장합니다.
    
    Args:
        key: 캐시 키
        value: 저장할 값 (JSON 직렬화 가능)
        expire_seconds: 만료 시간(초), 기본값 6시간(21600초)
    
    Returns:
        bool: 성공 여부
    """
    client = get_redis_client()
    if not client:
        return False
    
    try:
        serialized = json.dumps(value, ensure_ascii=False)
        return client.set(key, serialized, ex=expire_seconds)
    except Exception as e:
        logger.error(f"Redis 캐시 저장 오류: {e}")
        return False

def cache_get(key: str) -> Optional[Any]:
    """
    Redis에서 키에 해당하는 값을 가져옵니다.
    
    Args:
        key: 캐시 키
    
    Returns:
        캐시된 값 또는 None (캐시 미스)
    """
    client = get_redis_client()
    if not client:
        return None
    
    try:
        value = client.get(key)
        if value:
            return json.loads(value)
        return None
    except Exception as e:
        logger.error(f"Redis 캐시 조회 오류: {e}")
        return None

def generate_cache_key(prefix: str, *args, **kwargs) -> str:
    """
    인자들을 기반으로 일관된 캐시 키를 생성합니다.
    
    Args:
        prefix: 키 접두사
        *args, **kwargs: 키 생성에 사용할 인자들
    
    Returns:
        str: 생성된 캐시 키
    """
    key_parts = [prefix]
    
    # 위치 인자 추가
    for arg in args:
        key_parts.append(str(arg))
    
    # 키워드 인자 추가 (정렬하여 일관성 유지)
    for k in sorted(kwargs.keys()):
        key_parts.append(f"{k}:{kwargs[k]}")
    
    # 전체 문자열 해시화
    key_str = "_".join(key_parts)
    hash_obj = hashlib.md5(key_str.encode())
    hash_str = hash_obj.hexdigest()
    
    return f"{prefix}:{hash_str}"

def cached(prefix: str, ttl: int = 21600):
    """
    함수 결과를 캐싱하는 데코레이터
    
    Args:
        prefix: 캐시 키 접두사
        ttl: 캐시 유효 시간(초), 기본값 6시간
    
    Returns:
        Callable: 데코레이터 함수
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Redis가 사용 불가능하면 캐싱 없이 함수 실행
            if not REDIS_AVAILABLE:
                return await func(*args, **kwargs)
                
            # 캐시 키 생성
            cache_key = generate_cache_key(prefix, *args, **kwargs)
            
            # 캐시 확인
            cached_result = cache_get(cache_key)
            if cached_result is not None:
                logger.debug(f"캐시 적중: {cache_key}")
                return cached_result
            
            # 함수 실행
            result = await func(*args, **kwargs)
            
            # 결과 캐싱
            cache_set(cache_key, result, ttl)
            logger.debug(f"캐시 저장: {cache_key}")
            
            return result
        return wrapper
    return decorator 