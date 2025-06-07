#!/usr/bin/env python3
"""
US Stock API Client 테스트 스크립트

이 스크립트는 새로 생성된 US Stock API Client의 기능을 테스트합니다.
"""

import asyncio
import sys
from pathlib import Path
from datetime import date, timedelta

# 프로젝트 루트 디렉토리 추가
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.services.us_stock_api_client import us_stock_api_client

async def test_us_stock_api():
    """US Stock API Client 테스트"""
    print("=" * 60)
    print("US Stock API Client 테스트 시작")
    print("=" * 60)
    
    try:
        async with us_stock_api_client as client:
            # 1. 단일 주식 현재가 조회 테스트
            print("\n1. 단일 주식 현재가 조회 테스트")
            print("-" * 40)
            
            aapl_quote = await client.get_stock_quote("AAPL")
            print(f"AAPL 현재가: ${aapl_quote['price']:.2f}")
            print(f"변동률: {aapl_quote['change_percent']}%")
            print(f"데이터 소스: {aapl_quote['source']}")
            
            # 2. 여러 주식 동시 조회 테스트
            print("\n2. 여러 주식 동시 조회 테스트")
            print("-" * 40)
            
            symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]
            quotes = await client.get_multiple_quotes(symbols)
            
            for symbol, quote in quotes.items():
                print(f"{symbol}: ${quote['price']:.2f} ({quote['change_percent']}%)")
            
            # 3. 실적 캘린더 테스트
            print("\n3. 실적 캘린더 테스트")
            print("-" * 40)
            
            start_date = date.today()
            end_date = start_date + timedelta(days=30)
            
            earnings = await client.get_earnings_calendar(start_date, end_date)
            print(f"향후 30일간 실적 발표 예정: {len(earnings)}건")
            
            for i, event in enumerate(earnings[:5]):  # 처음 5개만 출력
                print(f"  {i+1}. {event['company_name']} - {event['report_date']} ({event['fiscal_period']})")
            
            # 4. 배당 캘린더 테스트
            print("\n4. 배당 캘린더 테스트")
            print("-" * 40)
            
            dividends = await client.get_dividend_calendar(start_date, end_date)
            print(f"향후 30일간 배당 예정: {len(dividends)}건")
            
            for i, event in enumerate(dividends[:5]):  # 처음 5개만 출력
                print(f"  {i+1}. {event['company_name']} - {event['ex_dividend_date']} (${event['dividend_amount']})")
            
            # 5. 경제 지표 캘린더 테스트
            print("\n5. 경제 지표 캘린더 테스트")
            print("-" * 40)
            
            economic_events = await client.get_economic_calendar(start_date, end_date)
            print(f"향후 30일간 경제 지표 발표: {len(economic_events)}건")
            
            for i, event in enumerate(economic_events[:5]):  # 처음 5개만 출력
                print(f"  {i+1}. {event['event']} - {event['date']} (중요도: {event['importance']})")
            
            # 6. 시장 상태 테스트
            print("\n6. 시장 상태 테스트")
            print("-" * 40)
            
            market_status = await client.get_market_status()
            print(f"미국 시장 상태: {'개장' if market_status['is_open'] else '폐장'}")
            print(f"타임존: {market_status['timezone']}")
            
            print("\n" + "=" * 60)
            print("✅ 모든 테스트가 성공적으로 완료되었습니다!")
            print("US Stock API Client가 정상적으로 작동합니다.")
            print("=" * 60)
            
    except Exception as e:
        print(f"\n❌ 테스트 중 오류 발생: {str(e)}")
        print("=" * 60)
        raise

async def test_api_integration():
    """API 통합 테스트"""
    print("\n📊 API 통합 테스트")
    print("-" * 40)
    
    try:
        async with us_stock_api_client as client:
            # 주요 종목들의 현재가를 조회하여 캘린더 이벤트 생성 시뮬레이션
            major_stocks = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
            quotes = await client.get_multiple_quotes(major_stocks)
            
            print("주요 종목 현재가 (캘린더 이벤트 생성용):")
            for symbol, quote in quotes.items():
                change_percent = float(quote.get('change_percent', '0'))
                status = "📈" if change_percent > 0 else "📉" if change_percent < 0 else "➡️"
                
                print(f"  {status} {symbol}: ${quote['price']:.2f} ({quote['change_percent']}%)")
                
                # 큰 변동이 있는 경우 알림 이벤트 생성 시뮬레이션
                if abs(change_percent) >= 3.0:
                    print(f"    🚨 주의: {symbol} 3% 이상 변동 - 캘린더 이벤트 생성 필요")
            
            # 실적 캘린더와 배당 캘린더를 결합한 투자 캘린더 시뮬레이션
            today = date.today()
            week_later = today + timedelta(days=7)
            
            earnings = await client.get_earnings_calendar(today, week_later)
            dividends = await client.get_dividend_calendar(today, week_later)
            
            print(f"\n향후 7일 투자 캘린더 요약:")
            print(f"  📊 실적 발표: {len(earnings)}건")
            print(f"  💰 배당 지급: {len(dividends)}건")
            
            # 통합 이벤트 카운트
            total_events = len(earnings) + len(dividends)
            print(f"  📅 총 이벤트: {total_events}건")
            
            if total_events > 0:
                print("  ✅ 투자 캘린더 데이터 준비 완료")
            else:
                print("  ℹ️  이번 주는 예정된 이벤트가 없습니다")
                
    except Exception as e:
        print(f"❌ 통합 테스트 실패: {str(e)}")
        raise

if __name__ == "__main__":
    print("🚀 US Stock API Client 테스트 시작...")
    
    try:
        # 기본 기능 테스트
        asyncio.run(test_us_stock_api())
        
        # API 통합 테스트
        asyncio.run(test_api_integration())
        
        print("\n🎉 모든 테스트가 성공적으로 완료되었습니다!")
        print("\n📋 다음 단계:")
        print("1. 실제 Alpha Vantage API 키 설정 (ALPHA_VANTAGE_API_KEY)")
        print("2. 프론트엔드에서 새로운 API 엔드포인트 연동")
        print("3. 캘린더 UI에 미국 주식 이벤트 표시")
        
    except Exception as e:
        print(f"\n💥 테스트 실패: {str(e)}")
        sys.exit(1)