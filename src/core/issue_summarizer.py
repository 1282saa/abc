"""
이슈 요약 및 인사이트 생성 모듈

이슈에 대한 종합적인 요약과 인사이트를 생성하는 기능을 제공
"""

from typing import Dict, List, Any, Optional
import re
import numpy as np
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer
from datetime import datetime

# 프로젝트 루트 디렉토리 찾기
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

class IssueSummarizer:
    """이슈를 요약하고 인사이트를 생성하는 클래스"""
    
    def __init__(self):
        """이슈 요약 엔진 초기화"""
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            min_df=1,
            max_df=0.9,
            stop_words='english'  # 한국어 불용어 처리는 별도로 구현 필요
        )
    
    def _preprocess_content(self, content: str) -> str:
        """텍스트 전처리
        
        Args:
            content: 원본 텍스트
            
        Returns:
            전처리된 텍스트
        """
        # HTML 태그 제거
        text = re.sub(r'<[^>]+>', '', content)
        
        # 특수문자, 불필요한 기호 제거
        text = re.sub(r'[^\w\s\.\,\'\"\!\?]', ' ', text)
        
        # 여러 공백 제거
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _extract_sentences(self, content: str) -> List[str]:
        """텍스트에서 문장 추출
        
        Args:
            content: 텍스트 내용
            
        Returns:
            문장 목록
        """
        # 간단한 문장 분리 (마침표, 물음표, 느낌표 기준)
        # 실제 구현에서는 KSS와 같은 한국어 문장 분리 라이브러리 사용 권장
        sentences = re.split(r'(?<=[.!?])\s+', content)
        return [s.strip() for s in sentences if s.strip()]
    
    def extractive_summarize(self, 
                           news_list: List[Dict[str, Any]], 
                           max_sentences: int = 10) -> List[str]:
        """추출적 요약 생성
        
        Args:
            news_list: 이슈 관련 뉴스 목록
            max_sentences: 최대 요약 문장 수
            
        Returns:
            중요 문장 목록
        """
        if not news_list:
            return []
        
        # 모든 뉴스 내용 결합 및 문장 추출
        all_text = " ".join([news.get("content", "") for news in news_list])
        cleaned_text = self._preprocess_content(all_text)
        sentences = self._extract_sentences(cleaned_text)
        
        if len(sentences) <= max_sentences:
            return sentences
        
        # TF-IDF 기반 문장 중요도 계산
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(sentences)
        
        # 각 문장의 평균 TF-IDF 점수 계산
        sentence_scores = []
        for i in range(len(sentences)):
            score = np.mean(tfidf_matrix[i].toarray()[0])
            sentence_scores.append((i, score))
        
        # 점수 기준 상위 문장 선택
        top_sentences = sorted(sentence_scores, key=lambda x: x[1], reverse=True)[:max_sentences]
        top_indices = [idx for idx, _ in sorted(top_sentences, key=lambda x: x[0])]
        
        return [sentences[i] for i in top_indices]
    
    def extract_key_quotes(self, 
                         quotations: List[Dict[str, Any]], 
                         max_quotes: int = 5) -> List[Dict[str, Any]]:
        """주요 인용문 추출
        
        Args:
            quotations: 이슈 관련 인용문 목록
            max_quotes: 최대 인용문 수
            
        Returns:
            주요 인용문 목록
        """
        if not quotations or len(quotations) <= max_quotes:
            return quotations
        
        # 인용문별 점수 계산 (길이와 출처의 신뢰도 기반)
        scored_quotes = []
        for quote in quotations:
            content = quote.get("quotation", "")
            source = quote.get("source", "")
            
            # 단순 점수 계산 (실제로는 더 복잡한 모델 사용 가능)
            score = len(content) * 0.3  # 긴 인용문 선호
            
            # 인물/조직 출처 추가 점수
            if source and len(source) > 1:
                score += 10
            
            scored_quotes.append((quote, score))
        
        # 점수 기준 상위 인용문 선택
        top_quotes = sorted(scored_quotes, key=lambda x: x[1], reverse=True)[:max_quotes]
        
        return [quote for quote, _ in top_quotes]
    
    def identify_perspectives(self, 
                           news_list: List[Dict[str, Any]],
                           quotations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """다양한 관점 식별
        
        Args:
            news_list: 이슈 관련 뉴스 목록
            quotations: 이슈 관련 인용문 목록
            
        Returns:
            관점 목록
        """
        # 언론사별 분류
        providers = {}
        for news in news_list:
            provider = news.get("provider", "")
            if provider not in providers:
                providers[provider] = []
            providers[provider].append(news)
        
        # 출처별 인용문 분류
        sources = {}
        for quote in quotations:
            source = quote.get("source", "")
            if source not in sources:
                sources[source] = []
            sources[source].append(quote)
        
        # 관점 도출
        perspectives = []
        
        # 주요 언론사 관점
        for provider, provider_news in providers.items():
            if len(provider_news) < 2:
                continue
                
            # 해당 언론사의 키워드 분석
            titles = [news.get("title", "") for news in provider_news]
            keywords = self._extract_keywords(" ".join(titles))
            
            perspective = {
                "type": "media",
                "source": provider,
                "keywords": keywords,
                "article_count": len(provider_news),
                "sample_title": provider_news[0].get("title", "")
            }
            
            perspectives.append(perspective)
        
        # 주요 인물/조직 관점
        for source, source_quotes in sources.items():
            if len(source_quotes) < 2 or not source:
                continue
                
            # 해당 출처의 인용문 분석
            quotes_text = [quote.get("quotation", "") for quote in source_quotes]
            keywords = self._extract_keywords(" ".join(quotes_text))
            
            perspective = {
                "type": "person/org",
                "source": source,
                "keywords": keywords,
                "quote_count": len(source_quotes),
                "sample_quote": source_quotes[0].get("quotation", "")
            }
            
            perspectives.append(perspective)
        
        # 가장 주요한 관점만 선택
        return sorted(perspectives, key=lambda x: x.get("article_count", 0) + x.get("quote_count", 0) * 2, reverse=True)[:5]
    
    def _extract_keywords(self, text: str, top_n: int = 5) -> List[str]:
        """텍스트에서 핵심 키워드 추출
        
        Args:
            text: 분석할 텍스트
            top_n: 추출할 키워드 수
            
        Returns:
            핵심 키워드 목록
        """
        # 간단한 단어 빈도 기반 키워드 추출
        words = re.findall(r'\b\w{2,}\b', text.lower())
        word_counts = Counter(words)
        
        # 가장 많이 등장한 단어 추출
        top_words = word_counts.most_common(top_n)
        
        return [word for word, _ in top_words]
    
    def generate_issue_summary(self, 
                             news_list: List[Dict[str, Any]], 
                             flow_analysis: Dict[str, Any],
                             quotations: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """이슈 종합 요약 및 인사이트 생성
        
        Args:
            news_list: 이슈 관련 뉴스 목록
            flow_analysis: 이슈 흐름 분석 결과
            quotations: 이슈 관련 인용문 목록
            
        Returns:
            이슈 요약 결과
        """
        if not quotations:
            quotations = []
        
        # 이슈 시작/종료 시간 추출
        timeline = flow_analysis.get("timeline", [])
        start_time = min([item["timestamp"] for item in timeline]) if timeline else datetime.now()
        end_time = max([item["timestamp"] for item in timeline]) if timeline else datetime.now()
        
        # 추출적 요약 생성
        summary_sentences = self.extractive_summarize(news_list)
        
        # 주요 인용문 추출
        key_quotes = self.extract_key_quotes(quotations)
        
        # 관점 식별
        perspectives = self.identify_perspectives(news_list, quotations)
        
        # 주요 이벤트 시점
        key_events = flow_analysis.get("key_events", [])
        
        # 이슈 단계 (서론, 본론, 결론 등)
        if "timeline" in flow_analysis and len(flow_analysis["timeline"]) >= 3:
            from issue_flow import IssueFlowAnalyzer
            flow_analyzer = IssueFlowAnalyzer()
            phases = flow_analyzer.segment_issue_phases(flow_analysis)
        else:
            phases = []
        
        # 종합 요약
        summary = {
            "title": self._generate_summary_title(news_list),
            "time_range": {
                "start": start_time,
                "end": end_time,
                "duration_hours": (end_time - start_time).total_seconds() / 3600
            },
            "article_count": len(news_list),
            "main_providers": self._get_main_providers(news_list),
            "summary_text": " ".join(summary_sentences),
            "key_quotes": key_quotes,
            "perspectives": perspectives,
            "key_events": key_events,
            "phases": phases,
            "keywords": self._extract_keywords(" ".join([news.get("title", "") + " " + news.get("content", "") for news in news_list]), 10)
        }
        
        return summary
    
    def _generate_summary_title(self, news_list: List[Dict[str, Any]]) -> str:
        """이슈 요약 제목 생성
        
        Args:
            news_list: 이슈 관련 뉴스 목록
            
        Returns:
            요약 제목
        """
        if not news_list:
            return "이슈 요약"
        
        # 가장 많이 등장하는 단어들을 기반으로 제목 생성
        titles = [news.get("title", "") for news in news_list]
        combined_title = " ".join(titles)
        
        # 주요 키워드 추출
        keywords = self._extract_keywords(combined_title, 3)
        
        # 첫 번째 뉴스 제목 활용
        first_title = news_list[0].get("title", "")
        
        # 키워드와 첫 번째 제목을 결합하여 요약 제목 생성
        return f"[{' / '.join(keywords)}] {first_title}"
    
    def _get_main_providers(self, news_list: List[Dict[str, Any]], top_n: int = 3) -> List[str]:
        """주요 언론사 추출
        
        Args:
            news_list: 이슈 관련 뉴스 목록
            top_n: 추출할 언론사 수
            
        Returns:
            주요 언론사 목록
        """
        providers = [news.get("provider", "") for news in news_list]
        provider_counts = Counter(providers)
        
        # 가장 많은 기사를 보도한 언론사 추출
        top_providers = provider_counts.most_common(top_n)
        
        return [provider for provider, _ in top_providers]