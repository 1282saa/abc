"""
문서 처리 모듈

빅카인즈 API에서 가져온 뉴스 데이터를 처리하고 벡터 데이터베이스에 저장하기 위한 형태로 가공하는 기능을 제공합니다.
"""

import re
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# 프로젝트 루트 디렉토리 찾기
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.logger import setup_logger

class DocumentProcessor:
    """뉴스 문서 처리 클래스"""
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        """문서 처리기 초기화
        
        Args:
            chunk_size: 청크 크기 (글자 수)
            chunk_overlap: 청크 간 중복 글자 수
        """
        self.logger = setup_logger("qa.document_processor")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        self.logger.info(f"문서 처리기 초기화 (청크 크기: {chunk_size}, 중복: {chunk_overlap})")
    
    def process_news_data(self, news_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """뉴스 데이터 처리
        
        Args:
            news_data: 빅카인즈 API로부터 가져온 뉴스 데이터 리스트
            
        Returns:
            처리된 문서 리스트
        """
        self.logger.info(f"{len(news_data)}개 뉴스 데이터 처리 시작")
        
        processed_documents = []
        
        for news in news_data:
            # 기본 필드 확인 및 정제
            news_id = news.get("news_id")
            if not news_id:
                self.logger.warning("news_id가 없는 뉴스 항목 건너뜀")
                continue
                
            title = news.get("title", "").strip()
            content = news.get("content", "").strip()
            
            # 제목이나 내용이 너무 짧으면 건너뜀
            if not title or len(content) < 50:
                self.logger.warning(f"제목 또는 내용이 불충분한 뉴스 건너뜀 (ID: {news_id})")
                continue
            
            # 메타데이터 정리
            date_str = news.get("date", "")
            try:
                date = datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y-%m-%d") if date_str else ""
            except ValueError:
                self.logger.warning(f"날짜 형식 오류: {date_str} (ID: {news_id})")
                date = date_str
            
            provider = news.get("provider", "")
            url = news.get("url", "")
            category = news.get("category", "")
            
            # 내용 정제
            content = self._clean_content(content)
            
            # 청크로 분할
            chunks = self._split_into_chunks(title, content)
            
            # 각 청크를 문서로 변환
            for i, chunk in enumerate(chunks):
                document = {
                    "id": f"{news_id}-{i}",
                    "news_id": news_id,
                    "title": title,
                    "content": chunk,
                    "provider": provider,
                    "date": date,
                    "url": url,
                    "category": category,
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                }
                
                processed_documents.append(document)
        
        self.logger.info(f"{len(processed_documents)}개 처리된 문서 생성 완료")
        
        # 중복 문서 필터링
        filtered_documents = self._filter_duplicates(processed_documents)
        
        self.logger.info(f"중복 제거 후 {len(filtered_documents)}개 문서 남음")
        return filtered_documents
    
    def _clean_content(self, content: str) -> str:
        """내용 정제
        
        Args:
            content: 원본 내용 텍스트
            
        Returns:
            정제된 내용 텍스트
        """
        # 불필요한 공백 및 특수 문자 제거
        content = re.sub(r'\s+', ' ', content)  # 연속된 공백을 하나로
        content = re.sub(r'[^\w\s\.\,\?\!\:\;\-\(\)\[\]\{\}\'\"\·\%]', '', content)  # 일부 특수문자만 허용
        
        # HTML 태그 제거
        content = re.sub(r'<.*?>', '', content)
        
        # 불필요한 출처 표기 제거
        content = re.sub(r'\([^)]*기자[^)]*\)', '', content)
        content = re.sub(r'\([^)]*특파원[^)]*\)', '', content)
        content = re.sub(r'\([^)]*뉴스[^)]*\)', '', content)
        
        return content.strip()
    
    def _split_into_chunks(self, title: str, content: str) -> List[str]:
        """내용을 청크로 분할
        
        Args:
            title: 뉴스 제목
            content: 뉴스 내용
            
        Returns:
            청크 리스트
        """
        # 내용 없으면 제목만 반환
        if not content:
            return [title]
        
        # 너무 짧은 경우 분할 없이 반환
        if len(content) <= self.chunk_size:
            return [f"{title} {content}"]
        
        chunks = []
        
        # 문장 단위로 분할
        sentences = re.split(r'(?<=[.!?])\s+', content)
        
        current_chunk = title + " "
        current_size = len(current_chunk)
        
        for sentence in sentences:
            sentence_len = len(sentence)
            
            # 문장이 너무 길면 더 작게 분할
            if sentence_len > self.chunk_size:
                # 현재 청크에 있는 내용 저장
                if current_size > len(title) + 1:  # 제목만 있는 경우 제외
                    chunks.append(current_chunk.strip())
                
                # 긴 문장 처리
                words = sentence.split()
                current_chunk = title + " "
                current_size = len(current_chunk)
                
                for word in words:
                    if current_size + len(word) + 1 <= self.chunk_size:
                        current_chunk += word + " "
                        current_size += len(word) + 1
                    else:
                        chunks.append(current_chunk.strip())
                        current_chunk = title + " " + word + " "  # 새 청크에 제목 포함
                        current_size = len(current_chunk)
            
            # 일반 문장 처리
            elif current_size + sentence_len + 1 <= self.chunk_size:
                # 청크에 문장 추가
                current_chunk += sentence + " "
                current_size += sentence_len + 1
            else:
                # 현재 청크가 가득 차면 저장하고 새로 시작
                chunks.append(current_chunk.strip())
                
                # 새 청크에는 제목을 포함시켜 맥락 유지
                current_chunk = title + " " + sentence + " "
                current_size = len(current_chunk)
        
        # 마지막 청크 저장
        if current_size > len(title) + 1:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _filter_duplicates(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """중복 문서 필터링
        
        Args:
            documents: 원본 문서 리스트
            
        Returns:
            중복 제거된 문서 리스트
        """
        # 해시값 기반 중복 확인
        seen_hashes = set()
        unique_documents = []
        
        for doc in documents:
            # 내용 기반 해시 생성
            content_hash = hashlib.md5(doc["content"].encode()).hexdigest()
            
            # 중복 확인
            if content_hash not in seen_hashes:
                seen_hashes.add(content_hash)
                unique_documents.append(doc)
        
        return unique_documents
    
    def preprocess_query(self, query: str) -> str:
        """사용자 쿼리 전처리
        
        Args:
            query: 원본 사용자 쿼리
            
        Returns:
            전처리된 쿼리
        """
        # 쿼리 정제
        query = query.strip()
        
        # 특수 문자 처리
        query = re.sub(r'[^\w\s\.\,\?\!\:\;\-\(\)\[\]\{\}\'\"\·]', ' ', query)
        
        # 공백 정리
        query = re.sub(r'\s+', ' ', query)
        
        return query 