"""
콘텐츠 제작자 API 모듈

콘텐츠 제작자 기능을 위한 API 엔드포인트 구현
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.modules.content_creator.workflow import ContentWorkflow
from src.api.bigkinds_client import BigKindsClient
from src.utils.logger import setup_logger

# API 라우터 생성
router = APIRouter(prefix="/content-creator", tags=["콘텐츠 제작자 도구"])

# 공통 의존성
async def get_content_workflow():
    """콘텐츠 워크플로우 의존성"""
    return ContentWorkflow()

@router.get("/")
async def content_creator_root():
    """콘텐츠 제작자 API 루트 경로"""
    return {"message": "AI NOVA 콘텐츠 제작자 API에 오신 것을 환영합니다", "version": "1.0.0"}

# 워크플로우 관련 엔드포인트
@router.post("/workflows", response_model=Dict[str, Any])
async def create_workflow(
    name: str = Body(..., description="워크플로우 이름"),
    description: str = Body("", description="워크플로우 설명"),
    template_id: Optional[str] = Body(None, description="템플릿 ID (옵션)"),
    workflow_service: ContentWorkflow = Depends(get_content_workflow)
):
    """새 워크플로우 생성"""
    workflow = await workflow_service.create_workflow(name, description, template_id)
    return workflow

@router.get("/workflows", response_model=List[Dict[str, Any]])
async def list_workflows(
    status: Optional[str] = Query(None, description="상태 필터 (옵션)"),
    workflow_service: ContentWorkflow = Depends(get_content_workflow)
):
    """워크플로우 목록 조회"""
    workflows = await workflow_service.list_workflows(status)
    return workflows

@router.get("/workflows/{workflow_id}", response_model=Dict[str, Any])
async def get_workflow(
    workflow_id: str,
    workflow_service: ContentWorkflow = Depends(get_content_workflow)
):
    """워크플로우 상세 조회"""
    workflow = await workflow_service.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="워크플로우를 찾을 수 없습니다")
    return workflow

@router.patch("/workflows/{workflow_id}", response_model=Dict[str, Any])
async def update_workflow(
    workflow_id: str,
    data: Dict[str, Any] = Body(..., description="업데이트할 데이터"),
    workflow_service: ContentWorkflow = Depends(get_content_workflow)
):
    """워크플로우 업데이트"""
    updated_workflow = await workflow_service.update_workflow(workflow_id, data)
    if not updated_workflow:
        raise HTTPException(status_code=404, detail="워크플로우를 찾을 수 없습니다")
    return updated_workflow

@router.delete("/workflows/{workflow_id}", response_model=Dict[str, Any])
async def delete_workflow(
    workflow_id: str,
    workflow_service: ContentWorkflow = Depends(get_content_workflow)
):
    """워크플로우 삭제"""
    success = await workflow_service.delete_workflow(workflow_id)
    if not success:
        raise HTTPException(status_code=404, detail="워크플로우를 찾을 수 없습니다")
    return {"success": True, "message": "워크플로우가 삭제되었습니다"}

@router.post("/workflows/{workflow_id}/execute", response_model=Dict[str, Any])
async def execute_workflow_stage(
    workflow_id: str,
    stage_id: Optional[str] = Body(None, description="단계 ID (옵션)"),
    stage_data: Optional[Dict[str, Any]] = Body(None, description="단계 실행 데이터 (옵션)"),
    workflow_service: ContentWorkflow = Depends(get_content_workflow)
):
    """워크플로우 단계 실행"""
    result = await workflow_service.execute_stage(workflow_id, stage_id, stage_data)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

# 템플릿 관련 엔드포인트
@router.post("/templates", response_model=Dict[str, Any])
async def save_as_template(
    workflow_id: str = Body(..., description="워크플로우 ID"),
    template_name: str = Body(..., description="템플릿 이름"),
    template_description: str = Body("", description="템플릿 설명"),
    workflow_service: ContentWorkflow = Depends(get_content_workflow)
):
    """워크플로우를 템플릿으로 저장"""
    template = await workflow_service.save_as_template(workflow_id, template_name, template_description)
    if "error" in template:
        raise HTTPException(status_code=400, detail=template["error"])
    return template

@router.get("/templates", response_model=List[Dict[str, Any]])
async def list_templates(
    workflow_service: ContentWorkflow = Depends(get_content_workflow)
):
    """템플릿 목록 조회"""
    templates = await workflow_service.list_templates()
    return templates

# 콘텐츠 지원 도구 엔드포인트
@router.post("/tools/content-brief", response_model=Dict[str, Any])
async def generate_content_brief(
    issue_data: Dict[str, Any] = Body(..., description="이슈 분석 데이터"),
    workflow_service: ContentWorkflow = Depends(get_content_workflow)
):
    """콘텐츠 개요 생성"""
    try:
        content_brief = workflow_service.content_assistant.generate_content_brief(issue_data)
        return {"content_brief": content_brief}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"콘텐츠 개요 생성 실패: {str(e)}")

@router.post("/tools/quote-image", response_model=Dict[str, Any])
async def create_quote_image(
    quote: str = Body(..., description="인용 문구"),
    source: str = Body("", description="출처"),
    width: int = Body(1200, description="이미지 너비"),
    height: int = Body(630, description="이미지 높이"),
    workflow_service: ContentWorkflow = Depends(get_content_workflow)
):
    """인용구 이미지 생성"""
    try:
        image_data = workflow_service.content_assistant.create_quote_image(quote, source, width, height)
        return {"image_data": image_data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"인용구 이미지 생성 실패: {str(e)}")

@router.post("/tools/timeline-image", response_model=Dict[str, Any])
async def create_timeline_image(
    events: List[Dict[str, Any]] = Body(..., description="이벤트 목록"),
    title: str = Body("이슈 타임라인", description="타임라인 제목"),
    width: int = Body(1200, description="이미지 너비"),
    height: int = Body(800, description="이미지 높이"),
    workflow_service: ContentWorkflow = Depends(get_content_workflow)
):
    """타임라인 이미지 생성"""
    try:
        image_data = workflow_service.content_assistant.create_timeline_image(events, title, width, height)
        return {"image_data": image_data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"타임라인 이미지 생성 실패: {str(e)}")

@router.post("/tools/stats-image", response_model=Dict[str, Any])
async def create_statistics_image(
    data: Dict[str, List[float]] = Body(..., description="차트 데이터"),
    title: str = Body("주요 통계", description="차트 제목"),
    chart_type: str = Body("bar", description="차트 유형 (bar, line, pie)"),
    width: int = Body(1000, description="이미지 너비"),
    height: int = Body(600, description="이미지 높이"),
    workflow_service: ContentWorkflow = Depends(get_content_workflow)
):
    """통계 차트 이미지 생성"""
    try:
        image_data = workflow_service.content_assistant.create_statistics_image(data, title, chart_type, width, height)
        return {"image_data": image_data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"통계 차트 이미지 생성 실패: {str(e)}")

@router.post("/tools/verify-facts", response_model=Dict[str, Any])
async def verify_facts(
    facts: List[Dict[str, Any]] = Body(..., description="검증할 사실 목록"),
    news_list: List[Dict[str, Any]] = Body(..., description="뉴스 기사 목록"),
    workflow_service: ContentWorkflow = Depends(get_content_workflow)
):
    """사실 검증"""
    try:
        verified_facts = workflow_service.content_assistant.verify_facts(facts, news_list)
        return {"verified_facts": verified_facts}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"사실 검증 실패: {str(e)}")

@router.post("/tools/export-package", response_model=Dict[str, Any])
async def export_content_package(
    issue_data: Dict[str, Any] = Body(..., description="이슈 분석 데이터"),
    format: str = Body("json", description="내보내기 형식 (json, md, html)"),
    workflow_service: ContentWorkflow = Depends(get_content_workflow)
):
    """콘텐츠 패키지 내보내기"""
    try:
        file_path = workflow_service.content_assistant.export_content_package(issue_data, format)
        return {"file_path": file_path, "format": format}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"콘텐츠 패키지 내보내기 실패: {str(e)}")

# 패키지 초기화 파일
def init_app(router):
    """FastAPI 앱에 콘텐츠 제작자 라우터 추가"""
    return router