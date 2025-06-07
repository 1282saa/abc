#!/usr/bin/env python3
"""
DART API 클라이언트 테스트 스크립트

DART API 클라이언트의 기능을 테스트합니다.
실제 API 키가 있으면 실제 API를 호출하고, 없으면 목업 데이터를 사용합니다.
"""

import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# 프로젝트 루트 추가
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# 환경변수 로드
load_dotenv(PROJECT_ROOT / ".env")

from backend.services.dart_api_client import DARTAPIClient

async def test_dart_api():
    """DART API 클라이언트 테스트"""
    print("=" * 60)
    print("DART API 클라이언트 테스트 시작")
    print("=" * 60)
    
    # API 키 확인
    api_key = os.environ.get("DART_API_KEY")
    if api_key:
        print(f"✅ DART API 키 설정됨: {api_key[:10]}...")
        print("🔄 실제 DART API를 호출합니다.")
    else:
        print("⚠️ DART API 키가 설정되지 않음")
        print("🔄 목업 데이터를 사용합니다.")
    print()
    
    async with DARTAPIClient() as dart_client:
        # 1. 최근 공시 조회 테스트
        print("1. 최근 공시 조회 테스트")
        print("-" * 40)
        try:
            recent_disclosures = await dart_client.get_recent_disclosures(
                corp_cls="Y",
                days=7,
                important_only=True
            )
            
            print(f"📊 조회된 공시 건수: {len(recent_disclosures)}")
            
            for i, disclosure in enumerate(recent_disclosures[:3]):
                print(f"  {i+1}. {disclosure.get('corp_name', 'N/A')} - {disclosure.get('report_nm', 'N/A')}")
                
        except Exception as e:
            print(f"❌ 오류: {e}")
        print()
        
        # 2. 공시 검색 테스트
        print("2. 공시 검색 테스트")
        print("-" * 40)
        try:
            disclosure_result = await dart_client.get_disclosure_list(
                corp_cls="Y",
                page_count=5
            )
            
            if disclosure_result.get("success"):
                disclosures = disclosure_result.get("data", [])
                print(f"📊 검색된 공시 건수: {len(disclosures)}")
                
                for i, disclosure in enumerate(disclosures[:3]):
                    print(f"  {i+1}. {disclosure.get('corp_name', 'N/A')}")
                    print(f"     보고서: {disclosure.get('report_nm', 'N/A')}")
                    print(f"     날짜: {disclosure.get('rcept_dt', 'N/A')}")
                    print()
            else:
                print(f"❌ 공시 검색 실패: {disclosure_result.get('error')}")
                
        except Exception as e:
            print(f"❌ 오류: {e}")
        print()
        
        # 3. 기업 정보 조회 테스트
        print("3. 기업 정보 조회 테스트 (삼성전자)")
        print("-" * 40)
        try:
            company_info = await dart_client.get_company_info("00126380")  # 삼성전자
            
            if company_info.get("success"):
                data = company_info.get("data", {})
                print(f"🏢 회사명: {data.get('corp_name', 'N/A')}")
                print(f"📈 종목코드: {data.get('stock_code', 'N/A')}")
                print(f"👨‍💼 대표이사: {data.get('ceo_nm', 'N/A')}")
                print(f"🏠 주소: {data.get('adres', 'N/A')}")
                print(f"🌐 홈페이지: {data.get('hm_url', 'N/A')}")
            else:
                print(f"❌ 기업 정보 조회 실패: {company_info.get('error')}")
                
        except Exception as e:
            print(f"❌ 오류: {e}")
        print()
        
        # 4. 회사명 검색 테스트
        print("4. 회사명 검색 테스트 ('삼성')")
        print("-" * 40)
        try:
            search_results = await dart_client.search_company_by_name("삼성")
            
            print(f"🔍 검색된 회사 수: {len(search_results)}")
            
            for i, company in enumerate(search_results[:3]):
                print(f"  {i+1}. {company.get('corp_name', 'N/A')} ({company.get('stock_code', 'N/A')})")
                
        except Exception as e:
            print(f"❌ 오류: {e}")
        print()
        
        # 5. 향후 공시 이벤트 조회 테스트
        print("5. 향후 공시 이벤트 조회 테스트")
        print("-" * 40)
        try:
            from datetime import datetime, timedelta
            
            start_date = datetime.now().strftime("%Y-%m-%d")
            end_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
            
            events = await dart_client.get_upcoming_disclosure_events(
                start_date=start_date,
                end_date=end_date,
                corp_cls="Y"
            )
            
            print(f"📅 향후 30일간 공시 이벤트: {len(events)}건")
            
            for i, event in enumerate(events[:3]):
                print(f"  {i+1}. [{event.get('date', 'N/A')}] {event.get('title', 'N/A')}")
                print(f"     종목: {event.get('stockName', 'N/A')} ({event.get('stockCode', 'N/A')})")
                print()
                
        except Exception as e:
            print(f"❌ 오류: {e}")
    
    print("=" * 60)
    print("DART API 클라이언트 테스트 완료")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_dart_api())