/**
 * API 서비스 모듈
 */

// API 기본 URL
const API_BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

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

// API 서비스 객체
const apiService = {
  /**
   * 타임라인 API 호출
   */
  async getTimeline(params: TimelineRequest): Promise<TimelineResponse> {
    const response = await fetch(`${API_BASE_URL}/api/timeline`, {
      ...defaultOptions,
      method: "POST",
      body: JSON.stringify(params),
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
    const response = await fetch(`${API_BASE_URL}/api/qa`, {
      ...defaultOptions,
      method: "POST",
      body: JSON.stringify(params),
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
      `${API_BASE_URL}/api/qa/stream?query=${encodeURIComponent(
        params.query
      )}&use_sources=${params.use_sources || false}`
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
    const response = await fetch(`${API_BASE_URL}/api/summary`, {
      ...defaultOptions,
      method: "POST",
      body: JSON.stringify(params),
    });

    if (!response.ok) {
      throw new Error(`API 오류: ${response.status}`);
    }

    return response.json();
  },
};

export default apiService;
