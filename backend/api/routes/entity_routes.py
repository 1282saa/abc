"""
엔티티(종목) 관련 API 라우트

카테고리별 엔티티 관리 및 동의어 확장 검색 기능을 제공합니다.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from backend.constants.entity_variants import (
    CATEGORIES,
    ENTITY_VARIANTS,
    get_all_entities,
    get_entity_by_keyword,
    get_entities_by_category,
    expand_query_with_variants,
    expand_query_with_boosted_variants,
    expand_query_with_fuzzy_search,
    search_entities
)
from backend.api.clients.bigkinds.client import BigKindsClient
from backend.api.dependencies import get_bigkinds_client
from backend.utils.logger import setup_logger

# API 라우터 생성
router = APIRouter(prefix="/api/entity", tags=["엔티티"])

# 응답 모델 정의
class CategoryInfo(BaseModel):
    """카테고리 정보"""
    key: str
    name: str
    count: int

class CategoryResponse(BaseModel):
    """카테고리 목록 응답"""
    categories: List[CategoryInfo]

class EntityResponse(BaseModel):
    """엔티티 정보 응답"""
    id: str
    name: str
    code: str
    variants: List[str]
    category: str
    category_name: str

class EntitiesListResponse(BaseModel):
    """엔티티 목록 응답"""
    entities: List[EntityResponse]
    total: int

class EntitySearchResponse(BaseModel):
    """엔티티 검색 응답"""
    results: List[Dict[str, Any]]
    total: int
    query: str

# 엔드포인트 정의
@router.get("/categories", response_model=CategoryResponse)
async def get_categories():
    """모든 카테고리 목록 조회"""
    logger = setup_logger("api.entity.categories")
    logger.info("카테고리 목록 요청")
    
    categories = [
        CategoryInfo(
            key=key, 
            name=name, 
            count=len(ENTITY_VARIANTS[key]["entities"])
        )
        for key, name in CATEGORIES.items()
    ]
    
    return CategoryResponse(categories=categories)

@router.get("/category/{category_key}", response_model=EntitiesListResponse)
async def get_category_entities(
    category_key: str,
    search: Optional[str] = Query(None, description="검색어")
):
    """특정 카테고리의 엔티티 목록 조회"""
    logger = setup_logger("api.entity.category_entities")
    logger.info(f"카테고리 엔티티 목록 요청: {category_key}")
    
    if category_key not in ENTITY_VARIANTS:
        raise HTTPException(status_code=404, detail="카테고리를 찾을 수 없습니다")
    
    entities = get_entities_by_category(category_key)
    
    # 검색어가 있으면 필터링
    if search:
        search_lower = search.lower()
        entities = [
            entity for entity in entities
            if search_lower in entity["name"].lower() or
            any(search_lower in variant.lower() for variant in entity["variants"])
        ]
    
    # 응답 형식으로 변환
    response_entities = [
        EntityResponse(
            id=entity["id"],
            name=entity["name"],
            code=entity["code"],
            variants=entity["variants"],
            category=category_key,
            category_name=ENTITY_VARIANTS[category_key]["name"]
        )
        for entity in entities
    ]
    
    return {
        "entities": response_entities,
        "total": len(response_entities)
    }

@router.get("/search", response_model=EntitySearchResponse)
async def search_entities_endpoint(
    q: str = Query(..., description="검색어", min_length=1)
):
    """엔티티 검색 (모든 카테고리에서)"""
    logger = setup_logger("api.entity.search")
    logger.info(f"엔티티 검색 요청: {q}")
    
    results = search_entities(q)
    
    return {
        "results": results,
        "total": len(results),
        "query": q
    }

@router.get("/entity/{entity_id}")
async def get_entity_detail(
    entity_id: str,
    category: str = Query(..., description="카테고리 키")
):
    """특정 엔티티 상세 정보 조회"""
    logger = setup_logger("api.entity.detail")
    logger.info(f"엔티티 상세 정보 요청: {entity_id} (카테고리: {category})")
    
    if category not in ENTITY_VARIANTS:
        raise HTTPException(status_code=404, detail="카테고리를 찾을 수 없습니다")
    
    # 해당 카테고리에서 엔티티 찾기
    entities = get_entities_by_category(category)
    entity = next((e for e in entities if e["id"] == entity_id), None)
    
    if not entity:
        raise HTTPException(status_code=404, detail="엔티티를 찾을 수 없습니다")
    
    return EntityResponse(
        id=entity["id"],
        name=entity["name"],
        code=entity["code"],
        variants=entity["variants"],
        category=category,
        category_name=ENTITY_VARIANTS[category]["name"]
    )

@router.post("/news/{entity_id}")
async def get_entity_news(
    entity_id: str,
    category: str = Query(..., description="카테고리 키"),
    date_from: Optional[str] = Query(None, description="시작일 (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="종료일 (YYYY-MM-DD)"),
    provider: Optional[List[str]] = Query(None, description="언론사 필터"),
    search_mode: str = Query("enhanced", description="검색 모드 (enhanced, boosted, fuzzy, basic)"),
    boost_factor: float = Query(2.0, description="부스트 가중치 (boosted 모드용)"),
    fuzziness: int = Query(1, description="퍼지 검색 정도 (fuzzy 모드용)"),
    exclude_prism: bool = Query(True, description="PRISM 기사 제외 여부 (서울경제 대상)"),
    bigkinds_client: BigKindsClient = Depends(get_bigkinds_client)
):
    """엔티티 관련 뉴스 검색 (개선된 동의어 확장 포함)"""
    logger = setup_logger("api.entity.news")
    logger.info(f"엔티티 뉴스 요청: {entity_id} (카테고리: {category}, 검색모드: {search_mode})")
    
    if category not in ENTITY_VARIANTS:
        raise HTTPException(status_code=404, detail="카테고리를 찾을 수 없습니다")
    
    # 엔티티 찾기
    entities = get_entities_by_category(category)
    entity = next((e for e in entities if e["id"] == entity_id), None)
    
    if not entity:
        raise HTTPException(status_code=404, detail="엔티티를 찾을 수 없습니다")
    
    # 날짜 기본값 설정
    if not date_from:
        date_from = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    if not date_to:
        date_to = datetime.now().strftime("%Y-%m-%d")
    
    # 검색 모드에 따른 동의어 확장 쿼리 생성
    # PRISM 제외 여부 결정 (서울경제 필터가 있을 때는 제외하지 않음)
    should_exclude_prism = exclude_prism and not (provider and "서울경제" in provider)
    
    if search_mode == "boosted":
        expanded_query = expand_query_with_boosted_variants(entity["name"], boost_factor, should_exclude_prism)
    elif search_mode == "fuzzy":
        expanded_query = expand_query_with_fuzzy_search(entity["name"], fuzziness, should_exclude_prism)
    elif search_mode == "basic":
        # 기본 OR 연산만 사용
        basic_query = " OR ".join([f'"{variant}"' for variant in entity["variants"]])
        if should_exclude_prism:
            expanded_query = f"({basic_query}) AND NOT \"PRISM\""
        else:
            expanded_query = f"({basic_query})"
    else:  # enhanced (기본값)
        # PRISM 제외 설정과 함께 쿼리 확장
        expanded_query = expand_query_with_variants(entity["name"], should_exclude_prism)
    
    logger.info(f"확장된 검색 쿼리 ({search_mode}): {expanded_query}")
    
    try:
        # BigKinds API로 뉴스 타임라인 조회
        result = bigkinds_client.get_company_news_timeline(
            company_name=expanded_query,  # 확장된 쿼리 사용
            date_from=date_from,
            date_to=date_to,
            return_size=50,
            provider=provider,
            exclude_prism=exclude_prism  # PRISM 기사 제외 옵션 전달
        )
        
        if not result.get("success", False):
            raise HTTPException(status_code=404, detail="뉴스를 찾을 수 없습니다")
        
        # 결과 로깅
        total_count = result.get("total_count", 0)
        logger.info(f"검색 결과 - 총 {total_count}개 기사 찾음")
        
        return {
            "entity": entity,
            "category": category,
            "category_name": ENTITY_VARIANTS[category]["name"],
            "period": {
                "from": date_from,
                "to": date_to
            },
            "total_count": total_count,
            "timeline": result.get("timeline", []),
            "search_query": expanded_query,
            "search_mode": search_mode,
            "search_params": {
                "boost_factor": boost_factor if search_mode == "boosted" else None,
                "fuzziness": fuzziness if search_mode == "fuzzy" else None
            }
        }
        
    except Exception as e:
        logger.error(f"엔티티 뉴스 조회 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"뉴스 조회 중 오류 발생: {str(e)}")

@router.get("/expand-query")
async def expand_entity_query(
    keyword: str = Query(..., description="검색 키워드"),
    mode: str = Query("all", description="확장 모드 (all, enhanced, boosted, fuzzy, basic)"),
    boost_factor: float = Query(2.0, description="부스트 가중치"),
    fuzziness: int = Query(1, description="퍼지 검색 정도"),
    exclude_prism: bool = Query(True, description="PRISM 기사 제외 여부")
):
    """키워드의 동의어 확장 쿼리 생성 (다양한 모드 지원)"""
    logger = setup_logger("api.entity.expand_query")
    logger.info(f"쿼리 확장 요청: {keyword} (모드: {mode})")
    
    entity = get_entity_by_keyword(keyword)
    
    # 다양한 확장 방식 결과
    expansions = {}
    
    if mode == "all" or mode == "enhanced":
        expansions["enhanced"] = expand_query_with_variants(keyword, exclude_prism)
    
    if mode == "all" or mode == "boosted":
        expansions["boosted"] = expand_query_with_boosted_variants(keyword, boost_factor, exclude_prism)
    
    if mode == "all" or mode == "fuzzy":
        expansions["fuzzy"] = expand_query_with_fuzzy_search(keyword, fuzziness, exclude_prism)
    
    if mode == "all" or mode == "basic":
        if entity:
            expansions["basic"] = " OR ".join([f'"{variant}"' for variant in entity["variants"]])
        else:
            expansions["basic"] = f'"{keyword}"'
    
    # 단일 모드인 경우 해당 결과만 반환
    if mode != "all" and mode in expansions:
        expanded_query = expansions[mode]
    else:
        expanded_query = expansions.get("enhanced", f'"{keyword}"')
    
    result = {
        "original": keyword,
        "expanded": expanded_query,
        "entity": entity,
        "variants": entity["variants"] if entity else [],
        "mode": mode
    }
    
    # 모든 모드 요청 시 각 확장 방식 결과 포함
    if mode == "all":
        result["expansions"] = expansions
        result["comparison"] = {
            "enhanced_length": len(expansions.get("enhanced", "")),
            "boosted_length": len(expansions.get("boosted", "")),
            "fuzzy_length": len(expansions.get("fuzzy", "")),
            "basic_length": len(expansions.get("basic", ""))
        }
    
    return result