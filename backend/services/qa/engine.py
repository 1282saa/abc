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
from datetime import datetime, timedelta
import time

# 프로젝트 루트 디렉토리 찾기
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.utils.logger import setup_logger
from backend.services.qa.vector_db import VectorDB
from backend.api.clients.bigkinds_client import BigKindsClient

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
        
        # 벡터 DB 초기화 (선택)
        try:
            self.vector_db = vector_db or VectorDB()
        except Exception as e:
            self.logger.warning(f"벡터 DB 초기화 실패 (개발 모드로 계속): {e}")
            self.vector_db = None
        
        # BigKinds 클라이언트 초기화
        try:
            # 환경변수 재로드
            from dotenv import load_dotenv
            load_dotenv()
            
            self.bigkinds = BigKindsClient()
            self.logger.info(f"BigKinds 클라이언트 초기화 성공: API 키 {os.environ.get('BIGKINDS_KEY', 'NONE')[:10]}...")
        except Exception as e:
            self.logger.warning(
                "BIGKINDS_KEY 미설정 또는 클라이언트 초기화 실패 – 개발 모드로 동작: %s",
                e,
            )
            self.bigkinds = None
        
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
        if self.vector_db is None:
            return {
                "status": "development_mode",
                "message": "벡터 DB 개발 중 - Mock 모드로 동작",
                "document_count": 0
            }
        
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
    
    async def process_query(self, query: str, stream: bool = False, search_params: Optional[Dict[str, Any]] = None) -> Union[Dict[str, Any], Any]:
        """사용자 질의를 처리하고 응답을 생성
        
        Args:
            query: 사용자 질의
            stream: 스트리밍 응답 여부
            search_params: 검색 파라미터
            
        Returns:
            처리된 질의응답 결과 또는 스트리밍 제너레이터
        """
        self.logger.info(f"질의 처리 시작: '{query}', 스트리밍: {stream}")
        
        try:
            # 현재는 임시 구현 - 추후 실제 QA 로직으로 교체
            if stream:
                # 스트리밍 응답 시뮬레이션
                return self._stream_mock_response(query)
            else:
                # 일반 응답
                return await self._generate_response(query, search_params)
                
        except Exception as e:
            self.logger.error(f"질의 처리 오류: {e}", exc_info=True)
            raise
    
    async def generate_summary(self, query: str, search_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """주제에 대한 뉴스 요약 생성
        
        Args:
            query: 검색어/주제
            search_params: 검색 파라미터
            
        Returns:
            요약 결과
            {
                "query": 검색어/URL,
                "summary": 요약 내용,
                "key_points": [주요 포인트들],
                "article_count": 기사 수,
                "generated_at": 생성 시간,
                "status": 상태 코드
            }
        """
        self.logger.info(f"요약 생성 시작: '{query}'")
        
        try:
            # BigKinds 클라이언트 사용 가능 여부 확인
            if self.bigkinds is None:
                # 개발 모드 응답
                return {
                    "query": query,
                    "summary": f"'{query}'에 대한 뉴스 요약입니다. 현재는 개발 중인 기능으로 임시 응답을 제공합니다.",
                    "key_points": [
                        f"{query} 관련 주요 동향",
                        f"{query}의 최근 변화",
                        f"{query}에 대한 전문가 의견"
                    ],
                    "article_count": 0,
                    "generated_at": datetime.now().isoformat(),
                    "status": "development_mode",
                    "message": "BIGKINDS_KEY가 설정되지 않았습니다. 환경 변수를 설정하고 서버를 재시작하세요."
                }
            
            # URL인지 키워드인지 판단
            is_url = query.startswith("http")
            
            if is_url:
                # URL에서 기사 ID 추출 시도
                url_parts = query.split("/")
                article_id = url_parts[-1] if len(url_parts) > 0 else ""
                
                # 뉴스 조회 API 사용 (URL -> 기사 ID로 조회)
                # 현재 BigKinds API에서 직접 URL로 조회하는 기능이 제공되지 않아 검색으로 대체
                self.logger.info(f"URL을 통한 뉴스 조회: {query}, ID: {article_id}")
                
                # 임시 구현: URL에서 검색어 추출 (더 정교한 구현 필요)
                search_query = article_id
            else:
                # 키워드 검색
                search_query = query
            
            # 날짜 범위 (최근 30일)
            end_date = datetime.utcnow().date()
            start_date = end_date - timedelta(days=30)
            
            # BigKinds API 호출
            result = self.bigkinds.news_search(
                query=search_query,
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d"),
                size=5
            )
             
            # 빅카인즈 API는 result=0이 성공
            if result.get("result") == 0:
                docs = result.get("return_object", {}).get("documents", [])
            else:
                docs = []
            
            # 요약: 첫 번째 기사 제목 + 본문 일부
            if docs:
                first_doc = docs[0]
                title = first_doc.get("title") or first_doc.get("TITLE", "")
                content = first_doc.get("content") or first_doc.get("CONTENT", "")
                
                # 간단한 요약 생성 (실제로는 LLM 등으로 더 정교하게 요약 가능)
                summary = f"{title}\n\n{content[:300]}..." if content else title
                
                # 핵심 포인트 추출 (현재는 임시 구현)
                key_points = [
                    f"{title}",
                    f"{len(docs)}개의 관련 기사가 검색되었습니다."
                ]
                
                return {
                    "query": query,
                    "summary": summary,
                    "key_points": key_points,
                    "article_count": len(docs),
                    "generated_at": datetime.now().isoformat(),
                    "status": "ok"
                }
            else:
                # 검색 결과 없음
                return {
                    "query": query,
                    "summary": f"'{query}'에 대한 검색 결과가 없습니다.",
                    "key_points": [],
                    "article_count": 0,
                    "generated_at": datetime.now().isoformat(),
                    "status": "no_results"
                }
        except Exception as e:
            self.logger.error(f"요약 생성 오류: {e}", exc_info=True)
            raise
    
    async def generate_timeline(self, query: str, search_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """주제에 대한 타임라인 생성
        
        Args:
            query: 검색어/주제
            search_params: 검색 파라미터
            
        Returns:
            타임라인 결과
            {
                "query": 검색어,
                "timeline_events": [이벤트 목록],
                "period": { 기간 },
                "event_count": 이벤트 수,
                "generated_at": 생성 시간,
                "status": 상태 코드
            }
        """
        self.logger.info(f"타임라인 생성 시작: '{query}'")
        
        try:
            # BigKinds 클라이언트 사용 가능 여부 확인
            if self.bigkinds is None:
                # 개발 모드 응답
                timeline_events = [
                    {
                        "date": "2024-01-01",
                        "title": f"{query} 관련 초기 사건",
                        "description": "주요 사건의 시작점",
                        "importance": "high"
                    },
                    {
                        "date": "2024-06-01", 
                        "title": f"{query} 중간 발전 사항",
                        "description": "상황의 변화와 발전",
                        "importance": "medium"
                    },
                    {
                        "date": "2024-12-01",
                        "title": f"{query} 최근 동향",
                        "description": "가장 최근의 상황",
                        "importance": "high"
                    }
                ]
                
                # 프론트엔드 형식에 맞춰 변환
                timeline_items = []
                for event in timeline_events:
                    timeline_items.append({
                        "date": event["date"],
                        "title": event["title"],
                        "summary": event["description"]
                    })
                
                return {
                    "timeline": timeline_items,
                    "query": query,
                    "timeline_events": timeline_events,
                    "period": {
                        "start": "2024-01-01",
                        "end": "2024-12-31"
                    },
                    "event_count": 3,
                    "generated_at": datetime.now().isoformat(),
                    "status": "development_mode",
                    "message": "BIGKINDS_KEY가 설정되지 않았습니다. 환경 변수를 설정하고 서버를 재시작하세요."
                }
            
            # 날짜 범위 설정 (최근 6개월)
            end_date = datetime.utcnow().date()
            start_date = end_date - timedelta(days=180)  # 6개월
            
            # 시간 간격 설정 (월별)
            interval = "month"
            
            # BigKinds API 호출
            result = self.bigkinds.time_line(
                query=query,
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d"),
                interval=interval
            )
            
            # 결과 파싱
            timeline_data = result.get("return_object", {}).get("time_line", [])
            total_hits = result.get("return_object", {}).get("total_hits", 0)
            
            # 타임라인 이벤트 생성
            timeline_events = []
            for item in timeline_data:
                # 레이블 포맷 변환 (YYYYMM -> YYYY-MM)
                label = item.get("label", "")
                if len(label) == 6:  # YYYYMM 형식
                    formatted_date = f"{label[:4]}-{label[4:6]}"
                else:
                    formatted_date = label
                    
                # 이벤트 생성
                timeline_events.append({
                    "date": formatted_date,
                    "title": f"{formatted_date}의 {query} 관련 뉴스",
                    "description": f"{item.get('hits', 0)}건의 뉴스 기사",
                    "count": item.get("hits", 0),
                    "importance": "high" if item.get("hits", 0) > 10 else "medium"
                })
            
            # 프론트엔드 형식에 맞춰 변환
            timeline_items = []
            for event in timeline_events:
                timeline_items.append({
                    "date": event["date"],
                    "title": event["title"],
                    "summary": event["description"]
                })
            
            return {
                "timeline": timeline_items,
                "query": query,
                "timeline_events": timeline_events,
                "period": {
                    "start": start_date.strftime("%Y-%m-%d"),
                    "end": end_date.strftime("%Y-%m-%d")
                },
                "event_count": len(timeline_events),
                "total_hits": total_hits,
                "generated_at": datetime.now().isoformat(),
                "status": "ok" if timeline_events else "no_results"
            }
            
        except Exception as e:
            self.logger.error(f"타임라인 생성 오류: {e}", exc_info=True)
            raise
    
    async def _generate_response(
        self, query: str, search_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """실제 BigKinds 데이터를 사용한 간단한 응답 생성"""

        # BigKinds가 없으면 모드 유지
        if self.bigkinds is None:
            return await self._generate_mock_response(query, search_params)

        # 날짜 범위 파싱 – 기본 최근 30일
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=30)

        try:
            result = self.bigkinds.news_search(
                query=query,
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d"),
                size=5,
            )

            # 빅카인즈 API는 result=0이 성공
            if result.get("result") == 0:
                docs = result.get("return_object", {}).get("documents", [])
            else:
                docs = []

            # 간단 요약: 제목 리스트 연결
            titles = [doc.get("title") or doc.get("TITLE") for doc in docs]
            answer = "\n".join(f"- {t}" for t in titles if t)

            sources = [
                {
                    "title": (doc.get("title") or doc.get("TITLE")),
                    "url": doc.get("url") or doc.get("provider_link_page"),
                    "content": doc.get("content") or doc.get("CONTENT"),
                }
                for doc in docs[:3]
            ]

            return {
                "query": query,
                "answer": answer if answer else "검색 결과가 없습니다.",
                "sources": sources,
                "generated_at": datetime.now().isoformat(),
                "status": "ok",
            }
        except Exception as e:
            self.logger.error("BigKinds 검색 오류: %s", e, exc_info=True)
            return await self._generate_mock_response(query, search_params)
    
    async def _generate_mock_response(self, query: str, search_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """임시 응답 생성 (개발용)"""
        return {
            "query": query,
            "answer": f"'{query}'에 대한 질의에 답변드립니다. 현재는 개발 중인 기능으로 임시 응답을 제공합니다. 실제 뉴스 기사 분석을 통한 응답은 곧 제공될 예정입니다.",
            "sources": [],
            "confidence": 0.5,
            "generated_at": datetime.now().isoformat(),
            "processing_time": 0.1,
            "status": "development_mode"
        }
    
    async def _stream_mock_response(self, query: str):
        """임시 스트리밍 응답 생성 (개발용)"""
        chunks = [
            f"'{query}'에 대한 질의를 ",
            "분석하고 있습니다. ",
            "관련 뉴스 기사를 ",
            "검색하여 ",
            "종합적인 답변을 ",
            "준비하고 있습니다. ",
            "현재는 개발 중인 기능으로 ",
            "임시 응답을 제공합니다."
        ]
        
        for chunk in chunks:
            await asyncio.sleep(0.1)  # 스트리밍 시뮬레이션
            yield chunk 