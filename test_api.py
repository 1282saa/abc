"""
간단한 Flask API 서버 테스트 스크립트 (FastAPI 대신)
"""

from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"message": "AI NOVA API 테스트 서버에 오신 것을 환영합니다", "version": "0.1.0"})

@app.route('/health')
def health_check():
    return jsonify({"status": "healthy", "service": "AI NOVA API 테스트"})

@app.route('/api/today-issues')
def get_today_issues():
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
            "date": "2025-05-21",
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
            "date": "2025-05-21",
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
    
    return jsonify({"issues": mock_issues, "count": len(mock_issues)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)