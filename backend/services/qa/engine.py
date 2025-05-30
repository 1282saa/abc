"""
질의응답 시스템 메인 엔진

사용자 질의를 처리하고 뉴스 데이터 기반으로 응답을 생성하는 질의응답 엔진을 제공합니다.
다른 모든 모듈들을 통합하여 완전한 질의응답 파이프라인을 구성합니다.
"""

import os
import logging
import json
import asyncio
from typing import Dict, List, Any, Optional, Union, Tuple, Callable
from datetime import datetime
import time

# 프로젝트 루트 디렉토리 찾기
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.utils.logger import setup_logger
from backend.services.qa.vector_db import VectorDB

# 아직 생성하지 않은 모듈들 (나중에 추가 예정)
# from backend.services.qa.document_processor import DocumentProcessor
# from backend.services.qa.embeddings import EmbeddingService
# from backend.services.qa.retriever import Retriever
# from backend.services.qa.prompts import PromptTemplates
# from backend.services.qa.llm_handler import LLMHandler

class QAEngine:
    """뉴스 질의응답 시스템 메인 엔진 클래스"""
    
    def __init__(
            self,
            vector_db: Optional[VectorDB] = None,
            # embedding_service: Optional[EmbeddingService] = None,
            # document_processor: Optional[DocumentProcessor] = None,
            # retriever: Optional[Retriever] = None,
            # prompt_templates: Optional[PromptTemplates] = None,
            # llm_handler: Optional[LLMHandler] = None,
            config: Optional[Dict[str, Any]] = None
        ):
        """질의응답 엔진 초기화
        
        Args:
            vector_db: 벡터 DB 인스턴스
            embedding_service: 임베딩 서비스 인스턴스
            document_processor: 문서 처리기 인스턴스
            retriever: 검색기 인스턴스
            prompt_templates: 프롬프트 템플릿 인스턴스
            llm_handler: LLM 핸들러 인스턴스
            config: 설정 딕셔너리
        """
        self.logger = setup_logger("qa.engine")
        
        # 설정 로드
        self.config = config or {}
        
        # 기본 모듈 생성 또는 주입된 모듈 사용
        self.vector_db = vector_db or VectorDB()
        
        # 나중에 추가될 모듈들
        # self.embedding_service = embedding_service or EmbeddingService()
        # self.document_processor = document_processor or DocumentProcessor()
        # self.prompt_templates = prompt_templates or PromptTemplates()
        # self.llm_handler = llm_handler or LLMHandler()
        
        # 검색기는 다른 모듈들에 의존하므로 마지막에 생성
        # self.retriever = retriever or Retriever(
        #     vector_db=self.vector_db,
        #     embedding_service=self.embedding_service,
        #     document_processor=self.document_processor
        # )
        
        # 기본 설정
        self.default_search_results = self.config.get("default_search_results", 5)
        self.max_context_items = self.config.get("max_context_items", 8)
        
        self.logger.info("질의응답 엔진 초기화 완료")
    
    def get_vector_db_status(self) -> Dict[str, Any]:
        """벡터 데이터베이스 상태 조회
        
        Returns:
            상태 정보 딕셔너리
        """
        try:
            document_count = self.vector_db.get_document_count()
            
            return {
                "document_count": document_count,
                "collection_name": self.vector_db.collection_name,
                "persist_directory": self.vector_db.persist_directory,
                "status": "available"
            }
        except Exception as e:
            self.logger.error(f"벡터 DB 상태 조회 오류: {e}")
            return {
                "status": "error",
                "error": str(e)
            } 