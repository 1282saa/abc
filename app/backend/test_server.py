"""
간단한 API 서버 테스트 스크립트
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Any, Optional
import uvicorn

# FastAPI 앱 생성
app = FastAPI(
    title="AI NOVA API 테스트",
    description="AI NOVA API 테스트 서버",
    version="0.1.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 루트 경로
@app.get("/")
async def root():
    return {"message": "AI NOVA API 테스트 서버에 오신 것을 환영합니다", "version": "0.1.0"}

# 서버 상태 확인
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "AI NOVA API 테스트"}

# 오늘의 이슈 API (목업 데이터)
@app.get("/api/today-issues")
async def get_today_issues(
    date: Optional[str] = None,
    top_n: int = 5
):
    """오늘의 주요 이슈 조회 (목업 데이터)"""
    
    # 목업 데이터
    mock_issues = [
        {
            "issue_id": "issue_1",
            "rank": 1,
            "topic": "윤석열 정부 개각 발표",
            "category": "정치",
            "keywords": ["윤석열", "개각", "내각", "인사"],
            "news_count": 56,
            "provider_count": 12,
            "date": date or "2025-05-21",
            "related_news": [
                {
                    "news_id": "news_1",
                    "title": "윤석열 대통령, 교육·법무·국방 등 7개 부처 개각 단행",
                    "provider": "서울경제",
                    "published_at": "2025-05-21T09:30:00Z"
                }
            ]
        },
        {
            "issue_id": "issue_2",
            "rank": 2,
            "topic": "물가상승률 3개월 연속 하락",
            "category": "경제",
            "keywords": ["물가", "인플레이션", "금리", "소비"],
            "news_count": 43,
            "provider_count": 10,
            "date": date or "2025-05-21",
            "related_news": [
                {
                    "news_id": "news_2",
                    "title": "5월 소비자물가 상승률 2.1%... 3개월 연속 하락세",
                    "provider": "서울경제",
                    "published_at": "2025-05-21T08:45:00Z"
                }
            ]
        }
    ]
    
    return {"issues": mock_issues[:top_n], "count": len(mock_issues[:top_n])}

# 앱 실행
if __name__ == "__main__":
    uvicorn.run(
        "test_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )