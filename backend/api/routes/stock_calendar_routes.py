"""
주식 캘린더 API 라우트

국내외 주요 투자 일정 및 이벤트를 관리하는 API 엔드포인트를 정의합니다.
"""

from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
from pathlib import Path
import sys
import json

# 프로젝트 루트 디렉토리 찾기
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.utils.logger import setup_logger
from backend.services.perplexity_client import perplexity_client
from backend.services.exchange_rate_service import exchange_rate_service
from backend.services.dart_api_client import dart_api_client
from backend.services.kis_api_client import kis_api_client
from backend.services.upbit_api_client import upbit_api_client
from backend.services.us_stock_api_client import us_stock_api_client

# 로거 설정
logger = setup_logger("api.stock_calendar")

# API 라우터 생성
router = APIRouter(prefix="/api/stock-calendar", tags=["주식캘린더"])

# 이벤트 타입 정의
EVENT_TYPES = ["earnings", "dividend", "holiday", "ipo", "economic", "split", "disclosure", "crypto"]

# 한국 주요 공휴일 및 휴장일 정의
KOREAN_HOLIDAYS = {
    "2025": [
        {"date": "2025-01-01", "name": "신정", "type": "holiday"},
        {"date": "2025-01-28", "name": "설날 연휴", "type": "holiday"},
        {"date": "2025-01-29", "name": "설날", "type": "holiday"},
        {"date": "2025-01-30", "name": "설날 연휴", "type": "holiday"},
        {"date": "2025-03-01", "name": "삼일절", "type": "holiday"},
        {"date": "2025-03-03", "name": "부처님 오신 날", "type": "holiday"},
        {"date": "2025-05-05", "name": "어린이날", "type": "holiday"},
        {"date": "2025-05-06", "name": "대체공휴일", "type": "holiday"},
        {"date": "2025-06-06", "name": "현충일", "type": "holiday"},
        {"date": "2025-08-15", "name": "광복절", "type": "holiday"},
        {"date": "2025-10-03", "name": "개천절", "type": "holiday"},
        {"date": "2025-10-09", "name": "한글날", "type": "holiday"},
        {"date": "2025-12-25", "name": "크리스마스", "type": "holiday"},
    ]
}

# 주요 경제 이벤트 (정기적으로 발생하는 이벤트들)
REGULAR_ECONOMIC_EVENTS = [
    {
        "title": "한국은행 기준금리 결정",
        "description": "한국은행 통화정책위원회 기준금리 결정",
        "eventType": "economic",
        "marketType": "domestic",
        "frequency": "monthly",  # 매월 셋째주 목요일
    },
    {
        "title": "미국 FOMC 회의",
        "description": "연준 연방공개시장위원회 금리 결정",
        "eventType": "economic", 
        "marketType": "global",
        "frequency": "quarterly",  # 분기별
    }
]

@router.get("/events")
async def get_calendar_events(
    start_date: str = Query(..., description="시작 날짜 (YYYY-MM-DD)"),
    end_date: str = Query(..., description="종료 날짜 (YYYY-MM-DD)"),
    market_type: Optional[str] = Query(None, description="시장 유형 (domestic, us, global, crypto)"),
    event_types: Optional[List[str]] = Query(None, description="이벤트 유형 필터"),
    include_disclosures: bool = Query(True, description="DART 공시 포함 여부"),
    include_earnings: bool = Query(True, description="실적발표 일정 포함 여부"),
    include_crypto: bool = Query(True, description="가상화폐 이벤트 포함 여부"),
):
    """캘린더 이벤트 조회
    
    지정된 기간의 투자 관련 이벤트를 조회합니다.
    DART API를 통해 실제 공시 정보를 포함합니다.
    """
    logger.info(f"캘린더 이벤트 조회: {start_date} ~ {end_date}")
    
    try:
        # 날짜 유효성 검사
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        if start > end:
            raise HTTPException(status_code=400, detail="시작일이 종료일보다 늦습니다.")
        
        all_events = []
        
        # 1. 한국 공휴일 및 휴장일 추가
        if not market_type or market_type == "domestic":
            year = str(start.year)
            if year in KOREAN_HOLIDAYS:
                for holiday in KOREAN_HOLIDAYS[year]:
                    holiday_date = datetime.strptime(holiday["date"], "%Y-%m-%d").date()
                    
                    # 날짜 범위 확인
                    if not (start <= holiday_date <= end):
                        continue
                    
                    # 이벤트 유형 필터
                    if event_types and "holiday" not in event_types:
                        continue
                    
                    holiday_event = {
                        "id": f"holiday_{holiday['date']}",
                        "title": f"🇰🇷 {holiday['name']}",
                        "date": holiday["date"],
                        "eventType": "holiday",
                        "description": "한국 증시 휴장",
                        "marketType": "domestic",
                        "country": "KR"
                    }
                    all_events.append(holiday_event)
        
        # 2. DART 공시 이벤트 추가
        if include_disclosures and (not market_type or market_type == "domestic"):
            try:
                # 국내 공시 이벤트 조회
                disclosure_events = await dart_api_client.get_upcoming_disclosure_events(
                    start_date=start_date,
                    end_date=end_date,
                    corp_cls="Y" if not market_type else None
                )
                
                # 이벤트 유형 필터 적용
                for event in disclosure_events:
                    if event_types and "disclosure" not in event_types:
                        continue
                    all_events.append(event)
                
                logger.info(f"DART 공시 이벤트 {len(disclosure_events)}건 추가")
                
            except Exception as e:
                logger.warning(f"DART 공시 조회 실패: {e}")
        
        # 3. KIS API를 통한 국내 주식 이벤트 추가
        if include_earnings and (not market_type or market_type == "domestic"):
            try:
                async with kis_api_client as kis:
                    # 국내 실적 발표 일정
                    earnings_events = await kis.get_earnings_calendar(start_date, end_date)
                    
                    # 캘린더 이벤트 형식으로 변환
                    for event in earnings_events:
                        if event_types and "earnings" not in event_types:
                            continue
                        
                        calendar_event = {
                            "id": f"kr_earnings_{event.get('stock_code')}_{event.get('announce_date')}",
                            "title": f"{event.get('company_name', '')} 실적발표",
                            "date": event.get("announce_date"),
                            "eventType": "earnings",
                            "stockCode": event.get("stock_code"),
                            "stockName": event.get("company_name"),
                            "description": f"{event.get('company_name', '')} {event.get('period', '')} 실적발표",
                            "marketType": "domestic",
                            "period": event.get("period"),
                            "market": event.get("market"),
                            "sector": event.get("sector")
                        }
                        all_events.append(calendar_event)
                    
                    # 국내 배당 일정
                    dividend_events = await kis.get_dividend_calendar(start_date, end_date)
                    
                    for event in dividend_events:
                        if event_types and "dividend" not in event_types:
                            continue
                        
                        calendar_event = {
                            "id": f"kr_dividend_{event.get('stock_code')}_{event.get('ex_dividend_date')}",
                            "title": f"{event.get('company_name', '')} 배당",
                            "date": event.get("ex_dividend_date"),
                            "eventType": "dividend",
                            "stockCode": event.get("stock_code"),
                            "stockName": event.get("company_name"),
                            "description": f"배당금: {event.get('dividend_amount', '')}원 (수익률: {event.get('yield', '')}%)",
                            "marketType": "domestic",
                            "dividend_amount": event.get("dividend_amount"),
                            "yield": event.get("yield"),
                            "record_date": event.get("record_date"),
                            "payment_date": event.get("payment_date")
                        }
                        all_events.append(calendar_event)
                    
                    logger.info(f"KIS 국내 주식 이벤트 {len(earnings_events + dividend_events)}건 추가")
                    
            except Exception as e:
                logger.warning(f"KIS 국내 주식 이벤트 조회 실패: {e}")
        
        # 4. 미국 주식 이벤트 추가
        if include_earnings and (not market_type or market_type == "us"):
            try:
                async with us_stock_api_client as us_client:
                    # 미국 실적 발표 일정
                    us_earnings_events = await us_client.get_earnings_calendar(start, end)
                    
                    # 캘린더 이벤트 형식으로 변환
                    for event in us_earnings_events:
                        if event_types and "earnings" not in event_types:
                            continue
                        
                        calendar_event = {
                            "id": f"us_earnings_{event['symbol']}_{event['report_date']}",
                            "title": f"{event['company_name']} 실적발표",
                            "date": event["report_date"],
                            "eventType": "earnings",
                            "stockCode": event["symbol"],
                            "stockName": event["company_name"],
                            "description": f"{event['fiscal_period']} 실적발표 ({event['time']})",
                            "marketType": "us",
                            "sector": event.get("sector", ""),
                            "estimate_eps": event.get("estimate_eps"),
                            "time": event.get("time")
                        }
                        all_events.append(calendar_event)
                    
                    # 미국 배당 일정
                    us_dividend_events = await us_client.get_dividend_calendar(start, end)
                    
                    for event in us_dividend_events:
                        if event_types and "dividend" not in event_types:
                            continue
                        
                        calendar_event = {
                            "id": f"us_dividend_{event['symbol']}_{event['ex_dividend_date']}",
                            "title": f"{event['company_name']} 배당",
                            "date": event["ex_dividend_date"],
                            "eventType": "dividend",
                            "stockCode": event["symbol"],
                            "stockName": event["company_name"],
                            "description": f"배당금: ${event['dividend_amount']} (수익률: {event['yield']}%)",
                            "marketType": "us",
                            "dividend_amount": event.get("dividend_amount"),
                            "yield": event.get("yield"),
                            "record_date": event.get("record_date"),
                            "payment_date": event.get("payment_date")
                        }
                        all_events.append(calendar_event)
                    
                    # 미국 경제 지표
                    us_economic_events = await us_client.get_economic_calendar(start, end)
                    
                    for event in us_economic_events:
                        if event_types and "economic" not in event_types:
                            continue
                        
                        calendar_event = {
                            "id": f"us_economic_{event['event']}_{event['date']}",
                            "title": f"🇺🇸 {event['event']}",
                            "date": event["date"],
                            "eventType": "economic",
                            "description": f"예상: {event['forecast']} (이전: {event['previous']})",
                            "marketType": "us",
                            "importance": event.get("importance"),
                            "time": event.get("time"),
                            "forecast": event.get("forecast"),
                            "previous": event.get("previous"),
                            "impact": event.get("impact")
                        }
                        all_events.append(calendar_event)
                    
                    logger.info(f"미국 주식 이벤트 {len(us_earnings_events + us_dividend_events + us_economic_events)}건 추가")
                    
            except Exception as e:
                logger.warning(f"미국 주식 이벤트 조회 실패: {e}")
        
        # 5. 가상화폐 이벤트 추가
        if include_crypto and (not market_type or market_type == "crypto"):
            try:
                async with upbit_api_client as upbit:
                    # 가상화폐 주요 이벤트 (상장, 상장폐지, 하드포크 등)
                    crypto_events = await upbit.get_crypto_events(start_date, end_date)
                    
                    # 이벤트 유형 필터 적용
                    for event in crypto_events:
                        if event_types and event.get("eventType") not in event_types:
                            continue
                        all_events.append(event)
                    
                    # 주요 가상화폐 시가총액 변동 이벤트도 추가
                    major_cryptos = await upbit.get_major_cryptos()
                    current_date = datetime.now().date()
                    
                    # 급등/급락 이벤트 감지 (24시간 변동률 5% 이상)
                    for crypto in major_cryptos:
                        if abs(crypto.change_rate) >= 5.0:  # 5% 이상 변동
                            if start <= current_date <= end:
                                movement_type = "상승" if crypto.change_rate > 0 else "하락"
                                crypto_event = {
                                    "id": f"crypto_movement_{crypto.symbol}_{current_date}",
                                    "title": f"💰 {crypto.korean_name} 급{movement_type}",
                                    "date": current_date.strftime("%Y-%m-%d"),
                                    "eventType": "crypto",
                                    "cryptoSymbol": crypto.symbol,
                                    "cryptoName": crypto.korean_name,
                                    "description": f"{crypto.korean_name} 24시간 {crypto.change_rate:+.1f}% 변동 (현재가: {crypto.trade_price:,.0f}원)",
                                    "marketType": "crypto",
                                    "change_rate": crypto.change_rate,
                                    "current_price": crypto.trade_price,
                                    "change_price": crypto.change_price
                                }
                                if event_types and "crypto" in event_types:
                                    all_events.append(crypto_event)
                                elif not event_types:
                                    all_events.append(crypto_event)
                    
                    logger.info(f"가상화폐 이벤트 {len(crypto_events)}건 추가")
                    
            except Exception as e:
                logger.warning(f"가상화폐 이벤트 조회 실패: {e}")
        
        # 6. 글로벌 경제 지표 및 중앙은행 정책 이벤트 추가
        if not market_type or market_type in ["global", "us"]:
            try:
                # 미국 연준 FOMC 회의 일정 (실제 API에서 가져오거나 고정 일정 사용)
                fomc_dates = [
                    "2025-01-28", "2025-01-29",  # 1월 FOMC
                    "2025-03-18", "2025-03-19",  # 3월 FOMC
                    "2025-04-29", "2025-04-30",  # 4월 FOMC
                    "2025-06-10", "2025-06-11",  # 6월 FOMC
                    "2025-07-29", "2025-07-30",  # 7월 FOMC
                    "2025-09-16", "2025-09-17",  # 9월 FOMC
                    "2025-10-28", "2025-10-29",  # 10월 FOMC
                    "2025-12-16", "2025-12-17",  # 12월 FOMC
                ]
                
                for fomc_date in fomc_dates:
                    event_date = datetime.strptime(fomc_date, "%Y-%m-%d").date()
                    if start <= event_date <= end:
                        if event_types and "economic" not in event_types:
                            continue
                        
                        fomc_event = {
                            "id": f"fomc_{fomc_date}",
                            "title": "🇺🇸 FOMC 회의",
                            "date": fomc_date,
                            "eventType": "economic",
                            "description": "연준 연방공개시장위원회 금리 결정",
                            "marketType": "global",
                            "country": "US",
                            "importance": "high",
                            "institution": "Federal Reserve"
                        }
                        all_events.append(fomc_event)
                        
            except Exception as e:
                logger.warning(f"글로벌 경제 이벤트 추가 실패: {e}")
        
        # 7. 한국은행 기준금리 결정 일정 추가
        if not market_type or market_type == "domestic":
            try:
                # 한국은행 통화정책 회의 일정 (일반적으로 매월 셋째주 목요일)
                bok_dates = [
                    "2025-01-16", "2025-02-13", "2025-03-13", "2025-04-10",
                    "2025-05-15", "2025-06-12", "2025-07-10", "2025-08-21",
                    "2025-09-11", "2025-10-16", "2025-11-13", "2025-12-11"
                ]
                
                for bok_date in bok_dates:
                    event_date = datetime.strptime(bok_date, "%Y-%m-%d").date()
                    if start <= event_date <= end:
                        if event_types and "economic" not in event_types:
                            continue
                        
                        bok_event = {
                            "id": f"bok_{bok_date}",
                            "title": "🇰🇷 한국은행 기준금리 결정",
                            "date": bok_date,
                            "eventType": "economic",
                            "description": "한국은행 통화정책위원회 기준금리 결정",
                            "marketType": "domestic",
                            "country": "KR",
                            "importance": "high",
                            "institution": "Bank of Korea"
                        }
                        all_events.append(bok_event)
                        
            except Exception as e:
                logger.warning(f"한국은행 이벤트 추가 실패: {e}")
        
        # 날짜순 정렬
        all_events.sort(key=lambda x: x["date"])
        
        # 중복 제거 (같은 날짜, 같은 종목의 이벤트)
        unique_events = []
        seen_keys = set()
        
        for event in all_events:
            # 고유 키 생성 (날짜 + 종목코드/가상화폐심볼 + 이벤트타입)
            identifier = event.get('stockCode', '') or event.get('cryptoSymbol', '')
            key = f"{event['date']}_{identifier}_{event.get('eventType', '')}"
            if key not in seen_keys:
                seen_keys.add(key)
                unique_events.append(event)
        
        return {
            "events": unique_events,
            "meta": {
                "total_events": len(unique_events),
                "date_range": {
                    "start": start_date,
                    "end": end_date
                },
                "filters": {
                    "market_type": market_type,
                    "event_types": event_types
                }
            }
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"날짜 형식 오류: {str(e)}")
    except Exception as e:
        logger.error(f"캘린더 이벤트 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="캘린더 이벤트 조회 중 오류가 발생했습니다.")

@router.get("/upcoming-events")
async def get_upcoming_events(
    days: int = Query(7, description="조회할 일수 (기본값: 7일)"),
    market_type: Optional[str] = Query(None, description="시장 유형 필터"),
):
    """예정된 이벤트 조회
    
    오늘부터 지정된 일수 내의 주요 이벤트를 조회합니다.
    """
    today = date.today()
    end_date = today + timedelta(days=days)
    
    return await get_calendar_events(
        start_date=today.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d"),
        market_type=market_type,
        event_types=None
    )

@router.get("/event-types")
async def get_event_types():
    """이벤트 유형 목록 조회"""
    return {
        "eventTypes": [
            {"code": "earnings", "name": "실적발표", "color": "#3b82f6"},
            {"code": "dividend", "name": "배당", "color": "#10b981"},
            {"code": "holiday", "name": "휴장일", "color": "#ef4444"},
            {"code": "ipo", "name": "IPO", "color": "#f59e0b"},
            {"code": "economic", "name": "경제지표", "color": "#8b5cf6"},
            {"code": "split", "name": "액면분할", "color": "#ec4899"},
            {"code": "disclosure", "name": "공시", "color": "#06b6d4"},
            {"code": "crypto", "name": "가상화폐", "color": "#f97316"},
        ]
    }

@router.get("/market-types")
async def get_market_types():
    """시장 유형 목록 조회"""
    return {
        "marketTypes": [
            {"code": "domestic", "name": "국내"},
            {"code": "us", "name": "미국"},
            {"code": "global", "name": "글로벌"},
            {"code": "crypto", "name": "가상화폐"},
        ]
    }

@router.post("/ai-analysis/event")
async def get_event_analysis(
    event_title: str,
    event_details: str = "",
):
    """이벤트에 대한 AI 분석 제공
    
    Perplexity AI를 사용하여 특정 이벤트에 대한 상세한 분석을 제공합니다.
    """
    logger.info(f"AI 이벤트 분석 요청: {event_title}")
    
    try:
        analysis = await perplexity_client.explain_market_event(event_title, event_details)
        return analysis
    except Exception as e:
        logger.error(f"AI 이벤트 분석 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="AI 분석 중 오류가 발생했습니다.")

@router.post("/ai-analysis/stock")
async def get_stock_analysis(
    stock_name: str,
    stock_code: str,
    current_price: str = "",
):
    """종목에 대한 AI 분석 제공
    
    Perplexity AI를 사용하여 특정 종목에 대한 분석을 제공합니다.
    """
    logger.info(f"AI 종목 분석 요청: {stock_name} ({stock_code})")
    
    try:
        analysis = await perplexity_client.get_stock_analysis(stock_name, stock_code, current_price)
        return analysis
    except Exception as e:
        logger.error(f"AI 종목 분석 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="AI 분석 중 오류가 발생했습니다.")

@router.post("/ai-analysis/term")
async def get_term_explanation(
    term: str,
    context: str = "",
):
    """금융 용어에 대한 AI 설명 제공
    
    Perplexity AI를 사용하여 금융 용어를 쉽게 설명합니다.
    """
    logger.info(f"AI 용어 설명 요청: {term}")
    
    try:
        explanation = await perplexity_client.explain_financial_term(term, context)
        return explanation
    except Exception as e:
        logger.error(f"AI 용어 설명 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="AI 설명 중 오류가 발생했습니다.")

@router.get("/market-summary")
async def get_market_summary():
    """오늘의 시장 요약 정보 제공
    
    Perplexity AI를 사용하여 오늘의 주요 시장 이슈를 요약합니다.
    """
    logger.info("시장 요약 정보 요청")
    
    try:
        summary = await perplexity_client.get_daily_market_summary()
        return summary
    except Exception as e:
        logger.error(f"시장 요약 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="시장 요약 조회 중 오류가 발생했습니다.")

@router.get("/exchange-rates")
async def get_exchange_rates():
    """주요 통화 환율 정보 조회"""
    logger.info("환율 정보 요청")
    
    try:
        rates = await exchange_rate_service.get_major_currencies()
        return rates
    except Exception as e:
        logger.error(f"환율 정보 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="환율 정보 조회 중 오류가 발생했습니다.")

@router.get("/exchange-rates/{currency}")
async def get_currency_info(currency: str):
    """특정 통화에 대한 상세 정보 조회
    
    Args:
        currency: 통화 코드 (USD, JPY, EUR, CNY, GBP)
    """
    logger.info(f"통화 정보 요청: {currency}")
    
    try:
        info = await exchange_rate_service.get_currency_info(currency.upper())
        return info
    except Exception as e:
        logger.error(f"통화 정보 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="통화 정보 조회 중 오류가 발생했습니다.")

@router.get("/exchange-rates/{currency}/trend")
async def get_currency_trend(
    currency: str,
    days: int = Query(7, description="조회할 일수", ge=1, le=30)
):
    """특정 통화의 환율 추세 정보 조회
    
    Args:
        currency: 통화 코드
        days: 조회할 일수 (1-30일)
    """
    logger.info(f"환율 추세 정보 요청: {currency}, {days}일")
    
    try:
        trend = await exchange_rate_service.get_currency_trend(currency.upper(), days)
        return trend
    except Exception as e:
        logger.error(f"환율 추세 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="환율 추세 조회 중 오류가 발생했습니다.")

@router.get("/exchange-rates/cross-rates")
async def get_cross_currency_rates():
    """주요 통화간 교차 환율 정보 조회"""
    logger.info("교차 환율 정보 요청")
    
    try:
        cross_rates = await exchange_rate_service.get_cross_currency_rates()
        return cross_rates
    except Exception as e:
        logger.error(f"교차 환율 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="교차 환율 조회 중 오류가 발생했습니다.")

@router.get("/exchange-rates/alerts")
async def get_exchange_rate_alerts(
    threshold: float = Query(1.0, description="알림 임계값 (%)", ge=0.1, le=10.0)
):
    """환율 급등락 알림 정보 조회
    
    Args:
        threshold: 알림을 발생시킬 변동률 임계값 (%)
    """
    logger.info(f"환율 알림 정보 요청: 임계값 {threshold}%")
    
    try:
        alerts = await exchange_rate_service.get_realtime_alerts(threshold)
        return alerts
    except Exception as e:
        logger.error(f"환율 알림 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="환율 알림 조회 중 오류가 발생했습니다.")

@router.get("/dart/disclosures")
async def get_dart_disclosures(
    start_date: str = Query(..., description="시작 날짜 (YYYY-MM-DD)"),
    end_date: str = Query(..., description="종료 날짜 (YYYY-MM-DD)"),
    corp_cls: Optional[str] = Query("Y", description="법인구분 (Y:유가, K:코스닥, N:코넥스, E:기타)"),
    important_only: bool = Query(True, description="중요 공시만 조회"),
):
    """DART 공시 정보 조회
    
    DART API를 통해 실제 공시 정보를 조회합니다.
    """
    logger.info(f"DART 공시 조회: {start_date} ~ {end_date}")
    
    try:
        # DART API를 통한 공시 이벤트 조회
        disclosure_events = await dart_api_client.get_upcoming_disclosure_events(
            start_date=start_date,
            end_date=end_date,
            corp_cls=corp_cls
        )
        
        # 중요 공시 필터링
        if important_only:
            important_keywords = [
                "실적발표", "실적공시", "분기보고서", "반기보고서", "사업보고서",
                "임시주주총회", "정기주주총회", "배당", "유상증자", "무상증자",
                "합병", "분할", "인수", "매각", "대규모내부거래",
                "주요사항보고", "공시정정", "특별관계자거래"
            ]
            
            filtered_events = []
            for event in disclosure_events:
                title = event.get("title", "")
                if any(keyword in title for keyword in important_keywords):
                    filtered_events.append(event)
            
            disclosure_events = filtered_events
        
        return {
            "disclosures": disclosure_events,
            "meta": {
                "total_count": len(disclosure_events),
                "corp_cls": corp_cls,
                "important_only": important_only,
                "date_range": {
                    "start": start_date,
                    "end": end_date
                }
            }
        }
        
    except Exception as e:
        logger.error(f"DART 공시 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="DART 공시 조회 중 오류가 발생했습니다.")

@router.get("/dart/company/{corp_code}")
async def get_dart_company_info(corp_code: str):
    """DART 기업 정보 조회
    
    Args:
        corp_code: 고유번호(8자리)
    """
    logger.info(f"DART 기업 정보 조회: {corp_code}")
    
    try:
        company_info = await dart_api_client.get_company_info(corp_code)
        
        if not company_info.get("success"):
            raise HTTPException(status_code=404, detail="기업 정보를 찾을 수 없습니다.")
        
        return company_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"DART 기업 정보 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="기업 정보 조회 중 오류가 발생했습니다.")

@router.get("/dart/search/company")
async def search_dart_companies(
    company_name: str = Query(..., description="회사명 (부분 검색)"),
):
    """DART 기업 검색
    
    Args:
        company_name: 검색할 회사명
    """
    logger.info(f"DART 기업 검색: {company_name}")
    
    try:
        companies = await dart_api_client.search_company_by_name(company_name)
        
        return {
            "companies": companies,
            "meta": {
                "total_count": len(companies),
                "search_term": company_name
            }
        }
        
    except Exception as e:
        logger.error(f"DART 기업 검색 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="기업 검색 중 오류가 발생했습니다.")

@router.get("/dart/recent")
async def get_recent_dart_disclosures(
    corp_cls: str = Query("Y", description="법인구분 (Y:유가, K:코스닥)"),
    days: int = Query(7, description="조회 기간 (일수)"),
    important_only: bool = Query(True, description="중요 공시만 조회"),
):
    """최근 DART 공시 조회
    
    최근 며칠간의 중요 공시를 조회합니다.
    """
    logger.info(f"최근 DART 공시 조회: {corp_cls}, {days}일")
    
    try:
        disclosures = await dart_api_client.get_recent_disclosures(
            corp_cls=corp_cls,
            days=days,
            important_only=important_only
        )
        
        # 캘린더 이벤트 형식으로 변환
        events = []
        for disclosure in disclosures:
            rcept_dt = disclosure.get("rcept_dt")
            if rcept_dt and len(rcept_dt) == 8:
                event_date = f"{rcept_dt[:4]}-{rcept_dt[4:6]}-{rcept_dt[6:8]}"
                
                events.append({
                    "id": f"recent_disclosure_{disclosure.get('rcept_no')}",
                    "title": disclosure.get("report_nm", "공시"),
                    "date": event_date,
                    "eventType": "disclosure",
                    "stockCode": disclosure.get("stock_code"),
                    "stockName": disclosure.get("corp_name"),
                    "description": f"{disclosure.get('corp_name')} - {disclosure.get('report_nm')}",
                    "marketType": "domestic",
                    "corp_cls": disclosure.get("corp_cls"),
                    "disclosure_url": f"http://dart.fss.or.kr/dsaf001/main.do?rcpNo={disclosure.get('rcept_no')}"
                })
        
        return {
            "events": events,
            "meta": {
                "total_count": len(events),
                "corp_cls": corp_cls,
                "days": days,
                "important_only": important_only
            }
        }
        
    except Exception as e:
        logger.error(f"최근 DART 공시 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="최근 공시 조회 중 오류가 발생했습니다.")

@router.get("/crypto/prices")
async def get_crypto_prices():
    """주요 가상화폐 현재가 조회
    
    업비트 API를 통해 주요 가상화폐의 실시간 시세를 조회합니다.
    """
    logger.info("가상화폐 현재가 조회")
    
    try:
        async with upbit_api_client as upbit:
            major_cryptos = await upbit.get_major_cryptos()
            
            crypto_data = []
            for crypto in major_cryptos:
                crypto_data.append({
                    "symbol": crypto.symbol,
                    "korean_name": crypto.korean_name,
                    "trade_price": crypto.trade_price,
                    "change": crypto.change,
                    "change_price": crypto.change_price,
                    "change_rate": crypto.change_rate,
                    "trade_volume": crypto.trade_volume,
                    "high_price": crypto.high_price,
                    "low_price": crypto.low_price,
                    "timestamp": crypto.timestamp.isoformat()
                })
            
            return {
                "cryptos": crypto_data,
                "meta": {
                    "total_count": len(crypto_data),
                    "timestamp": datetime.now().isoformat()
                }
            }
            
    except Exception as e:
        logger.error(f"가상화폐 현재가 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="가상화폐 시세 조회 중 오류가 발생했습니다.")

@router.get("/crypto/{symbol}")
async def get_crypto_detail(symbol: str):
    """특정 가상화폐 상세 정보 조회
    
    Args:
        symbol: 가상화폐 심볼 (BTC, ETH, XRP 등)
    """
    logger.info(f"가상화폐 상세 정보 조회: {symbol}")
    
    try:
        async with upbit_api_client as upbit:
            crypto_quote = await upbit.get_single_ticker(symbol.upper())
            
            if not crypto_quote:
                raise HTTPException(status_code=404, detail="해당 가상화폐를 찾을 수 없습니다.")
            
            # 일봉 데이터도 함께 조회
            candle_data = await upbit.get_candles_daily(symbol.upper(), 7)
            
            return {
                "crypto": {
                    "symbol": crypto_quote.symbol,
                    "korean_name": crypto_quote.korean_name,
                    "trade_price": crypto_quote.trade_price,
                    "change": crypto_quote.change,
                    "change_price": crypto_quote.change_price,
                    "change_rate": crypto_quote.change_rate,
                    "trade_volume": crypto_quote.trade_volume,
                    "acc_trade_volume_24h": crypto_quote.acc_trade_volume_24h,
                    "high_price": crypto_quote.high_price,
                    "low_price": crypto_quote.low_price,
                    "opening_price": crypto_quote.opening_price,
                    "timestamp": crypto_quote.timestamp.isoformat()
                },
                "candle_data": candle_data,
                "meta": {
                    "symbol": symbol.upper(),
                    "timestamp": datetime.now().isoformat()
                }
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"가상화폐 상세 정보 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="가상화폐 정보 조회 중 오류가 발생했습니다.")

@router.get("/crypto/events")
async def get_crypto_events(
    start_date: str = Query(..., description="시작 날짜 (YYYY-MM-DD)"),
    end_date: str = Query(..., description="종료 날짜 (YYYY-MM-DD)"),
):
    """가상화폐 이벤트 조회
    
    지정된 기간의 가상화폐 관련 이벤트를 조회합니다.
    """
    logger.info(f"가상화폐 이벤트 조회: {start_date} ~ {end_date}")
    
    try:
        # 날짜 유효성 검사
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        if start > end:
            raise HTTPException(status_code=400, detail="시작일이 종료일보다 늦습니다.")
        
        async with upbit_api_client as upbit:
            crypto_events = await upbit.get_crypto_events(start_date, end_date)
            
            return {
                "events": crypto_events,
                "meta": {
                    "total_events": len(crypto_events),
                    "date_range": {
                        "start": start_date,
                        "end": end_date
                    },
                    "market_type": "crypto"
                }
            }
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"날짜 형식 오류: {str(e)}")
    except Exception as e:
        logger.error(f"가상화폐 이벤트 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="가상화폐 이벤트 조회 중 오류가 발생했습니다.")

@router.get("/crypto/supported")
async def get_supported_cryptos():
    """지원되는 가상화폐 목록 조회
    
    업비트에서 지원하는 주요 가상화폐 목록을 반환합니다.
    """
    logger.info("지원 가상화폐 목록 조회")
    
    try:
        async with upbit_api_client as upbit:
            supported_symbols = upbit.get_supported_symbols()
            
            symbols_list = []
            for symbol, korean_name in supported_symbols.items():
                symbols_list.append({
                    "symbol": symbol,
                    "korean_name": korean_name,
                    "market": f"KRW-{symbol}"
                })
            
            return {
                "symbols": symbols_list,
                "meta": {
                    "total_count": len(symbols_list),
                    "timestamp": datetime.now().isoformat()
                }
            }
            
    except Exception as e:
        logger.error(f"지원 가상화폐 목록 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="가상화폐 목록 조회 중 오류가 발생했습니다.")

@router.post("/ai-analysis/crypto")
async def get_crypto_analysis(
    crypto_symbol: str,
    crypto_name: str,
    current_price: str = "",
):
    """가상화폐에 대한 AI 분석 제공
    
    Perplexity AI를 사용하여 특정 가상화폐에 대한 분석을 제공합니다.
    """
    logger.info(f"AI 가상화폐 분석 요청: {crypto_name} ({crypto_symbol})")
    
    try:
        # 가상화폐 전용 분석 프롬프트 생성
        analysis_prompt = f"""
        가상화폐 {crypto_name}({crypto_symbol})에 대한 분석을 제공해주세요.
        현재가: {current_price}
        
        다음 내용을 포함해주세요:
        1. 현재 시장 상황과 가격 동향
        2. 기술적 특징 및 용도
        3. 최근 중요한 뉴스나 업데이트
        4. 투자 시 고려사항
        5. 위험 요소
        """
        
        analysis = await perplexity_client.explain_market_event(
            f"{crypto_name} 가상화폐 분석", 
            analysis_prompt
        )
        return analysis
        
    except Exception as e:
        logger.error(f"AI 가상화폐 분석 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="AI 분석 중 오류가 발생했습니다.")

# ================== US Stock Endpoints ==================

@router.get("/us-stocks/quote/{symbol}")
async def get_us_stock_quote(symbol: str):
    """미국 주식 현재가 조회
    
    Args:
        symbol: 미국 주식 심볼 (AAPL, MSFT, GOOGL 등)
    """
    logger.info(f"미국 주식 현재가 조회: {symbol}")
    
    try:
        async with us_stock_api_client as us_client:
            quote = await us_client.get_stock_quote(symbol.upper())
            
            if not quote:
                raise HTTPException(status_code=404, detail="해당 주식을 찾을 수 없습니다.")
            
            return {
                "quote": quote,
                "meta": {
                    "symbol": symbol.upper(),
                    "timestamp": datetime.now().isoformat(),
                    "source": quote.get("source", "unknown")
                }
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"미국 주식 현재가 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="미국 주식 조회 중 오류가 발생했습니다.")

@router.get("/us-stocks/quotes")
async def get_multiple_us_stock_quotes(
    symbols: str = Query(..., description="쉼표로 구분된 주식 심볼 (예: AAPL,MSFT,GOOGL)")
):
    """여러 미국 주식 현재가 동시 조회
    
    Args:
        symbols: 쉼표로 구분된 주식 심볼들
    """
    symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    
    if not symbol_list:
        raise HTTPException(status_code=400, detail="유효한 주식 심볼을 입력해주세요.")
    
    if len(symbol_list) > 20:
        raise HTTPException(status_code=400, detail="한 번에 최대 20개 종목까지 조회 가능합니다.")
    
    logger.info(f"다중 미국 주식 현재가 조회: {symbol_list}")
    
    try:
        async with us_stock_api_client as us_client:
            quotes = await us_client.get_multiple_quotes(symbol_list)
            
            return {
                "quotes": quotes,
                "meta": {
                    "symbols": symbol_list,
                    "total_count": len(quotes),
                    "timestamp": datetime.now().isoformat()
                }
            }
            
    except Exception as e:
        logger.error(f"다중 미국 주식 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="미국 주식 조회 중 오류가 발생했습니다.")

@router.get("/us-stocks/earnings")
async def get_us_earnings_calendar(
    start_date: Optional[str] = Query(None, description="시작 날짜 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="종료 날짜 (YYYY-MM-DD)"),
    days: int = Query(30, description="조회할 일수 (start_date 미제공시)", ge=1, le=90)
):
    """미국 주식 실적 발표 캘린더 조회"""
    logger.info(f"미국 실적 캘린더 조회: {start_date} ~ {end_date}")
    
    try:
        if start_date and end_date:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
        else:
            start = date.today()
            end = start + timedelta(days=days)
        
        if start > end:
            raise HTTPException(status_code=400, detail="시작일이 종료일보다 늦습니다.")
        
        async with us_stock_api_client as us_client:
            earnings_events = await us_client.get_earnings_calendar(start, end)
            
            return {
                "earnings": earnings_events,
                "meta": {
                    "total_count": len(earnings_events),
                    "date_range": {
                        "start": start.strftime("%Y-%m-%d"),
                        "end": end.strftime("%Y-%m-%d")
                    },
                    "market": "US"
                }
            }
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"날짜 형식 오류: {str(e)}")
    except Exception as e:
        logger.error(f"미국 실적 캘린더 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="실적 캘린더 조회 중 오류가 발생했습니다.")

@router.get("/us-stocks/dividends")
async def get_us_dividend_calendar(
    start_date: Optional[str] = Query(None, description="시작 날짜 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="종료 날짜 (YYYY-MM-DD)"),
    days: int = Query(30, description="조회할 일수 (start_date 미제공시)", ge=1, le=90)
):
    """미국 주식 배당 캘린더 조회"""
    logger.info(f"미국 배당 캘린더 조회: {start_date} ~ {end_date}")
    
    try:
        if start_date and end_date:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
        else:
            start = date.today()
            end = start + timedelta(days=days)
        
        if start > end:
            raise HTTPException(status_code=400, detail="시작일이 종료일보다 늦습니다.")
        
        async with us_stock_api_client as us_client:
            dividend_events = await us_client.get_dividend_calendar(start, end)
            
            return {
                "dividends": dividend_events,
                "meta": {
                    "total_count": len(dividend_events),
                    "date_range": {
                        "start": start.strftime("%Y-%m-%d"),
                        "end": end.strftime("%Y-%m-%d")
                    },
                    "market": "US"
                }
            }
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"날짜 형식 오류: {str(e)}")
    except Exception as e:
        logger.error(f"미국 배당 캘린더 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="배당 캘린더 조회 중 오류가 발생했습니다.")

@router.get("/us-stocks/economic-calendar")
async def get_us_economic_calendar(
    start_date: Optional[str] = Query(None, description="시작 날짜 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="종료 날짜 (YYYY-MM-DD)"),
    days: int = Query(30, description="조회할 일수 (start_date 미제공시)", ge=1, le=90)
):
    """미국 경제 지표 캘린더 조회"""
    logger.info(f"미국 경제 지표 캘린더 조회: {start_date} ~ {end_date}")
    
    try:
        if start_date and end_date:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
        else:
            start = date.today()
            end = start + timedelta(days=days)
        
        if start > end:
            raise HTTPException(status_code=400, detail="시작일이 종료일보다 늦습니다.")
        
        async with us_stock_api_client as us_client:
            economic_events = await us_client.get_economic_calendar(start, end)
            
            return {
                "economic_indicators": economic_events,
                "meta": {
                    "total_count": len(economic_events),
                    "date_range": {
                        "start": start.strftime("%Y-%m-%d"),
                        "end": end.strftime("%Y-%m-%d")
                    },
                    "market": "US"
                }
            }
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"날짜 형식 오류: {str(e)}")
    except Exception as e:
        logger.error(f"미국 경제 지표 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="경제 지표 조회 중 오류가 발생했습니다.")

@router.get("/us-stocks/market-status")
async def get_us_market_status():
    """미국 시장 상태 조회"""
    logger.info("미국 시장 상태 조회")
    
    try:
        async with us_stock_api_client as us_client:
            market_status = await us_client.get_market_status()
            
            return {
                "market_status": market_status,
                "meta": {
                    "timestamp": datetime.now().isoformat()
                }
            }
            
    except Exception as e:
        logger.error(f"미국 시장 상태 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="시장 상태 조회 중 오류가 발생했습니다.")

@router.get("/us-stocks/major")
async def get_major_us_stocks():
    """주요 미국 주식 현재가 조회"""
    logger.info("주요 미국 주식 현재가 조회")
    
    # 주요 미국 주식 심볼들
    major_symbols = [
        "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", 
        "NVDA", "META", "NFLX", "AMD", "INTC",
        "JPM", "BAC", "WMT", "JNJ", "V"
    ]
    
    try:
        async with us_stock_api_client as us_client:
            quotes = await us_client.get_multiple_quotes(major_symbols)
            
            # 섹터별로 그룹화
            sectors = {}
            for symbol, quote in quotes.items():
                sector = quote.get("sector", "기타")
                if sector not in sectors:
                    sectors[sector] = []
                sectors[sector].append({
                    "symbol": symbol,
                    "name": quote.get("name", symbol),
                    "price": quote.get("price", 0),
                    "change": quote.get("change", 0),
                    "change_percent": quote.get("change_percent", "0"),
                    "volume": quote.get("volume", 0),
                    "source": quote.get("source", "unknown")
                })
            
            return {
                "major_stocks": {
                    "by_symbol": quotes,
                    "by_sector": sectors
                },
                "meta": {
                    "total_count": len(quotes),
                    "symbols": major_symbols,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
    except Exception as e:
        logger.error(f"주요 미국 주식 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="주요 주식 조회 중 오류가 발생했습니다.")

@router.post("/ai-analysis/us-stock")
async def get_us_stock_analysis(
    stock_symbol: str,
    stock_name: str = "",
    current_price: str = "",
):
    """미국 주식에 대한 AI 분석 제공
    
    Perplexity AI를 사용하여 미국 주식에 대한 분석을 제공합니다.
    """
    logger.info(f"AI 미국 주식 분석 요청: {stock_name} ({stock_symbol})")
    
    try:
        # 미국 주식 전용 분석 프롬프트 생성
        analysis_prompt = f"""
        미국 주식 {stock_name}({stock_symbol})에 대한 분석을 제공해주세요.
        현재가: {current_price}
        
        다음 내용을 포함해주세요:
        1. 회사 개요 및 사업 분야
        2. 최근 실적 및 재무 상황
        3. 주가 동향 및 기술적 분석
        4. 최근 중요한 뉴스나 발표
        5. 경쟁사 대비 포지션
        6. 투자 시 고려사항
        7. 위험 요소
        """
        
        analysis = await perplexity_client.get_stock_analysis(
            stock_name or stock_symbol, 
            stock_symbol, 
            current_price
        )
        return analysis
        
    except Exception as e:
        logger.error(f"AI 미국 주식 분석 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="AI 분석 중 오류가 발생했습니다.")

@router.get("/dashboard/summary")
async def get_dashboard_summary():
    """투자 대시보드 종합 요약 정보
    
    모든 API 클라이언트에서 실시간 데이터를 수집하여 종합 요약을 제공합니다.
    """
    logger.info("투자 대시보드 종합 요약 요청")
    
    try:
        summary_data = {}
        
        # 1. 환율 정보
        try:
            exchange_rates = await exchange_rate_service.get_major_currencies()
            exchange_alerts = await exchange_rate_service.get_realtime_alerts(1.0)
            summary_data["exchange_rates"] = {
                "rates": exchange_rates.get("rates", {}),
                "alerts": exchange_alerts.get("alerts", []),
                "last_updated": exchange_rates.get("timestamp")
            }
        except Exception as e:
            logger.warning(f"환율 정보 수집 실패: {e}")
            summary_data["exchange_rates"] = {"error": str(e)}
        
        # 2. 미국 주식 주요 지수 현황
        try:
            async with us_stock_api_client as us_client:
                major_indices = ["SPY", "QQQ", "DIA", "IWM"]  # S&P500, 나스닥, 다우, 러셀
                us_quotes = await us_client.get_multiple_quotes(major_indices)
                
                market_status = await us_client.get_market_status()
                
                summary_data["us_market"] = {
                    "indices": us_quotes,
                    "market_status": market_status,
                    "last_updated": datetime.now().isoformat()
                }
        except Exception as e:
            logger.warning(f"미국 주식 정보 수집 실패: {e}")
            summary_data["us_market"] = {"error": str(e)}
        
        # 3. 가상화폐 주요 종목 현황
        try:
            async with upbit_api_client as upbit:
                major_cryptos = await upbit.get_major_cryptos()
                
                crypto_data = []
                for crypto in major_cryptos[:10]:  # 상위 10개만
                    crypto_data.append({
                        "symbol": crypto.symbol,
                        "korean_name": crypto.korean_name,
                        "trade_price": crypto.trade_price,
                        "change_rate": crypto.change_rate,
                        "change": crypto.change
                    })
                
                summary_data["crypto_market"] = {
                    "major_cryptos": crypto_data,
                    "last_updated": datetime.now().isoformat()
                }
        except Exception as e:
            logger.warning(f"가상화폐 정보 수집 실패: {e}")
            summary_data["crypto_market"] = {"error": str(e)}
        
        # 4. 오늘의 주요 이벤트 (향후 3일)
        try:
            today = date.today()
            end_date = today + timedelta(days=3)
            
            events_response = await get_calendar_events(
                start_date=today.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d"),
                market_type=None,
                event_types=None,
                include_disclosures=True,
                include_earnings=True,
                include_crypto=True
            )
            
            # 중요도 높은 이벤트만 선별
            important_events = []
            for event in events_response.get("events", []):
                if (event.get("importance") == "high" or 
                    event.get("eventType") in ["earnings", "economic", "dividend"]):
                    important_events.append(event)
            
            summary_data["upcoming_events"] = {
                "events": important_events[:15],  # 최대 15개
                "total_count": len(important_events)
            }
        except Exception as e:
            logger.warning(f"이벤트 정보 수집 실패: {e}")
            summary_data["upcoming_events"] = {"error": str(e)}
        
        # 5. 최근 중요 공시 (DART)
        try:
            recent_disclosures = await dart_api_client.get_recent_disclosures(
                corp_cls="Y",
                days=2,
                important_only=True
            )
            
            summary_data["recent_disclosures"] = {
                "disclosures": recent_disclosures[:10],  # 최대 10개
                "total_count": len(recent_disclosures)
            }
        except Exception as e:
            logger.warning(f"공시 정보 수집 실패: {e}")
            summary_data["recent_disclosures"] = {"error": str(e)}
        
        # 6. AI 시장 분석 요약
        try:
            market_summary = await perplexity_client.get_daily_market_summary()
            summary_data["ai_market_analysis"] = market_summary
        except Exception as e:
            logger.warning(f"AI 시장 분석 실패: {e}")
            summary_data["ai_market_analysis"] = {"error": str(e)}
        
        return {
            "dashboard_summary": summary_data,
            "meta": {
                "generated_at": datetime.now().isoformat(),
                "data_sources": [
                    "KIS API (국내주식)",
                    "US Stock API (미국주식)",
                    "Upbit API (가상화폐)",
                    "DART API (공시)",
                    "Exchange Rate API (환율)",
                    "Perplexity AI (분석)"
                ],
                "refresh_interval": "5분"
            }
        }
        
    except Exception as e:
        logger.error(f"대시보드 요약 생성 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="대시보드 요약 생성 중 오류가 발생했습니다.")

@router.get("/realtime/market-status")
async def get_realtime_market_status():
    """실시간 시장 상태 종합 정보
    
    국내외 주요 시장의 실시간 상태를 제공합니다.
    """
    logger.info("실시간 시장 상태 요청")
    
    try:
        market_status = {
            "timestamp": datetime.now().isoformat(),
            "markets": {}
        }
        
        # 1. 미국 시장 상태
        try:
            async with us_stock_api_client as us_client:
                us_status = await us_client.get_market_status()
                market_status["markets"]["us"] = us_status
        except Exception as e:
            logger.warning(f"미국 시장 상태 조회 실패: {e}")
            market_status["markets"]["us"] = {"status": "unknown", "error": str(e)}
        
        # 2. 한국 시장 상태 (KIS API 또는 시간 기반)
        try:
            # 한국 시간 기준 시장 시간 계산
            from datetime import timezone
            kst = timezone(timedelta(hours=9))
            now_kst = datetime.now(kst)
            hour = now_kst.hour
            minute = now_kst.minute
            weekday = now_kst.weekday()
            
            # 주말이면 휴장
            if weekday >= 5:  # 토요일(5), 일요일(6)
                kr_status = "closed"
                kr_message = "주말 휴장"
            # 평일 9:00-15:30이면 개장
            elif (hour == 9 and minute >= 0) or (9 < hour < 15) or (hour == 15 and minute <= 30):
                kr_status = "open"
                kr_message = "정규장 거래시간"
            else:
                kr_status = "closed"
                kr_message = "정규장 마감"
            
            market_status["markets"]["korea"] = {
                "status": kr_status,
                "message": kr_message,
                "local_time": now_kst.strftime("%Y-%m-%d %H:%M:%S KST")
            }
        except Exception as e:
            logger.warning(f"한국 시장 상태 계산 실패: {e}")
            market_status["markets"]["korea"] = {"status": "unknown", "error": str(e)}
        
        # 3. 가상화폐 시장 (24시간 운영)
        market_status["markets"]["crypto"] = {
            "status": "open",
            "message": "24시간 거래",
            "note": "가상화폐는 24시간 연중무휴 거래됩니다."
        }
        
        # 4. 환율 시장 (24시간 운영, 주말 제외)
        try:
            weekday = datetime.now().weekday()
            if weekday >= 5:
                forex_status = "limited"
                forex_message = "주말 제한 거래"
            else:
                forex_status = "open"
                forex_message = "24시간 거래"
            
            market_status["markets"]["forex"] = {
                "status": forex_status,
                "message": forex_message
            }
        except Exception as e:
            market_status["markets"]["forex"] = {"status": "unknown", "error": str(e)}
        
        return market_status
        
    except Exception as e:
        logger.error(f"실시간 시장 상태 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="시장 상태 조회 중 오류가 발생했습니다.")