"""
임베딩 처리 모듈

텍스트를 벡터로 변환하는 임베딩 기능을 제공합니다.
OpenAI 임베딩 API 및 HuggingFace 모델을 지원합니다.
"""

import os
import logging
import numpy as np
from typing import Dict, List, Any, Optional, Union
import asyncio
import time
import openai

# 프로젝트 루트 디렉토리 찾기
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.logger import setup_logger

# 선택적 HuggingFace 라이브러리 가져오기
try:
    import torch
    from transformers import AutoTokenizer, AutoModel
    HUGGINGFACE_AVAILABLE = True
except ImportError:
    HUGGINGFACE_AVAILABLE = False

class EmbeddingService:
    """텍스트 임베딩 서비스 클래스"""
    
    def __init__(self, model_name: str = "text-embedding-ada-002", use_openai: bool = True):
        """임베딩 서비스 초기화
        
        Args:
            model_name: 사용할 임베딩 모델 이름
            use_openai: OpenAI API 사용 여부, False면 HuggingFace 모델 사용
        """
        self.logger = setup_logger("qa.embeddings")
        self.model_name = model_name
        self.use_openai = use_openai
        
        # OpenAI 설정
        self.openai_api_key = os.environ.get("OPENAI_API_KEY")
        
        # HuggingFace 모델 설정
        self.hf_model = None
        self.hf_tokenizer = None
        
        self.logger.info(f"임베딩 서비스 초기화: {'OpenAI' if use_openai else 'HuggingFace'} ({model_name})")
        
        # 모델 초기화
        if not use_openai:
            self._init_huggingface_model()
    
    def _init_huggingface_model(self):
        """HuggingFace 모델 초기화"""
        if not HUGGINGFACE_AVAILABLE:
            self.logger.error("HuggingFace 라이브러리가 설치되지 않았습니다. 'pip install transformers torch'로 설치하세요.")
            raise ImportError("HuggingFace 라이브러리가 필요합니다.")
        
        try:
            self.logger.info(f"HuggingFace 모델 로드: {self.model_name}")
            self.hf_tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.hf_model = AutoModel.from_pretrained(self.model_name)
            
            # GPU 사용 가능하면 모델 이동
            if torch.cuda.is_available():
                self.hf_model = self.hf_model.to("cuda")
                self.logger.info("GPU로 모델 이동 완료")
            else:
                self.logger.info("GPU를 찾을 수 없어 CPU에서 실행합니다.")
        except Exception as e:
            self.logger.error(f"HuggingFace 모델 로드 오류: {e}")
            raise
    
    async def get_embeddings(self, texts: List[str], batch_size: int = 8) -> List[List[float]]:
        """텍스트 리스트의 임베딩 벡터 반환
        
        Args:
            texts: 임베딩할 텍스트 리스트
            batch_size: 배치 크기
            
        Returns:
            임베딩 벡터 리스트
        """
        self.logger.info(f"{len(texts)}개 텍스트 임베딩 시작")
        
        if not texts:
            return []
        
        # OpenAI 또는 HuggingFace 모델 사용
        if self.use_openai:
            return await self._get_openai_embeddings(texts, batch_size)
        else:
            return self._get_huggingface_embeddings(texts, batch_size)
    
    async def _get_openai_embeddings(self, texts: List[str], batch_size: int) -> List[List[float]]:
        """OpenAI API를 사용하여 임베딩 생성
        
        Args:
            texts: 임베딩할 텍스트 리스트
            batch_size: 배치 크기
            
        Returns:
            임베딩 벡터 리스트
        """
        if not self.openai_api_key:
            self.logger.error("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
            raise ValueError("OpenAI API 키가 필요합니다.")
            
        all_embeddings = []
        
        # 배치 처리
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            
            try:
                # OpenAI API 호출
                response = await openai.Embedding.acreate(
                    input=batch,
                    model=self.model_name,
                    api_key=self.openai_api_key
                )
                
                # 임베딩 추출
                batch_embeddings = [item["embedding"] for item in response["data"]]
                all_embeddings.extend(batch_embeddings)
                
                self.logger.debug(f"배치 {i//batch_size + 1}/{(len(texts) + batch_size - 1)//batch_size} 임베딩 완료")
                
                # API 호출 간격 조절
                if i + batch_size < len(texts):
                    await asyncio.sleep(0.5)
                    
            except Exception as e:
                self.logger.error(f"OpenAI 임베딩 오류 (배치 {i//batch_size + 1}): {e}")
                # 오류 발생 시 빈 임베딩으로 채움
                batch_embeddings = [[0.0] * 1536] * len(batch)  # OpenAI 임베딩 크기는 1536
                all_embeddings.extend(batch_embeddings)
                
                # 재시도 전 잠시 대기
                await asyncio.sleep(1.0)
        
        return all_embeddings
    
    def _get_huggingface_embeddings(self, texts: List[str], batch_size: int) -> List[List[float]]:
        """HuggingFace 모델을 사용하여 임베딩 생성
        
        Args:
            texts: 임베딩할 텍스트 리스트
            batch_size: 배치 크기
            
        Returns:
            임베딩 벡터 리스트
        """
        if self.hf_model is None or self.hf_tokenizer is None:
            self._init_huggingface_model()
        
        all_embeddings = []
        
        # 모델 평가 모드 설정
        self.hf_model.eval()
        
        # 배치 처리
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            
            try:
                with torch.no_grad():
                    # 토큰화 및 임베딩 생성
                    inputs = self.hf_tokenizer(
                        batch,
                        padding=True,
                        truncation=True,
                        max_length=512,
                        return_tensors="pt"
                    )
                    
                    # GPU로 이동 (가능한 경우)
                    if torch.cuda.is_available():
                        inputs = {k: v.to("cuda") for k, v in inputs.items()}
                    
                    # 임베딩 계산
                    outputs = self.hf_model(**inputs)
                    
                    # 평균 풀링으로 문장 임베딩 (토큰 임베딩의 평균)
                    attention_mask = inputs["attention_mask"]
                    embeddings = self._mean_pooling(outputs.last_hidden_state, attention_mask)
                    
                    # 정규화
                    batch_embeddings = [
                        embedding.cpu().numpy().tolist() 
                        for embedding in torch.nn.functional.normalize(embeddings, p=2, dim=1)
                    ]
                    
                    all_embeddings.extend(batch_embeddings)
                
                self.logger.debug(f"배치 {i//batch_size + 1}/{(len(texts) + batch_size - 1)//batch_size} 임베딩 완료")
                    
            except Exception as e:
                self.logger.error(f"HuggingFace 임베딩 오류 (배치 {i//batch_size + 1}): {e}")
                
                # 모델 차원 확인
                embedding_size = 768  # 대부분의 HF 모델의 기본값
                try:
                    config = self.hf_model.config
                    embedding_size = config.hidden_size
                except:
                    pass
                
                # 오류 발생 시 빈 임베딩으로 채움
                batch_embeddings = [[0.0] * embedding_size] * len(batch)
                all_embeddings.extend(batch_embeddings)
        
        return all_embeddings
    
    def _mean_pooling(self, token_embeddings, attention_mask):
        """토큰 임베딩의 평균 계산 (BERT/RoBERTa 등의 모델용)
        
        Args:
            token_embeddings: 토큰별 임베딩 ([batch_size, seq_len, hidden_size])
            attention_mask: 어텐션 마스크 ([batch_size, seq_len])
            
        Returns:
            문장 임베딩 ([batch_size, hidden_size])
        """
        # 마스크 확장
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        
        # 마스킹된 임베딩 합계 / 마스크 합계
        sum_embeddings = torch.sum(token_embeddings * input_mask_expanded, 1)
        sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
        
        return sum_embeddings / sum_mask
    
    def get_embedding_dimension(self) -> int:
        """현재 임베딩 모델의 벡터 차원 반환
        
        Returns:
            임베딩 벡터 차원
        """
        if self.use_openai:
            # OpenAI 모델별 차원 정보
            dimensions = {
                "text-embedding-ada-002": 1536,
                "text-embedding-3-small": 1536,
                "text-embedding-3-large": 3072
            }
            return dimensions.get(self.model_name, 1536)  # 기본값 1536
        else:
            # HuggingFace 모델 차원
            if self.hf_model is None:
                self._init_huggingface_model()
                
            try:
                config = self.hf_model.config
                return config.hidden_size
            except:
                return 768  # 대부분의 BERT 계열 모델의 기본 차원 