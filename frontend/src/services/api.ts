/**
 * News API 서비스 모듈
 * BigKinds 뉴스 API와 통신하는 클라이언트
 */

// Vite 환경 변수는 import.meta.env 를 통해 접근합니다.
const API_BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

// 요청 옵션
const defaultOptions: RequestInit = {
  headers: {
    "Content-Type": "application/json",
  },
};

// 뉴스 기사 인터페이스
export interface NewsArticle {
  id: string;
  title: string;
  content: string;
  summary: string;
  published_at: string;
  dateline: string;
  category: string[];
  provider: string;
  provider_code: string;
  url: string;
  byline: string;
  images: string[];
  images_caption?: string;
}

// 타임라인 항목 인터페이스
export interface TimelineItem {
  date: string;
  articles: NewsArticle[];
  count: number;
}

// 언론사별 기사 수 breakdown 인터페이스
export interface ProviderBreakdown {
  provider: string;
  provider_code: string;
  count: number;
}

// 이슈 토픽 인터페이스 (백엔드 응답에 맞게 수정)
export interface IssueTopic {
  rank: number;
  title: string;
  count: number;
  related_news: string[];
  provider_breakdown?: ProviderBreakdown[]; // 언론사별 기사 수
  related_news_ids?: string[]; // 실제 뉴스 ID 목록
  cluster_ids?: string[]; // 원본 클러스터 ID
  // 프론트엔드 호환성을 위한 선택적 필드들
  topic_id?: string;
  topic_name?: string;
  score?: number;
  news_cluster?: string[];
  keywords?: string[];
  topic?: string;
  topic_rank?: number;
  topic_keyword?: string;
}

// 인기 키워드 인터페이스 (백엔드 응답에 맞게 수정)
export interface PopularKeyword {
  rank: number;
  keyword: string;
  count: number;
  trend: string;
  // 프론트엔드 호환성을 위한 선택적 필드들
  category?: string;
  score?: number;
}

// 최신 뉴스 응답 인터페이스
export interface LatestNewsResponse {
  today_issues: IssueTopic[];
  popular_keywords: PopularKeyword[];
  timestamp: string;
}

// 기업 뉴스 요청 인터페이스
export interface CompanyNewsRequest {
  company_name: string;
  date_from?: string;
  date_to?: string;
  limit?: number;
}

// 키워드 뉴스 요청 인터페이스
export interface KeywordNewsRequest {
  keyword: string;
  date_from?: string;
  date_to?: string;
  limit?: number;
}

// 뉴스 타임라인 응답 인터페이스
export interface NewsTimelineResponse {
  keyword?: string;
  company?: string;
  period: {
    from: string;
    to: string;
  };
  total_count: number;
  timeline: TimelineItem[];
}

// AI 요약 요청 인터페이스
export interface AISummaryRequest {
  news_ids: string[];
}

// AI 요약 응답 인터페이스
export interface AISummaryResponse {
  title: string;
  summary: string;
  type: string;
  key_points?: string[];
  key_quotes?: Array<{
    source: string;
    quote: string;
  }>;
  key_data?: Array<{
    metric: string;
    value: string;
    context: string;
  }>;
  articles_analyzed: number;
  generated_at: string;
  model_used: string;
}

// 뉴스 상세 정보 응답 인터페이스
export interface NewsDetailResponse {
  success: boolean;
  news: NewsArticle;
  has_original_link: boolean;
}

// 관심 종목 추천 응답 인터페이스
export interface WatchlistSuggestion {
  name: string;
  code: string;
  category: string;
}

export interface WatchlistSuggestionsResponse {
  suggestions: WatchlistSuggestion[];
}

// 주식 캘린더 요청 인터페이스 (기존 유지)
export interface StockCalendarRequest {
  startDate: string;
  endDate: string;
  marketType?: string;
  eventTypes?: string[];
}

// 주식 캘린더 응답 인터페이스 (기존 유지)
export interface StockCalendarResponse {
  events: Array<{
    id: string;
    title: string;
    date: string;
    eventType:
      | "earnings"
      | "dividend"
      | "holiday"
      | "ipo"
      | "economic"
      | "split";
    stockCode?: string;
    stockName?: string;
    description?: string;
    marketType?: "domestic" | "us" | "global";
  }>;
}

// 관련 질문 인터페이스
export interface RelatedQuestion {
  id: number;
  question: string;
  query: string;
  count: number;
  score: number;
  description: string;
}

// 관련 질문 응답 인터페이스
export interface RelatedQuestionsResponse {
  success: boolean;
  keyword: string;
  period: {
    from: string;
    to: string;
  };
  total_count: number;
  questions: RelatedQuestion[];
}

// News API 서비스 객체
const newsApiService = {
  /**
   * 최신 뉴스 정보 가져오기
   */
  async getLatestNews(): Promise<LatestNewsResponse> {
    const response = await fetch(`${API_BASE_URL}/api/news/latest`, {
      ...defaultOptions,
      method: "GET",
    });

    if (!response.ok) {
      throw new Error(`API 오류: ${response.status}`);
    }

    return response.json();
  },

  /**
   * 기업 뉴스 타임라인 조회
   */
  async getCompanyNews(
    request: CompanyNewsRequest
  ): Promise<NewsTimelineResponse> {
    const response = await fetch(`${API_BASE_URL}/api/news/company`, {
      ...defaultOptions,
      method: "POST",
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`API 오류: ${response.status}`);
    }

    return response.json();
  },

  /**
   * 키워드 뉴스 타임라인 조회
   */
  async getKeywordNews(
    request: KeywordNewsRequest
  ): Promise<NewsTimelineResponse> {
    const response = await fetch(`${API_BASE_URL}/api/news/keyword`, {
      ...defaultOptions,
      method: "POST",
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`API 오류: ${response.status}`);
    }

    return response.json();
  },

  /**
   * 뉴스 상세 정보 조회
   */
  async getNewsDetail(newsId: string): Promise<NewsDetailResponse> {
    const response = await fetch(`${API_BASE_URL}/api/news/detail/${newsId}`, {
      ...defaultOptions,
      method: "GET",
    });

    if (!response.ok) {
      throw new Error(`API 오류: ${response.status}`);
    }

    return response.json();
  },

  /**
   * AI 요약 생성
   */
  async generateAISummary(
    request: AISummaryRequest
  ): Promise<AISummaryResponse> {
    const response = await fetch(`${API_BASE_URL}/api/news/ai-summary`, {
      ...defaultOptions,
      method: "POST",
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`API 오류: ${response.status}`);
    }

    return response.json();
  },

  /**
   * AI 요약 생성 (스트리밍)
   */
  async generateAISummaryStream(
    request: AISummaryRequest,
    onProgress: (data: any) => void,
    onChunk: (chunk: string) => void,
    onComplete: (result: AISummaryResponse) => void,
    onError: (error: string) => void
  ): Promise<void> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/news/ai-summary-stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`API 오류: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error("스트림 읽기 실패");
      }

      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              
              if (data.error) {
                onError(data.error);
                return;
              }
              
              if (data.step && data.progress) {
                onProgress(data);
              }
              
              if (data.chunk) {
                onChunk(data.chunk);
              }
              
              if (data.result) {
                onComplete(data.result);
                return;
              }
            } catch (e) {
              console.warn('JSON 파싱 실패:', line);
            }
          }
        }
      }
    } catch (error) {
      onError(error instanceof Error ? error.message : "알 수 없는 오류가 발생했습니다");
    }
  },

  /**
   * 관심 종목 추천 목록 조회
   */
  async getWatchlistSuggestions(): Promise<WatchlistSuggestionsResponse> {
    const response = await fetch(
      `${API_BASE_URL}/api/news/watchlist/suggestions`,
      {
        ...defaultOptions,
        method: "GET",
      }
    );

    if (!response.ok) {
      throw new Error(`API 오류: ${response.status}`);
    }

    return response.json();
  },

  /**
   * 뉴스 검색 (GET 방식)
   */
  async searchNews(
    keyword: string,
    dateFrom?: string,
    dateTo?: string,
    limit: number = 30
  ): Promise<NewsTimelineResponse> {
    const params = new URLSearchParams({
      keyword,
      limit: limit.toString(),
    });

    if (dateFrom) {
      params.append("date_from", dateFrom);
    }

    if (dateTo) {
      params.append("date_to", dateTo);
    }

    const response = await fetch(`${API_BASE_URL}/api/news/search?${params}`, {
      ...defaultOptions,
      method: "GET",
    });

    if (!response.ok) {
      throw new Error(`API 오류: ${response.status}`);
    }

    return response.json();
  },

  /**
   * 주식 캘린더 이벤트 조회 (기존 유지)
   */
  async getStockCalendarEvents(
    params: StockCalendarRequest
  ): Promise<StockCalendarResponse> {
    const queryParams = new URLSearchParams({
      start_date: params.startDate,
      end_date: params.endDate,
    });

    if (params.marketType && params.marketType !== "all") {
      queryParams.append("market_type", params.marketType);
    }

    if (params.eventTypes && params.eventTypes.length > 0) {
      params.eventTypes.forEach((type) => {
        queryParams.append("event_types", type);
      });
    }

    const response = await fetch(
      `${API_BASE_URL}/api/stock-calendar/events?${queryParams}`,
      {
        ...defaultOptions,
        method: "GET",
      }
    );

    if (!response.ok) {
      throw new Error(`API 오류: ${response.status} - ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * 연관 질문 조회
   */
  async getRelatedQuestions(
    keyword: string,
    dateFrom?: string,
    dateTo?: string,
    maxQuestions: number = 10
  ): Promise<RelatedQuestionsResponse> {
    const params = new URLSearchParams({
      keyword,
      max_questions: maxQuestions.toString(),
    });

    if (dateFrom) {
      params.append("date_from", dateFrom);
    }

    if (dateTo) {
      params.append("date_to", dateTo);
    }

    const response = await fetch(
      `${API_BASE_URL}/api/related-questions?${params}`,
      {
        ...defaultOptions,
        method: "GET",
      }
    );

    if (!response.ok) {
      throw new Error(`API 오류: ${response.status}`);
    }

    return response.json();
  },
};

export default newsApiService;

// 개별 함수들도 export
export const {
  getLatestNews,
  getCompanyNews,
  getKeywordNews,
  getNewsDetail,
  generateAISummary,
  generateAISummaryStream,
  getWatchlistSuggestions,
  searchNews,
  getStockCalendarEvents,
  getRelatedQuestions,
} = newsApiService;
