import { useState } from "react";
import apiService, { SummaryRequest, SummaryResponse } from "../services/api";

export interface UseSummaryReturn {
  url: string;
  setUrl: (url: string) => void;
  title: string;
  originalText: string;
  summary: string;
  keywords: string[];
  isLoading: boolean;
  error: string | null;
  handleSubmit: (e: React.FormEvent) => Promise<void>;
}

/**
 * 요약 기능을 관리하는 커스텀 훅
 */
export const useSummary = (): UseSummaryReturn => {
  const [url, setUrl] = useState<string>("");
  const [title, setTitle] = useState<string>("");
  const [originalText, setOriginalText] = useState<string>("");
  const [summary, setSummary] = useState<string>("");
  const [keywords, setKeywords] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // 요약 요청 처리
  const handleSubmit = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault();

    if (!url.trim()) return;

    setIsLoading(true);
    setError(null);
    setTitle("");
    setOriginalText("");
    setSummary("");
    setKeywords([]);

    try {
      const params: SummaryRequest = {
        url: url.trim(),
      };

      const response = await apiService.getSummary(params);
      setTitle(response.title);
      setOriginalText(response.original_text);
      setSummary(response.summary);
      setKeywords(response.keywords);
    } catch (err) {
      console.error("Error:", err);
      setError(
        "요약을 생성하는 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
      );
    } finally {
      setIsLoading(false);
    }
  };

  return {
    url,
    setUrl,
    title,
    originalText,
    summary,
    keywords,
    isLoading,
    error,
    handleSubmit,
  };
};

export default useSummary;
