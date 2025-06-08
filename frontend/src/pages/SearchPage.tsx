import React, { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { motion } from "framer-motion";
import { containerVariants, itemVariants } from "../animations/pageAnimations";
import LoadingSpinner from "../components/common/LoadingSpinner";
import ErrorMessage from "../components/common/ErrorMessage";
import RelatedQuestions from "../components/common/RelatedQuestions";
import NewsArticleCard from "../components/news/NewsArticleCard";
import SearchForm from "../components/forms/SearchForm";
import { NewsArticle } from "../services/api";

interface Question {
  question: string;
  query: string;
  type: string;
}

const SearchPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const query = searchParams.get("q") || "";
  const dateFrom = searchParams.get("from") || "";
  const dateTo = searchParams.get("to") || "";

  const [searchResults, setSearchResults] = useState<NewsArticle[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [totalResults, setTotalResults] = useState(0);
  const [currentQuery, setCurrentQuery] = useState(query);
  const [currentQuestion, setCurrentQuestion] = useState<string | null>(null);

  // 검색 실행
  const performSearch = async (
    searchQuery: string,
    question: string | null = null
  ) => {
    if (!searchQuery) return;

    setIsLoading(true);
    setError(null);
    setCurrentQuery(searchQuery);
    if (question) setCurrentQuestion(question);

    try {
      // 검색 쿼리에 따라 엔드포인트 결정
      let url = "";
      if (question) {
        // 질문 검색 API 사용
        url = `/api/news/search-by-question?query=${encodeURIComponent(
          searchQuery
        )}&question=${encodeURIComponent(question)}`;
      } else {
        // 일반 검색 API 사용
        url = `/api/news/search/news?keyword=${encodeURIComponent(
          searchQuery
        )}`;
      }

      // 날짜 파라미터 추가
      if (dateFrom) {
        url += `&date_from=${dateFrom}`;
      }
      if (dateTo) {
        url += `&date_to=${dateTo}`;
      }

      const response = await fetch(url);

      if (!response.ok) {
        throw new Error("검색 결과를 불러오는데 실패했습니다");
      }

      const data = await response.json();

      if (data.success) {
        setSearchResults(data.articles || []);
        setTotalResults(data.total_count || 0);
      } else {
        setError(data.error || "검색 결과를 불러올 수 없습니다");
        setSearchResults([]);
        setTotalResults(0);
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "알 수 없는 오류가 발생했습니다"
      );
      setSearchResults([]);
      setTotalResults(0);
    } finally {
      setIsLoading(false);
    }
  };

  // 초기 검색 및 URL 변경 시 검색
  useEffect(() => {
    if (query) {
      performSearch(query);
    }
  }, [query, dateFrom, dateTo]);

  // 검색 폼 제출 핸들러
  const handleSearch = (
    searchQuery: string,
    fromDate?: string,
    toDate?: string
  ) => {
    const params: Record<string, string> = { q: searchQuery };
    if (fromDate) params.from = fromDate;
    if (toDate) params.to = toDate;

    setSearchParams(params);
  };

  // 연관 질문 클릭 핸들러
  const handleQuestionClick = (question: Question) => {
    performSearch(question.query, question.question);

    // URL 업데이트 (원래 검색어는 유지)
    setSearchParams((prev) => {
      const newParams = new URLSearchParams(prev);
      newParams.set("related_query", question.query);
      newParams.set("question", question.question);
      return newParams;
    });
  };

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={containerVariants}
      className="container mx-auto py-8 px-4"
    >
      <motion.div variants={itemVariants}>
        <h1 className="text-3xl font-bold mb-6">뉴스 검색</h1>

        <SearchForm
          initialQuery={query}
          initialDateFrom={dateFrom}
          initialDateTo={dateTo}
          onSearch={handleSearch}
        />
      </motion.div>

      {currentQuery && (
        <motion.div variants={itemVariants} className="mt-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold">검색 결과</h2>
            <p className="text-sm text-gray-500">
              {currentQuestion ? (
                <>
                  질문: <span className="italic">{currentQuestion}</span>
                </>
              ) : (
                <>
                  검색어: <span className="font-medium">{currentQuery}</span>
                </>
              )}
              {totalResults > 0 && ` (총 ${totalResults}건)`}
            </p>
          </div>

          {isLoading ? (
            <div className="flex justify-center py-12">
              <LoadingSpinner />
            </div>
          ) : error ? (
            <ErrorMessage message={error} />
          ) : searchResults.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-gray-500">검색 결과가 없습니다.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {searchResults.map((article) => (
                <NewsArticleCard
                  key={article.id}
                  article={article}
                  useNavigationInsteadOfModal={true}
                />
              ))}
            </div>
          )}

          {/* 연관 질문 컴포넌트 */}
          {currentQuery && !isLoading && searchResults.length > 0 && (
            <RelatedQuestions
              keyword={currentQuery}
              onQuestionClick={handleQuestionClick}
              className="mt-8"
            />
          )}
        </motion.div>
      )}
    </motion.div>
  );
};

export default SearchPage;
