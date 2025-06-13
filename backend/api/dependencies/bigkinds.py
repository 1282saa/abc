"""
BigKinds API 클라이언트 의존성 정의

FastAPI 엔드포인트에서 사용할 BigKinds 클라이언트 의존성을 정의합니다.
"""

from ..clients.bigkinds import BigKindsClient
import os

def get_bigkinds_client() -> BigKindsClient:
    """BigKinds 클라이언트 인스턴스 가져오기 (다중 API 키 지원)"""
    # 클라이언트가 자동으로 환경변수에서 다중 키를 읽도록 함
    return BigKindsClient() 