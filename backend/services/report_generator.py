"""
기업 레포트 생성 서비스

기업의 뉴스 데이터를 분석하여 AI 기반 인사이트 레포트를 생성합니다.
"""

import asyncio
import json
import re
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, AsyncGenerator, Tuple
import openai
import sys
from pathlib import Path

# 프로젝트 루트 디렉토리 설정
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.api.clients.bigkinds import BigKindsClient
from backend.api.models.report_models import (
    ReportRequest, CompanyReport, ReportSection, CitationSource, 
    ReportMetadata, ReportStreamData, ReportPeriodType, REPORT_TEMPLATES
)
from backend.utils.logger import setup_logger

class ReportGenerator:
    """기업 레포트 생성기"""
    
    def __init__(self, openai_api_key: str, bigkinds_client: BigKindsClient):
        """
        Args:
            openai_api_key: OpenAI API 키
            bigkinds_client: BigKinds 클라이언트
        """
        self.openai_api_key = openai_api_key
        self.bigkinds_client = bigkinds_client
        self.logger = setup_logger("services.report_generator")
        
        # OpenAI 클라이언트 초기화
        openai.api_key = self.openai_api_key
        
    async def generate_report_stream(
        self, 
        request: ReportRequest
    ) -> AsyncGenerator[ReportStreamData, None]:
        """
        스트리밍 방식으로 레포트 생성
        
        Args:
            request: 레포트 생성 요청
            
        Yields:
            ReportStreamData: 진행 상황과 결과 데이터
        """
        start_time = time.time()
        
        try:
            # 1단계: 뉴스 데이터 수집
            yield ReportStreamData(
                type="progress",
                step="뉴스 데이터를 수집하고 있습니다...",
                progress=10
            )
            
            articles = await self._collect_news_articles(request)
            
            if not articles:
                yield ReportStreamData(
                    type="error",
                    error=f"지정된 기간({request.date_from} ~ {request.date_to})에 {request.company_name} 관련 뉴스를 찾을 수 없습니다."
                )
                return
            
            yield ReportStreamData(
                type="progress", 
                step=f"{len(articles)}개의 관련 기사를 발견했습니다.",
                progress=25
            )
            
            # 2단계: 기사 내용 분석 및 전처리
            yield ReportStreamData(
                type="progress",
                step="기사 내용을 분석하고 중요 정보를 추출하고 있습니다...",
                progress=40
            )
            
            processed_articles = await self._process_articles(articles)
            citations = self._create_citations(processed_articles)
            
            # 3단계: AI 분석 및 레포트 생성
            yield ReportStreamData(
                type="progress",
                step="AI가 종합적인 분석을 수행하고 인사이트를 도출하고 있습니다...",
                progress=60
            )
            
            # 템플릿 기반 레포트 생성
            template = REPORT_TEMPLATES[request.period_type]
            
            yield ReportStreamData(
                type="progress",
                step=f"{template.name}을 작성하고 있습니다...",
                progress=75
            )
            
            # AI 레포트 생성
            report_content = await self._generate_ai_report(
                request, processed_articles, template
            )
            
            yield ReportStreamData(
                type="progress",
                step="레포트를 완성하고 있습니다...",
                progress=90
            )
            
            # 4단계: 레포트 구조화 및 완성
            report = await self._create_final_report(
                request, report_content, citations, articles, start_time
            )
            
            yield ReportStreamData(
                type="complete",
                step="레포트 생성이 완료되었습니다!",
                progress=100,
                result=report
            )
            
        except Exception as e:
            self.logger.error(f"레포트 생성 중 오류 발생: {e}", exc_info=True)
            yield ReportStreamData(
                type="error",
                error=f"레포트 생성 중 오류가 발생했습니다: {str(e)}"
            )
    
    async def _collect_news_articles(self, request: ReportRequest) -> List[Dict[str, Any]]:
        """뉴스 기사 수집"""
        try:
            # BigKinds API를 통해 기사 검색
            search_result = self.bigkinds_client.search_news(
                query=request.company_name,
                date_from=request.date_from,
                date_to=request.date_to,
                sort="date",
                page_size=min(request.max_articles, 100),
                provider=["서울경제"] if request.company_name else None
            )
            
            articles = search_result.get("return_object", {}).get("documents", [])
            
            # 기사 제목과 내용 필터링 (중복 제거)
            unique_articles = []
            seen_titles = set()
            
            for article in articles:
                title = article.get("title", "")
                if title not in seen_titles and len(title) > 10:
                    seen_titles.add(title)
                    unique_articles.append(article)
                    
                    if len(unique_articles) >= request.max_articles:
                        break
            
            self.logger.info(f"수집된 기사 수: {len(unique_articles)}")
            return unique_articles
            
        except Exception as e:
            self.logger.error(f"뉴스 수집 실패: {e}")
            return []
    
    async def _process_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """기사 내용 전처리 및 분석"""
        processed = []
        
        for i, article in enumerate(articles):
            try:
                # 기사 정보 추출
                processed_article = {
                    "id": article.get("_id", f"article_{i}"),
                    "title": article.get("title", "").strip(),
                    "content": article.get("content", "").strip(),
                    "provider": article.get("provider_name", "알 수 없음"),
                    "published_at": article.get("published_at", ""),
                    "url": article.get("url", ""),
                    "category": article.get("category", []),
                    "summary": article.get("content", "")[:200] + "..." if len(article.get("content", "")) > 200 else article.get("content", "")
                }
                
                # 내용이 있는 기사만 포함
                if processed_article["title"] and (processed_article["content"] or processed_article["summary"]):
                    processed.append(processed_article)
                    
            except Exception as e:
                self.logger.warning(f"기사 처리 실패 (인덱스 {i}): {e}")
                continue
        
        return processed
    
    def _create_citations(self, articles: List[Dict[str, Any]]) -> List[CitationSource]:
        """인용 출처 생성"""
        citations = []
        
        for i, article in enumerate(articles):
            citation = CitationSource(
                id=article["id"],
                title=article["title"],
                url=article.get("url", "#"),
                provider=article["provider"],
                published_at=article["published_at"],
                excerpt=article["summary"]
            )
            citations.append(citation)
        
        return citations
    
    async def _generate_ai_report(
        self, 
        request: ReportRequest, 
        articles: List[Dict[str, Any]], 
        template: Any
    ) -> str:
        """AI를 이용한 레포트 생성"""
        
        # 기사 내용을 하나의 텍스트로 결합
        articles_text = ""
        for i, article in enumerate(articles, 1):
            articles_text += f"\\n\\n[{i}] {article['title']}\\n"
            articles_text += f"언론사: {article['provider']}\\n"
            articles_text += f"날짜: {article['published_at']}\\n"
            articles_text += f"내용: {article['content'][:500]}...\\n"
        
        # 프롬프트 구성
        prompt = template.prompt_template.format(
            company_name=request.company_name,
            date_from=request.date_from,
            date_to=request.date_to
        )
        
        full_prompt = f"""
{prompt}

기사 데이터:
{articles_text}

중요 지침:
1. 각 섹션마다 반드시 관련 기사를 인용하고 [숫자] 형식으로 각주를 표시하세요.
2. 객관적이고 전문적인 어조로 작성하세요.
3. 구체적인 사실과 데이터를 바탕으로 분석하세요.
4. 추측이나 근거 없는 주장은 피하세요.
5. 각 섹션을 명확히 구분하여 작성하세요.

레포트를 작성해주세요:
"""
        
        try:
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system", 
                        "content": "당신은 기업 분석 전문가입니다. 뉴스 기사를 바탕으로 전문적이고 객관적인 기업 분석 레포트를 작성합니다."
                    },
                    {"role": "user", "content": full_prompt}
                ],
                max_tokens=4000,
                temperature=0.3
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            self.logger.error(f"AI 레포트 생성 실패: {e}")
            # 폴백: 기본 레포트 생성
            return await self._generate_fallback_report(request, articles)
    
    async def _generate_fallback_report(
        self, 
        request: ReportRequest, 
        articles: List[Dict[str, Any]]
    ) -> str:
        """AI 실패시 기본 레포트 생성"""
        
        fallback_content = f"""
# {request.company_name} {request.period_type.value.title()} 레포트

## 개요
{request.date_from}부터 {request.date_to}까지의 기간 동안 {request.company_name}와 관련된 {len(articles)}개의 뉴스 기사를 분석했습니다.

## 주요 뉴스 헤드라인
"""
        
        for i, article in enumerate(articles[:10], 1):
            fallback_content += f"\\n{i}. {article['title']} [{i}]"
            fallback_content += f"\\n   - {article['provider']}, {article['published_at']}"
        
        fallback_content += f"""

## 분석 결과
이 기간 동안 {request.company_name}에 대한 언론 보도가 활발했으며, 다양한 측면에서 관심을 받았습니다.

※ 이 레포트는 자동 생성된 기본 형태입니다.
"""
        
        return fallback_content
    
    async def _create_final_report(
        self,
        request: ReportRequest,
        report_content: str,
        citations: List[CitationSource],
        articles: List[Dict[str, Any]],
        start_time: float
    ) -> CompanyReport:
        """최종 레포트 생성"""
        
        # 레포트 내용을 섹션별로 분할
        sections = self._parse_report_sections(report_content)
        
        # 메타데이터 생성
        metadata = ReportMetadata(
            company_name=request.company_name,
            company_code=request.company_code,
            period_type=request.period_type,
            date_from=request.date_from,
            date_to=request.date_to,
            total_articles=len(articles),
            generated_at=datetime.now().isoformat(),
            generation_time_seconds=round(time.time() - start_time, 2),
            model_used="gpt-4"
        )
        
        # 경영진 요약 추출
        executive_summary = self._extract_executive_summary(report_content)
        
        # 키워드 추출
        keywords = self._extract_keywords(articles)
        
        return CompanyReport(
            metadata=metadata,
            executive_summary=executive_summary,
            sections=sections,
            citations=citations,
            keywords=keywords,
            sentiment_analysis={},  # 추후 구현
            stock_impact=None  # 추후 구현
        )
    
    def _parse_report_sections(self, content: str) -> List[ReportSection]:
        """레포트 내용을 섹션별로 파싱"""
        sections = []
        
        # 섹션 분할 (## 또는 **로 시작하는 제목 기준)
        section_pattern = r'(?:^|\n)(?:##?\s*|\\*\\*?)([^\\n]+?)(?:\\*\\*)?\\n'
        matches = re.split(section_pattern, content)
        
        if len(matches) < 3:
            # 섹션 구분이 명확하지 않은 경우 전체를 하나의 섹션으로
            return [ReportSection(
                title="종합 분석",
                content=content,
                key_points=[],
                citations=self._extract_citations_from_text(content)
            )]
        
        for i in range(1, len(matches), 2):
            if i + 1 < len(matches):
                title = matches[i].strip()
                section_content = matches[i + 1].strip()
                
                if title and section_content:
                    # 키 포인트 추출 (- 또는 * 로 시작하는 리스트)
                    key_points = re.findall(r'^[-*]\\s*(.+)$', section_content, re.MULTILINE)
                    
                    # 인용 번호 추출
                    citations = self._extract_citations_from_text(section_content)
                    
                    sections.append(ReportSection(
                        title=title,
                        content=section_content,
                        key_points=key_points[:5],  # 최대 5개
                        citations=citations
                    ))
        
        return sections
    
    def _extract_citations_from_text(self, text: str) -> List[int]:
        """텍스트에서 인용 번호 추출"""
        citation_pattern = r'\\[(\\d+)\\]'
        citations = re.findall(citation_pattern, text)
        return [int(c) for c in citations]
    
    def _extract_executive_summary(self, content: str) -> str:
        """경영진 요약 추출"""
        # 첫 번째 섹션이나 요약 부분을 경영진 요약으로 사용
        lines = content.split('\\n')
        summary_lines = []
        
        for line in lines[:10]:  # 처음 10줄만 확인
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('**'):
                summary_lines.append(line)
                if len(summary_lines) >= 3:
                    break
        
        return ' '.join(summary_lines) if summary_lines else "요약 정보를 생성할 수 없습니다."
    
    def _extract_keywords(self, articles: List[Dict[str, Any]]) -> List[str]:
        """기사에서 주요 키워드 추출"""
        # 간단한 키워드 추출 (제목에서 자주 등장하는 단어)
        word_count = {}
        
        for article in articles:
            title = article.get("title", "")
            # 한글 단어 추출 (2글자 이상)
            words = re.findall(r'[가-힣]{2,}', title)
            
            for word in words:
                if len(word) >= 2:
                    word_count[word] = word_count.get(word, 0) + 1
        
        # 빈도수 기준 상위 키워드 반환
        sorted_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)
        return [word for word, count in sorted_words[:10] if count >= 2]