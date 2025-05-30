"""
벡터 데이터베이스 관리 모듈

ChromaDB를 사용하여 뉴스 기사의 벡터 임베딩을 저장하고 검색하는 기능을 제공합니다.
"""

import os
import logging
from typing import Dict, List, Any, Optional, Union
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import uuid
import json
from pathlib import Path

# 프로젝트 루트 디렉토리 찾기
import sys
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.logger import setup_logger

class VectorDB:
    """뉴스 임베딩 벡터 저장 및 검색 클래스"""
    
    def __init__(self, persist_directory: Optional[str] = None, collection_name: str = "news_articles"):
        """벡터 데이터베이스 초기화
        
        Args:
            persist_directory: 데이터베이스 저장 디렉토리 (없으면 메모리 DB)
            collection_name: 컬렉션 이름
        """
        self.logger = setup_logger("qa.vectordb")
        
        # 저장 디렉토리 설정
        if persist_directory:
            self.persist_directory = persist_directory
        else:
            # 기본 저장 경로 설정
            self.persist_directory = os.path.join(PROJECT_ROOT, "cache", "vectordb")
            os.makedirs(self.persist_directory, exist_ok=True)
        
        self.collection_name = collection_name
        
        self.logger.info(f"벡터 DB 초기화: {self.persist_directory}, 컬렉션: {self.collection_name}")
        
        # ChromaDB 클라이언트 설정
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # 임베딩 함수 설정 (기본 OpenAI)
        self.embedding_function = embedding_functions.OpenAIEmbeddingFunction(
            api_key=os.environ.get("OPENAI_API_KEY"),
            model_name="text-embedding-ada-002"
        )
        
        # 컬렉션 가져오기 또는 생성
        try:
            self.collection = self.client.get_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function
            )
            self.logger.info(f"기존 컬렉션 로드: {self.collection_name}")
        except ValueError:
            # 컬렉션이 없는 경우 새로 생성
            self.collection = self.client.create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function
            )
            self.logger.info(f"새 컬렉션 생성: {self.collection_name}")
    
    def add_documents(self, documents: List[Dict[str, Any]], batch_size: int = 100) -> None:
        """문서 추가
        
        Args:
            documents: 추가할 문서 리스트
            batch_size: 배치 크기
        """
        self.logger.info(f"{len(documents)}개 문서 추가 시작")
        
        # 배치 처리
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i+batch_size]
            
            ids = []
            texts = []
            metadatas = []
            
            for doc in batch:
                # ID 생성 또는 기존 ID 사용
                doc_id = doc.get("id", str(uuid.uuid4()))
                
                # 임베딩을 위한 텍스트 준비 (제목 + 본문)
                text = f"{doc.get('title', '')} {doc.get('content', '')}"
                
                # 메타데이터 추출 (필요한 필드만)
                metadata = {
                    "news_id": doc.get("news_id", ""),
                    "title": doc.get("title", ""),
                    "provider": doc.get("provider", ""),
                    "date": doc.get("date", ""),
                    "url": doc.get("url", "")
                }
                
                ids.append(doc_id)
                texts.append(text)
                metadatas.append(metadata)
            
            # 배치 삽입
            self.collection.add(
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            
            self.logger.info(f"배치 {i//batch_size + 1} 추가 완료 ({len(batch)}개)")
    
    def query(self, text: str, n_results: int = 5, filter_metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """텍스트 쿼리로 관련 문서 검색
        
        Args:
            text: 쿼리 텍스트
            n_results: 반환할 결과 수
            filter_metadata: 필터링할 메타데이터
            
        Returns:
            검색 결과 문서 리스트
        """
        self.logger.info(f"쿼리 실행: '{text}', 결과 수: {n_results}")
        
        try:
            # 검색 실행
            results = self.collection.query(
                query_texts=[text],
                n_results=n_results,
                where=filter_metadata
            )
            
            # 결과 처리
            documents = results.get("documents", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]
            distances = results.get("distances", [[]])[0]
            
            # 결과 조합
            search_results = []
            for i, (doc, metadata, distance) in enumerate(zip(documents, metadatas, distances)):
                # 유사도 점수 계산 (거리를 0~1 사이 유사도로 변환)
                similarity = 1.0 - (distance / 2.0)  # 거리 0 -> 유사도 1, 거리 2 -> 유사도 0
                
                search_results.append({
                    "text": doc,
                    "metadata": metadata,
                    "similarity": similarity,
                    "rank": i + 1
                })
            
            return search_results
        
        except Exception as e:
            self.logger.error(f"쿼리 오류: {e}")
            return []
    
    def delete_document(self, document_id: str) -> None:
        """문서 삭제
        
        Args:
            document_id: 삭제할 문서 ID
        """
        try:
            self.collection.delete(ids=[document_id])
            self.logger.info(f"문서 삭제 완료: {document_id}")
        except Exception as e:
            self.logger.error(f"문서 삭제 오류: {e}")
    
    def delete_collection(self) -> None:
        """컬렉션 전체 삭제"""
        try:
            self.client.delete_collection(self.collection_name)
            self.logger.info(f"컬렉션 삭제 완료: {self.collection_name}")
            
            # 컬렉션 재생성
            self.collection = self.client.create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function
            )
        except Exception as e:
            self.logger.error(f"컬렉션 삭제 오류: {e}")
    
    def get_document_count(self) -> int:
        """문서 개수 반환
        
        Returns:
            컬렉션 내 문서 개수
        """
        try:
            count = self.collection.count()
            return count
        except Exception as e:
            self.logger.error(f"문서 개수 조회 오류: {e}")
            return 0
    
    def set_embedding_function(self, model_name: str = "text-embedding-ada-002") -> None:
        """임베딩 함수 설정
        
        Args:
            model_name: 사용할 임베딩 모델 이름
        """
        # 현재는 OpenAI 임베딩만 지원
        self.embedding_function = embedding_functions.OpenAIEmbeddingFunction(
            api_key=os.environ.get("OPENAI_API_KEY"),
            model_name=model_name
        )
        
        # 컬렉션 임베딩 함수 갱신
        self.collection = self.client.get_collection(
            name=self.collection_name,
            embedding_function=self.embedding_function
        )
        
        self.logger.info(f"임베딩 함수 갱신: {model_name}") 