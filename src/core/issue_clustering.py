"""
이슈 클러스터링 모듈

뉴스 데이터를 분석하여 이슈별로 클러스터링하는 기능을 제공
"""

import numpy as np
from typing import Dict, List, Tuple, Any, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import DBSCAN, AgglomerativeClustering
from sklearn.metrics.pairwise import cosine_similarity
import networkx as nx
from collections import Counter

# 프로젝트 루트 디렉토리 찾기
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import ISSUE_ANALYSIS

class IssueClusterer:
    """뉴스 기사를 이슈별로 클러스터링하는 클래스"""
    
    def __init__(self, 
                min_cluster_size: Optional[int] = None, 
                max_clusters: Optional[int] = None, 
                similarity_threshold: Optional[float] = None):
        """이슈 클러스터링 엔진 초기화
        
        Args:
            min_cluster_size: 최소 클러스터 크기
            max_clusters: 최대 클러스터 수
            similarity_threshold: 유사도 임계값
        """
        self.min_cluster_size = min_cluster_size or ISSUE_ANALYSIS.get("min_cluster_size", 5)
        self.max_clusters = max_clusters or ISSUE_ANALYSIS.get("max_clusters", 20)
        self.similarity_threshold = similarity_threshold or ISSUE_ANALYSIS.get("similarity_threshold", 0.7)
        self.vectorizer = TfidfVectorizer(
            max_features=10000,
            min_df=2,
            max_df=0.85,
            stop_words='english'  # 한국어 불용어 처리는 별도로 구현 필요
        )
        
    def preprocess_news(self, news_list: List[Dict[str, Any]]) -> Tuple[List[str], List[Dict[str, Any]]]:
        """뉴스 데이터 전처리
        
        Args:
            news_list: 뉴스 기사 목록
            
        Returns:
            전처리된 텍스트 목록과 원본 뉴스 데이터
        """
        processed_texts = []
        cleaned_news = []
        
        for news in news_list:
            # 제목과 본문 결합
            title = news.get('title', '')
            content = news.get('content', '')
            
            if not title and not content:
                continue
            
            # 텍스트 정제 (실제 구현 시 한국어 형태소 분석 등 추가 필요)
            combined_text = f"{title} {content}"
            processed_texts.append(combined_text)
            cleaned_news.append(news)
            
        return processed_texts, cleaned_news
    
    def vectorize_texts(self, texts: List[str]) -> np.ndarray:
        """텍스트를 벡터화
        
        Args:
            texts: 전처리된 텍스트 목록
            
        Returns:
            벡터화된 텍스트 행렬
        """
        return self.vectorizer.fit_transform(texts)
    
    def cluster_with_dbscan(self, vectors: np.ndarray) -> List[int]:
        """DBSCAN 알고리즘으로 클러스터링
        
        Args:
            vectors: 벡터화된 텍스트 행렬
            
        Returns:
            클러스터 레이블 목록
        """
        # 코사인 유사도 행렬 계산 (1 - 유사도를 거리로 사용)
        distance_matrix = 1 - cosine_similarity(vectors)
        
        # DBSCAN 클러스터링 수행
        dbscan = DBSCAN(
            eps=1.0 - self.similarity_threshold,
            min_samples=self.min_cluster_size,
            metric='precomputed'
        )
        
        return dbscan.fit_predict(distance_matrix)
    
    def cluster_with_hierarchical(self, vectors: np.ndarray) -> List[int]:
        """계층적 클러스터링 알고리즘으로 클러스터링
        
        Args:
            vectors: 벡터화된 텍스트 행렬
            
        Returns:
            클러스터 레이블 목록
        """
        # 코사인 유사도 행렬 계산 (1 - 유사도를 거리로 사용)
        distance_matrix = 1 - cosine_similarity(vectors)
        
        # 계층적 클러스터링 수행
        n_clusters = min(self.max_clusters, vectors.shape[0] // 2)
        if n_clusters < 2:
            n_clusters = 2
            
        hac = AgglomerativeClustering(
            n_clusters=n_clusters,
            affinity='precomputed',
            linkage='average'
        )
        
        return hac.fit_predict(distance_matrix)
    
    def extract_cluster_keywords(self, 
                              cluster_texts: List[str], 
                              top_n: int = 5) -> List[str]:
        """클러스터의 핵심 키워드 추출
        
        Args:
            cluster_texts: 클러스터에 속한 텍스트 목록
            top_n: 추출할 키워드 수
            
        Returns:
            핵심 키워드 목록
        """
        # 클러스터 내 텍스트에 대한 TF-IDF 벡터화
        cluster_vectorizer = TfidfVectorizer(
            max_features=1000,
            min_df=1,
            max_df=0.9
        )
        
        try:
            vectors = cluster_vectorizer.fit_transform(cluster_texts)
            feature_names = cluster_vectorizer.get_feature_names_out()
            
            # 각 단어의 평균 TF-IDF 점수 계산
            tfidf_scores = vectors.sum(axis=0).A1
            
            # 상위 키워드 추출
            top_indices = tfidf_scores.argsort()[-top_n:][::-1]
            return [feature_names[i] for i in top_indices]
        except:
            # 충분한 데이터가 없는 경우
            return []
    
    def create_issue_network(self, 
                           clusters: Dict[int, List[Dict[str, Any]]],
                           vectors: np.ndarray) -> nx.Graph:
        """이슈 간 관계 네트워크 생성
        
        Args:
            clusters: 클러스터별 뉴스 데이터
            vectors: 벡터화된 텍스트 행렬
            
        Returns:
            이슈 네트워크 그래프
        """
        G = nx.Graph()
        
        # 각 클러스터의 중심 벡터 계산
        cluster_centers = {}
        for cluster_id, news_items in clusters.items():
            if cluster_id == -1:  # 노이즈 클러스터 제외
                continue
                
            indices = [news["index"] for news in news_items]
            cluster_vectors = vectors[indices]
            center = cluster_vectors.mean(axis=0)
            cluster_centers[cluster_id] = center
            
            # 노드 추가
            keywords = self.extract_cluster_keywords([news["text"] for news in news_items])
            keyword_text = ", ".join(keywords[:3])
            G.add_node(cluster_id, 
                       keywords=keywords,
                       label=keyword_text,
                       size=len(news_items))
        
        # 클러스터 간 유사도에 기반한 엣지 추가
        for i in cluster_centers:
            for j in cluster_centers:
                if i >= j:
                    continue
                    
                sim = cosine_similarity(cluster_centers[i], cluster_centers[j])[0, 0]
                if sim > 0.3:  # 임계값 이상의 유사도를 가진 클러스터 연결
                    G.add_edge(i, j, weight=sim)
        
        return G
    
    def cluster_news(self, news_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """뉴스 데이터를 이슈별로 클러스터링
        
        Args:
            news_list: 뉴스 기사 목록
            
        Returns:
            클러스터링 결과
            {
                "clusters": 클러스터별 뉴스 목록,
                "network": 이슈 네트워크,
                "keywords": 클러스터별 키워드
            }
        """
        # 데이터 전처리
        texts, cleaned_news = self.preprocess_news(news_list)
        
        if len(texts) < self.min_cluster_size:
            return {
                "clusters": {0: cleaned_news},
                "network": nx.Graph(),
                "keywords": {0: self.extract_cluster_keywords(texts)}
            }
        
        # 텍스트 벡터화
        vectors = self.vectorize_texts(texts)
        
        # 클러스터링 (두 가지 방법 중 선택)
        if len(texts) < 100:
            labels = self.cluster_with_hierarchical(vectors)
        else:
            labels = self.cluster_with_dbscan(vectors)
        
        # 클러스터별 뉴스 그룹화
        clusters = {}
        for i, (label, news, text) in enumerate(zip(labels, cleaned_news, texts)):
            if label not in clusters:
                clusters[label] = []
            
            # 인덱스 정보 추가
            news_with_index = dict(news)
            news_with_index["index"] = i
            news_with_index["text"] = text
            news_with_index["cluster_id"] = label
            
            clusters[label].append(news_with_index)
        
        # 클러스터별 키워드 추출
        keywords = {}
        for label, news_items in clusters.items():
            texts = [item["text"] for item in news_items]
            keywords[label] = self.extract_cluster_keywords(texts)
        
        # 이슈 네트워크 생성
        network = self.create_issue_network(clusters, vectors)
        
        # 결과 반환
        return {
            "clusters": clusters,
            "network": network,
            "keywords": keywords
        }
    
    def extract_key_clusters(self, clustering_result: Dict[str, Any], top_n: int = 5) -> List[int]:
        """중요 클러스터 추출
        
        Args:
            clustering_result: 클러스터링 결과
            top_n: 추출할 클러스터 수
            
        Returns:
            중요 클러스터 ID 목록
        """
        clusters = clustering_result["clusters"]
        
        # 노이즈 클러스터(-1) 제외
        valid_clusters = {k: v for k, v in clusters.items() if k != -1}
        
        # 클러스터 크기 기준 정렬
        sorted_clusters = sorted(
            valid_clusters.keys(),
            key=lambda k: len(valid_clusters[k]),
            reverse=True
        )
        
        return sorted_clusters[:top_n]