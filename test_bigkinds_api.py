#!/usr/bin/env python3
"""
BigKinds API 연결 테스트 스크립트

API 키와 연결이 정상적으로 작동하는지 확인합니다.
"""

import os
import sys
import json
import requests
from pathlib import Path
from datetime import datetime, timedelta

# 프로젝트 루트 디렉토리 추가
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# 환경 변수 로드
from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / "config" / ".env")

from backend.api.clients.bigkinds_client import BigKindsClient

def test_direct_api_endpoints():
    """직접 API 엔드포인트 테스트"""
    api_key = os.environ.get('BIGKINDS_API_KEY')
    print(f"🔍 직접 API 엔드포인트 테스트 시작...")
    print(f"API 키: {api_key[:10]}...")
    
    # 다양한 도메인과 엔드포인트 시도
    base_urls = [
        "https://tools.kinds.or.kr/api/",
        "https://kinds.or.kr/api/",
        "https://bigkinds.or.kr/api/",
        "https://www.kinds.or.kr/api/",
        "https://www.bigkinds.or.kr/api/",
        "https://api.kinds.or.kr/",
        "https://api.bigkinds.or.kr/"
    ]
    
    endpoints = ["news/search", "search/news", "newsSearch"]
    
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    
    test_payload = {
        "access_key": api_key,
        "query": "삼성전자",
        "published_at": {
            "from": start_date,
            "until": end_date
        },
        "return_from": 0,
        "return_size": 5
    }
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    
    for base_url in base_urls:
        for endpoint in endpoints:
            url = f"{base_url}{endpoint}"
            print(f"\n🌐 시도 중: {url}")
            
            try:
                response = requests.post(url, json=test_payload, headers=headers, timeout=10)
                print(f"  상태 코드: {response.status_code}")
                
                if response.status_code == 200:
                    try:
                        result = response.json()
                        print(f"  ✅ 성공! 응답: {json.dumps(result, ensure_ascii=False, indent=2)[:200]}...")
                        return True, url
                    except json.JSONDecodeError:
                        print(f"  ⚠️  JSON 파싱 실패: {response.text[:100]}...")
                elif response.status_code == 404:
                    print(f"  ❌ 404 - 엔드포인트를 찾을 수 없음")
                elif response.status_code == 401:
                    print(f"  🔐 401 - 인증 오류 (API 키 문제일 수 있음)")
                elif response.status_code == 403:
                    print(f"  🚫 403 - 접근 거부")
                else:
                    print(f"  ⚠️  기타 오류: {response.text[:100]}...")
                    
            except requests.exceptions.Timeout:
                print(f"  ⏰ 타임아웃")
            except requests.exceptions.ConnectionError:
                print(f"  🚫 연결 오류")
            except Exception as e:
                print(f"  ❌ 예외: {e}")
    
    return False, None

def test_api_connection():
    """API 연결 테스트"""
    print("🔍 BigKinds API 연결 테스트 시작...")
    
    # 먼저 직접 엔드포인트 테스트
    success, working_url = test_direct_api_endpoints()
    
    if success:
        print(f"\n🎉 작동하는 엔드포인트 발견: {working_url}")
        return True
    
    # 기존 클라이언트로도 시도
    try:
        print(f"\n📦 기존 클라이언트로 테스트...")
        client = BigKindsClient()
        print("✅ 클라이언트 생성 성공")
        
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        result = client.news_search_advanced(
            query="삼성전자",
            start_date=start_date,
            end_date=end_date,
            size=5,
            use_seoul_economic=False
        )
        
        if result.get("result") == "success":
            print(f"✅ 기존 클라이언트 검색 성공!")
            return True
        else:
            print(f"❌ 기존 클라이언트 검색 실패: {result}")
            return False
            
    except Exception as e:
        print(f"❌ API 연결 오류: {e}")
        return False

def test_seoul_economic_only():
    """서울경제신문만 검색 테스트"""
    print("\n🏢 서울경제신문 전용 검색 테스트...")
    
    try:
        client = BigKindsClient()
        
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        print(f"📅 검색 기간: {start_date} ~ {end_date}")
        print("🔍 '경제' 키워드로 서울경제신문만 검색 중...")
        
        result = client.news_search_advanced(
            query="경제",
            start_date=start_date,
            end_date=end_date,
            size=10,
            use_seoul_economic=True  # 서울경제신문만
        )
        
        if result.get("result") == "success":
            return_obj = result.get("return_object", {})
            documents = return_obj.get("documents", [])
            total_count = return_obj.get("total_count", 0)
            
            print(f"✅ 서울경제신문 검색 성공!")
            print(f"📰 전체 기사 수: {total_count}")
            print(f"📄 가져온 기사 수: {len(documents)}")
            
            if documents:
                print(f"📋 기사 목록 (최대 5개):")
                for i, doc in enumerate(documents[:5]):
                    print(f"  {i+1}. {doc.get('TITLE', '제목 없음')[:40]}...")
                    print(f"     언론사: {doc.get('PROVIDER_NAME', '알 수 없음')}")
                    print(f"     날짜: {doc.get('PUBLISHED_AT', '날짜 없음')}")
                    print()
                    
            return True
        else:
            print(f"❌ 서울경제신문 검색 실패: {result}")
            return False
            
    except Exception as e:
        print(f"❌ 서울경제신문 검색 오류: {e}")
        return False

def test_timeline():
    """타임라인 API 테스트"""
    print("\n📈 타임라인 API 테스트...")
    
    try:
        client = BigKindsClient()
        
        timeline_data = client.get_news_timeline(
            query="삼성전자",
            start_date="2024-05-01",
            end_date="2024-05-30",
            interval="day"
        )
        
        print(f"📊 타임라인 데이터: {len(timeline_data)}개 포인트")
        
        if timeline_data:
            print("📋 샘플 데이터 (최대 5개):")
            for date, count in timeline_data[:5]:
                print(f"  {date}: {count}건")
            return True
        else:
            print("❌ 타임라인 데이터 없음")
            return False
            
    except Exception as e:
        print(f"❌ 타임라인 테스트 오류: {e}")
        return False

if __name__ == "__main__":
    print("🚀 BigKinds API 종합 테스트 시작\n")
    
    # 기본 연결 테스트
    success1 = test_api_connection()
    
    # 서울경제신문 전용 테스트
    success2 = test_seoul_economic_only()
    
    # 타임라인 테스트
    success3 = test_timeline()
    
    print("\n📋 테스트 결과 요약:")
    print(f"  기본 API 연결: {'✅ 성공' if success1 else '❌ 실패'}")
    print(f"  서울경제신문 검색: {'✅ 성공' if success2 else '❌ 실패'}")
    print(f"  타임라인 기능: {'✅ 성공' if success3 else '❌ 실패'}")
    
    if all([success1, success2, success3]):
        print("\n🎉 모든 테스트 통과! API가 정상적으로 작동합니다.")
    else:
        print("\n⚠️  일부 테스트 실패. API 설정을 확인해주세요.")