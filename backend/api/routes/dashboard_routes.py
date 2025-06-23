"""
관심 종목 대시보드 API 라우터
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any

from backend.api.dependencies import get_bigkinds_client
from backend.services.news.dashboard_service import DashboardService
from backend.services.news.briefing_service import BriefingService
from backend.api.clients.bigkinds.client import BigKindsClient

router = APIRouter(
    prefix="/api/dashboard",
    tags=["Dashboard"]
)

# 서비스 의존성 주입
def get_dashboard_service(client: BigKindsClient = Depends(get_bigkinds_client)) -> DashboardService:
    briefing_service = BriefingService(client)
    return DashboardService(client, briefing_service)

@router.get("/company/{company_name}", response_model=Dict[str, Any])
async def get_company_dashboard(
    company_name: str,
    service: DashboardService = Depends(get_dashboard_service)
):
    """
    특정 기업에 대한 종합 대시보드 데이터를 반환합니다.
    """
    if not company_name:
        raise HTTPException(status_code=400, detail="기업명은 필수입니다.")

    try:
        dashboard_data = await service.get_full_dashboard(company_name)
        return dashboard_data
    except Exception as e:
        # 에러 로깅을 추가하면 더 좋습니다.
        raise HTTPException(status_code=500, detail=f"대시보드 데이터 생성 중 오류 발생: {str(e)}") 