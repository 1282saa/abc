"""
연관 질문 관련 API 라우터

키워드 기반 연관 질문 생성 및 조회 API를 제공합니다.
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
import os
import asyncio

from backend.api.dependencies import get_bigkinds_client
from backend.api.clients.bigkinds.client import BigKindsClient
from backend.utils.logger import setup_logger
from backend.services.content.question_generator_service import generate_refined_questions
from backend.services.news.question_builder import sanitize_list
from backend.services.news.related_news_system import RelatedNewsSystem

logger = setup_logger("api.related_questions")
router = APIRouter(
    prefix="/api/related-questions",
    tags=["관련 질문"],
    responses={404: {"description": "Not found"}}
)

# 키워드 전처리 함수
def preprocess_keyword(keyword: str) -> str:
    """
    키워드 전처리: 따옴표, 쉼표 제거 및 공백 정리
    
    Args:
        keyword: 원본 키워드
        
    Returns:
        전처리된 키워드
    """
    # 따옴표, 쉼표 제거 및 공백 정리
    cleaned = keyword.strip().strip("'\"").strip(",").strip()
    logger.debug(f"키워드 전처리: '{keyword}' -> '{cleaned}'")
    return cleaned

@router.get("/")
async def get_related_questions(
    keyword: str,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    max_questions: int = Query(10, ge=1, le=20),
    client: BigKindsClient = Depends(get_bigkinds_client)
):
    """
    키워드 기반 연관 질문 조회
    
    키워드 및 날짜 범위를 기반으로 의미 있는 연관 질문 목록을 생성합니다.
    
    Args:
        keyword: 검색 키워드
        date_from: 시작일 (YYYY-MM-DD)
        date_to: 종료일 (YYYY-MM-DD)
        max_questions: 반환할 최대 질문 수
        
    Returns:
        연관 질문 목록
    """
    # 키워드 전처리
    keyword = preprocess_keyword(keyword)
    logger.info(f"키워드 '{keyword}'에 대한 연관 질문 요청 - date_from: {date_from}, date_to: {date_to}")
    
    try:
        # 날짜 기본값 설정
        if not date_from:
            # 기본적으로 최근 30일
            date_from = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            
        if not date_to:
            # 기본적으로 오늘
            date_to = datetime.now().strftime("%Y-%m-%d")
        
        # 연관 질문 생성
        questions = client.generate_related_questions(
            keyword=keyword,
            date_from=date_from,
            date_to=date_to,
            max_questions=max_questions,
            cluster_count=5,
            max_recursion_depth=2,
            min_articles_per_query=3
        )
        
        return {
            "success": True,
            "keyword": keyword,
            "period": {
                "from": date_from,
                "to": date_to
            },
            "total_count": len(questions),
            "questions": questions
        }
    
    except Exception as e:
        logger.error(f"연관 질문 생성 오류: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"연관 질문 생성 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/v2")
async def get_related_questions_v2(
    keyword: str,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    max_questions: int = Query(7, ge=1, le=10),
    client: BigKindsClient = Depends(get_bigkinds_client)
):
    """
    키워드 기반 연관 질문 조회 (새 알고리즘)
    
    "AND 우선, 부족하면 OR" 전략을 사용하여 키워드 및 날짜 범위를 기반으로 
    의미 있는 연관 질문 목록을 생성합니다.
    
    Args:
        keyword: 검색 키워드
        date_from: 시작일 (YYYY-MM-DD)
        date_to: 종료일 (YYYY-MM-DD)
        max_questions: 반환할 최대 질문 수
        
    Returns:
        연관 질문 목록
    """
    # 키워드 전처리
    keyword = preprocess_keyword(keyword)
    logger.info(f"키워드 '{keyword}'에 대한 연관 질문(v2) 요청 - date_from: {date_from}, date_to: {date_to}")
    
    try:
        # 날짜 기본값 설정
        if not date_from:
            # 기본적으로 최근 30일
            date_from = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            
        if not date_to:
            # 기본적으로 오늘
            date_to = datetime.now().strftime("%Y-%m-%d")
        
        # API 키 디버깅 로그
        logger.debug(f"API 키 상태: OPENAI_API_KEY={bool(os.environ.get('OPENAI_API_KEY'))}, BIGKINDS_KEY={bool(os.environ.get('BIGKINDS_KEY'))}")
        
        # 새로운 알고리즘 기반 연관 질문 생성
        questions = await client.build_related_questions(
            keyword=keyword,
            date_from=date_from,
            date_to=date_to,
            max_questions=max_questions
        )
        
        return {
            "success": True,
            "keyword": keyword,
            "algorithm": "and_first_or_fallback",
            "period": {
                "from": date_from,
                "to": date_to
            },
            "total_count": len(questions),
            "questions": questions
        }
    
    except Exception as e:
        logger.error(f"연관 질문(v2) 생성 오류: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"연관 질문 생성 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/v3")
async def get_related_questions_v3(
    keyword: str,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    max_questions: int = Query(7, ge=1, le=10),
    client: BigKindsClient = Depends(get_bigkinds_client)
):
    """
    키워드 기반 LLM 다듬기 연관 질문 조회
    
    "경량 LLM → 요약 → 의미 추론 → 질문 생성" 방식을 사용하여 
    키워드 및 날짜 범위를 기반으로 고품질 연관 질문 목록을 생성합니다.
    
    Args:
        keyword: 검색 키워드
        date_from: 시작일 (YYYY-MM-DD)
        date_to: 종료일 (YYYY-MM-DD)
        max_questions: 반환할 최대 질문 수
        
    Returns:
        LLM으로 다듬어진 연관 질문 목록
    """
    # 키워드 전처리
    keyword = preprocess_keyword(keyword)
    logger.info(f"키워드 '{keyword}'에 대한 LLM 다듬기 연관 질문(v3) 요청 - date_from: {date_from}, date_to: {date_to}")
    
    try:
        # 날짜 기본값 설정
        if not date_from:
            # 기본적으로 최근 30일
            date_from = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            
        if not date_to:
            # 기본적으로 오늘
            date_to = datetime.now().strftime("%Y-%m-%d")
        
        # API 키 디버깅 로그
        logger.debug(f"API 키 상태: OPENAI_API_KEY={bool(os.environ.get('OPENAI_API_KEY'))}, BIGKINDS_KEY={bool(os.environ.get('BIGKINDS_KEY'))}")
        
        # LLM 기반 연관 질문 생성
        refined_questions = await generate_refined_questions(
            keyword=keyword,
            client=client,
            date_from=date_from,
            date_to=date_to
        )
        
        # 최대 질문 수 제한
        questions = refined_questions[:max_questions] if max_questions else refined_questions
        
        return {
            "success": True,
            "keyword": keyword,
            "algorithm": "llm_refined_questions",
            "period": {
                "from": date_from,
                "to": date_to
            },
            "total_count": len(questions),
            "questions": questions
        }
    
    except Exception as e:
        logger.error(f"LLM 다듬기 연관 질문(v3) 생성 오류: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"연관 질문 생성 중 오류가 발생했습니다: {str(e)}"
        )

# 뉴스 검색 헬퍼 함수
async def get_news_for_keyword(client: BigKindsClient, keyword: str, date_from: str, date_to: str, limit: int) -> Dict[str, Any]:
    """
    키워드에 대한 뉴스 검색 헬퍼 함수
    
    Args:
        client: BigKindsClient 인스턴스
        keyword: 검색할 키워드
        date_from: 시작일
        date_to: 종료일
        limit: 결과 제한 수
        
    Returns:
        키워드와 뉴스 정보가 포함된 딕셔너리
    """
    try:
        # 키워드 전처리
        processed_keyword = preprocess_keyword(keyword)
        
        # 뉴스 검색 - highlight와 images 필드 추가
        news_response = client.get_keyword_news(
            keyword=processed_keyword,
            date_from=date_from,
            date_to=date_to,
            return_size=limit,
            fields=[
                "news_id", 
                "title", 
                "content", 
                "published_at", 
                "provider_name", 
                "byline", 
                "highlight",  # 검색어 하이라이트 추가
                "images",     # 이미지 URL 추가
                "images_caption"  # 이미지 캡션 추가
            ]
        )
        
        # 응답 포맷팅
        formatted_news = client.format_news_response(news_response)
        news_items = formatted_news.get("documents", [])
        
        # 각 뉴스 항목에 대해 하이라이트와 이미지 정보 처리
        for item in news_items:
            # 하이라이트가 있으면 요약에 활용할 수 있도록 별도 필드로 추가
            if "highlight" in item and item["highlight"]:
                item["summary_from_highlight"] = item["highlight"]
            
            # 이미지 URL 처리
            if "images" in item and item["images"]:
                # 첫 번째 이미지만 대표 이미지로 지정
                if isinstance(item["images"], list) and len(item["images"]) > 0:
                    item["thumbnail"] = item["images"][0]
                elif isinstance(item["images"], str):
                    item["thumbnail"] = item["images"]
        
        return {
            "keyword": processed_keyword,
            "news": news_items,
            "total": len(news_items)
        }
    except Exception as e:
        logger.error(f"키워드 '{keyword}' 뉴스 조회 오류: {str(e)}")
        return {
            "keyword": keyword,
            "news": [],
            "error": str(e),
            "total": 0
        }

@router.post("/article-analysis")
async def analyze_article_and_get_related_news(
    request: Dict[str, Any],
    date_from: Optional[str] = Query(None, description="시작일 (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="종료일 (YYYY-MM-DD)"),
    news_limit: int = Query(10, ge=1, le=50, description="조회할 뉴스 기사 수"),
    keyword_limit: int = Query(10, ge=1, le=20, description="추출할 키워드 수"),
    client: BigKindsClient = Depends(get_bigkinds_client)
):
    """
    기사 내용 분석 및 관련 뉴스 조회 (OR 쿼리 방식)
    
    기사의 제목과 본문에서 키워드를 추출하고,
    추출된 키워드들을 OR 연산자로 연결하여 관련 뉴스를 조회합니다.
    
    Args:
        request: 기사 정보 (title, sub_title, content, url 등)
        date_from: 시작일 (YYYY-MM-DD)
        date_to: 종료일 (YYYY-MM-DD)
        news_limit: 조회할 뉴스 기사 수
        keyword_limit: 추출할 키워드 수
        
    Returns:
        추출된 키워드와 OR 쿼리로 조회한 관련 뉴스 목록
    """
    logger.info("기사 내용 분석 및 관련 뉴스 조회 요청")
    
    try:
        # 날짜 기본값 설정
        if not date_from:
            # 기본적으로 최근 30일
            date_from = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            
        if not date_to:
            # 기본적으로 오늘
            date_to = datetime.now().strftime("%Y-%m-%d")
        
        # 요청 데이터 추출
        title = request.get("title", "")
        sub_title = request.get("sub_title", "")
        content = request.get("content", "")
        article_url = request.get("url", "")
        
        if not title and not content:
            raise HTTPException(
                status_code=400,
                detail="제목이나 본문 중 하나는 필수입니다."
            )
        
        # 1. 키워드 추출 (특징 추출 API 사용)
        features = client.extract_features(
            title=title,
            sub_title=sub_title,
            content=content
        )
        
        # 2. 키워드 점수 기준으로 정렬 및 선택 (고유명사 우선)
        all_keywords = []
        
        # 각 필드에서 추출된 키워드를 통합
        for field in ["title", "sub_title", "content"]:
            for kw_data in features.get(field, []):
                keyword = preprocess_keyword(kw_data["keyword"])
                score = kw_data["score"]
                
                # 고유명사 가중치 부여
                is_proper_noun = any([
                    any(c.isupper() for c in keyword),  # 대문자 포함
                    any(c.isdigit() for c in keyword),  # 숫자 포함
                    keyword in ['AI', 'PRISM', 'D2LOG', '코스피', 'CEO', 'CFO', 'IT'],  # 중요 키워드
                    len(keyword) >= 3 and '_' in keyword,  # 복합 고유명사
                    keyword.endswith('전자') or keyword.endswith('그룹') or keyword.endswith('회사'),  # 기업명
                ])
                
                # 특별 중요 키워드에 추가 가중치
                is_super_important = any([
                    '2800' in keyword,
                    'D2LOG' in keyword,
                    'PRISM' in keyword,
                    keyword in ['AI', '코스피'],
                    '22조' in keyword,
                    keyword.endswith('전자')
                ])
                
                # 가중치 적용
                if is_super_important:
                    score *= 2.0  # 매우 중요한 키워드는 2배
                elif is_proper_noun:
                    score *= 1.5  # 일반 고유명사는 1.5배
                
                all_keywords.append({
                    "keyword": keyword,
                    "score": score,
                    "original_score": kw_data["score"],
                    "field": field,
                    "is_proper_noun": is_proper_noun
                })
        
        # 가중치 적용된 점수 기준 내림차순 정렬
        all_keywords.sort(key=lambda x: x["score"], reverse=True)
        
        # 중복 제거 및 상위 키워드 선택
        seen_keywords = set()
        selected_keywords = []
        
        for kw_data in all_keywords:
            keyword = kw_data["keyword"]
            if keyword not in seen_keywords and len(keyword) > 1:  # 한 글자 키워드 제외
                seen_keywords.add(keyword)
                selected_keywords.append(kw_data)
                if len(selected_keywords) >= keyword_limit:
                    break
        
        logger.debug(f"추출된 키워드 ({len(selected_keywords)}개): {[k['keyword'] for k in selected_keywords]}")
        
        # 키워드가 없으면 에러
        if not selected_keywords:
            raise HTTPException(
                status_code=400,
                detail="기사에서 유효한 키워드를 추출할 수 없습니다."
            )
        
        # 3. OR 쿼리 생성 (상위 5개 키워드만 사용)
        top_keywords = [kw["keyword"] for kw in selected_keywords[:5]]
        or_query = " OR ".join(top_keywords)
        
        logger.info(f"생성된 OR 쿼리: {or_query}")
        
        # 4. OR 쿼리로 뉴스 검색
        news_response = client.get_keyword_news(
            keyword=or_query,
            date_from=date_from,
            date_to=date_to,
            return_size=news_limit
        )
        
        # 응답 포맷팅
        formatted_news = client.format_news_response(news_response)
        news_list = formatted_news.get("documents", [])
        
        # 5. 결과 정리
        return {
            "success": True,
            "article": {
                "title": title,
                "sub_title": sub_title,
                "url": article_url,
                "content_preview": content[:200] + "..." if len(content) > 200 else content
            },
            "period": {
                "from": date_from,
                "to": date_to
            },
            "extracted_keywords": [k["keyword"] for k in selected_keywords],
            "keywords_with_scores": [
                {
                    "keyword": k["keyword"],
                    "score": k["score"],
                    "original_score": k["original_score"],
                    "field": k["field"],
                    "is_proper_noun": k["is_proper_noun"]
                } for k in selected_keywords
            ],
            "search_query": or_query,
            "news": news_list,
            "total_news": len(news_list)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"기사 분석 및 관련 뉴스 조회 오류: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"기사 분석 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/article-to-questions")
async def generate_questions_from_article(
    request: Dict[str, Any],
    date_from: Optional[str] = Query(None, description="시작일 (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="종료일 (YYYY-MM-DD)"),
    max_questions: int = Query(5, ge=1, le=10, description="생성할 질문 수"),
    client: BigKindsClient = Depends(get_bigkinds_client)
):
    """
    기사 전체 내용 분석을 통한 AI 맞춤형 질문 생성
    
    기사의 제목과 본문 전체를 특성추출 API에 보내서 핵심 키워드를 추출하고,
    그 키워드들을 바탕으로 관련 뉴스를 조회한 후 의미있는 질문을 생성합니다.
    
    Args:
        request: 기사 정보 (title, sub_title, content 등)
        date_from: 시작일 (YYYY-MM-DD)
        date_to: 종료일 (YYYY-MM-DD)
        max_questions: 생성할 질문 수
        
    Returns:
        추출된 키워드와 생성된 맞춤형 질문 목록
    """
    logger.info("기사 전체 내용 기반 AI 맞춤형 질문 생성 요청")
    
    try:
        # 날짜 기본값 설정 (범위 확장)
        if not date_from:
            date_from = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")  # 3개월로 확장
        if not date_to:
            date_to = datetime.now().strftime("%Y-%m-%d")
        
        # 요청 데이터 추출
        title = request.get("title", "")
        sub_title = request.get("sub_title", "")
        content = request.get("content", "")
        
        if not title and not content:
            raise HTTPException(
                status_code=400,
                detail="제목이나 본문 중 하나는 필수입니다."
            )
        
        # 1. 전체 기사 내용에서 특성 추출
        logger.info("기사 전체 내용 특성 추출 시작")
        features = client.extract_features(
            title=title,
            sub_title=sub_title,
            content=content
        )
        
        # 2. 추출된 특성에서 주요 키워드 선별 (단일 고유명사 우선)
        all_keywords = []
        
        for field in ["title", "sub_title", "content"]:
            for kw_data in features.get(field, []):
                original_keyword = preprocess_keyword(kw_data["keyword"])
                score = kw_data["score"]
                
                # 복합 키워드 처리 - 단순 키워드 우선
                keywords_to_process = []
                
                if '_' in original_keyword and len(original_keyword.split('_')) <= 3:
                    # 복합 키워드를 분리하여 단순 키워드 우선 처리
                    parts = original_keyword.split('_')
                    for part in parts:
                        if len(part) >= 2:  # 2글자 이상만
                            keywords_to_process.append((part, score * 1.2))  # 단순 키워드에 가중치
                    
                    # 복합 키워드는 낮은 점수로
                    if len(parts) <= 2:  # 2개 조합까지만 허용
                        keywords_to_process.append((original_keyword, score * 0.5))
                else:
                    keywords_to_process.append((original_keyword, score))
                
                for keyword, kw_score in keywords_to_process:
                    # 특별 중요 키워드 (높은 가중치)
                    is_super_important = any([
                        keyword in ['책임광물', '삼성전자', 'LG전자', 'SK하이닉스', 'ESG', '공급망'],
                        keyword.endswith('전자') or keyword.endswith('그룹') or keyword.endswith('회사'),
                        keyword in ['AI', 'IT', '정부', '정책', '법안', '규정', '규제']
                    ])
                    
                    # 일반 고유명사 (중간 가중치)
                    is_proper_noun = any([
                        any(c.isupper() for c in keyword),  # 대문자 포함
                        any(c.isdigit() for c in keyword),  # 숫자 포함
                        len(keyword) >= 4,  # 4글자 이상 단어
                        keyword.endswith('법') or keyword.endswith('청') or keyword.endswith('부')
                    ])
                    
                    # 가중치 적용
                    if is_super_important:
                        kw_score *= 3.0  # 매우 중요한 키워드는 3배
                    elif is_proper_noun:
                        kw_score *= 1.5  # 일반 고유명사는 1.5배
                    
                    # 너무 짧거나 불용어는 제외
                    if len(keyword) >= 2 and keyword not in ['관련', '통해', '위해', '등', '및']:
                        all_keywords.append({
                            "keyword": keyword,
                            "score": kw_score,
                            "field": field,
                            "is_super_important": is_super_important,
                            "is_proper_noun": is_proper_noun
                        })
        
        # 점수 기준 정렬 및 중복 제거
        all_keywords.sort(key=lambda x: x["score"], reverse=True)
        
        # 중복 제거하면서 상위 키워드 선택
        seen_keywords = set()
        top_keywords = []
        for kw in all_keywords:
            if kw["keyword"] not in seen_keywords:
                seen_keywords.add(kw["keyword"])
                top_keywords.append(kw["keyword"])
                if len(top_keywords) >= 8:  # 더 많은 키워드 확보
                    break
        
        if not top_keywords:
            raise HTTPException(
                status_code=400,
                detail="기사에서 유효한 키워드를 추출할 수 없습니다."
            )
        
        # 3. 각 주요 키워드로 실용적인 질문 생성
        questions = []
        
        # 상위 키워드들로 다양한 유형의 질문 생성
        question_templates = [
            ("{} 관련 주요 뉴스는?", "basic"),
            ("{} 최근 동향은?", "basic"),  
            ("{} 기업 동향은?", "business"),
            ("{} 정책 변화는?", "policy"),
            ("{} 시장 전망은?", "market")
        ]
        
        # 키워드별로 질문 생성
        for i, keyword in enumerate(top_keywords[:max_questions]):
            if i < len(question_templates):
                template, q_type = question_templates[i]
                question = template.format(keyword)
            else:
                # 기본 템플릿 재사용
                question = f"{keyword} 관련 주요 뉴스는?"
                q_type = "basic"
                
            questions.append({
                "question": question,
                "type": q_type,
                "keywords": [keyword],
                "base_keyword": keyword
            })
        
        # 복합 질문도 몇 개 추가 (키워드가 충분히 있을 때)
        if len(top_keywords) >= 2 and len(questions) < max_questions:
            combo_question = f"{top_keywords[0]}와 {top_keywords[1]} 최근 이슈는?"
            questions.append({
                "question": combo_question,
                "type": "combo",
                "keywords": top_keywords[:2],
                "base_keyword": top_keywords[0]
            })
        
        # 요청된 수만큼 질문 제한
        questions = questions[:max_questions]
        
        # 4. 각 질문에 대해 실제 뉴스 조회하여 관련성 검증
        for question_data in questions:
            base_keyword = question_data["base_keyword"]
            try:
                # 해당 키워드로 실제 뉴스 검색해서 관련성 확인
                news_response = client.get_keyword_news(
                    keyword=base_keyword,
                    date_from=date_from,
                    date_to=date_to,
                    return_size=5  # 적은 수로 빠르게 확인
                )
                
                # 응답 포맷팅하여 뉴스 수 확인
                formatted_news = client.format_news_response(news_response)
                news_count = len(formatted_news.get("documents", []))
                
                question_data["related_news_count"] = news_count
                question_data["has_related_news"] = news_count > 0
                
                # 관련 뉴스가 있으면 샘플 제목 저장
                if news_count > 0:
                    sample_titles = [news.get("title", "") for news in formatted_news.get("documents", [])[:2]]
                    question_data["sample_news_titles"] = sample_titles
                    
            except Exception as e:
                logger.warning(f"키워드 '{base_keyword}' 뉴스 조회 실패: {e}")
                question_data["related_news_count"] = 0
                question_data["has_related_news"] = False
        
        logger.info(f"AI 맞춤형 질문 {len(questions)}개 생성 완료")
        
        return {
            "success": True,
            "article": {
                "title": title,
                "sub_title": sub_title,
                "content_preview": content[:200] + "..." if len(content) > 200 else content
            },
            "extracted_keywords": top_keywords,
            "period": {
                "from": date_from,
                "to": date_to
            },
            "questions": questions,
            "total_questions": len(questions)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"기사 기반 질문 생성 오류: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"질문 생성 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/keywords-news")
async def get_keywords_with_news(
    keyword: str,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    related_limit: int = Query(5, ge=1, le=20, description="연관 키워드 수"),
    topn_limit: int = Query(5, ge=1, le=20, description="TopN 키워드 수"),
    news_limit: int = Query(3, ge=1, le=10, description="각 키워드당 뉴스 기사 수"),
    client: BigKindsClient = Depends(get_bigkinds_client)
):
    """
    키워드 및 연관 키워드 기반 뉴스 조회
    
    입력된 키워드로 연관 키워드와 TopN 키워드를 추출하고,
    각 키워드별로 뉴스를 조회하여 함께 반환합니다.
    
    Args:
        keyword: 검색 키워드
        date_from: 시작일 (YYYY-MM-DD)
        date_to: 종료일 (YYYY-MM-DD)
        related_limit: 연관 키워드 수
        topn_limit: TopN 키워드 수
        news_limit: 각 키워드당 뉴스 기사 수
        
    Returns:
        연관 키워드 및 TopN 키워드와 각 키워드별 뉴스 목록
    """
    # 키워드 전처리
    keyword = preprocess_keyword(keyword)
    logger.info(f"키워드 '{keyword}'에 대한 연관 키워드 및 뉴스 요청 - date_from: {date_from}, date_to: {date_to}")
    
    try:
        # 날짜 기본값 설정
        if not date_from:
            # 기본적으로 최근 30일
            date_from = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            
        if not date_to:
            # 기본적으로 오늘
            date_to = datetime.now().strftime("%Y-%m-%d")
        
        # 연관 키워드와 TopN 키워드 병렬로 가져오기
        related_keywords_raw, topn_keywords_raw = await asyncio.gather(
            client.get_related_keywords(
                keyword=keyword,
                date_from=date_from,
                date_to=date_to,
                max_count=related_limit * 2  # 필터링을 고려해 2배로 요청
            ),
            client.get_keyword_topn(
                keyword=keyword,
                date_from=date_from,
                date_to=date_to,
                limit=topn_limit * 2  # 필터링을 고려해 2배로 요청
            )
        )
        
        # 데이터 정제 (해시 불가능한 요소 제거)
        related_keywords_clean = sanitize_list(related_keywords_raw, "연관어")
        topn_keywords_clean = sanitize_list(topn_keywords_raw, "TopN")
        
        # 문자열 키워드만 필터링
        related_keywords = [k for k in related_keywords_clean if isinstance(k, str)][:related_limit]
        topn_keywords = [k for k in topn_keywords_clean if isinstance(k, str)][:topn_limit]
        
        # 중복 제거: TopN 키워드 중 연관 키워드와 중복되는 것 제외
        topn_keywords = [k for k in topn_keywords if k not in related_keywords]
        
        logger.debug(f"필터링 후 연관 키워드 ({len(related_keywords)}개): {related_keywords}")
        logger.debug(f"필터링 후 TopN 키워드 ({len(topn_keywords)}개): {topn_keywords}")
        
        # 모든 키워드 준비 (원본 키워드, 연관 키워드, TopN 키워드)
        all_keywords = [{"keyword": keyword, "type": "original"}]
        all_keywords.extend([{"keyword": k, "type": "related"} for k in related_keywords])
        all_keywords.extend([{"keyword": k, "type": "topn"} for k in topn_keywords])
        
        # 병렬로 모든 키워드에 대한 뉴스 검색
        news_tasks = []
        for kw_info in all_keywords:
            task = get_news_for_keyword(
                client=client,
                keyword=kw_info["keyword"],
                date_from=date_from,
                date_to=date_to,
                limit=news_limit
            )
            news_tasks.append(task)
        
        # 모든 뉴스 검색 작업 병렬 실행
        news_results = await asyncio.gather(*news_tasks)
        
        # 결과 통합
        keywords_news = []
        for i, result in enumerate(news_results):
            kw_type = all_keywords[i]["type"]
            keywords_news.append({
                "keyword": result["keyword"],
                "type": kw_type,
                "news": result["news"],
                "total": result["total"],
                "error": result.get("error", None)
            })
        
        return {
            "success": True,
            "keyword": keyword,
            "period": {
                "from": date_from,
                "to": date_to
            },
            "related_keywords": related_keywords,
            "topn_keywords": topn_keywords,
            "keywords_news": keywords_news
        }
    
    except Exception as e:
        logger.error(f"연관 키워드 및 뉴스 조회 오류: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"연관 키워드 및 뉴스 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/article-questions")
async def generate_article_questions_with_news(
    request: Dict[str, Any],
    date_from: Optional[str] = Query(None, description="시작일 (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="종료일 (YYYY-MM-DD)"),
    max_questions: int = Query(7, ge=1, le=10, description="생성할 질문 수"),
    client: BigKindsClient = Depends(get_bigkinds_client)
):
    """
    기사 내용 기반 고급 질문 생성 및 관련 뉴스 검색
    
    기사 내용을 분석하여 키워드를 추출하고 그룹화한 후,
    템플릿 기반의 질문을 생성하고 각 질문에 관련된 뉴스를 매핑합니다.
    
    Args:
        request: 기사 정보 (title, content 등)
        date_from: 시작일 (YYYY-MM-DD)
        date_to: 종료일 (YYYY-MM-DD)
        max_questions: 생성할 질문 수
        
    Returns:
        질문 목록 및 각 질문에 매핑된 관련 뉴스
    """
    logger.info("기사 내용 기반 고급 질문 생성 및 관련 뉴스 검색 요청")
    
    # 날짜 기본값 설정
    if not date_from:
        # 기본적으로 최근 30일
        date_from = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    if not date_to:
        # 기본적으로 오늘
        date_to = datetime.now().strftime("%Y-%m-%d")
    
    # 요청 데이터 추출
    title = request.get("title", "")
    content = request.get("content", "")
    
    if not title and not content:
        raise HTTPException(
            status_code=400,
            detail="제목이나 본문 중 하나는 필수입니다."
        )
    
    try:
        # 통합 시스템 처리
        result = await RelatedNewsSystem.process_article_async(
            article={"title": title, "content": content},
            client=client,
            date_from=date_from,
            date_to=date_to
        )
        
        if not result.get("success", False):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "질문 생성 처리 중 오류가 발생했습니다.")
            )
        
        # 생성된 질문 수 제한
        questions = result.get("questions", [])[:max_questions]
        
        # 질문-뉴스 매핑
        question_news_mapping = {}
        for question in questions:
            question_news_mapping[question] = result.get("question_news_mapping", {}).get(question, [])
        
        return {
            "success": True,
            "article": {
                "title": title,
                "content_preview": content[:200] + "..." if len(content) > 200 else content
            },
            "period": {
                "from": date_from,
                "to": date_to
            },
            "keyword_groups": result.get("keyword_groups", {}),
            "search_queries": result.get("search_queries", []),
            "related_keywords": result.get("related_keywords", []),
            "topn_keywords": result.get("topn_keywords", []),
            "questions": questions,
            "question_news_mapping": question_news_mapping,
            "total_questions": len(questions),
            "formatted_result": RelatedNewsSystem.format_questions_with_news(result)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"기사 기반 질문 생성 및 뉴스 검색 오류: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"질문 생성 및 뉴스 검색 중 오류가 발생했습니다: {str(e)}"
        ) 