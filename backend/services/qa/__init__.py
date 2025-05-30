"""
질의응답 서비스 패키지

뉴스 기반 질의응답 시스템의 핵심 구성 요소를 제공합니다.
"""

from backend.services.qa.vector_db import VectorDB
from backend.services.qa.engine import QAEngine

__all__ = [
    "VectorDB",
    "QAEngine"
]

__version__ = "0.1.0" 