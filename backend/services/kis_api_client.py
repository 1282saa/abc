"""
한국투자증권 Open API 클라이언트
주식 데이터, 시장 지수, 투자자별 매매동향 등을 제공
"""

import os
import sys
import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path

# 프로젝트 루트 디렉토리 찾기
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.utils.logger import setup_logger

logger = setup_logger("services.kis_api")

class KISAPIClient:
    """한국투자증권 Open API 클라이언트"""
    
    def __init__(self):
        """KIS API 클라이언트 초기화"""
        self.app_key = os.environ.get("KIS_APP_KEY")
        self.app_secret = os.environ.get("KIS_APP_SECRET")
        self.base_url = os.environ.get("KIS_BASE_URL", "https://openapivts.koreainvestment.com:29443")
        self.env = "vts"  # virtual trading system
        
        self.access_token = None
        self.token_expires_at = None
        self.token_file = PROJECT_ROOT / "kis_token.json"
        
        if not self.app_key or not self.app_secret:
            logger.warning("KIS API 키가 설정되지 않았습니다.")

    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        await self._load_token()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        pass

    async def _load_token(self):
        """저장된 토큰 로드"""
        if self.token_file.exists():
            try:
                with open(self.token_file, 'r') as f:
                    token_data = json.load(f)
                    expires_at = datetime.fromisoformat(token_data['expires_at'])
                    if expires_at > datetime.now():
                        self.access_token = token_data['access_token']
                        self.token_expires_at = expires_at
                        logger.info("기존 토큰 로드 성공")
            except Exception as e:
                logger.error(f"토큰 로드 실패: {e}")

    async def _save_token(self):
        """토큰을 파일에 저장"""
        if self.access_token and self.token_expires_at:
            token_data = {
                "access_token": self.access_token,
                "expires_at": self.token_expires_at.isoformat()
            }
            with open(self.token_file, 'w') as f:
                json.dump(token_data, f)

    async def get_access_token(self) -> Optional[str]:
        """액세스 토큰 발급 및 갱신"""
        if not self.app_key or not self.app_secret:
            logger.warning("KIS API 키가 없어 토큰 발급을 건너뜁니다.")
            return None
            
        if self.access_token and self.token_expires_at and datetime.now() < self.token_expires_at:
            return self.access_token
            
        url = f"{self.base_url}/oauth2/tokenP"
        data = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "appsecret": self.app_secret
        }
        
        headers = {
            "content-type": "application/json; charset=utf-8",
            "appkey": self.app_key,
            "appsecret": self.app_secret
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data, headers=headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        self.access_token = result["access_token"]
                        self.token_expires_at = datetime.now() + timedelta(seconds=result["expires_in"])
                        await self._save_token()
                        logger.info("토큰 발급 성공")
                        return self.access_token
                    else:
                        logger.error(f"토큰 발급 실패: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"토큰 발급 중 오류: {e}")
            return None

    async def _get_headers(self, tr_id: str) -> Dict[str, str]:
        """KIS API용 헤더 생성"""
        token = await self.get_access_token()
        if not token:
            return {}
            
        # 모의투자인 경우 TR_ID 변경
        if self.env == "vts" and tr_id[0] in ('T', 'J', 'C'):
            tr_id = 'V' + tr_id[1:]
            
        return {
            "authorization": f"Bearer {token}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "tr_id": tr_id,
            "custtype": "P",
            "content-type": "application/json; charset=utf-8"
        }

    async def get_stock_price(self, stock_code: str) -> Dict[str, Any]:
        """주식 현재가 조회"""
        if not self.app_key:
            return self._get_mock_stock_price(stock_code)
            
        url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-price"
        headers = await self._get_headers("FHKST01010100")
        
        params = {
            "fid_cond_mrkt_div_code": "J",
            "fid_input_iscd": stock_code
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        output = data.get("output", {})
                        return {
                            "stock_code": stock_code,
                            "current_price": int(output.get("stck_prpr", 0)),
                            "change_price": int(output.get("prdy_vrss", 0)),
                            "change_rate": float(output.get("prdy_ctrt", 0)),
                            "volume": int(output.get("acml_vol", 0)),
                            "market_cap": int(output.get("hts_avls", 0)),
                            "success": True
                        }
        except Exception as e:
            logger.error(f"주식 현재가 조회 실패: {e}")
            
        return self._get_mock_stock_price(stock_code)

    async def get_major_indices(self) -> Dict[str, Any]:
        """주요 지수 조회 (KOSPI, KOSDAQ)"""
        if not self.app_key:
            return self._get_mock_indices()
            
        indices = {}
        index_codes = {
            "KOSPI": "0001",
            "KOSDAQ": "1001"
        }
        
        url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-index-price"
        headers = await self._get_headers("FHPUP02100000")
        
        for index_name, index_code in index_codes.items():
            try:
                params = {
                    "fid_cond_mrkt_div_code": "U",
                    "fid_input_iscd": index_code
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=headers, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            output = data.get("output", {})
                            indices[index_name] = {
                                "current": float(output.get("bstp_nmix_prpr", 0)),
                                "change": float(output.get("bstp_nmix_prdy_vrss", 0)),
                                "change_rate": float(output.get("prdy_vrss_sign", 0))
                            }
            except Exception as e:
                logger.error(f"{index_name} 지수 조회 실패: {e}")
                
        return indices if indices else self._get_mock_indices()

    async def get_market_holidays(self, year: str) -> List[str]:
        """시장 휴장일 조회"""
        if not self.app_key:
            return self._get_mock_holidays()
            
        url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/chk-holiday"
        headers = await self._get_headers("CTCA0903R")
        
        holidays = []
        try:
            # 월별로 조회
            for month in range(1, 13):
                params = {
                    "BASS_DT": f"{year}{month:02d}01",
                    "CTX_AREA_NK": "",
                    "CTX_AREA_FK": ""
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=headers, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            output = data.get("output", [])
                            for item in output:
                                holiday_date = item.get("bass_dt")
                                if holiday_date:
                                    holidays.append(f"{holiday_date[:4]}-{holiday_date[4:6]}-{holiday_date[6:8]}")
        except Exception as e:
            logger.error(f"휴장일 조회 실패: {e}")
            
        return holidays if holidays else self._get_mock_holidays()

    async def get_earnings_calendar(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """실적발표 일정 조회 (기업 정보 기반)"""
        # KIS API는 직접적인 실적발표 일정 API가 없으므로 주요 기업들의 예상 일정을 반환
        major_companies = [
            {"code": "005930", "name": "삼성전자"},
            {"code": "000660", "name": "SK하이닉스"},
            {"code": "035420", "name": "NAVER"},
            {"code": "005380", "name": "현대자동차"},
            {"code": "006400", "name": "삼성SDI"},
            {"code": "051910", "name": "LG화학"},
            {"code": "068270", "name": "셀트리온"},
            {"code": "035720", "name": "카카오"},
        ]
        
        earnings_events = []
        
        # 분기별 실적발표 예상 시기
        current_year = datetime.now().year
        quarters = [
            {"quarter": "Q1", "month": 4, "day": 15},
            {"quarter": "Q2", "month": 7, "day": 15},
            {"quarter": "Q3", "month": 10, "day": 15},
            {"quarter": "Q4", "month": 1, "day": 30, "year_offset": 1},
        ]
        
        for quarter in quarters:
            year = current_year + quarter.get("year_offset", 0)
            earnings_date = datetime(year, quarter["month"], quarter["day"])
            earnings_date_str = earnings_date.strftime("%Y-%m-%d")
            
            # 날짜 범위 확인
            if start_date <= earnings_date_str <= end_date:
                for company in major_companies:
                    earnings_events.append({
                        "id": f"earnings_{company['code']}_{quarter['quarter']}_{year}",
                        "title": f"{company['name']} 실적발표",
                        "date": earnings_date_str,
                        "eventType": "earnings",
                        "stockCode": company["code"],
                        "stockName": company["name"],
                        "description": f"{year-1 if quarter['quarter'] == 'Q4' else year}년 {quarter['quarter']} 실적발표",
                        "marketType": "domestic"
                    })
                    
        return earnings_events

    def _get_mock_stock_price(self, stock_code: str) -> Dict[str, Any]:
        """목업 주식 데이터"""
        mock_prices = {
            "005930": {"price": 71000, "name": "삼성전자"},
            "000660": {"price": 89000, "name": "SK하이닉스"},
            "035420": {"price": 180000, "name": "NAVER"},
            "005380": {"price": 185000, "name": "현대자동차"},
        }
        
        data = mock_prices.get(stock_code, {"price": 50000, "name": f"종목{stock_code}"})
        
        return {
            "stock_code": stock_code,
            "current_price": data["price"],
            "change_price": data["price"] * 0.01,  # 1% 변동
            "change_rate": 1.0,
            "volume": 1000000,
            "market_cap": data["price"] * 1000000,
            "success": False,  # 목업 데이터임을 표시
            "message": "KIS API 키가 없어 목업 데이터를 사용합니다."
        }

    def _get_mock_indices(self) -> Dict[str, Any]:
        """목업 지수 데이터"""
        return {
            "KOSPI": {"current": 2500.0, "change": 20.0, "change_rate": 0.8},
            "KOSDAQ": {"current": 850.0, "change": 15.0, "change_rate": 1.8}
        }

    def _get_mock_holidays(self) -> List[str]:
        """목업 휴장일 데이터"""
        current_year = datetime.now().year
        return [
            f"{current_year}-01-01",  # 신정
            f"{current_year}-03-01",  # 3.1절
            f"{current_year}-05-05",  # 어린이날
            f"{current_year}-06-06",  # 현충일
            f"{current_year}-08-15",  # 광복절
            f"{current_year}-10-03",  # 개천절
            f"{current_year}-10-09",  # 한글날
            f"{current_year}-12-25",  # 크리스마스
        ]

# 전역 클라이언트 인스턴스
kis_api_client = KISAPIClient()