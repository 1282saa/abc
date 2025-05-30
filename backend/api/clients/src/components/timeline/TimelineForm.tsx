import React from "react";
import KeywordChips from "../common/KeywordChips";

interface TimelineFormProps {
  keywords: string;
  dateFrom: string;
  dateTo: string;
  isLoading: boolean;
  setKeywords: (value: string) => void;
  setDateFrom: (value: string) => void;
  setDateTo: (value: string) => void;
  handleSubmit: (e: React.FormEvent) => Promise<void>;
  handleKeywordClick: (keyword: string) => void;
}

// 키워드 예시
const keywordExamples = [
  "코로나19",
  "우크라이나 전쟁",
  "올림픽",
  "대통령 선거",
];

/**
 * 타임라인 검색 폼 컴포넌트
 */
const TimelineForm: React.FC<TimelineFormProps> = ({
  keywords,
  dateFrom,
  dateTo,
  isLoading,
  setKeywords,
  setDateFrom,
  setDateTo,
  handleSubmit,
  handleKeywordClick,
}) => {
  return (
    <div className="card">
      <h2 className="text-xl font-semibold mb-4">키워드 입력</h2>
      <form onSubmit={handleSubmit}>
        <div className="mb-4">
          <label
            htmlFor="keywords"
            className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
          >
            키워드
          </label>
          <input
            id="keywords"
            type="text"
            className="input w-full"
            placeholder="예: 우크라이나 전쟁"
            value={keywords}
            onChange={(e) => setKeywords(e.target.value)}
            disabled={isLoading}
          />
        </div>

        <div className="mb-4">
          <label
            htmlFor="dateFrom"
            className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
          >
            시작 날짜 (선택)
          </label>
          <input
            id="dateFrom"
            type="date"
            className="input w-full"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
            disabled={isLoading}
          />
        </div>

        <div className="mb-6">
          <label
            htmlFor="dateTo"
            className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
          >
            종료 날짜 (선택)
          </label>
          <input
            id="dateTo"
            type="date"
            className="input w-full"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
            disabled={isLoading}
          />
        </div>

        <button
          type="submit"
          className="btn-primary w-full"
          disabled={isLoading || !keywords.trim()}
        >
          {isLoading ? "타임라인 생성 중..." : "타임라인 생성"}
        </button>
      </form>

      <div className="mt-6">
        <h3 className="text-md font-medium mb-2">키워드 예시</h3>
        <KeywordChips
          keywords={keywordExamples}
          onKeywordClick={handleKeywordClick}
        />
      </div>
    </div>
  );
};

export default TimelineForm;
