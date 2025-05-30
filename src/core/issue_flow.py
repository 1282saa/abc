"""
이슈 흐름 분석 모듈

시간에 따른 이슈의 흐름을 분석하는 기능을 제공
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import networkx as nx

# 프로젝트 루트 디렉토리 찾기
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

class IssueFlowAnalyzer:
    """이슈의 시간적 흐름을 분석하는 클래스"""
    
    def __init__(self):
        """이슈 흐름 분석 엔진 초기화"""
        pass
    
    def extract_timeline(self, news_cluster: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """이슈 클러스터의 시간적 타임라인 추출
        
        Args:
            news_cluster: 이슈 클러스터에 속한 뉴스 목록
            
        Returns:
            시간순으로 정렬된 이슈 타임라인
        """
        # 뉴스를 시간 순으로 정렬
        sorted_news = sorted(
            news_cluster, 
            key=lambda x: datetime.fromisoformat(x.get('published_at', '').replace('Z', '+00:00'))
        )
        
        # 타임라인 구성
        timeline = []
        for news in sorted_news:
            published_at = datetime.fromisoformat(news.get('published_at', '').replace('Z', '+00:00'))
            
            timeline_item = {
                'timestamp': published_at,
                'news_id': news.get('news_id', ''),
                'title': news.get('title', ''),
                'provider': news.get('provider', ''),
                'category': news.get('category', ''),
                'keywords': news.get('keywords', [])
            }
            
            timeline.append(timeline_item)
        
        return timeline
    
    def identify_key_events(self, timeline: List[Dict[str, Any]], 
                           window_size: int = 3) -> List[Dict[str, Any]]:
        """타임라인에서 주요 이벤트 시점 식별
        
        Args:
            timeline: 이슈 타임라인
            window_size: 분석 윈도우 크기(시간 단위)
            
        Returns:
            주요 이벤트 목록
        """
        if not timeline:
            return []
        
        # 시간별 뉴스 빈도 계산
        df = pd.DataFrame(timeline)
        df['hour'] = df['timestamp'].dt.floor('H')
        hourly_counts = df.groupby('hour').size()
        
        # 롤링 윈도우를 사용한 이동 평균 계산
        rolling_mean = hourly_counts.rolling(window=window_size, min_periods=1).mean()
        
        # 급증 시점 감지 (이동 평균보다 1.5배 이상 높은 시간대)
        peak_hours = hourly_counts[hourly_counts > 1.5 * rolling_mean].index.tolist()
        
        # 주요 이벤트 구성
        key_events = []
        for hour in peak_hours:
            hour_news = df[df['hour'] == hour]
            
            if len(hour_news) < 2:
                continue
                
            # 해당 시간대의 첫 뉴스를 주요 이벤트로 선정
            first_news = hour_news.iloc[0]
            
            event = {
                'timestamp': hour,
                'news_id': first_news['news_id'],
                'title': first_news['title'],
                'importance': len(hour_news),  # 뉴스 수를 중요도로 사용
                'provider': first_news['provider'],
                'related_news_count': len(hour_news)
            }
            
            key_events.append(event)
        
        return key_events
    
    def extract_keyword_trends(self, timeline: List[Dict[str, Any]], 
                             top_n: int = 10) -> Dict[str, List[float]]:
        """시간에 따른 키워드 트렌드 추출
        
        Args:
            timeline: 이슈 타임라인
            top_n: 추출할 상위 키워드 수
            
        Returns:
            키워드별 시간 트렌드
        """
        if not timeline:
            return {}
        
        # 전체 기간에서 주요 키워드 추출
        all_keywords = []
        for item in timeline:
            all_keywords.extend(item.get('keywords', []))
        
        # 빈도 기준 상위 키워드 선정
        keyword_counts = pd.Series(all_keywords).value_counts()
        top_keywords = keyword_counts.nlargest(top_n).index.tolist()
        
        # 시간대별 키워드 빈도 계산
        df = pd.DataFrame(timeline)
        df['date'] = df['timestamp'].dt.date
        
        keyword_trends = {}
        for keyword in top_keywords:
            # 날짜별 해당 키워드 포함 뉴스 수 계산
            daily_counts = []
            for date, group in df.groupby('date'):
                count = sum(1 for item in group['keywords'] if keyword in item)
                daily_counts.append((date, count))
            
            # 결과 정렬 및 저장
            sorted_counts = sorted(daily_counts, key=lambda x: x[0])
            keyword_trends[keyword] = [count for _, count in sorted_counts]
        
        # 날짜 목록 (X축)
        dates = sorted(df['date'].unique())
        keyword_trends['dates'] = [d.strftime('%Y-%m-%d') for d in dates]
        
        return keyword_trends
    
    def create_flow_graph(self, timeline: List[Dict[str, Any]], 
                        key_events: List[Dict[str, Any]]) -> nx.DiGraph:
        """이슈 흐름 그래프 생성
        
        Args:
            timeline: 이슈 타임라인
            key_events: 주요 이벤트 목록
            
        Returns:
            이슈 흐름 방향성 그래프
        """
        G = nx.DiGraph()
        
        # 주요 이벤트를 노드로 추가
        for i, event in enumerate(key_events):
            G.add_node(
                i,
                timestamp=event['timestamp'],
                title=event['title'],
                news_id=event['news_id'],
                importance=event['importance']
            )
        
        # 시간 순으로 엣지 연결
        for i in range(len(key_events) - 1):
            G.add_edge(i, i+1, weight=1)
        
        return G
    
    def analyze_issue_flow(self, news_cluster: List[Dict[str, Any]]) -> Dict[str, Any]:
        """이슈 클러스터의 흐름 분석
        
        Args:
            news_cluster: 이슈 클러스터에 속한 뉴스 목록
            
        Returns:
            이슈 흐름 분석 결과
        """
        # 타임라인 추출
        timeline = self.extract_timeline(news_cluster)
        
        # 주요 이벤트 식별
        key_events = self.identify_key_events(timeline)
        
        # 키워드 트렌드 추출
        keyword_trends = self.extract_keyword_trends(timeline)
        
        # 흐름 그래프 생성
        flow_graph = self.create_flow_graph(timeline, key_events)
        
        # 결과 반환
        return {
            "timeline": timeline,
            "key_events": key_events,
            "keyword_trends": keyword_trends,
            "flow_graph": flow_graph
        }
    
    def segment_issue_phases(self, flow_analysis: Dict[str, Any], 
                           num_phases: int = 3) -> List[Dict[str, Any]]:
        """이슈 흐름을 단계별로 분할
        
        Args:
            flow_analysis: 이슈 흐름 분석 결과
            num_phases: 분할할 단계 수
            
        Returns:
            이슈 단계 목록 (서론, 본론, 결론 등)
        """
        timeline = flow_analysis["timeline"]
        
        if not timeline or len(timeline) < num_phases:
            return []
        
        # 시간 순으로 동일한 크기로 분할
        df = pd.DataFrame(timeline)
        segment_size = len(df) // num_phases
        
        phases = []
        for i in range(num_phases):
            start_idx = i * segment_size
            end_idx = (i+1) * segment_size if i < num_phases - 1 else len(df)
            
            segment = df.iloc[start_idx:end_idx]
            
            # 가장 중요한 뉴스 선택 (첫 번째 뉴스 사용)
            representative_news = segment.iloc[0].to_dict()
            
            phase = {
                "phase_id": i,
                "name": self._get_phase_name(i, num_phases),
                "start_time": segment['timestamp'].min(),
                "end_time": segment['timestamp'].max(),
                "representative_news": representative_news,
                "news_count": len(segment)
            }
            
            phases.append(phase)
        
        return phases
    
    def _get_phase_name(self, phase_id: int, total_phases: int) -> str:
        """이슈 단계 이름 생성
        
        Args:
            phase_id: 단계 ID
            total_phases: 전체 단계 수
            
        Returns:
            단계 이름
        """
        if total_phases == 3:
            phases = ["서론", "본론", "결론"]
        elif total_phases == 5:
            phases = ["도입", "전개", "위기", "절정", "결말"]
        else:
            return f"단계 {phase_id+1}"
        
        return phases[phase_id]