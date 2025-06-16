/**
 * News API 서비스 모듈
 * BigKinds 뉴스 API와 통신하는 클라이언트
 */

// Vite 환경 변수는 import.meta.env 를 통해 접근합니다.
const API_BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8080";

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

// 관심종목 추가 요청 인터페이스
export interface WatchlistAddRequest {
  name: string;
  code: string;
  category: string;
}

// 관심종목 응답 인터페이스
export interface WatchlistResponse {
  success: boolean;
  message: string;
  watchlist?: Array<{
    name: string;
    code: string;
    category: string;
    added_at: string;
    recent_news_count: number;
    has_recent_news: boolean;
  }>;
}

// 레포트 기간 타입
export type ReportPeriodType = "daily" | "weekly" | "monthly" | "quarterly" | "yearly";

// 레포트 생성 요청 인터페이스
export interface ReportRequest {
  company_name: string;
  company_code?: string;
  period_type: ReportPeriodType;
  date_from: string;
  date_to: string;
  language?: "ko" | "en";
  include_charts?: boolean;
  max_articles?: number;
}

// 인용 출처 인터페이스
export interface CitationSource {
  id: string;
  title: string;
  url: string;
  provider: string;
  published_at: string;
  excerpt: string;
}

// 레포트 섹션 인터페이스
export interface ReportSection {
  title: string;
  content: string;
  key_points: string[];
  citations: number[];
}

// 레포트 메타데이터 인터페이스
export interface ReportMetadata {
  company_name: string;
  company_code?: string;
  period_type: ReportPeriodType;
  date_from: string;
  date_to: string;
  total_articles: number;
  generated_at: string;
  generation_time_seconds: number;
  model_used: string;
}

// 기업 레포트 인터페이스
export interface CompanyReport {
  metadata: ReportMetadata;
  executive_summary: string;
  sections: ReportSection[];
  citations: CitationSource[];
  keywords: string[];
  sentiment_analysis: Record<string, any>;
  stock_impact?: string;
}

// 레포트 스트리밍 데이터 인터페이스
export interface ReportStreamData {
  type: "progress" | "content" | "section" | "complete" | "error";
  step?: string;
  progress?: number;
  section_title?: string;
  content?: string;
  result?: CompanyReport;
  error?: string;
}

// 기간별 레포트 관련 인터페이스들
export interface ReportGenerationProgress {
  stage: string;
  progress: number;
  message: string;
  current_task?: string;
  estimated_remaining_seconds?: number;
}

export enum PeriodReportType {
  DAILY = "daily",
  WEEKLY = "weekly", 
  MONTHLY = "monthly",
  QUARTERLY = "quarterly",
  YEARLY = "yearly"
}

export interface AutoReportRequest {
  report_type: PeriodReportType;
  company_name?: string;
  company_code?: string;
  target_date?: string;
  categories: string[];
  max_articles: number;
  include_sentiment: boolean;
  include_keywords: boolean;
  language: string;
}

export interface NewsCluster {
  id: string;
  title: string;
  articles_count: number;
  representative_article_id: string;
  keywords: string[];
  categories: string[];
  sentiment_score?: number;
  impact_score?: number;
}

export interface PeriodInsight {
  type: string;
  title: string;
  description: string;
  confidence: number;
  supporting_clusters: string[];
}

export interface CategorySummary {
  category: string;
  total_articles: number;
  top_clusters: NewsCluster[];
  key_developments: string[];
  sentiment_trend?: string;
}

export interface TimelineEvent {
  date: string;
  title: string;
  description: string;
  importance: number;
  related_cluster_ids: string[];
  category: string;
}

export interface PeriodReport {
  id: string;
  report_type: PeriodReportType;
  company_name?: string;
  company_code?: string;
  period_start: string;
  period_end: string;
  generated_at: string;
  total_articles_analyzed: number;
  categories_covered: string[];
  analysis_duration_seconds: number;
  executive_summary: string;
  key_highlights: string[];
  category_summaries: CategorySummary[];
  timeline: TimelineEvent[];
  insights: PeriodInsight[];
  top_keywords: Array<{keyword: string; count: number; category: string}>;
  sentiment_analysis: Record<string, any>;
  trend_analysis: Record<string, any>;
  comparison?: Record<string, any>;
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
    onProgress: (data: {
      step: string;
      progress: number;
      type?: string;
    }) => void,
    onChunk: (chunk: string) => void,
    onComplete: (result: AISummaryResponse) => void,
    onError: (error: string) => void
  ): Promise<void> {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/news/ai-summary-stream`,
        {
          ...defaultOptions,
          method: "POST",
          body: JSON.stringify(request),
        }
      );

      if (!response.ok) {
        throw new Error(`API 오류: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error("스트림을 읽을 수 없습니다");
      }

      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6));

              if (data.error) {
                onError(data.error);
                return;
              }

              if (data.step && data.progress !== undefined) {
                onProgress({
                  step: data.step,
                  progress: data.progress,
                  type: data.type || "thinking",
                });
              }

              if (data.chunk && data.type === "content") {
                onChunk(data.chunk);
              }

              if (data.result && data.type === "complete") {
                onComplete(data.result);
                return;
              }
            } catch (e) {
              console.warn("JSON 파싱 오류:", e);
            }
          }
        }
      }
    } catch (error) {
      onError(
        error instanceof Error
          ? error.message
          : "알 수 없는 오류가 발생했습니다"
      );
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

  /**
   * 관심종목에 기업 추가
   */
  async addToWatchlist(
    request: WatchlistAddRequest
  ): Promise<WatchlistResponse> {
    const response = await fetch(`${API_BASE_URL}/api/news/watchlist`, {
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
   * 관심종목에서 기업 삭제
   */
  async removeFromWatchlist(stockCode: string): Promise<WatchlistResponse> {
    const response = await fetch(
      `${API_BASE_URL}/api/news/watchlist/${stockCode}`,
      {
        ...defaultOptions,
        method: "DELETE",
      }
    );

    if (!response.ok) {
      throw new Error(`API 오류: ${response.status}`);
    }

    return response.json();
  },

  /**
   * 기업 레포트 생성 (동기식)
   */
  async generateCompanyReport(request: ReportRequest): Promise<CompanyReport> {
    const response = await fetch(`${API_BASE_URL}/api/reports/company/generate`, {
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
   * 기업 레포트 생성 (스트리밍)
   */
  async generateCompanyReportStream(
    request: ReportRequest,
    onProgress: (data: ReportStreamData) => void,
    onComplete: (result: CompanyReport) => void,
    onError: (error: string) => void
  ): Promise<void> {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/reports/company/generate-stream`,
        {
          ...defaultOptions,
          method: "POST",
          body: JSON.stringify(request),
        }
      );

      if (!response.ok) {
        throw new Error(`API 오류: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error("스트림을 읽을 수 없습니다");
      }

      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6)) as ReportStreamData;

              if (data.error) {
                onError(data.error);
                return;
              }

              if (data.type === "progress") {
                onProgress(data);
              }

              if (data.type === "complete" && data.result) {
                onComplete(data.result);
                return;
              }
            } catch (e) {
              console.warn("JSON 파싱 오류:", e);
            }
          }
        }
      }
    } catch (error) {
      onError(
        error instanceof Error
          ? error.message
          : "알 수 없는 오류가 발생했습니다"
      );
    }
  },

  /**
   * 사용 가능한 레포트 템플릿 조회
   */
  async getReportTemplates(): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/api/reports/templates`, {
      ...defaultOptions,
      method: "GET",
    });

    if (!response.ok) {
      throw new Error(`API 오류: ${response.status}`);
    }

    return response.json();
  },

  /**
   * 레포트 요청 유효성 검사
   */
  async validateReportRequest(request: ReportRequest): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/api/reports/company/validate`, {
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
   * 기간별 레포트 생성 (동기식)
   */
  async generatePeriodReport(request: AutoReportRequest): Promise<PeriodReport> {
    const response = await fetch(`${API_BASE_URL}/api/period-reports/generate`, {
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
   * 기간별 레포트 생성 (스트리밍)
   */
  async generatePeriodReportStream(
    request: AutoReportRequest,
    onProgress: (data: ReportGenerationProgress) => void,
    onComplete: (result: PeriodReport) => void,
    onError: (error: string) => void
  ): Promise<void> {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/period-reports/generate-stream`,
        {
          ...defaultOptions,
          method: "POST",
          body: JSON.stringify(request),
        }
      );

      if (!response.ok) {
        throw new Error(`API 오류: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error("스트림을 읽을 수 없습니다");
      }

      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6));

              if (data.error) {
                onError(data.error);
                return;
              }

              if (data.stage === "final_result" && data.result) {
                onComplete(data.result);
                return;
              } else if (data.stage && data.progress !== undefined) {
                onProgress(data as ReportGenerationProgress);
              }
            } catch (e) {
              console.warn("JSON 파싱 오류:", e);
            }
          }
        }
      }
    } catch (error) {
      onError(
        error instanceof Error
          ? error.message
          : "알 수 없는 오류가 발생했습니다"
      );
    }
  },

  /**
   * 기간별 레포트 템플릿 조회
   */
  async getPeriodReportTemplates(): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/api/period-reports/templates`, {
      ...defaultOptions,
      method: "GET",
    });

    if (!response.ok) {
      throw new Error(`API 오류: ${response.status}`);
    }

    return response.json();
  },

  /**
   * 빠른 기간별 레포트 생성
   */
  async quickGeneratePeriodReport(
    reportType: PeriodReportType,
    categories?: string,
    maxArticles?: number
  ): Promise<PeriodReport> {
    const params = new URLSearchParams();
    if (categories) params.append("categories", categories);
    if (maxArticles) params.append("max_articles", maxArticles.toString());

    const response = await fetch(
      `${API_BASE_URL}/api/period-reports/quick-generate/${reportType}?${params}`,
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
   * 기간 정보 조회
   */
  async getPeriodInfo(reportType: PeriodReportType): Promise<any> {
    const response = await fetch(
      `${API_BASE_URL}/api/period-reports/period-info/${reportType}`,
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
   * 사용 가능한 카테고리 조회
   */
  async getPeriodReportCategories(): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/api/period-reports/categories`, {
      ...defaultOptions,
      method: "GET",
    });

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
  addToWatchlist,
  removeFromWatchlist,
  generateCompanyReport,
  generateCompanyReportStream,
  getReportTemplates,
  validateReportRequest,
  generatePeriodReport,
  generatePeriodReportStream,
  getPeriodReportTemplates,
  quickGeneratePeriodReport,
  getPeriodInfo,
  getPeriodReportCategories,
} = newsApiService;

// API 객체로도 export (기간별 레포트 페이지에서 사용)
export const api = newsApiService;
