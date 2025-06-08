"""
BigKinds API 응답 포맷팅 유틸리티

API 응답을 프론트엔드 친화적인 구조로 변환하는 함수들을 제공합니다.
"""

from typing import Dict, Any, List

def format_news_response(api_response: Dict[str, Any]) -> Dict[str, Any]:
    """API 응답을 프론트엔드 친화적 형식으로 변환
    
    Args:
        api_response: BigKinds API 응답
        
    Returns:
        변환된 응답
    """
    if api_response.get("result") != 0:
        return {
            "success": False,
            "error": "API 요청 실패",
            "documents": []
        }
    
    return_object = api_response.get("return_object", {})
    documents = return_object.get("documents", [])
    
    # 문서 형식 정규화
    formatted_docs = []
    for doc in documents:
        formatted_doc = {
            "id": doc.get("news_id", ""),
            "title": doc.get("title", ""),
            "content": doc.get("content", ""),
            "summary": doc.get("content", "")[:200] + "..." if doc.get("content") else "",
            "published_at": doc.get("published_at", ""),
            "dateline": doc.get("dateline", ""),
            "category": doc.get("category", []),
            "provider": doc.get("provider_name", ""),
            "provider_code": doc.get("provider_code", ""),
            "url": doc.get("provider_link_page", ""),
            "byline": doc.get("byline", ""),
            "images": doc.get("images", [])
        }
        formatted_docs.append(formatted_doc)
    
    return {
        "success": True,
        "total_hits": return_object.get("total_hits", 0),
        "documents": formatted_docs
    }

def format_issue_ranking_response(api_response: Dict[str, Any]) -> Dict[str, Any]:
    """이슈 랭킹 API 응답을 topics 구조로 변환 - 실제 API 구조 기반
    
    Args:
        api_response: BigKinds issue_ranking API 응답
        
    Returns:
        topics 구조로 변환된 응답
    """
    if api_response.get("result") != 0:
        return {
            "success": False,
            "error": "이슈 랭킹 조회 실패",
            "topics": []
        }
    
    return_object = api_response.get("return_object", {})
    # 실제 API 응답은 topics 배열을 직접 반환
    raw_topics = return_object.get("topics", [])
    
    # topics 구조로 변환 - 실제 API 필드명 사용
    topics = []
    for idx, topic_data in enumerate(raw_topics):
        topic = {
            "topic_id": f"topic_{idx+1}",  # API에는 topic_id가 없으므로 생성
            "topic_name": topic_data.get("topic", ""),  # 실제 필드명: 'topic'
            "rank": topic_data.get("topic_rank", idx + 1),  # 실제 필드명: 'topic_rank'
            "score": topic_data.get("topic_rank", idx + 1),  # rank를 score로 사용
            "news_cluster": topic_data.get("news_cluster", []),  # 실제 필드명: 'news_cluster'
            "keywords": topic_data.get("topic_keyword", "").split(",") if topic_data.get("topic_keyword") else [],  # 실제 필드명: 'topic_keyword'
            # 원본 필드도 그대로 보존 (프론트 요구)
            "topic": topic_data.get("topic", ""),
            "topic_rank": topic_data.get("topic_rank", idx + 1),
            "topic_keyword": topic_data.get("topic_keyword", ""),
        }
        topics.append(topic)
    
    return {
        "success": True,
        "topics": topics
    }

def format_quotation_response(api_response: Dict[str, Any]) -> Dict[str, Any]:
    """인용문 검색 API 응답을 포맷팅
    
    Args:
        api_response: BigKinds quotation_search API 응답
        
    Returns:
        포맷팅된 인용문 검색 결과
    """
    if api_response.get("result") != 0:
        return {
            "success": False,
            "error": "인용문 검색 실패",
            "quotations": []
        }
    
    return_object = api_response.get("return_object", {})
    documents = return_object.get("documents", [])
    
    # 인용문 구조로 변환
    quotations = []
    for doc in documents:
        quotation = {
            "id": doc.get("news_id", ""),
            "title": doc.get("title", ""),
            "published_at": doc.get("published_at", ""),
            "provider": doc.get("provider", ""),
            "source": doc.get("source", ""),  # 인용 출처
            "quotation": doc.get("quotation", "")  # 인용문
        }
        quotations.append(quotation)
    
    return {
        "success": True,
        "total_hits": return_object.get("total_hits", 0),
        "quotations": quotations
    } 