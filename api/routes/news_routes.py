from typing import Optional
from fastapi import APIRouter, Query, HTTPException
from datetime import datetime, timedelta
from api.clients.bigkinds_client import BigKindsClient
from api.utils.logger import setup_logger

router = APIRouter()

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