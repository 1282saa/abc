"""
LLM 처리 모듈

대형 언어 모델(LLM)과 상호작용하여 응답을 생성하는 기능을 제공합니다.
OpenAI API 및 기타 LLM을 지원합니다.
"""

import os
import logging
import json
import asyncio
from typing import Dict, List, Any, Optional, Union, Tuple
import openai
import time

# 프로젝트 루트 디렉토리 찾기
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.logger import setup_logger

# 비동기 지원 
from openai import AsyncOpenAI

class LLMHandler:
    """대형 언어 모델(LLM) 처리 클래스"""
    
    def __init__(self, model_name: str = "gpt-3.5-turbo", api_key: Optional[str] = None):
        """LLM 핸들러 초기화
        
        Args:
            model_name: 사용할 모델 이름
            api_key: API 키 (None이면 환경 변수에서 가져옴)
        """
        self.logger = setup_logger("qa.llm_handler")
        self.model_name = model_name
        
        # API 키 설정
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            self.logger.warning("OPENAI_API_KEY가 설정되지 않았습니다.")
        
        # 모델 제공자 감지 (현재는 OpenAI만 지원)
        self.provider = "openai"
        if "llama" in model_name.lower() or "claude" in model_name.lower():
            self.logger.warning(f"현재 '{model_name}' 모델은 정식 지원되지 않습니다.")
        
        self.logger.info(f"LLM 핸들러 초기화 (모델: {model_name}, 제공자: {self.provider})")
        
        # 비동기 클라이언트 초기화
        self.async_client = AsyncOpenAI(api_key=self.api_key)
    
    async def generate_response(self, 
                        prompts: Dict[str, str], 
                        temperature: float = 0.3,
                        max_tokens: Optional[int] = None,
                        stream: bool = False) -> Union[str, AsyncGenerator[str, None]]:
        """LLM으로부터 응답 생성
        
        Args:
            prompts: 시스템 및 사용자 프롬프트가 담긴 딕셔너리
            temperature: 온도 값 (높을수록 다양한 응답)
            max_tokens: 최대 토큰 수 (None이면 모델 기본값)
            stream: 스트리밍 응답 여부
            
        Returns:
            LLM 응답 텍스트 또는 스트리밍 응답 제너레이터
        """
        # 기본 최대 토큰 설정
        if max_tokens is None:
            # 모델별 적절한 최대 토큰 수 설정
            model_max_tokens = {
                "gpt-3.5-turbo": 2048,
                "gpt-3.5-turbo-16k": 4096,
                "gpt-4": 4096,
                "gpt-4-turbo": 4096,
                "gpt-4-1106-preview": 4096,
                "gpt-4-32k": 8192
            }
            max_tokens = model_max_tokens.get(self.model_name, 2048)
        
        system_prompt = prompts.get("system", "당신은 뉴스 데이터 기반 질의응답 AI 비서입니다.")
        user_prompt = prompts.get("user", "")
        
        self.logger.info(f"응답 생성 시작 (모델: {self.model_name}, 온도: {temperature})")
        
        try:
            if stream:
                return self._generate_streaming_response(system_prompt, user_prompt, temperature, max_tokens)
            else:
                return await self._generate_complete_response(system_prompt, user_prompt, temperature, max_tokens)
        except Exception as e:
            self.logger.error(f"LLM 응답 생성 오류: {e}")
            return f"오류: LLM 응답을 생성하는 중 문제가 발생했습니다. ({str(e)})"
    
    async def _generate_complete_response(self, 
                                   system_prompt: str, 
                                   user_prompt: str,
                                   temperature: float,
                                   max_tokens: int) -> str:
        """전체 응답 생성 (한 번에 반환)
        
        Args:
            system_prompt: 시스템 프롬프트
            user_prompt: 사용자 프롬프트
            temperature: 온도 값
            max_tokens: 최대 토큰 수
            
        Returns:
            생성된 응답 텍스트
        """
        try:
            # 메시지 구성
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            # API 호출 시작 시간
            start_time = time.time()
            
            # 응답 생성
            response = await self.async_client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=0.95,
                frequency_penalty=0,
                presence_penalty=0
            )
            
            # 응답 처리 시간
            elapsed_time = time.time() - start_time
            
            # 응답 추출
            content = response.choices[0].message.content
            
            # 토큰 사용량
            total_tokens = response.usage.total_tokens
            prompt_tokens = response.usage.prompt_tokens
            completion_tokens = response.usage.completion_tokens
            
            self.logger.info(
                f"응답 생성 완료 (시간: {elapsed_time:.2f}초, "
                f"토큰: {total_tokens}개 [프롬프트: {prompt_tokens}, 응답: {completion_tokens}])"
            )
            
            return content
            
        except Exception as e:
            self.logger.error(f"응답 생성 오류: {e}")
            raise
    
    async def _generate_streaming_response(self, 
                                    system_prompt: str, 
                                    user_prompt: str,
                                    temperature: float,
                                    max_tokens: int) -> AsyncGenerator[str, None]:
        """스트리밍 응답 생성
        
        Args:
            system_prompt: 시스템 프롬프트
            user_prompt: 사용자 프롬프트
            temperature: 온도 값
            max_tokens: 최대 토큰 수
            
        Yields:
            생성된 응답 청크
        """
        # 메시지 구성
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            # API 호출 시작 시간
            start_time = time.time()
            
            # 스트리밍 응답 생성
            stream = await self.async_client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=0.95,
                stream=True
            )
            
            # 청크별로 응답 생성
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
            
            # 응답 처리 시간
            elapsed_time = time.time() - start_time
            self.logger.info(f"스트리밍 응답 생성 완료 (시간: {elapsed_time:.2f}초)")
            
        except Exception as e:
            self.logger.error(f"스트리밍 응답 생성 오류: {e}")
            yield f"오류: 스트리밍 응답 생성 중 문제가 발생했습니다. ({str(e)})"
    
    async def batch_generate(self, 
                      prompt_list: List[Dict[str, str]], 
                      temperature: float = 0.3,
                      max_tokens: Optional[int] = None) -> List[str]:
        """여러 프롬프트에 대한 응답 일괄 생성
        
        Args:
            prompt_list: 프롬프트 딕셔너리 리스트
            temperature: 온도 값
            max_tokens: 최대 토큰 수
            
        Returns:
            응답 리스트
        """
        tasks = []
        
        # 각 프롬프트에 대한 응답 생성 태스크 생성
        for prompts in prompt_list:
            task = asyncio.create_task(
                self.generate_response(prompts, temperature, max_tokens)
            )
            tasks.append(task)
        
        # 모든 태스크 완료 대기
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 예외 처리
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                self.logger.error(f"배치 항목 {i} 생성 오류: {response}")
                responses[i] = f"오류: 응답을 생성하는 중 문제가 발생했습니다. ({str(response)})"
        
        return responses
    
    def change_model(self, model_name: str) -> None:
        """사용 모델 변경
        
        Args:
            model_name: 새로운 모델 이름
        """
        self.model_name = model_name
        self.logger.info(f"모델 변경: {model_name}")
        
        # 모델 제공자 업데이트
        if "gpt" in model_name.lower() or model_name.startswith("text-"):
            self.provider = "openai"
        elif "llama" in model_name.lower():
            self.provider = "llama"
        elif "claude" in model_name.lower():
            self.provider = "anthropic"
        else:
            self.provider = "unknown" 