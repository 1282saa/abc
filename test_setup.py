"""
프로젝트 설정 테스트 스크립트

리팩토링된 프로젝트 구조가 올바르게 설정되었는지 확인합니다.
"""

import os
import sys
from pathlib import Path

def check_directory(path):
    """디렉토리 존재 확인
    
    Args:
        path: 확인할 디렉토리 경로
    
    Returns:
        존재하면 True, 아니면 False
    """
    return os.path.exists(path) and os.path.isdir(path)

def check_file(path):
    """파일 존재 확인
    
    Args:
        path: 확인할 파일 경로
    
    Returns:
        존재하면 True, 아니면 False
    """
    return os.path.exists(path) and os.path.isfile(path)

def run_test():
    """프로젝트 구조 테스트 실행"""
    errors = []
    
    # 1. 필수 디렉토리 확인
    directories = [
        "backend",
        "backend/api",
        "backend/api/clients",
        "backend/api/routes",
        "backend/services",
        "backend/services/qa",
        "backend/services/news",
        "backend/services/content",
        "backend/utils",
        "config",
        "logs",
        "cache",
        "output"
    ]
    
    print("\n===== 디렉토리 확인 =====")
    for dir_path in directories:
        if check_directory(dir_path):
            print(f"✅ {dir_path} - 확인")
        else:
            print(f"❌ {dir_path} - 없음")
            errors.append(f"디렉토리가 없음: {dir_path}")
    
    # 2. 필수 파일 확인
    files = [
        "README.md",
        "requirements.txt",
        "config/settings.py",
        "config/.env.example",
        "backend/__init__.py",
        "backend/server.py",
        "backend/api/__init__.py",
        "backend/api/clients/__init__.py",
        "backend/api/routes/__init__.py",
        "backend/api/clients/bigkinds_client.py",
        "backend/api/routes/qa_routes.py",
        "backend/services/__init__.py",
        "backend/services/qa/__init__.py",
        "backend/services/news/__init__.py",
        "backend/services/content/__init__.py",
        "backend/services/qa/vector_db.py",
        "backend/services/qa/engine.py",
        "backend/utils/__init__.py",
        "backend/utils/logger.py"
    ]
    
    print("\n===== 파일 확인 =====")
    for file_path in files:
        if check_file(file_path):
            print(f"✅ {file_path} - 확인")
        else:
            print(f"❌ {file_path} - 없음")
            errors.append(f"파일이 없음: {file_path}")
    
    # 3. 모듈 임포트 테스트
    print("\n===== 모듈 임포트 테스트 =====")
    try:
        sys.path.insert(0, os.path.abspath('.'))
        
        # 주요 모듈 임포트 시도
        try:
            from backend.utils.logger import setup_logger
            print("✅ 로거 모듈 임포트 성공")
        except ImportError as e:
            print(f"❌ 로거 모듈 임포트 실패: {e}")
            errors.append(f"모듈 임포트 오류 (logger): {e}")
        
        try:
            from backend.api.clients.bigkinds_client import BigKindsClient
            print("✅ 빅카인즈 클라이언트 모듈 임포트 성공")
        except ImportError as e:
            print(f"❌ 빅카인즈 클라이언트 모듈 임포트 실패: {e}")
            errors.append(f"모듈 임포트 오류 (bigkinds_client): {e}")
        
        try:
            from backend.services.qa.vector_db import VectorDB
            print("✅ 벡터 DB 모듈 임포트 성공")
        except ImportError as e:
            print(f"❌ 벡터 DB 모듈 임포트 실패: {e}")
            errors.append(f"모듈 임포트 오류 (vector_db): {e}")
        
    except Exception as e:
        print(f"❌ 모듈 테스트 중 오류 발생: {e}")
        errors.append(f"모듈 테스트 오류: {e}")
    
    # 4. 결과 출력
    print("\n===== 테스트 결과 =====")
    if errors:
        print(f"❌ 테스트 실패: {len(errors)}개 오류 발견")
        for i, error in enumerate(errors, 1):
            print(f"  {i}. {error}")
        print("\n수정이 필요한 부분이 있습니다.")
    else:
        print("✅ 모든 테스트 통과! 프로젝트 구조가 올바르게 설정되었습니다.")

if __name__ == "__main__":
    run_test() 