"""
빅카인즈 API 클라이언트 테스트
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import json

# 프로젝트 루트 디렉토리 찾기
from pathlib import Path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.api.bigkinds_client import BigKindsClient

class TestBigKindsClient(unittest.TestCase):
    """빅카인즈 API 클라이언트 테스트 클래스"""

    def setUp(self):
        """테스트 설정"""
        self.test_api_key = "test_api_key"
        self.client = BigKindsClient(api_key=self.test_api_key)
    
    @patch('src.api.bigkinds_client.requests.post')
    def test_news_search(self, mock_post):
        """뉴스 검색 API 테스트"""
        # Mock 응답 설정
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": "success",
            "return_object": {
                "total_count": 2,
                "documents": [
                    {
                        "news_id": "test_id_1",
                        "title": "테스트 제목 1",
                        "content": "테스트 내용 1",
                        "published_at": "2025-05-01T12:00:00Z",
                        "provider": "서울경제"
                    },
                    {
                        "news_id": "test_id_2",
                        "title": "테스트 제목 2",
                        "content": "테스트 내용 2",
                        "published_at": "2025-05-02T12:00:00Z",
                        "provider": "서울경제"
                    }
                ]
            }
        }
        mock_post.return_value = mock_response
        
        # API 호출
        result = self.client.news_search(
            query="테스트",
            start_date="2025-05-01",
            end_date="2025-05-10",
            size=10,
            page=1
        )
        
        # 검증
        self.assertEqual(result["result"], "success")
        self.assertEqual(len(result["return_object"]["documents"]), 2)
        self.assertEqual(result["return_object"]["documents"][0]["title"], "테스트 제목 1")
        
        # 요청 파라미터 검증
        called_args, _ = mock_post.call_args
        self.assertEqual(called_args[0], "https://tools.kinds.or.kr/search/news")
    
    @patch('src.api.bigkinds_client.requests.post')
    def test_issue_ranking(self, mock_post):
        """오늘의 이슈 API 테스트"""
        # Mock 응답 설정
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": "success",
            "return_object": {
                "issues": [
                    {
                        "id": "issue_1",
                        "rank": 1,
                        "topic": "테스트 이슈 1",
                        "category": "정치",
                        "keywords": ["테스트", "이슈", "키워드"],
                        "news_count": 10,
                        "provider_count": 5,
                        "news": [
                            {
                                "news_id": "news_1",
                                "title": "테스트 뉴스 1",
                                "provider": "서울경제",
                                "published_at": "2025-05-01T12:00:00Z"
                            }
                        ]
                    }
                ]
            }
        }
        mock_post.return_value = mock_response
        
        # API 호출
        result = self.client.issue_ranking(
            date="2025-05-01"
        )
        
        # 검증
        self.assertEqual(result["result"], "success")
        self.assertEqual(len(result["return_object"]["issues"]), 1)
        self.assertEqual(result["return_object"]["issues"][0]["topic"], "테스트 이슈 1")
        
        # 요청 파라미터 검증
        called_args, _ = mock_post.call_args
        self.assertEqual(called_args[0], "https://tools.kinds.or.kr/issue_ranking")
    
    @patch('src.api.bigkinds_client.requests.post')
    def test_word_cloud(self, mock_post):
        """연관어 분석 API 테스트"""
        # Mock 응답 설정
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": "success",
            "return_object": [
                {"keyword": "테스트1", "weight": 10},
                {"keyword": "테스트2", "weight": 8},
                {"keyword": "테스트3", "weight": 6}
            ]
        }
        mock_post.return_value = mock_response
        
        # API 호출
        result = self.client.word_cloud(
            query="테스트",
            start_date="2025-05-01",
            end_date="2025-05-10",
            display_count=20
        )
        
        # 검증
        self.assertEqual(result["result"], "success")
        self.assertEqual(len(result["return_object"]), 3)
        self.assertEqual(result["return_object"][0]["keyword"], "테스트1")
        
        # 요청 파라미터 검증
        called_args, _ = mock_post.call_args
        self.assertEqual(called_args[0], "https://tools.kinds.or.kr/word_cloud")
    
    def test_api_key_validation(self):
        """API 키 검증 테스트"""
        # API 키 없이 초기화 시도
        with self.assertRaises(ValueError):
            client = BigKindsClient(api_key=None)

if __name__ == '__main__':
    unittest.main()