"""
AI NOVA 설정 파일
"""

# API 기본 설정
API_BASE_URL = "https://tools.kinds.or.kr"
API_VERSION = "1.0"

# API 엔드포인트
API_ENDPOINTS = {
    "news_search": "/search/news",
    "issue_ranking": "/issue_ranking",
    "word_cloud": "/word_cloud",
    "time_line": "/time_line",
    "quotation_search": "/search/quotation",
    "today_category_keyword": "/today_category_keyword",
    "feature": "/feature",
    "keyword": "/keyword",
    "topn_keyword": "/topn_keyword",
    "query_rank": "/query_rank",
}

# 데이터베이스 설정
DATABASE = {
    "host": "localhost",
    "port": 5432,
    "database": "ainova",
    "user": "ainova_user",
    "password": "",  # 실제 배포 시 환경 변수에서 로드
}

# 캐싱 설정
CACHE = {
    "type": "redis",
    "host": "localhost",
    "port": 6379,
    "ttl": 3600,  # 기본 캐시 유효 시간(초)
}

# 로깅 설정
LOGGING = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": "logs/ainova.log",
}

# 성능 설정
PERFORMANCE = {
    "max_workers": 10,  # 동시 API 요청 워커 수
    "request_timeout": 30,  # API 요청 타임아웃(초)
    "batch_size": 100,  # 배치 처리 크기
}

# 이슈 분석 설정
ISSUE_ANALYSIS = {
    "min_cluster_size": 5,  # 최소 클러스터 크기
    "max_clusters": 20,  # 최대 클러스터 수
    "similarity_threshold": 0.7,  # 유사도 임계값
}

# 인터페이스 설정
INTERFACE = {
    "default_page_size": 20,
    "max_page_size": 100,
}