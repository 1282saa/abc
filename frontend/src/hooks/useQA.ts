import { useState } from "react";
import apiService, { QARequest, QAResponse } from "../services/api";

export interface Source {
  title: string;
  url: string;
  content: string;
}

export interface UseQAReturn {
  query: string;
  setQuery: (query: string) => void;
  answer: string;
  sources: Source[];
  isLoading: boolean;
  error: string | null;
  handleSubmit: (e: React.FormEvent) => Promise<void>;
  useSources: boolean;
  setUseSources: (value: boolean) => void;
}

/**
 * QA 기능을 관리하는 커스텀 훅
 */
export const useQA = (): UseQAReturn => {
  const [query, setQuery] = useState<string>("");
  const [answer, setAnswer] = useState<string>("");
  const [sources, setSources] = useState<Source[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [useSources, setUseSources] = useState<boolean>(true);

  // QA 요청 처리
  const handleSubmit = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault();

    if (!query.trim()) return;

    setIsLoading(true);
    setError(null);
    setAnswer("");
    setSources([]);

    try {
      const params: QARequest = {
        query: query.trim(),
        use_sources: useSources,
      };

      const response = await apiService.getAnswer(params);
      setAnswer(response.answer);
      setSources(response.sources || []);
    } catch (err) {
      console.error("Error:", err);
      setError(
        "질문에 대한 답변을 생성하는 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
      );
    } finally {
      setIsLoading(false);
    }
  };

  return {
    query,
    setQuery,
    answer,
    sources,
    isLoading,
    error,
    handleSubmit,
    useSources,
    setUseSources,
  };
};

export default useQA;
