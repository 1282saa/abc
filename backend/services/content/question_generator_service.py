"""
뉴스 질문 생성 서비스

이 모듈은 "경량 LLM → 요약 → 의미 추론 → 질문 생성" 방식의 하이브리드 질문 생성 파이프라인을 구현합니다.
1. BigKinds 연관어/TopN을 통해 키워드 데이터 수집
2. 규칙 엔진을 통해 초안 질문 생성
3. 경량 LLM을 통해 질문 다듬기 및 심층 질문 추가
4. Redis 캐싱을 통해 결과 저장
"""

import os
import json
import asyncio
from typing import List, Dict, Any, Optional, Tuple
import logging
from datetime import datetime, timedelta

# AsyncOpenAI 대신 openai 모듈 직접 사용
import openai
from backend.api.clients.bigkinds import BigKindsClient
from backend.services.news.question_builder import build_questions
from backend.utils.redis_cache import cached, cache_get, cache_set, generate_cache_key

# 로거 설정
logger = logging.getLogger(__name__)

# OpenAI API 키 설정
openai.api_key = os.environ.get("OPENAI_API_KEY")

# 시스템 프롬프트 및 사용자 프롬프트 템플릿
SYSTEM_PROMPT = "당신은 경제 전문 기자입니다."

USER_PROMPT_TEMPLATE = """
[요약]
{summary}
[초안 질문]
{draft_questions_json}

위 요약을 기준으로 독자가 궁금해할 추가 질문을
5개 내외로 엄선해 주세요.
- draft에서 의미가 겹치면 하나만 남기고 자연스러운 문장으로 다듬습니다.
- 최소 1개는 '영향·전망' 같은 심층형 질문을 넣습니다.
JSON 배열:
[{"question":"...", "query":"..."}]
"""

SUMMARY_PROMPT = """
다음 뉴스 내용을 3문장으로 요약해주세요:

{content}
"""


async def quick_summary(keyword: str, client: BigKindsClient, 
                   date_from: Optional[str] = None, 
                   date_to: Optional[str] = None) -> str:
    """
    뉴스 기사를 3문장으로 요약
    
    Args:
        keyword: 검색 키워드
        client: BigKindsClient 인스턴스
        date_from: 시작일 (YYYY-MM-DD)
        date_to: 종료일 (YYYY-MM-DD)
        
    Returns:
        3문장 요약 텍스트
    """
    # 날짜 기본값 설정
    if not date_from:
        date_from = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    if not date_to:
        date_to = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    # 키워드 관련 최신 뉴스 가져오기 (요약용)
    result = client.search_news(
        query=keyword,
        date_from=date_from,
        date_to=date_to,
        return_size=5,  # 상위 5개 기사만 가져옴
        fields=["content", "title"]
    )
    
    # 뉴스 내용 추출
    news_contents = []
    if result.get("result") == 0:
        documents = result.get("return_object", {}).get("documents", [])
        for doc in documents:
            content = doc.get("content", "")
            if content:
                news_contents.append(content)
    
    if not news_contents:
        return f"{keyword} 관련 최근 뉴스가 충분하지 않습니다."
    
    # 내용이 너무 길면 토큰 제한을 위해 앞부분만 사용
    combined_content = "\n\n".join(news_contents[:3])
    if len(combined_content) > 6000:
        combined_content = combined_content[:6000] + "..."
    
    # OpenAI API를 사용한 요약 생성 (구버전 호환)
    try:
        response = await openai.ChatCompletion.create(
            model="gpt-4o-mini",  # 또는 다른 경량 모델 (Mistral-7B-Instruct 등)
            temperature=0.3,
            messages=[
                {"role": "system", "content": "당신은 뉴스 요약 전문가입니다."},
                {"role": "user", "content": SUMMARY_PROMPT.format(content=combined_content)}
            ]
        )
        summary = response.choices[0].message.content.strip()
        return summary
    except Exception as e:
        logger.error(f"뉴스 요약 오류: {str(e)}")
        # 요약 실패 시 첫 번째 뉴스 내용 앞부분만 반환
        if news_contents:
            return news_contents[0][:300] + "..."
        return f"{keyword} 관련 요약 생성에 실패했습니다."


async def llm_refine(summary: str, draft_questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    경량 LLM을 사용하여 초안 질문을 다듬고 심층 질문 추가
    
    Args:
        summary: 뉴스 요약 (3문장)
        draft_questions: 초안 질문 목록
        
    Returns:
        다듬어진 질문 목록
    """
    try:
        # JSON 변환
        draft_json = json.dumps(
            [{"question": q["question"], "query": q["query"]} for q in draft_questions], 
            ensure_ascii=False
        )
        
        # LLM 호출 (구버전 호환)
        response = await openai.ChatCompletion.create(
            model="gpt-4o-mini",
            temperature=0.3,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": USER_PROMPT_TEMPLATE.format(
                    summary=summary,
                    draft_questions_json=draft_json
                )}
            ]
        )
        
        # 응답 처리
        content = response.choices[0].message.content
        
        # JSON 부분 추출 및 파싱
        try:
            # 응답에서 JSON 배열 부분만 추출
            import re
            json_match = re.search(r'\[(.*?)\]', content, re.DOTALL)
            if json_match:
                json_str = "[" + json_match.group(1) + "]"
                refined_questions = json.loads(json_str)
            else:
                # 전체 응답을 JSON으로 파싱 시도
                refined_questions = json.loads(content)
            
            # 유효성 검사
            if not isinstance(refined_questions, list):
                raise ValueError("응답이 유효한 JSON 배열이 아닙니다")
            
            return refined_questions
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"LLM 응답 파싱 오류: {str(e)}, 응답: {content}")
            return draft_questions
            
    except Exception as e:
        logger.error(f"LLM 질문 다듬기 오류: {str(e)}")
        return draft_questions


@cached(prefix="refined_questions", ttl=21600)  # 6시간 캐싱
async def generate_refined_questions(
    keyword: str,
    client: BigKindsClient,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    키워드 기반 다듬어진 질문 생성 (규칙 엔진 + LLM)
    
    Args:
        keyword: 검색 키워드
        client: BigKindsClient 인스턴스
        date_from: 시작일 (YYYY-MM-DD)
        date_to: 종료일 (YYYY-MM-DD)
        
    Returns:
        다듬어진 질문 목록
    """
    # 날짜 기본값 설정
    if not date_from:
        date_from = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    if not date_to:
        date_to = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    logger.info(f"'{keyword}' 키워드 기반 다듬어진 질문 생성 시작")
    
    try:
        # 1. 규칙 엔진으로 초안 질문 생성
        draft_questions = await build_questions(
            base=keyword,
            client=client,
            date_from=date_from,
            date_until=date_to
        )
        
        # 기본 질문만 있는 경우 바로 반환
        if len(draft_questions) <= 1:
            logger.info(f"'{keyword}' 초안 질문이 충분하지 않아 LLM 호출 생략")
            return draft_questions
        
        # 2. 뉴스 요약 생성
        summary = await quick_summary(keyword, client, date_from, date_to)
        
        # 3. LLM으로 질문 다듬기
        refined_questions = await llm_refine(summary, draft_questions)
        
        logger.info(f"'{keyword}' 다듬어진 질문 {len(refined_questions)}개 생성 완료")
        return refined_questions
    
    except Exception as e:
        logger.error(f"질문 생성 오류: {str(e)}")
        # 오류 발생 시 원본 질문 반환 (또는 빈 배열)
        return draft_questions if 'draft_questions' in locals() else [] 