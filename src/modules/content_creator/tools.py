"""
콘텐츠 제작자 지원 도구

콘텐츠 제작 워크플로우를 지원하는 도구 모음
"""

import os
import json
import base64
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import textwrap
from PIL import Image, ImageDraw, ImageFont
import numpy as np

class ContentAssistant:
    """콘텐츠 제작을 지원하는 도구 모음"""
    
    def __init__(self):
        """콘텐츠 어시스턴트 초기화"""
        # 캐시 디렉토리 확인
        self.cache_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "cache")
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # 결과물 저장 디렉토리
        self.output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "output")
        os.makedirs(self.output_dir, exist_ok=True)
    
    def generate_content_brief(self, 
                             issue_data: Dict[str, Any]) -> Dict[str, Any]:
        """이슈 데이터를 기반으로 콘텐츠 개요 생성
        
        Args:
            issue_data: 이슈 분석 데이터
            
        Returns:
            콘텐츠 개요 정보
        """
        # 이슈 요약 정보 추출
        summary = issue_data.get("issue_summary", {})
        title = summary.get("title", "이슈 분석")
        summary_text = summary.get("summary_text", "")
        keywords = summary.get("keywords", [])
        perspectives = summary.get("perspectives", [])
        key_quotes = summary.get("key_quotes", [])
        
        # 이슈 흐름 정보 추출
        flow = issue_data.get("issue_flow", {})
        key_events = flow.get("key_events", [])
        phases = flow.get("phases", [])
        
        # 콘텐츠 주제 제안
        topic_suggestions = [
            f"{title}에 대한 심층 분석",
            f"{keywords[0] if keywords else '이슈'}: 무엇이 문제인가?",
            f"{title} - 전문가들의 관점",
            f"{keywords[0] if keywords else '이슈'}의 현재와 미래"
        ]
        
        # 콘텐츠 구조 제안
        content_structure = []
        
        # 서론 구성
        intro = {
            "section": "서론",
            "description": "이슈 배경 및 중요성 소개",
            "key_points": [
                "이슈의 등장 배경",
                "왜 지금 중요한지",
                "주요 이해관계자 소개"
            ],
            "suggested_content": summary_text[:200] + "..." if len(summary_text) > 200 else summary_text
        }
        content_structure.append(intro)
        
        # 본론 구성 (이슈 단계 또는 관점 기반)
        if phases:
            for i, phase in enumerate(phases):
                section = {
                    "section": f"본론 {i+1}: {phase.get('name', '단계')}",
                    "description": f"이슈의 {phase.get('name', '단계')} 단계 분석",
                    "key_points": [
                        f"{phase.get('name', '이슈 단계')}에서 발생한 주요 사건",
                        "관련 주요 인물 및 조직의 입장",
                        "주요 쟁점 및 영향"
                    ],
                    "suggested_content": (f"이 단계는 {phase.get('start_time', '')}부터 "
                                        f"{phase.get('end_time', '')}까지 진행되었으며, "
                                        f"{phase.get('news_count', 0)}건의 관련 뉴스가 보도되었습니다.")
                }
                content_structure.append(section)
        elif perspectives:
            for i, perspective in enumerate(perspectives[:3]):
                source = perspective.get("source", "관계자")
                perspective_type = perspective.get("type", "")
                title = f"{source} 관점" if perspective_type == "person/org" else f"{source} 보도 관점"
                
                section = {
                    "section": f"본론 {i+1}: {title}",
                    "description": f"{title}에서 바라본 이슈 분석",
                    "key_points": perspective.get("keywords", [])[:3],
                    "suggested_content": perspective.get("sample_quote", "") or perspective.get("sample_title", "")
                }
                content_structure.append(section)
        else:
            # 기본 본론 구조
            section = {
                "section": "본론: 이슈 분석",
                "description": "이슈의 주요 측면 분석",
                "key_points": keywords[:3] if keywords else ["주요 쟁점", "관련 사례", "전문가 의견"],
                "suggested_content": "이슈의 핵심 내용과 다양한 관점을 분석합니다."
            }
            content_structure.append(section)
        
        # 결론 구성
        conclusion = {
            "section": "결론",
            "description": "이슈 요약 및 전망",
            "key_points": [
                "핵심 쟁점 요약",
                "향후 전망",
                "시사점"
            ],
            "suggested_content": "이슈의 핵심 내용을 요약하고 향후 전개 방향을 전망합니다."
        }
        content_structure.append(conclusion)
        
        # 주요 인용구 추출
        quotes = []
        for quote in key_quotes[:5]:
            quotes.append({
                "quote": quote.get("quotation", ""),
                "source": quote.get("source", "관계자"),
                "provider": quote.get("provider", ""),
                "date": quote.get("published_at", "")[:10] if quote.get("published_at") else ""
            })
        
        # 주요 통계 및 사실 추출 (여기서는 간단히 이벤트 기반)
        facts = []
        for event in key_events[:5]:
            facts.append({
                "fact": event.get("title", ""),
                "date": event.get("timestamp", ""),
                "importance": event.get("importance", 0),
                "source": "이슈 흐름 분석"
            })
        
        # 결과 구성
        brief = {
            "title": title,
            "keywords": keywords[:10],
            "topic_suggestions": topic_suggestions,
            "content_structure": content_structure,
            "key_quotes": quotes,
            "key_facts": facts,
            "generated_at": datetime.now().isoformat()
        }
        
        return brief
    
    def create_quote_image(self, 
                         quote: str, 
                         source: str = "", 
                         width: int = 1200, 
                         height: int = 630) -> str:
        """인용구 이미지 생성
        
        Args:
            quote: 인용 문구
            source: 출처
            width: 이미지 너비
            height: 이미지 높이
            
        Returns:
            Base64 인코딩된 이미지 데이터
        """
        # 기본 이미지 생성
        image = Image.new('RGB', (width, height), color=(255, 255, 255))
        draw = ImageDraw.Draw(image)
        
        # 배경 디자인
        draw.rectangle([(0, 0), (width, height)], fill=(240, 242, 245))
        draw.rectangle([(20, 20), (width-20, height-20)], fill=(255, 255, 255), outline=(200, 200, 200), width=2)
        
        # 인용 부호 추가
        draw.text((50, 50), '"', fill=(80, 80, 80), font_size=100)
        
        # 텍스트 래핑
        quote_lines = textwrap.wrap(quote, width=40)
        
        # 인용구 텍스트 추가
        y_position = 120
        for line in quote_lines:
            draw.text((100, y_position), line, fill=(50, 50, 50), font_size=36)
            y_position += 50
        
        # 출처 텍스트 추가
        if source:
            draw.text((100, height - 100), f"- {source}", fill=(100, 100, 100), font_size=30)
        
        # 이미지를 메모리에 저장
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        
        # 이미지를 파일로 저장
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        file_path = os.path.join(self.output_dir, f"quote_{timestamp}.png")
        image.save(file_path, format="PNG")
        
        # Base64 인코딩
        image_data = base64.b64encode(buffer.read()).decode("utf-8")
        return f"data:image/png;base64,{image_data}"
    
    def create_timeline_image(self, 
                           events: List[Dict[str, Any]], 
                           title: str = "이슈 타임라인",
                           width: int = 1200, 
                           height: int = 800) -> str:
        """타임라인 이미지 생성
        
        Args:
            events: 이벤트 목록 (timestamp, title, importance 필드 포함)
            title: 타임라인 제목
            width: 이미지 너비
            height: 이미지 높이
            
        Returns:
            Base64 인코딩된 이미지 데이터
        """
        if not events:
            return ""
        
        # 이벤트 시간 순 정렬
        sorted_events = sorted(events, key=lambda x: x.get("timestamp", ""))
        
        # 날짜 변환
        dates = []
        for event in sorted_events:
            timestamp = event.get("timestamp", "")
            if isinstance(timestamp, str):
                try:
                    date = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                except:
                    date = datetime.now()
            else:
                date = timestamp
            dates.append(date)
        
        # Matplotlib 그래프 생성
        plt.figure(figsize=(width/100, height/100), dpi=100)
        
        # 타임라인 그리기
        levels = []
        for i in range(len(dates)):
            # 중첩 방지를 위한 레벨 계산
            level = 0
            for j in range(len(dates[:i])):
                if (dates[i] - dates[j]).days < 5:
                    level = max(level, levels[j] + 1)
            levels.append(level)
        
        # 타임라인 그리기
        for i, (date, event, level) in enumerate(zip(dates, sorted_events, levels)):
            importance = event.get("importance", 1)
            marker_size = max(importance * 5, 10)
            
            plt.plot([date], [level], 'o', markersize=marker_size, color='#1f77b4')
            plt.annotate(
                event.get("title", ""),
                (date, level),
                xytext=(10, 0),
                textcoords="offset points",
                ha='left',
                va='center',
                fontsize=10,
                wrap=True
            )
        
        # 그래프 스타일 설정
        plt.grid(False)
        plt.yticks([])
        plt.title(title, fontsize=16)
        plt.xlabel("날짜", fontsize=12)
        
        # x축 날짜 포맷 설정
        plt.gcf().autofmt_xdate()
        
        # 여백 조정
        plt.tight_layout()
        
        # 이미지를 메모리에 저장
        buffer = BytesIO()
        plt.savefig(buffer, format="PNG", bbox_inches="tight")
        plt.close()
        
        # 이미지를 파일로 저장
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        file_path = os.path.join(self.output_dir, f"timeline_{timestamp}.png")
        buffer.seek(0)
        with open(file_path, 'wb') as f:
            f.write(buffer.read())
        
        # Base64 인코딩
        buffer.seek(0)
        image_data = base64.b64encode(buffer.read()).decode("utf-8")
        
        return f"data:image/png;base64,{image_data}"
    
    def create_statistics_image(self, 
                             data: Dict[str, List[float]], 
                             title: str = "주요 통계",
                             chart_type: str = "bar", 
                             width: int = 1000, 
                             height: int = 600) -> str:
        """통계 차트 이미지 생성
        
        Args:
            data: 차트 데이터 (라벨: 값 리스트 형식)
            title: 차트 제목
            chart_type: 차트 유형 (bar, line, pie)
            width: 이미지 너비
            height: 이미지 높이
            
        Returns:
            Base64 인코딩된 이미지 데이터
        """
        plt.figure(figsize=(width/100, height/100), dpi=100)
        
        if chart_type == "bar":
            # 바 차트
            labels = list(data.keys())
            values = [data[label][0] if isinstance(data[label], list) and data[label] else 0 for label in labels]
            
            plt.bar(labels, values, color='#1f77b4')
            plt.xlabel("항목", fontsize=12)
            plt.ylabel("값", fontsize=12)
            plt.xticks(rotation=45, ha="right")
            
        elif chart_type == "line":
            # 라인 차트
            for label, values in data.items():
                if isinstance(values, list) and values:
                    x = range(len(values))
                    plt.plot(x, values, marker='o', linestyle='-', linewidth=2, label=label)
            
            plt.xlabel("시점", fontsize=12)
            plt.ylabel("값", fontsize=12)
            plt.legend()
            
        elif chart_type == "pie":
            # 파이 차트
            labels = list(data.keys())
            values = [data[label][0] if isinstance(data[label], list) and data[label] else 0 for label in labels]
            
            plt.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
            plt.axis('equal')
        
        # 차트 스타일 설정
        plt.title(title, fontsize=16)
        plt.grid(True, linestyle="--", alpha=0.7)
        plt.tight_layout()
        
        # 이미지를 메모리에 저장
        buffer = BytesIO()
        plt.savefig(buffer, format="PNG", bbox_inches="tight")
        plt.close()
        
        # 이미지를 파일로 저장
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        file_path = os.path.join(self.output_dir, f"stats_{timestamp}.png")
        buffer.seek(0)
        with open(file_path, 'wb') as f:
            f.write(buffer.read())
        
        # Base64 인코딩
        buffer.seek(0)
        image_data = base64.b64encode(buffer.read()).decode("utf-8")
        
        return f"data:image/png;base64,{image_data}"
    
    def create_perspective_comparison(self, 
                                  perspectives: List[Dict[str, Any]],
                                  title: str = "관점 비교",
                                  width: int = 1000, 
                                  height: int = 600) -> str:
        """관점 비교 차트 생성
        
        Args:
            perspectives: 관점 목록 (source, keywords, type 필드 포함)
            title: 차트 제목
            width: 이미지 너비
            height: 이미지 높이
            
        Returns:
            Base64 인코딩된 이미지 데이터
        """
        if not perspectives:
            return ""
        
        # 관점별 핵심 키워드 추출
        sources = []
        keywords_list = []
        
        for perspective in perspectives[:5]:  # 최대 5개 관점
            source = perspective.get("source", "관계자")
            sources.append(source)
            
            # 키워드 추출 (최대 3개)
            keywords = perspective.get("keywords", [])[:3]
            while len(keywords) < 3:
                keywords.append("")
                
            keywords_list.append(keywords)
        
        # Matplotlib 표 생성
        fig, ax = plt.subplots(figsize=(width/100, height/100), dpi=100)
        
        # 표 데이터
        table_data = []
        for keywords in keywords_list:
            table_data.append(keywords)
        
        # 테이블 생성
        table = ax.table(
            cellText=table_data,
            rowLabels=sources,
            colLabels=["핵심 키워드 1", "핵심 키워드 2", "핵심 키워드 3"],
            loc='center',
            cellLoc='center'
        )
        
        # 테이블 스타일링
        table.auto_set_font_size(False)
        table.set_fontsize(12)
        table.scale(1, 2)
        
        # 축 숨기기
        ax.axis('off')
        
        # 제목 설정
        plt.title(title, fontsize=16, pad=30)
        plt.tight_layout()
        
        # 이미지를 메모리에 저장
        buffer = BytesIO()
        plt.savefig(buffer, format="PNG", bbox_inches="tight")
        plt.close()
        
        # 이미지를 파일로 저장
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        file_path = os.path.join(self.output_dir, f"perspectives_{timestamp}.png")
        buffer.seek(0)
        with open(file_path, 'wb') as f:
            f.write(buffer.read())
        
        # Base64 인코딩
        buffer.seek(0)
        image_data = base64.b64encode(buffer.read()).decode("utf-8")
        
        return f"data:image/png;base64,{image_data}"
    
    def verify_facts(self, 
                  facts: List[Dict[str, Any]], 
                  news_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """사실 검증 및 신뢰도 평가
        
        Args:
            facts: 검증할 사실 목록
            news_list: 뉴스 기사 목록
            
        Returns:
            검증 결과가 추가된 사실 목록
        """
        verified_facts = []
        
        for fact in facts:
            fact_text = fact.get("fact", "")
            
            # 관련 뉴스 검색
            related_news = []
            for news in news_list:
                title = news.get("title", "")
                content = news.get("content", "")
                
                # 간단한 관련성 검사 (실제로는 더 복잡한 알고리즘 필요)
                if fact_text in title or fact_text in content:
                    related_news.append({
                        "title": title,
                        "provider": news.get("provider", ""),
                        "published_at": news.get("published_at", "")
                    })
            
            # 신뢰도 점수 계산 (언론사 수에 기반한 간단한 휴리스틱)
            providers = set([news.get("provider", "") for news in related_news])
            confidence_score = min(len(providers) * 20, 100)  # 언론사당 20점, 최대 100점
            
            # 검증 결과 추가
            verified_fact = dict(fact)
            verified_fact["confidence_score"] = confidence_score
            verified_fact["related_news_count"] = len(related_news)
            verified_fact["unique_sources"] = len(providers)
            verified_fact["related_news"] = related_news[:3]  # 최대 3개 관련 뉴스
            
            # 신뢰도 레벨 추가
            if confidence_score >= 80:
                verified_fact["confidence_level"] = "높음"
            elif confidence_score >= 50:
                verified_fact["confidence_level"] = "중간"
            else:
                verified_fact["confidence_level"] = "낮음"
            
            verified_facts.append(verified_fact)
        
        return verified_facts
    
    def export_content_package(self, 
                            issue_data: Dict[str, Any],
                            format: str = "json") -> str:
        """콘텐츠 패키지 내보내기
        
        Args:
            issue_data: 이슈 분석 데이터
            format: 내보내기 형식 (json, md, html)
            
        Returns:
            파일 경로 또는 내용
        """
        # 콘텐츠 브리프 생성
        brief = self.generate_content_brief(issue_data)
        
        # 이슈 요약 정보 추출
        summary = issue_data.get("issue_summary", {})
        
        # 시각 자료 생성
        visuals = {}
        
        # 인용구 이미지 생성
        if summary.get("key_quotes"):
            quote = summary["key_quotes"][0]
            quote_text = quote.get("quotation", "")
            source = quote.get("source", "")
            visuals["quote_image"] = self.create_quote_image(quote_text, source)
        
        # 타임라인 이미지 생성
        if "issue_flow" in issue_data and issue_data["issue_flow"].get("key_events"):
            visuals["timeline_image"] = self.create_timeline_image(
                issue_data["issue_flow"]["key_events"],
                "이슈 주요 이벤트 타임라인"
            )
        
        # 관점 비교 이미지 생성
        if summary.get("perspectives"):
            visuals["perspectives_image"] = self.create_perspective_comparison(
                summary["perspectives"],
                "이슈 관련 다양한 관점"
            )
        
        # 형식에 따른 내보내기
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        if format == "json":
            # JSON 형식으로 내보내기
            export_data = {
                "brief": brief,
                "visuals": visuals,
                "issue_data": issue_data,
                "exported_at": datetime.now().isoformat()
            }
            
            file_path = os.path.join(self.output_dir, f"content_package_{timestamp}.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            return file_path
        
        elif format == "md":
            # 마크다운 형식으로 내보내기
            title = brief.get("title", "이슈 분석")
            
            md_content = f"# {title}\n\n"
            md_content += f"*생성일: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
            
            # 키워드
            md_content += "## 키워드\n\n"
            md_content += ", ".join(brief.get("keywords", [])) + "\n\n"
            
            # 콘텐츠 구조
            md_content += "## 콘텐츠 구조\n\n"
            for section in brief.get("content_structure", []):
                md_content += f"### {section.get('section', '')}\n\n"
                md_content += f"{section.get('description', '')}\n\n"
                
                md_content += "핵심 포인트:\n"
                for point in section.get("key_points", []):
                    md_content += f"- {point}\n"
                md_content += "\n"
                
                md_content += f"제안 내용: {section.get('suggested_content', '')}\n\n"
            
            # 주요 인용구
            md_content += "## 주요 인용구\n\n"
            for quote in brief.get("key_quotes", []):
                md_content += f"> {quote.get('quote', '')}\n>\n"
                md_content += f"> -- {quote.get('source', '')}, {quote.get('provider', '')} ({quote.get('date', '')})\n\n"
            
            # 주요 사실
            md_content += "## 주요 사실 및 통계\n\n"
            for fact in brief.get("key_facts", []):
                md_content += f"- {fact.get('fact', '')}\n"
                if fact.get('date'):
                    md_content += f"  - 날짜: {fact.get('date', '')}\n"
                md_content += f"  - 출처: {fact.get('source', '')}\n\n"
            
            file_path = os.path.join(self.output_dir, f"content_brief_{timestamp}.md")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
            
            return file_path
        
        elif format == "html":
            # HTML 형식으로 내보내기 (간단한 예시)
            title = brief.get("title", "이슈 분석")
            
            html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; }}
        h1, h2, h3 {{ color: #333; }}
        .container {{ max-width: 1000px; margin: 0 auto; }}
        .quote {{ background-color: #f8f9fa; border-left: 4px solid #ccc; padding: 15px; margin: 15px 0; }}
        .quote-source {{ text-align: right; font-style: italic; }}
        .fact {{ margin-bottom: 15px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        <p><em>생성일: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</em></p>
        
        <h2>키워드</h2>
        <p>{", ".join(brief.get("keywords", []))}</p>
"""
            
            # 콘텐츠 구조
            html_content += "<h2>콘텐츠 구조</h2>\n"
            for section in brief.get("content_structure", []):
                html_content += f"<h3>{section.get('section', '')}</h3>\n"
                html_content += f"<p>{section.get('description', '')}</p>\n"
                
                html_content += "<p><strong>핵심 포인트:</strong></p>\n<ul>\n"
                for point in section.get("key_points", []):
                    html_content += f"<li>{point}</li>\n"
                html_content += "</ul>\n"
                
                html_content += f"<p><strong>제안 내용:</strong> {section.get('suggested_content', '')}</p>\n"
            
            # 주요 인용구
            html_content += "<h2>주요 인용구</h2>\n"
            for quote in brief.get("key_quotes", []):
                html_content += f"""<div class="quote">
    <p>{quote.get('quote', '')}</p>
    <p class="quote-source">— {quote.get('source', '')}, {quote.get('provider', '')} ({quote.get('date', '')})</p>
</div>\n"""
            
            # 주요 사실
            html_content += "<h2>주요 사실 및 통계</h2>\n<div class='facts'>\n"
            for fact in brief.get("key_facts", []):
                html_content += f"""<div class="fact">
    <p><strong>{fact.get('fact', '')}</strong></p>
    <p>날짜: {fact.get('date', '')}<br>
    출처: {fact.get('source', '')}</p>
</div>\n"""
            
            html_content += """
    </div>
</body>
</html>"""
            
            file_path = os.path.join(self.output_dir, f"content_brief_{timestamp}.html")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return file_path
        
        else:
            return "지원하지 않는 형식입니다."