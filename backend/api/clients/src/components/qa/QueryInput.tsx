import React from "react";

interface QueryInputProps {
  query: string;
  setQuery: (query: string) => void;
  handleSubmit: (e: React.FormEvent) => Promise<void>;
  isLoading: boolean;
  useSources: boolean;
  setUseSources: (value: boolean) => void;
}

/**
 * 질문 입력 컴포넌트
 */
const QueryInput: React.FC<QueryInputProps> = ({
  query,
  setQuery,
  handleSubmit,
  isLoading,
  useSources,
  setUseSources,
}) => {
  // 예시 질문들
  const exampleQueries = [
    "최근 반도체 산업 동향은 어떻게 되나요?",
    "대한민국 금리 인상이 부동산 시장에 미치는 영향은?",
    "올해 서울 지역 부동산 가격 추이는 어떻게 되나요?",
    "최근 인공지능 기술 발전 동향에 대해 알려주세요.",
  ];

  // 예시 질문 선택 핸들러
  const handleExampleClick = (example: string) => {
    setQuery(example);
  };

  return (
    <div className="card">
      <h2 className="text-xl font-semibold mb-4">질문하기</h2>

      <form onSubmit={handleSubmit}>
        <div className="mb-4">
          <label
            htmlFor="query"
            className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
          >
            질문
          </label>
          <textarea
            id="query"
            className="input w-full min-h-[100px] resize-y"
            placeholder="뉴스 데이터에 대한 질문을 입력하세요..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            disabled={isLoading}
          />
        </div>

        <div className="mb-4 flex items-center">
          <input
            type="checkbox"
            id="useSources"
            className="h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500 dark:focus:ring-primary-400"
            checked={useSources}
            onChange={(e) => setUseSources(e.target.checked)}
            disabled={isLoading}
          />
          <label
            htmlFor="useSources"
            className="ml-2 block text-sm text-gray-700 dark:text-gray-300"
          >
            출처 정보 포함하기
          </label>
        </div>

        <button
          type="submit"
          className="btn-primary w-full"
          disabled={isLoading || !query.trim()}
        >
          {isLoading ? "답변 생성 중..." : "질문하기"}
        </button>
      </form>

      <div className="mt-6">
        <h3 className="text-md font-medium mb-2">예시 질문</h3>
        <div className="space-y-2">
          {exampleQueries.map((example, index) => (
            <button
              key={index}
              onClick={() => handleExampleClick(example)}
              disabled={isLoading}
              className="block w-full text-left p-2 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 rounded text-sm text-gray-700 dark:text-gray-300"
            >
              {example}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default QueryInput;
