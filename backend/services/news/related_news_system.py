"""
연관 질문 생성 및 뉴스 검색 통합 시스템

기사 분석, 키워드 추출, 연관 질문 생성, 뉴스 검색을 통합적으로 처리하는 시스템입니다.
"""

import asyncio
import logging
from typing import Dict, List, Any, Tuple, Optional

from .keyword_analyzer import KeywordAnalyzer
from .question_generator import QuestionGenerator
from .query_generator import QueryGenerator
from backend.api.clients.bigkinds import BigKindsClient

logger = logging.getLogger(__name__)

class RelatedNewsSystem:
    """연관 질문 생성 및 뉴스 검색 통합 시스템 클래스"""
    
    @staticmethod
    async def process_article_async(
        article: Dict[str, str], 
        client: BigKindsClient,
        date_from: str = None,
        date_to: str = None
    ) -> Dict[str, Any]:
        """기사 처리 비동기 함수
        
        Args:
            article: 기사 정보 (제목, 본문)
            client: BigKindsClient 인스턴스
            date_from: 검색 시작일 (YYYY-MM-DD)
            date_to: 검색 종료일 (YYYY-MM-DD)
            
        Returns:
            처리 결과 (질문, 뉴스 매핑 등)
        """
        title = article.get("title", "")
        content = article.get("content", "")
        
        # 빈 기사 체크
        if not title or not content:
            logger.error("기사 제목 또는 본문이 비어 있습니다.")
            return {
                "success": False,
                "questions": [],
                "question_news_mapping": {},
                "error": "기사 내용이 부족합니다."
            }
        
        try:
            # 1. 특성 추출
            logger.info("특성 추출 중...")
            features = client.extract_features(
                title=title,
                sub_title="",
                content=content
            )
            
            # 2. 키워드 추출 및 그룹화
            logger.info("키워드 그룹화 중...")
            all_keywords = []
            for field_type in ["title", "content"]:
                field_features = features.get(field_type, [])
                keywords = [kw["keyword"] for kw in field_features]
                all_keywords.extend(keywords)
            
            # 중복 제거
            unique_keywords = KeywordAnalyzer.remove_duplicates(all_keywords)
            
            # 키워드 그룹화
            keyword_groups = KeywordAnalyzer.group_related_keywords(unique_keywords, content)
            
            # 3. 연관 키워드 및 TopN 키워드 가져오기
            logger.info("연관 키워드 및 TopN 키워드 가져오기...")
            # 제목에서 추출한 핵심 키워드
            title_keywords = [kw["keyword"] for kw in features.get("title", [])][:2]
            
            related_keywords = []
            topn_keywords = []
            
            if title_keywords:
                # 첫 번째 제목 키워드로 연관 키워드 가져오기
                try:
                    related_keywords_raw = await client.get_related_keywords(
                        keyword=title_keywords[0],
                        date_from=date_from,
                        date_to=date_to,
                        max_count=10
                    )
                    related_keywords = [k for k in related_keywords_raw if isinstance(k, str)][:5]
                except Exception as e:
                    logger.warning(f"연관 키워드 가져오기 실패: {e}")
                
                # TopN 키워드 가져오기
                try:
                    topn_keywords_raw = await client.get_keyword_topn(
                        keyword=title_keywords[0],
                        date_from=date_from,
                        date_to=date_to,
                        limit=10
                    )
                    topn_keywords = [k for k in topn_keywords_raw if isinstance(k, str)][:5]
                except Exception as e:
                    logger.warning(f"TopN 키워드 가져오기 실패: {e}")
            
            # 4. 질문 생성
            logger.info("연관 질문 생성 중...")
            questions = QuestionGenerator.generate_questions_from_article(
                article, keyword_groups, features, related_keywords, topn_keywords
            )
            
            # 5. 검색 쿼리 생성
            logger.info("검색 쿼리 생성 중...")
            search_queries = QueryGenerator.create_optimized_search_queries(keyword_groups)
            
            # 6. 뉴스 검색
            logger.info("관련 뉴스 검색 중...")
            search_results = []
            
            # 상위 3개 쿼리만 사용
            for query in search_queries[:3]:
                try:
                    # 뉴스 검색 - highlight와 images 필드 추가
                    news_response = client.get_keyword_news(
                        keyword=query,
                        date_from=date_from,
                        date_to=date_to,
                        return_size=5,
                        fields=[
                            "news_id", 
                            "title", 
                            "content", 
                            "published_at", 
                            "provider_name", 
                            "byline", 
                            "category",
                            "highlight",  # 검색어 하이라이트 추가
                            "images",     # 이미지 URL 추가
                            "images_caption"  # 이미지 캡션 추가
                        ]
                    )
                    
                    # 응답 포맷팅
                    formatted_news = client.format_news_response(news_response)
                    articles = formatted_news.get("documents", [])
                    
                    if articles:
                        search_results.append({
                            "query": query,
                            "articles": articles
                        })
                except Exception as e:
                    logger.error(f"쿼리 '{query}' 뉴스 검색 실패: {e}")
            
            # 7. 질문-뉴스 매핑
            logger.info("질문-뉴스 매핑 중...")
            question_news_mapping = {}
            
            for question in questions:
                # 질문에서 핵심 키워드 추출
                question_keywords = KeywordAnalyzer.extract_keywords_from_questions([question])
                
                best_articles = []
                
                # 모든 검색 결과에서 관련성 높은 기사 찾기
                for search_result in search_results:
                    query = search_result["query"]
                    articles = search_result["articles"]
                    
                    # 쿼리와 질문의 관련성 확인
                    query_relevance = sum(1 for kw in question_keywords if kw in query)
                    
                    if query_relevance > 0:
                        # 기사 관련성 평가
                        for article in articles:
                            article_title = article.get("title", "")
                            article_relevance = sum(1 for kw in question_keywords if kw in article_title)
                            
                            # 관련성 점수 계산
                            relevance_score = query_relevance * 0.6 + article_relevance * 0.4
                            
                            if relevance_score > 0:
                                # 중복 기사 제외
                                article_id = article.get("news_id", "")
                                if not any(a.get("news_id", "") == article_id for a in best_articles):
                                    best_articles.append({
                                        "article": article,
                                        "relevance_score": relevance_score
                                    })
                
                # 관련성 점수로 정렬
                best_articles.sort(key=lambda x: x["relevance_score"], reverse=True)
                
                # 상위 3개 기사만 선택
                question_news_mapping[question] = [item["article"] for item in best_articles[:3]]
            
            # 8. 결과 반환
            logger.info("처리 완료")
            return {
                "success": True,
                "questions": questions,
                "question_news_mapping": question_news_mapping,
                "keyword_groups": keyword_groups,
                "search_queries": search_queries,
                "related_keywords": related_keywords,
                "topn_keywords": topn_keywords
            }
            
        except Exception as e:
            logger.error(f"기사 처리 중 오류 발생: {str(e)}")
            return {
                "success": False,
                "questions": [],
                "question_news_mapping": {},
                "error": f"처리 중 오류 발생: {str(e)}"
            }
    
    @staticmethod
    def format_questions_with_news(result: Dict[str, Any]) -> str:
        """질문과 뉴스를 텍스트로 포맷팅하는 함수
        
        Args:
            result: 처리 결과
            
        Returns:
            포맷팅된 텍스트
        """
        if not result.get("success", False):
            return f"오류: {result.get('error', '알 수 없는 오류')}"
        
        questions = result.get("questions", [])
        question_news_mapping = result.get("question_news_mapping", {})
        
        if not questions:
            return "생성된 질문이 없습니다."
        
        output = "연관 질문 및 관련 뉴스:\n\n"
        
        for i, question in enumerate(questions, 1):
            output += f"Q{i}: {question}\n"
            
            # 관련 뉴스 추가
            articles = question_news_mapping.get(question, [])
            if articles:
                output += "   관련 뉴스:\n"
                for j, article in enumerate(articles, 1):
                    title = article.get("title", "제목 없음")
                    provider = article.get("provider", "출처 미상")
                    date = article.get("published_at", "").split("T")[0] if article.get("published_at") else ""
                    output += f"   {j}. [{provider}] {title} ({date})\n"
            else:
                output += "   관련 뉴스가 없습니다.\n"
            
            output += "\n"
        
        # 주요 검색 쿼리 추가
        search_queries = result.get("search_queries", [])
        if search_queries:
            output += "주요 검색 쿼리:\n"
            for i, query in enumerate(search_queries[:3], 1):
                output += f"{i}. {query}\n"
        
        return output 