"""
프롬프트 템플릿 모듈

LLM에 전송할 다양한 프롬프트 템플릿을 제공합니다.
질의응답, 요약, 타임라인 생성 등 다양한 목적에 맞는 프롬프트를 구성합니다.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime

class PromptTemplates:
    """LLM 프롬프트 템플릿 클래스"""
    
    def __init__(self):
        """프롬프트 템플릿 초기화"""
        # 시스템 프롬프트 사전 정의
        self.system_prompts = {
            "default": "당신은 뉴스 데이터 기반 질의응답 AI 비서입니다. 제공된 뉴스 기사 정보를 바탕으로 사용자 질문에 정확하게 답변해 주세요.",
            "qa": "당신은 뉴스 데이터 기반 질의응답 AI 비서입니다. 제공된 뉴스 기사 정보를 바탕으로 사용자 질문에 정확하게 답변해 주세요. 제공된 뉴스 정보에 없는 내용은 '제공된 뉴스에서 관련 정보를 찾을 수 없습니다'라고 답변하세요. 사실과 다른 내용을 생성하거나 추측하지 마세요.",
            "summarize": "당신은 뉴스 요약 전문가입니다. 제공된 여러 뉴스 기사를 종합하여 핵심 내용을 간결하고 명확하게 요약해 주세요. 중요한 사실과 정보만 포함하고, 불필요한 세부 사항은 생략하세요.",
            "timeline": "당신은 뉴스 기반 타임라인 생성 전문가입니다. 제공된 뉴스 기사들을 시간 순서대로 정렬하여 사건의 흐름을 타임라인 형식으로 정리해 주세요. 각 사건별로 날짜와 핵심 내용을 명확히 표시하세요."
        }
        
    def get_qa_prompt(self, query: str, contexts: List[Dict[str, Any]], max_context_count: int = 5) -> Dict[str, str]:
        """질의응답 프롬프트 생성
        
        Args:
            query: 사용자 질문
            contexts: 검색된 관련 문맥 정보 리스트
            max_context_count: 최대 문맥 수
            
        Returns:
            시스템 프롬프트와 사용자 프롬프트가 담긴 딕셔너리
        """
        # 문맥이 너무 많으면 자르기
        if len(contexts) > max_context_count:
            contexts = contexts[:max_context_count]
        
        # 문맥 포매팅
        formatted_contexts = []
        for i, context in enumerate(contexts, 1):
            title = context.get("metadata", {}).get("title", "제목 없음")
            text = context.get("text", "")
            provider = context.get("metadata", {}).get("provider", "")
            date = context.get("metadata", {}).get("date", "")
            
            source = f"{provider}" if provider else ""
            if date:
                source = f"{source} ({date})" if source else f"{date}"
            
            formatted_context = f"[출처 {i}] {title}\n{text}\n출처: {source}\n"
            formatted_contexts.append(formatted_context)
        
        # 문맥 결합
        combined_context = "\n".join(formatted_contexts)
        
        # 사용자 프롬프트 구성
        user_prompt = f"""질문: {query}

다음은 질문과 관련된 뉴스 기사 정보입니다:

{combined_context}

위 뉴스 정보를 바탕으로 질문에 답변해주세요. 답변에는 관련된 출처를 [출처 번호]와 같이 표시해주세요. 제공된 뉴스 정보에 없는 내용은 추측하지 말고 '제공된 뉴스에서 관련 정보를 찾을 수 없습니다'라고 답변하세요."""

        return {
            "system": self.system_prompts["qa"],
            "user": user_prompt
        }
    
    def get_summarization_prompt(self, query: str, contexts: List[Dict[str, Any]], max_context_count: int = 8) -> Dict[str, str]:
        """요약 프롬프트 생성
        
        Args:
            query: 요약 주제 또는 질문
            contexts: 요약할 문맥 정보 리스트
            max_context_count: 최대 문맥 수
            
        Returns:
            시스템 프롬프트와 사용자 프롬프트가 담긴 딕셔너리
        """
        # 문맥이 너무 많으면 자르기
        if len(contexts) > max_context_count:
            contexts = contexts[:max_context_count]
        
        # 문맥 포매팅
        formatted_contexts = []
        for i, context in enumerate(contexts, 1):
            title = context.get("metadata", {}).get("title", "제목 없음")
            text = context.get("text", "")
            date = context.get("metadata", {}).get("date", "")
            
            date_str = f" ({date})" if date else ""
            formatted_context = f"[기사 {i}]{date_str} {title}\n{text}\n"
            formatted_contexts.append(formatted_context)
        
        # 문맥 결합
        combined_context = "\n".join(formatted_contexts)
        
        # 요약 지시문 구성
        summary_instruction = f"'{query}' 주제와 관련하여 다음 뉴스 기사들을 종합 요약해주세요."
        
        # 사용자 프롬프트 구성
        user_prompt = f"""{summary_instruction}

다음은 관련 뉴스 기사들입니다:

{combined_context}

위 뉴스들을 종합하여 핵심 내용을 간결하게 요약해주세요. 중요한 사실과 정보만 포함하고, 불필요한 세부 사항은 생략하세요. 상반된 관점이 있다면 균형있게 다루어주세요."""

        return {
            "system": self.system_prompts["summarize"],
            "user": user_prompt
        }
    
    def get_timeline_prompt(self, query: str, contexts: List[Dict[str, Any]], max_context_count: int = 15) -> Dict[str, str]:
        """타임라인 생성 프롬프트
        
        Args:
            query: 타임라인 주제 또는 질문
            contexts: 관련 문맥 정보 리스트
            max_context_count: 최대 문맥 수
            
        Returns:
            시스템 프롬프트와 사용자 프롬프트가 담긴 딕셔너리
        """
        # 문맥이 너무 많으면 자르기
        if len(contexts) > max_context_count:
            contexts = contexts[:max_context_count]
        
        # 날짜별 정렬
        try:
            contexts = sorted(
                contexts, 
                key=lambda x: datetime.strptime(x.get("metadata", {}).get("date", "2000-01-01"), "%Y-%m-%d")
            )
        except Exception:
            # 날짜 형식이 다양할 경우 정렬 실패 가능성 있음
            pass
        
        # 문맥 포매팅
        formatted_contexts = []
        for i, context in enumerate(contexts, 1):
            title = context.get("metadata", {}).get("title", "제목 없음")
            text = context.get("text", "")
            date = context.get("metadata", {}).get("date", "날짜 미상")
            
            formatted_context = f"[{date}] {title}\n{text}\n"
            formatted_contexts.append(formatted_context)
        
        # 문맥 결합
        combined_context = "\n".join(formatted_contexts)
        
        # 타임라인 지시문 구성
        timeline_instruction = f"'{query}' 주제에 대한 시간순 타임라인을 작성해주세요."
        
        # 사용자 프롬프트 구성
        user_prompt = f"""{timeline_instruction}

다음은 관련 뉴스 기사들입니다 (시간순 정렬):

{combined_context}

위 뉴스들을 바탕으로 주요 사건을 시간 순서대로 정리한 타임라인을 작성해주세요. 각 사건은 날짜와 함께 간결하게 설명하고, 중요한 변화나 전환점을 강조해주세요. 타임라인 형식은 다음과 같이 만들어주세요:

## [주제] 타임라인

- **YYYY-MM-DD**: 첫 번째 사건 내용
- **YYYY-MM-DD**: 두 번째 사건 내용
...

마지막에는 이 타임라인을 통해 알 수 있는 전체적인 흐름이나 통찰을 1-2문장으로 추가해주세요."""

        return {
            "system": self.system_prompts["timeline"],
            "user": user_prompt
        }
    
    def get_custom_prompt(self, system_prompt: str, user_prompt: str) -> Dict[str, str]:
        """사용자 정의 프롬프트 생성
        
        Args:
            system_prompt: 시스템 프롬프트
            user_prompt: 사용자 프롬프트
            
        Returns:
            시스템 프롬프트와 사용자 프롬프트가 담긴 딕셔너리
        """
        return {
            "system": system_prompt,
            "user": user_prompt
        }
    
    def analyze_query_intent(self, query: str) -> str:
        """쿼리 의도 분석
        
        Args:
            query: 사용자 질문
            
        Returns:
            의도 유형 (qa, summarize, timeline 등)
        """
        query_lower = query.lower()
        
        # 타임라인 의도 감지
        timeline_keywords = ["타임라인", "시간순", "연대순", "흐름", "전개", "과정", "추이", "변화"]
        for keyword in timeline_keywords:
            if keyword in query_lower:
                return "timeline"
        
        # 요약 의도 감지
        summary_keywords = ["요약", "정리", "종합", "간략", "간단", "핵심"]
        for keyword in summary_keywords:
            if keyword in query_lower:
                return "summarize"
        
        # 기본값은 질의응답
        return "qa" 