"""
뉴스 관련 API 라우트

최신 뉴스, 인기 키워드, 이슈 등 뉴스 관련 API 엔드포인트를 정의합니다.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime, date, timedelta
import sys
from pathlib import Path

# 프로젝트 루트 디렉토리 찾기
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.utils.logger import setup_logger
from backend.api.clients.bigkinds_client import BigKindsClient
import openai
import os

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

class AISummaryRequest(BaseModel):
    """AI 요약 요청 모델"""
    news_ids: List[str] = Field(..., description="요약할 뉴스 ID 리스트 (최대 5개)", max_items=5)
    summary_type: str = Field(..., description="요약 유형", pattern="^(issue|quote|data)$")

# 엔드포인트 정의
@router.get("/latest", response_model=LatestNewsResponse)
async def get_latest_news(
    bigkinds_client: BigKindsClient = Depends(get_bigkinds_client)
):
    """최신 뉴스 정보 가져오기
    
    오늘의 이슈(빅카인즈 이슈 랭킹)와 인기 키워드를 반환합니다.
    """
    logger = setup_logger("api.news.latest")
    logger.info("최신 뉴스 정보 요청")
    
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        # 오늘의 이슈 가져오기 (이슈 랭킹 API 사용)
        today_issues_result = bigkinds_client.get_issue_ranking(today)
        formatted_issues = bigkinds_client.format_issue_ranking_response(today_issues_result)
        
        # 인기 키워드 가져오기 (오늘의 카테고리 키워드 API 사용)
        popular_keywords_result = bigkinds_client.get_today_category_keyword()
        
        # topics 구조로 데이터 추출
        today_issues = formatted_issues.get("topics", [])[:10] if formatted_issues.get("success") else []
        
        # 인기 키워드 데이터 추출
        popular_keywords = popular_keywords_result.get("return_object", {}).get("documents", [])[:10]
        
        return LatestNewsResponse(
            today_issues=today_issues,
            popular_keywords=popular_keywords,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"최신 뉴스 조회 오류: {e}", exc_info=True)
        # API 실패 시 더미 데이터 반환 (오늘의 이슈로 통합)
        return LatestNewsResponse(
            today_issues=[
                {
                    "topic_id": "topic_001",
                    "topic_name": "반도체 수출 증가",
                    "rank": 1,
                    "score": 95.2,
                    "news_cluster": ["news_cluster_001", "news_cluster_002"]
                },
                {
                    "topic_id": "topic_002",
                    "topic_name": "AI 스타트업 투자",
                    "rank": 2,
                    "score": 89.7,
                    "news_cluster": ["news_cluster_003", "news_cluster_004"]
                },
                {
                    "topic_id": "topic_003",
                    "topic_name": "디지털 금융 혁신",
                    "rank": 3,
                    "score": 82.5,
                    "news_cluster": ["news_cluster_005", "news_cluster_006"]
                },
                {
                    "topic_id": "topic_004",
                    "topic_name": "카보네이트리티 정책",
                    "rank": 4,
                    "score": 78.9,
                    "news_cluster": ["news_cluster_007"]
                },
                {
                    "topic_id": "topic_005",
                    "topic_name": "K-콘텐츠 해외진출",
                    "rank": 5,
                    "score": 75.3,
                    "news_cluster": ["news_cluster_008", "news_cluster_009"]
                }
            ],
            popular_keywords=[
                {"keyword": "생성 AI", "rank": 1, "score": 95, "category": "기술"},
                {"keyword": "ESG 경영", "rank": 2, "score": 92, "category": "경영"},
                {"keyword": "메타버스", "rank": 3, "score": 88, "category": "기술"},
                {"keyword": "탄소중립", "rank": 4, "score": 85, "category": "환경"},
                {"keyword": "디지털전환", "rank": 5, "score": 82, "category": "산업"},
                {"keyword": "비대면 금융", "rank": 6, "score": 79, "category": "금융"},
                {"keyword": "자동차 전동화", "rank": 7, "score": 76, "category": "자동차"}
            ],
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
        
        # BigKinds API로 기업 뉴스 검색
        result = bigkinds_client.get_company_news(
            company_name=request.company_name,
            date_from=request.date_from,
            date_to=request.date_to,
            return_size=request.limit
        )
        
        # API 응답 형식 변환
        formatted_result = bigkinds_client.format_news_response(result)
        documents = formatted_result.get("documents", [])
        
        # 날짜별로 그룹화
        timeline = {}
        for doc in documents:
            # published_at에서 날짜 부분만 추출
            published_at = doc.get("published_at", "")
            date_str = published_at[:10] if published_at else ""  # YYYY-MM-DD 형식
            
            if date_str and date_str not in timeline:
                timeline[date_str] = []
            
            if date_str:
                timeline[date_str].append({
                    "id": doc.get("id"),
                    "title": doc.get("title"),
                    "summary": doc.get("summary"),
                    "provider": doc.get("provider"),
                    "url": doc.get("url"),
                    "category": doc.get("category"),
                    "byline": doc.get("byline"),
                    "images": doc.get("images", [])
                })
        
        # 타임라인을 리스트로 변환 (최신 날짜 순)
        timeline_list = [
            {
                "date": date_str,
                "articles": articles,
                "count": len(articles)
            }
            for date_str, articles in sorted(timeline.items(), reverse=True)
        ]
        
        return {
            "company": request.company_name,
            "period": {
                "from": request.date_from,
                "to": request.date_to
            },
            "total_count": len(documents),
            "timeline": timeline_list
        }
        
    except Exception as e:
        logger.error(f"기업 뉴스 조회 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"기업 뉴스 조회 중 오류 발생: {str(e)}")

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
        
        # GPT-4 Turbo로 요약 생성
        response = openai.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": prompt_config["system"]},
                {"role": "user", "content": prompt_config["user"]}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        
        # 응답 파싱
        import json
        try:
            summary_result = json.loads(response.choices[0].message.content)
        except json.JSONDecodeError:
            # JSON 파싱 실패 시 기본 응답
            summary_result = {
                "title": f"{request.summary_type.title()} 중심 요약",
                "summary": response.choices[0].message.content,
                "type": request.summary_type
            }
        
        summary_result["articles_analyzed"] = len(articles)
        summary_result["generated_at"] = datetime.now().isoformat()
        summary_result["model_used"] = "gpt-4-turbo-preview"
        
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