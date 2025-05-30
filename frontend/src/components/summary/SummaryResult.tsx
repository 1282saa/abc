import React, { useState } from "react";
import LoadingSpinner from "../common/LoadingSpinner";
import KeywordChips from "../common/KeywordChips";

interface SummaryResultProps {
  title: string;
  originalText: string;
  summary: string;
  keywords: string[];
  isLoading: boolean;
}

/**
 * 요약 결과 표시 컴포넌트
 */
const SummaryResult: React.FC<SummaryResultProps> = ({
  title,
  originalText,
  summary,
  keywords,
  isLoading,
}) => {
  const [tab, setTab] = useState<"summary" | "original">("summary");

  // 탭이 없고 로딩 중이 아닌 경우 빈 상태 표시
  if (!summary && !originalText && !isLoading) {
    return (
      <div className="card min-h-[300px] flex flex-col items-center justify-center text-center p-8">
        <svg
          className="w-16 h-16 text-gray-400 dark:text-gray-600 mb-4"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
          ></path>
        </svg>
        <h3 className="text-lg font-medium mb-2">
          URL을 입력하면 요약 결과가 여기에 표시됩니다
        </h3>
        <p className="text-gray-500 dark:text-gray-400 max-w-md">
          왼쪽의 입력 폼에서 뉴스 기사 URL을 입력하거나 예시 URL을 클릭해보세요.
        </p>
      </div>
    );
  }

  // 로딩 중인 경우
  if (isLoading) {
    return (
      <div className="card">
        <div className="p-4">
          <LoadingSpinner text="요약 생성 중..." />
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      {/* 제목 */}
      {title && (
        <div className="mb-6">
          <h2 className="text-xl font-semibold">{title}</h2>
          {keywords.length > 0 && (
            <div className="mt-3">
              <KeywordChips keywords={keywords} />
            </div>
          )}
        </div>
      )}

      {/* 탭 네비게이션 */}
      <div className="flex border-b border-gray-200 dark:border-gray-700 mb-4">
        <button
          className={`py-2 px-4 font-medium text-sm focus:outline-none ${
            tab === "summary"
              ? "border-b-2 border-primary-600 dark:border-primary-400 text-primary-600 dark:text-primary-400"
              : "text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
          }`}
          onClick={() => setTab("summary")}
        >
          요약
        </button>
        <button
          className={`py-2 px-4 font-medium text-sm focus:outline-none ${
            tab === "original"
              ? "border-b-2 border-primary-600 dark:border-primary-400 text-primary-600 dark:text-primary-400"
              : "text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
          }`}
          onClick={() => setTab("original")}
        >
          원문
        </button>
      </div>

      {/* 콘텐츠 */}
      <div className="prose dark:prose-invert max-w-none">
        {tab === "summary" && <p className="whitespace-pre-line">{summary}</p>}
        {tab === "original" && (
          <div>
            <p className="whitespace-pre-line text-gray-700 dark:text-gray-300">
              {originalText}
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default SummaryResult;
