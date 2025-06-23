import axiosInstance from "./axiosConfig";
import { AxiosError } from "axios";

export interface ConciergeBriefingResponse {
  query: string;
  summary: string;
  points?: {
    question: string;
    answer: string;
    citations: number[];
  }[];
  documents: {
    news_id: string;
    title: string;
    content: string;
    provider: string;
    published_at: string;
    enveloped_at?: string; // 수집 시간
    dateline?: string; // 언론사 출고시간
    url?: string;
    provider_link_page?: string; // 언론사 원본 링크
    hilight?: string; // 검색어가 포함된 영역
    byline?: string; // 기자 이름
    category?: string; // 뉴스 분류
    images?: string[]; // 이미지 파일명
    images_caption?: string[]; // 이미지 설명
  }[];
  keywords?: {
    keyword: string;
    count: number;
    weight: number;
  }[];
  network_data?: {
    nodes: any[];
    links: any[];
  };
  total_hits?: number; // 전체 검색 결과 수
  current_page?: number; // 현재 페이지
  has_more?: boolean; // 더 많은 결과 존재 여부
}

// 페이지네이션을 지원하는 검색 함수
export const getConciergeBriefing = async (
  query: string,
  page: number = 1,
  size: number = 10
): Promise<ConciergeBriefingResponse> => {
  try {
    // 불용어 처리 및 쿼리 최적화
    const optimizedQuery = optimizeSearchQuery(query);

    const response = await axiosInstance.post("/briefing/question", {
      question: optimizedQuery,
      page: page,
      size: size,
      include_hilight: true, // 하이라이트 정보 포함 요청
      sort: "published_at:desc", // 날짜순 내림차순 정렬
    });
    return response.data;
  } catch (error: any) {
    if (error instanceof AxiosError && error.response) {
      throw new Error(
        error.response.data.detail ||
          "AI 컨시어지 브리핑을 가져오는 중 오류가 발생했습니다."
      );
    }
    throw new Error("네트워크 오류 또는 서버에 연결할 수 없습니다.");
  }
};

// 기존 함수는 호환성을 위해 유지 (첫 페이지만)
export const getConciergeBriefingLegacy = async (
  query: string
): Promise<ConciergeBriefingResponse> => {
  return getConciergeBriefing(query, 1, 50); // 첫 페이지, 50개 기사
};

// 불용어 처리 및 검색 쿼리 최적화 함수
export const optimizeSearchQuery = (query: string): string => {
  // 한국어 불용어 목록
  const stopwords = [
    "은",
    "는",
    "이",
    "가",
    "을",
    "를",
    "에",
    "에서",
    "로",
    "으로",
    "와",
    "과",
    "의",
    "도",
    "만",
    "부터",
    "까지",
    "보다",
    "처럼",
    "같이",
    "하고",
    "하지만",
    "그리고",
    "또는",
    "그런데",
    "하지만",
    "그래서",
    "따라서",
    "그러나",
    "하지만",
    "그런",
    "이런",
    "저런",
    "어떤",
    "무엇",
    "누구",
    "언제",
    "어디",
    "어떻게",
    "왜",
    "얼마나",
  ];

  // 기존 AND 연산자 제거하고 다시 처리
  const cleanQuery = query.replace(/\s+AND\s+/gi, " ").trim();

  // 쿼리를 단어로 분리하고 불용어 제거
  const words = cleanQuery
    .split(/\s+/)
    .filter((word) => word.length > 1) // 1글자 단어 제거
    .filter((word) => !stopwords.includes(word)) // 불용어 제거
    .filter((word) => !/^[!@#$%^&*(),.?":{}|<>]+$/.test(word)) // 특수문자만으로 구성된 단어 제거
    .filter((word, index, arr) => arr.indexOf(word) === index); // 중복 제거

  // 중요한 키워드들을 공백으로 연결 (AND 연산자 사용하지 않음)
  if (words.length > 0) {
    return words.join(" ");
  } else {
    return cleanQuery || query; // 원본 쿼리 반환 (모든 단어가 불용어인 경우)
  }
};

// 맥락을 고려한 스마트 쿼리 구성 함수
export const buildSmartContextualQuery = (
  newQuery: string,
  previousQueries: string[] = []
): string => {
  const newKeywords = extractKeywords(newQuery);

  // 이전 질문들과의 키워드 유사도 계산
  let relevantContext: string[] = [];

  if (previousQueries.length > 0) {
    for (const prevQuery of previousQueries.slice(-2)) {
      // 최근 2개만 확인
      const prevKeywords = extractKeywords(prevQuery);
      const similarity = calculateKeywordSimilarity(newKeywords, prevKeywords);

      // 유사도가 30% 이상이면 관련 맥락으로 간주
      if (similarity > 0.3) {
        relevantContext.push(prevQuery);
      }
    }
  }

  // 관련 맥락이 있으면 포함, 없으면 새로운 질문만 사용
  if (relevantContext.length > 0) {
    const contextKeywords = relevantContext
      .map(extractKeywords)
      .flat()
      .filter((keyword, index, arr) => arr.indexOf(keyword) === index) // 중복 제거
      .slice(0, 3); // 최대 3개의 맥락 키워드

    const allKeywords = Array.from(
      new Set([...newKeywords, ...contextKeywords])
    );
    return optimizeSearchQuery(allKeywords.join(" "));
  } else {
    return optimizeSearchQuery(newQuery);
  }
};

// 키워드 추출 함수
const extractKeywords = (text: string): string[] => {
  return text
    .split(/\s+/)
    .filter((word) => word.length > 1)
    .filter((word) => !/^[!@#$%^&*(),.?":{}|<>]+$/.test(word))
    .slice(0, 5); // 최대 5개 키워드
};

// 키워드 유사도 계산 함수
const calculateKeywordSimilarity = (
  keywords1: string[],
  keywords2: string[]
): number => {
  if (keywords1.length === 0 || keywords2.length === 0) return 0;

  const intersection = keywords1.filter((k) => keywords2.includes(k));
  const union = Array.from(new Set([...keywords1, ...keywords2]));

  return intersection.length / union.length; // Jaccard 유사도
};

export interface ArticleSearchResponse {
  success: boolean;
  query: string;
  page: number;
  size: number;
  total_hits: number;
  documents: {
    news_id: string;
    title: string;
    content: string;
    provider: string;
    published_at: string;
    url: string;
  }[];
  has_more: boolean;
}

export const searchArticles = async (
  query: string,
  page: number = 0,
  size: number = 10
): Promise<ArticleSearchResponse> => {
  try {
    const response = await axiosInstance.post("/briefing/articles", {
      query,
      page,
      size,
    });
    return response.data;
  } catch (error: any) {
    if (error instanceof AxiosError && error.response) {
      throw new Error(
        error.response.data.detail || "기사 검색 중 오류가 발생했습니다."
      );
    }
    throw new Error("네트워크 오류 또는 서버에 연결할 수 없습니다.");
  }
};
