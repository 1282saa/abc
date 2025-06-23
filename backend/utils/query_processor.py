"""
빅카인즈 API에 최적화된 쿼리 처리 모듈

빅카인즈 API 특성:
- 공백 기준으로 키워드 분리하여 검색
- AND 연산자로 정확도 향상 가능
- 구체적인 키워드일수록 정확한 결과
- tf-idf 기반 _score 정렬 제공
"""
import re
from typing import List, Tuple

# 한국어 불용어 확장 리스트
STOPWORDS = {
    # 조사
    '과', '와', '의', '은', '는', '이', '가', '을', '를', '에', '에서', '에게', '께', '으로', '로', '와', '과',
    '도', '만', '까지', '부터', '처럼', '같이', '보다', '마다', '조차', '마저', '뿐', '밖에',
    
    # 어미/연결어
    '그리고', '하지만', '그러나', '그런데', '따라서', '그래서', '또한', '또는', '혹은', '그러면',
    
    # 질문/요청 표현
    '어떤', '어떻게', '무엇', '언제', '어디', '왜', '누구', '얼마', '몇', '어떤가요',
    '알려줘', '알려주세요', '궁금해', '궁금합니다', '궁금해요', '설명해', '설명해주세요',
    '요약해', '요약해주세요', '정리해', '정리해주세요', '분석해', '분석해주세요',
    
    # 시간 표현
    '오늘', '어제', '내일', '지난', '다음', '올해', '내년', '작년', '최근', '향후', '앞으로',
    '이번', '다음번', '저번', '언제부터', '언제까지', '현재', '지금',
    
    # 일반적인 수식어
    '매우', '정말', '너무', '조금', '많이', '적게', '크게', '작게', '빠르게', '느리게',
    '좋은', '나쁜', '큰', '작은', '높은', '낮은', '빠른', '느린',
    
    # 뉴스/분석 관련 불용어
    '관련', '현황', '동향', '이슈', '정보', '소식', '뉴스', '기사', '보도', '발표',
    '상황', '상태', '결과', '원인', '이유', '방법', '방안', '대안', '해결책',
    '전망', '예상', '예측', '계획', '방향', '추세', '경향',
    
    # 어미 패턴
    '전망이', '동향이', '상황이', '현황이', '결과가', '방법은', '이유는',
    
    # 기타
    '것', '거', '게', '점', '번', '개', '명', '건', '회', '차례', '때', '경우', '상황'
}

# 회사명 정규화 맵핑
COMPANY_NORMALIZATION = {
    '삼성전자와': '삼성전자',
    '삼성전자의': '삼성전자', 
    '네이버의': '네이버',
    '현대차의': '현대차',
    'SK하이닉스의': 'SK하이닉스',
    '카카오의': '카카오'
}

def preprocess_query(text: str) -> List[str]:
    """
    빅카인즈 API에 최적화된 키워드 추출
    
    Args:
        text: 사용자 질문 (예: "네이버 주가 실황이 궁금해요")
        
    Returns:
        추출된 핵심 키워드 리스트 (예: ['네이버', '주가', '실황'])
    """
    # 1. 특수문자 제거 (한글, 영문, 숫자만 유지)
    text = re.sub(r'[^\w\s가-힣]', ' ', text)
    
    # 2. 연속된 공백을 하나로 통합
    text = re.sub(r'\s+', ' ', text.strip())
    
    # 3. 단어 분리
    words = text.split()
    
    # 4. 회사명 정규화 및 필터링
    keywords = []
    for word in words:
        word = word.strip()
        
        # 회사명 정규화 적용
        if word in COMPANY_NORMALIZATION:
            word = COMPANY_NORMALIZATION[word]
        
        # 필터링 조건
        if (len(word) >= 2 and  # 2글자 이상
            word not in STOPWORDS and  # 불용어 아님
            not word.isdigit() and  # 순수 숫자 아님
            not re.match(r'.*[?!]$', word)):  # 물음표/느낌표로 끝나지 않음
            keywords.append(word)
    
    # 5. 중복 제거하되 순서 유지
    return list(dict.fromkeys(keywords))

def build_bigkinds_query(keywords: List[str], strategy: str = "and") -> str:
    """
    빅카인즈 API용 쿼리 문자열 생성
    
    Args:
        keywords: 키워드 리스트
        strategy: "and" (정확도 우선) 또는 "or" (범위 우선)
        
    Returns:
        빅카인즈 API 쿼리 문자열
    """
    if not keywords:
        return ""
    
    if len(keywords) == 1:
        return f'"{keywords[0]}"'
    
    if strategy == "and":
        # 정확도 우선: "키워드1" AND "키워드2" AND "키워드3"
        return " AND ".join([f'"{keyword}"' for keyword in keywords])
    else:
        # 범위 우선: "키워드1" OR "키워드2" OR "키워드3" 
        return " OR ".join([f'"{keyword}"' for keyword in keywords])

def create_fallback_queries(keywords: List[str]) -> List[Tuple[str, str]]:
    """
    검색 실패 시 사용할 폴백 쿼리들을 생성
    
    Args:
        keywords: 원본 키워드 리스트
        
    Returns:
        (쿼리문, 설명) 튜플의 리스트
    """
    if not keywords:
        return []
    
    queries = []
    
    # 1순위: 모든 키워드 AND 검색
    if len(keywords) > 1:
        queries.append((
            build_bigkinds_query(keywords, "and"),
            f"정확도 우선 (모든 키워드 포함): {' + '.join(keywords)}"
        ))
    
    # 2순위: 중요 키워드만 AND 검색 (처음 3개)
    if len(keywords) > 3:
        queries.append((
            build_bigkinds_query(keywords[:3], "and"),
            f"핵심 키워드 우선: {' + '.join(keywords[:3])}"
        ))
    
    # 3순위: 가장 중요한 2개 키워드만
    if len(keywords) > 2:
        queries.append((
            build_bigkinds_query(keywords[:2], "and"),
            f"주요 키워드: {' + '.join(keywords[:2])}"
        ))
    
    # 4순위: OR 검색 (범위 확대)
    if len(keywords) > 1:
        queries.append((
            build_bigkinds_query(keywords, "or"),
            f"범위 확대: {' 또는 '.join(keywords)}"
        ))
    
    # 5순위: 첫 번째 키워드만
    queries.append((
        build_bigkinds_query([keywords[0]], "and"),
        f"기본 검색: {keywords[0]}"
    ))
    
    return queries

def analyze_query_intent(text: str) -> dict:
    """
    사용자 질문의 의도를 분석
    
    Args:
        text: 사용자 질문
        
    Returns:
        분석 결과 딕셔너리
    """
    intent = {
        "type": "general",  # general, company, market, tech, finance
        "time_sensitive": False,
        "comparison": False,
        "analysis_depth": "basic"  # basic, detailed, comprehensive
    }
    
    # 기업 관련 키워드
    company_keywords = ['삼성', '엘지', 'LG', '현대', '네이버', '카카오', '포스코', 'SK', '한화']
    if any(keyword in text for keyword in company_keywords):
        intent["type"] = "company"
    
    # 시장/경제 관련 키워드  
    market_keywords = ['주가', '주식', '증권', '시장', '경제', '금리', '환율', '거래']
    if any(keyword in text for keyword in market_keywords):
        intent["type"] = "finance"
    
    # 실시간성 키워드
    realtime_keywords = ['실황', '실시간', '현재', '지금', '오늘', '최신']
    if any(keyword in text for keyword in realtime_keywords):
        intent["time_sensitive"] = True
    
    # 비교 분석 키워드
    comparison_keywords = ['비교', '차이', '대비', '경쟁', 'vs', '대', '와의']
    if any(keyword in text for keyword in comparison_keywords):
        intent["comparison"] = True
    
    # 분석 깊이
    if any(keyword in text for keyword in ['분석', '전망', '예측', '평가']):
        intent["analysis_depth"] = "detailed"
    
    return intent 