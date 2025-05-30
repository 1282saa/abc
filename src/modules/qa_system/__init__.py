"""
QA 시스템 패키지

빅카인즈 뉴스 데이터 기반 질의응답 시스템 모듈들을 제공합니다.
이 패키지는 벡터 DB, 임베딩, 검색, LLM 응답 생성 등의 기능을 통합하여 종합적인 질의응답 시스템을 구성합니다.
"""

from .vectordb import VectorDB
from .document_processor import DocumentProcessor
from .embeddings import EmbeddingService
from .retriever import Retriever
from .prompt_templates import PromptTemplates
from .llm_handler import LLMHandler
from .qa_engine import QAEngine

__all__ = [
    'VectorDB',
    'DocumentProcessor',
    'EmbeddingService',
    'Retriever',
    'PromptTemplates',
    'LLMHandler',
    'QAEngine'
]

__version__ = "0.1.0"
