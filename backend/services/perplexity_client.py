"""
Perplexity AI API 클라이언트
실시간 AI 설명 서비스 제공
"""

import os
import sys
import asyncio
import aiohttp
from typing import Dict, Any, Optional
from pathlib import Path

# 프로젝트 루트 디렉토리 찾기
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.utils.logger import setup_logger

logger = setup_logger("services.perplexity")

class PerplexityClient:
    """Perplexity AI API 클라이언트"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Perplexity AI 클라이언트 초기화
        
        Args:
            api_key: Perplexity API 키. 없으면 환경변수에서 로드
        """
        self.api_key = api_key or os.environ.get("PERPLEXITY_API_KEY")
        if not self.api_key:
            logger.warning("Perplexity API 키가 설정되지 않았습니다.")
            
        self.base_url = "https://api.perplexity.ai"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def explain_financial_term(self, term: str, context: str = "") -> Dict[str, Any]:
        """금융 용어나 개념을 간단하게 설명
        
        Args:
            term: 설명할 용어
            context: 추가 맥락 정보
            
        Returns:
            설명 결과 딕셔너리
        """
        try:
            prompt = f"""
            한국 주식 투자자를 위해 '{term}' 용어를 쉽고 실용적으로 설명해주세요.
            {f"상황: {context}" if context else ""}
            
            아래 형식으로 정확히 작성해주세요:
            
            📌 정의
            - {term}이 무엇인지 초보자도 이해할 수 있게 1-2문장으로 설명
            
            💡 투자 포인트  
            - 주식 투자할 때 이 용어가 왜 중요한지 실용적인 관점에서 1-2문장으로 설명
            - 투자 결정에 어떤 영향을 주는지 구체적인 예시 포함
            
            ⚠️ 주의사항
            - 투자자가 놓치기 쉬운 중요한 점이나 함정 1문장으로 설명
            
            한국어로만 답변하고, 전문용어는 괄호 안에 쉬운 설명을 추가해주세요.
            """
            
            response = await self._make_request(prompt)
            
            if response:
                return {
                    "term": term,
                    "explanation": response.get("choices", [{}])[0].get("message", {}).get("content", "설명을 가져올 수 없습니다."),
                    "success": True
                }
            else:
                return {
                    "term": term,
                    "explanation": "현재 설명을 가져올 수 없습니다. 나중에 다시 시도해주세요.",
                    "success": False
                }
                
        except Exception as e:
            logger.error(f"용어 설명 조회 실패: {e}")
            return {
                "term": term,
                "explanation": "설명을 가져오는 중 오류가 발생했습니다.",
                "success": False
            }
    
    async def explain_market_event(self, event_title: str, event_details: str = "") -> Dict[str, Any]:
        """시장 이벤트나 실적발표 등에 대한 설명
        
        Args:
            event_title: 이벤트 제목
            event_details: 이벤트 상세 정보
            
        Returns:
            이벤트 분석 결과 딕셔너리
        """
        try:
            prompt = f"""
            한국 주식 투자자를 위해 '{event_title}' 이벤트를 분석해주세요.
            {f"추가 정보: {event_details}" if event_details else ""}
            
            아래 형식으로 정확히 작성해주세요:
            
            🎯 이벤트 분석
            - 이 이벤트가 무엇이고 왜 중요한지 초보자도 이해할 수 있게 1-2문장으로 설명
            
            📈 주가 영향 예상
            - 이 이벤트가 주가에 어떤 영향을 줄 수 있는지 구체적으로 1-2문장으로 설명
            - 상승/하락 요인과 그 이유를 명확히 제시
            
            💼 투자 전략
            - 이 이벤트를 고려한 실용적인 투자 관점이나 주의사항 1-2문장으로 설명
            - 언제 매수/매도하거나 관망해야 하는지 구체적인 가이드 제공
            
            ⏰ 타이밍
            - 이벤트 전후로 언제 주목해야 하는지 시점 제시
            
            한국 시장 상황에 맞게 실용적으로 설명하고, 전문용어는 쉽게 풀어서 설명해주세요.
            """
            
            response = await self._make_request(prompt)
            
            if response:
                return {
                    "event": event_title,
                    "explanation": response.get("choices", [{}])[0].get("message", {}).get("content", "설명을 가져올 수 없습니다."),
                    "success": True
                }
            else:
                return {
                    "event": event_title,
                    "explanation": "현재 설명을 가져올 수 없습니다. 나중에 다시 시도해주세요.",
                    "success": False
                }
                
        except Exception as e:
            logger.error(f"이벤트 설명 조회 실패: {e}")
            return {
                "event": event_title,
                "explanation": "설명을 가져오는 중 오류가 발생했습니다.",
                "success": False
            }
    
    async def get_daily_market_summary(self) -> Dict[str, Any]:
        """오늘의 주식 및 가상화폐 시장 주요 이슈 요약
        
        Returns:
            시장 요약 결과 딕셔너리
        """
        try:
            from datetime import datetime
            today = datetime.now().strftime("%Y년 %m월 %d일")
            
            prompt = f"""
            {today} 한국 및 글로벌 금융시장의 주요 이슈를 요약해주세요.
            
            다음 항목들을 포함해서 간단하게 정리해주세요:
            1. 한국 주식시장 (KOSPI, KOSDAQ) 주요 움직임
            2. 미국 주식시장 주요 이슈
            3. 가상화폐 시장 동향
            4. 환율 및 경제 이슈
            
            각 항목당 1-2문장으로 핵심만 정리해주세요.
            """
            
            response = await self._make_request(prompt)
            
            if response:
                return {
                    "date": today,
                    "summary": response.get("choices", [{}])[0].get("message", {}).get("content", "시장 요약을 가져올 수 없습니다."),
                    "success": True
                }
            else:
                return {
                    "date": today,
                    "summary": "현재 시장 요약을 가져올 수 없습니다. 나중에 다시 시도해주세요.",
                    "success": False
                }
                
        except Exception as e:
            logger.error(f"시장 요약 조회 실패: {e}")
            return {
                "date": "오늘",
                "summary": "시장 요약을 가져오는 중 오류가 발생했습니다.",
                "success": False
            }
    
    async def get_stock_analysis(self, stock_name: str, stock_code: str, current_price: str = "") -> Dict[str, Any]:
        """특정 종목에 대한 간단한 분석
        
        Args:
            stock_name: 종목명
            stock_code: 종목코드
            current_price: 현재가 (선택사항)
            
        Returns:
            종목 분석 결과 딕셔너리
        """
        try:
            price_info = f" 현재가 {current_price}원" if current_price else ""
            prompt = f"""
            {stock_name}({stock_code}){price_info}에 대해 간단한 투자 관점을 제공해주세요.
            
            다음을 포함하여 2-3문장으로 설명해주세요:
            - 회사의 주요 사업과 특징
            - 최근 주가 동향이나 이슈
            - 투자시 고려사항
            """
            
            response = await self._make_request(prompt)
            
            if response:
                return {
                    "stock_name": stock_name,
                    "stock_code": stock_code,
                    "analysis": response.get("choices", [{}])[0].get("message", {}).get("content", "분석을 가져올 수 없습니다."),
                    "success": True
                }
            else:
                return {
                    "stock_name": stock_name,
                    "stock_code": stock_code,
                    "analysis": "현재 분석을 가져올 수 없습니다. 나중에 다시 시도해주세요.",
                    "success": False
                }
                
        except Exception as e:
            logger.error(f"종목 분석 조회 실패: {e}")
            return {
                "stock_name": stock_name,
                "stock_code": stock_code,
                "analysis": "분석을 가져오는 중 오류가 발생했습니다.",
                "success": False
            }
    
    async def _make_request(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Perplexity API 요청 실행
        
        Args:
            prompt: 요청할 프롬프트
            
        Returns:
            API 응답 딕셔너리 또는 None
        """
        if not self.api_key:
            logger.warning("Perplexity API 키가 없어 요청을 건너뜁니다.")
            return None
            
        try:
            payload = {
                "model": "llama-3.1-sonar-small-128k-online",
                "messages": [
                    {
                        "role": "system",
                        "content": "당신은 한국의 금융 투자 전문가입니다. 복잡한 금융 개념을 일반 투자자가 이해하기 쉽게 설명하는 것이 특기입니다. 항상 한국어로 답변하고, 간결하고 실용적인 정보를 제공합니다."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                "max_tokens": 300,
                "temperature": 0.2,
                "top_p": 0.9,
                "stream": False
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Perplexity API 오류: {response.status}")
                        return None
                        
        except asyncio.TimeoutError:
            logger.error("Perplexity API 타임아웃")
            return None
        except Exception as e:
            logger.error(f"Perplexity API 요청 실패: {e}")
            return None

# 전역 클라이언트 인스턴스
perplexity_client = PerplexityClient()