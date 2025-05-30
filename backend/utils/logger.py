"""
로깅 설정 모듈

프로젝트 전체에서 사용할 일관된 로깅 설정을 제공합니다.
"""

import logging
import os
from pathlib import Path
from typing import Optional

# 로그 디렉토리 설정
LOG_DIR = Path(__file__).parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

def setup_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """로거 설정
    
    Args:
        name: 로거 이름
        level: 로깅 레벨 (기본값: INFO)
        
    Returns:
        설정된 로거
    """
    if level is None:
        level = logging.INFO
        
    # 환경 변수로 로깅 레벨 오버라이드 가능
    env_level = os.environ.get("LOG_LEVEL", "").upper()
    if env_level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        level = getattr(logging, env_level)
    
    # 로거 생성
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 핸들러가 이미 존재하면 추가하지 않음
    if not logger.handlers:
        # 콘솔 핸들러
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        
        # 파일 핸들러
        log_file = LOG_DIR / f"{name.replace('.', '_')}.log"
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        
        # 포맷 설정
        formatter = logging.Formatter(
            "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        
        # 핸들러 추가
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
    
    return logger 