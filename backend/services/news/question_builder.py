"""
키워드 기반 맞춤형 질문 생성 모듈

이 모듈은 "AND 우선, 부족하면 OR" 전략을 사용하여 빅카인즈 API 기반의
키워드 관련 맞춤형 질문을 생성합니다.

Usage:
    from backend.services.news.question_builder import build_questions
    questions = await build_questions("삼성전자", client, date_from, date_until)
"""

import asyncio
import random
from datetime import datetime, timedelta
from typing import List, Dict, Set, Optional, Any, Tuple

from backend.utils.logger import setup_logger

# 로거 설정
logger = setup_logger("services.news.question_builder")

# 상수 정의
STOPWORDS = {"및", "등", "관련", "통해", "위해", "보다", "대한", "위한", "따른", "의한", "대해"}
MIN_DOCS = 5  # AND/OR 성공 판정 기준
MAX_Q = 7     # UI에 노출할 최대 질문 수

# 질문 유형별 템플릿
TEMPLATES = {
    "refine": ["{base}의 {kw} 이슈는?", "{kw}와 관련된 {base} 동향은?", "{base}와 {kw}의 연관성은?"],
    "expand": ["{base}와 {kws} 관계가 궁금합니다.", "{base}가 {kws} 분야에 미치는 영향은?", "{base}와 {kws}의 최근 뉴스는?"],
    "exclude": ["{kw}를 제외한 {base} 주요 이슈는?", "{base}에서 {kw}를 뺀 화제는?", "{base}의 {kw} 이외 동향은?"],
    "basic": ["{base} 최근 동향은?", "{base} 관련 주요 뉴스는?", "{base}에 대해 알고 싶습니다."]
}


def filter_keywords(words: List[str]) -> List[str]:
    """
    키워드 필터링: 불용어 및 한 글자 단어 제거
    
    Args:
        words: 필터링할 키워드 목록
        
    Returns:
        필터링된 키워드 목록 (중복 제거)
    """
    # 입력값 검증: None이거나 빈 리스트면 빈 리스트 반환
    if not words:
        return []
        
    out = []
    for w in words:
        # 유효성 검사: 문자열이 아니면 건너뛰기
        if not isinstance(w, str):
            continue
            
        # 한 글자 단어 또는 불용어 제외
        if len(w) <= 1 or w in STOPWORDS:
            continue
        out.append(w)
    
    # 중복 제거 (순서 유지)
    return list(dict.fromkeys(out))


def merge_similar(words: List[str]) -> List[str]:
    """
    유사 키워드 병합
    
    Args:
        words: 병합할 키워드 목록
        
    Returns:
        병합된 키워드 목록
    """
    # 입력값 검증: None이거나 빈 리스트면 빈 리스트 반환
    if not words:
        return []
        
    try:
        from rapidfuzz import fuzz
        
        merged = []
        for w in words:
            # 유효성 검사: 문자열이 아니면 건너뛰기
            if not isinstance(w, str):
                continue
                
            # 이미 있는 단어와 85% 이상 유사하면 건너뛰기
            if any(fuzz.ratio(w, m) >= 85 for m in merged):
                continue
            merged.append(w)
        return merged
    except Exception as e:
        logger.error(f"유사 키워드 병합 오류: {e}")
        # 오류 발생 시 원본 반환
        return words


def score_keywords(
    rel: List[str], 
    topn: List[str],
    recent_set: Set[str]
) -> Dict[str, float]:
    """
    키워드 점수화
    
    Args:
        rel: 연관어 API 결과 (순서 중요)
        topn: TopN API 결과 (순서 중요)
        recent_set: 최근 7일 연관어 세트 (가중치 부여용)
        
    Returns:
        키워드별 점수 딕셔너리
    """
    # 입력값 검증
    if not rel:
        rel = []
    if not topn:
        topn = []
    if not recent_set:
        recent_set = set()
        
    # 타입 변환: list나 set이 아닌 경우 변환
    if not isinstance(rel, list):
        rel = []
    if not isinstance(topn, list):
        topn = []
    if not isinstance(recent_set, set):
        try:
            recent_set = set(recent_set)
        except:
            recent_set = set()
    
    scores = {}
    
    # 연관어 역순위 (순위가 높을수록 큰 점수)
    for i, kw in enumerate(rel):
        # 키가 해시 가능한지 확인 (문자열 등)
        if not isinstance(kw, (str, int, float, bool, tuple)):
            continue
        scores[kw] = scores.get(kw, 0) + (len(rel) - i)
    
    # TopN 키워드 (가중치 0.7)
    for i, kw in enumerate(topn):
        # 키가 해시 가능한지 확인 (문자열 등)
        if not isinstance(kw, (str, int, float, bool, tuple)):
            continue
        scores[kw] = scores.get(kw, 0) + (len(topn) - i) * 0.7
    
    # 중복 키워드 보너스 (+5)
    try:
        # 안전하게 집합 생성
        rel_set = set(kw for kw in rel if isinstance(kw, (str, int, float, bool, tuple)))
        topn_set = set(kw for kw in topn if isinstance(kw, (str, int, float, bool, tuple)))
        
        for kw in rel_set & topn_set:
            if kw in scores:  # 이미 점수가 있는 경우만 추가
                scores[kw] += 5
    except Exception as e:
        logger.warning(f"중복 키워드 보너스 계산 오류: {e}")
    
    # 최근성 가중치 (1.5배)
    for kw in recent_set:
        if kw in scores:  # 이미 점수가 있는 경우만 가중치 적용
            scores[kw] *= 1.5
    
    return scores


def pick_template(tp: str) -> str:
    """템플릿 유형에서 랜덤 선택"""
    templates = TEMPLATES.get(tp, TEMPLATES["basic"])
    return random.choice(templates)


def sanitize_list(data: Any, name: str = "unknown") -> List[str]:
    """
    리스트 데이터 정제 (해시 불가능한 요소 제거)
    
    Args:
        data: 정제할 데이터
        name: 로깅용 데이터 이름
        
    Returns:
        해시 가능한 문자열만 포함한 리스트
    """
    result = []
    
    try:
        # None이거나 빈 값인 경우
        if data is None:
            logger.debug(f"{name} 데이터가 None")
            return result
            
        # 빈 리스트인 경우
        if isinstance(data, list) and len(data) == 0:
            logger.debug(f"{name} 데이터가 빈 리스트")
            return result
        
        # 리스트가 아니면 빈 리스트 반환
        if not isinstance(data, list):
            logger.warning(f"{name} 데이터가 리스트가 아님: {type(data)}")
            # 문자열인 경우 리스트로 변환
            if isinstance(data, str):
                return [data] if data.strip() else []
            return result
            
        # 중첩 리스트 처리
        for item in data:
            try:
                # 중첩 리스트인 경우 재귀적으로 처리
                if isinstance(item, list):
                    # 중첩 리스트를 평탄화
                    flattened = sanitize_list(item, f"{name}-nested")
                    result.extend(flattened)
                # 딕셔너리인 경우 (word 키가 있으면 추출)
                elif isinstance(item, dict):
                    if "word" in item and isinstance(item["word"], str):
                        word = item["word"].strip()
                        if word:
                            result.append(word)
                    elif "name" in item and isinstance(item["name"], str):
                        name_val = item["name"].strip()
                        if name_val:
                            result.append(name_val)
                    elif "keyword" in item and isinstance(item["keyword"], str):
                        keyword_val = item["keyword"].strip()
                        if keyword_val:
                            result.append(keyword_val)
                # 문자열인 경우 바로 추가
                elif isinstance(item, str):
                    cleaned_item = item.strip()
                    if cleaned_item:
                        result.append(cleaned_item)
                # 숫자나 기타 타입은 문자열로 변환
                elif isinstance(item, (int, float)):
                    result.append(str(item))
                # 튜플인 경우 첫 번째 요소만 사용
                elif isinstance(item, tuple) and len(item) > 0:
                    if isinstance(item[0], str):
                        result.append(item[0])
            except Exception as e:
                logger.warning(f"{name} 데이터 항목 처리 오류: {e}, 항목 타입: {type(item)}")
                continue
    
    except Exception as e:
        logger.error(f"{name} 데이터 정제 중 오류: {e}")
        return []
            
    # 중복 제거 및 빈 문자열 제거
    clean_result = []
    seen = set()
    for item in result:
        if item and item not in seen:
            seen.add(item)
            clean_result.append(item)
    
    logger.debug(f"{name} 정제 결과: {len(clean_result)}개 항목")
    return clean_result


async def build_questions(
    base: str,
    client: Any,  # BigKindsClient 타입 (순환 임포트 방지)
    date_from: str,
    date_until: str
) -> List[Dict[str, Any]]:
    """
    키워드 기반 맞춤형 질문 생성
    
    Args:
        base: 기본 키워드
        client: BigKindsClient 인스턴스
        date_from: 시작일 (YYYY-MM-DD)
        date_until: 종료일 (YYYY-MM-DD)
        
    Returns:
        생성된 질문 목록
    """
    logger.info(f"'{base}' 키워드 기반 맞춤형 질문 생성 시작")
    
    # 기본 질문 준비 (오류 발생 시 최소한의 결과)
    basic_question = {
        "type": "basic",
        "query": base,
        "question": f"{base} 관련 주요 뉴스는?"
    }
    
    # 1. 키워드 수집
    try:
        rel30_raw, top30_raw = await asyncio.gather(
            client.get_related_keywords(
                keyword=base, 
                date_from=date_from,
                date_to=date_until,
                max_count=50
            ),
            client.get_keyword_topn(
                keyword=base,
                date_from=date_from,
                date_to=date_until,
                limit=50
            )
        )
        
        # API 응답 로깅 (디버깅용)
        logger.debug(f"연관어 API 응답 형식: {type(rel30_raw)}")
        logger.debug(f"연관어 API 원본 데이터: {rel30_raw[:5] if rel30_raw else []}...")  # 처음 5개만 로깅
        logger.debug(f"TopN API 응답 형식: {type(top30_raw)}")
        logger.debug(f"TopN API 원본 데이터: {top30_raw[:5] if top30_raw else []}...")  # 처음 5개만 로깅
        
        # 데이터 정제 (해시 불가능한 요소 제거)
        rel30 = sanitize_list(rel30_raw, "연관어")
        top30 = sanitize_list(top30_raw, "TopN")
        
    except Exception as e:
        logger.error(f"키워드 수집 오류: {str(e)}")
        logger.error(f"키워드 수집 상세 오류: {type(e).__name__}", exc_info=True)
        return [basic_question]  # 오류 시 기본 질문만 반환
    
    # 최근 7일 추가 가중치 세트
    try:
        today = datetime.now()
        df7 = (today - timedelta(days=7)).strftime("%Y-%m-%d")
        recent_rel_raw = await client.get_related_keywords(
            keyword=base,
            date_from=df7,
            date_to=date_until,
            max_count=20
        )
        
        # 데이터 정제 후 집합으로 변환
        recent_rel = sanitize_list(recent_rel_raw, "최근 연관어")
        recent_set = set(recent_rel)
        
    except Exception as e:
        logger.error(f"최근 연관어 수집 오류: {str(e)}")
        logger.error(f"최근 연관어 수집 상세 오류: {type(e).__name__}", exc_info=True)
        recent_set = set()
    
    # 2. 전처리
    logger.debug(f"수집된 연관어: {len(rel30)}개, TopN: {len(top30)}개, 최근 7일: {len(recent_set)}개")
    
    try:
        # 리스트 합치기 전에 안전성 확인
        combined_keywords = []
        if rel30 and isinstance(rel30, list):
            combined_keywords.extend(rel30)
        if top30 and isinstance(top30, list):
            combined_keywords.extend(top30)
            
        kws = merge_similar(filter_keywords(combined_keywords))
        scores = score_keywords(rel30, top30, recent_set)
        
        # 상위 15개 키워드 선택
        kws = sorted(kws, key=lambda k: scores.get(k, 0), reverse=True)[:15]
        logger.debug(f"필터링 후 상위 키워드: {kws}")
    except Exception as e:
        logger.error(f"키워드 전처리 오류: {str(e)}")
        logger.error(f"키워드 전처리 상세 오류: {type(e).__name__}", exc_info=True)
        return [basic_question]  # 오류 시 기본 질문만 반환
    
    # 키워드가 없는 경우 기본 질문만 반환
    if not kws:
        logger.warning(f"'{base}' 키워드에 대한 연관 키워드가 없습니다.")
        return [basic_question]
    
    questions = []
    
    # 3. 기본 질문
    tpl = pick_template("basic")
    questions.append({
        "type": "basic",
        "query": base,
        "question": tpl.format(base=base)
    })
    
    # 4. Refine (AND) or fallback OR
    for kw in kws[:5]:
        q_and = f"{base} AND {kw}"
        try:
            cnt = await client.quick_count(
                query=q_and,
                date_from=date_from,
                date_to=date_until
            )
            
            if cnt >= MIN_DOCS:
                # AND 쿼리 성공
                tpl = pick_template("refine")
                questions.append({
                    "type": "refine",
                    "query": q_and,
                    "question": tpl.format(base=base, kw=kw)
                })
            else:
                # AND 쿼리 실패, OR로 폴백
                q_or = f"{base} OR {kw}"
                cnt2 = await client.quick_count(
                    query=q_or,
                    date_from=date_from,
                    date_to=date_until
                )
                
                if cnt2 >= MIN_DOCS:
                    tpl = pick_template("expand")
                    questions.append({
                        "type": "expand",
                        "query": q_or,
                        "question": tpl.format(base=base, kws=kw)
                    })
        except Exception as e:
            logger.error(f"쿼리 카운트 오류 ({q_and}): {str(e)}")
    
    # 5. Expand OR (두 키워드 묶음)
    if len(kws) >= 3:
        try:
            kw1, kw2 = kws[1], kws[2]
            or_part = f"({kw1} OR {kw2})"
            q_exp = f"{base} AND {or_part}"
            
            if await client.quick_count(q_exp, date_from, date_until) >= MIN_DOCS:
                tpl = pick_template("expand")
                kws_txt = f"{kw1}·{kw2}"
                questions.append({
                    "type": "expand", 
                    "query": q_exp,
                    "question": tpl.format(base=base, kws=kws_txt)
                })
        except Exception as e:
            logger.error(f"확장 쿼리 카운트 오류: {str(e)}")
    
    # 6. Exclude
    for kw in kws[-3:]:
        try:
            q_not = f"{base} NOT {kw}"
            if await client.quick_count(q_not, date_from, date_until) >= MIN_DOCS:
                tpl = pick_template("exclude")
                questions.append({
                    "type": "exclude",
                    "query": q_not,
                    "question": tpl.format(base=base, kw=kw)
                })
                
                # 최대 질문 수 도달 시 중단
                if len(questions) >= MAX_Q:
                    break
        except Exception as e:
            logger.error(f"제외 쿼리 카운트 오류 ({q_not}): {str(e)}")
    
    # 결과가 없으면 기본 질문만 반환
    if not questions:
        logger.warning(f"'{base}' 키워드에 대한 질문을 생성하지 못했습니다. 기본 질문만 반환합니다.")
        return [basic_question]
    
    logger.info(f"'{base}' 키워드 기반 질문 {len(questions)}개 생성 완료")
    return questions[:MAX_Q] 