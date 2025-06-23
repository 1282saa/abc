#!/usr/bin/env python3
"""
네트워크 데이터 생성 테스트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Mock 데이터로 테스트
articles = [
    {
        "title": "삼성전자 3분기 실적 발표",
        "content": "삼성전자가 3분기 실적을 발표했다. 메모리 반도체 사업의 성장으로 영업이익이 크게 증가했다.",
        "provider_name": "서울경제",
        "published_at": "2024-10-25",
        "provider_link_page": "http://example.com",
        "news_id": "1"
    },
    {
        "title": "반도체 시장 전망 밝아",
        "content": "전문가들은 메모리 반도체 시장의 회복세가 지속될 것이라고 전망했다. 삼성전자와 SK하이닉스의 실적 개선이 기대된다.",
        "provider_name": "한국경제",
        "published_at": "2024-10-24", 
        "provider_link_page": "http://example.com",
        "news_id": "2"
    }
]

# 키워드 추출 테스트
from collections import Counter
import re

def extract_keywords_from_articles(articles):
    keyword_pattern = re.compile(r'[가-힣]{2,}')
    
    stopwords = {
        '기자', '기업', '회사', '사업', '시장', '정부', '국가', '지난', '올해', '내년',
        '이번', '당시', '현재', '관련', '통해', '위해', '대한', '국내', '해외', '전년',
        '이날', '오늘', '어제', '내일', '이후', '이전', '동안', '과정', '결과', '상황'
    }
    
    all_keywords = []
    for article in articles:
        title = article.get("title", "")
        content = article.get("content", "")
        text = f"{title} {content}"
        
        keywords = keyword_pattern.findall(text)
        keywords = [kw for kw in keywords if kw not in stopwords and len(kw) <= 10]
        all_keywords.extend(keywords)
    
    keyword_counts = Counter(all_keywords).most_common(10)
    
    return [
        {
            "keyword": keyword,
            "count": count,
            "weight": count / max(keyword_counts[0][1], 1)
        }
        for keyword, count in keyword_counts
    ]

def generate_network_data(articles, keywords):
    nodes = []
    links = []
    
    # 키워드 노드 생성
    for i, keyword_data in enumerate(keywords[:5]):
        nodes.append({
            "id": f"keyword_{i}",
            "name": keyword_data["keyword"],
            "type": "keyword", 
            "weight": keyword_data["weight"],
            "size": 10 + keyword_data["weight"] * 20,
            "color": "#3B82F6"
        })
    
    # 기사 노드 생성
    for i, article in enumerate(articles):
        nodes.append({
            "id": f"article_{i}",
            "name": article.get("title", "")[:30] + "...",
            "type": "article",
            "title": article.get("title", ""),
            "provider": article.get("provider_name", ""),
            "url": article.get("provider_link_page", ""),
            "published_at": article.get("published_at", ""),
            "size": 15,
            "color": "#EF4444"
        })
    
    # 기사-키워드 간 링크 생성
    for article_idx, article in enumerate(articles):
        title = article.get("title", "")
        content = article.get("content", "")
        text = f"{title} {content}".lower()
        
        for keyword_idx, keyword_data in enumerate(keywords[:5]):
            keyword = keyword_data["keyword"]
            if keyword in text:
                strength = text.count(keyword) * keyword_data["weight"]
                links.append({
                    "source": f"keyword_{keyword_idx}",
                    "target": f"article_{article_idx}",
                    "strength": strength,
                    "width": max(1, strength * 3)
                })
    
    return {
        "nodes": nodes,
        "links": links
    }

print("🔍 네트워크 데이터 생성 테스트")
print("=" * 50)

# 키워드 추출
keywords = extract_keywords_from_articles(articles)
print(f"📝 추출된 키워드: {len(keywords)}개")
for kw in keywords:
    print(f"  - {kw['keyword']}: {kw['count']}회 (가중치: {kw['weight']:.2f})")

# 네트워크 데이터 생성
network_data = generate_network_data(articles, keywords)
print(f"\n🕸️ 네트워크 데이터:")
print(f"  - 노드: {len(network_data['nodes'])}개")
print(f"  - 링크: {len(network_data['links'])}개")

print(f"\n📊 노드 정보:")
for node in network_data['nodes']:
    print(f"  - {node['name']} ({node['type']}) - size: {node['size']}")

print(f"\n🔗 링크 정보:")
for link in network_data['links']:
    print(f"  - {link['source']} → {link['target']} (강도: {link['strength']:.2f})")

print("\n✅ 테스트 완료! 네트워크 데이터가 정상적으로 생성됩니다.")