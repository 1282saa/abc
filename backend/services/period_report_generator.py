"""
기간별 자동 레포트 생성 서비스

뉴스 데이터를 기간별로 자동 수집하고 AI 분석을 통해 인사이트 레포트를 생성합니다.
"""

import asyncio
import json
import re
import time
from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional, AsyncGenerator, Tuple
import openai
import sys
from pathlib import Path
from collections import Counter, defaultdict
import uuid

# 프로젝트 루트 디렉토리 설정
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.api.clients.bigkinds import BigKindsClient
from backend.api.models.period_report_models import (
    AutoReportRequest, PeriodReport, PeriodReportType, NewsCluster,
    CategorySummary, TimelineEvent, PeriodInsight, ReportGenerationProgress,
    PERIOD_REPORT_TEMPLATES
)
from backend.utils.logger import setup_logger

class PeriodReportGenerator:
    """기간별 자동 레포트 생성기"""
    
    def __init__(self, openai_api_key: str, bigkinds_client: BigKindsClient):
        """
        Args:
            openai_api_key: OpenAI API 키
            bigkinds_client: BigKinds 클라이언트
        """
        self.openai_api_key = openai_api_key
        self.bigkinds_client = bigkinds_client
        self.logger = setup_logger("services.period_report_generator")
        
        # OpenAI 클라이언트 초기화
        openai.api_key = self.openai_api_key
        
    async def generate_period_report_stream(
        self, 
        request: AutoReportRequest
    ) -> AsyncGenerator[ReportGenerationProgress, None]:
        """
        스트리밍 방식으로 기간별 레포트 생성
        
        Args:
            request: 자동 레포트 생성 요청
            
        Yields:
            ReportGenerationProgress: 진행 상황
        """
        start_time = time.time()
        report_id = str(uuid.uuid4())
        
        try:
            # 기업명 저장 (AI 분석에서 사용)
            self._current_company_name = request.company_name
            
            # 1단계: 기간 설정 및 검증
            company_msg = f"{request.company_name} " if request.company_name else ""
            yield ReportGenerationProgress(
                stage="initialization",
                progress=5,
                message=f"{company_msg}분석 기간을 설정하고 있습니다...",
                current_task="기간 계산"
            )
            
            period_start, period_end = self._calculate_period(request.report_type, request.target_date)
            
            yield ReportGenerationProgress(
                stage="period_set",
                progress=10,
                message=f"{period_start} ~ {period_end} 기간으로 설정되었습니다.",
                current_task="뉴스 수집 준비"
            )
            
            # 2단계: 뉴스 데이터 수집
            yield ReportGenerationProgress(
                stage="data_collection",
                progress=20,
                message="해당 기간의 뉴스 데이터를 수집하고 있습니다...",
                current_task="BigKinds API 호출"
            )
            
            articles_by_category = await self._collect_period_news(
                period_start, period_end, request.categories, request.max_articles, request.company_name
            )
            
            total_articles = sum(len(articles) for articles in articles_by_category.values())
            
            yield ReportGenerationProgress(
                stage="data_collected",
                progress=35,
                message=f"총 {total_articles}개의 기사를 수집했습니다.",
                current_task="뉴스 클러스터링"
            )
            
            # 3단계: 뉴스 클러스터링 및 분석
            yield ReportGenerationProgress(
                stage="clustering",
                progress=50,
                message="유사한 뉴스들을 그룹화하고 주요 이슈를 파악하고 있습니다...",
                current_task="클러스터 분석"
            )
            
            clusters_by_category = await self._cluster_news_by_category(articles_by_category)
            
            yield ReportGenerationProgress(
                stage="clustering_done",
                progress=60,
                message="주요 이슈들을 성공적으로 식별했습니다.",
                current_task="AI 분석 시작"
            )
            
            # 4단계: AI 분석 및 인사이트 도출
            yield ReportGenerationProgress(
                stage="ai_analysis",
                progress=70,
                message="AI가 뉴스 데이터를 분석하고 인사이트를 도출하고 있습니다...",
                current_task="GPT 분석"
            )
            
            ai_analysis = await self._generate_ai_analysis(
                request.report_type, period_start, period_end, 
                clusters_by_category, total_articles
            )
            
            yield ReportGenerationProgress(
                stage="analysis_done",
                progress=85,
                message="AI 분석이 완료되었습니다. 레포트를 구성하고 있습니다...",
                current_task="레포트 구성"
            )
            
            # 5단계: 최종 레포트 생성
            yield ReportGenerationProgress(
                stage="report_generation",
                progress=95,
                message="최종 레포트를 생성하고 있습니다...",
                current_task="레포트 완성"
            )
            
            final_report = await self._create_final_period_report(
                report_id, request, period_start, period_end,
                articles_by_category, clusters_by_category, ai_analysis, start_time
            )
            
            # 기업명 정리
            self._current_company_name = None
            
            yield ReportGenerationProgress(
                stage="completed",
                progress=100,
                message="기간별 레포트 생성이 완료되었습니다!",
                current_task="완료"
            )
            
            # 완성된 레포트 반환을 위한 특별 진행상황
            progress = ReportGenerationProgress(
                stage="result",
                progress=100,
                message="완료",
                current_task="결과 전달"
            )
            # 동적으로 result 필드 추가
            progress.__dict__['result'] = final_report
            yield progress
            
        except Exception as e:
            self.logger.error(f"기간별 레포트 생성 중 오류 발생: {e}", exc_info=True)
            yield ReportGenerationProgress(
                stage="error",
                progress=0,
                message=f"레포트 생성 중 오류가 발생했습니다: {str(e)}",
                current_task="오류 처리"
            )
    
    def _calculate_period(self, report_type: PeriodReportType, target_date: Optional[str] = None) -> Tuple[str, str]:
        """분석 기간 계산"""
        
        if target_date:
            base_date = datetime.strptime(target_date, "%Y-%m-%d").date()
        else:
            base_date = date.today()
        
        if report_type == PeriodReportType.DAILY:
            # 전날 하루
            target_day = base_date - timedelta(days=1)
            return target_day.strftime("%Y-%m-%d"), target_day.strftime("%Y-%m-%d")
            
        elif report_type == PeriodReportType.WEEKLY:
            # 지난 주 (월요일부터 일요일까지)
            days_since_monday = base_date.weekday()
            last_monday = base_date - timedelta(days=days_since_monday + 7)
            last_sunday = last_monday + timedelta(days=6)
            return last_monday.strftime("%Y-%m-%d"), last_sunday.strftime("%Y-%m-%d")
            
        elif report_type == PeriodReportType.MONTHLY:
            # 지난 달 (1일부터 말일까지)
            if base_date.month == 1:
                last_month = base_date.replace(year=base_date.year - 1, month=12, day=1)
            else:
                last_month = base_date.replace(month=base_date.month - 1, day=1)
            
            # 지난 달 말일 계산
            if last_month.month == 12:
                next_month = last_month.replace(year=last_month.year + 1, month=1, day=1)
            else:
                next_month = last_month.replace(month=last_month.month + 1, day=1)
            last_day = next_month - timedelta(days=1)
            
            return last_month.strftime("%Y-%m-%d"), last_day.strftime("%Y-%m-%d")
            
        elif report_type == PeriodReportType.QUARTERLY:
            # 지난 분기 (3개월)
            current_quarter = (base_date.month - 1) // 3 + 1
            if current_quarter == 1:
                last_quarter_start = base_date.replace(year=base_date.year - 1, month=10, day=1)
                last_quarter_end = base_date.replace(year=base_date.year - 1, month=12, day=31)
            else:
                start_month = (current_quarter - 2) * 3 + 1
                last_quarter_start = base_date.replace(month=start_month, day=1)
                if start_month + 2 == 12:
                    last_quarter_end = base_date.replace(month=12, day=31)
                else:
                    next_quarter_start = base_date.replace(month=start_month + 3, day=1)
                    last_quarter_end = next_quarter_start - timedelta(days=1)
            
            return last_quarter_start.strftime("%Y-%m-%d"), last_quarter_end.strftime("%Y-%m-%d")
            
        else:  # YEARLY
            # 작년 (1월 1일부터 12월 31일까지)
            last_year_start = base_date.replace(year=base_date.year - 1, month=1, day=1)
            last_year_end = base_date.replace(year=base_date.year - 1, month=12, day=31)
            return last_year_start.strftime("%Y-%m-%d"), last_year_end.strftime("%Y-%m-%d")
    
    async def _collect_period_news(
        self, 
        period_start: str, 
        period_end: str, 
        categories: List[str], 
        max_articles: int,
        company_name: Optional[str] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """기간별 뉴스 수집"""
        
        articles_by_category = {}
        articles_per_category = max_articles // len(categories)
        
        for category in categories:
            try:
                # 검색 쿼리 구성
                if company_name:
                    # 종목별 레포트인 경우 기업명으로 검색
                    query = f"{company_name}"
                else:
                    # 일반 기간별 레포트인 경우 카테고리로 검색
                    query = f"카테고리:{category}"
                
                # 카테고리별 뉴스 검색
                search_result = self.bigkinds_client.search_news(
                    query=query,
                    date_from=period_start,
                    date_to=period_end,
                    sort="date",
                    page_size=min(articles_per_category, 100)
                )
                
                articles = search_result.get("return_object", {}).get("documents", [])
                articles_by_category[category] = articles
                
                self.logger.info(f"{category} 카테고리: {len(articles)}개 기사 수집")
                
            except Exception as e:
                self.logger.error(f"{category} 카테고리 뉴스 수집 실패: {e}")
                articles_by_category[category] = []
        
        return articles_by_category
    
    async def _cluster_news_by_category(
        self, 
        articles_by_category: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, List[NewsCluster]]:
        """카테고리별 뉴스 클러스터링"""
        
        clusters_by_category = {}
        
        for category, articles in articles_by_category.items():
            if not articles:
                clusters_by_category[category] = []
                continue
            
            # 간단한 키워드 기반 클러스터링
            clusters = self._simple_clustering(articles, category)
            clusters_by_category[category] = clusters
            
        return clusters_by_category
    
    def _simple_clustering(self, articles: List[Dict[str, Any]], category: str) -> List[NewsCluster]:
        """간단한 키워드 기반 클러스터링"""
        
        # 제목에서 키워드 추출
        keyword_groups = defaultdict(list)
        
        for article in articles:
            title = article.get("title", "")
            # 주요 키워드 추출 (한글 2글자 이상)
            keywords = re.findall(r'[가-힣]{2,}', title)
            
            # 가장 긴 키워드를 대표 키워드로 사용
            if keywords:
                main_keyword = max(keywords, key=len)
                keyword_groups[main_keyword].append(article)
        
        # 클러스터 생성
        clusters = []
        for i, (keyword, group_articles) in enumerate(keyword_groups.items()):
            if len(group_articles) >= 2:  # 최소 2개 이상의 기사가 있는 경우만
                cluster = NewsCluster(
                    id=f"{category}_cluster_{i}",
                    title=f"{keyword} 관련 뉴스",
                    articles_count=len(group_articles),
                    representative_article_id=group_articles[0].get("_id", ""),
                    keywords=[keyword],
                    categories=[category],
                    sentiment_score=0.0,  # 기본값
                    impact_score=len(group_articles) / len(articles)  # 비율로 영향도 계산
                )
                clusters.append(cluster)
        
        # 영향도 순으로 정렬 후 상위 5개만 선택
        clusters.sort(key=lambda x: x.impact_score, reverse=True)
        return clusters[:5]
    
    async def _generate_ai_analysis(
        self,
        report_type: PeriodReportType,
        period_start: str,
        period_end: str,
        clusters_by_category: Dict[str, List[NewsCluster]],
        total_articles: int
    ) -> Dict[str, Any]:
        """AI를 이용한 뉴스 분석"""
        
        # 클러스터 정보를 텍스트로 구성
        clusters_text = ""
        for category, clusters in clusters_by_category.items():
            clusters_text += f"\\n\\n[{category}]\\n"
            for cluster in clusters:
                clusters_text += f"- {cluster.title} ({cluster.articles_count}개 기사)\\n"
        
        template = PERIOD_REPORT_TEMPLATES[report_type]
        
        # 종목별 레포트인지 일반 레포트인지에 따라 프롬프트 구성
        if hasattr(self, '_current_company_name') and self._current_company_name:
            company_context = f"기업명: {self._current_company_name}\n"
            report_focus = f"{self._current_company_name} 기업"
            analysis_instruction = f"{self._current_company_name} 기업과 관련된"
        else:
            company_context = ""
            report_focus = "전반적인"
            analysis_instruction = "전반적인"

        prompt = f"""
다음은 {period_start}부터 {period_end}까지의 기간 동안 수집된 뉴스 클러스터 정보입니다.

{company_context}분석 기간: {period_start} ~ {period_end}
총 기사 수: {total_articles}개
레포트 타입: {report_type.value}

{template['name']} 형태로 {report_focus} 분석 레포트를 작성해주세요.

뉴스 클러스터 정보:
{clusters_text}

다음 형식으로 분석해주세요:

1. 핵심 요약 (3-5줄) - {analysis_instruction} 내용 중심
2. 주요 하이라이트 (5개 항목)
3. 카테고리별 분석
4. 주요 트렌드
5. 향후 전망

각 분석은 구체적이고 객관적인 내용으로 작성하고, 추측보다는 실제 뉴스 내용을 바탕으로 해주세요.
"""
        
        try:
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system", 
                        "content": "당신은 뉴스 분석 전문가입니다. 주어진 뉴스 클러스터 정보를 바탕으로 객관적이고 통찰력 있는 분석을 제공합니다."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=3000,
                temperature=0.3
            )
            
            analysis_text = response.choices[0].message.content
            
            # 분석 결과를 구조화
            return {
                "ai_analysis": analysis_text,
                "analysis_timestamp": datetime.now().isoformat(),
                "model_used": "gpt-4",
                "tokens_used": response.usage.total_tokens if hasattr(response, 'usage') else 0
            }
            
        except Exception as e:
            self.logger.error(f"AI 분석 실패: {e}")
            return {
                "ai_analysis": "AI 분석을 수행할 수 없습니다. 수집된 뉴스 클러스터를 바탕으로 기본 분석을 제공합니다.",
                "analysis_timestamp": datetime.now().isoformat(),
                "model_used": "fallback",
                "error": str(e)
            }
    
    async def _create_final_period_report(
        self,
        report_id: str,
        request: AutoReportRequest,
        period_start: str,
        period_end: str,
        articles_by_category: Dict[str, List[Dict[str, Any]]],
        clusters_by_category: Dict[str, List[NewsCluster]],
        ai_analysis: Dict[str, Any],
        start_time: float
    ) -> PeriodReport:
        """최종 기간별 레포트 생성"""
        
        total_articles = sum(len(articles) for articles in articles_by_category.values())
        
        # AI 분석 결과 파싱
        ai_text = ai_analysis.get("ai_analysis", "")
        
        # 카테고리별 요약 생성
        category_summaries = []
        for category, clusters in clusters_by_category.items():
            if clusters:
                top_clusters = clusters[:3]  # 상위 3개 클러스터
                
                summary = CategorySummary(
                    category=category,
                    total_articles=len(articles_by_category.get(category, [])),
                    top_clusters=top_clusters,
                    key_developments=[cluster.title for cluster in top_clusters],
                    sentiment_trend="neutral"  # 기본값
                )
                category_summaries.append(summary)
        
        # 주요 이벤트 타임라인 생성 (간단한 버전)
        timeline = []
        for category, clusters in clusters_by_category.items():
            for i, cluster in enumerate(clusters[:2]):  # 카테고리당 상위 2개
                event = TimelineEvent(
                    date=period_start,  # 실제로는 기사 날짜를 분석해야 함
                    title=cluster.title,
                    description=f"{category} 분야의 주요 이슈",
                    importance=5 - i,  # 순서에 따라 중요도 설정
                    related_cluster_ids=[cluster.id],
                    category=category
                )
                timeline.append(event)
        
        # 인사이트 생성
        insights = [
            PeriodInsight(
                type="summary",
                title="기간 분석 요약",
                description=ai_text[:200] + "..." if len(ai_text) > 200 else ai_text,
                confidence=0.8,
                supporting_clusters=[]
            )
        ]
        
        # 키워드 분석
        all_keywords = []
        for clusters in clusters_by_category.values():
            for cluster in clusters:
                all_keywords.extend(cluster.keywords)
        
        keyword_counts = Counter(all_keywords)
        top_keywords = [
            {"keyword": keyword, "count": count, "category": "general"}
            for keyword, count in keyword_counts.most_common(10)
        ]
        
        return PeriodReport(
            id=report_id,
            report_type=request.report_type,
            company_name=request.company_name,
            company_code=request.company_code,
            period_start=period_start,
            period_end=period_end,
            generated_at=datetime.now().isoformat(),
            total_articles_analyzed=total_articles,
            categories_covered=list(articles_by_category.keys()),
            analysis_duration_seconds=round(time.time() - start_time, 2),
            executive_summary=ai_text.split("\\n")[0] if ai_text else "기간별 뉴스 분석 완료",
            key_highlights=[
                f"총 {total_articles}개 기사 분석",
                f"{len(category_summaries)}개 카테고리 다룸",
                f"{len(timeline)}개 주요 이벤트 식별",
                f"{len(top_keywords)}개 핵심 키워드 추출"
            ],
            category_summaries=category_summaries,
            timeline=timeline,
            insights=insights,
            top_keywords=top_keywords,
            sentiment_analysis={
                "overall_sentiment": "neutral",
                "positive_ratio": 0.4,
                "negative_ratio": 0.3,
                "neutral_ratio": 0.3
            },
            trend_analysis={
                "primary_trends": [cluster.title for clusters in clusters_by_category.values() for cluster in clusters[:1]],
                "emerging_topics": [],
                "declining_topics": []
            }
        )