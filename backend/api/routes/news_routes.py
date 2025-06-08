"""
뉴스 관련 API 라우트

최신 뉴스, 인기 키워드, 이슈 등 뉴스 관련 API 엔드포인트를 정의합니다.
타임라인 형식의 뉴스 제공 및 상세 내용 조회 기능을 포함합니다.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Path
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime, date, timedelta
import sys
from pathlib import Path as PathLib

# 프로젝트 루트 디렉토리 찾기
PROJECT_ROOT = PathLib(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.utils.logger import setup_logger
from backend.api.clients.bigkinds_client import BigKindsClient
import openai
import os
from backend.constants.provider_map import PROVIDER_MAP

# API 라우터 생성
router = APIRouter(prefix="/api/news", tags=["뉴스"])

# BigKinds 클라이언트 인스턴스
def get_bigkinds_client():
    """BigKinds 클라이언트 인스턴스 가져오기"""
    return BigKindsClient()

# 모델 정의
class LatestNewsResponse(BaseModel):
    """최신 뉴스 응답 모델"""
    today_issues: List[Dict[str, Any]] = Field(description="오늘의 이슈 (빅카인즈 이슈 랭킹)")
    popular_keywords: List[Dict[str, Any]] = Field(description="인기 키워드")
    timestamp: str = Field(description="응답 시간")

class CompanyNewsRequest(BaseModel):
    """기업 뉴스 요청 모델"""
    company_name: str = Field(..., description="기업명")
    date_from: Optional[str] = Field(None, description="시작일 (YYYY-MM-DD)")
    date_to: Optional[str] = Field(None, description="종료일 (YYYY-MM-DD)")
    limit: Optional[int] = Field(default=20, description="가져올 기사 수", ge=1, le=100)

class KeywordNewsRequest(BaseModel):
    """키워드 뉴스 요청 모델"""
    keyword: str = Field(..., description="검색 키워드")
    date_from: Optional[str] = Field(None, description="시작일 (YYYY-MM-DD)")
    date_to: Optional[str] = Field(None, description="종료일 (YYYY-MM-DD)")
    limit: Optional[int] = Field(default=30, description="가져올 기사 수", ge=1, le=100)

class AISummaryRequest(BaseModel):
    """AI 요약 요청 모델"""
    news_ids: List[str] = Field(..., description="요약할 뉴스 ID 리스트 (최대 5개)", max_items=5)
    summary_type: str = Field(..., description="요약 유형", pattern="^(issue|quote|data)$")

# 엔드포인트 정의
@router.get("/latest", response_model=LatestNewsResponse)
async def get_latest_news(
    bigkinds_client: BigKindsClient = Depends(get_bigkinds_client)
):
    """최신 뉴스 정보 조회 (수정된 API 구조 기반)
    
    - 오늘의 이슈 (빅카인즈 이슈 랭킹)
    - 인기 키워드 (전체 검색 순위)
    """
    logger = setup_logger("api.news.latest")
    logger.info("최신 뉴스 정보 요청")
    
    today_issues = []
    popular_keywords = []
    
    try:
        # 1. 오늘의 이슈 가져오기 (오늘 날짜 기본 사용)
        logger.info("오늘의 이슈 요청 시작")
        issue_response = bigkinds_client.get_issue_ranking()  # 오늘 날짜 자동 설정
        
        if issue_response.get("result") == 0:
            # format_issue_ranking_response 메소드 사용
            formatted_issues = bigkinds_client.format_issue_ranking_response(issue_response)
            ### 언론사 기사 매핑.
            if formatted_issues.get("success"):
                topics = formatted_issues.get("topics", [])[:10]  # 상위 10개만
                # 언론사 코드 → 이름 매핑 (일부 주요 언론사만 포함, 필요시 추가 가능) 
                today_issues = []
                for idx, topic in enumerate(topics):
                    cluster_ids = topic.get("news_cluster", [])
                    # 실제 뉴스 ID 수집 및 언론사별 카운팅
                    provider_counts = {}
                    actual_news_ids = []
                    
                    if cluster_ids:
                        try:
                            # 먼저 클러스터 ID에서 직접 언론사 코드 추출 (추가 로직)
                            logger.info(f"클러스터 ID 직접 처리 시작: {len(cluster_ids)} 개")
                            for cluster_id in cluster_ids:
                                if cluster_id and "." in cluster_id:
                                    # 언론사 코드 추출 (첫 번째 부분)
                                    code = cluster_id.split(".")[0]
                                    
                                    # 뉴스 ID 저장
                                    actual_news_ids.append(cluster_id)
                                    
                                    # 언론사별 카운트 증가
                                    provider_counts[code] = provider_counts.get(code, 0) + 1
                            
                            logger.info(f"클러스터 ID 직접 처리 완료: {len(provider_counts)} 개 언론사 코드 추출")
                            
                            # provider_counts가 비어있는 경우에만 API 호출 (기존 로직)
                            if not provider_counts:
                                logger.info("언론사 코드 직접 추출 실패, API 호출 시도")
                                search_res = bigkinds_client.get_news_by_cluster_ids(cluster_ids[:100])
                                formatted = bigkinds_client.format_news_response(search_res)
                                for doc in formatted.get("documents", []):
                                    code = doc.get("provider_code")
                                    if not code:
                                        nid = doc.get("id") or doc.get("news_id")
                                        if nid and "." in nid:
                                            code = nid.split(".")[0]
                                    news_id = doc.get("id")
                                    
                                    if news_id:
                                        actual_news_ids.append(news_id)
                        except Exception as e:
                            logger.error(f"언론사 코드 추출 오류: {str(e)}", exc_info=True)
                            provider_counts = {}

                    # Fallback: 클러스터로 찾지 못한 경우 토픽명으로 키워드 검색
                    if not provider_counts:
                        try:
                            keyword = topic.get("topic", "") or topic.get("topic_keyword", "").split(",")[0] if topic.get("topic_keyword") else ""
                            if keyword:
                                # 최근 7일간 해당 키워드로 뉴스 검색 (datetime은 모듈 상단에서 import됨)
                                date_from = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
                                date_to = datetime.now().strftime("%Y-%m-%d")
                                
                                kw_res = bigkinds_client.search_news(
                                    query=keyword.strip(), 
                                    date_from=date_from,
                                    date_to=date_to,
                                    return_size=100
                                )
                                kw_docs = bigkinds_client.format_news_response(kw_res).get("documents", [])
                                for doc in kw_docs:
                                    code = doc.get("provider_code")
                                    if not code:
                                        nid = doc.get("id") or doc.get("news_id")
                                        if nid and "." in nid:
                                            code = nid.split(".")[0]
                                    news_id = doc.get("id")
                                    
                                    if news_id:
                                        actual_news_ids.append(news_id)
                        except Exception:
                            pass

                    # 집계가 전혀 없을 경우 count를 클러스터 길이나 actual_news_ids 길이로 보정
                    total_count = sum(provider_counts.values())
                    if total_count == 0:
                        total_count = len(actual_news_ids) if actual_news_ids else len(cluster_ids)

                    # provider breakdown 정렬 (기사 수 내림차순)
                    breakdown = [
                        {
                            "provider": PROVIDER_MAP.get(code, code),
                            "provider_code": code,
                            "count": cnt
                        }
                        for code, cnt in sorted(provider_counts.items(), key=lambda x: x[1], reverse=True)
                    ]
                    
                    # 디버깅을 위한 로깅 추가
                    if breakdown:
                        log_items = [f"{item['provider']}({item['provider_code']}): {item['count']}" for item in breakdown[:5]]
                        logger.info(f"이슈 '{topic.get('topic', '')}' 언론사별 기사 수: {', '.join(log_items)}")
                    else:
                        logger.warning(f"이슈 '{topic.get('topic', '')}' 언론사별 기사 수 매핑 실패")

                    today_issues.append({
                        "rank": topic.get("rank", idx + 1),
                        "title": topic.get("topic", ""),
                        "count": total_count,
                        "provider_breakdown": breakdown,
                        "related_news_ids": actual_news_ids[:50],  # 실제 뉴스 ID 목록 (최대 50개)
                        "cluster_ids": cluster_ids,  # 원본 클러스터 ID도 보관
                        "topic": topic.get("topic", ""),
                        "topic_rank": topic.get("rank", idx + 1),
                        "topic_keyword": topic.get("topic_keyword", ""),
                        "news_cluster": cluster_ids,
                    })
                logger.info(f"오늘의 이슈 {len(today_issues)}개 조회 성공")
            else:
                logger.warning(f"이슈 랭킹 포맷팅 실패: {formatted_issues.get('error')}")
                today_issues = []
        else:
            logger.warning(f"이슈 랭킹 API 오류: {issue_response.get('error', '알 수 없는 오류')}")
            today_issues = [{
                "rank": 1,
                "title": "최신 이슈를 불러오는 중입니다.",
                "count": 0,
                "related_news_ids": [],
                "cluster_ids": [],
                "topic": "",
                "topic_rank": 1,
                "topic_keyword": "",
                "news_cluster": []
            }]
    
    except Exception as e:
        logger.error(f"오늘의 이슈 조회 오류: {e}", exc_info=True)
        today_issues = [{
            "rank": 1,
            "title": "이슈 데이터 로딩 중 오류 발생",
            "count": 0,
            "related_news_ids": [],
            "cluster_ids": [],
            "topic": "",
            "topic_rank": 1,
            "topic_keyword": "",
            "news_cluster": []
        }]
    
    try:
        # 2. 인기 키워드 가져오기 (수정된 API 사용)
        logger.info("인기 키워드 요청 시작")
        keyword_response = bigkinds_client.get_popular_keywords(days=1, limit=10)
        
        if keyword_response.get("result") == 0:
            # 수정된 API에서 formatted_keywords 사용
            formatted_keywords = keyword_response.get("formatted_keywords", [])
            
            popular_keywords = [
                {
                    "rank": kw.get("rank", idx + 1),
                    "keyword": kw.get("keyword", ""),
                    "count": kw.get("count", 0),
                    "trend": kw.get("trend", "stable")
                }
                for idx, kw in enumerate(formatted_keywords[:10])  # 상위 10개만
            ]
            
            logger.info(f"인기 키워드 {len(popular_keywords)}개 조회 성공")
        else:
            logger.warning(f"키워드 랭킹 API 오류: {keyword_response.get('error', '알 수 없는 오류')}")
            popular_keywords = [{
                "rank": 1,
                "keyword": "키워드 데이터를 불러오는 중입니다.",
                "count": 0,
                "trend": "stable"
            }]
    
    except Exception as e:
        logger.error(f"인기 키워드 조회 오류: {e}", exc_info=True)
        popular_keywords = [{
            "rank": 1,
            "keyword": "키워드 데이터 로딩 중 오류 발생",
            "count": 0,
            "trend": "stable"
        }]
    
    return LatestNewsResponse(
        today_issues=today_issues,
        popular_keywords=popular_keywords,
        timestamp=datetime.now().isoformat()
    )

@router.post("/company")
async def get_company_news(
    request: CompanyNewsRequest,
    bigkinds_client: BigKindsClient = Depends(get_bigkinds_client)
):
    """특정 기업의 뉴스 가져오기
    
    기업명으로 뉴스를 검색하고 타임라인 형식으로 반환합니다.
    """
    logger = setup_logger("api.news.company")
    logger.info(f"기업 뉴스 요청: {request.company_name}")
    
    try:
        # 날짜 기본값 설정 (최근 30일)
        if not request.date_from:
            request.date_from = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not request.date_to:
            request.date_to = datetime.now().strftime("%Y-%m-%d")
        
        # BigKinds API로 기업 뉴스 타임라인 조회
        result = bigkinds_client.get_company_news_timeline(
            company_name=request.company_name,
            date_from=request.date_from,
            date_to=request.date_to,
            return_size=request.limit
        )
        
        if not result.get("success", False):
            raise HTTPException(status_code=404, detail="기업 뉴스를 찾을 수 없습니다")
        
        return {
            "company": request.company_name,
            "period": {
                "from": request.date_from,
                "to": request.date_to
            },
            "total_count": result.get("total_count", 0),
            "timeline": result.get("timeline", [])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"기업 뉴스 조회 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"기업 뉴스 조회 중 오류 발생: {str(e)}")

@router.post("/keyword")
async def get_keyword_news(
    request: KeywordNewsRequest,
    bigkinds_client: BigKindsClient = Depends(get_bigkinds_client)
):
    """키워드 기반 뉴스 검색 및 타임라인 구성
    
    키워드로 뉴스를 검색하고 타임라인 형식으로 반환합니다.
    """
    logger = setup_logger("api.news.keyword")
    logger.info(f"키워드 뉴스 요청: {request.keyword}")
    
    try:
        # 날짜 기본값 설정 (최근 30일)
        if not request.date_from:
            request.date_from = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not request.date_to:
            request.date_to = datetime.now().strftime("%Y-%m-%d")
        
        # BigKinds API로 키워드 뉴스 타임라인 조회
        result = bigkinds_client.get_keyword_news_timeline(
            keyword=request.keyword,
            date_from=request.date_from,
            date_to=request.date_to,
            return_size=request.limit
        )
        
        if not result.get("success", False):
            raise HTTPException(status_code=404, detail="키워드 관련 뉴스를 찾을 수 없습니다")
        
        return {
            "keyword": request.keyword,
            "period": {
                "from": request.date_from,
                "to": request.date_to
            },
            "total_count": result.get("total_count", 0),
            "timeline": result.get("timeline", [])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"키워드 뉴스 조회 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"키워드 뉴스 조회 중 오류 발생: {str(e)}")

@router.get("/detail/{news_id}")
async def get_news_detail(
    news_id: str = Path(..., description="뉴스 ID"),
    bigkinds_client: BigKindsClient = Depends(get_bigkinds_client)
):
    """뉴스 상세 정보 조회
    
    뉴스 ID로 상세 정보를 조회합니다.
    """
    logger = setup_logger("api.news.detail")
    logger.info(f"뉴스 상세 정보 요청: {news_id}")
    
    try:
        # 뉴스 ID로 상세 정보 조회
        result = bigkinds_client.get_news_detail(news_id)
        
        if not result.get("success", False):
            raise HTTPException(status_code=404, detail="뉴스를 찾을 수 없습니다")
        
        return {
            "success": True,
            "news": result.get("news"),
            "has_original_link": result.get("has_original_link", False),
            "metadata": {
                "retrieved_at": datetime.now().isoformat(),
                "source": "BigKinds API"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"뉴스 상세 정보 조회 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"뉴스 상세 정보 조회 중 오류 발생: {str(e)}")

@router.post("/ai-summary")
async def generate_ai_summary(
    request: AISummaryRequest,
    bigkinds_client: BigKindsClient = Depends(get_bigkinds_client)
):
    """선택된 뉴스 기사들의 AI 요약 생성
    
    이슈 중심, 인용 중심, 수치 중심 요약을 생성합니다.
    """
    logger = setup_logger("api.news.ai_summary")
    logger.info(f"AI 요약 요청: {request.summary_type} - {len(request.news_ids)}개 기사")
    
    try:
        # OpenAI API 키 설정
        openai.api_key = os.getenv("OPENAI_API_KEY")
        
        # 선택된 뉴스 기사들 가져오기
        # news_ids가 뉴스 클러스터 ID인 경우 cluster 메소드 사용
        if request.news_ids and any("cluster" in news_id.lower() for news_id in request.news_ids):
            search_result = bigkinds_client.get_news_by_cluster_ids(request.news_ids)
        else:
            search_result = bigkinds_client.get_news_by_ids(request.news_ids)
        
        formatted_result = bigkinds_client.format_news_response(search_result)
        articles = formatted_result.get("documents", [])
        
        if not articles:
            raise HTTPException(status_code=404, detail="선택된 뉴스를 찾을 수 없습니다")
        
        # 기사 내용 준비 (전체 content 사용)
        articles_text = ""
        for i, article in enumerate(articles, 1):
            title = article.get("title", "")
            # 전체 content 사용, summary는 대체용
            content = article.get("content", "") or article.get("summary", "")
            provider = article.get("provider", "")
            published_at = article.get("published_at", "")
            byline = article.get("byline", "")
            
            articles_text += f"[기사 {i}]\n"
            articles_text += f"제목: {title}\n"
            articles_text += f"언론사: {provider}\n"
            if byline:
                articles_text += f"기자: {byline}\n"
            articles_text += f"발행일: {published_at}\n"
            articles_text += f"내용: {content}\n\n"
        
        # 요약 타입에 따른 프롬프트 설정
        prompts = {
            "issue": {
                "system": "당신은 뉴스 분석 전문가입니다. 주어진 뉴스 기사들을 분석하여 핵심 이슈를 중심으로 요약해주세요.",
                "user": f"다음 {len(articles)}개의 뉴스 기사를 분석하여 이슈 중심으로 요약해주세요.\n\n{articles_text}\n\n요구사항:\n1. 핵심 이슈 3-5개를 명확히 파악\n2. 각 이슈의 중요도와 영향을 분석\n3. 향후 전망 제시\n4. JSON 형태로 응답: {{\"title\": \"이슈 중심 요약\", \"summary\": \"전체 요약\", \"key_points\": [\"포인트1\", \"포인트2\", ...], \"type\": \"issue\"}}"
            },
            "quote": {
                "system": "당신은 뉴스 분석 전문가입니다. 주어진 뉴스 기사들에서 주요 인용문과 발언을 중심으로 요약해주세요.",
                "user": f"다음 {len(articles)}개의 뉴스 기사에서 주요 인용문을 중심으로 요약해주세요.\n\n{articles_text}\n\n요구사항:\n1. 중요한 인용문과 발언자 식별\n2. 발언의 맥락과 의미 분석\n3. 각 발언의 영향력 평가\n4. JSON 형태로 응답: {{\"title\": \"인용 중심 요약\", \"summary\": \"전체 요약\", \"key_quotes\": [{{\"source\": \"발언자\", \"quote\": \"인용문\"}}, ...], \"type\": \"quote\"}}"
            },
            "data": {
                "system": "당신은 뉴스 분석 전문가입니다. 주어진 뉴스 기사들에서 수치와 데이터를 중심으로 요약해주세요.",
                "user": f"다음 {len(articles)}개의 뉴스 기사에서 중요한 수치와 데이터를 중심으로 요약해주세요.\n\n{articles_text}\n\n요구사항:\n1. 핵심 수치와 통계 데이터 추출\n2. 각 수치의 의미와 변화율 분석\n3. 비교 기준과 맥락 제시\n4. JSON 형태로 응답: {{\"title\": \"수치 중심 요약\", \"summary\": \"전체 요약\", \"key_data\": [{{\"metric\": \"지표명\", \"value\": \"수치\", \"context\": \"맥락\"}}, ...], \"type\": \"data\"}}"
            }
        }
        
        prompt_config = prompts.get(request.summary_type, prompts["issue"])
        
        # OpenAI GPT-4 Turbo로 요약 생성 (구버전 openai 패키지 방식)
        openai.api_key = os.getenv("OPENAI_API_KEY")
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": prompt_config["system"]},
                    {"role": "user", "content": prompt_config["user"]}
                ],
                max_tokens=2000,
                temperature=0.3
            )
            
            ai_summary = response.choices[0].message.content
        except Exception as e:
            logger.error(f"AI 요약 생성 오류: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"AI 요약 생성 중 오류 발생: {str(e)}")
        
        summary_result = {
            "title": f"{request.summary_type.title()} 중심 요약",
            "summary": ai_summary,
            "type": request.summary_type,
            "articles_analyzed": len(articles),
            "generated_at": datetime.now().isoformat(),
            "model_used": "gpt-4-turbo-preview"
        }
        
        return summary_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI 요약 생성 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"AI 요약 생성 중 오류 발생: {str(e)}")

@router.get("/watchlist/suggestions")
async def get_watchlist_suggestions():
    """관심 종목 추천 목록
    
    인기 있는 기업들의 목록을 반환합니다.
    """
    # 하드코딩된 추천 목록 (실제로는 DB나 분석 결과 기반)
    suggestions = [
        {"name": "삼성전자", "code": "005930", "category": "반도체"},
        {"name": "SK하이닉스", "code": "000660", "category": "반도체"},
        {"name": "LG에너지솔루션", "code": "373220", "category": "배터리"},
        {"name": "현대자동차", "code": "005380", "category": "자동차"},
        {"name": "네이버", "code": "035420", "category": "인터넷"},
        {"name": "카카오", "code": "035720", "category": "인터넷"},
        {"name": "셀트리온", "code": "068270", "category": "바이오"},
        {"name": "삼성바이오로직스", "code": "207940", "category": "바이오"}
    ]
    
    return {"suggestions": suggestions}

@router.get("/search")
async def search_news(
    keyword: str = Query(..., description="검색 키워드"),
    date_from: Optional[str] = Query(None, description="시작일 (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="종료일 (YYYY-MM-DD)"),
    limit: int = Query(30, description="결과 수", ge=1, le=100),
    bigkinds_client: BigKindsClient = Depends(get_bigkinds_client)
):
    """뉴스 검색 API (GET 방식)
    
    키워드로 뉴스를 검색하고 타임라인 형식으로 반환합니다.
    """
    logger = setup_logger("api.news.search")
    logger.info(f"뉴스 검색 요청: {keyword}")
    
    try:
        # 날짜 기본값 설정 (최근 30일)
        if not date_from:
            date_from = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not date_to:
            date_to = datetime.now().strftime("%Y-%m-%d")
        
        # BigKinds API로 키워드 뉴스 타임라인 조회
        result = bigkinds_client.get_keyword_news_timeline(
            keyword=keyword,
            date_from=date_from,
            date_to=date_to,
            return_size=limit
        )
        
        if not result.get("success", False):
            raise HTTPException(status_code=404, detail="키워드 관련 뉴스를 찾을 수 없습니다")
        
        return {
            "keyword": keyword,
            "period": {
                "from": date_from,
                "to": date_to
            },
            "total_count": result.get("total_count", 0),
            "timeline": result.get("timeline", [])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"뉴스 검색 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"뉴스 검색 중 오류 발생: {str(e)}")

@router.get("/company/{company_name}/summary")
async def get_company_news_summary(
    company_name: str = Path(..., description="기업명"),
    days: int = Query(7, description="최근 며칠간의 뉴스", ge=1, le=30),
    bigkinds_client: BigKindsClient = Depends(get_bigkinds_client)
):
    """관심 종목의 최근 뉴스 자동 요약
    
    기업의 최근 뉴스 5개를 자동으로 가져와서 GPT-4 Turbo로 요약합니다.
    """
    logger = setup_logger("api.news.company_summary")
    logger.info(f"기업 뉴스 자동 요약 요청: {company_name}")
    
    try:
        # OpenAI API 키 확인
        openai.api_key = os.getenv("OPENAI_API_KEY")
        if not openai.api_key:
            raise HTTPException(status_code=500, detail="AI 요약 서비스를 사용할 수 없습니다")
        
        # 기업의 최근 뉴스 가져오기
        news_data = bigkinds_client.get_company_news_for_summary(
            company_name=company_name,
            days=days,
            limit=5
        )
        
        if not news_data.get("success") or not news_data.get("articles"):
            raise HTTPException(status_code=404, detail=f"{company_name}의 최근 뉴스를 찾을 수 없습니다")
        
        articles = news_data.get("articles", [])
        
        # 기사 내용 준비
        articles_text = ""
        for i, article in enumerate(articles, 1):
            title = article.get("title", "")
            content = article.get("content", "") or article.get("summary", "")
            provider = article.get("provider", "")
            published_at = article.get("published_at", "")
            
            articles_text += f"[기사 {i}]\n"
            articles_text += f"제목: {title}\n"
            articles_text += f"언론사: {provider}\n"
            articles_text += f"발행일: {published_at}\n"
            articles_text += f"내용: {content}\n\n"
        
        # OpenAI GPT-4 Turbo로 뉴스 요약 생성 (구버전 openai 패키지 방식)
        openai.api_key = os.getenv("OPENAI_API_KEY")
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "당신은 경제 뉴스 전문 분석가입니다. 주어진 뉴스들을 종합하여 간결하고 통찰력 있는 요약을 제공해주세요."},
                    {"role": "user", "content": f"다음은 '{company_name}' 관련 최근 {days}일간의 뉴스입니다. 이를 바탕으로 해당 기업의 현재 상황과 주요 이슈를 300자 내외로 요약해주세요:\n\n{articles_text}"}
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            ai_summary = response.choices[0].message.content
        except Exception as e:
            logger.error(f"AI 요약 생성 오류: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"AI 요약 생성 중 오류 발생: {str(e)}")
        
        # 메타데이터 추가
        summary_result = {
            "company": company_name,
            "summary": ai_summary,
            "key_points": [],
            "sentiment": "neutral",
            "investment_implications": "추가 분석이 필요합니다.",
            "articles_analyzed": len(articles),
            "period": news_data.get("period"),
            "generated_at": datetime.now().isoformat(),
            "model_used": "gpt-4-turbo-preview",
            "source_articles": [
                {
                    "id": article.get("id"),
                    "title": article.get("title"),
                    "published_at": article.get("published_at"),
                    "provider": article.get("provider")
                }
                for article in articles
            ]
        }
        
        return summary_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"기업 뉴스 자동 요약 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"뉴스 요약 중 오류 발생: {str(e)}")

@router.get("/company/{company_name}/report/{report_type}")
async def get_company_report(
    company_name: str = Path(..., description="기업명"),
    report_type: str = Path(..., description="레포트 타입 (daily, weekly, monthly, quarterly, yearly)"),
    reference_date: Optional[str] = Query(None, description="기준 날짜 (YYYY-MM-DD), 없으면 오늘 날짜 사용"),
    bigkinds_client: BigKindsClient = Depends(get_bigkinds_client)
):
    """기업 기간별 뉴스 레포트 생성
    
    기업명과 레포트 타입에 따라 기간별 뉴스 레포트를 생성합니다.
    """
    logger = setup_logger("api.news.company_report")
    logger.info(f"기업 레포트 요청: {company_name}, 타입: {report_type}")
    
    valid_report_types = ["daily", "weekly", "monthly", "quarterly", "yearly"]
    if report_type not in valid_report_types:
        raise HTTPException(status_code=400, detail=f"지원하지 않는 레포트 타입입니다. 유효한 타입: {', '.join(valid_report_types)}")
    
    try:
        # OpenAI API 키 확인
        openai.api_key = os.getenv("OPENAI_API_KEY")
        if not openai.api_key:
            raise HTTPException(status_code=500, detail="AI 요약 서비스를 사용할 수 없습니다")
        
        # BigKinds API로 기업 뉴스 레포트 데이터 조회
        report_data = bigkinds_client.get_company_news_report(
            company_name=company_name,
            report_type=report_type,
            reference_date=reference_date
        )
        
        if not report_data.get("success", False):
            raise HTTPException(status_code=404, detail=f"기업 뉴스 레포트를 생성할 수 없습니다")
        
        articles = report_data.get("articles", [])
        if not articles:
            return {
                **report_data,
                "summary": f"{company_name}에 대한 {report_data.get('report_type_kr')} 레포트 기간 내 뉴스가 없습니다."
            }
        
        # 각 기사에 고유 ID 부여 (인용 참조용)
        for i, article in enumerate(articles):
            if not article.get("ref_id"):
                article["ref_id"] = f"ref{i+1}"
        
        # 기사 내용 준비 (전체 content 사용)
        articles_text = ""
        for i, article in enumerate(articles, 1):
            ref_id = article.get("ref_id", f"ref{i}")
            title = article.get("title", "")
            content = article.get("content", "") or article.get("summary", "")
            provider = article.get("provider", "")
            published_at = article.get("published_at", "")
            
            articles_text += f"[기사 {ref_id}]\n"
            articles_text += f"제목: {title}\n"
            articles_text += f"언론사: {provider}\n"
            articles_text += f"발행일: {published_at}\n"
            articles_text += f"내용: {content}\n\n"
        
        # 토큰 한계를 초과하는 경우 청킹 및 요약 처리
        max_tokens = 4000  # 청크당 최대 토큰 수 (대략적인 추정)
        chunks = []
        current_chunk = ""
        current_tokens = 0
        
        for i, article in enumerate(articles, 1):
            ref_id = article.get("ref_id", f"ref{i}")
            article_text = f"[기사 {ref_id}]\n"
            article_text += f"제목: {article.get('title', '')}\n"
            article_text += f"내용: {article.get('content', '') or article.get('summary', '')}\n\n"
            
            # 대략적으로 토큰 수 추정 (영어 기준 4자당 1토큰, 한글은 더 적을 수 있음)
            article_tokens = len(article_text) // 2
            
            if current_tokens + article_tokens > max_tokens:
                chunks.append(current_chunk)
                current_chunk = article_text
                current_tokens = article_tokens
            else:
                current_chunk += article_text
                current_tokens += article_tokens
        
        if current_chunk:
            chunks.append(current_chunk)
        
        # 기간에 따른 요약 프롬프트 설정
        period_from = report_data["period"]["from"]
        period_to = report_data["period"]["to"]
        
        prompts = {
            "daily": f"{period_to}일 하루 동안의 {company_name} 관련 주요 뉴스를 요약해주세요.",
            "weekly": f"{period_from}부터 {period_to}까지 일주일 간의 {company_name} 관련 주요 뉴스와 동향을 요약해주세요.",
            "monthly": f"{period_from}부터 {period_to}까지 한 달 간의 {company_name}의 주요 이슈, 동향 및 변화를 분석하여 요약해주세요.",
            "quarterly": f"{period_from}부터 {period_to}까지 3개월 간의 {company_name}의 분기별 성과, 주요 이슈 및 변화를 분석하여 요약해주세요.",
            "yearly": f"{period_from}부터 {period_to}까지 1년 간의 {company_name}의 주요 이슈, 성과, 시장 변화 및 전략적 방향을 종합적으로 분석하여 요약해주세요."
        }
        
        # 개선된 시스템 프롬프트 - 인용 정보 포함 요청
        system_prompt = """당신은 금융 및 경제 분야의 전문 애널리스트입니다. 주어진 뉴스 기사들을 분석하여 객관적이고 통찰력 있는 요약을 제공해주세요.

요약 시 다음 사항을 지켜주세요:
1. 중요한 사실이나 주장을 인용할 때 반드시 출처를 표시하세요. 예: [기사 ref1]
2. 직접 인용구는 큰따옴표로 표시하고 출처를 명시하세요. 예: "삼성전자는 신규 투자를 발표했다"[기사 ref2]
3. 요약은 주요 이슈, 동향, 영향으로 구분하여 작성하세요.
4. 요약 말미에 모든 참고 기사 목록을 포함하세요.

이 형식을 반드시 지켜 작성해주세요."""

        user_prompt = prompts.get(report_type, prompts["daily"]) + "\n\n각 기사의 중요한 내용을 인용할 때는 [기사 ref번호] 형태로 출처를 표시해주세요."
        
        # 청크가 여러 개인 경우 각각 요약 후 메타 요약
        final_summary = ""
        if len(chunks) > 1:
            chunk_summaries = []
            
            for i, chunk in enumerate(chunks, 1):
                try:
                    chunk_response = openai.ChatCompletion.create(
                        model="gpt-4-turbo-preview",
                        messages=[
                            {"role": "system", "content": "주어진 뉴스 기사들의 핵심 내용을 간결하게 요약해주세요. 중요한 내용을 인용할 때는 [기사 ref번호] 형태로 출처를 표시해주세요."},
                            {"role": "user", "content": f"다음은 {company_name} 관련 뉴스 기사입니다. 핵심 내용만 간결하게 요약해주세요. 중요한 내용을 인용할 때는 [기사 ref번호] 형태로 출처를 표시해주세요:\n\n{chunk}"}
                        ],
                        max_tokens=800,
                        temperature=0.3
                    )
                    
                    chunk_summary = chunk_response.choices[0].message.content
                    chunk_summaries.append(f"파트 {i} 요약: {chunk_summary}")
                except Exception as e:
                    logger.error(f"청크 {i} 요약 생성 오류: {e}", exc_info=True)
                    chunk_summaries.append(f"파트 {i} 요약: 요약 생성 실패")
            
            # 메타 요약 생성
            meta_summaries_text = "\n\n".join(chunk_summaries)
            try:
                meta_response = openai.ChatCompletion.create(
                    model="gpt-4-turbo-preview",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"{user_prompt}\n\n다음은 여러 부분으로 나눠진 요약입니다. 이를 통합하여 최종 요약을 작성해주세요. 각 부분에 있는 인용 정보([기사 ref번호])는 그대로 유지해주세요:\n\n{meta_summaries_text}"}
                    ],
                    max_tokens=1500,
                    temperature=0.3
                )
                
                final_summary = meta_response.choices[0].message.content
            except Exception as e:
                logger.error(f"메타 요약 생성 오류: {e}", exc_info=True)
                final_summary = "요약 생성 중 오류가 발생했습니다."
        else:
            # 단일 청크일 경우 바로 요약
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-4-turbo-preview",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"{user_prompt}\n\n다음은 {company_name} 관련 뉴스 기사입니다. 각 기사의 중요한 내용을 인용할 때는 [기사 ref번호] 형태로 출처를 표시해주세요:\n\n{articles_text}"}
                    ],
                    max_tokens=1500,
                    temperature=0.3
                )
                
                final_summary = response.choices[0].message.content
            except Exception as e:
                logger.error(f"요약 생성 오류: {e}", exc_info=True)
                final_summary = "요약 생성 중 오류가 발생했습니다."
        
        # 모든 기사 정보 포함 (content 필드를 제외하고 기본 정보만 포함)
        detailed_articles = []
        for article in articles:
            detailed_articles.append({
                "id": article.get("id", ""),
                "ref_id": article.get("ref_id", ""),
                "title": article.get("title", ""),
                "summary": article.get("summary", ""),
                "provider": article.get("provider", ""),
                "published_at": article.get("published_at", ""),
                "url": article.get("url", ""),
                "category": article.get("category", ""),
                "byline": article.get("byline", "")
            })
        
        # 최종 결과 반환
        return {
            **report_data,
            "summary": final_summary,
            "detailed_articles": detailed_articles,  # 모든 기사의 상세 정보 포함
            "generated_at": datetime.now().isoformat(),
            "model_used": "gpt-4-turbo-preview"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"기업 레포트 생성 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"기업 레포트 생성 중 오류 발생: {str(e)}")

@router.get("/watchlist")
async def get_watchlist_data(
    bigkinds_client: BigKindsClient = Depends(get_bigkinds_client)
):
    """관심 종목 전체 데이터 (종목 목록 + 각 종목별 최신 뉴스 수)
    
    프론트엔드에서 관심 종목 섹션을 구성할 때 필요한 모든 데이터를 제공합니다.
    """
    logger = setup_logger("api.news.watchlist")
    logger.info("관심 종목 데이터 요청")
    
    try:
        # 추천 종목 목록 (하드코딩된 주요 기업들)
        watchlist_companies = [
            {"name": "삼성전자", "code": "005930", "category": "반도체"},
            {"name": "SK하이닉스", "code": "000660", "category": "반도체"},
            {"name": "LG에너지솔루션", "code": "373220", "category": "배터리"},
            {"name": "현대자동차", "code": "005380", "category": "자동차"},
            {"name": "네이버", "code": "035420", "category": "인터넷"},
            {"name": "카카오", "code": "035720", "category": "인터넷"},
            {"name": "셀트리온", "code": "068270", "category": "바이오"},
            {"name": "삼성바이오로직스", "code": "207940", "category": "바이오"}
        ]
        
        # 각 기업별 최근 뉴스 수 확인 (간단한 검색으로)
        enhanced_watchlist = []
        for company in watchlist_companies:
            try:
                # 최근 7일간 뉴스 수 확인
                news_data = bigkinds_client.get_company_news_for_summary(
                    company_name=company["name"],
                    days=7,
                    limit=1  # 개수만 확인하므로 1개만
                )
                
                company_data = {
                    **company,
                    "recent_news_count": news_data.get("total_found", 0),
                    "has_recent_news": news_data.get("total_found", 0) > 0,
                    "last_updated": datetime.now().isoformat()
                }
                enhanced_watchlist.append(company_data)
                
            except Exception as e:
                logger.warning(f"기업 {company['name']} 뉴스 수 조회 실패: {e}")
                # 오류 시 기본값 설정
                company_data = {
                    **company,
                    "recent_news_count": 0,
                    "has_recent_news": False,
                    "last_updated": datetime.now().isoformat()
                }
                enhanced_watchlist.append(company_data)
        
        return {
            "success": True,
            "watchlist": enhanced_watchlist,
            "total_companies": len(enhanced_watchlist),
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"관심 종목 데이터 조회 오류: {e}", exc_info=True)
        # 오류 시 기본 데이터 반환
        return {
            "success": False,
            "watchlist": [
                {"name": "삼성전자", "code": "005930", "category": "반도체", "recent_news_count": 0, "has_recent_news": False},
                {"name": "SK하이닉스", "code": "000660", "category": "반도체", "recent_news_count": 0, "has_recent_news": False},
                {"name": "현대자동차", "code": "005380", "category": "자동차", "recent_news_count": 0, "has_recent_news": False}
            ],
            "total_companies": 3,
            "generated_at": datetime.now().isoformat(),
            "error": str(e)
        }

@router.get("/related-questions/{keyword}")
async def get_related_questions(
    keyword: str = Path(..., description="검색 키워드"),
    days: Optional[int] = Query(None, description="검색 기간(일)", ge=1, le=365),
    date_from: Optional[str] = Query(None, description="시작일(YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="종료일(YYYY-MM-DD)"),
    max_questions: int = Query(7, description="최대 질문 수", ge=1, le=20),
    bigkinds_client: BigKindsClient = Depends(get_bigkinds_client)
):
    """키워드 기반 연관 질문 생성
    
    키워드를 바탕으로 연관 검색어와 TopN 키워드를 분석하여 연관 질문을 생성합니다.
    """
    from api.utils.keywords_utils import (
        filter_keywords, score_keywords, create_boolean_queries, 
        keywords_to_questions, get_topic_sensitive_date_range
    )
    
    logger = setup_logger("api.news.related_questions")
    logger.info(f"연관 질문 요청: {keyword}")
    
    try:
        # 주제 기반 기간 설정
        topic_date_range = get_topic_sensitive_date_range(keyword)
        
        # 사용자 지정 기간 처리
        if date_from and date_to:
            period = {"date_from": date_from, "date_to": date_to}
        elif days:
            # 일수로 기간 지정
            date_to = datetime.now().strftime("%Y-%m-%d")
            date_from = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            period = {"date_from": date_from, "date_to": date_to}
        else:
            # 주제 기반 기간 사용
            period = {
                "date_from": topic_date_range["date_from"],
                "date_to": topic_date_range["date_to"]
            }
        
        # 1단계: 연관어와 TopN 키워드 가져오기
        related_keywords = bigkinds_client.get_related_keywords(
            keyword=keyword, 
            max_count=20,
            date_from=period["date_from"],
            date_to=period["date_to"]
        )
        
        topn_keywords = bigkinds_client.get_keyword_topn(
            keyword=keyword,
            date_from=period["date_from"],
            date_to=period["date_to"]
        )
        
        # 2단계: 키워드 필터링 및 점수화
        filtered_related = filter_keywords(related_keywords)
        filtered_topn = filter_keywords(topn_keywords)
        
        # 키워드가 너무 적으면 기간 확장 시도
        if len(filtered_related) < 5 or len(filtered_topn) < 5:
            # 기간 확장 (60일)
            extended_date_from = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")
            
            # 확장된 기간으로 다시 시도
            extended_related = bigkinds_client.get_related_keywords(
                keyword=keyword, 
                max_count=30,
                date_from=extended_date_from,
                date_to=period["date_to"]
            )
            
            extended_topn = bigkinds_client.get_keyword_topn(
                keyword=keyword,
                date_from=extended_date_from,
                date_to=period["date_to"],
                limit=30
            )
            
            # 확장된 결과로 업데이트 (기존 결과가 충분하면 유지)
            if len(filtered_related) < 5 and len(extended_related) > len(filtered_related):
                filtered_related = filter_keywords(extended_related)
                
            if len(filtered_topn) < 5 and len(extended_topn) > len(filtered_topn):
                filtered_topn = filter_keywords(extended_topn)
                
            # 기간 정보 업데이트
            period["date_from"] = extended_date_from
        
        # 키워드 점수 계산
        keyword_scores = score_keywords(keyword, filtered_related, filtered_topn)
        
        # 3단계: 점수 기반 상위 키워드 선택
        sorted_keywords = sorted(keyword_scores.keys(), key=lambda k: keyword_scores[k], reverse=True)
        top_keywords = sorted_keywords[:15]  # 상위 15개만 사용
        
        # 4단계: 쿼리 변형 생성
        query_variations = create_boolean_queries(keyword, top_keywords, max_variations=10)
        
        # 5단계: 질문 생성
        questions = keywords_to_questions(keyword, query_variations)
        
        # 최대 질문 수로 제한
        limited_questions = questions[:max_questions]
        
        return {
            "success": True,
            "keyword": keyword,
            "period": {
                "from": period["date_from"],
                "to": period["date_to"]
            },
            "detected_topic": topic_date_range.get("detected_topic"),
            "questions": limited_questions,
            "total_questions": len(limited_questions),
            "keywords": {
                "related": filtered_related[:10],
                "topn": filtered_topn[:10],
                "top_scored": top_keywords[:10]
            },
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"연관 질문 생성 오류: {e}", exc_info=True)
        return {
            "success": False,
            "keyword": keyword,
            "error": str(e),
            "questions": [],
            "generated_at": datetime.now().isoformat()
        }

@router.post("/search/news")
async def search_news_content(
    keyword: str = Query(..., description="검색 키워드"),
    date_from: Optional[str] = Query(None, description="시작일 (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="종료일 (YYYY-MM-DD)"),
    limit: int = Query(30, description="결과 수", ge=1, le=100),
    bigkinds_client: BigKindsClient = Depends(get_bigkinds_client)
):
    """뉴스 전체 내용 검색 API
    
    키워드로 뉴스를 검색하고 전체 내용(content)를 포함하여 반환합니다.
    """
    logger = setup_logger("api.news.search_content")
    logger.info(f"뉴스 내용 검색 요청: {keyword}")
    
    try:
        # 날짜 기본값 설정 (최근 30일)
        if not date_from:
            date_from = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not date_to:
            # until은 오늘 날짜 +1일로 설정 (오늘 데이터 포함 위해)
            date_to = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        # 필수 필드 설정 (content 포함)
        fields = [
            "news_id",
            "title",
            "content",  # 전체 내용 포함
            "published_at",
            "provider_name",
            "provider_code",
            "provider_link_page",
            "byline",
            "category",
            "images"
        ]
        
        # BigKinds API로 직접 뉴스 검색 (타임라인 아닌 원본 데이터)
        result = bigkinds_client.search_news(
            query=keyword,
            date_from=date_from,
            date_to=date_to,
            return_size=limit,
            fields=fields
        )
        
        # 응답 포맷팅
        formatted_result = bigkinds_client.format_news_response(result)
        
        if not formatted_result.get("success", False):
            raise HTTPException(status_code=404, detail="키워드 관련 뉴스를 찾을 수 없습니다")
        
        return {
            "keyword": keyword,
            "period": {
                "from": date_from,
                "to": date_to
            },
            "total_count": formatted_result.get("total_hits", 0),
            "articles": formatted_result.get("documents", [])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"뉴스 내용 검색 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"뉴스 내용 검색 중 오류 발생: {str(e)}")

@router.get("/search/news")
async def search_news_content_get(
    keyword: str = Query(..., description="검색 키워드"),
    date_from: Optional[str] = Query(None, description="시작일 (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="종료일 (YYYY-MM-DD)"),
    limit: int = Query(30, description="결과 수", ge=1, le=100),
    bigkinds_client: BigKindsClient = Depends(get_bigkinds_client)
):
    """뉴스 전체 내용 검색 API (GET 방식)
    
    키워드로 뉴스를 검색하고 전체 내용(content)를 포함하여 반환합니다.
    """
    logger = setup_logger("api.news.search_content_get")
    logger.info(f"뉴스 내용 검색 요청(GET): {keyword}")
    
    try:
        # 날짜 기본값 설정 (최근 30일)
        if not date_from:
            date_from = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not date_to:
            # until은 오늘 날짜 +1일로 설정 (오늘 데이터 포함 위해)
            date_to = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        # 필수 필드 설정 (content 포함)
        fields = [
            "news_id",
            "title",
            "content",  # 전체 내용 포함
            "published_at",
            "provider_name",
            "provider_code",
            "provider_link_page",
            "byline",
            "category",
            "images"
        ]
        
        # BigKinds API로 직접 뉴스 검색 (타임라인 아닌 원본 데이터)
        result = bigkinds_client.search_news(
            query=keyword,
            date_from=date_from,
            date_to=date_to,
            return_size=limit,
            fields=fields
        )
        
        # 응답 포맷팅
        formatted_result = bigkinds_client.format_news_response(result)
        
        if not formatted_result.get("success", False):
            raise HTTPException(status_code=404, detail="키워드 관련 뉴스를 찾을 수 없습니다")
        
        return {
            "keyword": keyword,
            "period": {
                "from": date_from,
                "to": date_to
            },
            "total_count": formatted_result.get("total_hits", 0),
            "articles": formatted_result.get("documents", [])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"뉴스 내용 검색 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"뉴스 내용 검색 중 오류 발생: {str(e)}")

@router.get("/search-by-question")
async def search_by_question(
    query: str = Query(..., description="검색 쿼리 (불리언 연산자 지원)"),
    question: Optional[str] = Query(None, description="원래 질문 (표시용)"),
    date_from: Optional[str] = Query(None, description="시작일 (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="종료일 (YYYY-MM-DD)"),
    limit: int = Query(10, description="결과 수", ge=1, le=100),
    bigkinds_client: BigKindsClient = Depends(get_bigkinds_client)
):
    """질문 기반 뉴스 검색
    
    연관 질문에서 생성된 불리언 쿼리로 뉴스를 검색합니다.
    """
    logger = setup_logger("api.news.search_by_question")
    logger.info(f"질문 검색 요청: '{query}', 질문: '{question}'")
    
    try:
        # 날짜 기본값 설정 (최근 30일)
        if not date_from:
            date_from = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not date_to:
            date_to = datetime.now().strftime("%Y-%m-%d")
        
        # 필수 필드 설정 (content 포함)
        fields = [
            "news_id",
            "title",
            "content",  # 전체 내용 포함
            "summary",
            "published_at",
            "provider_name",
            "provider_code",
            "provider_link_page",
            "byline",
            "category",
            "images"
        ]
        
        # BigKinds API로 뉴스 검색
        result = bigkinds_client.search_news(
            query=query,
            date_from=date_from,
            date_to=date_to,
            return_size=limit,
            fields=fields
        )
        
        # 응답 포맷팅
        formatted_result = bigkinds_client.format_news_response(result)
        
        if not formatted_result.get("success", False):
            raise HTTPException(status_code=404, detail="검색 결과를 찾을 수 없습니다")
        
        return {
            "success": True,
            "original_query": query,
            "question": question or "질문 정보 없음",
            "period": {
                "from": date_from,
                "to": date_to
            },
            "total_count": formatted_result.get("total_hits", 0),
            "articles": formatted_result.get("documents", [])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"질문 검색 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"질문 검색 중 오류 발생: {str(e)}")