import { useState } from "react";
import apiService, { TimelineRequest, TimelineResponse } from "../services/api";

export interface TimelineItem {
  date: string;
  title: string;
  summary: string;
}

export interface UseTimelineReturn {
  keywords: string;
  setKeywords: (keywords: string) => void;
  dateFrom: string;
  setDateFrom: (date: string) => void;
  dateTo: string;
  setDateTo: (date: string) => void;
  timeline: TimelineItem[];
  isLoading: boolean;
  error: string | null;
  handleSubmit: (e: React.FormEvent) => Promise<void>;
  handleKeywordClick: (keyword: string) => void;
}

/**
 * 타임라인 데이터를 관리하는 커스텀 훅
 */
export const useTimeline = (): UseTimelineReturn => {
  const [keywords, setKeywords] = useState<string>("");
  const [dateFrom, setDateFrom] = useState<string>("");
  const [dateTo, setDateTo] = useState<string>("");
  const [timeline, setTimeline] = useState<TimelineItem[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // 타임라인 요청 처리
  const handleSubmit = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault();

    if (!keywords.trim()) return;

    setIsLoading(true);
    setError(null);
    setTimeline([]);

    try {
      const params: TimelineRequest = {
        keywords,
      };

      if (dateFrom) params.date_from = dateFrom;
      if (dateTo) params.date_to = dateTo;

      const response = await apiService.getTimeline(params);
      setTimeline(response.timeline);
    } catch (err) {
      console.error("Error:", err);
      setError(
        "타임라인 생성 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
      );
    } finally {
      setIsLoading(false);
    }
  };

  // 키워드 예시 클릭 처리
  const handleKeywordClick = (keyword: string): void => {
    setKeywords(keyword);
  };

  return {
    keywords,
    setKeywords,
    dateFrom,
    setDateFrom,
    dateTo,
    setDateTo,
    timeline,
    isLoading,
    error,
    handleSubmit,
    handleKeywordClick,
  };
};

export default useTimeline;
