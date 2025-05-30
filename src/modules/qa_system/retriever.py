"""
검색 모듈

사용자 질의를 처리하고 벡터 데이터베이스에서 관련 뉴스 기사를 검색하는 기능을 제공합니다.
"""

import os
import logging
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
import asyncio

# 프로젝트 루트 디렉토리 찾기
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.logger import setup_logger
from src.modules.qa_system.vectordb import VectorDB
from src.modules.qa_system.document_processor import DocumentProcessor
from src.modules.qa_system.embeddings import EmbeddingService

class Retriever:
    """뉴스 검색 클래스"""
    
    def __init__(
            self,
            vector_db: Optional[VectorDB] = None,
            embedding_service: Optional[EmbeddingService] = None,
            document_processor: Optional[DocumentProcessor] = None
        ):
        """검색 모듈 초기화
        
        Args:
            vector_db: 벡터 DB 인스턴스 (없으면 새로 생성)
            embedding_service: 임베딩 서비스 인스턴스 (없으면 새로 생성)
            document_processor: 문서 처리기 인스턴스 (없으면 새로 생성)
        """
        self.logger = setup_logger("qa.retriever")
        
        # 의존성 주입 또는 생성
        self.vector_db = vector_db or VectorDB()
        self.embedding_service = embedding_service or EmbeddingService()
        self.document_processor = document_processor or DocumentProcessor()
        
        self.logger.info("검색 모듈 초기화 완료")
    
    async def search(
            self, 
            query: str, 
            n_results: int = 5,
            filter_metadata: Optional[Dict[str, Any]] = None,
            date_range: Optional[Tuple[str, str]] = None,
            providers: Optional[List[str]] = None,
            categories: Optional[List[str]] = None
        ) -> List[Dict[str, Any]]:
        """쿼리로 관련 뉴스 검색
        
        Args:
            query: 검색 쿼리
            n_results: 반환할 결과 수
            filter_metadata: 기타 필터링 메타데이터
            date_range: 날짜 범위 (시작일, 종료일)
            providers: 뉴스 제공자 필터
            categories: 카테고리 필터
            
        Returns:
            검색 결과 리스트
        """
        # 쿼리 전처리
        processed_query = self.document_processor.preprocess_query(query)
        
        self.logger.info(f"검색 시작: '{processed_query}', 결과 수: {n_results}")
        
        # 필터 조건 구성
        filter_conditions = self._build_filter_conditions(
            filter_metadata, date_range, providers, categories
        )
        
        # 쿼리 임베딩 생성
        query_embedding = await self.embedding_service.get_embeddings([processed_query])
        if not query_embedding or len(query_embedding) == 0:
            self.logger.error("쿼리 임베딩 생성 실패")
            return []
        
        # 벡터 검색 실행
        search_results = self.vector_db.query(
            text=processed_query,
            n_results=n_results,
            filter_metadata=filter_conditions
        )
        
        self.logger.info(f"검색 완료: {len(search_results)}개 결과 찾음")
        return search_results
    
    def _build_filter_conditions(
            self,
            filter_metadata: Optional[Dict[str, Any]],
            date_range: Optional[Tuple[str, str]],
            providers: Optional[List[str]],
            categories: Optional[List[str]]
        ) -> Dict[str, Any]:
        """필터 조건 구성
        
        Args:
            filter_metadata: 기타 필터링 메타데이터
            date_range: 날짜 범위 (시작일, 종료일)
            providers: 뉴스 제공자 필터
            categories: 카테고리 필터
            
        Returns:
            ChromaDB 필터 조건
        """
        filter_conditions = filter_metadata.copy() if filter_metadata else {}
        
        # 날짜 범위 필터
        if date_range and len(date_range) == 2:
            start_date, end_date = date_range
            
            # 날짜 형식 검증
            try:
                start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
                end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
                
                # end_date가 start_date보다 이전인 경우 교체
                if end_date_obj < start_date_obj:
                    start_date, end_date = end_date, start_date
                
                # 날짜가 너무 오래된 경우(10년 이상) 제한
                max_date_range = timedelta(days=365 * 10)  # 10년
                if end_date_obj - start_date_obj > max_date_range:
                    start_date_obj = end_date_obj - max_date_range
                    start_date = start_date_obj.strftime("%Y-%m-%d")
                
                # 날짜 필터 적용
                filter_conditions["date"] = {"$gte": start_date, "$lte": end_date}
                
            except ValueError:
                self.logger.warning(f"날짜 형식 오류: {date_range}")
        
        # 제공자 필터
        if providers and len(providers) > 0:
            filter_conditions["provider"] = {"$in": providers}
        
        # 카테고리 필터
        if categories and len(categories) > 0:
            filter_conditions["category"] = {"$in": categories}
        
        return filter_conditions
    
    async def hybrid_search(
            self, 
            query: str, 
            n_results: int = 5,
            filter_metadata: Optional[Dict[str, Any]] = None,
            hybrid_alpha: float = 0.5,  # 0: 키워드만, 1: 벡터만, 0.5: 균등 혼합
        ) -> List[Dict[str, Any]]:
        """키워드 검색과 벡터 검색을 혼합한 하이브리드 검색
        
        Args:
            query: 검색 쿼리
            n_results: 반환할 결과 수
            filter_metadata: 필터링 메타데이터
            hybrid_alpha: 벡터 검색 가중치 (0~1)
            
        Returns:
            검색 결과 리스트
        """
        self.logger.info(f"하이브리드 검색 시작: '{query}', 결과 수: {n_results}, 벡터 가중치: {hybrid_alpha}")
        
        # TODO: 하이브리드 검색 구현
        # 현재는 단순 벡터 검색만 지원
        search_results = await self.search(query, n_results, filter_metadata)
        
        return search_results
    
    async def date_sorted_search(
            self, 
            query: str, 
            n_results: int = 10,
            filter_metadata: Optional[Dict[str, Any]] = None,
            order: str = "desc"  # "asc" 또는 "desc"
        ) -> List[Dict[str, Any]]:
        """날짜순으로 정렬된 검색 결과 반환
        
        Args:
            query: 검색 쿼리
            n_results: 반환할 결과 수 (더 많은 결과를 가져와서 정렬 후 자름)
            filter_metadata: 필터링 메타데이터
            order: 정렬 순서 ("asc": 오름차순, "desc": 내림차순)
            
        Returns:
            날짜순 정렬된 검색 결과 리스트
        """
        # 더 많은 결과를 가져와서 정렬
        search_n = min(n_results * 3, 50)  # 요청 결과의 3배 또는 최대 50개
        
        # 기본 검색 실행
        search_results = await self.search(query, search_n, filter_metadata)
        
        # 날짜 정렬
        try:
            # 날짜별 정렬
            sorted_results = sorted(
                search_results,
                key=lambda x: datetime.strptime(x.get("metadata", {}).get("date", "2000-01-01"), "%Y-%m-%d"),
                reverse=(order.lower() == "desc")  # 내림차순이면 reverse=True
            )
        except Exception as e:
            self.logger.error(f"날짜 정렬 오류: {e}")
            sorted_results = search_results
        
        # 요청 개수만큼 자르기
        return sorted_results[:n_results]
    
    async def provider_grouped_search(
            self, 
            query: str, 
            n_providers: int = 3,
            n_per_provider: int = 2,
            filter_metadata: Optional[Dict[str, Any]] = None
        ) -> Dict[str, List[Dict[str, Any]]]:
        """뉴스 제공자별로 그룹화된 검색 결과 반환
        
        Args:
            query: 검색 쿼리
            n_providers: 포함할 최대 제공자 수
            n_per_provider: 제공자별 최대 결과 수
            filter_metadata: 필터링 메타데이터
            
        Returns:
            제공자별 그룹화된 검색 결과 딕셔너리
        """
        # 충분한 수의 결과 가져오기
        search_n = n_providers * n_per_provider * 2  # 필요한 양의 2배
        
        # 기본 검색 실행
        search_results = await self.search(query, search_n, filter_metadata)
        
        # 제공자별 그룹화
        provider_groups = {}
        
        for result in search_results:
            provider = result.get("metadata", {}).get("provider", "unknown")
            
            # 새 제공자 그룹 생성 또는 기존 그룹에 추가
            if provider not in provider_groups:
                # 최대 제공자 수 제한
                if len(provider_groups) >= n_providers:
                    continue
                provider_groups[provider] = []
            
            # 제공자별 결과 수 제한
            if len(provider_groups[provider]) < n_per_provider:
                provider_groups[provider].append(result)
        
        return provider_groups 