"""
최신 뉴스 관련 API 라우트

최신 뉴스, 인기 키워드, 이슈 등 최신 정보 관련 API 엔드포인트를 정의합니다.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import sys
import os

from ..models.news_models import LatestNewsResponse
from ..dependencies.clients import get_bigkinds_client
from ..clients.bigkinds import BigKindsClient
from backend.utils.logger import setup_logger
from backend.constants.provider_map import PROVIDER_MAP

# API 라우터 생성
router = APIRouter(prefix="/api/news", tags=["최신 뉴스"])

@router.get("/latest", response_model=LatestNewsResponse)
async def get_latest_news(
    bigkinds_client: BigKindsClient = Depends(get_bigkinds_client)
):
    """최신 뉴스 정보 조회 (수정된 API 구조 기반)
    
    - 오늘의 이슈 (빅카인즈 이슈 랭킹)
    - 인기 키워드 (전체 검색 순위)
    """
    logger = setup_logger("api.news.latest")
    logger.info("최신 뉴스 정보 요청")
    
    today_issues = []
    popular_keywords = []
    
    try:
        # 1. 오늘의 이슈 가져오기 (오늘 날짜 기본 사용)
        logger.info("오늘의 이슈 요청 시작")
        issue_response = bigkinds_client.get_issue_ranking()  # 오늘 날짜 자동 설정
        
        if issue_response.get("result") == 0:
            # format_issue_ranking_response 메소드 사용
            formatted_issues = bigkinds_client.format_issue_ranking_response(issue_response)
            ### 언론사 기사 매핑.
            if formatted_issues.get("success"):
                topics = formatted_issues.get("topics", [])[:10]  # 상위 10개만
                # 언론사 코드 → 이름 매핑 (일부 주요 언론사만 포함, 필요시 추가 가능) 
                today_issues = []
                for idx, topic in enumerate(topics):
                    cluster_ids = topic.get("news_cluster", [])
                    # 실제 뉴스 ID 수집 및 언론사별 카운팅
                    provider_counts = {}
                    actual_news_ids = []
                    
                    if cluster_ids:
                        try:
                            # 먼저 클러스터 ID에서 직접 언론사 코드 추출 (추가 로직)
                            logger.info(f"클러스터 ID 직접 처리 시작: {len(cluster_ids)} 개")
                            for cluster_id in cluster_ids:
                                if cluster_id and "." in cluster_id:
                                    # 언론사 코드 추출 (첫 번째 부분)
                                    code = cluster_id.split(".")[0]
                                    
                                    # 뉴스 ID 저장
                                    actual_news_ids.append(cluster_id)
                                    
                                    # 언론사별 카운트 증가
                                    provider_counts[code] = provider_counts.get(code, 0) + 1
                            
                            logger.info(f"클러스터 ID 직접 처리 완료: {len(provider_counts)} 개 언론사 코드 추출")
                            
                            # provider_counts가 비어있는 경우에만 API 호출 (기존 로직)
                            if not provider_counts:
                                logger.info("언론사 코드 직접 추출 실패, API 호출 시도")
                                search_res = bigkinds_client.get_news_by_cluster_ids(cluster_ids[:100])
                                formatted = bigkinds_client.format_news_response(search_res)
                                for doc in formatted.get("documents", []):
                                    code = doc.get("provider_code")
                                    if not code:
                                        nid = doc.get("id") or doc.get("news_id")
                                        if nid and "." in nid:
                                            code = nid.split(".")[0]
                                    news_id = doc.get("id")
                                    
                                    if news_id:
                                        actual_news_ids.append(news_id)
                        except Exception as e:
                            logger.error(f"언론사 코드 추출 오류: {str(e)}", exc_info=True)
                            provider_counts = {}

                    # Fallback: 클러스터로 찾지 못한 경우 토픽명으로 키워드 검색
                    if not provider_counts:
                        try:
                            keyword = topic.get("topic", "") or topic.get("topic_keyword", "").split(",")[0] if topic.get("topic_keyword") else ""
                            if keyword:
                                # 최근 7일간 해당 키워드로 뉴스 검색 (datetime은 모듈 상단에서 import됨)
                                date_from = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
                                date_to = datetime.now().strftime("%Y-%m-%d")
                                
                                kw_res = bigkinds_client.search_news(
                                    query=keyword.strip(), 
                                    date_from=date_from,
                                    date_to=date_to,
                                    return_size=100
                                )
                                kw_docs = bigkinds_client.format_news_response(kw_res).get("documents", [])
                                for doc in kw_docs:
                                    code = doc.get("provider_code")
                                    if not code:
                                        nid = doc.get("id") or doc.get("news_id")
                                        if nid and "." in nid:
                                            code = nid.split(".")[0]
                                    news_id = doc.get("id")
                                    
                                    if news_id:
                                        actual_news_ids.append(news_id)
                        except Exception:
                            pass

                    # 집계가 전혀 없을 경우 count를 클러스터 길이나 actual_news_ids 길이로 보정
                    total_count = sum(provider_counts.values())
                    if total_count == 0:
                        total_count = len(actual_news_ids) if actual_news_ids else len(cluster_ids)

                    # provider breakdown 정렬 (기사 수 내림차순)
                    breakdown = [
                        {
                            "provider": PROVIDER_MAP.get(code, code),
                            "provider_code": code,
                            "count": cnt
                        }
                        for code, cnt in sorted(provider_counts.items(), key=lambda x: x[1], reverse=True)
                    ]
                    
                    # 디버깅을 위한 로깅 추가
                    if breakdown:
                        log_items = [f"{item['provider']}({item['provider_code']}): {item['count']}" for item in breakdown[:5]]
                        logger.info(f"이슈 '{topic.get('topic', '')}' 언론사별 기사 수: {', '.join(log_items)}")
                    else:
                        logger.warning(f"이슈 '{topic.get('topic', '')}' 언론사별 기사 수 매핑 실패")

                    today_issues.append({
                        "rank": topic.get("rank", idx + 1),
                        "title": topic.get("topic", ""),
                        "count": total_count,
                        "provider_breakdown": breakdown,
                        "related_news_ids": actual_news_ids[:50],  # 실제 뉴스 ID 목록 (최대 50개)
                        "cluster_ids": cluster_ids,  # 원본 클러스터 ID도 보관
                        "topic": topic.get("topic", ""),
                        "topic_rank": topic.get("rank", idx + 1),
                        "topic_keyword": topic.get("topic_keyword", ""),
                        "news_cluster": cluster_ids,
                    })
                logger.info(f"오늘의 이슈 {len(today_issues)}개 조회 성공")
            else:
                logger.warning(f"이슈 랭킹 포맷팅 실패: {formatted_issues.get('error')}")
                today_issues = []
        else:
            logger.warning(f"이슈 랭킹 API 오류: {issue_response.get('error', '알 수 없는 오류')}")
            today_issues = [{
                "rank": 1,
                "title": "최신 이슈를 불러오는 중입니다.",
                "count": 0,
                "related_news_ids": [],
                "cluster_ids": [],
                "topic": "",
                "topic_rank": 1,
                "topic_keyword": "",
                "news_cluster": []
            }]
    
    except Exception as e:
        logger.error(f"오늘의 이슈 조회 오류: {e}", exc_info=True)
        today_issues = [{
            "rank": 1,
            "title": "이슈 데이터 로딩 중 오류 발생",
            "count": 0,
            "related_news_ids": [],
            "cluster_ids": [],
            "topic": "",
            "topic_rank": 1,
            "topic_keyword": "",
            "news_cluster": []
        }]
    
    try:
        # 2. 인기 키워드 가져오기 (수정된 API 사용)
        logger.info("인기 키워드 요청 시작")
        keyword_response = bigkinds_client.get_popular_keywords(days=1, limit=10)
        
        if keyword_response.get("result") == 0:
            # 수정된 API에서 formatted_keywords 사용
            formatted_keywords = keyword_response.get("formatted_keywords", [])
            
            popular_keywords = [
                {
                    "rank": kw.get("rank", idx + 1),
                    "keyword": kw.get("keyword", ""),
                    "count": kw.get("count", 0),
                    "trend": kw.get("trend", "stable")
                }
                for idx, kw in enumerate(formatted_keywords[:10])  # 상위 10개만
            ]
            
            logger.info(f"인기 키워드 {len(popular_keywords)}개 조회 성공")
        else:
            logger.warning(f"키워드 랭킹 API 오류: {keyword_response.get('error', '알 수 없는 오류')}")
            popular_keywords = [{
                "rank": 1,
                "keyword": "키워드 데이터를 불러오는 중입니다.",
                "count": 0,
                "trend": "stable"
            }]
    
    except Exception as e:
        logger.error(f"인기 키워드 조회 오류: {e}", exc_info=True)
        popular_keywords = [{
            "rank": 1,
            "keyword": "키워드 데이터 로딩 중 오류 발생",
            "count": 0,
            "trend": "stable"
        }]
    
    return LatestNewsResponse(
        today_issues=today_issues,
        popular_keywords=popular_keywords,
        timestamp=datetime.now().isoformat()
    ) 