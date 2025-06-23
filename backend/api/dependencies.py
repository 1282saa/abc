"""
API 라우터에서 사용될 의존성 주입(Dependency Injection)을 정의합니다.
"""
from backend.api.clients.bigkinds.client import BigKindsClient

# BigKindsClient의 싱글턴 인스턴스를 관리하기 위한 변수
_bigkinds_client_instance = None

def get_bigkinds_client() -> BigKindsClient:
    """
    BigKindsClient의 싱글턴 인스턴스를 반환하는 의존성 함수.
    이 함수를 통해 모든 API 요청이 동일한 클라이언트 인스턴스를 공유하게 됩니다.
    """
    global _bigkinds_client_instance
    if _bigkinds_client_instance is None:
        # 첫 호출 시 인스턴스 생성
        _bigkinds_client_instance = BigKindsClient()
    return _bigkinds_client_instance 