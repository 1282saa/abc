"""
키워드 처리 및 질문 생성 유틸리티
"""

import re
import random
from typing import List, Dict, Any, Set, Tuple, Optional
from collections import Counter

# 한국어 불용어 목록
KOREAN_STOPWORDS = {
    "및", "등", "통해", "위해", "으로", "에서", "이는", "있는", "있다", "또한", 
    "그리고", "하지만", "그러나", "그런데", "따라서", "이에", "따라", "대한", 
    "위한", "이런", "저런", "하는", "이와", "관련", "관련된", "등의", "라며", 
    "지난", "이번", "한편", "말했다", "밝혔다", "전했다", "있다고", "이라고"
}

def filter_keywords(keywords: List[str]) -> List[str]:
    """키워드 필터링
    
    Args:
        keywords: 필터링할 키워드 목록
        
    Returns:
        필터링된 키워드 목록
    """
    # 중복 제거
    unique_keywords = list(set(keywords))
    
    # 불용어 제거
    filtered = [k for k in unique_keywords if k not in KOREAN_STOPWORDS]
    
    # 최소 길이 필터링 (1글자 단어 제외)
    filtered = [k for k in filtered if len(k) > 1]
    
    # 숫자만 있는 키워드 제거
    filtered = [k for k in filtered if not re.match(r'^\d+$', k)]
    
    return filtered

def score_keywords(base_query: str, related_keywords: List[str], topn_keywords: List[str]) -> Dict[str, float]:
    """키워드 점수 계산
    
    Args:
        base_query: 기본 검색어
        related_keywords: 연관어 목록
        topn_keywords: TopN 키워드 목록
        
    Returns:
        키워드별 점수
    """
    scores = {}
    
    # 연관어 가중치 
    for i, kw in enumerate(related_keywords):
        # 순위 기반 역가중치 (상위일수록 높은 점수)
        scores[kw] = scores.get(kw, 0) + (len(related_keywords) - i) / len(related_keywords) * 10
    
    # TopN 가중치
    for i, kw in enumerate(topn_keywords):
        scores[kw] = scores.get(kw, 0) + (len(topn_keywords) - i) / len(topn_keywords) * 8
    
    # 중복 보너스 (두 API에 모두 등장하면 가중치 +5)
    for kw in set(related_keywords) & set(topn_keywords):
        scores[kw] = scores.get(kw, 0) + 5
    
    # 원래 쿼리와의 관련성 (포함 관계 +3)
    for kw in scores:
        if base_query in kw or kw in base_query:
            scores[kw] = scores.get(kw, 0) + 3
    
    return scores

def create_boolean_queries(base_query: str, selected_keywords: List[str], max_variations: int = 10) -> List[Dict[str, Any]]:
    """불리언 연산자를 활용한 쿼리 변형 생성
    
    Args:
        base_query: 기본 검색어
        selected_keywords: 선택된 키워드 목록
        max_variations: 최대 변형 수
        
    Returns:
        쿼리 변형 목록
    """
    variations = []
    
    # 1. 정교화 쿼리 (AND 연산자)
    for kw in selected_keywords[:min(4, len(selected_keywords))]:  # 상위 4개까지
        if kw != base_query and not (kw in base_query or base_query in kw):  # 중복 방지
            variations.append({
                "query": f"{base_query} AND {kw}",
                "type": "refine",
                "keyword": kw
            })
    
    # 2. 확장 쿼리 (OR 연산자)
    # 상위 키워드 중 2-3개 선택하여 OR로 묶기
    if len(selected_keywords) >= 3:
        similar_kws = selected_keywords[2:5]  # 3~5번째 키워드
        if len(similar_kws) >= 2:
            kw_text = " OR ".join(similar_kws[:2])
            variations.append({
                "query": f"{base_query} AND ({kw_text})",
                "type": "expand",
                "keywords": similar_kws[:2]
            })
    
    # 3. 제외 쿼리 (NOT 연산자)
    # 점수가 낮은 키워드 중에서 선택
    if len(selected_keywords) > 6:
        for kw in selected_keywords[-3:]:  # 하위 3개
            variations.append({
                "query": f"{base_query} NOT {kw}",
                "type": "exclude",
                "keyword": kw
            })
    
    # 4. 복합 쿼리 (그룹화)
    if len(selected_keywords) >= 4:
        group1 = selected_keywords[0]
        group2 = selected_keywords[1]
        variations.append({
            "query": f"({base_query} OR {group1}) AND {group2}",
            "type": "complex",
            "keywords": [group1, group2]
        })
    
    # 최대 변형 수로 제한
    return variations[:max_variations]

def keywords_to_questions(base_query: str, query_variations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """쿼리 변형을 자연어 질문으로 변환
    
    Args:
        base_query: 기본 검색어
        query_variations: 쿼리 변형 목록
        
    Returns:
        질문 목록
    """
    questions = []
    
    # 쿼리 유형별 질문 템플릿
    templates = {
        "refine": [
            "{base}의 {keyword}에 관한 최근 소식이 궁금합니다.",
            "{keyword}와(과) 관련된 {base}의 동향은 어떤가요?",
            "{base}가 {keyword}에 미치는 영향은 무엇인가요?",
            "{base}와(과) {keyword}의 상관관계는 어떻게 되나요?",
            "{base}에서 {keyword}가 차지하는 비중은 어느 정도인가요?"
        ],
        "expand": [
            "{base}와(과) {keywords}의 관계가 궁금합니다.",
            "{base}가 {keywords} 분야에 어떤 의미가 있나요?",
            "{keywords} 관점에서 {base}는 어떤 의미인가요?",
            "{base}가 {keywords}에 미치는 영향을 알려주세요.",
            "{base}와(과) {keywords} 중 어느 것이 더 중요한가요?"
        ],
        "exclude": [
            "{keyword}를 제외한 {base}의 주요 이슈는 무엇인가요?",
            "{base}에서 {keyword}가 아닌 부분에 대해 알려주세요.",
            "{base}와(과) 관련된 {keyword} 외의 주요 동향은 무엇인가요?",
            "{keyword}가 아닌 관점에서 {base}를 설명해주세요.",
            "{base}를 이해하는데 {keyword}가 꼭 필요한가요?"
        ],
        "complex": [
            "{base}와(과) {keywords}의 복합적인 관계에 대해 알려주세요.",
            "{keywords} 관점에서 볼 때 {base}의 의미는 무엇인가요?",
            "{base}와(과) {keywords}는 어떻게 연결되어 있나요?",
            "{base}가 {keywords}에 미치는 복합적인 영향은 무엇인가요?",
            "{base}와(과) {keywords}의 차이점은 무엇인가요?"
        ]
    }
    
    # 기본 질문 추가 (항상 포함)
    basic_templates = [
        "{base}에 대해 간단히 설명해주세요.",
        "{base}의 최근 이슈는 무엇인가요?",
        "{base}의 현재 상황은 어떤가요?",
        "{base}에 대해 알아야 할 중요한 점은 무엇인가요?",
        "{base}의 전망은 어떤가요?"
    ]
    
    # 기본 질문 1개 추가
    basic_question = {
        "question": random.choice(basic_templates).format(base=base_query),
        "query": base_query,
        "type": "basic"
    }
    questions.append(basic_question)
    
    # 쿼리 변형별 질문 생성
    for variation in query_variations:
        query = variation["query"]
        variation_type = variation["type"]
        
        if variation_type == "refine":
            # 정교화 쿼리에서 키워드 추출
            keyword = variation["keyword"]
            template = random.choice(templates["refine"])
            question = template.format(base=base_query, keyword=keyword)
            
        elif variation_type == "expand":
            # 확장 쿼리에서 키워드들 추출
            keywords = variation["keywords"]
            keywords_text = " 또는 ".join(keywords)
            template = random.choice(templates["expand"])
            question = template.format(base=base_query, keywords=keywords_text)
            
        elif variation_type == "exclude":
            # 제외 쿼리에서 키워드 추출
            keyword = variation["keyword"]
            template = random.choice(templates["exclude"])
            question = template.format(base=base_query, keyword=keyword)
            
        elif variation_type == "complex":
            # 복합 쿼리에서 키워드 추출
            keywords = variation["keywords"]
            keywords_text = "와(과) ".join(keywords)
            template = random.choice(templates["complex"])
            question = template.format(base=base_query, keywords=keywords_text)
            
        else:
            # 기본 질문
            question = f"{base_query}에 대해 더 알려주세요."
        
        questions.append({
            "question": question,
            "query": query,
            "type": variation_type
        })
    
    # 중복 제거
    unique_questions = []
    seen = set()
    
    for q in questions:
        if q["question"] not in seen:
            seen.add(q["question"])
            unique_questions.append(q)
    
    return unique_questions

def get_topic_sensitive_date_range(topic: str) -> Dict[str, str]:
    """주제별 최적 기간 설정
    
    Args:
        topic: 검색 주제
        
    Returns:
        기간 설정 정보
    """
    # 주제별 기간 설정 (일 단위)
    topic_periods = {
        "정치": 14,        # 정치 뉴스는 빠르게 변화
        "경제": 30,        # 경제 뉴스는 중기적 관점
        "국제": 21,        # 국제 뉴스는 중단기
        "사회": 14,        # 사회 뉴스는 단기
        "문화": 60,        # 문화 뉴스는 장기적
        "IT/과학": 45,     # IT/과학 뉴스는 중장기
        "스포츠": 7,       # 스포츠 뉴스는 매우 단기
        "연예": 14,        # 연예 뉴스는 단기
    }
    
    # 주제 키워드 매핑
    topic_keywords = {
        "정치": ["정치", "정당", "국회", "선거", "대통령"],
        "경제": ["경제", "금융", "주식", "투자", "은행"],
        "국제": ["국제", "해외", "외교", "미국", "중국"],
        "사회": ["사회", "사건", "범죄", "교육", "환경"],
        "문화": ["문화", "예술", "영화", "음악", "전시"],
        "IT/과학": ["IT", "과학", "기술", "인공지능", "반도체"],
        "스포츠": ["스포츠", "축구", "야구", "올림픽", "경기"],
        "연예": ["연예", "연예인", "아이돌", "배우", "가수"]
    }
    
    # 주제 감지
    detected_topic = None
    for t, keywords in topic_keywords.items():
        if any(kw in topic.lower() for kw in keywords):
            detected_topic = t
            break
    
    # 기간 결정 (감지된 주제가 없으면 기본 30일)
    days = topic_periods.get(detected_topic, 30)
    
    from datetime import datetime, timedelta
    date_from = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    date_to = datetime.now().strftime("%Y-%m-%d")
    
    return {
        "date_from": date_from, 
        "date_to": date_to, 
        "detected_topic": detected_topic,
        "days": days
    } 