import React, { useState } from "react";
import { Source } from "../../hooks/useQA";
import LoadingSpinner from "../common/LoadingSpinner";

interface AnswerDisplayProps {
  answer: string;
  sources: Source[];
  isLoading: boolean;
}

/**
 * 답변 표시 컴포넌트
 */
const AnswerDisplay: React.FC<AnswerDisplayProps> = ({
  answer,
  sources,
  isLoading,
}) => {
  const [expandedSource, setExpandedSource] = useState<number | null>(null);

  // 출처 토글 핸들러
  const toggleSource = (index: number) => {
    if (expandedSource === index) {
      setExpandedSource(null);
    } else {
      setExpandedSource(index);
    }
  };

  // 답변이 없고 로딩 중이 아닌 경우 빈 상태 표시
  if (!answer && !isLoading) {
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
            d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
          ></path>
        </svg>
        <h3 className="text-lg font-medium mb-2">
          질문을 입력하면 답변이 여기에 표시됩니다
        </h3>
        <p className="text-gray-500 dark:text-gray-400 max-w-md">
          왼쪽의 입력 폼에서 질문을 입력하거나 예시 질문을 클릭해보세요.
        </p>
      </div>
    );
  }

  // 로딩 중인 경우
  if (isLoading) {
    return (
      <div className="card">
        <div className="p-4">
          <LoadingSpinner text="답변 생성 중..." />
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <h2 className="text-xl font-semibold mb-4">답변</h2>
      <div className="prose dark:prose-invert max-w-none">
        <p className="whitespace-pre-line">{answer}</p>
      </div>

      {/* 출처 목록 */}
      {sources && sources.length > 0 && (
        <div className="mt-8 border-t border-gray-200 dark:border-gray-700 pt-4">
          <h3 className="text-lg font-medium mb-4">출처 ({sources.length})</h3>
          <div className="space-y-4">
            {sources.map((source, index) => (
              <div
                key={index}
                className="bg-gray-50 dark:bg-gray-800 rounded-lg overflow-hidden border border-gray-200 dark:border-gray-700"
              >
                <div
                  className="px-4 py-3 cursor-pointer flex justify-between items-center hover:bg-gray-100 dark:hover:bg-gray-700"
                  onClick={() => toggleSource(index)}
                >
                  <h4 className="font-medium">{source.title}</h4>
                  <svg
                    className={`w-5 h-5 transition-transform ${
                      expandedSource === index ? "transform rotate-180" : ""
                    }`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M19 9l-7 7-7-7"
                    ></path>
                  </svg>
                </div>
                {expandedSource === index && (
                  <div className="px-4 py-3 border-t border-gray-200 dark:border-gray-700 text-sm">
                    <div className="mb-2">
                      <a
                        href={source.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primary-600 dark:text-primary-400 hover:underline"
                      >
                        원문 링크
                      </a>
                    </div>
                    <div className="mt-2 bg-white dark:bg-gray-900 p-3 rounded border border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300 text-sm max-h-40 overflow-y-auto">
                      {source.content}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default AnswerDisplay;
