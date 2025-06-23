"""
BigKinds API 관련 상수 정의
"""

# API 설정
API_BASE_URL = "https://tools.kinds.or.kr/"
API_ENDPOINTS = {
    "news_search": "search/news",
    "issue_ranking": "issue_ranking", 
    "query_rank": "query_rank",
    "word_cloud": "word_cloud",
    "time_line": "time_line",
    "quotation_search": "search/quotation",
    "today_category_keyword": "today_category_keyword",
    "feature": "feature",
    "keyword": "keyword",
    "word_related": "word/related",
    "word_topn": "word/topn"
}

# 서울경제신문 관련 설정
SEOUL_ECONOMIC = {
    "name": "서울경제",
    "code": "02100311"
}

# 기본 필드 설정
DEFAULT_NEWS_FIELDS = [
    "news_id",
    "title", 
    "content",
    "published_at",
    "dateline",
    "category",
    "images",
    "provider_link_page",
    "provider_code",
    "provider_name",
    "byline",
    "hilight",
    "enveloped_at",
    "url"
] 