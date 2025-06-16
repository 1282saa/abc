"""
기간별 자동 레포트 생성 API 라우트

일간, 주간, 월간, 분기별, 연간 뉴스 분석 레포트 생성 API를 제공합니다.
"""

import os
import json
import asyncio
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta, date
import sys
from pathlib import Path

# 프로젝트 루트 디렉토리 설정
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.api.models.period_report_models import (
    AutoReportRequest, PeriodReport, PeriodReportType, ReportGenerationProgress,
    PERIOD_REPORT_TEMPLATES
)
from backend.services.period_report_generator import PeriodReportGenerator
from backend.api.clients.bigkinds import BigKindsClient
from backend.utils.logger import setup_logger

# API 라우터 생성
router = APIRouter(prefix="/api/period-reports", tags=["기간별 레포트"])

# 로거 설정
logger = setup_logger("api.period_reports")

def get_period_report_generator():
    """기간별 레포트 생성기 인스턴스 가져오기"""
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if not openai_api_key:
        raise HTTPException(status_code=500, detail="OpenAI API 키가 설정되지 않았습니다.")
    
    bigkinds_client = BigKindsClient()
    return PeriodReportGenerator(openai_api_key, bigkinds_client)

@router.post("/generate", response_model=PeriodReport)
async def generate_period_report(
    request: AutoReportRequest,
    generator: PeriodReportGenerator = Depends(get_period_report_generator)
):
    """
    기간별 자동 레포트 생성 (동기식)
    
    Args:
        request: 자동 레포트 생성 요청
        
    Returns:
        PeriodReport: 생성된 기간별 레포트
    """
    logger.info(f"기간별 레포트 생성 요청: {request.report_type.value}")
    
    try:
        # 스트리밍 생성기를 통해 최종 결과만 반환
        final_result = None
        async for progress in generator.generate_period_report_stream(request):
            if progress.stage == "result" and hasattr(progress, 'result'):
                final_result = progress.result
                break
            elif progress.stage == "error":
                raise HTTPException(status_code=500, detail=progress.message)
        
        if not final_result:
            raise HTTPException(status_code=500, detail="레포트 생성에 실패했습니다.")
        
        logger.info(f"기간별 레포트 생성 완료: {request.report_type.value}")
        return final_result
        
    except ValueError as e:
        logger.warning(f"잘못된 요청: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"기간별 레포트 생성 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"레포트 생성 중 오류가 발생했습니다: {str(e)}")

@router.post("/generate-stream")
async def generate_period_report_stream(
    request: AutoReportRequest,
    generator: PeriodReportGenerator = Depends(get_period_report_generator)
):
    """
    기간별 자동 레포트 생성 (스트리밍)
    
    Args:
        request: 자동 레포트 생성 요청
        
    Returns:
        StreamingResponse: 실시간 생성 진행 상황
    """
    logger.info(f"스트리밍 기간별 레포트 생성 요청: {request.report_type.value}")
    
    try:
        async def stream_generator():
            """스트리밍 응답 생성기"""
            try:
                async for progress in generator.generate_period_report_stream(request):
                    # SSE 형식으로 데이터 전송
                    if hasattr(progress, 'result'):
                        # result 필드가 있는 경우 별도 처리
                        progress_dict = progress.__dict__.copy()
                        result = progress_dict.pop('result')
                        
                        # 진행상황 먼저 전송
                        yield f"data: {json.dumps(progress_dict)}\\n\\n"
                        
                        # 결과 별도 전송
                        result_data = {
                            "stage": "final_result",
                            "progress": 100,
                            "message": "완료",
                            "result": result.model_dump() if hasattr(result, 'model_dump') else result
                        }
                        yield f"data: {json.dumps(result_data)}\\n\\n"
                    else:
                        # 일반 진행상황
                        json_data = progress.model_dump_json()
                        yield f"data: {json_data}\\n\\n"
                    
                    # 완료 또는 오류 시 연결 종료
                    if progress.stage in ["completed", "error", "result"]:
                        break
                        
            except Exception as e:
                error_progress = ReportGenerationProgress(
                    stage="error",
                    progress=0,
                    message=f"스트리밍 중 오류 발생: {str(e)}",
                    current_task="오류 처리"
                )
                yield f"data: {error_progress.model_dump_json()}\\n\\n"
        
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
        logger.error(f"스트리밍 기간별 레포트 생성 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"스트리밍 레포트 생성 중 오류가 발생했습니다: {str(e)}")

@router.get("/templates")
async def get_period_report_templates():
    """
    사용 가능한 기간별 레포트 템플릿 목록 조회
    
    Returns:
        Dict: 템플릿 정보들
    """
    templates = {}
    for period_type, template_data in PERIOD_REPORT_TEMPLATES.items():
        templates[period_type.value] = template_data
    
    return {
        "templates": templates,
        "available_periods": [period.value for period in PeriodReportType],
        "default_categories": ["정치", "경제", "사회", "생활/문화", "IT/과학", "국제", "스포츠"]
    }

@router.get("/quick-generate/{report_type}")
async def quick_generate_period_report(
    report_type: PeriodReportType,
    categories: Optional[str] = Query(default="정치,경제,사회", description="분석할 카테고리 (콤마로 구분)"),
    max_articles: Optional[int] = Query(default=100, description="최대 기사 수", ge=10, le=500),
    generator: PeriodReportGenerator = Depends(get_period_report_generator)
):
    """
    빠른 기간별 레포트 생성
    
    Args:
        report_type: 레포트 타입 (daily, weekly, monthly, quarterly, yearly)
        categories: 분석할 카테고리들 (콤마로 구분)
        max_articles: 분석할 최대 기사 수
        
    Returns:
        PeriodReport: 생성된 레포트
    """
    logger.info(f"빠른 기간별 레포트 생성: {report_type.value}")
    
    try:
        # 카테고리 파싱
        category_list = [cat.strip() for cat in categories.split(",") if cat.strip()]
        
        # 자동 요청 생성
        request = AutoReportRequest(
            report_type=report_type,
            categories=category_list,
            max_articles=max_articles,
            include_sentiment=True,
            include_keywords=True
        )
        
        # 레포트 생성
        final_result = None
        async for progress in generator.generate_period_report_stream(request):
            if progress.stage == "result" and hasattr(progress, 'result'):
                final_result = progress.result
                break
            elif progress.stage == "error":
                raise HTTPException(status_code=500, detail=progress.message)
        
        if not final_result:
            raise HTTPException(status_code=500, detail="레포트 생성에 실패했습니다.")
        
        return final_result
        
    except Exception as e:
        logger.error(f"빠른 레포트 생성 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/period-info/{report_type}")
async def get_period_info(report_type: PeriodReportType):
    """
    특정 레포트 타입의 기간 정보 조회
    
    Args:
        report_type: 레포트 타입
        
    Returns:
        Dict: 기간 정보
    """
    today = date.today()
    
    if report_type == PeriodReportType.DAILY:
        target_date = today - timedelta(days=1)
        period_start = period_end = target_date.strftime("%Y-%m-%d")
        description = "어제 하루 동안의 뉴스"
        
    elif report_type == PeriodReportType.WEEKLY:
        days_since_monday = today.weekday()
        last_monday = today - timedelta(days=days_since_monday + 7)
        last_sunday = last_monday + timedelta(days=6)
        period_start = last_monday.strftime("%Y-%m-%d")
        period_end = last_sunday.strftime("%Y-%m-%d")
        description = "지난 주 (월~일) 동안의 뉴스"
        
    elif report_type == PeriodReportType.MONTHLY:
        if today.month == 1:
            last_month = today.replace(year=today.year - 1, month=12, day=1)
        else:
            last_month = today.replace(month=today.month - 1, day=1)
        
        if last_month.month == 12:
            next_month = last_month.replace(year=last_month.year + 1, month=1, day=1)
        else:
            next_month = last_month.replace(month=last_month.month + 1, day=1)
        last_day = next_month - timedelta(days=1)
        
        period_start = last_month.strftime("%Y-%m-%d")
        period_end = last_day.strftime("%Y-%m-%d")
        description = "지난 달 전체 기간의 뉴스"
        
    elif report_type == PeriodReportType.QUARTERLY:
        current_quarter = (today.month - 1) // 3 + 1
        if current_quarter == 1:
            period_start = today.replace(year=today.year - 1, month=10, day=1).strftime("%Y-%m-%d")
            period_end = today.replace(year=today.year - 1, month=12, day=31).strftime("%Y-%m-%d")
        else:
            start_month = (current_quarter - 2) * 3 + 1
            period_start = today.replace(month=start_month, day=1).strftime("%Y-%m-%d")
            if start_month + 2 == 12:
                period_end = today.replace(month=12, day=31).strftime("%Y-%m-%d")
            else:
                next_quarter_start = today.replace(month=start_month + 3, day=1)
                period_end = (next_quarter_start - timedelta(days=1)).strftime("%Y-%m-%d")
        description = "지난 분기 (3개월) 동안의 뉴스"
        
    else:  # YEARLY
        period_start = today.replace(year=today.year - 1, month=1, day=1).strftime("%Y-%m-%d")
        period_end = today.replace(year=today.year - 1, month=12, day=31).strftime("%Y-%m-%d")
        description = "작년 전체 기간의 뉴스"
    
    template = PERIOD_REPORT_TEMPLATES[report_type]
    
    return {
        "report_type": report_type.value,
        "period_start": period_start,
        "period_end": period_end,
        "description": description,
        "template": template,
        "estimated_articles": template["max_articles"],
        "estimated_time_minutes": {
            "daily": 3,
            "weekly": 5,
            "monthly": 8,
            "quarterly": 12,
            "yearly": 20
        }.get(report_type.value, 5)
    }

@router.get("/categories")
async def get_available_categories():
    """
    사용 가능한 뉴스 카테고리 목록 조회
    
    Returns:
        Dict: 카테고리 정보
    """
    categories = {
        "정치": {
            "description": "정치, 정부, 정책 관련 뉴스",
            "keywords": ["정치", "정부", "국회", "정책", "선거"]
        },
        "경제": {
            "description": "경제, 금융, 기업 관련 뉴스",
            "keywords": ["경제", "금융", "기업", "증시", "부동산"]
        },
        "사회": {
            "description": "사회, 사건사고, 복지 관련 뉴스", 
            "keywords": ["사회", "사건", "복지", "교육", "의료"]
        },
        "생활/문화": {
            "description": "문화, 예술, 생활 관련 뉴스",
            "keywords": ["문화", "예술", "생활", "여행", "음식"]
        },
        "IT/과학": {
            "description": "IT, 과학기술, 혁신 관련 뉴스",
            "keywords": ["IT", "과학", "기술", "AI", "스마트폰"]
        },
        "국제": {
            "description": "국제, 외교, 해외 관련 뉴스",
            "keywords": ["국제", "외교", "해외", "미국", "중국"]
        },
        "스포츠": {
            "description": "스포츠, 경기, 선수 관련 뉴스",
            "keywords": ["스포츠", "축구", "야구", "올림픽", "경기"]
        }
    }
    
    return {
        "categories": categories,
        "recommended_combinations": {
            "comprehensive": ["정치", "경제", "사회"],
            "business_focused": ["경제", "IT/과학", "국제"],
            "social_focused": ["사회", "생활/문화", "정치"],
            "all": list(categories.keys())
        }
    }