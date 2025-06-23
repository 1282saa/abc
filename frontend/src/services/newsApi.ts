import axios from "axios";
import axiosInstance from "./axiosConfig";

export interface NewsArticle {
  news_id: string;
  title: string;
  content: string;
  summary?: string;
  provider: string;
  provider_code?: string;
  provider_link_page?: string;
  url?: string;
  byline?: string;
  category?: string;
  published_at: string;
  enveloped_at?: string;
  images?: string[];
  images_caption?: string[];
}

export interface NewsDetailResponse {
  success: boolean;
  news: NewsArticle;
  has_original_link: boolean;
  metadata?: {
    retrieved_at: string;
    source: string;
  };
}

/**
 * 뉴스 상세 정보를 가져오는 함수
 * @param newsId 뉴스 ID
 * @returns 뉴스 상세 정보
 */
export const getNewsDetail = async (
  newsId: string
): Promise<NewsDetailResponse> => {
  try {
    const response = await axiosInstance.get<NewsDetailResponse>(
      `/news/detail/${newsId}`
    );
    return response.data;
  } catch (error) {
    console.error("뉴스 상세 정보 조회 실패:", error);
    throw new Error("뉴스 상세 정보를 가져오는데 실패했습니다.");
  }
};

/**
 * 뉴스 링크를 결정하는 함수
 * @param article 뉴스 기사 객체
 * @returns 뉴스 링크 URL
 */
export const getArticleLink = (article: any): string => {
  // 언론사 원본 링크가 있으면 우선 사용
  if (article.provider_link_page && article.provider_link_page.trim()) {
    return article.provider_link_page;
  }
  // 빅카인즈 URL이 있으면 사용
  if (article.url && article.url.trim()) {
    return article.url;
  }
  // 둘 다 없으면 빅카인즈 검색 페이지로 이동
  const searchQuery = encodeURIComponent(article.title || '뉴스');
  return `https://www.kinds.or.kr/search?query=${searchQuery}`;
};
