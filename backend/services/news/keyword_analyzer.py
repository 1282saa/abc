"""
키워드 분석 및 그룹화 모듈

키워드 추출, 분석, 그룹화 및 정제 기능을 제공합니다.
"""

from typing import List, Dict, Tuple, Any, Set

class KeywordAnalyzer:
    """키워드 분석 및 그룹화 기능 제공 클래스"""

    # 키워드 그룹화를 위한 사전 정의 데이터
    COMPANIES = {
        "삼성", "현대", "LG", "SK", "네이버", "카카오", "두산", "롯데", "CJ", "신세계",
        "한화", "포스코", "KT", "SKT", "셀트리온", "삼성전자", "현대차", "기아", 
        "에이비엘바이오", "글로벌파운드리스", "알리익스프레스", "GSK", "애플", "구글", "마이크로소프트"
    }
    
    INDUSTRIES = {
        "바이오", "전자상거래", "여행", "건축자재", "가상자산", "반도체", "시니어", "에너지",
        "IT", "통신", "금융", "자동차", "유통", "의료", "제약", "헬스케어", "클라우드",
        "인공지능", "AI", "로봇", "메타버스", "NFT", "블록체인", "빅데이터", "플랫폼", 
        "모빌리티", "ESG", "SMR", "수소", "태양광", "풍력", "가상현실", "스마트홈"
    }
    
    STRATEGIES = {
        "투자", "매각", "진출", "확장", "빅딜", "기술수출", "파트너십", "글로벌", "협력",
        "인수", "합병", "전략", "계약", "리스크", "성장", "혁신", "개발", "출시", "런칭",
        "업그레이드", "경쟁", "마케팅", "수익", "실적", "영업이익", "매출", "판매", 
        "비용절감", "리스크", "효율화", "최적화", "확대", "축소", "재편", "재구성"
    }
    
    REGIONS = {
        "한국", "중국", "미국", "일본", "유럽", "베트남", "인도", "아시아", "북미", "남미",
        "서울", "경기", "인천", "부산", "대구", "광주", "대전", "울산", "세종", "강원",
        "충북", "충남", "전북", "전남", "경북", "경남", "제주", "보스턴", "뉴욕", "워싱턴",
        "실리콘밸리", "선전", "상하이", "베이징", "도쿄", "런던", "파리", "베를린"
    }
    
    @staticmethod
    def extract_keywords_from_questions(questions: List[str]) -> List[str]:
        """질문에서 핵심 키워드 추출 함수
        
        Args:
            questions: 질문 목록
            
        Returns:
            추출된 키워드 목록
        """
        # 불용어 정의
        stopwords = {
            "무엇인가요", "어떤", "이유", "어떻게", "영향", "전략", "시장", "이것이", 
            "전망", "배경", "의", "에", "가", "는", "을", "를", "이", "것", "왜",
            "그", "이런", "어느", "어디", "언제", "어떠한", "어디에", "무엇을", "주요",
            "하는", "있는", "되는"
        }
        
        all_keywords = []
        for question in questions:
            # 질문을 단어로 분리
            words = question.replace("?", "").replace(",", " ").replace(".", " ").split()
            # 불용어 제거 및 2글자 이상 단어만 선택
            keywords = [word for word in words if word not in stopwords and len(word) >= 2]
            all_keywords.extend(keywords)
        
        # 빈도수 기준으로 정렬
        keyword_counts = {}
        for keyword in all_keywords:
            if keyword in keyword_counts:
                keyword_counts[keyword] += 1
            else:
                keyword_counts[keyword] = 1
        
        sorted_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)
        return [k[0] for k in sorted_keywords[:20]]  # 상위 20개 키워드 반환
    
    @classmethod
    def group_related_keywords(cls, keywords: List[str], article_content: str) -> Dict[str, List[str]]:
        """키워드 그룹화 함수
        
        Args:
            keywords: 키워드 목록
            article_content: 기사 본문
            
        Returns:
            그룹화된 키워드 사전
        """
        # 키워드 그룹화 정의
        keyword_groups = {
            "기업_관련": [],
            "산업_관련": [],
            "전략_관련": [],
            "지역_관련": [],
            "기타": []
        }
        
        # 키워드 분류
        for keyword in keywords:
            # 소문자 변환 및 공백 제거
            k = keyword.lower().strip()
            
            # 기업 관련 키워드 분류
            if any(company.lower() in k or k in company.lower() for company in cls.COMPANIES):
                keyword_groups["기업_관련"].append(keyword)
            # 산업 관련 키워드 분류
            elif any(industry.lower() in k or k in industry.lower() for industry in cls.INDUSTRIES):
                keyword_groups["산업_관련"].append(keyword)
            # 전략 관련 키워드 분류
            elif any(strategy.lower() in k or k in strategy.lower() for strategy in cls.STRATEGIES):
                keyword_groups["전략_관련"].append(keyword)
            # 지역 관련 키워드 분류
            elif any(region.lower() in k or k in region.lower() for region in cls.REGIONS):
                keyword_groups["지역_관련"].append(keyword)
            # 기타 키워드
            else:
                keyword_groups["기타"].append(keyword)
        
        # 각 그룹 내에서 원문 언급 빈도 기준으로 정렬
        for group, group_keywords in keyword_groups.items():
            if group_keywords:
                group_keywords.sort(key=lambda k: article_content.count(k), reverse=True)
        
        return keyword_groups
    
    @staticmethod
    def remove_duplicates(keywords: List[str]) -> List[str]:
        """중복 키워드 제거 함수
        
        Args:
            keywords: 키워드 목록
            
        Returns:
            중복이 제거된 키워드 목록
        """
        seen: Set[str] = set()
        result = []
        
        for keyword in keywords:
            # 소문자 변환 및 공백 제거
            k = keyword.lower().strip()
            if k and k not in seen:
                seen.add(k)
                result.append(keyword)  # 원래 형태 유지
        
        return result
    
    @staticmethod
    def prioritize_keywords(keywords: List[str], title_features: List[Tuple[str, float]]) -> List[str]:
        """제목 특성을 기반으로 키워드 우선순위 설정
        
        Args:
            keywords: 키워드 목록
            title_features: 제목에서 추출한 특성
            
        Returns:
            우선순위가 적용된 키워드 목록
        """
        # 제목 특성 키워드
        title_kws = {kw[0].lower(): kw[1] for kw in title_features}
        
        # 점수 계산
        scored_keywords = []
        for kw in keywords:
            score = 1.0  # 기본 점수
            kw_lower = kw.lower()
            
            # 제목 특성에 있으면 점수 가산
            if kw_lower in title_kws:
                score += title_kws[kw_lower] * 2
            
            # 점수와 함께 저장
            scored_keywords.append((kw, score))
        
        # 점수 기준 정렬
        scored_keywords.sort(key=lambda x: x[1], reverse=True)
        
        # 원래 키워드만 반환
        return [kw[0] for kw in scored_keywords] 