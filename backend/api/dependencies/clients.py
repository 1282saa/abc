"""
API 클라이언트 의존성 정의

FastAPI 엔드포인트에서 사용할 클라이언트 의존성을 정의합니다.
"""

from ..clients.bigkinds import BigKindsClient
import os

def get_bigkinds_client() -> BigKindsClient:
    """BigKinds 클라이언트 인스턴스 가져오기"""
    api_key = os.environ.get("BIGKINDS_KEY", "")
    return BigKindsClient(api_key=api_key) 