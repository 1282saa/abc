"""
전역 설정 모듈

환경 변수 및 기본 설정을 관리합니다.
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Any, List, Optional

# 프로젝트 루트 디렉토리 찾기
PROJECT_ROOT = Path(__file__).parent.parent
ENV_FILE = PROJECT_ROOT / "config" / ".env"

# 환경 변수 로드
load_dotenv(dotenv_path=ENV_FILE)

# API 설정
API_BASE_URL = "https://tools.kinds.or.kr/api/"
API_ENDPOINTS = {
    "news_search": "news/search",
    "issue_ranking": "issue/ranking",
    "word_cloud": "word/cloud",
    "time_line": "time/line",
    "quotation_search": "quotation/search",
    "today_category_keyword": "today/category/keyword",
    "feature": "feature",
    "keyword": "keyword",
    "topn_keyword": "topn/keyword",
    "query_rank": "query/rank"
}

# 서버 설정
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", 8000))
DEBUG = os.environ.get("DEBUG", "False").lower() in ("true", "1", "t")

# 벡터 데이터베이스 설정
VECTOR_DB_PATH = os.environ.get("VECTOR_DB_PATH", os.path.join(PROJECT_ROOT, "cache", "vectordb"))

# 모델 설정
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "text-embedding-ada-002")
LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-4-turbo-preview")
LLM_TEMPERATURE = float(os.environ.get("LLM_TEMPERATURE", "0.3"))

# 성능 설정
PERFORMANCE = {
    "request_timeout": int(os.environ.get("REQUEST_TIMEOUT", 30)),
    "cache_ttl": int(os.environ.get("CACHE_TTL", 3600)),
    "max_retries": int(os.environ.get("MAX_RETRIES", 3)),
    "backoff_factor": 2.0
}

# 카테고리 코드
CATEGORIES = {
    "정치": "정치",
    "경제": "경제",
    "사회": "사회",
    "생활/문화": "생활문화",
    "IT/과학": "IT_과학",
    "국제": "국제",
    "스포츠": "스포츠",
}

# 서울경제신문 언론사 코드
SEOUL_ECONOMIC_DAILY_CODE = "02100311"

# 파일 경로
CACHE_DIR = PROJECT_ROOT / "cache"
OUTPUT_DIR = PROJECT_ROOT / "output"
LOGS_DIR = PROJECT_ROOT / "logs"

# 디렉토리 생성
CACHE_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)