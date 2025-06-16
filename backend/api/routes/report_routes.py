"""
레포트 생성 관련 API 라우트

기업별 분석 레포트 생성 및 관리 API 엔드포인트를 정의합니다.
"""

import os
import json
import asyncio
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from typing import Dict, Any
from datetime import datetime, timedelta
import sys
from pathlib import Path

# 프로젝트 루트 디렉토리 설정
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.api.models.report_models import (
    ReportRequest, CompanyReport, ReportStreamData, ReportPeriodType
)
from backend.services.report_generator import ReportGenerator
from backend.api.clients.bigkinds import BigKindsClient
from backend.utils.logger import setup_logger

# API 라우터 생성
router = APIRouter(prefix="/api/reports", tags=["레포트"])

# 로거 설정
logger = setup_logger("api.reports")

def get_report_generator():
    """레포트 생성기 인스턴스 가져오기"""
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if not openai_api_key:
        raise HTTPException(status_code=500, detail="OpenAI API 키가 설정되지 않았습니다.")
    
    bigkinds_client = BigKindsClient()
    return ReportGenerator(openai_api_key, bigkinds_client)

@router.post("/company/generate", response_model=CompanyReport)
async def generate_company_report(
    request: ReportRequest,
    generator: ReportGenerator = Depends(get_report_generator)
):
    """
    기업 분석 레포트 생성 (동기식)
    
    Args:
        request: 레포트 생성 요청
        
    Returns:
        CompanyReport: 생성된 레포트
    """
    logger.info(f"레포트 생성 요청: {request.company_name} ({request.period_type.value})")
    
    try:
        # 날짜 유효성 검사
        _validate_date_range(request.date_from, request.date_to, request.period_type)
        
        # 스트리밍 생성기를 통해 최종 결과만 반환
        final_result = None
        async for data in generator.generate_report_stream(request):
            if data.type == "complete" and data.result:
                final_result = data.result
                break
            elif data.type == "error":
                raise HTTPException(status_code=500, detail=data.error)
        
        if not final_result:
            raise HTTPException(status_code=500, detail="레포트 생성에 실패했습니다.")
        
        logger.info(f"레포트 생성 완료: {request.company_name}")
        return final_result
        
    except ValueError as e:
        logger.warning(f"잘못된 요청: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"레포트 생성 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"레포트 생성 중 오류가 발생했습니다: {str(e)}")

@router.post("/company/generate-stream")
async def generate_company_report_stream(
    request: ReportRequest,
    generator: ReportGenerator = Depends(get_report_generator)
):
    """
    기업 분석 레포트 생성 (스트리밍)
    
    Args:
        request: 레포트 생성 요청
        
    Returns:
        StreamingResponse: 실시간 생성 진행 상황
    """
    logger.info(f"스트리밍 레포트 생성 요청: {request.company_name}")
    
    try:
        # 날짜 유효성 검사
        _validate_date_range(request.date_from, request.date_to, request.period_type)
        
        async def stream_generator():
            """스트리밍 응답 생성기"""
            try:
                async for data in generator.generate_report_stream(request):
                    # SSE 형식으로 데이터 전송
                    json_data = data.model_dump_json()
                    yield f"data: {json_data}\\n\\n"
                    
                    # 완료 또는 오류 시 연결 종료
                    if data.type in ["complete", "error"]:
                        break
                        
            except Exception as e:
                error_data = ReportStreamData(
                    type="error",
                    error=f"스트리밍 중 오류 발생: {str(e)}"
                )
                yield f"data: {error_data.model_dump_json()}\\n\\n"
        
        return StreamingResponse(
            stream_generator(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # Nginx 버퍼링 비활성화
            }
        )
        
    except ValueError as e:
        logger.warning(f"잘못된 스트리밍 요청: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"스트리밍 레포트 생성 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"스트리밍 레포트 생성 중 오류가 발생했습니다: {str(e)}")

@router.get("/templates")
async def get_report_templates():
    """
    사용 가능한 레포트 템플릿 목록 조회
    
    Returns:
        Dict: 템플릿 정보들
    """
    from backend.api.models.report_models import REPORT_TEMPLATES
    
    templates = {}
    for period_type, template in REPORT_TEMPLATES.items():
        templates[period_type.value] = {
            "name": template.name,
            "description": template.description,
            "sections": template.sections
        }
    
    return {
        "templates": templates,
        "available_periods": [period.value for period in ReportPeriodType]
    }

@router.get("/periods")
async def get_available_periods():
    """
    사용 가능한 레포트 기간 타입 조회
    
    Returns:
        Dict: 기간 타입 정보
    """
    periods = {}
    
    for period_type in ReportPeriodType:
        periods[period_type.value] = {
            "name": period_type.value.title(),
            "description": _get_period_description(period_type),
            "recommended_date_range": _get_recommended_date_range(period_type)
        }
    
    return {"periods": periods}

@router.post("/company/validate")
async def validate_report_request(request: ReportRequest):
    """
    레포트 생성 요청 유효성 검사
    
    Args:
        request: 레포트 생성 요청
        
    Returns:
        Dict: 유효성 검사 결과
    """
    try:
        # 날짜 유효성 검사
        _validate_date_range(request.date_from, request.date_to, request.period_type)
        
        # 기업명 유효성 검사
        if len(request.company_name.strip()) < 2:
            raise ValueError("기업명은 최소 2글자 이상이어야 합니다.")
        
        # 추천 기간 확인
        recommended_range = _get_recommended_date_range(request.period_type)
        
        return {
            "valid": True,
            "message": "유효한 요청입니다.",
            "recommended_date_range": recommended_range,
            "estimated_articles": "정확한 수치는 생성 시 확인됩니다.",
            "estimated_time_minutes": _get_estimated_time(request.period_type)
        }
        
    except ValueError as e:
        return {
            "valid": False,
            "message": str(e),
            "recommended_date_range": _get_recommended_date_range(request.period_type)
        }

def _validate_date_range(date_from: str, date_to: str, period_type: ReportPeriodType):
    """날짜 범위 유효성 검사"""
    try:
        start_date = datetime.strptime(date_from, "%Y-%m-%d")
        end_date = datetime.strptime(date_to, "%Y-%m-%d")
    except ValueError:
        raise ValueError("날짜 형식이 올바르지 않습니다. YYYY-MM-DD 형식을 사용하세요.")
    
    if start_date >= end_date:
        raise ValueError("시작일은 종료일보다 이전이어야 합니다.")
    
    # 기간 타입별 권장 범위 검사
    date_diff = (end_date - start_date).days
    
    if period_type == ReportPeriodType.DAILY and date_diff > 1:
        raise ValueError("일간 레포트는 1일 범위로 설정해주세요.")
    elif period_type == ReportPeriodType.WEEKLY and (date_diff < 7 or date_diff > 14):
        raise ValueError("주간 레포트는 7-14일 범위로 설정해주세요.")
    elif period_type == ReportPeriodType.MONTHLY and (date_diff < 28 or date_diff > 35):
        raise ValueError("월간 레포트는 28-35일 범위로 설정해주세요.")
    elif period_type == ReportPeriodType.QUARTERLY and (date_diff < 85 or date_diff > 95):
        raise ValueError("분기별 레포트는 85-95일 범위(약 3개월)로 설정해주세요.")
    elif period_type == ReportPeriodType.YEARLY and (date_diff < 360 or date_diff > 370):
        raise ValueError("연간 레포트는 360-370일 범위(약 1년)로 설정해주세요.")
    
    # 과거 데이터 범위 확인 (너무 과거 데이터는 제한)
    if start_date < datetime.now() - timedelta(days=365 * 3):
        raise ValueError("3년 이전의 데이터는 분석할 수 없습니다.")

def _get_period_description(period_type: ReportPeriodType) -> str:
    """기간 타입별 설명 반환"""
    descriptions = {
        ReportPeriodType.DAILY: "하루 동안의 주요 뉴스와 이슈를 분석합니다.",
        ReportPeriodType.WEEKLY: "일주일 동안의 기업 동향을 종합 분석합니다.",
        ReportPeriodType.MONTHLY: "한 달 동안의 기업 활동을 상세히 분석합니다.",
        ReportPeriodType.QUARTERLY: "분기 동안의 전략과 성과를 심층 분석합니다.",
        ReportPeriodType.YEARLY: "연간 기업의 모든 활동을 종합적으로 분석합니다."
    }
    return descriptions.get(period_type, "기간별 분석 레포트")

def _get_recommended_date_range(period_type: ReportPeriodType) -> Dict[str, str]:
    """기간 타입별 권장 날짜 범위 반환"""
    today = datetime.now()
    
    if period_type == ReportPeriodType.DAILY:
        start = today - timedelta(days=1)
        end = today - timedelta(days=1)
    elif period_type == ReportPeriodType.WEEKLY:
        start = today - timedelta(days=7)
        end = today
    elif period_type == ReportPeriodType.MONTHLY:
        start = today - timedelta(days=30)
        end = today
    elif period_type == ReportPeriodType.QUARTERLY:
        start = today - timedelta(days=90)
        end = today
    else:  # YEARLY
        start = today - timedelta(days=365)
        end = today
    
    return {
        "from": start.strftime("%Y-%m-%d"),
        "to": end.strftime("%Y-%m-%d")
    }

def _get_estimated_time(period_type: ReportPeriodType) -> int:
    """예상 생성 시간(분) 반환"""
    time_estimates = {
        ReportPeriodType.DAILY: 2,
        ReportPeriodType.WEEKLY: 3,
        ReportPeriodType.MONTHLY: 5,
        ReportPeriodType.QUARTERLY: 8,
        ReportPeriodType.YEARLY: 12
    }
    return time_estimates.get(period_type, 5)