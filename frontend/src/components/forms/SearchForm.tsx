import React, { useState } from "react";

interface SearchFormProps {
  initialQuery?: string;
  initialDateFrom?: string;
  initialDateTo?: string;
  onSearch: (query: string, dateFrom?: string, dateTo?: string) => void;
}

const SearchForm: React.FC<SearchFormProps> = ({
  initialQuery = "",
  initialDateFrom = "",
  initialDateTo = "",
  onSearch,
}) => {
  const [query, setQuery] = useState(initialQuery);
  const [dateFrom, setDateFrom] = useState(initialDateFrom);
  const [dateTo, setDateTo] = useState(initialDateTo);
  const [showDateFilter, setShowDateFilter] = useState(
    !!initialDateFrom || !!initialDateTo
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      onSearch(query.trim(), dateFrom, dateTo);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="flex flex-col md:flex-row gap-2">
        <div className="flex-1">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="검색어를 입력하세요"
            className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 dark:bg-gray-800 dark:text-white"
            required
          />
        </div>
        <button
          type="submit"
          className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
        >
          검색
        </button>
        <button
          type="button"
          className="px-3 py-2 text-gray-600 dark:text-gray-300 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          onClick={() => setShowDateFilter(!showDateFilter)}
        >
          <svg
            className="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
            />
          </svg>
        </button>
      </div>

      {showDateFilter && (
        <div className="flex flex-col md:flex-row gap-4 items-center bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
          <div className="flex items-center">
            <label
              htmlFor="date-from"
              className="text-sm mr-2 whitespace-nowrap"
            >
              시작일:
            </label>
            <input
              id="date-from"
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              className="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white"
            />
          </div>
          <div className="flex items-center">
            <label htmlFor="date-to" className="text-sm mr-2 whitespace-nowrap">
              종료일:
            </label>
            <input
              id="date-to"
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              className="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white"
            />
          </div>
          <button
            type="button"
            onClick={() => {
              setDateFrom("");
              setDateTo("");
            }}
            className="text-sm text-gray-600 dark:text-gray-400 hover:text-red-500 dark:hover:text-red-400 transition-colors"
          >
            날짜 초기화
          </button>
        </div>
      )}
    </form>
  );
};

export default SearchForm;
