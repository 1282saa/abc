/**
 * API 서비스 모듈
 */

// Vite 환경 변수는 import.meta.env 를 통해 접근합니다.
// .env 파일에서는 VITE_API_URL 로 정의해 주세요.
const API_BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

// 요청 옵션
const defaultOptions: RequestInit = {
  headers: {
    "Content-Type": "application/json",
  },
};

// 타임라인 요청 인터페이스
export interface TimelineRequest {
  keywords: string;
  date_from?: string;
  date_to?: string;
}

// 타임라인 응답 인터페이스
export interface TimelineResponse {
  timeline: Array<{
    date: string;
    title: string;
    summary: string;
  }>;
}

// QA 요청 인터페이스
export interface QARequest {
  query: string;
  use_sources?: boolean;
}

// QA 응답 인터페이스
export interface QAResponse {
  answer: string;
  sources?: Array<{
    title: string;
    url: string;
    content: string;
  }>;
}

// 요약 요청 인터페이스
export interface SummaryRequest {
  url: string;
  keywords?: string[];
}

// 요약 응답 인터페이스
export interface SummaryResponse {
  title: string;
  original_text: string;
  summary: string;
  keywords: string[];
}

// 주식 캘린더 요청 인터페이스
export interface StockCalendarRequest {
  startDate: string;
  endDate: string;
  marketType?: string;
  eventTypes?: string[];
}

// 주식 캘린더 응답 인터페이스
export interface StockCalendarResponse {
  events: Array<{
    id: string;
    title: string;
    date: string;
    eventType: "earnings" | "dividend" | "holiday" | "ipo" | "economic" | "split";
    stockCode?: string;
    stockName?: string;
    description?: string;
    marketType?: "domestic" | "us" | "global";
  }>;
}

// API 서비스 객체
const apiService = {
  /**
   * 타임라인 API 호출
   */
  async getTimeline(params: TimelineRequest): Promise<TimelineResponse> {
    // 백엔드 QueryRequest { query, search_params } 구조에 맞춰 변환
    const backendBody: any = {
      query: params.keywords,
    };

    if (params.date_from && params.date_to) {
      backendBody.search_params = {
        date_range: [params.date_from, params.date_to],
      };
    }

    const response = await fetch(`${API_BASE_URL}/api/qa/timeline`, {
      ...defaultOptions,
      method: "POST",
      body: JSON.stringify(backendBody),
    });

    if (!response.ok) {
      throw new Error(`API 오류: ${response.status}`);
    }

    return response.json();
  },

  /**
   * QA API 호출
   */
  async getAnswer(params: QARequest): Promise<QAResponse> {
    const response = await fetch(`${API_BASE_URL}/api/qa/query`, {
      ...defaultOptions,
      method: "POST",
      body: JSON.stringify({ query: params.query, stream: false }),
    });

    if (!response.ok) {
      throw new Error(`API 오류: ${response.status}`);
    }

    return response.json();
  },

  /**
   * 스트리밍 QA API 호출 (SSE)
   */
  getAnswerStream(
    params: QARequest,
    onData: (data: string) => void,
    onComplete: () => void,
    onError: (error: Error) => void
  ): () => void {
    const eventSource = new EventSource(
      `${API_BASE_URL}/api/qa/query?stream=true&query=${encodeURIComponent(
        params.query
      )}`
    );

    eventSource.onmessage = (event) => {
      const data = event.data;
      if (data === "[DONE]") {
        eventSource.close();
        onComplete();
      } else {
        onData(data);
      }
    };

    eventSource.onerror = (error) => {
      eventSource.close();
      onError(new Error("SSE 연결 오류"));
    };

    // 연결 종료 함수 반환
    return () => {
      eventSource.close();
    };
  },

  /**
   * 요약 API 호출
   */
  async getSummary(params: SummaryRequest): Promise<SummaryResponse> {
    // 백엔드 QueryRequest 구조에 맞춰 변환
    const response = await fetch(`${API_BASE_URL}/api/qa/summarize`, {
      ...defaultOptions,
      method: "POST",
      body: JSON.stringify({ query: params.url }),
    });

    if (!response.ok) {
      throw new Error(`API 오류: ${response.status}`);
    }

    return response.json();
  },

  /**
   * 주식 캘린더 이벤트 조회 API 호출
   */
  async getStockCalendarEvents(params: StockCalendarRequest): Promise<StockCalendarResponse> {
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

    const response = await fetch(`${API_BASE_URL}/api/stock-calendar/events?${queryParams}`, {
      ...defaultOptions,
      method: "GET",
    });

    if (!response.ok) {
      throw new Error(`API 오류: ${response.status} - ${response.statusText}`);
    }

    return response.json();
  },
};

export default apiService;
export const getStockCalendarEvents = apiService.getStockCalendarEvents;
