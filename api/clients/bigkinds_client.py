from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

class BigkindsClient:
    def get_company_news(
        self,
        company_name: str,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        return_size: int = 20
    ) -> Dict[str, Any]:
        """기업 관련 뉴스 검색
        
        Args:
            company_name: 기업명
            date_from: 시작일
            date_to: 종료일
            return_size: 반환할 결과 수
            
        Returns:
            기업 뉴스 검색 결과
        """
        # 기업명으로 검색, 모든 언론사 대상
        return self.search_news(
            query=company_name,
            date_from=date_from,
            date_to=date_to,
            fields=[
                "news_id",
                "title",
                "content", 
                "published_at",
                "category",
                "provider_name",
                "provider_code",
                "provider_link_page",
                "byline",
                "images"
            ],
            return_size=return_size
        )
    
    def get_company_news_for_summary(
        self,
        company_name: str,
        days: int = 7,
        limit: int = 5
    ) -> Dict[str, Any]:
        """기업의 최근 뉴스를 요약용으로 가져오기
        
        Args:
            company_name: 기업명
            days: 최근 며칠간 (기본값: 7일)
            limit: 가져올 기사 수 (기본값: 5개)
            
        Returns:
            요약용 뉴스 데이터 (제목, 내용 포함)
        """
        # 날짜 범위 설정
        end_date = datetime.now()
        # until은 오늘 날짜 +1일로 설정 (오늘 데이터 포함 위해)
        end_date_plus_one = end_date + timedelta(days=1)
        start_date = end_date - timedelta(days=days)
        
        date_from = start_date.strftime("%Y-%m-%d")
        date_to = end_date_plus_one.strftime("%Y-%m-%d")
        
        # 기업 뉴스 검색 - content 필드 반드시 포함
        search_result = self.get_company_news(
            company_name=company_name,
            date_from=date_from,
            date_to=date_to,
            return_size=limit
        )
        
        # 응답 포맷팅
        formatted_result = self.format_news_response(search_result)
        
        return {
            "success": formatted_result.get("success", False),
            "company": company_name,
            "period": {"from": date_from, "to": date_to},
            "articles": formatted_result.get("documents", []),
            "total_found": formatted_result.get("total_hits", 0)
        }
    
    def get_company_news_timeline(
        self,
        company_name: str,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        return_size: int = 30
    ) -> Dict[str, Any]:
        """기업별 뉴스 타임라인 조회
        
        Args:
            company_name: 기업명
            date_from: 시작일
            date_to: 종료일
            return_size: 반환할 결과 수
            
        Returns:
            일자별 뉴스 목록
        """
        # 종료일에 +1일 추가 (오늘 데이터 포함)
        if date_to:
            # 이미 date_to가 설정된 경우 +1일
            dt_obj = datetime.strptime(date_to, "%Y-%m-%d")
            date_to = (dt_obj + timedelta(days=1)).strftime("%Y-%m-%d")
        
        # 기업 관련 뉴스 검색
        news_response = self.get_company_news(
            company_name=company_name,
            date_from=date_from,
            date_to=date_to,
            return_size=return_size
        )
        
        # 응답 포맷팅
        formatted_response = self.format_news_response(news_response)
        
        # 날짜별로 뉴스 그룹화
        timeline = {}
        for doc in formatted_response.get("documents", []):
            # published_at에서 날짜 부분만 추출
            published_at = doc.get("published_at", "")
            date_str = published_at[:10] if published_at else ""  # YYYY-MM-DD 형식
            
            if date_str and date_str not in timeline:
                timeline[date_str] = []
            
            if date_str:
                timeline[date_str].append(doc)
        
        # 날짜 기준 내림차순 정렬
        sorted_timeline = []
        for date_str in sorted(timeline.keys(), reverse=True):
            sorted_timeline.append({
                "date": date_str,
                "articles": timeline[date_str],
                "count": len(timeline[date_str])
            })
        
        return {
            "success": True,
            "company": company_name,
            "period": {
                "from": date_from,
                "to": date_to
            },
            "total_count": len(formatted_response.get("documents", [])),
            "timeline": sorted_timeline
        }
        
    def search_news(
        self,
        query: str = "",
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        provider: Optional[List[str]] = None,
        category: Optional[List[str]] = None,
        fields: Optional[List[str]] = None,
        sort_by: str = "date",
        sort_order: str = "desc",
        return_from: int = 0,
        return_size: int = 10,
        news_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """뉴스 검색 API"""
        pass
        
    def format_news_response(self, api_response: Dict[str, Any]) -> Dict[str, Any]:
        """API 응답 포맷팅"""
        pass 