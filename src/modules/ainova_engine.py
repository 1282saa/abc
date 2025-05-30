"""
AI NOVA 메인 엔진 모듈

빅카인즈 API와 다양한 분석 모듈을 통합하여 이슈 분석 기능을 제공
"""

import time
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple
import logging
import asyncio
import networkx as nx

# 프로젝트 루트 디렉토리 찾기
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.api.bigkinds_client import BigKindsClient
from src.core.issue_clustering import IssueClusterer
from src.core.issue_flow import IssueFlowAnalyzer
from src.core.issue_summarizer import IssueSummarizer
from src.utils.data_processor import DataProcessor
from src.utils.logger import setup_logger, APILogger
from src.utils.visualizer import (
    network_to_json, generate_network_image, generate_timeline_chart,
    generate_keyword_chart, generate_multi_line_chart, generate_clusters_chart
)

class AINOVAEngine:
    """AI NOVA 통합 엔진"""
    
    def __init__(self, api_key: Optional[str] = None):
        """AI NOVA 엔진 초기화
        
        Args:
            api_key: 빅카인즈 API 키
        """
        self.logger = setup_logger("ainova")
        self.api_logger = APILogger()
        
        # API 클라이언트 및 유틸리티 초기화
        self.api_client = BigKindsClient(api_key)
        self.data_processor = DataProcessor()
        
        # 분석 모듈 초기화
        self.clusterer = IssueClusterer()
        self.flow_analyzer = IssueFlowAnalyzer()
        self.summarizer = IssueSummarizer()
        
        self.logger.info("AI NOVA 엔진 초기화 완료")
    
    async def get_top_issues(self, date: Optional[str] = None, 
                         top_n: int = 5) -> List[Dict[str, Any]]:
        """오늘의 주요 이슈 조회
        
        Args:
            date: 조회 날짜 (YYYY-MM-DD)
            top_n: 반환할 이슈 수
            
        Returns:
            주요 이슈 목록
        """
        # 날짜가 없으면 오늘 날짜 사용
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        self.logger.info(f"주요 이슈 조회: {date}")
        
        # 캐시 키 생성
        cache_key = self.data_processor.generate_cache_key(
            "top_issues", {"date": date, "top_n": top_n}
        )
        
        # 캐시 체크
        cached_data = self.data_processor.get_cached_data(cache_key)
        if cached_data:
            self.logger.info(f"캐시에서 주요 이슈 로드: {date}")
            return cached_data
        
        try:
            # 이슈 랭킹 조회
            response = self.api_client.issue_ranking(date)
            
            if response.get("result") != "success":
                self.logger.error(f"이슈 랭킹 조회 실패: {response.get('message')}")
                return []
            
            # 이슈 데이터 처리
            issues = []
            issue_data = response.get("return_object", {})
            
            # 이슈 목록 추출
            for issue in issue_data.get("issues", [])[:top_n]:
                issue_dict = {
                    "issue_id": issue.get("id"),
                    "rank": issue.get("rank", 0),
                    "topic": issue.get("topic", ""),
                    "category": issue.get("category", ""),
                    "keywords": issue.get("keywords", []),
                    "news_count": issue.get("news_count", 0),
                    "provider_count": issue.get("provider_count", 0),
                    "date": date
                }
                
                # 관련 뉴스 추가
                related_news = []
                for news in issue.get("news", [])[:5]:  # 상위 5개만 포함
                    related_news.append({
                        "news_id": news.get("news_id"),
                        "title": news.get("title", ""),
                        "provider": news.get("provider", ""),
                        "published_at": news.get("published_at", "")
                    })
                
                issue_dict["related_news"] = related_news
                issues.append(issue_dict)
            
            # 캐시에 저장
            self.data_processor.set_cached_data(cache_key, issues)
            
            return issues
        
        except Exception as e:
            self.logger.error(f"주요 이슈 조회 오류: {e}")
            return []
    
    async def search_news(self, query: str, start_date: str, end_date: str,
                      provider: Optional[List[str]] = None,
                      category: Optional[List[str]] = None,
                      max_results: int = 100) -> List[Dict[str, Any]]:
        """뉴스 검색
        
        Args:
            query: 검색어
            start_date: 시작 날짜 (YYYY-MM-DD)
            end_date: 종료 날짜 (YYYY-MM-DD)
            provider: 언론사 코드 리스트
            category: 카테고리 코드 리스트
            max_results: 최대 검색 결과 수
            
        Returns:
            뉴스 목록
        """
        self.logger.info(f"뉴스 검색: {query} ({start_date} ~ {end_date})")
        
        # 페이지 크기 및 페이지 수 계산
        page_size = 100  # API 최대 페이지 크기
        page_count = (max_results + page_size - 1) // page_size
        
        # 캐시 키 생성
        cache_key = self.data_processor.generate_cache_key(
            "news_search",
            {
                "query": query,
                "start_date": start_date,
                "end_date": end_date,
                "provider": provider,
                "category": category,
                "max_results": max_results
            }
        )
        
        # 캐시 체크
        cached_data = self.data_processor.get_cached_data(cache_key)
        if cached_data:
            self.logger.info(f"캐시에서 검색 결과 로드: {query}")
            return cached_data
        
        try:
            all_news = []
            
            # 페이지별 검색
            for page in range(1, page_count + 1):
                response = self.api_client.news_search(
                    query=query,
                    start_date=start_date,
                    end_date=end_date,
                    provider=provider,
                    category=category,
                    size=page_size,
                    page=page
                )
                
                if response.get("result") != "success":
                    self.logger.error(f"뉴스 검색 실패 (페이지 {page}): {response.get('message')}")
                    break
                
                # 뉴스 데이터 추출 및 정규화
                news_list = self.data_processor.normalize_news_data(response)
                all_news.extend(news_list)
                
                # 최대 결과 수 체크
                if len(all_news) >= max_results:
                    all_news = all_news[:max_results]
                    break
                
                # API 호출 간격 조절
                if page < page_count:
                    await asyncio.sleep(0.5)
            
            # 캐시에 저장
            self.data_processor.set_cached_data(cache_key, all_news)
            
            return all_news
        
        except Exception as e:
            self.logger.error(f"뉴스 검색 오류: {e}")
            return []
    
    async def get_issue_map(self, news_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """이슈 맵 생성
        
        Args:
            news_list: 뉴스 목록
            
        Returns:
            이슈 맵 데이터
        """
        self.logger.info(f"이슈 맵 생성: {len(news_list)}개 뉴스")
        
        try:
            # 뉴스 클러스터링 실행
            clustering_result = self.clusterer.cluster_news(news_list)
            
            # 주요 클러스터 추출
            key_clusters = self.clusterer.extract_key_clusters(clustering_result)
            
            # 네트워크 그래프 준비
            network_data = network_to_json(clustering_result["network"])
            
            # 클러스터별 키워드
            clusters = clustering_result["clusters"]
            keywords = clustering_result["keywords"]
            
            # 클러스터 정보 구성
            cluster_info = {}
            for cluster_id in clusters:
                # 노이즈 클러스터(-1) 제외
                if cluster_id == -1:
                    continue
                    
                cluster_news = clusters[cluster_id]
                cluster_keywords = keywords.get(cluster_id, [])
                
                # 클러스터 대표 제목 선택 (첫 번째 뉴스)
                representative_title = cluster_news[0].get("title", "") if cluster_news else ""
                
                # 클러스터 정보 구성
                cluster_info[cluster_id] = {
                    "id": cluster_id,
                    "keywords": cluster_keywords,
                    "news_count": len(cluster_news),
                    "representative_title": representative_title,
                    "is_key_cluster": cluster_id in key_clusters
                }
            
            # 클러스터 크기 및 레이블 추출
            cluster_sizes = {cid: info["news_count"] for cid, info in cluster_info.items()}
            cluster_labels = {cid: ", ".join(info["keywords"][:3]) for cid, info in cluster_info.items()}
            
            # 클러스터 차트 생성
            cluster_chart = generate_clusters_chart(
                cluster_sizes,
                cluster_labels,
                "주요 이슈 클러스터"
            )
            
            # 이슈 맵 시각화
            issue_map_image = generate_network_image(clustering_result["network"])
            
            return {
                "clusters": cluster_info,
                "network": network_data,
                "key_clusters": key_clusters,
                "cluster_chart": cluster_chart,
                "issue_map_image": issue_map_image
            }
        
        except Exception as e:
            self.logger.error(f"이슈 맵 생성 오류: {e}")
            return {"clusters": {}, "network": {"nodes": [], "edges": []}, "key_clusters": []}
    
    async def get_issue_flow(self, news_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """이슈 흐름 분석
        
        Args:
            news_list: 이슈 관련 뉴스 목록
            
        Returns:
            이슈 흐름 분석 결과
        """
        self.logger.info(f"이슈 흐름 분석: {len(news_list)}개 뉴스")
        
        try:
            # 이슈 흐름 분석 실행
            flow_analysis = self.flow_analyzer.analyze_issue_flow(news_list)
            
            # 타임라인 데이터 추출
            timeline = flow_analysis["timeline"]
            
            # 타임라인 시각화 데이터 준비
            dates = {}
            for item in timeline:
                date_str = item["timestamp"].strftime("%Y-%m-%d")
                dates[date_str] = dates.get(date_str, 0) + 1
            
            date_labels = sorted(dates.keys())
            date_counts = [dates[d] for d in date_labels]
            
            # 타임라인 차트 생성
            timeline_chart = generate_timeline_chart(
                date_labels,
                date_counts,
                "뉴스 타임라인"
            )
            
            # 키워드 트렌드 데이터
            keyword_trends = flow_analysis["keyword_trends"]
            trend_dates = keyword_trends.get("dates", [])
            
            # 주요 키워드만 선택
            top_keywords = {}
            for keyword, counts in keyword_trends.items():
                if keyword != "dates" and sum(counts) > 0:
                    top_keywords[keyword] = counts
                    
                    # 최대 5개 키워드만 선택
                    if len(top_keywords) >= 5:
                        break
            
            # 키워드 트렌드 차트 생성
            if trend_dates and top_keywords:
                trend_chart = generate_multi_line_chart(
                    trend_dates,
                    top_keywords,
                    "키워드 트렌드"
                )
            else:
                trend_chart = ""
            
            # 주요 이벤트 시각화
            key_events = flow_analysis["key_events"]
            
            # 이슈 흐름도 시각화
            flow_graph = flow_analysis["flow_graph"]
            flow_graph_json = network_to_json(flow_graph)
            flow_graph_image = generate_network_image(flow_graph)
            
            # 이슈 단계 분석
            phases = self.flow_analyzer.segment_issue_phases(flow_analysis)
            
            return {
                "timeline": timeline,
                "key_events": key_events,
                "keyword_trends": keyword_trends,
                "timeline_chart": timeline_chart,
                "trend_chart": trend_chart,
                "flow_graph": flow_graph_json,
                "flow_graph_image": flow_graph_image,
                "phases": phases
            }
        
        except Exception as e:
            self.logger.error(f"이슈 흐름 분석 오류: {e}")
            return {"timeline": [], "key_events": [], "keyword_trends": {}}
    
    async def get_issue_summary(self, 
                            news_list: List[Dict[str, Any]], 
                            flow_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """이슈 요약 및 인사이트 생성
        
        Args:
            news_list: 이슈 관련 뉴스 목록
            flow_analysis: 이슈 흐름 분석 결과
            
        Returns:
            이슈 요약 및 인사이트
        """
        self.logger.info(f"이슈 요약 생성: {len(news_list)}개 뉴스")
        
        try:
            # 인용문 검색
            # 이슈 관련 키워드 추출
            all_titles = " ".join([news.get("title", "") for news in news_list])
            keywords = self.summarizer._extract_keywords(all_titles, 5)
            
            # 인용문 검색 쿼리 구성
            query = " ".join(keywords)
            
            # 검색 기간 설정
            if flow_analysis.get("timeline"):
                timeline = flow_analysis["timeline"]
                start_time = min([item["timestamp"] for item in timeline])
                end_time = max([item["timestamp"] for item in timeline])
            else:
                # 기본값으로 최근 7일
                end_time = datetime.now()
                start_time = end_time - timedelta(days=7)
            
            start_date = start_time.strftime("%Y-%m-%d")
            end_date = end_time.strftime("%Y-%m-%d")
            
            # 인용문 검색
            quotations = []
            try:
                response = self.api_client.quotation_search(
                    query=query,
                    start_date=start_date,
                    end_date=end_date,
                    size=20
                )
                
                if response.get("result") == "success":
                    quotations = self.data_processor.normalize_quotation_data(response)
            except Exception as e:
                self.logger.error(f"인용문 검색 오류: {e}")
            
            # 이슈 요약 생성
            summary = self.summarizer.generate_issue_summary(news_list, flow_analysis, quotations)
            
            # 키워드 차트 생성
            keywords = summary.get("keywords", [])
            keyword_values = [10 - i for i in range(len(keywords))]  # 임의의 값
            keyword_chart = generate_keyword_chart(
                keywords,
                keyword_values,
                "주요 키워드"
            )
            
            # 차트 추가
            summary["keyword_chart"] = keyword_chart
            
            return summary
        
        except Exception as e:
            self.logger.error(f"이슈 요약 생성 오류: {e}")
            return {}
    
    async def analyze_issue(self, query: str, start_date: str, end_date: str,
                       provider: Optional[List[str]] = None,
                       category: Optional[List[str]] = None,
                       max_results: int = 100) -> Dict[str, Any]:
        """이슈 종합 분석
        
        Args:
            query: 검색어
            start_date: 시작 날짜 (YYYY-MM-DD)
            end_date: 종료 날짜 (YYYY-MM-DD)
            provider: 언론사 코드 리스트
            category: 카테고리 코드 리스트
            max_results: 최대 검색 결과 수
            
        Returns:
            이슈 분석 결과
        """
        self.logger.info(f"이슈 종합 분석: {query} ({start_date} ~ {end_date})")
        
        # 캐시 키 생성
        cache_key = self.data_processor.generate_cache_key(
            "issue_analysis",
            {
                "query": query,
                "start_date": start_date,
                "end_date": end_date,
                "provider": provider,
                "category": category,
                "max_results": max_results
            }
        )
        
        # 캐시 체크
        cached_data = self.data_processor.get_cached_data(cache_key)
        if cached_data:
            self.logger.info(f"캐시에서 이슈 분석 결과 로드: {query}")
            return cached_data
        
        try:
            # 뉴스 검색
            news_list = await self.search_news(query, start_date, end_date, provider, category, max_results)
            
            if not news_list:
                return {"error": "검색 결과가 없습니다."}
            
            # 이슈 맵 생성
            issue_map = await self.get_issue_map(news_list)
            
            # 이슈 흐름 분석
            issue_flow = await self.get_issue_flow(news_list)
            
            # 이슈 요약 생성
            issue_summary = await self.get_issue_summary(news_list, issue_flow)
            
            # 결과 통합
            result = {
                "query": query,
                "start_date": start_date,
                "end_date": end_date,
                "news_count": len(news_list),
                "issue_map": issue_map,
                "issue_flow": issue_flow,
                "issue_summary": issue_summary,
                "timestamp": datetime.now().isoformat()
            }
            
            # 캐시에 저장
            self.data_processor.set_cached_data(cache_key, result)
            
            return result
        
        except Exception as e:
            self.logger.error(f"이슈 종합 분석 오류: {e}")
            return {"error": str(e)}
    
    async def get_today_keywords(self) -> Dict[str, Any]:
        """오늘의 키워드 조회
        
        Returns:
            카테고리별 키워드 분석 결과
        """
        self.logger.info("오늘의 키워드 조회")
        
        # 캐시 키 생성
        today = datetime.now().strftime("%Y-%m-%d")
        cache_key = f"today_keywords_{today}"
        
        # 캐시 체크
        cached_data = self.data_processor.get_cached_data(cache_key)
        if cached_data:
            self.logger.info("캐시에서 오늘의 키워드 로드")
            return cached_data
        
        try:
            # API 호출
            response = self.api_client.today_category_keyword()
            
            if response.get("result") != "success":
                self.logger.error(f"오늘의 키워드 조회 실패: {response.get('message')}")
                return {}
            
            # 카테고리별 키워드 처리
            result = {}
            category_keywords = response.get("return_object", {})
            
            for category, keywords in category_keywords.items():
                # 개체명 유형별 분류
                categorized = {
                    "person": [],
                    "location": [],
                    "organization": [],
                    "keyword": []
                }
                
                for item in keywords:
                    keyword = item.get("keyword", "")
                    count = item.get("count", 0)
                    word_type = item.get("type", "keyword").lower()
                    
                    if word_type not in categorized:
                        word_type = "keyword"
                    
                    categorized[word_type].append({
                        "keyword": keyword,
                        "count": count,
                        "type": word_type
                    })
                
                # 결과 저장
                result[category] = categorized
            
            # 차트 데이터 생성 (예: 정치 카테고리 키워드)
            charts = {}
            for category, data in result.items():
                all_keywords = data["keyword"] + data["person"] + data["organization"]
                if all_keywords:
                    # 상위 10개 키워드 선택
                    top_keywords = sorted(all_keywords, key=lambda x: x["count"], reverse=True)[:10]
                    
                    keywords = [item["keyword"] for item in top_keywords]
                    counts = [item["count"] for item in top_keywords]
                    
                    # 차트 생성
                    chart = generate_keyword_chart(
                        keywords,
                        counts,
                        f"{category} 주요 키워드"
                    )
                    
                    charts[category] = chart
            
            # 결과 통합
            final_result = {
                "date": today,
                "categories": result,
                "charts": charts
            }
            
            # 캐시에 저장
            self.data_processor.set_cached_data(cache_key, final_result)
            
            return final_result
        
        except Exception as e:
            self.logger.error(f"오늘의 키워드 조회 오류: {e}")
            return {}