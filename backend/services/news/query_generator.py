"""
검색 쿼리 생성기 모듈

키워드 그룹을 기반으로 최적화된 검색 쿼리를 생성하는 모듈입니다.
"""

from typing import List, Dict, Set

class QueryGenerator:
    """검색 쿼리 생성 클래스"""
    
    @staticmethod
    def create_optimized_search_queries(keyword_groups: Dict[str, List[str]]) -> List[str]:
        """최적화된 검색 쿼리 생성 함수
        
        Args:
            keyword_groups: 그룹화된 키워드
            
        Returns:
            최적화된 검색 쿼리 목록
        """
        optimized_queries = []
        
        # 모든 그룹에서 최소 하나의 키워드가 있는지 확인
        has_company = len(keyword_groups["기업_관련"]) > 0
        has_industry = len(keyword_groups["산업_관련"]) > 0
        has_strategy = len(keyword_groups["전략_관련"]) > 0
        has_region = len(keyword_groups["지역_관련"]) > 0
        
        # 전략 1: 기업 키워드 중심 정밀 검색
        if has_company:
            main_company = keyword_groups["기업_관련"][0]  # 가장 중요한 기업
            
            # 산업 키워드가 있는 경우
            if has_industry:
                industry_terms = " OR ".join(keyword_groups["산업_관련"][:2])
                query = f"{main_company} AND ({industry_terms})"
                optimized_queries.append(query)
            
            # 전략 키워드가 있는 경우
            if has_strategy:
                strategy_terms = " OR ".join(keyword_groups["전략_관련"][:2])
                query = f"{main_company} AND ({strategy_terms})"
                optimized_queries.append(query)
            
            # 산업 + 전략 키워드 조합
            if has_industry and has_strategy:
                industry_term = keyword_groups["산업_관련"][0]
                strategy_term = keyword_groups["전략_관련"][0]
                query = f"{main_company} AND {industry_term} AND {strategy_term}"
                optimized_queries.append(query)
        
        # 전략 2: 산업 키워드 중심 포괄 검색
        if has_industry:
            main_industry = keyword_groups["산업_관련"][0]  # 가장 중요한 산업
            
            # 기업 키워드가 있는 경우
            if has_company:
                company_terms = " OR ".join(keyword_groups["기업_관련"][:3])
                query = f"{main_industry} AND ({company_terms})"
                optimized_queries.append(query)
            
            # 전략 키워드가 있는 경우
            if has_strategy:
                strategy_term = keyword_groups["전략_관련"][0]
                query = f"{main_industry} AND {strategy_term}"
                optimized_queries.append(query)
        
        # 전략 3: 지역과 전략/산업 키워드 조합
        if has_region:
            main_region = keyword_groups["지역_관련"][0]
            
            # 산업 키워드가 있는 경우
            if has_industry:
                main_industry = keyword_groups["산업_관련"][0]
                query = f"{main_region} AND {main_industry}"
                optimized_queries.append(query)
            
            # 전략 키워드가 있는 경우
            if has_strategy:
                main_strategy = keyword_groups["전략_관련"][0]
                query = f"{main_region} AND {main_strategy}"
                optimized_queries.append(query)
            
            # 기업 키워드가 있는 경우
            if has_company:
                main_company = keyword_groups["기업_관련"][0]
                query = f"{main_region} AND {main_company}"
                optimized_queries.append(query)
        
        # 전략 4: 복합 OR 조건을 활용한 포괄적 검색
        if has_company and has_industry:
            top_companies = " OR ".join(keyword_groups["기업_관련"][:2])
            top_industries = " OR ".join(keyword_groups["산업_관련"][:2])
            query = f"({top_companies}) AND ({top_industries})"
            optimized_queries.append(query)
        
        # 생성된 쿼리가 없는 경우
        if not optimized_queries:
            # 기타 키워드 사용
            if keyword_groups["기타"]:
                optimized_queries.append(keyword_groups["기타"][0])
            # 모든 키워드 그룹에서 하나씩 추출
            else:
                all_keywords = []
                for group, keywords in keyword_groups.items():
                    if keywords:
                        all_keywords.append(keywords[0])
                if all_keywords:
                    optimized_queries.append(" AND ".join(all_keywords[:3]))
                else:
                    # 기본 쿼리
                    optimized_queries.append("최신 뉴스")
        
        return optimized_queries 