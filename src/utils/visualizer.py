"""
시각화 유틸리티 모듈

데이터 시각화 관련 유틸리티 함수 제공
"""

import json
import networkx as nx
from typing import Dict, List, Any, Tuple, Optional
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import io
import base64

def network_to_json(graph: nx.Graph) -> Dict[str, Any]:
    """네트워크 그래프를 JSON 형식으로 변환
    
    Args:
        graph: NetworkX 그래프
        
    Returns:
        JSON 호환 데이터
    """
    # 노드 정보 추출
    nodes = []
    for node_id, attrs in graph.nodes(data=True):
        node = {
            "id": str(node_id),
            "label": attrs.get("label", str(node_id)),
            "size": attrs.get("size", 10),
            "color": attrs.get("color", "#1f77b4")
        }
        
        # 추가 속성 복사
        for key, value in attrs.items():
            if key not in ["label", "size", "color"]:
                # datetime 객체 처리
                if isinstance(value, datetime):
                    node[key] = value.isoformat()
                else:
                    node[key] = value
        
        nodes.append(node)
    
    # 엣지 정보 추출
    edges = []
    for source, target, attrs in graph.edges(data=True):
        edge = {
            "source": str(source),
            "target": str(target),
            "weight": attrs.get("weight", 1.0)
        }
        
        # 추가 속성 복사
        for key, value in attrs.items():
            if key != "weight":
                edge[key] = value
        
        edges.append(edge)
    
    return {
        "nodes": nodes,
        "edges": edges
    }

def generate_network_image(graph: nx.Graph, width: int = 800, height: int = 600) -> str:
    """네트워크 그래프 이미지 생성
    
    Args:
        graph: NetworkX 그래프
        width: 이미지 너비
        height: 이미지 높이
        
    Returns:
        Base64 인코딩된 이미지 데이터
    """
    plt.figure(figsize=(width/100, height/100), dpi=100)
    
    # 노드 크기 설정
    node_sizes = []
    for _, attrs in graph.nodes(data=True):
        size = attrs.get("size", 10)
        node_sizes.append(size * 50)  # 크기 조정
    
    # 엣지 두께 설정
    edge_weights = []
    for _, _, attrs in graph.edges(data=True):
        weight = attrs.get("weight", 1.0)
        edge_weights.append(weight * 2)  # 두께 조정
    
    # 그래프 레이아웃 계산
    pos = nx.spring_layout(graph, seed=42)
    
    # 그래프 그리기
    nx.draw_networkx(
        graph,
        pos=pos,
        with_labels=True,
        node_size=node_sizes,
        node_color="#1f77b4",
        edge_color="#aaaaaa",
        width=edge_weights,
        font_size=10,
        font_color="#000000",
        alpha=0.8
    )
    
    plt.axis("off")
    
    # 이미지를 메모리에 저장
    buffer = io.BytesIO()
    plt.savefig(buffer, format="png", bbox_inches="tight")
    plt.close()
    
    # Base64 인코딩
    buffer.seek(0)
    image_data = base64.b64encode(buffer.read()).decode("utf-8")
    
    return f"data:image/png;base64,{image_data}"

def generate_timeline_chart(dates: List[str], counts: List[int], title: str = "뉴스 타임라인") -> str:
    """타임라인 차트 이미지 생성
    
    Args:
        dates: 날짜 목록
        counts: 각 날짜별 카운트
        title: 차트 제목
        
    Returns:
        Base64 인코딩된 이미지 데이터
    """
    plt.figure(figsize=(10, 6), dpi=100)
    
    # 날짜 파싱
    x_dates = [datetime.strptime(d, "%Y-%m-%d") for d in dates]
    
    # 라인 차트 그리기
    plt.plot(x_dates, counts, marker="o", linestyle="-", linewidth=2, markersize=6)
    
    # 그래프 스타일 설정
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.title(title, fontsize=16)
    plt.xlabel("날짜", fontsize=12)
    plt.ylabel("뉴스 건수", fontsize=12)
    
    # x축 날짜 포맷 설정
    plt.gcf().autofmt_xdate()
    
    # 이미지를 메모리에 저장
    buffer = io.BytesIO()
    plt.savefig(buffer, format="png", bbox_inches="tight")
    plt.close()
    
    # Base64 인코딩
    buffer.seek(0)
    image_data = base64.b64encode(buffer.read()).decode("utf-8")
    
    return f"data:image/png;base64,{image_data}"

def generate_keyword_chart(keywords: List[str], values: List[float], 
                         title: str = "주요 키워드", horizontal: bool = True) -> str:
    """키워드 차트 이미지 생성
    
    Args:
        keywords: 키워드 목록
        values: 키워드별 값
        title: 차트 제목
        horizontal: 가로 바 차트 여부
        
    Returns:
        Base64 인코딩된 이미지 데이터
    """
    plt.figure(figsize=(10, 6), dpi=100)
    
    # 데이터 정렬
    sorted_data = sorted(zip(keywords, values), key=lambda x: x[1])
    sorted_keywords, sorted_values = zip(*sorted_data)
    
    # 바 차트 그리기
    if horizontal:
        plt.barh(sorted_keywords, sorted_values, color="#1f77b4")
        plt.xlabel("빈도", fontsize=12)
        plt.ylabel("키워드", fontsize=12)
    else:
        plt.bar(sorted_keywords, sorted_values, color="#1f77b4")
        plt.xlabel("키워드", fontsize=12)
        plt.ylabel("빈도", fontsize=12)
        plt.xticks(rotation=45, ha="right")
    
    # 그래프 스타일 설정
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.title(title, fontsize=16)
    
    # 이미지를 메모리에 저장
    buffer = io.BytesIO()
    plt.savefig(buffer, format="png", bbox_inches="tight")
    plt.close()
    
    # Base64 인코딩
    buffer.seek(0)
    image_data = base64.b64encode(buffer.read()).decode("utf-8")
    
    return f"data:image/png;base64,{image_data}"

def generate_multi_line_chart(dates: List[str], datasets: Dict[str, List[float]], 
                            title: str = "키워드 트렌드") -> str:
    """다중 라인 차트 이미지 생성
    
    Args:
        dates: 날짜 목록
        datasets: 키워드별 값 목록
        title: 차트 제목
        
    Returns:
        Base64 인코딩된 이미지 데이터
    """
    plt.figure(figsize=(10, 6), dpi=100)
    
    # 날짜 파싱
    x_dates = [datetime.strptime(d, "%Y-%m-%d") for d in dates]
    
    # 각 데이터셋별로 라인 그리기
    for label, values in datasets.items():
        if len(values) == len(x_dates):
            plt.plot(x_dates, values, marker="o", linestyle="-", linewidth=2, markersize=4, label=label)
    
    # 그래프 스타일 설정
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.title(title, fontsize=16)
    plt.xlabel("날짜", fontsize=12)
    plt.ylabel("빈도", fontsize=12)
    plt.legend(loc="best")
    
    # x축 날짜 포맷 설정
    plt.gcf().autofmt_xdate()
    
    # 이미지를 메모리에 저장
    buffer = io.BytesIO()
    plt.savefig(buffer, format="png", bbox_inches="tight")
    plt.close()
    
    # Base64 인코딩
    buffer.seek(0)
    image_data = base64.b64encode(buffer.read()).decode("utf-8")
    
    return f"data:image/png;base64,{image_data}"

def generate_clusters_chart(cluster_sizes: Dict[int, int], 
                          cluster_labels: Dict[int, str],
                          title: str = "이슈 클러스터") -> str:
    """클러스터 크기 차트 이미지 생성
    
    Args:
        cluster_sizes: 클러스터 ID별 크기
        cluster_labels: 클러스터 ID별 레이블
        title: 차트 제목
        
    Returns:
        Base64 인코딩된 이미지 데이터
    """
    plt.figure(figsize=(10, 6), dpi=100)
    
    # 클러스터 정렬 (크기 기준)
    sorted_clusters = sorted(
        cluster_sizes.items(),
        key=lambda x: x[1],
        reverse=True
    )
    
    cluster_ids, sizes = zip(*sorted_clusters)
    
    # 레이블 준비
    labels = [cluster_labels.get(cid, f"클러스터 {cid}") for cid in cluster_ids]
    
    # 바 차트 그리기
    plt.barh(labels, sizes, color="#1f77b4")
    
    # 그래프 스타일 설정
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.title(title, fontsize=16)
    plt.xlabel("뉴스 건수", fontsize=12)
    plt.ylabel("이슈", fontsize=12)
    
    # 이미지를 메모리에 저장
    buffer = io.BytesIO()
    plt.savefig(buffer, format="png", bbox_inches="tight")
    plt.close()
    
    # Base64 인코딩
    buffer.seek(0)
    image_data = base64.b64encode(buffer.read()).decode("utf-8")
    
    return f"data:image/png;base64,{image_data}"