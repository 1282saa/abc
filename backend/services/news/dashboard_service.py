"""
관심 종목 대시보드 서비스

특정 기업에 대한 다각적인 정보를 종합하여 대시보드 형태로 제공합니다.
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from backend.api.clients.bigkinds.client import BigKindsClient
from backend.services.news.briefing_service import BriefingService

class DashboardService:
    def __init__(self, bigkinds_client: BigKindsClient, briefing_service: BriefingService):
        self.bigkinds_client = bigkinds_client
        self.briefing_service = briefing_service

    async def get_full_dashboard(self, company_name: str) -> Dict[str, Any]:
        """
        한 번의 호출로 특정 기업에 대한 전체 대시보드 데이터를 생성합니다.

        Args:
            company_name: 분석할 기업명

        Returns:
            오늘의 브리핑, 주요 키워드 등을 포함하는 종합 대시보드 데이터
        """
        # 1. 오늘의 핵심 브리핑 생성
        # BriefingService를 재사용하여 "오늘의 [회사명] 주요 이슈"와 같은 질문으로 요약 생성
        todays_briefing_question = f"오늘의 {company_name} 주요 이슈와 동향 알려줘"
        briefing_data = await self.briefing_service.generate_briefing_for_question(todays_briefing_question)

        # 2. 주요 이슈 & 키워드 추출 (최근 7일)
        key_issues = self._get_key_issues_and_keywords(company_name, days=7)

        # 3. 긍정/부정 시그널 (향후 확장 기능)
        sentiment_signal = self._get_sentiment_signal(company_name)

        # 4. 연관 기업 분석 (향후 확장 기능)
        related_companies = self._get_related_companies(company_name)

        return {
            "company_name": company_name,
            "todays_briefing": briefing_data,
            "key_issues": key_issues,
            "sentiment_signal": sentiment_signal,
            "related_companies": related_companies,
            "last_updated": datetime.now().isoformat()
        }

    def _get_key_issues_and_keywords(self, company_name: str, days: int = 7) -> List[str]:
        """
        최근 n일간 기업 뉴스에서 가장 빈번하게 언급된 키워드를 추출합니다.
        """
        try:
            # 날짜 설정
            date_to = datetime.now()
            date_from = date_to - timedelta(days=days)

            # TopN API를 호출하여 연관 키워드 추출
            # get_keyword_topn은 정확한 키워드 매칭이 중요하므로, preprocess_query를 사용하지 않고 회사명을 그대로 사용
            top_n_keywords = self.bigkinds_client.get_keyword_topn(
                keyword=f'"{company_name}"', # 정확한 회사명으로 검색
                date_from=date_from.strftime("%Y-%m-%d"),
                date_to=date_to.strftime("%Y-%m-%d"),
                limit=10 # 상위 10개 추출
            )
            
            # 회사명 자체는 키워드에서 제외
            return [kw for kw in top_n_keywords if kw != company_name]

        except Exception as e:
            self.bigkinds_client.logger.error(f"주요 키워드 추출 실패: {e}")
            return []

    def _get_sentiment_signal(self, company_name: str) -> Dict[str, Any]:
        """
        (향후 구현) 기사 제목 등을 분석하여 긍정/부정 시그널을 생성합니다.
        """
        # 이 기능을 구현하려면 감성분석 모델(예: KoBERT 기반 모델)이 필요합니다.
        return {
            "status": "not_implemented",
            "positive_rate": 0.0,
            "negative_rate": 0.0,
            "neutral_rate": 1.0,
            "message": "감성 분석 기능은 향후 지원될 예정입니다."
        }
        
    def _get_related_companies(self, company_name: str) -> List[str]:
        """
        (향후 구현) 뉴스 본문을 분석하여 가장 많이 함께 언급된 연관 기업을 추출합니다.
        """
        # 이 기능을 구현하려면 여러 기사의 본문(tms_raw_stream)에서 기업명을 인식하고 빈도를 세는 로직이 필요합니다.
        return ["(향후 지원 예정)"] 