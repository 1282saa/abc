import React from "react";

interface UrlInputProps {
  url: string;
  setUrl: (url: string) => void;
  handleSubmit: (e: React.FormEvent) => Promise<void>;
  isLoading: boolean;
}

/**
 * 요약할 URL 입력 컴포넌트
 */
const UrlInput: React.FC<UrlInputProps> = ({
  url,
  setUrl,
  handleSubmit,
  isLoading,
}) => {
  // 예시 URL들
  const exampleUrls = [
    "https://www.sedaily.com/NewsView/29YPQNTAQV",
    "https://www.sedaily.com/NewsView/29YNO8VDAD",
    "https://www.sedaily.com/NewsView/29YPOJ6JOQ",
  ];

  // 예시 URL 선택 핸들러
  const handleExampleClick = (exampleUrl: string) => {
    setUrl(exampleUrl);
  };

  return (
    <div className="card">
      <h2 className="text-xl font-semibold mb-4">URL 입력</h2>

      <form onSubmit={handleSubmit}>
        <div className="mb-4">
          <label
            htmlFor="url"
            className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
          >
            뉴스 URL
          </label>
          <input
            id="url"
            type="url"
            className="input w-full"
            placeholder="https://..."
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            disabled={isLoading}
          />
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            요약할 뉴스 기사 URL을 입력하세요.
          </p>
        </div>

        <button
          type="submit"
          className="btn-primary w-full"
          disabled={isLoading || !url.trim()}
        >
          {isLoading ? "요약 생성 중..." : "기사 요약하기"}
        </button>
      </form>

      <div className="mt-6">
        <h3 className="text-md font-medium mb-2">예시 URL</h3>
        <div className="space-y-2">
          {exampleUrls.map((exampleUrl, index) => (
            <button
              key={index}
              onClick={() => handleExampleClick(exampleUrl)}
              disabled={isLoading}
              className="block w-full text-left p-2 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 rounded text-sm text-gray-700 dark:text-gray-300 truncate"
            >
              {exampleUrl}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default UrlInput;
