"""
Upbit API 클라이언트

업비트(Upbit) API를 통해 실시간 가상화폐 데이터를 제공하는 서비스입니다.
실제 API 연동과 Mock 데이터 대체 기능을 지원합니다.
"""

import aiohttp
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import logging
import json
from dataclasses import dataclass
import random

# 로거 설정
logger = logging.getLogger(__name__)

@dataclass
class CryptoQuote:
    """가상화폐 시세 정보"""
    symbol: str
    korean_name: str
    trade_price: float
    change: str  # 'RISE', 'FALL', 'EVEN'
    change_price: float
    change_rate: float
    trade_volume: float
    acc_trade_volume_24h: float
    high_price: float
    low_price: float
    opening_price: float
    timestamp: datetime

class UpbitAPIClient:
    """업비트 API 클라이언트"""
    
    def __init__(self):
        self.base_url = "https://api.upbit.com/v1"
        self.session = None
        self.mock_mode = False
        self._supported_symbols = {
            'BTC': '비트코인',
            'ETH': '이더리움', 
            'XRP': '리플',
            'ADA': '에이다',
            'DOT': '폴카닷',
            'SOL': '솔라나',
            'AVAX': '아발란체',
            'MATIC': '폴리곤',
            'ATOM': '코스모스',
            'LINK': '체인링크',
            'UNI': '유니스왑',
            'LTC': '라이트코인',
            'BCH': '비트코인캐시',
            'ETC': '이더리움클래식',
            'DOGE': '도지코인',
            'SHIB': '시바이누',
            'SAND': '더샌드박스',
            'MANA': '디센트럴랜드',
            'TRX': '트론',
            'ALGO': '알고랜드'
        }
        
        # Mock 데이터 생성기
        self._mock_provider = CryptoMockProvider()
    
    async def __aenter__(self):
        """컨텍스트 매니저 진입"""
        await self._init_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 매니저 종료"""
        await self._close_session()
    
    async def _init_session(self):
        """HTTP 세션 초기화"""
        if not self.session or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=10)
            self.session = aiohttp.ClientSession(timeout=timeout)
    
    async def _close_session(self):
        """HTTP 세션 종료"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def get_market_all(self) -> List[Dict[str, Any]]:
        """마켓 코드 조회"""
        try:
            await self._init_session()
            
            url = f"{self.base_url}/market/all"
            params = {"isDetails": "true"}
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    # KRW 마켓만 필터링
                    krw_markets = [market for market in data if market['market'].startswith('KRW-')]
                    return krw_markets
                else:
                    logger.error(f"마켓 코드 조회 실패: {response.status}")
                    return self._mock_provider.get_market_all()
                    
        except Exception as e:
            logger.error(f"마켓 코드 조회 중 오류: {str(e)}")
            self.mock_mode = True
            return self._mock_provider.get_market_all()
    
    async def get_ticker(self, symbols: List[str]) -> List[CryptoQuote]:
        """현재가 정보 조회"""
        try:
            await self._init_session()
            
            # KRW- 마켓 코드로 변환
            markets = [f"KRW-{symbol}" for symbol in symbols]
            markets_param = ",".join(markets)
            
            url = f"{self.base_url}/ticker"
            params = {"markets": markets_param}
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    quotes = []
                    
                    for item in data:
                        symbol = item['market'].replace('KRW-', '')
                        korean_name = self._supported_symbols.get(symbol, symbol)
                        
                        quote = CryptoQuote(
                            symbol=symbol,
                            korean_name=korean_name,
                            trade_price=item['trade_price'],
                            change=item['change'],
                            change_price=item['change_price'],
                            change_rate=item['change_rate'],
                            trade_volume=item['trade_volume'],
                            acc_trade_volume_24h=item['acc_trade_volume_24h'],
                            high_price=item['high_price'],
                            low_price=item['low_price'],
                            opening_price=item['opening_price'],
                            timestamp=datetime.now()
                        )
                        quotes.append(quote)
                    
                    return quotes
                else:
                    logger.error(f"현재가 조회 실패: {response.status}")
                    return self._mock_provider.get_ticker(symbols)
                    
        except Exception as e:
            logger.error(f"현재가 조회 중 오류: {str(e)}")
            self.mock_mode = True
            return self._mock_provider.get_ticker(symbols)
    
    async def get_single_ticker(self, symbol: str) -> Optional[CryptoQuote]:
        """단일 종목 현재가 조회"""
        quotes = await self.get_ticker([symbol])
        return quotes[0] if quotes else None
    
    async def get_major_cryptos(self) -> List[CryptoQuote]:
        """주요 가상화폐 시세 조회"""
        major_symbols = ['BTC', 'ETH', 'XRP', 'ADA', 'DOT', 'SOL', 'AVAX', 'MATIC']
        return await self.get_ticker(major_symbols)
    
    async def get_candles_daily(self, symbol: str, count: int = 30) -> List[Dict[str, Any]]:
        """일봉 데이터 조회"""
        try:
            await self._init_session()
            
            market = f"KRW-{symbol}"
            url = f"{self.base_url}/candles/days"
            params = {
                "market": market,
                "count": count
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    logger.error(f"일봉 데이터 조회 실패: {response.status}")
                    return self._mock_provider.get_candles_daily(symbol, count)
                    
        except Exception as e:
            logger.error(f"일봉 데이터 조회 중 오류: {str(e)}")
            return self._mock_provider.get_candles_daily(symbol, count)
    
    async def get_orderbook(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """호가 정보 조회"""
        try:
            await self._init_session()
            
            markets = [f"KRW-{symbol}" for symbol in symbols]
            markets_param = ",".join(markets)
            
            url = f"{self.base_url}/orderbook"
            params = {"markets": markets_param}
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    logger.error(f"호가 정보 조회 실패: {response.status}")
                    return self._mock_provider.get_orderbook(symbols)
                    
        except Exception as e:
            logger.error(f"호가 정보 조회 중 오류: {str(e)}")
            return self._mock_provider.get_orderbook(symbols)
    
    async def get_crypto_events(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """가상화폐 관련 이벤트 생성
        
        실제 이벤트 데이터는 없으므로, 주요 가상화폐의 가격 변동을 기반으로
        캘린더 이벤트를 생성합니다.
        """
        try:
            # 주요 가상화폐 시세 조회
            major_cryptos = await self.get_major_cryptos()
            
            events = []
            for crypto in major_cryptos:
                # 가격 변동이 큰 경우 이벤트로 추가
                if abs(crypto.change_rate) > 0.05:  # 5% 이상 변동
                    event_type = "crypto_surge" if crypto.change == "RISE" else "crypto_drop"
                    change_direction = "급등" if crypto.change_rate > 0 else "급락"
                    
                    event = {
                        "id": f"crypto_{crypto.symbol}_{datetime.now().strftime('%Y%m%d')}",
                        "title": f"{crypto.korean_name} {change_direction}",
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "eventType": "crypto",
                        "cryptoSymbol": crypto.symbol,
                        "cryptoName": crypto.korean_name,
                        "description": f"{crypto.korean_name} {crypto.change_rate*100:.2f}% {change_direction} (현재가: {crypto.trade_price:,.0f}원)",
                        "marketType": "crypto",
                        "change_rate": crypto.change_rate,
                        "current_price": crypto.trade_price,
                        "volume_24h": crypto.acc_trade_volume_24h
                    }
                    events.append(event)
            
            # 예정된 가상화폐 이벤트들 (하드코딩된 예시)
            scheduled_events = self._get_scheduled_crypto_events(start_date, end_date)
            events.extend(scheduled_events)
            
            return events
            
        except Exception as e:
            logger.error(f"가상화폐 이벤트 생성 중 오류: {str(e)}")
            return self._mock_provider.get_crypto_events(start_date, end_date)
    
    def _get_scheduled_crypto_events(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """예정된 가상화폐 이벤트 (예시 데이터)"""
        scheduled_events = [
            {
                "id": "crypto_halving_2025",
                "title": "비트코인 반감기",
                "date": "2025-03-15",
                "eventType": "crypto",
                "cryptoSymbol": "BTC",
                "cryptoName": "비트코인",
                "description": "비트코인 블록 보상 반감기 예정",
                "marketType": "crypto",
                "importance": "high"
            },
            {
                "id": "crypto_ethereum_upgrade_2025",
                "title": "이더리움 업그레이드",
                "date": "2025-02-20",
                "eventType": "crypto",
                "cryptoSymbol": "ETH",
                "cryptoName": "이더리움",
                "description": "이더리움 네트워크 주요 업그레이드",
                "marketType": "crypto",
                "importance": "high"
            },
            {
                "id": "crypto_listing_new",
                "title": "신규 코인 상장",
                "date": "2025-01-25",
                "eventType": "crypto",
                "description": "업비트 신규 코인 상장 예정",
                "marketType": "crypto",
                "importance": "medium"
            }
        ]
        
        # 날짜 범위 필터링
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        filtered_events = []
        for event in scheduled_events:
            event_date = datetime.strptime(event["date"], "%Y-%m-%d").date()
            if start <= event_date <= end:
                filtered_events.append(event)
        
        return filtered_events
    
    def get_supported_symbols(self) -> Dict[str, str]:
        """지원되는 가상화폐 심볼 목록 반환"""
        return self._supported_symbols.copy()


class CryptoMockProvider:
    """가상화폐 Mock 데이터 제공자"""
    
    def __init__(self):
        self.base_prices = {
            'BTC': 93000000,   # 비트코인
            'ETH': 3850000,    # 이더리움
            'XRP': 650,        # 리플
            'ADA': 520,        # 에이다
            'DOT': 8200,       # 폴카닷
            'SOL': 245000,     # 솔라나
            'AVAX': 45000,     # 아발란체
            'MATIC': 1150,     # 폴리곤
            'ATOM': 12500,     # 코스모스
            'LINK': 25000,     # 체인링크
            'UNI': 8500,       # 유니스왑
            'LTC': 110000,     # 라이트코인
            'BCH': 520000,     # 비트코인캐시
            'ETC': 35000,      # 이더리움클래식
            'DOGE': 320,       # 도지코인
            'SHIB': 0.03,      # 시바이누
            'SAND': 850,       # 더샌드박스
            'MANA': 950,       # 디센트럴랜드
            'TRX': 250,        # 트론
            'ALGO': 450        # 알고랜드
        }
        
        self.korean_names = {
            'BTC': '비트코인',
            'ETH': '이더리움',
            'XRP': '리플',
            'ADA': '에이다',
            'DOT': '폴카닷',
            'SOL': '솔라나',
            'AVAX': '아발란체',
            'MATIC': '폴리곤',
            'ATOM': '코스모스',
            'LINK': '체인링크',
            'UNI': '유니스왑',
            'LTC': '라이트코인',
            'BCH': '비트코인캐시',
            'ETC': '이더리움클래식',
            'DOGE': '도지코인',
            'SHIB': '시바이누',
            'SAND': '더샌드박스',
            'MANA': '디센트럴랜드',
            'TRX': '트론',
            'ALGO': '알고랜드'
        }
    
    def get_market_all(self) -> List[Dict[str, Any]]:
        """Mock 마켓 코드 데이터"""
        markets = []
        for symbol, korean_name in self.korean_names.items():
            markets.append({
                "market": f"KRW-{symbol}",
                "korean_name": korean_name,
                "english_name": symbol
            })
        return markets
    
    def get_ticker(self, symbols: List[str]) -> List[CryptoQuote]:
        """Mock 현재가 데이터"""
        quotes = []
        
        for symbol in symbols:
            if symbol not in self.base_prices:
                continue
                
            base_price = self.base_prices[symbol]
            korean_name = self.korean_names.get(symbol, symbol)
            
            # 랜덤 변동률 생성 (-10% ~ +10%)
            change_rate = random.uniform(-0.1, 0.1)
            change_price = base_price * change_rate
            trade_price = base_price + change_price
            
            # 변동 방향 결정
            change = "RISE" if change_rate > 0 else "FALL" if change_rate < 0 else "EVEN"
            
            quote = CryptoQuote(
                symbol=symbol,
                korean_name=korean_name,
                trade_price=trade_price,
                change=change,
                change_price=abs(change_price),
                change_rate=change_rate,
                trade_volume=random.uniform(0.1, 100),
                acc_trade_volume_24h=random.uniform(1000, 100000),
                high_price=trade_price * random.uniform(1.01, 1.05),
                low_price=trade_price * random.uniform(0.95, 0.99),
                opening_price=trade_price * random.uniform(0.98, 1.02),
                timestamp=datetime.now()
            )
            quotes.append(quote)
        
        return quotes
    
    def get_candles_daily(self, symbol: str, count: int) -> List[Dict[str, Any]]:
        """Mock 일봉 데이터"""
        if symbol not in self.base_prices:
            return []
            
        base_price = self.base_prices[symbol]
        candles = []
        
        for i in range(count):
            date = datetime.now() - timedelta(days=i)
            
            # 일별 랜덤 변동
            open_price = base_price * random.uniform(0.95, 1.05)
            close_price = open_price * random.uniform(0.95, 1.05)
            high_price = max(open_price, close_price) * random.uniform(1.0, 1.03)
            low_price = min(open_price, close_price) * random.uniform(0.97, 1.0)
            
            candle = {
                "market": f"KRW-{symbol}",
                "candle_date_time_utc": date.strftime("%Y-%m-%dT00:00:00"),
                "candle_date_time_kst": date.strftime("%Y-%m-%dT09:00:00"),
                "opening_price": open_price,
                "high_price": high_price,
                "low_price": low_price,
                "trade_price": close_price,
                "timestamp": int(date.timestamp() * 1000),
                "candle_acc_trade_price": random.uniform(1000000, 10000000),
                "candle_acc_trade_volume": random.uniform(100, 1000)
            }
            candles.append(candle)
        
        return candles
    
    def get_orderbook(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """Mock 호가 데이터"""
        orderbooks = []
        
        for symbol in symbols:
            if symbol not in self.base_prices:
                continue
                
            base_price = self.base_prices[symbol]
            
            # 매도/매수 호가 생성
            orderbook_units = []
            for i in range(15):  # 15호가
                ask_price = base_price * (1 + (i + 1) * 0.001)  # 매도가
                bid_price = base_price * (1 - (i + 1) * 0.001)  # 매수가
                
                orderbook_units.append({
                    "ask_price": ask_price,
                    "bid_price": bid_price,
                    "ask_size": random.uniform(0.1, 10),
                    "bid_size": random.uniform(0.1, 10)
                })
            
            orderbook = {
                "market": f"KRW-{symbol}",
                "timestamp": int(datetime.now().timestamp() * 1000),
                "total_ask_size": sum(unit["ask_size"] for unit in orderbook_units),
                "total_bid_size": sum(unit["bid_size"] for unit in orderbook_units),
                "orderbook_units": orderbook_units
            }
            orderbooks.append(orderbook)
        
        return orderbooks
    
    def get_crypto_events(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Mock 가상화폐 이벤트"""
        events = [
            {
                "id": "mock_crypto_event_1",
                "title": "비트코인 급등",
                "date": "2025-06-04",
                "eventType": "crypto",
                "cryptoSymbol": "BTC",
                "cryptoName": "비트코인",
                "description": "비트코인 7.5% 급등 (현재가: 93,000,000원)",
                "marketType": "crypto",
                "change_rate": 0.075,
                "current_price": 93000000,
                "volume_24h": 15000
            },
            {
                "id": "mock_crypto_event_2",
                "title": "이더리움 변동성 확대",
                "date": "2025-06-04",
                "eventType": "crypto", 
                "cryptoSymbol": "ETH",
                "cryptoName": "이더리움",
                "description": "이더리움 업그레이드 소식으로 변동성 확대",
                "marketType": "crypto",
                "change_rate": -0.035,
                "current_price": 3850000,
                "volume_24h": 8500
            }
        ]
        
        return events


# 전역 Upbit API 클라이언트 인스턴스
upbit_api_client = UpbitAPIClient()