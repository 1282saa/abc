"""
AI 뉴스 컨시어지 (브리핑) API 라우터
"""
from fastapi import APIRouter, Depends, HTTPException, Body
from typing import Dict, Any

from backend.api.dependencies import get_bigkinds_client
from backend.services.news.briefing_service import BriefingService
from backend.api.clients.bigkinds.client import BigKindsClient

router = APIRouter(
    prefix="/api/briefing",
    tags=["AI Briefing"]
)

# 서비스 인스턴스 생성 (의존성 주입)
def get_briefing_service(client: BigKindsClient = Depends(get_bigkinds_client)) -> BriefingService:
    return BriefingService(client)

@router.post("/question", response_model=Dict[str, Any])
async def get_briefing_for_question(
    payload: Dict[str, Any] = Body(..., example={"question": "HBM 시장에서 삼성전자와 SK하이닉스의 경쟁력은?"}),
    service: BriefingService = Depends(get_briefing_service)
):
    """
    사용자의 자연어 질문에 대해 AI가 생성한 뉴스 브리핑을 반환합니다.
    """
    question = payload.get("question")
    if not question:
        raise HTTPException(status_code=400, detail="'question' 필드는 필수입니다.")

    try:
        briefing_data = await service.generate_briefing_for_question(question)
        return briefing_data
    except Exception as e:
        raise HTTPException(status_code=500, detail="브리핑 생성 중 오류 발생: {}".format(str(e)))

@router.post("/articles", response_model=Dict[str, Any])
async def search_articles(
    payload: Dict[str, Any] = Body(..., example={
        "query": "네이버 AI", 
        "page": 0, 
        "size": 10
    }),
    client: BigKindsClient = Depends(get_bigkinds_client)
):
    """
    키워드로 기사 검색 (무한 스크롤용)
    """
    query = payload.get("query")
    page = payload.get("page", 0)
    size = payload.get("size", 10)
    
    if not query:
        raise HTTPException(status_code=400, detail="'query' 필드는 필수입니다.")

    try:
        # 페이징 계산
        return_from = page * size
        
        # 기사 검색
        search_result = client.search_news_with_fallback(
            keyword=query,
            return_from=return_from,
            return_size=size,
            sort=[{"date": "desc"}, {"_score": "desc"}] # 최신순 우선 + 정확도
        )
        
        # 응답 포맷팅
        from backend.api.clients.bigkinds.formatters import format_news_response
        formatted_response = format_news_response(search_result)
        
        return {
            "success": True,
            "query": query,
            "page": page,
            "size": size,
            "total_hits": formatted_response.get("total_hits", 0),
            "documents": formatted_response.get("documents", []),
            "has_more": len(formatted_response.get("documents", [])) == size
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="기사 검색 중 오류 발생: {}".format(str(e))) 