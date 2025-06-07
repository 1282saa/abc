"""
DART(전자공시시스템) API 클라이언트
공시정보 및 기업개황 조회 서비스
"""

import os
import sys
import aiohttp
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from pathlib import Path

# 프로젝트 루트 디렉토리 찾기
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.utils.logger import setup_logger

logger = setup_logger("services.dart_api")

class DARTAPIClient:
    """DART(전자공시시스템) Open API 클라이언트"""
    
    def __init__(self, api_key: str = None):
        """DART API 클라이언트 초기화"""
        self.api_key = api_key or os.environ.get("DART_API_KEY")
        self.base_url = "https://opendart.fss.or.kr/api"
        
        if not self.api_key:
            logger.warning("DART API 키가 설정되지 않았습니다. 목업 데이터를 사용합니다.")
        else:
            logger.info("DART API 클라이언트 초기화 완료")

    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        pass
        
    async def get_disclosure_list(
        self,
        corp_code: str = None,
        bgn_de: str = None,
        end_de: str = None,
        corp_cls: str = None,
        page_no: int = 1,
        page_count: int = 10
    ) -> Dict[str, Any]:
        """
        공시검색 - 공시정보를 조회합니다
        
        Args:
            corp_code: 고유번호(8자리) - 특정 회사의 공시만 조회
            bgn_de: 시작일(YYYYMMDD)
            end_de: 종료일(YYYYMMDD) 
            corp_cls: 법인구분 (Y:유가, K:코스닥, N:코넥스, E:기타)
            page_no: 페이지 번호
            page_count: 페이지당 건수(최대 100)
        """
        if not self.api_key:
            return self._get_mock_disclosure_list(corp_code, bgn_de, end_de, corp_cls, page_no, page_count)
            
        try:
            # 기본값 설정: 최근 7일간 공시
            if not end_de:
                end_de = datetime.now().strftime("%Y%m%d")
            if not bgn_de:
                bgn_de = (datetime.now() - timedelta(days=7)).strftime("%Y%m%d")
                
            params = {
                "crtfc_key": self.api_key,
                "page_no": page_no,
                "page_count": min(page_count, 100)  # 최대 100건
            }
            
            # 선택적 파라미터 추가
            if corp_code:
                params["corp_code"] = corp_code
            if bgn_de:
                params["bgn_de"] = bgn_de
            if end_de:
                params["end_de"] = end_de
            if corp_cls:
                params["corp_cls"] = corp_cls
                
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/list.json",
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("status") == "000":
                            return {
                                "success": True,
                                "data": data.get("list", []),
                                "page_info": {
                                    "page_no": data.get("page_no"),
                                    "page_count": data.get("page_count"),
                                    "total_count": data.get("total_count"),
                                    "total_page": data.get("total_page")
                                }
                            }
                        else:
                            logger.error(f"DART API 오류: {data.get('message')}")
                            return {"success": False, "error": data.get("message")}
                    else:
                        logger.error(f"DART API HTTP 오류: {response.status}")
                        return {"success": False, "error": f"HTTP {response.status}"}
                        
        except Exception as e:
            logger.error(f"DART API 공시검색 실패: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_company_info(self, corp_code: str) -> Dict[str, Any]:
        """
        기업개황 조회
        
        Args:
            corp_code: 고유번호(8자리)
        """
        if not self.api_key:
            return self._get_mock_company_info(corp_code)
            
        try:
            params = {
                "crtfc_key": self.api_key,
                "corp_code": corp_code
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/company.json",
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("status") == "000":
                            return {
                                "success": True,
                                "data": {
                                    "corp_name": data.get("corp_name"),
                                    "corp_name_eng": data.get("corp_name_eng"),
                                    "stock_name": data.get("stock_name"),
                                    "stock_code": data.get("stock_code"),
                                    "ceo_nm": data.get("ceo_nm"),
                                    "corp_cls": data.get("corp_cls"),
                                    "adres": data.get("adres"),
                                    "hm_url": data.get("hm_url"),
                                    "ir_url": data.get("ir_url"),
                                    "phn_no": data.get("phn_no"),
                                    "induty_code": data.get("induty_code"),
                                    "est_dt": data.get("est_dt"),
                                    "acc_mt": data.get("acc_mt")
                                }
                            }
                        else:
                            logger.error(f"DART API 기업개황 오류: {data.get('message')}")
                            return {"success": False, "error": data.get("message")}
                    else:
                        logger.error(f"DART API HTTP 오류: {response.status}")
                        return {"success": False, "error": f"HTTP {response.status}"}
                        
        except Exception as e:
            logger.error(f"DART API 기업개황 조회 실패: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_recent_disclosures(
        self, 
        corp_cls: str = "Y", 
        days: int = 7,
        important_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        최근 중요 공시 조회 (캘린더 이벤트용)
        
        Args:
            corp_cls: 법인구분 (Y:유가, K:코스닥)
            days: 조회 기간 (일)
            important_only: 중요 공시만 필터링
        """
        if not self.api_key:
            return self._get_mock_recent_disclosures(corp_cls, days, important_only)
            
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            result = await self.get_disclosure_list(
                bgn_de=start_date.strftime("%Y%m%d"),
                end_de=end_date.strftime("%Y%m%d"),
                corp_cls=corp_cls,
                page_count=100
            )
            
            if not result["success"]:
                return []
            
            disclosures = result["data"]
            
            # 중요 공시 키워드 필터링
            if important_only:
                important_keywords = [
                    "실적발표", "실적공시", "분기보고서", "반기보고서", "사업보고서",
                    "임시주주총회", "정기주주총회", "배당", "유상증자", "무상증자",
                    "합병", "분할", "인수", "매각", "대규모내부거래",
                    "주요사항보고", "공시정정", "특별관계자거래"
                ]
                
                filtered_disclosures = []
                for disclosure in disclosures:
                    report_name = disclosure.get("report_nm", "")
                    if any(keyword in report_name for keyword in important_keywords):
                        filtered_disclosures.append(disclosure)
                
                return filtered_disclosures[:20]  # 최대 20건
            
            return disclosures[:20]
            
        except Exception as e:
            logger.error(f"최근 공시 조회 실패: {e}")
            return []
    
    async def search_company_by_name(self, company_name: str) -> List[Dict[str, Any]]:
        """
        회사명으로 기업 검색 (부분 검색)
        """
        if not self.api_key:
            return self._get_mock_company_search(company_name)
            
        try:
            # 최근 30일 공시에서 회사명 검색
            result = await self.get_disclosure_list(
                bgn_de=(datetime.now() - timedelta(days=30)).strftime("%Y%m%d"),
                page_count=100
            )
            
            if not result["success"]:
                return []
            
            # 회사명으로 필터링
            companies = {}
            for disclosure in result["data"]:
                corp_name = disclosure.get("corp_name", "")
                if company_name.lower() in corp_name.lower():
                    corp_code = disclosure.get("corp_code")
                    if corp_code and corp_code not in companies:
                        companies[corp_code] = {
                            "corp_code": corp_code,
                            "corp_name": corp_name,
                            "stock_code": disclosure.get("stock_code"),
                            "corp_cls": disclosure.get("corp_cls")
                        }
            
            return list(companies.values())[:10]  # 최대 10건
            
        except Exception as e:
            logger.error(f"회사 검색 실패: {e}")
            return []

    async def get_upcoming_disclosure_events(
        self, 
        start_date: str, 
        end_date: str,
        corp_cls: str = None
    ) -> List[Dict[str, Any]]:
        """
        향후 공시 이벤트 조회 (주식 캘린더용)
        
        Args:
            start_date: 시작일 (YYYY-MM-DD)
            end_date: 종료일 (YYYY-MM-DD)
            corp_cls: 법인구분 (Y:유가, K:코스닥)
        """
        try:
            # 날짜 형식 변환
            bgn_de = start_date.replace("-", "")
            end_de = end_date.replace("-", "")
            
            result = await self.get_disclosure_list(
                bgn_de=bgn_de,
                end_de=end_de,
                corp_cls=corp_cls,
                page_count=100
            )
            
            if not result["success"]:
                return self._get_mock_upcoming_events(start_date, end_date)
            
            # 공시를 캘린더 이벤트 형식으로 변환
            events = []
            for disclosure in result["data"]:
                rcept_dt = disclosure.get("rcept_dt")
                if rcept_dt and len(rcept_dt) == 8:
                    event_date = f"{rcept_dt[:4]}-{rcept_dt[4:6]}-{rcept_dt[6:8]}"
                    
                    events.append({
                        "id": f"disclosure_{disclosure.get('rcept_no')}",
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
            
            return events[:50]  # 최대 50건
            
        except Exception as e:
            logger.error(f"향후 공시 이벤트 조회 실패: {e}")
            return self._get_mock_upcoming_events(start_date, end_date)

    # Mock 데이터 메서드들
    def _get_mock_disclosure_list(self, corp_code, bgn_de, end_de, corp_cls, page_no, page_count):
        """목업 공시 리스트 데이터"""
        mock_disclosures = [
            {
                "corp_code": "00126380",
                "corp_name": "삼성전자",
                "stock_code": "005930",
                "corp_cls": "Y",
                "report_nm": "분기보고서 (제54기 1분기)",
                "rcept_no": "20241101000001",
                "flr_nm": "삼성전자",
                "rcept_dt": "20241101",
                "rm": ""
            },
            {
                "corp_code": "00164779",
                "corp_name": "SK하이닉스",
                "stock_code": "000660",
                "corp_cls": "Y",
                "report_nm": "연결재무제표 공시",
                "rcept_no": "20241102000001",
                "flr_nm": "SK하이닉스",
                "rcept_dt": "20241102",
                "rm": ""
            },
            {
                "corp_code": "00401731",
                "corp_name": "NAVER",
                "stock_code": "035420",
                "corp_cls": "Y",
                "report_nm": "주요사항보고서",
                "rcept_no": "20241103000001",
                "flr_nm": "NAVER",
                "rcept_dt": "20241103",
                "rm": ""
            }
        ]
        
        return {
            "success": False,  # 목업 데이터임을 표시
            "data": mock_disclosures,
            "page_info": {
                "page_no": 1,
                "page_count": len(mock_disclosures),
                "total_count": len(mock_disclosures),
                "total_page": 1
            },
            "message": "DART API 키가 없어 목업 데이터를 사용합니다."
        }

    def _get_mock_company_info(self, corp_code):
        """목업 기업 정보 데이터"""
        mock_companies = {
            "00126380": {
                "corp_name": "삼성전자",
                "corp_name_eng": "SAMSUNG ELECTRONICS CO., LTD.",
                "stock_name": "삼성전자",
                "stock_code": "005930",
                "ceo_nm": "한종희",
                "corp_cls": "Y",
                "adres": "경기도 수원시 영통구 삼성로 129",
                "hm_url": "http://www.samsung.com/sec",
                "ir_url": "http://www.samsung.com/sec/ir",
                "phn_no": "031-200-1114",
                "induty_code": "26400",
                "est_dt": "19690113",
                "acc_mt": "12"
            },
            "00164779": {
                "corp_name": "SK하이닉스",
                "corp_name_eng": "SK hynix Inc.",
                "stock_name": "SK하이닉스",
                "stock_code": "000660",
                "ceo_nm": "곽노정",
                "corp_cls": "Y",
                "adres": "경기도 이천시 부발읍 경충대로 2091",
                "hm_url": "http://www.skhynix.com",
                "ir_url": "http://www.skhynix.com/eng/ir",
                "phn_no": "031-5185-4114",
                "induty_code": "26110",
                "est_dt": "19830211",
                "acc_mt": "12"
            }
        }
        
        company_data = mock_companies.get(corp_code, {
            "corp_name": f"회사{corp_code}",
            "corp_name_eng": f"Company {corp_code}",
            "stock_name": f"종목{corp_code}",
            "stock_code": "000000",
            "ceo_nm": "대표이사",
            "corp_cls": "Y",
            "adres": "서울특별시",
            "hm_url": "http://example.com",
            "ir_url": "http://example.com/ir",
            "phn_no": "02-000-0000",
            "induty_code": "00000",
            "est_dt": "20000101",
            "acc_mt": "12"
        })
        
        return {
            "success": False,  # 목업 데이터임을 표시
            "data": company_data,
            "message": "DART API 키가 없어 목업 데이터를 사용합니다."
        }

    def _get_mock_recent_disclosures(self, corp_cls, days, important_only):
        """목업 최근 공시 데이터"""
        mock_disclosures = [
            {
                "corp_code": "00126380",
                "corp_name": "삼성전자",
                "stock_code": "005930",
                "report_nm": "분기보고서 (제54기 1분기)",
                "rcept_dt": datetime.now().strftime("%Y%m%d")
            },
            {
                "corp_code": "00164779",
                "corp_name": "SK하이닉스",
                "stock_code": "000660",
                "report_nm": "실적발표",
                "rcept_dt": (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
            },
            {
                "corp_code": "00401731",
                "corp_name": "NAVER",
                "stock_code": "035420",
                "report_nm": "주주총회소집공고",
                "rcept_dt": (datetime.now() - timedelta(days=2)).strftime("%Y%m%d")
            }
        ]
        
        return mock_disclosures

    def _get_mock_company_search(self, company_name):
        """목업 회사 검색 데이터"""
        all_companies = [
            {"corp_code": "00126380", "corp_name": "삼성전자", "stock_code": "005930", "corp_cls": "Y"},
            {"corp_code": "00164779", "corp_name": "SK하이닉스", "stock_code": "000660", "corp_cls": "Y"},
            {"corp_code": "00401731", "corp_name": "NAVER", "stock_code": "035420", "corp_cls": "Y"},
            {"corp_code": "00126380", "corp_name": "삼성SDI", "stock_code": "006400", "corp_cls": "Y"},
            {"corp_code": "00108860", "corp_name": "현대자동차", "stock_code": "005380", "corp_cls": "Y"},
        ]
        
        # 회사명으로 필터링
        filtered = [
            company for company in all_companies 
            if company_name.lower() in company["corp_name"].lower()
        ]
        
        return filtered[:10]

    def _get_mock_upcoming_events(self, start_date, end_date):
        """목업 향후 이벤트 데이터"""
        events = []
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        # 주요 기업들의 예상 공시 일정
        companies = [
            {"code": "005930", "name": "삼성전자", "corp_code": "00126380"},
            {"code": "000660", "name": "SK하이닉스", "corp_code": "00164779"},
            {"code": "035420", "name": "NAVER", "corp_code": "00401731"},
        ]
        
        disclosure_types = ["분기보고서", "사업보고서", "주주총회소집공고", "실적발표"]
        
        current_date = start_dt
        event_id = 1
        
        while current_date <= end_dt and len(events) < 20:
            for company in companies:
                if len(events) >= 20:
                    break
                    
                # 랜덤하게 공시 생성 (5일에 한 번 정도)
                if current_date.day % 5 == 0:
                    disclosure_type = disclosure_types[event_id % len(disclosure_types)]
                    
                    events.append({
                        "id": f"mock_disclosure_{event_id}",
                        "title": f"{company['name']} {disclosure_type}",
                        "date": current_date.strftime("%Y-%m-%d"),
                        "eventType": "disclosure",
                        "stockCode": company["code"],
                        "stockName": company["name"],
                        "description": f"{company['name']} - {disclosure_type}",
                        "marketType": "domestic",
                        "corp_cls": "Y",
                        "disclosure_url": f"http://dart.fss.or.kr/mock/{company['corp_code']}"
                    })
                    
                    event_id += 1
            
            current_date += timedelta(days=1)
        
        return events

# 전역 DART API 클라이언트 인스턴스
dart_api_client = DARTAPIClient()