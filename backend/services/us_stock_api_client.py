"""
US Stock API Client
실시간 미국 주식 시장 데이터를 제공하는 API 클라이언트

지원하는 API:
- Alpha Vantage API (실시간 주가, 실적 캘린더)
- Yahoo Finance API (대체 데이터 소스)
- Mock Data (API 실패 시 대체 데이터)

주요 기능:
- 실시간 주가 조회
- 실적 발표 일정
- 배당 일정
- 경제 지표 캘린더
"""

import os
import sys
import asyncio
import aiohttp
import json
import random
from datetime import datetime, timedelta, date
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import logging

# 프로젝트 루트 디렉토리 찾기
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.utils.logger import setup_logger

logger = setup_logger("services.us_stock_api")

class USStockAPIClient:
    """미국 주식 시장 데이터 API 클라이언트"""
    
    def __init__(self):
        """US Stock API 클라이언트 초기화"""
        # Alpha Vantage API 설정
        self.alpha_vantage_key = os.environ.get("ALPHA_VANTAGE_API_KEY")
        self.alpha_vantage_base_url = "https://www.alphavantage.co/query"
        
        # Yahoo Finance 대체 API 설정
        self.yahoo_finance_base_url = "https://query1.finance.yahoo.com/v8/finance/chart"
        
        # API 호출 제한 (Alpha Vantage는 분당 5회 제한)
        self.api_call_interval = 12  # 초
        self.last_api_call = None
        
        # Mock 데이터 제공자
        self.mock_provider = USStockMockProvider()
        
        # 세션 관리
        self.session = None
        
        if not self.alpha_vantage_key:
            logger.warning("Alpha Vantage API 키가 설정되지 않았습니다. Mock 데이터를 사용합니다.")

    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        if self.session:
            await self.session.close()

    async def _wait_for_rate_limit(self):
        """API 호출 제한 대기"""
        if self.last_api_call:
            elapsed = (datetime.now() - self.last_api_call).total_seconds()
            if elapsed < self.api_call_interval:
                wait_time = self.api_call_interval - elapsed
                logger.debug(f"API 호출 제한으로 {wait_time:.1f}초 대기")
                await asyncio.sleep(wait_time)
        
        self.last_api_call = datetime.now()

    async def _make_request(self, url: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """HTTP 요청 실행"""
        await self._wait_for_rate_limit()
        
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
                
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"API 호출 실패: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"API 요청 중 오류: {str(e)}")
            return None

    async def get_stock_quote(self, symbol: str) -> Dict[str, Any]:
        """실시간 주가 조회"""
        logger.info(f"US 주식 현재가 조회: {symbol}")
        
        # Alpha Vantage API 호출 시도
        if self.alpha_vantage_key:
            quote_data = await self._get_alpha_vantage_quote(symbol)
            if quote_data:
                return quote_data
        
        # Yahoo Finance API 대체 시도
        yahoo_data = await self._get_yahoo_finance_quote(symbol)
        if yahoo_data:
            return yahoo_data
        
        # Mock 데이터 반환
        logger.warning(f"실제 API 호출 실패, Mock 데이터 반환: {symbol}")
        return self.mock_provider.get_stock_quote(symbol)

    async def _get_alpha_vantage_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Alpha Vantage API로 주가 조회"""
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": self.alpha_vantage_key
        }
        
        response = await self._make_request(self.alpha_vantage_base_url, params)
        if not response:
            return None
            
        global_quote = response.get("Global Quote", {})
        if not global_quote:
            logger.warning(f"Alpha Vantage에서 {symbol} 데이터를 찾을 수 없습니다.")
            return None
        
        try:
            return {
                "symbol": symbol,
                "price": float(global_quote.get("05. price", 0)),
                "change": float(global_quote.get("09. change", 0)),
                "change_percent": global_quote.get("10. change percent", "0%").replace("%", ""),
                "volume": int(global_quote.get("06. volume", 0)),
                "latest_trading_day": global_quote.get("07. latest trading day", ""),
                "previous_close": float(global_quote.get("08. previous close", 0)),
                "open": float(global_quote.get("02. open", 0)),
                "high": float(global_quote.get("03. high", 0)),
                "low": float(global_quote.get("04. low", 0)),
                "source": "alpha_vantage"
            }
        except (ValueError, TypeError) as e:
            logger.error(f"Alpha Vantage 데이터 파싱 오류: {e}")
            return None

    async def _get_yahoo_finance_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Yahoo Finance API로 주가 조회"""
        url = f"{self.yahoo_finance_base_url}/{symbol}"
        params = {
            "interval": "1d",
            "range": "1d"
        }
        
        response = await self._make_request(url, params)
        if not response:
            return None
            
        try:
            chart = response.get("chart", {})
            result = chart.get("result", [])
            if not result:
                return None
                
            data = result[0]
            meta = data.get("meta", {})
            indicators = data.get("indicators", {})
            quote = indicators.get("quote", [{}])[0]
            
            current_price = meta.get("regularMarketPrice", 0)
            previous_close = meta.get("previousClose", 0)
            change = current_price - previous_close
            change_percent = (change / previous_close * 100) if previous_close else 0
            
            return {
                "symbol": symbol,
                "price": current_price,
                "change": change,
                "change_percent": f"{change_percent:.2f}",
                "volume": quote.get("volume", [0])[-1] if quote.get("volume") else 0,
                "latest_trading_day": datetime.now().strftime("%Y-%m-%d"),
                "previous_close": previous_close,
                "open": quote.get("open", [0])[-1] if quote.get("open") else 0,
                "high": quote.get("high", [0])[-1] if quote.get("high") else 0,
                "low": quote.get("low", [0])[-1] if quote.get("low") else 0,
                "source": "yahoo_finance"
            }
        except (KeyError, IndexError, TypeError) as e:
            logger.error(f"Yahoo Finance 데이터 파싱 오류: {e}")
            return None

    async def get_earnings_calendar(self, start_date: date = None, end_date: date = None) -> List[Dict[str, Any]]:
        """실적 발표 캘린더 조회"""
        if not start_date:
            start_date = date.today()
        if not end_date:
            end_date = start_date + timedelta(days=30)
            
        logger.info(f"실적 캘린더 조회: {start_date} ~ {end_date}")
        
        # Alpha Vantage Earnings Calendar API 호출 시도
        if self.alpha_vantage_key:
            earnings_data = await self._get_alpha_vantage_earnings(start_date, end_date)
            if earnings_data:
                return earnings_data
        
        # Mock 데이터 반환
        logger.warning("실제 API 호출 실패, Mock 실적 캘린더 반환")
        return self.mock_provider.get_earnings_calendar(start_date, end_date)

    async def _get_alpha_vantage_earnings(self, start_date: date, end_date: date) -> Optional[List[Dict[str, Any]]]:
        """Alpha Vantage 실적 캘린더 API 호출"""
        params = {
            "function": "EARNINGS_CALENDAR",
            "horizon": "12month",
            "apikey": self.alpha_vantage_key
        }
        
        response = await self._make_request(self.alpha_vantage_base_url, params)
        if not response:
            return None
            
        # CSV 형식 응답 파싱 (Alpha Vantage 실적 캘린더는 CSV 반환)
        # 실제 구현에서는 CSV 파싱 로직 필요
        # 여기서는 Mock 데이터 반환
        return None

    async def get_dividend_calendar(self, start_date: date = None, end_date: date = None) -> List[Dict[str, Any]]:
        """배당 일정 캘린더 조회"""
        if not start_date:
            start_date = date.today()
        if not end_date:
            end_date = start_date + timedelta(days=30)
            
        logger.info(f"배당 캘린더 조회: {start_date} ~ {end_date}")
        
        # Mock 데이터 반환 (실제 API는 별도 구현 필요)
        return self.mock_provider.get_dividend_calendar(start_date, end_date)

    async def get_economic_calendar(self, start_date: date = None, end_date: date = None) -> List[Dict[str, Any]]:
        """경제 지표 캘린더 조회"""
        if not start_date:
            start_date = date.today()
        if not end_date:
            end_date = start_date + timedelta(days=30)
            
        logger.info(f"경제 지표 캘린더 조회: {start_date} ~ {end_date}")
        
        # Mock 데이터 반환 (실제 API는 별도 구현 필요)
        return self.mock_provider.get_economic_calendar(start_date, end_date)

    async def get_multiple_quotes(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """여러 종목 동시 조회"""
        logger.info(f"다중 종목 조회: {symbols}")
        
        results = {}
        # 동시 실행으로 성능 개선
        tasks = [self.get_stock_quote(symbol) for symbol in symbols]
        quotes = await asyncio.gather(*tasks, return_exceptions=True)
        
        for symbol, quote in zip(symbols, quotes):
            if isinstance(quote, Exception):
                logger.error(f"{symbol} 조회 실패: {quote}")
                results[symbol] = self.mock_provider.get_stock_quote(symbol)
            else:
                results[symbol] = quote
                
        return results

    async def get_market_status(self) -> Dict[str, Any]:
        """미국 시장 상태 조회"""
        logger.info("미국 시장 상태 조회")
        
        # 현재 시간 기준으로 시장 상태 판단
        now = datetime.now()
        
        # 미국 동부 시간 기준 (UTC-5 또는 UTC-4)
        # 간단한 구현으로 현재 시간만 고려
        is_market_open = 9 <= now.hour <= 16  # 대략적인 시장 시간
        
        return {
            "market": "US",
            "is_open": is_market_open,
            "next_open": "09:30 ET" if not is_market_open else None,
            "next_close": "16:00 ET" if is_market_open else None,
            "timezone": "America/New_York",
            "last_updated": now.isoformat()
        }

class USStockMockProvider:
    """US 주식 Mock 데이터 제공자"""
    
    def __init__(self):
        """Mock 데이터 초기화"""
        self.major_stocks = {
            "AAPL": {"name": "Apple Inc.", "sector": "Technology", "price": 175.00},
            "MSFT": {"name": "Microsoft Corporation", "sector": "Technology", "price": 378.00},
            "GOOGL": {"name": "Alphabet Inc.", "sector": "Technology", "price": 140.00},
            "AMZN": {"name": "Amazon.com Inc.", "sector": "Consumer Discretionary", "price": 153.00},
            "TSLA": {"name": "Tesla Inc.", "sector": "Consumer Discretionary", "price": 252.00},
            "NVDA": {"name": "NVIDIA Corporation", "sector": "Technology", "price": 875.00},
            "META": {"name": "Meta Platforms Inc.", "sector": "Technology", "price": 485.00},
            "NFLX": {"name": "Netflix Inc.", "sector": "Communication Services", "price": 445.00},
            "AMD": {"name": "Advanced Micro Devices", "sector": "Technology", "price": 142.00},
            "INTC": {"name": "Intel Corporation", "sector": "Technology", "price": 43.00},
            "JPM": {"name": "JPMorgan Chase & Co.", "sector": "Financial Services", "price": 178.00},
            "BAC": {"name": "Bank of America Corp", "sector": "Financial Services", "price": 41.50},
            "WMT": {"name": "Walmart Inc.", "sector": "Consumer Staples", "price": 165.00},
            "JNJ": {"name": "Johnson & Johnson", "sector": "Healthcare", "price": 155.00},
            "V": {"name": "Visa Inc.", "sector": "Financial Services", "price": 285.00}
        }

    def get_stock_quote(self, symbol: str) -> Dict[str, Any]:
        """Mock 주식 데이터 반환"""
        stock_info = self.major_stocks.get(symbol, {
            "name": f"Unknown Stock {symbol}",
            "sector": "Unknown",
            "price": 100.00
        })
        
        base_price = stock_info["price"]
        
        # 무작위 변동률 생성 (-5% ~ +5%)
        change_percent = random.uniform(-5.0, 5.0)
        change = base_price * change_percent / 100
        current_price = base_price + change
        
        # 일중 고가/저가 생성
        daily_range = base_price * 0.03  # 3% 범위
        high = current_price + random.uniform(0, daily_range)
        low = current_price - random.uniform(0, daily_range)
        open_price = base_price + random.uniform(-daily_range/2, daily_range/2)
        
        return {
            "symbol": symbol,
            "name": stock_info["name"],
            "sector": stock_info["sector"],
            "price": round(current_price, 2),
            "change": round(change, 2),
            "change_percent": f"{change_percent:.2f}",
            "volume": random.randint(1000000, 50000000),
            "latest_trading_day": datetime.now().strftime("%Y-%m-%d"),
            "previous_close": base_price,
            "open": round(open_price, 2),
            "high": round(high, 2),
            "low": round(low, 2),
            "source": "mock"
        }

    def get_earnings_calendar(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """Mock 실적 캘린더 데이터"""
        earnings_events = []
        symbols = list(self.major_stocks.keys())
        
        # 기간 내 날짜들에 대해 실적 이벤트 생성
        current_date = start_date
        while current_date <= end_date:
            # 평일에만 실적 발표
            if current_date.weekday() < 5:
                # 20% 확률로 실적 발표
                if random.random() < 0.2:
                    symbol = random.choice(symbols)
                    stock_info = self.major_stocks[symbol]
                    
                    earnings_events.append({
                        "symbol": symbol,
                        "company_name": stock_info["name"],
                        "report_date": current_date.strftime("%Y-%m-%d"),
                        "fiscal_period": f"Q{random.randint(1, 4)} 2024",
                        "estimate_eps": round(random.uniform(1.0, 5.0), 2),
                        "time": random.choice(["Before Market Open", "After Market Close"]),
                        "sector": stock_info["sector"]
                    })
            
            current_date += timedelta(days=1)
        
        return earnings_events

    def get_dividend_calendar(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """Mock 배당 캘린더 데이터"""
        dividend_events = []
        dividend_stocks = ["AAPL", "MSFT", "JPM", "JNJ", "WMT", "V"]
        
        current_date = start_date
        while current_date <= end_date:
            if current_date.weekday() < 5:  # 평일만
                if random.random() < 0.1:  # 10% 확률
                    symbol = random.choice(dividend_stocks)
                    stock_info = self.major_stocks[symbol]
                    
                    dividend_events.append({
                        "symbol": symbol,
                        "company_name": stock_info["name"],
                        "ex_dividend_date": current_date.strftime("%Y-%m-%d"),
                        "record_date": (current_date + timedelta(days=2)).strftime("%Y-%m-%d"),
                        "payment_date": (current_date + timedelta(days=30)).strftime("%Y-%m-%d"),
                        "dividend_amount": round(random.uniform(0.50, 3.00), 2),
                        "yield": round(random.uniform(1.5, 4.0), 2),
                        "frequency": "Quarterly"
                    })
            
            current_date += timedelta(days=1)
        
        return dividend_events

    def get_economic_calendar(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """Mock 경제 지표 캘린더 데이터"""
        economic_events = [
            {
                "event": "Non-Farm Payrolls",
                "date": "2025-01-10",
                "time": "08:30 ET",
                "importance": "High",
                "forecast": "200K",
                "previous": "227K",
                "actual": None,
                "impact": "USD"
            },
            {
                "event": "Consumer Price Index (CPI)",
                "date": "2025-01-15",
                "time": "08:30 ET",
                "importance": "High",
                "forecast": "2.7%",
                "previous": "2.6%",
                "actual": None,
                "impact": "USD"
            },
            {
                "event": "Federal Reserve Interest Rate Decision",
                "date": "2025-01-20",
                "time": "14:00 ET",
                "importance": "High",
                "forecast": "5.25%",
                "previous": "5.25%",
                "actual": None,
                "impact": "USD"
            },
            {
                "event": "GDP Preliminary",
                "date": "2025-01-25",
                "time": "08:30 ET",
                "importance": "Medium",
                "forecast": "2.8%",
                "previous": "2.8%",
                "actual": None,
                "impact": "USD"
            },
            {
                "event": "Unemployment Rate",
                "date": "2025-01-10",
                "time": "08:30 ET",
                "importance": "High",
                "forecast": "4.2%",
                "previous": "4.2%",
                "actual": None,
                "impact": "USD"
            }
        ]
        
        # 날짜 필터링
        filtered_events = []
        for event in economic_events:
            event_date = datetime.strptime(event["date"], "%Y-%m-%d").date()
            if start_date <= event_date <= end_date:
                filtered_events.append(event)
        
        return filtered_events

# 전역 클라이언트 인스턴스
us_stock_api_client = USStockAPIClient()