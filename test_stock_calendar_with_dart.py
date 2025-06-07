#!/usr/bin/env python3
"""
주식 캘린더 + DART 통합 테스트 스크립트

주식 캘린더 API가 DART API와 통합되어 실제 공시 데이터를 제공하는지 테스트합니다.
"""

import os
import sys
import asyncio
import aiohttp
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

# 프로젝트 루트 추가
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# 환경변수 로드
load_dotenv(PROJECT_ROOT / ".env")

async def test_stock_calendar_api():
    """주식 캘린더 API 테스트"""
    print("=" * 60)
    print("주식 캘린더 + DART 통합 API 테스트")
    print("=" * 60)
    
    base_url = "http://localhost:8000/api/stock-calendar"
    
    # 테스트할 날짜 범위
    start_date = datetime.now().strftime("%Y-%m-%d")
    end_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    
    print(f"테스트 날짜 범위: {start_date} ~ {end_date}")
    print()
    
    async with aiohttp.ClientSession() as session:
        
        # 1. 이벤트 유형 목록 조회
        print("1. 이벤트 유형 목록 조회")
        print("-" * 40)
        try:
            async with session.get(f"{base_url}/event-types") as response:
                if response.status == 200:
                    data = await response.json()
                    event_types = data.get("eventTypes", [])
                    print(f"📊 지원되는 이벤트 유형: {len(event_types)}개")
                    for event_type in event_types:
                        print(f"  - {event_type['name']} ({event_type['code']})")
                else:
                    print(f"❌ API 오류: {response.status}")
        except Exception as e:
            print(f"❌ 연결 오류: {e}")
        print()
        
        # 2. 전체 캘린더 이벤트 조회 (DART 포함)
        print("2. 전체 캘린더 이벤트 조회 (DART 포함)")
        print("-" * 40)
        try:
            params = {
                "start_date": start_date,
                "end_date": end_date,
                "include_disclosures": "true",
                "include_earnings": "true"
            }
            
            async with session.get(f"{base_url}/events", params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    events = data.get("events", [])
                    meta = data.get("meta", {})
                    
                    print(f"📅 전체 이벤트: {meta.get('total_events', 0)}건")
                    
                    # 이벤트 유형별 집계
                    event_type_counts = {}
                    for event in events:
                        event_type = event.get("eventType", "unknown")
                        event_type_counts[event_type] = event_type_counts.get(event_type, 0) + 1
                    
                    for event_type, count in event_type_counts.items():
                        print(f"  - {event_type}: {count}건")
                    
                    print("\n주요 이벤트:")
                    for event in events[:5]:
                        print(f"  📌 [{event.get('date')}] {event.get('title')}")
                        print(f"     종목: {event.get('stockName', 'N/A')} ({event.get('stockCode', 'N/A')})")
                        print(f"     유형: {event.get('eventType', 'N/A')}")
                        if event.get('disclosure_url'):
                            print(f"     링크: {event['disclosure_url']}")
                        print()
                else:
                    print(f"❌ API 오류: {response.status}")
                    error_text = await response.text()
                    print(f"   상세: {error_text}")
        except Exception as e:
            print(f"❌ 연결 오류: {e}")
        print()
        
        # 3. DART 공시만 조회
        print("3. DART 공시만 조회")
        print("-" * 40)
        try:
            params = {
                "start_date": start_date,
                "end_date": end_date,
                "corp_cls": "Y",
                "important_only": "true"
            }
            
            async with session.get(f"{base_url}/dart/disclosures", params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    disclosures = data.get("disclosures", [])
                    meta = data.get("meta", {})
                    
                    print(f"🏢 DART 공시: {meta.get('total_count', 0)}건")
                    print(f"   법인구분: {meta.get('corp_cls', 'N/A')}")
                    print(f"   중요공시만: {meta.get('important_only', 'N/A')}")
                    
                    for disclosure in disclosures[:3]:
                        print(f"\n  📋 {disclosure.get('title', 'N/A')}")
                        print(f"     회사: {disclosure.get('stockName', 'N/A')}")
                        print(f"     날짜: {disclosure.get('date', 'N/A')}")
                        if disclosure.get('disclosure_url'):
                            print(f"     링크: {disclosure['disclosure_url']}")
                else:
                    print(f"❌ API 오류: {response.status}")
                    error_text = await response.text()
                    print(f"   상세: {error_text}")
        except Exception as e:
            print(f"❌ 연결 오류: {e}")
        print()
        
        # 4. 최근 DART 공시 조회
        print("4. 최근 DART 공시 조회")
        print("-" * 40)
        try:
            params = {
                "corp_cls": "Y",
                "days": "7",
                "important_only": "true"
            }
            
            async with session.get(f"{base_url}/dart/recent", params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    events = data.get("events", [])
                    meta = data.get("meta", {})
                    
                    print(f"🕒 최근 7일간 중요 공시: {meta.get('total_count', 0)}건")
                    
                    for event in events[:3]:
                        print(f"\n  📈 {event.get('title', 'N/A')}")
                        print(f"     회사: {event.get('stockName', 'N/A')} ({event.get('stockCode', 'N/A')})")
                        print(f"     날짜: {event.get('date', 'N/A')}")
                else:
                    print(f"❌ API 오류: {response.status}")
                    error_text = await response.text()
                    print(f"   상세: {error_text}")
        except Exception as e:
            print(f"❌ 연결 오류: {e}")
        print()
        
        # 5. DART 기업 검색
        print("5. DART 기업 검색")
        print("-" * 40)
        try:
            params = {"company_name": "삼성"}
            
            async with session.get(f"{base_url}/dart/search/company", params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    companies = data.get("companies", [])
                    meta = data.get("meta", {})
                    
                    print(f"🔍 '{meta.get('search_term')}'로 검색된 회사: {meta.get('total_count', 0)}개")
                    
                    for company in companies[:3]:
                        print(f"  🏢 {company.get('corp_name', 'N/A')} ({company.get('stock_code', 'N/A')})")
                        print(f"     고유번호: {company.get('corp_code', 'N/A')}")
                        print(f"     법인구분: {company.get('corp_cls', 'N/A')}")
                else:
                    print(f"❌ API 오류: {response.status}")
                    error_text = await response.text()
                    print(f"   상세: {error_text}")
        except Exception as e:
            print(f"❌ 연결 오류: {e}")

async def main():
    """메인 실행 함수"""
    # 서버가 실행 중인지 확인
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8000/api/docs") as response:
                if response.status == 200:
                    print("✅ 서버가 실행 중입니다.")
                    await test_stock_calendar_api()
                else:
                    print("❌ 서버에 연결할 수 없습니다.")
    except Exception as e:
        print("❌ 서버가 실행 중이 아닙니다.")
        print("다음 명령어로 서버를 먼저 실행해주세요:")
        print("cd /Users/yeong-gwang/Desktop/work/서울경제신문/빅카인즈/big_proto && python -m backend.server")
        print(f"\n오류 상세: {e}")

if __name__ == "__main__":
    asyncio.run(main())