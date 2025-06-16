#!/usr/bin/env python3
"""
파운데이션 모델 및 API 연결 상태 테스트 스크립트
"""

import os
import sys
from pathlib import Path
import asyncio
import requests
from dotenv import load_dotenv

# 프로젝트 루트 디렉토리 설정
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# .env 파일 로드
load_dotenv(PROJECT_ROOT / ".env")

def test_openai_api():
    """OpenAI API 키 테스트"""
    print("\n=== OpenAI API 테스트 ===")
    
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
        return False
    
    print(f"✅ OpenAI API 키: {api_key[:10]}...{api_key[-5:]}")
    
    try:
        import openai
        openai.api_key = api_key
        
        # 간단한 API 호출 테스트
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=10
        )
        
        print("✅ OpenAI API 연결 성공")
        print(f"   모델: gpt-3.5-turbo")
        print(f"   응답: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"❌ OpenAI API 연결 실패: {e}")
        return False

def test_bigkinds_api():
    """BigKinds API 키 테스트"""
    print("\n=== BigKinds API 테스트 ===")
    
    general_key = os.environ.get("BIGKINDS_KEY_GENERAL")
    seoul_key = os.environ.get("BIGKINDS_KEY_SEOUL")
    
    if not general_key and not seoul_key:
        print("❌ BigKinds API 키가 설정되지 않았습니다.")
        return False
    
    print(f"✅ 일반 API 키: {'설정됨' if general_key else '미설정'}")
    print(f"✅ 서울경제 API 키: {'설정됨' if seoul_key else '미설정'}")
    
    # BigKinds API 호출 테스트
    try:
        from backend.api.clients.bigkinds import BigKindsClient
        
        client = BigKindsClient()
        
        # 오늘의 이슈 API 테스트
        issues = client.get_today_issues(limit=3)
        
        if issues and len(issues) > 0:
            print("✅ BigKinds API 연결 성공")
            print(f"   오늘의 이슈 수: {len(issues)}개")
            print(f"   첫 번째 이슈: {issues[0].get('title', 'N/A')}")
            return True
        else:
            print("⚠️ BigKinds API 응답이 비어있습니다.")
            return False
            
    except Exception as e:
        print(f"❌ BigKinds API 연결 실패: {e}")
        return False

def test_other_apis():
    """기타 API 키 테스트"""
    print("\n=== 기타 API 테스트 ===")
    
    apis = {
        "한국투자증권 API": {
            "key": "KIS_APP_KEY",
            "secret": "KIS_APP_SECRET",
            "url": "KIS_BASE_URL"
        },
        "DART API": {
            "key": "DART_API_KEY"
        },
        "News API": {
            "key": "NEWS_API_KEY"
        }
    }
    
    results = {}
    
    for api_name, config in apis.items():
        key = os.environ.get(config["key"])
        if key:
            print(f"✅ {api_name}: 설정됨 ({key[:8]}...)")
            results[api_name] = True
        else:
            print(f"❌ {api_name}: 미설정")
            results[api_name] = False
    
    return results

def test_server_settings():
    """서버 설정 확인"""
    print("\n=== 서버 설정 확인 ===")
    
    settings = {
        "HOST": os.environ.get("HOST", "0.0.0.0"),
        "PORT": os.environ.get("PORT", "8000"),
        "LLM_MODEL": os.environ.get("LLM_MODEL", "gpt-4-turbo-preview"),
        "EMBEDDING_MODEL": os.environ.get("EMBEDDING_MODEL", "text-embedding-ada-002"),
        "LLM_TEMPERATURE": os.environ.get("LLM_TEMPERATURE", "0.3"),
    }
    
    for key, value in settings.items():
        print(f"✅ {key}: {value}")
    
    return True

def test_database_settings():
    """데이터베이스 설정 확인"""
    print("\n=== 데이터베이스 설정 확인 ===")
    
    vector_db_path = os.environ.get("VECTOR_DB_PATH", "./cache/vectordb")
    mongo_uri = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
    
    print(f"✅ Vector DB 경로: {vector_db_path}")
    print(f"✅ MongoDB URI: {mongo_uri}")
    
    # Vector DB 디렉토리 확인
    vector_path = Path(vector_db_path)
    if vector_path.exists():
        print(f"✅ Vector DB 디렉토리 존재: {vector_path.absolute()}")
    else:
        print(f"⚠️ Vector DB 디렉토리 없음: {vector_path.absolute()}")
        vector_path.mkdir(parents=True, exist_ok=True)
        print(f"✅ Vector DB 디렉토리 생성됨")
    
    return True

def test_model_imports():
    """모델 관련 라이브러리 import 테스트"""
    print("\n=== 모델 라이브러리 Import 테스트 ===")
    
    libraries = [
        ("openai", "OpenAI"),
        ("chromadb", "ChromaDB"),
        ("requests", "Requests"),
        ("fastapi", "FastAPI"),
        ("pydantic", "Pydantic")
    ]
    
    results = {}
    
    for lib_name, display_name in libraries:
        try:
            __import__(lib_name)
            print(f"✅ {display_name}: 정상 import")
            results[display_name] = True
        except ImportError as e:
            print(f"❌ {display_name}: import 실패 - {e}")
            results[display_name] = False
    
    return results

def main():
    """메인 테스트 실행"""
    print("="*60)
    print("파운데이션 모델 및 API 연결 상태 테스트")
    print("="*60)
    
    test_results = {}
    
    # 각 테스트 실행
    test_results["OpenAI API"] = test_openai_api()
    test_results["BigKinds API"] = test_bigkinds_api()
    test_results["기타 APIs"] = test_other_apis()
    test_results["서버 설정"] = test_server_settings()
    test_results["데이터베이스 설정"] = test_database_settings()
    test_results["라이브러리 Import"] = test_model_imports()
    
    # 결과 요약
    print("\n" + "="*60)
    print("테스트 결과 요약")
    print("="*60)
    
    total_tests = 0
    passed_tests = 0
    
    for test_name, result in test_results.items():
        if isinstance(result, dict):
            # 개별 API 결과들
            for sub_test, sub_result in result.items():
                total_tests += 1
                if sub_result:
                    passed_tests += 1
                    print(f"✅ {test_name} - {sub_test}")
                else:
                    print(f"❌ {test_name} - {sub_test}")
        else:
            total_tests += 1
            if result:
                passed_tests += 1
                print(f"✅ {test_name}")
            else:
                print(f"❌ {test_name}")
    
    print(f"\n총 {total_tests}개 테스트 중 {passed_tests}개 통과 ({passed_tests/total_tests*100:.1f}%)")
    
    # 추천 사항
    print("\n" + "="*60)
    print("추천 사항")
    print("="*60)
    
    if test_results.get("OpenAI API"):
        print("✅ AI 요약 기능이 정상적으로 작동할 것입니다.")
    else:
        print("⚠️ OpenAI API 키를 확인하고 다시 설정해주세요.")
    
    if test_results.get("BigKinds API"):
        print("✅ 뉴스 검색 및 데이터 수집이 정상적으로 작동할 것입니다.")
    else:
        print("⚠️ BigKinds API 키를 확인하고 다시 설정해주세요.")
    
    print("\n서버를 시작하려면:")
    print("cd backend && python server.py")

if __name__ == "__main__":
    main()