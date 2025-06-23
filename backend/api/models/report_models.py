"""
레포트 생성 관련 모델 정의
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any
from datetime import datetime
from enum import Enum

class ReportPeriodType(str, Enum):
    """레포트 기간 타입"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"

class ReportRequest(BaseModel):
    """레포트 생성 요청 모델"""
    company_name: str = Field(..., description="기업명")
    company_code: Optional[str] = Field(None, description="기업 코드")
    period_type: ReportPeriodType = Field(..., description="레포트 기간 타입")
    date_from: str = Field(..., description="시작일 (YYYY-MM-DD)")
    date_to: str = Field(..., description="종료일 (YYYY-MM-DD)")
    language: Literal["ko", "en"] = Field(default="ko", description="레포트 언어")
    include_charts: bool = Field(default=True, description="차트 포함 여부")
    max_articles: int = Field(default=50, description="분석할 최대 기사 수", ge=10, le=200)
    
class CitationSource(BaseModel):
    """인용 출처 정보"""
    id: str = Field(..., description="기사 ID")
    title: str = Field(..., description="기사 제목")
    url: str = Field(..., description="기사 URL")
    provider: str = Field(..., description="언론사")
    published_at: str = Field(..., description="발행일시")
    excerpt: str = Field(..., description="인용된 부분")

class ReportSection(BaseModel):
    """레포트 섹션"""
    title: str = Field(..., description="섹션 제목")
    content: str = Field(..., description="섹션 내용")
    key_points: List[str] = Field(default=[], description="주요 포인트")
    citations: List[int] = Field(default=[], description="인용 번호 목록")

class ReportMetadata(BaseModel):
    """레포트 메타데이터"""
    company_name: str
    company_code: Optional[str]
    period_type: ReportPeriodType
    date_from: str
    date_to: str
    total_articles: int
    generated_at: str
    generation_time_seconds: float
    model_used: str

class CompanyReport(BaseModel):
    """기업 레포트 응답 모델"""
    metadata: ReportMetadata = Field(..., description="레포트 메타데이터")
    executive_summary: str = Field(..., description="경영진 요약")
    sections: List[ReportSection] = Field(..., description="레포트 섹션들")
    citations: List[CitationSource] = Field(..., description="인용 출처들")
    keywords: List[str] = Field(default=[], description="주요 키워드")
    sentiment_analysis: Dict[str, Any] = Field(default={}, description="감정 분석 결과")
    stock_impact: Optional[str] = Field(None, description="주가 영향 분석")
    
class ReportGenerationStatus(BaseModel):
    """레포트 생성 상태"""
    status: Literal["processing", "completed", "error"] = Field(..., description="생성 상태")
    progress: int = Field(default=0, description="진행률 (0-100)")
    current_step: str = Field(default="", description="현재 단계")
    estimated_time_remaining: Optional[int] = Field(None, description="예상 남은 시간(초)")
    error_message: Optional[str] = Field(None, description="오류 메시지")

class ReportStreamData(BaseModel):
    """레포트 스트리밍 데이터"""
    type: Literal["progress", "content", "section", "complete", "error"] = Field(..., description="데이터 타입")
    step: Optional[str] = Field(None, description="현재 작업 단계")
    progress: Optional[int] = Field(None, description="진행률")
    section_title: Optional[str] = Field(None, description="섹션 제목")
    content: Optional[str] = Field(None, description="내용")
    result: Optional[CompanyReport] = Field(None, description="완성된 레포트")
    error: Optional[str] = Field(None, description="오류 메시지")

# 레포트 템플릿 관련 모델들
class ReportTemplate(BaseModel):
    """레포트 템플릿"""
    name: str = Field(..., description="템플릿 이름")
    description: str = Field(..., description="템플릿 설명")
    sections: List[str] = Field(..., description="포함될 섹션들")
    prompt_template: str = Field(..., description="프롬프트 템플릿")

# 사전 정의된 레포트 템플릿들
REPORT_TEMPLATES = {
    ReportPeriodType.DAILY: ReportTemplate(
        name="일간 기업 분석 리포트",
        description="하루 동안의 기업 관련 뉴스를 분석한 간략한 리포트",
        sections=["주요 이슈", "언론 반응", "시장 영향"],
        prompt_template="""다음은 {company_name}에 대한 {date_from}의 뉴스 기사들입니다. 
        MZ세대를 위한 FAQ 형식으로 일간 분석 리포트를 작성해주세요:

        ### 응답 형식:
        기사 핵심요약 - {company_name} 일간 리포트

        [70~80자 내외의 간결한 요약]

        서울경제 기사 FAQ - {company_name} 일간 리포트

        Q1. [주요 이슈 관련 질문 - 50자 이내]

        A. [70~80자 내외 답변]

        Q2. [언론 반응 관련 질문 - 50자 이내]

        A. [70~80자 내외 답변]

        Q3. [시장 영향 관련 질문 - 50자 이내]

        A. [70~80자 내외 답변]

        Q4. [향후 전망 관련 질문 - 50자 이내]

        A. [70~80자 내외 답변]

        ### [FAQ 작성 필수 지침]

        **① MZ세대 최적화 원칙**:
        - **짧고 임팩트**: 각 답변은 MZ세대가 카드를 넘기며 빠르게 읽을 수 있는 2~4줄 분량
        - **핵심 정보 집중**: 궁금증 해소에 필요한 가장 중요한 정보만 포함
        - **빠른 이해**: 복잡한 설명보다는 명확하고 간결한 핵심 전달

        **② 구체적 정보 포함 의무 (매우 중요)**:
        - **인명**: 관련된 모든 인물의 실명과 직책을 정확히 명시
        - **지명**: 구체적인 지역명, 국가명, 도시명 등을 명확히 표기
        - **날짜**: 구체적인 날짜, 기간, 시점을 정확히 기재
        - **기관명**: 관련 기관, 회사, 조직의 정확한 명칭 포함
        - **수치 정보**: 금액, 비율, 규모 등 구체적 수치 반드시 포함

        **③ 답변 작성 규칙**:
        - **글자 수**: 모든 답변 70~80자 내외 (공백 포함)
        - **톤앤매너**: 구어체 사용 ("했어요", "해요", "한다고 해요", "라고 해요", "이에요", "예요")
        - **친근한 표현**: MZ세대가 친근감을 느낄 수 있는 자연스러운 구어체

        각 섹션마다 관련 기사를 인용하고 [1], [2] 형식으로 각주를 달아주세요."""
    ),
    
    ReportPeriodType.WEEKLY: ReportTemplate(
        name="주간 기업 동향 리포트", 
        description="일주일 동안의 기업 동향을 종합 분석한 리포트",
        sections=["주간 하이라이트", "사업 동향", "언론 보도 분석", "향후 전망"],
        prompt_template="""다음은 {company_name}에 대한 {date_from}부터 {date_to}까지의 뉴스 기사들입니다.
        MZ세대를 위한 FAQ 형식으로 주간 동향 리포트를 작성해주세요:

        ### 응답 형식:
        기사 핵심요약 - {company_name} 주간 리포트

        [70~80자 내외의 간결한 요약]

        서울경제 기사 FAQ - {company_name} 주간 리포트

        Q1. [주간 하이라이트 관련 질문 - 50자 이내]

        A. [70~80자 내외 답변]

        Q2. [사업 동향 관련 질문 - 50자 이내]

        A. [70~80자 내외 답변]

        Q3. [언론 보도 분석 관련 질문 - 50자 이내]

        A. [70~80자 내외 답변]

        Q4. [향후 전망 관련 질문 - 50자 이내]

        A. [70~80자 내외 답변]

        Q5. [주요 이슈 관련 질문 - 50자 이내]

        A. [70~80자 내외 답변]

        ### [FAQ 작성 필수 지침]

        **① MZ세대 최적화 원칙**:
        - **짧고 임팩트**: 각 답변은 MZ세대가 카드를 넘기며 빠르게 읽을 수 있는 2~4줄 분량
        - **핵심 정보 집중**: 궁금증 해소에 필요한 가장 중요한 정보만 포함
        - **빠른 이해**: 복잡한 설명보다는 명확하고 간결한 핵심 전달

        **② 구체적 정보 포함 의무 (매우 중요)**:
        - **인명**: 관련된 모든 인물의 실명과 직책을 정확히 명시
        - **지명**: 구체적인 지역명, 국가명, 도시명 등을 명확히 표기
        - **날짜**: 구체적인 날짜, 기간, 시점을 정확히 기재
        - **기관명**: 관련 기관, 회사, 조직의 정확한 명칭 포함
        - **수치 정보**: 금액, 비율, 규모 등 구체적 수치 반드시 포함

        **③ 답변 작성 규칙**:
        - **글자 수**: 모든 답변 70~80자 내외 (공백 포함)
        - **톤앤매너**: 구어체 사용 ("했어요", "해요", "한다고 해요", "라고 해요", "이에요", "예요")
        - **친근한 표현**: MZ세대가 친근감을 느낄 수 있는 자연스러운 구어체

        각 섹션마다 관련 기사를 인용하고 [1], [2] 형식으로 각주를 달아주세요."""
    ),
    
    ReportPeriodType.MONTHLY: ReportTemplate(
        name="월간 기업 분석 리포트",
        description="한 달 동안의 기업 활동을 종합적으로 분석한 상세 리포트", 
        sections=["월간 요약", "주요 사업 동향", "재무 관련 뉴스", "ESG 및 지속가능경영", "시장 평가", "향후 한 달 전망"],
        prompt_template="""다음은 {company_name}에 대한 {date_from}부터 {date_to}까지 한 달간의 뉴스 기사들입니다.
        MZ세대를 위한 FAQ 형식으로 월간 종합 분석 리포트를 작성해주세요:

        ### 응답 형식:
        기사 핵심요약 - {company_name} 월간 리포트

        [70~80자 내외의 간결한 요약]

        서울경제 기사 FAQ - {company_name} 월간 리포트

        Q1. [월간 요약 관련 질문 - 50자 이내]

        A. [70~80자 내외 답변]

        Q2. [주요 사업 동향 관련 질문 - 50자 이내]

        A. [70~80자 내외 답변]

        Q3. [재무 관련 뉴스 관련 질문 - 50자 이내]

        A. [70~80자 내외 답변]

        Q4. [ESG 및 지속가능경영 관련 질문 - 50자 이내]

        A. [70~80자 내외 답변]

        Q5. [시장 평가 관련 질문 - 50자 이내]

        A. [70~80자 내외 답변]

        Q6. [향후 한 달 전망 관련 질문 - 50자 이내]

        A. [70~80자 내외 답변]

        ### [FAQ 작성 필수 지침]

        **① MZ세대 최적화 원칙**:
        - **짧고 임팩트**: 각 답변은 MZ세대가 카드를 넘기며 빠르게 읽을 수 있는 2~4줄 분량
        - **핵심 정보 집중**: 궁금증 해소에 필요한 가장 중요한 정보만 포함
        - **빠른 이해**: 복잡한 설명보다는 명확하고 간결한 핵심 전달

        **② 구체적 정보 포함 의무 (매우 중요)**:
        - **인명**: 관련된 모든 인물의 실명과 직책을 정확히 명시
        - **지명**: 구체적인 지역명, 국가명, 도시명 등을 명확히 표기
        - **날짜**: 구체적인 날짜, 기간, 시점을 정확히 기재
        - **기관명**: 관련 기관, 회사, 조직의 정확한 명칭 포함
        - **수치 정보**: 금액, 비율, 규모 등 구체적 수치 반드시 포함

        **③ 답변 작성 규칙**:
        - **글자 수**: 모든 답변 70~80자 내외 (공백 포함)
        - **톤앤매너**: 구어체 사용 ("했어요", "해요", "한다고 해요", "라고 해요", "이에요", "예요")
        - **친근한 표현**: MZ세대가 친근감을 느낄 수 있는 자연스러운 구어체

        각 섹션마다 관련 기사를 인용하고 [1], [2] 형식으로 각주를 달아주세요."""
    ),
    
    ReportPeriodType.QUARTERLY: ReportTemplate(
        name="분기별 기업 전략 리포트",
        description="분기 동안의 기업 전략과 성과를 심층 분석한 리포트",
        sections=["분기 핵심 성과", "전략적 이니셔티브", "경쟁 환경 분석", "재무 성과 분석", "리스크 요인", "다음 분기 전략 방향"],
        prompt_template="""다음은 {company_name}에 대한 {date_from}부터 {date_to}까지 분기간의 뉴스 기사들입니다.
        MZ세대를 위한 FAQ 형식으로 분기별 전략 분석 리포트를 작성해주세요:

        ### 응답 형식:
        기사 핵심요약 - {company_name} 분기 리포트

        [70~80자 내외의 간결한 요약]

        서울경제 기사 FAQ - {company_name} 분기 리포트

        Q1. [분기 핵심 성과 관련 질문 - 50자 이내]

        A. [70~80자 내외 답변]

        Q2. [전략적 이니셔티브 관련 질문 - 50자 이내]

        A. [70~80자 내외 답변]

        Q3. [경쟁 환경 분석 관련 질문 - 50자 이내]

        A. [70~80자 내외 답변]

        Q4. [재무 성과 분석 관련 질문 - 50자 이내]

        A. [70~80자 내외 답변]

        Q5. [리스크 요인 관련 질문 - 50자 이내]

        A. [70~80자 내외 답변]

        Q6. [다음 분기 전략 방향 관련 질문 - 50자 이내]

        A. [70~80자 내외 답변]

        ### [FAQ 작성 필수 지침]

        **① MZ세대 최적화 원칙**:
        - **짧고 임팩트**: 각 답변은 MZ세대가 카드를 넘기며 빠르게 읽을 수 있는 2~4줄 분량
        - **핵심 정보 집중**: 궁금증 해소에 필요한 가장 중요한 정보만 포함
        - **빠른 이해**: 복잡한 설명보다는 명확하고 간결한 핵심 전달

        **② 구체적 정보 포함 의무 (매우 중요)**:
        - **인명**: 관련된 모든 인물의 실명과 직책을 정확히 명시
        - **지명**: 구체적인 지역명, 국가명, 도시명 등을 명확히 표기
        - **날짜**: 구체적인 날짜, 기간, 시점을 정확히 기재
        - **기관명**: 관련 기관, 회사, 조직의 정확한 명칭 포함
        - **수치 정보**: 금액, 비율, 규모 등 구체적 수치 반드시 포함

        **③ 답변 작성 규칙**:
        - **글자 수**: 모든 답변 70~80자 내외 (공백 포함)
        - **톤앤매너**: 구어체 사용 ("했어요", "해요", "한다고 해요", "라고 해요", "이에요", "예요")
        - **친근한 표현**: MZ세대가 친근감을 느낄 수 있는 자연스러운 구어체

        각 섹션마다 관련 기사를 인용하고 [1], [2] 형식으로 각주를 달아주세요."""
    ),
    
    ReportPeriodType.YEARLY: ReportTemplate(
        name="연간 기업 종합 리포트",
        description="연간 기업의 모든 활동을 종합적으로 분석한 포괄적 리포트",
        sections=["연간 성과 요약", "사업 포트폴리오 변화", "글로벌 전략", "혁신과 R&D", "지속가능경영", "재무 성과", "주주가치 창출", "내년도 전략 과제"],
        prompt_template="""다음은 {company_name}에 대한 {date_from}부터 {date_to}까지 1년간의 뉴스 기사들입니다.
        MZ세대를 위한 FAQ 형식으로 연간 종합 분석 리포트를 작성해주세요:

        ### 응답 형식:
        기사 핵심요약 - {company_name} 연간 리포트

        [70~80자 내외의 간결한 요약]

        서울경제 기사 FAQ - {company_name} 연간 리포트

        Q1. [연간 성과 요약 관련 질문 - 50자 이내]

        A. [70~80자 내외 답변]

        Q2. [사업 포트폴리오 변화 관련 질문 - 50자 이내]

        A. [70~80자 내외 답변]

        Q3. [글로벌 전략 관련 질문 - 50자 이내]

        A. [70~80자 내외 답변]

        Q4. [혁신과 R&D 관련 질문 - 50자 이내]

        A. [70~80자 내외 답변]

        Q5. [지속가능경영 관련 질문 - 50자 이내]

        A. [70~80자 내외 답변]

        Q6. [재무 성과 관련 질문 - 50자 이내]

        A. [70~80자 내외 답변]

        Q7. [주주가치 창출 관련 질문 - 50자 이내]

        A. [70~80자 내외 답변]

        Q8. [내년도 전략 과제 관련 질문 - 50자 이내]

        A. [70~80자 내외 답변]

        ### [FAQ 작성 필수 지침]

        **① MZ세대 최적화 원칙**:
        - **짧고 임팩트**: 각 답변은 MZ세대가 카드를 넘기며 빠르게 읽을 수 있는 2~4줄 분량
        - **핵심 정보 집중**: 궁금증 해소에 필요한 가장 중요한 정보만 포함
        - **빠른 이해**: 복잡한 설명보다는 명확하고 간결한 핵심 전달

        **② 구체적 정보 포함 의무 (매우 중요)**:
        - **인명**: 관련된 모든 인물의 실명과 직책을 정확히 명시
        - **지명**: 구체적인 지역명, 국가명, 도시명 등을 명확히 표기
        - **날짜**: 구체적인 날짜, 기간, 시점을 정확히 기재
        - **기관명**: 관련 기관, 회사, 조직의 정확한 명칭 포함
        - **수치 정보**: 금액, 비율, 규모 등 구체적 수치 반드시 포함

        **③ 답변 작성 규칙**:
        - **글자 수**: 모든 답변 70~80자 내외 (공백 포함)
        - **톤앤매너**: 구어체 사용 ("했어요", "해요", "한다고 해요", "라고 해요", "이에요", "예요")
        - **친근한 표현**: MZ세대가 친근감을 느낄 수 있는 자연스러운 구어체

        각 섹션마다 관련 기사를 인용하고 [1], [2] 형식으로 각주를 달아주세요."""
    )
}