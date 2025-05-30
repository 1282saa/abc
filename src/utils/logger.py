"""
로깅 유틸리티 모듈

애플리케이션 로깅을 위한 표준 로거 설정
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import json

# 프로젝트 루트 디렉토리 찾기
PROJECT_ROOT = Path(__file__).parent.parent.parent

import sys
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import LOGGING

def setup_logger(name: str = None) -> logging.Logger:
    """로거 설정
    
    Args:
        name: 로거 이름
        
    Returns:
        설정된 로거
    """
    # 로거 이름이 지정되지 않은 경우 기본 로거 사용
    if name is None:
        name = "ainova"
    
    # 로그 레벨 설정
    log_level_str = os.environ.get('LOG_LEVEL', LOGGING.get('level', 'INFO'))
    log_level = getattr(logging, log_level_str.upper(), logging.INFO)
    
    # 로그 포맷 설정
    log_format = LOGGING.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    formatter = logging.Formatter(log_format)
    
    # 로거 생성
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # 핸들러가 이미 설정되어 있으면 추가하지 않음
    if not logger.handlers:
        # 콘솔 핸들러 추가
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # 파일 핸들러 추가
        log_file = LOGGING.get('file', 'logs/ainova.log')
        log_path = PROJECT_ROOT / log_file
        
        # 로그 디렉토리 생성
        log_dir = log_path.parent
        log_dir.mkdir(exist_ok=True)
        
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

class APILogger:
    """API 요청 및 응답 로깅 클래스"""
    
    def __init__(self, logger_name: str = "ainova.api"):
        """API 로거 초기화
        
        Args:
            logger_name: 로거 이름
        """
        self.logger = setup_logger(logger_name)
        self.log_dir = PROJECT_ROOT / "logs" / "api"
        self.log_dir.mkdir(exist_ok=True, parents=True)
    
    def log_request(self, endpoint: str, params: dict) -> None:
        """API 요청 로깅
        
        Args:
            endpoint: API 엔드포인트
            params: 요청 파라미터
        """
        # 기본 로그 메시지
        self.logger.info(f"API 요청: {endpoint}")
        
        # 상세 로그를 파일에 저장
        try:
            log_entry = {
                "type": "request",
                "endpoint": endpoint,
                "params": params
            }
            
            # 파라미터에서 API 키 제거
            if 'access_key' in log_entry['params']:
                log_entry['params']['access_key'] = '***'
            
            log_path = self.log_dir / f"api_log_{endpoint.replace('/', '_')}.log"
            
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            self.logger.error(f"API 요청 로깅 실패: {e}")
    
    def log_response(self, endpoint: str, response: dict, elapsed_time: float) -> None:
        """API 응답 로깅
        
        Args:
            endpoint: API 엔드포인트
            response: API 응답
            elapsed_time: 요청 처리 시간(초)
        """
        # 기본 로그 메시지
        status = "성공" if response.get("result") == "success" else "실패"
        self.logger.info(f"API 응답: {endpoint} - {status} ({elapsed_time:.2f}초)")
        
        # 상세 로그를 파일에 저장
        try:
            log_entry = {
                "type": "response",
                "endpoint": endpoint,
                "status": status,
                "elapsed_time": elapsed_time
            }
            
            # 오류가 있는 경우 기록
            if status == "실패":
                log_entry["error"] = response.get("error", {})
            
            log_path = self.log_dir / f"api_log_{endpoint.replace('/', '_')}.log"
            
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            self.logger.error(f"API 응답 로깅 실패: {e}")
    
    def log_error(self, endpoint: str, error: Exception) -> None:
        """API 오류 로깅
        
        Args:
            endpoint: API 엔드포인트
            error: 발생한 예외
        """
        # 기본 로그 메시지
        self.logger.error(f"API 오류: {endpoint} - {str(error)}")
        
        # 상세 로그를 파일에 저장
        try:
            log_entry = {
                "type": "error",
                "endpoint": endpoint,
                "error": str(error)
            }
            
            log_path = self.log_dir / f"api_error.log"
            
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            self.logger.error(f"API 오류 로깅 실패: {e}")