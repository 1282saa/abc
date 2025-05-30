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

from src.utils.logger import setup_logger
from src.modules.qa_system.vectordb import VectorDB
from src.modules.qa_system.document_processor import DocumentProcessor
from src.modules.qa_system.embeddings import EmbeddingService
from src.modules.qa_system.retriever import Retriever
from src.modules.qa_system.prompt_templates import PromptTemplates
from src.modules.qa_system.llm_handler import LLMHandler

class QAEngine:
    """뉴스 질의응답 시스템 메인 엔진 클래스"""
    
    def __init__(
            self,
            vector_db: Optional[VectorDB] = None,
            embedding_service: Optional[EmbeddingService] = None,
            document_processor: Optional[DocumentProcessor] = None,
            retriever: Optional[Retriever] = None,
            prompt_templates: Optional[PromptTemplates] = None,
            llm_handler: Optional[LLMHandler] = None,
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
        self.embedding_service = embedding_service or EmbeddingService()
        self.document_processor = document_processor or DocumentProcessor()
        self.vector_db = vector_db or VectorDB()
        self.prompt_templates = prompt_templates or PromptTemplates()
        self.llm_handler = llm_handler or LLMHandler()
        
        # 검색기는 다른 모듈들에 의존하므로 마지막에 생성
        self.retriever = retriever or Retriever(
            vector_db=self.vector_db,
            embedding_service=self.embedding_service,
            document_processor=self.document_processor
        )
        
        # 기본 설정
        self.default_search_results = self.config.get("default_search_results", 5)
        self.max_context_items = self.config.get("max_context_items", 8)
        
        self.logger.info("질의응답 엔진 초기화 완료")
    
    async def process_query(self, 
                     query: str, 
                     stream: bool = False,
                     query_type: Optional[str] = None,
                     search_params: Optional[Dict[str, Any]] = None) -> Union[Dict[str, Any], AsyncGenerator[str, None]]:
        """사용자 질의 처리
        
        Args:
            query: 사용자 질의
            stream: 스트리밍 응답 여부
            query_type: 질의 유형 (None이면 자동 감지)
            search_params: 검색 파라미터
            
        Returns:
            응답 딕셔너리 또는 스트리밍 응답 제너레이터
        """
        search_params = search_params or {}
        
        start_time = time.time()
        self.logger.info(f"질의 처리 시작: '{query}'")
        
        # 1. 질의 의도 분석
        if not query_type:
            query_type = self.prompt_templates.analyze_query_intent(query)
        
        self.logger.info(f"질의 유형 감지: {query_type}")
        
        # 2. 관련 문서 검색
        n_results = search_params.get("n_results", self.default_search_results)
        filter_metadata = search_params.get("filter_metadata")
        date_range = search_params.get("date_range")
        providers = search_params.get("providers")
        categories = search_params.get("categories")
        
        # 요약이나 타임라인은 더 많은 문서 검색
        if query_type == "summarize":
            n_results = max(n_results, 8)
        elif query_type == "timeline":
            n_results = max(n_results, 15)
        
        # 검색 실행
        search_results = await self.retriever.search(
            query=query,
            n_results=n_results,
            filter_metadata=filter_metadata,
            date_range=date_range,
            providers=providers,
            categories=categories
        )
        
        # 검색 결과 없으면 빈 응답
        if not search_results or len(search_results) == 0:
            self.logger.warning(f"검색 결과 없음: '{query}'")
            return {"answer": "죄송합니다. 질문에 관련된 뉴스를 찾을 수 없습니다. 다른 질문을 해주세요.", "contexts": []}
        
        self.logger.info(f"{len(search_results)}개 관련 문서 찾음")
        
        # 3. 프롬프트 생성
        # 질의 유형에 따라 다른 프롬프트 템플릿 사용
        max_context_items = min(self.max_context_items, len(search_results))
        
        if query_type == "summarize":
            prompts = self.prompt_templates.get_summarization_prompt(
                query=query, 
                contexts=search_results[:max_context_items]
            )
        elif query_type == "timeline":
            prompts = self.prompt_templates.get_timeline_prompt(
                query=query, 
                contexts=search_results[:max_context_items]
            )
        else:  # 기본 qa
            prompts = self.prompt_templates.get_qa_prompt(
                query=query, 
                contexts=search_results[:max_context_items]
            )
        
        # 4. LLM 응답 생성
        if stream:
            # 스트리밍 응답 생성
            streaming_response = await self.llm_handler.generate_response(
                prompts=prompts,
                stream=True
            )
            
            # 생성 시간 기록
            elapsed_time = time.time() - start_time
            self.logger.info(f"질의 처리 완료 (스트리밍) (시간: {elapsed_time:.2f}초)")
            
            return streaming_response
        else:
            # 일반 응답 생성
            answer = await self.llm_handler.generate_response(
                prompts=prompts,
                stream=False
            )
            
            # 5. 결과 조합
            response = {
                "query": query,
                "query_type": query_type,
                "answer": answer,
                "contexts": [
                    {
                        "text": result.get("text"),
                        "metadata": result.get("metadata", {}),
                        "similarity": result.get("similarity", 0)
                    }
                    for result in search_results[:max_context_items]
                ]
            }
            
            # 생성 시간 기록
            elapsed_time = time.time() - start_time
            self.logger.info(f"질의 처리 완료 (시간: {elapsed_time:.2f}초)")
            
            return response
    
    async def add_documents(self, documents: List[Dict[str, Any]]) -> int:
        """문서 추가
        
        Args:
            documents: 추가할 문서 리스트
            
        Returns:
            추가된 문서 수
        """
        # 문서 처리 (정제, 청크 분할 등)
        processed_documents = self.document_processor.process_news_data(documents)
        
        # 벡터 DB에 추가
        self.vector_db.add_documents(processed_documents)
        
        return len(processed_documents)
    
    async def generate_summary(self, 
                        query: str,
                        search_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """뉴스 요약 생성
        
        Args:
            query: 요약할 주제 또는 질문
            search_params: 검색 파라미터
            
        Returns:
            요약 결과 딕셔너리
        """
        # 요약 특화 처리
        return await self.process_query(
            query=query,
            query_type="summarize",
            search_params=search_params
        )
    
    async def generate_timeline(self, 
                         query: str,
                         search_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """시간순 타임라인 생성
        
        Args:
            query: 타임라인 주제
            search_params: 검색 파라미터
            
        Returns:
            타임라인 결과 딕셔너리
        """
        # 타임라인 특화 처리
        # 날짜 정렬 검색 적용
        if not search_params:
            search_params = {}
        
        # 검색 결과 수 증가
        search_params["n_results"] = search_params.get("n_results", 15)
        
        return await self.process_query(
            query=query,
            query_type="timeline",
            search_params=search_params
        )
    
    async def batch_process_queries(self, 
                             queries: List[str],
                             query_types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """여러 질의 일괄 처리
        
        Args:
            queries: 질의 리스트
            query_types: 질의 유형 리스트 (None이면 자동 감지)
            
        Returns:
            응답 리스트
        """
        if query_types and len(query_types) != len(queries):
            raise ValueError("질의 목록과 유형 목록의 길이가 일치해야 합니다")
        
        # 질의 유형 처리
        if not query_types:
            query_types = [self.prompt_templates.analyze_query_intent(q) for q in queries]
        
        # 태스크 생성
        tasks = []
        for query, query_type in zip(queries, query_types):
            task = asyncio.create_task(
                self.process_query(query=query, query_type=query_type)
            )
            tasks.append(task)
        
        # 모든 태스크 완료 대기
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 예외 처리
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"배치 처리 항목 {i} 오류: {result}")
                results[i] = {
                    "query": queries[i], 
                    "error": str(result),
                    "answer": "처리 중 오류가 발생했습니다."
                }
        
        return results
    
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