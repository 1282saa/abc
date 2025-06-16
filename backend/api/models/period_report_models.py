"""
기간별 자동 레포트 생성 관련 모델 정의
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from enum import Enum

class PeriodReportType(str, Enum):
    """기간별 레포트 타입"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"

class AutoReportRequest(BaseModel):
    """자동 레포트 생성 요청"""
    report_type: PeriodReportType = Field(..., description="레포트 타입")
    company_name: Optional[str] = Field(None, description="특정 기업명 (종목별 레포트인 경우)")
    company_code: Optional[str] = Field(None, description="특정 기업 코드 (종목별 레포트인 경우)")
    target_date: Optional[str] = Field(None, description="기준일 (YYYY-MM-DD), 미지정시 어제/지난주/지난달 등")
    categories: List[str] = Field(default=["정치", "경제", "사회"], description="분석할 뉴스 카테고리")
    max_articles: int = Field(default=100, description="분석할 최대 기사 수", ge=10, le=500)
    include_sentiment: bool = Field(default=True, description="감정 분석 포함 여부")
    include_keywords: bool = Field(default=True, description="키워드 분석 포함 여부")
    language: str = Field(default="ko", description="레포트 언어")

class NewsCluster(BaseModel):
    """뉴스 클러스터 (유사한 뉴스들의 그룹)"""
    id: str = Field(..., description="클러스터 ID")
    title: str = Field(..., description="클러스터 대표 제목")
    articles_count: int = Field(..., description="포함된 기사 수")
    representative_article_id: str = Field(..., description="대표 기사 ID")
    keywords: List[str] = Field(default=[], description="클러스터 키워드")
    categories: List[str] = Field(default=[], description="관련 카테고리")
    sentiment_score: Optional[float] = Field(None, description="감정 점수 (-1 ~ 1)")
    impact_score: Optional[float] = Field(None, description="사회적 영향도 점수")

class PeriodInsight(BaseModel):
    """기간별 인사이트"""
    type: str = Field(..., description="인사이트 타입 (trend, pattern, anomaly 등)")
    title: str = Field(..., description="인사이트 제목")
    description: str = Field(..., description="인사이트 설명")
    confidence: float = Field(..., description="신뢰도 (0-1)")
    supporting_clusters: List[str] = Field(default=[], description="관련 클러스터 ID들")

class CategorySummary(BaseModel):
    """카테고리별 요약"""
    category: str = Field(..., description="카테고리명")
    total_articles: int = Field(..., description="총 기사 수")
    top_clusters: List[NewsCluster] = Field(..., description="주요 클러스터들")
    key_developments: List[str] = Field(default=[], description="주요 발전사항")
    sentiment_trend: Optional[str] = Field(None, description="감정 트렌드 (positive/negative/neutral)")
    
class TimelineEvent(BaseModel):
    """타임라인 이벤트"""
    date: str = Field(..., description="날짜")
    title: str = Field(..., description="이벤트 제목")
    description: str = Field(..., description="이벤트 설명")
    importance: int = Field(..., description="중요도 (1-5)")
    related_cluster_ids: List[str] = Field(default=[], description="관련 클러스터 ID들")
    category: str = Field(..., description="카테고리")

class PeriodReport(BaseModel):
    """기간별 레포트"""
    id: str = Field(..., description="레포트 ID")
    report_type: PeriodReportType = Field(..., description="레포트 타입")
    company_name: Optional[str] = Field(None, description="분석 대상 기업명")
    company_code: Optional[str] = Field(None, description="분석 대상 기업 코드")
    period_start: str = Field(..., description="분석 기간 시작")
    period_end: str = Field(..., description="분석 기간 종료")
    generated_at: str = Field(..., description="생성 시간")
    
    # 메타데이터
    total_articles_analyzed: int = Field(..., description="분석된 총 기사 수")
    categories_covered: List[str] = Field(..., description="다룬 카테고리들")
    analysis_duration_seconds: float = Field(..., description="분석 소요 시간")
    
    # 핵심 내용
    executive_summary: str = Field(..., description="경영진 요약")
    key_highlights: List[str] = Field(..., description="핵심 하이라이트")
    
    # 상세 분석
    category_summaries: List[CategorySummary] = Field(..., description="카테고리별 요약")
    timeline: List[TimelineEvent] = Field(..., description="주요 이벤트 타임라인")
    insights: List[PeriodInsight] = Field(..., description="기간별 인사이트")
    
    # 통계 및 분석
    top_keywords: List[Dict[str, Any]] = Field(default=[], description="상위 키워드")
    sentiment_analysis: Dict[str, Any] = Field(default={}, description="전체 감정 분석")
    trend_analysis: Dict[str, Any] = Field(default={}, description="트렌드 분석")
    
    # 비교 분석 (이전 기간과의 비교)
    comparison: Optional[Dict[str, Any]] = Field(None, description="이전 기간 대비 변화")

class ReportGenerationProgress(BaseModel):
    """레포트 생성 진행상황"""
    stage: str = Field(..., description="현재 단계")
    progress: int = Field(..., description="진행률 (0-100)")
    message: str = Field(..., description="진행 메시지")
    estimated_remaining_seconds: Optional[int] = Field(None, description="예상 남은 시간")
    current_task: Optional[str] = Field(None, description="현재 작업")

# 레포트 템플릿 정의
PERIOD_REPORT_TEMPLATES = {
    PeriodReportType.DAILY: {
        "name": "일간 뉴스 브리핑",
        "description": "어제 하루 동안의 주요 뉴스를 분석한 일일 브리핑",
        "sections": [
            "오늘의 핵심 이슈",
            "정치 주요 동향", 
            "경제 핵심 뉴스",
            "사회 이슈 분석",
            "국제 뉴스 요약",
            "내일 주목할 이슈"
        ],
        "max_articles": 100,
        "focus": "즉시성과 중요도"
    },
    
    PeriodReportType.WEEKLY: {
        "name": "주간 뉴스 리뷰",
        "description": "지난 일주일간의 뉴스를 종합 분석한 주간 리포트", 
        "sections": [
            "주간 하이라이트",
            "정치 주요 이슈",
            "경제 동향 분석", 
            "사회 트렌드",
            "문화·IT 동향",
            "다음 주 전망"
        ],
        "max_articles": 200,
        "focus": "트렌드와 패턴 분석"
    },
    
    PeriodReportType.MONTHLY: {
        "name": "월간 뉴스 분석",
        "description": "지난 한 달간의 뉴스를 심층 분석한 월간 리포트",
        "sections": [
            "월간 핵심 이슈",
            "정치 환경 변화",
            "경제 지표 분석",
            "사회 변화 동향", 
            "정책 변화 영향",
            "다음 달 주요 이슈"
        ],
        "max_articles": 500,
        "focus": "깊이있는 분석과 인사이트"
    },
    
    PeriodReportType.QUARTERLY: {
        "name": "분기별 종합 분석",
        "description": "지난 분기의 뉴스를 종합적으로 분석한 분기 리포트",
        "sections": [
            "분기 핵심 성과",
            "정치 환경 평가",
            "경제 성과 분석",
            "사회 변화 평가",
            "정책 효과 분석", 
            "다음 분기 전망"
        ],
        "max_articles": 1000,
        "focus": "전략적 분석과 평가"
    },
    
    PeriodReportType.YEARLY: {
        "name": "연간 종합 평가",
        "description": "지난 1년간의 뉴스를 총괄 분석한 연간 리포트",
        "sections": [
            "연간 주요 성과",
            "정치 환경 총평",
            "경제 성과 평가",
            "사회 변화 총결",
            "정책 성과 분석",
            "내년 전망과 과제"
        ],
        "max_articles": 2000,
        "focus": "총괄적 평가와 미래 전망"
    }
}

class ReportTemplate(BaseModel):
    """레포트 템플릿"""
    name: str
    description: str
    sections: List[str]
    max_articles: int
    focus: str