import React, { useState, useEffect, useCallback, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Link, useNavigate } from "react-router-dom";
import { containerVariants, itemVariants } from "../animations/pageAnimations";
import LoadingSpinner from "../components/common/LoadingSpinner";
import ErrorMessage from "../components/common/ErrorMessage";
import ChatInterface from "../components/chat/ChatInterface";
import {
  getLatestNews,
  type LatestNewsResponse,
  type IssueTopic,
  type PopularKeyword,
} from "../services/api";
import {
  getConciergeBriefing,
  ConciergeBriefingResponse,
  searchArticles,
} from "../services/briefingApi";
import NetworkGraph from "../components/visualization/NetworkGraph";
import { getArticleLink, getNewsDetail } from "../services/newsApi";

interface NewsItem {
  id?: string;
  topic_id?: string;
  title: string;
  summary?: string;
  content?: string;
  provider: string;
  date: string;
  category: string;
  url?: string;
  published_at?: string;
}

interface TabProps {
  label: string;
  isActive: boolean;
  onClick: () => void;
}

const Tab: React.FC<TabProps> = ({ label, isActive, onClick }) => (
  <button
    onClick={onClick}
    role="tab"
    aria-selected={isActive}
    aria-controls={`tabpanel-${label.replace(/\s+/g, "-").toLowerCase()}`}
    className={`relative px-4 sm:px-6 py-3 font-medium transition-all duration-300 rounded-t-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 ${
      isActive
        ? "text-primary-600 dark:text-primary-400 bg-primary-50 dark:bg-primary-900/20"
        : "text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-800"
    }`}
  >
    {label}
    {isActive && (
      <motion.div
        layoutId="activeTab"
        className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-primary-500 to-secondary-500 rounded-full"
        transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
      />
    )}
  </button>
);

const NewsCard: React.FC<{ item: NewsItem }> = ({ item }) => {
  const navigate = useNavigate();

  const handleCardClick = async () => {
    if (!item.id) return;

    try {
      // 뉴스 상세 정보 조회하여 외부 링크 가져오기
      const newsDetail = await getNewsDetail(item.id);
      if (newsDetail.success && newsDetail.news) {
        const externalLink = getArticleLink(newsDetail.news);
        // 외부 링크로 이동
        window.open(externalLink, '_blank', 'noopener,noreferrer');
      } else {
        // 상세 정보를 가져올 수 없으면 내부 페이지로 이동
        navigate(`/news/${item.id}`);
      }
    } catch (error) {
      console.error('뉴스 상세 정보 조회 실패:', error);
      // 오류 발생 시 내부 페이지로 이동
      navigate(`/news/${item.id}`);
    }
  };

  return (
    <motion.div
      variants={itemVariants}
      whileHover={{
        y: -4,
        transition: { type: "spring", stiffness: 300, damping: 20 },
      }}
      className="group relative bg-white dark:bg-gray-800 rounded-xl shadow-md hover:shadow-xl transition-all duration-300 cursor-pointer overflow-hidden border border-gray-100 dark:border-gray-700"
      onClick={handleCardClick}
    >
      {/* 그라데이션 보더 효과 */}
      <div className="absolute inset-0 bg-gradient-to-r from-primary-500/20 to-secondary-500/20 opacity-0 group-hover:opacity-100 transition-opacity duration-300 rounded-xl" />

      <div className="relative p-6">
        <div className="flex items-start justify-between mb-4">
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-primary-50 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 border border-primary-200 dark:border-primary-800">
            {item.provider}
          </span>
          <time className="text-xs text-gray-500 dark:text-gray-400 font-mono">
            {item.date}
          </time>
        </div>

        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3 line-clamp-2 group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors">
          {item.title}
        </h3>

        {item.summary && (
          <p className="text-gray-600 dark:text-gray-400 text-sm mb-4 line-clamp-3 leading-relaxed">
            {item.summary}
          </p>
        )}

        <div className="flex items-center justify-between">
          <span className="inline-flex items-center text-xs text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 px-3 py-1.5 rounded-full font-medium">
            #{item.category}
          </span>
          <button
            onClick={async (e) => {
              e.stopPropagation();
              if (!item.id) return;

              try {
                // 뉴스 상세 정보 조회하여 외부 링크 가져오기
                const newsDetail = await getNewsDetail(item.id);
                if (newsDetail.success && newsDetail.news) {
                  const externalLink = getArticleLink(newsDetail.news);
                  // 외부 링크로 이동
                  window.open(externalLink, '_blank', 'noopener,noreferrer');
                } else {
                  // 상세 정보를 가져올 수 없으면 내부 페이지로 이동
                  navigate(`/news/${item.id}`);
                }
              } catch (error) {
                console.error('뉴스 상세 정보 조회 실패:', error);
                // 오류 발생 시 내부 페이지로 이동
                navigate(`/news/${item.id}`);
              }
            }}
            className="inline-flex items-center text-sm text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 font-medium transition-colors"
          >
            자세히 보기
            <svg
              className="w-4 h-4 ml-1 transition-transform group-hover:translate-x-1"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 5l7 7-7 7"
              />
            </svg>
          </button>
        </div>
      </div>
    </motion.div>
  );
};

const IssueCard: React.FC<{ item: IssueTopic }> = ({ item }) => {
  const [showDetails, setShowDetails] = useState(false);

  return (
    <motion.div
      variants={itemVariants}
      className="group relative bg-white dark:bg-gray-800 rounded-xl shadow-md hover:shadow-xl transition-all duration-300 cursor-pointer overflow-hidden border border-gray-100 dark:border-gray-700"
      whileHover={{
        y: -2,
        transition: { type: "spring", stiffness: 300, damping: 20 },
      }}
      onClick={() => setShowDetails(!showDetails)}
    >
      {/* 랭킹 배지 */}
      <div className="absolute top-4 left-4 w-12 h-12 bg-gradient-to-br from-primary-500 to-secondary-500 rounded-full flex items-center justify-center text-white font-bold text-lg shadow-lg">
        {item.rank}
      </div>

      {/* 메인 콘텐츠 */}
      <div className="pt-20 p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2 pr-4 group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors">
              {item.title || item.topic_name}
            </h3>
          </div>
          <div className="flex flex-col items-end space-y-2">
            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/30 dark:to-indigo-900/30 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800">
              <svg
                className="w-3 h-3 mr-1"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  d="M2 5a2 2 0 012-2h12a2 2 0 012 2v2a2 2 0 01-2 2H4a2 2 0 01-2-2V5zm14 1a1 1 0 11-2 0 1 1 0 012 0zM2 13a2 2 0 012-2h12a2 2 0 012 2v2a2 2 0 01-2 2H4a2 2 0 01-2-2v-2zm14 1a1 1 0 11-2 0 1 1 0 012 0z"
                  clipRule="evenodd"
                />
              </svg>
              {item.count}건
            </span>
          </div>
        </div>

        {/* 상세 정보 토글 버튼 */}
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600 dark:text-gray-400">
            뉴스 기사 {item.count}개 수집됨
          </span>
          <button className="inline-flex items-center text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 font-medium transition-colors">
            {showDetails ? (
              <>
                접기
                <svg
                  className="w-4 h-4 ml-1 transition-transform"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M5 15l7-7 7 7"
                  />
                </svg>
              </>
            ) : (
              <>
                언론사별 보기
                <svg
                  className="w-4 h-4 ml-1 transition-transform"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M19 9l-7 7-7-7"
                  />
                </svg>
              </>
            )}
          </button>
        </div>

        {/* 언론사별 breakdown (토글) */}
        <AnimatePresence>
          {showDetails &&
            item.provider_breakdown &&
            item.provider_breakdown.length > 0 && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.3, ease: "easeInOut" }}
                className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-700"
              >
                <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4 flex items-center">
                  <svg
                    className="w-4 h-4 mr-2 text-primary-500"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M2 5a2 2 0 012-2h12a2 2 0 012 2v2a2 2 0 01-2 2H4a2 2 0 01-2-2V5zm14 1a1 1 0 11-2 0 1 1 0 012 0zM2 13a2 2 0 012-2h12a2 2 0 012 2v2a2 2 0 01-2 2H4a2 2 0 01-2-2v-2zm14 1a1 1 0 11-2 0 1 1 0 012 0z"
                      clipRule="evenodd"
                    />
                  </svg>
                  언론사별 보도 현황
                </h4>
                <div className="grid grid-cols-1 gap-2 max-h-40 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-300 dark:scrollbar-thumb-gray-600">
                  {item.provider_breakdown?.map(
                    (provider: any, index: number) => (
                      <motion.div
                        key={provider.provider_code}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.05 }}
                        className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg border border-gray-100 dark:border-gray-600"
                      >
                        <span className="font-medium text-gray-700 dark:text-gray-300 text-sm">
                          {provider.provider}
                        </span>
                        <div className="flex items-center space-x-2">
                          <span className="text-primary-600 dark:text-primary-400 font-bold text-sm">
                            {provider.count}건
                          </span>
                          <div className="w-12 h-2 bg-gray-200 dark:bg-gray-600 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-gradient-to-r from-primary-500 to-secondary-500 rounded-full transition-all duration-500"
                              style={{
                                width: `${Math.min(
                                  (provider.count /
                                    Math.max(
                                      ...(item.provider_breakdown?.map(
                                        (p: any) => p.count
                                      ) || [1])
                                    )) *
                                    100,
                                  100
                                )}%`,
                              }}
                            />
                          </div>
                        </div>
                      </motion.div>
                    )
                  )}
                </div>
              </motion.div>
            )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
};

const KeywordTag: React.FC<{ item: PopularKeyword }> = ({ item }) => {
  const getTrendIcon = (trend?: string) => {
    switch (trend) {
      case "up":
        return (
          <svg
            className="w-4 h-4 text-green-500"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fillRule="evenodd"
              d="M3.293 9.707a1 1 0 010-1.414l6-6a1 1 0 011.414 0l6 6a1 1 0 01-1.414 1.414L11 5.414V17a1 1 0 11-2 0V5.414L4.707 9.707a1 1 0 01-1.414 0z"
              clipRule="evenodd"
            />
          </svg>
        );
      case "down":
        return (
          <svg
            className="w-4 h-4 text-red-500"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fillRule="evenodd"
              d="M16.707 10.293a1 1 0 010 1.414l-6 6a1 1 0 01-1.414 0l-6-6a1 1 0 111.414-1.414L9 14.586V3a1 1 0 012 0v11.586l4.293-4.293a1 1 0 011.414 0z"
              clipRule="evenodd"
            />
          </svg>
        );
      case "new":
        return (
          <svg
            className="w-4 h-4 text-gray-400"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fillRule="evenodd"
              d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z"
              clipRule="evenodd"
            />
          </svg>
        );
      default:
        return (
          <svg
            className="w-4 h-4 text-gray-400"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fillRule="evenodd"
              d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z"
              clipRule="evenodd"
            />
          </svg>
        );
    }
  };

  const getTrendColor = (trend?: string) => {
    switch (trend) {
      case "up":
        return "from-green-50 to-emerald-50 dark:from-green-900/30 dark:to-emerald-900/30 border-green-200 dark:border-green-800 text-green-700 dark:text-green-300";
      case "down":
        return "from-red-50 to-rose-50 dark:from-red-900/30 dark:to-rose-900/30 border-red-200 dark:border-red-800 text-red-700 dark:text-red-300";
      case "new":
        return "border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-gray-700 dark:text-gray-300";
      default:
        return "from-primary-50 to-blue-50 dark:from-primary-900/30 dark:to-blue-900/30 border-primary-200 dark:border-primary-800 text-primary-700 dark:text-primary-300";
    }
  };

  return (
    <motion.div
      variants={itemVariants}
      whileHover={{
        scale: 1.05,
        y: -2,
        transition: { type: "spring", stiffness: 400, damping: 17 },
      }}
      whileTap={{ scale: 0.95 }}
      className={`group relative flex items-center space-x-2 px-4 py-2 rounded-full transition-all duration-300 cursor-pointer border ${getTrendColor(
        item.trend
      )}`}
    >
      {getTrendIcon(item.trend)}
      <span className="font-semibold text-sm">{item.keyword}</span>
    </motion.div>
  );
};

// AI 컨시어지 검색 결과 컴포넌트
const ConciergeResultDisplay: React.FC<{
  result: ConciergeBriefingResponse;
  onKeywordClick?: (keyword: string) => void;
}> = ({ result, onKeywordClick }) => {
  const [viewMode, setViewMode] = useState<"cards" | "network">("cards");
  const [sortOrder, setSortOrder] = useState<"date" | "score">("date");

  // 무한 스크롤을 위한 상태 관리
  const [allArticles, setAllArticles] = useState<any[]>([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [hasMoreArticles, setHasMoreArticles] = useState(true);
  const [totalHits, setTotalHits] = useState(0);
  const articlesPerPage = 10;
  const loadMoreRef = useRef<HTMLDivElement>(null);

  // 기사 정렬 함수
  const sortArticles = useCallback(
    (articles: any[], order: "date" | "score") => {
      return [...articles].sort((a, b) => {
        if (order === "date") {
          // 날짜순 정렬 (최신이 위로)
          const dateA = new Date(a.published_at).getTime();
          const dateB = new Date(b.published_at).getTime();
          return dateB - dateA;
        } else {
          // 정확도순 정렬 (score가 높은 순)
          return (b.score || 0) - (a.score || 0);
        }
      });
    },
    []
  );

  // 초기 기사 로드
  useEffect(() => {
    if (result.documents && result.documents.length > 0) {
      const sortedArticles = sortArticles(result.documents, sortOrder);
      setAllArticles(sortedArticles);
      setCurrentPage(1);
      setTotalHits(result.total_hits || result.documents.length);
      setHasMoreArticles(result.has_more || false);
    } else {
      setAllArticles([]);
      setCurrentPage(1);
      setTotalHits(0);
      setHasMoreArticles(false);
    }
  }, [result, sortOrder, sortArticles]);

  // 정렬 순서 변경 핸들러
  const handleSortChange = (newSortOrder: "date" | "score") => {
    setSortOrder(newSortOrder);
    // 현재 로드된 기사들을 새로운 순서로 정렬
    setAllArticles((prev) => sortArticles(prev, newSortOrder));
  };

  // 추가 기사 로드 함수 (실제 API 호출)
  const loadMoreArticles = useCallback(async () => {
    if (isLoadingMore || !hasMoreArticles || !result.query) return;

    setIsLoadingMore(true);

    try {
      console.log(`추가 기사 로드: 페이지 ${currentPage + 1}`);

      // 정렬 파라미터를 포함한 API 호출
      const sortParam =
        sortOrder === "date" ? "published_at:desc" : "_score:desc";

      // 실제 API 호출로 다음 페이지 기사 가져오기
      const nextPageResult = await getConciergeBriefing(
        result.query,
        currentPage + 1,
        articlesPerPage
      );

      if (nextPageResult.documents && nextPageResult.documents.length > 0) {
        const sortedNewArticles = sortArticles(
          nextPageResult.documents,
          sortOrder
        );

        setAllArticles((prev) => [...prev, ...sortedNewArticles]);
        setCurrentPage((prev) => prev + 1);
        setHasMoreArticles(nextPageResult.has_more || false);
        setTotalHits(nextPageResult.total_hits || totalHits);

        console.log(`${sortedNewArticles.length}개 기사 추가 로드됨`);
      } else {
        setHasMoreArticles(false);
        console.log("더 이상 로드할 기사가 없습니다");
      }
    } catch (error: any) {
      console.error("추가 기사 로드 실패:", error);
      setHasMoreArticles(false);
    } finally {
      setIsLoadingMore(false);
    }
  }, [
    currentPage,
    result.query,
    isLoadingMore,
    hasMoreArticles,
    totalHits,
    sortOrder,
    sortArticles,
  ]);

  // Intersection Observer 설정
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasMoreArticles && !isLoadingMore) {
          loadMoreArticles();
        }
      },
      { threshold: 0.1 }
    );

    if (loadMoreRef.current) {
      observer.observe(loadMoreRef.current);
    }

    return () => observer.disconnect();
  }, [loadMoreArticles, hasMoreArticles, isLoadingMore]);

  const handleKeywordClick = (keyword: string) => {
    if (onKeywordClick) {
      onKeywordClick(keyword);
    }
  };

  // 하이라이트 텍스트 렌더링 함수
  const renderHighlightedText = (
    text: string,
    hilight?: string
  ): JSX.Element => {
    if (!hilight) {
      return <span>{text}</span>;
    }

    // 하이라이트 태그를 실제 HTML로 변환
    const highlightedHtml = hilight
      .replace(/<em>/g, '<mark class="bg-yellow-200 dark:bg-yellow-800">')
      .replace(/<\/em>/g, "</mark>");

    return <span dangerouslySetInnerHTML={{ __html: highlightedHtml }} />;
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.5 }}
      className="mt-12 bg-white dark:bg-gray-800 rounded-2xl shadow-lg border border-gray-200 dark:border-gray-700 p-8"
    >
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center">
          <div className="w-12 h-12 bg-gradient-to-r from-primary-500 to-secondary-500 rounded-full flex items-center justify-center mr-4">
            <svg
              className="w-7 h-7 text-white"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 4v16m8-8H4"
              />
            </svg>
          </div>
          <div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
              AI 뉴스 컨시어지 답변
            </h2>
            <p className="text-gray-600 dark:text-gray-400">
              "{result.query}"에 대한 검색 결과입니다.
            </p>
          </div>
        </div>

        {/* 뷰 모드 전환 버튼 */}
        <div className="flex bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
          <button
            onClick={() => setViewMode("cards")}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
              viewMode === "cards"
                ? "bg-white dark:bg-gray-800 text-gray-900 dark:text-white shadow-sm"
                : "text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
            }`}
          >
            📋 카드 뷰
          </button>
          {result.network_data &&
            result.network_data.nodes &&
            result.network_data.nodes.length > 0 && (
              <button
                onClick={() => setViewMode("network")}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
                  viewMode === "network"
                    ? "bg-white dark:bg-gray-800 text-gray-900 dark:text-white shadow-sm"
                    : "text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
                }`}
              >
                🕸️ 연결망
              </button>
            )}
        </div>
      </div>

      <div className="prose dark:prose-invert max-w-none mb-8 p-6 bg-gray-50 dark:bg-gray-900/50 rounded-lg border border-gray-200 dark:border-gray-700">
        <p className="text-lg leading-relaxed">{result.summary}</p>
      </div>

      {/* FAQ 답변 표시 */}
      {result.points && result.points.length > 0 && (
        <div className="mb-8">
          <h3 className="text-xl font-semibold text-gray-800 dark:text-gray-200 mb-6 flex items-center">
            <span className="bg-gradient-to-r from-primary-500 to-secondary-500 text-transparent bg-clip-text">
              💡 AI 분석 FAQ
            </span>
          </h3>
          <div className="space-y-4">
            {result.points.map((point: any, index: number) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="p-6 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm hover:shadow-md transition-shadow"
              >
                <div className="mb-3">
                  <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                    {point.question}
                  </h4>
                  <div className="flex items-start justify-between">
                    <p className="text-gray-700 dark:text-gray-300 leading-relaxed flex-1">
                      {point.answer}
                    </p>
                    {/* 인용 표시 */}
                    {point.citations && point.citations.length > 0 && (
                      <div className="ml-4 flex flex-wrap gap-1">
                        {point.citations.map((citation: number, citationIndex: number) => (
                          <button
                            key={citationIndex}
                            onClick={() => {
                              // 해당 기사로 스크롤
                              const articleElement = document.getElementById(`article-${citation - 1}`);
                              if (articleElement) {
                                articleElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
                                // 하이라이트 효과
                                articleElement.classList.add('ring-2', 'ring-primary-300', 'ring-opacity-75');
                                setTimeout(() => {
                                  articleElement.classList.remove('ring-2', 'ring-primary-300', 'ring-opacity-75');
                                }, 2000);
                              }
                            }}
                            className="inline-flex items-center px-2 py-1 text-xs font-mono bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 rounded-md hover:bg-primary-200 dark:hover:bg-primary-900/50 transition-colors cursor-pointer"
                            title={`기사 ${citation}번 보기`}
                          >
                            [{citation}]
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {/* 키워드 표시 */}
      {result.keywords && result.keywords.length > 0 && (
        <div className="mb-8">
          <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-4">
            주요 키워드
          </h3>
          <div className="flex flex-wrap gap-2">
            {result.keywords
              .slice(0, 10)
              .map(
                (
                  keyword: { keyword: string; count: number; weight: number },
                  index: number
                ) => (
                  <button
                    key={index}
                    onClick={() => handleKeywordClick(keyword.keyword)}
                    className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-700 hover:bg-blue-100 dark:hover:bg-blue-900/50 transition-colors cursor-pointer"
                    style={{
                      fontSize: `${0.8 + keyword.weight * 0.4}rem`,
                      opacity: 0.7 + keyword.weight * 0.3,
                    }}
                    title={`"${keyword.keyword}"로 새로 검색하기`}
                  >
                    {keyword.keyword}
                    <span className="ml-1 text-xs opacity-75">
                      ({keyword.count})
                    </span>
                  </button>
                )
              )}
          </div>
        </div>
      )}

      {/* 네트워크 뷰 또는 카드 뷰 */}
      <AnimatePresence mode="wait">
        {viewMode === "network" &&
        result.network_data &&
        result.network_data.nodes &&
        result.network_data.nodes.length > 0 ? (
          <motion.div
            key="network"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.3 }}
          >
            <NetworkGraph
              data={result.network_data}
              width={window.innerWidth > 768 ? 800 : window.innerWidth - 100}
              height={500}
              onNodeDoubleClick={(node) => {
                if (node.type === "keyword" && onKeywordClick) {
                  onKeywordClick(node.name);
                }
              }}
            />
          </motion.div>
        ) : (
          <motion.div
            key="cards"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.3 }}
            className="max-h-[600px] overflow-y-auto"
          >
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-semibold text-gray-800 dark:text-gray-200">
                관련 뉴스 기사
              </h3>
              <div className="flex items-center space-x-4">
                <div className="flex bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
                  <button
                    onClick={() => handleSortChange("date")}
                    className={`px-3 py-1 rounded-md text-xs font-medium transition-all ${
                      sortOrder === "date"
                        ? "bg-white dark:bg-gray-800 text-gray-900 dark:text-white shadow-sm"
                        : "text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
                    }`}
                  >
                    📅 최신순
                  </button>
                  <button
                    onClick={() => handleSortChange("score")}
                    className={`px-3 py-1 rounded-md text-xs font-medium transition-all ${
                      sortOrder === "score"
                        ? "bg-white dark:bg-gray-800 text-gray-900 dark:text-white shadow-sm"
                        : "text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
                    }`}
                  >
                    🎯 정확도순
                  </button>
                </div>
                <div className="text-sm text-gray-500 dark:text-gray-400">
                  {allArticles.length}개 / {totalHits.toLocaleString()}개 전체
                </div>
              </div>
            </div>

            <div className="space-y-4 pr-2">
              {allArticles.map((doc: any, index: number) => (
                <motion.a
                  key={`${doc.news_id}-${index}`}
                  id={`article-${index}`}
                  href={getArticleLink(doc)}
                  target="_blank"
                  rel="noopener noreferrer"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: (index % 10) * 0.1 }}
                  whileHover={{
                    y: -2,
                    transition: { type: "spring", stiffness: 300, damping: 20 },
                  }}
                  className="group relative block bg-white dark:bg-gray-800 rounded-xl shadow-md hover:shadow-xl transition-all duration-300 overflow-hidden border border-gray-100 dark:border-gray-700 p-6"
                >
                  {/* 기사 번호 표시 */}
                  <div className="absolute top-4 left-4 bg-primary-500 text-white text-xs font-mono px-2 py-1 rounded-md">
                    [{index + 1}]
                  </div>
                  <div className="flex items-start justify-between mb-3 ml-12">
                    <div className="flex items-center space-x-2">
                      <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-primary-50 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 border border-primary-200 dark:border-primary-800">
                        {doc.provider}
                      </span>
                      {doc.byline && (
                        <span className="text-sm text-gray-600 dark:text-gray-400 font-medium">
                          {doc.byline}
                        </span>
                      )}
                    </div>
                    <div className="text-right">
                      <time className="text-sm text-gray-700 dark:text-gray-300 font-semibold block">
                        {new Date(doc.published_at || doc.dateline).toLocaleDateString(
                          "ko-KR",
                          {
                            year: "numeric",
                            month: "long",
                            day: "numeric",
                          }
                        )}
                      </time>
                      <time className="text-xs text-gray-500 dark:text-gray-400 block">
                        {new Date(doc.published_at || doc.dateline).toLocaleTimeString(
                          "ko-KR",
                          {
                            hour: "2-digit",
                            minute: "2-digit",
                          }
                        )}
                      </time>
                      {doc.dateline && doc.dateline !== doc.published_at && (
                        <time className="text-xs text-gray-400 dark:text-gray-500 block mt-1" title="언론사 출고시간">
                          출고: {new Date(doc.dateline).toLocaleString("ko-KR", {
                            month: "short",
                            day: "numeric",
                            hour: "2-digit",
                            minute: "2-digit",
                          })}
                        </time>
                      )}
                      {doc.enveloped_at && (
                        <time className="text-xs text-gray-400 dark:text-gray-500 block mt-1" title="빅카인즈 수집시간">
                          수집: {new Date(doc.enveloped_at).toLocaleString("ko-KR", {
                            month: "short",
                            day: "numeric",
                            hour: "2-digit",
                            minute: "2-digit",
                          })}
                        </time>
                      )}
                    </div>
                  </div>
                  <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-3 line-clamp-2 group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors">
                    {doc.title}
                  </h4>

                  <div className="text-gray-600 dark:text-gray-400 text-sm line-clamp-3 leading-relaxed mb-4">
                    {doc.hilight ? (
                      renderHighlightedText(doc.hilight, doc.hilight)
                    ) : (
                      <span>{doc.content.substring(0, 200)}...</span>
                    )}
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4 text-xs text-gray-500 dark:text-gray-400">
                      <div className="flex items-center">
                        <svg
                          className="w-4 h-4 mr-1"
                          fill="currentColor"
                          viewBox="0 0 20 20"
                        >
                          <path
                            fillRule="evenodd"
                            d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z"
                            clipRule="evenodd"
                          />
                        </svg>
                        {new Date(doc.published_at).toLocaleDateString("ko-KR")}
                      </div>
                      {doc.category && (
                        <span className="bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded">
                          {doc.category}
                        </span>
                      )}
                    </div>
                    <div className="flex items-center text-primary-600 dark:text-primary-400 text-sm font-medium">
                      {doc.provider_link_page && doc.provider_link_page.trim() ? (
                        <>
                          <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M12.586 4.586a2 2 0 112.828 2.828l-3 3a2 2 0 01-2.828 0 1 1 0 00-1.414 1.414 4 4 0 005.656 0l3-3a4 4 0 00-5.656-5.656l-1.5 1.5a1 1 0 101.414 1.414l1.5-1.5zm-5 5a2 2 0 012.828 0 1 1 0 101.414-1.414 4 4 0 00-5.656 0l-3 3a4 4 0 105.656 5.656l1.5-1.5a1 1 0 10-1.414-1.414l-1.5 1.5a2 2 0 11-2.828-2.828l3-3z" clipRule="evenodd" />
                          </svg>
                          {doc.provider || '언론사'} 원문보기
                        </>
                      ) : doc.url && doc.url.trim() ? (
                        <>
                          <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zM3 10a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1v-6zM14 9a1 1 0 00-1 1v6a1 1 0 001 1h2a1 1 0 001-1v-6a1 1 0 00-1-1h-2z" clipRule="evenodd" />
                          </svg>
                          기사 보기
                        </>
                      ) : (
                        <>
                          <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clipRule="evenodd" />
                          </svg>
                          빅카인즈에서 검색
                        </>
                      )}
                      <svg
                        className="w-4 h-4 ml-1 transition-transform group-hover:translate-x-1"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                        />
                      </svg>
                    </div>
                  </div>
                </motion.a>
              ))}
            </div>

            {isLoadingMore && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex flex-col items-center justify-center py-8"
              >
                <div className="w-8 h-8 border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin mb-4"></div>
                <p className="text-gray-600 dark:text-gray-400 text-sm">
                  추가 기사를 불러오는 중입니다... ({allArticles.length}/
                  {totalHits.toLocaleString()})
                </p>
              </motion.div>
            )}

            {!hasMoreArticles && allArticles.length > 0 && (
              <div className="text-center py-8">
                <p className="text-gray-500 dark:text-gray-400 text-sm">
                  모든 기사를 확인했습니다. (
                  {allArticles.length.toLocaleString()}개)
                </p>
              </div>
            )}

            <div ref={loadMoreRef} className="h-4" />
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

/**
 * 홈페이지 컴포넌트
 */
const HomePage: React.FC = () => {
  const [activeTab, setActiveTab] = useState("최신 뉴스");
  const [latestNewsData, setLatestNewsData] =
    useState<LatestNewsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // AI 컨시어지 검색 상태
  const [query, setQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [searchResult, setSearchResult] =
    useState<ConciergeBriefingResponse | null>(null);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [loadingStep, setLoadingStep] = useState(0);

  // 대화형 검색 상태
  const [showChatInterface, setShowChatInterface] = useState(false);

  // 로딩 메시지 배열
  const loadingMessages = [
    { message: "질문을 분석하고 있습니다...", icon: "" },
    { message: "관련 기사를 검색하고 있습니다...", icon: "" },
    { message: "검색 결과를 분석하고 있습니다...", icon: "" },
    { message: "답변을 준비하고 있습니다...", icon: "" },
  ];

  useEffect(() => {
    const fetchLatestNews = async () => {
      setLoading(true);
      setError(null);

      try {
        const data = await getLatestNews();
        setLatestNewsData(data);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "알 수 없는 오류가 발생했습니다"
        );
        // 개발 중 더미 데이터 사용 (이슈 랭킹 구조)
        setLatestNewsData({
          today_issues: [
            {
              rank: 1,
              title: "반도체 수출 증가",
              count: 42,
              related_news: ["cluster_001", "cluster_002"],
            },
            {
              rank: 2,
              title: "AI 스타트업 투자",
              count: 38,
              related_news: ["cluster_003", "cluster_004"],
            },
            {
              rank: 3,
              title: "디지털 금융 혁신",
              count: 25,
              related_news: ["cluster_005"],
            },
            {
              rank: 4,
              title: "탄소중립 정책",
              count: 20,
              related_news: ["cluster_006"],
            },
            {
              rank: 5,
              title: "K-콘텐츠 해외진출",
              count: 18,
              related_news: ["cluster_007"],
            },
          ],
          popular_keywords: [
            { rank: 1, keyword: "생성 AI", count: 1250, trend: "up" },
            { rank: 2, keyword: "ESG 경영", count: 980, trend: "up" },
            { rank: 3, keyword: "메타버스", count: 850, trend: "stable" },
            { rank: 4, keyword: "탄소중립", count: 720, trend: "up" },
            { rank: 5, keyword: "디지털전환", count: 680, trend: "stable" },
            { rank: 6, keyword: "비대면 금융", count: 550, trend: "down" },
            { rank: 7, keyword: "자동차 전동화", count: 480, trend: "up" },
          ],
          timestamp: new Date().toISOString(),
        });
      } finally {
        setLoading(false);
      }
    };

    fetchLatestNews();
  }, []);

  // AI 컨시어지 검색 핸들러
  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    console.log("검색 시작:", query);
    setIsSearching(true);
    setSearchError(null);
    setSearchResult(null);
    setLoadingStep(0);

    // 로딩 단계를 순차적으로 진행
    const stepInterval = setInterval(() => {
      setLoadingStep((prev) => {
        if (prev < loadingMessages.length - 1) {
          return prev + 1;
        }
        return prev;
      });
    }, 1000);

    try {
      const result = await getConciergeBriefing(query);
      console.log("검색 결과 받음:", result);
      console.log("네트워크 데이터:", result.network_data);
      if (result.network_data) {
        console.log("노드 수:", result.network_data.nodes?.length || 0);
        console.log("링크 수:", result.network_data.links?.length || 0);
      }
      setSearchResult(result);
    } catch (err: any) {
      console.error("검색 오류:", err);
      setSearchError(err.message || "검색 중 오류가 발생했습니다.");
    } finally {
      clearInterval(stepInterval);
      setIsSearching(false);
      setLoadingStep(0);
    }
  };

  // 키워드 클릭 시 새로운 검색 실행
  const handleKeywordSearch = async (keyword: string) => {
    setQuery(keyword);
    console.log("🔍 키워드 검색 시작:", keyword);
    setIsSearching(true);
    setSearchError(null);
    setSearchResult(null);
    setLoadingStep(0);

    // 로딩 단계를 순차적으로 진행
    const stepInterval = setInterval(() => {
      setLoadingStep((prev) => {
        if (prev < loadingMessages.length - 1) {
          return prev + 1;
        }
        return prev;
      });
    }, 1000);

    try {
      const result = await getConciergeBriefing(keyword);
      console.log("키워드 검색 결과 받음:", result);
      console.log("키워드 검색 네트워크 데이터:", result.network_data);
      if (result.network_data) {
        console.log(
          "키워드 검색 노드 수:",
          result.network_data.nodes?.length || 0
        );
        console.log(
          "키워드 검색 링크 수:",
          result.network_data.links?.length || 0
        );
      }
      setSearchResult(result);
    } catch (err: any) {
      console.error("키워드 검색 오류:", err);
      setSearchError(err.message || "검색 중 오류가 발생했습니다.");
    } finally {
      clearInterval(stepInterval);
      setIsSearching(false);
      setLoadingStep(0);
    }
  };

  const renderContent = () => {
    if (loading) {
      return <LoadingSpinner />;
    }

    if (!latestNewsData) {
      return <ErrorMessage message={error} />;
    }

    switch (activeTab) {
      case "최신 뉴스":
        return (
          <motion.div
            key="latest-news"
            initial="hidden"
            animate="visible"
            variants={containerVariants}
          >
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                서울경제 헤드라인
              </h3>
              <p className="text-gray-600 dark:text-gray-400 text-sm">
                서울경제신문의 최신 헤드라인 뉴스를 실시간으로 확인하세요.
              </p>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg overflow-hidden border border-gray-200 dark:border-gray-700">
              <iframe
                src="https://www.sedaily.com/News/HeadLine"
                title="서울경제 헤드라인 뉴스"
                className="w-full h-[600px] border-0"
                style={{
                  minHeight: '600px',
                }}
                loading="lazy"
                sandbox="allow-scripts allow-same-origin allow-popups allow-forms"
                referrerPolicy="no-referrer-when-downgrade"
              />
              <div className="p-4 bg-gray-50 dark:bg-gray-700 border-t border-gray-200 dark:border-gray-600">
                <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
                  <a 
                    href="https://www.sedaily.com/News/HeadLine" 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="hover:text-primary-500 transition-colors"
                  >
                    서울경제신문에서 더 많은 뉴스 보기 →
                  </a>
                </p>
              </div>
            </div>
          </motion.div>
        );
      case "주요 이슈":
        return (
          <motion.div
            key="issues"
            initial="hidden"
            animate="visible"
            variants={containerVariants}
          >
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                이슈 랭킹
              </h3>
              <p className="text-gray-600 dark:text-gray-400 text-sm">
                오늘 가장 주목받는 이슈들을 점수 순으로 보여드립니다.
              </p>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
              {latestNewsData?.today_issues?.length > 0 ? (
                latestNewsData.today_issues.map((item, index) => (
                  <IssueCard key={item.topic_id || index} item={item} />
                ))
              ) : (
                <div className="col-span-full text-center py-8 text-gray-500 dark:text-gray-400">
                  <svg className="w-12 h-12 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" />
                  </svg>
                  <p>오늘의 주요 이슈를 불러오고 있습니다...</p>
                </div>
              )}
            </div>
          </motion.div>
        );
      case "인기 키워드":
        return (
          <motion.div
            key="popular-keywords"
            initial="hidden"
            animate="visible"
            variants={containerVariants}
            className="flex flex-wrap gap-4 justify-center"
          >
            {(latestNewsData?.popular_keywords || [])
              .slice(0, 30)
              .map((item, index) => (
                <KeywordTag key={item.keyword + index} item={item} />
              ))}
          </motion.div>
        );
      default:
        return null;
    }
  };

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={containerVariants}
      exit="hidden"
      className="container mx-auto px-4 sm:px-6 lg:px-8 py-12"
    >
      <div className="text-center mb-12">
        <h1 className="text-4xl sm:text-5xl md:text-6xl font-extrabold text-gray-900 dark:text-white tracking-tight">
          <span className="bg-clip-text text-transparent bg-gradient-to-r from-primary-500 to-secondary-500">
            AI Nova
          </span>
        </h1>
        <p className="mt-4 max-w-2xl mx-auto text-lg text-gray-600 dark:text-gray-400">
          빅카인즈 기반 스마트 뉴스 분석 플랫폼
        </p>
      </div>

      {/* AI 뉴스 컨시어지 검색 섹션 */}
      <div className="max-w-3xl mx-auto mb-16">
        <form onSubmit={handleSearch} className="relative">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="궁금한 점을 질문해보세요. 예: 삼성전자 최근 실적은?"
            className="w-full pl-6 pr-32 py-4 text-lg bg-white dark:bg-gray-800 border-2 border-gray-200 dark:border-gray-700 rounded-full focus:ring-4 focus:ring-primary-300 dark:focus:ring-primary-500/50 focus:border-primary-500 dark:focus:border-primary-500 transition-all duration-300 outline-none"
            disabled={isSearching}
          />
          <button
            type="submit"
            disabled={isSearching || !query.trim()}
            className="absolute right-2.5 top-1/2 -translate-y-1/2 h-12 px-8 bg-gradient-to-r from-primary-500 to-secondary-500 text-white font-semibold rounded-full hover:shadow-lg hover:from-primary-600 hover:to-secondary-600 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSearching ? (
              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
            ) : (
              "검색"
            )}
          </button>
        </form>

        {/* 검색 모드 선택 버튼 */}
        <div className="flex justify-center mt-4 space-x-4">
          <button
            onClick={() => setShowChatInterface(true)}
            className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white font-medium rounded-full hover:shadow-lg hover:from-purple-600 hover:to-pink-600 transition-all duration-300"
          >
            <svg
              className="w-5 h-5 mr-2"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
              />
            </svg>
            대화형 검색
          </button>
          <div className="text-sm text-gray-500 dark:text-gray-400 self-center">
            연속 질문으로 더 정확한 정보를 찾아보세요
          </div>
        </div>
      </div>

      {/* 검색 결과 표시 */}
      <AnimatePresence>
        {isSearching && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="max-w-3xl mx-auto mt-8 bg-white dark:bg-gray-800 rounded-2xl shadow-lg border border-gray-200 dark:border-gray-700 p-8"
          >
            <div className="flex flex-col items-center justify-center">
              <div className="relative mb-6">
                <div className="w-16 h-16 border-4 border-primary-200 dark:border-primary-800 rounded-full animate-spin">
                  <div className="absolute top-0 left-0 w-16 h-16 border-4 border-transparent border-t-primary-600 dark:border-t-primary-400 rounded-full animate-spin"></div>
                </div>
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-2xl animate-pulse">
                    {loadingMessages[loadingStep]?.icon}
                  </span>
                </div>
              </div>

              <div className="text-center">
                <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                  AI 뉴스 컨시어지가 답변을 준비하고 있습니다
                </h3>
                <p className="text-gray-600 dark:text-gray-400 mb-4">
                  "{query}"에 대해서 {loadingMessages[loadingStep]?.message}
                </p>

                {/* 진행 상태 표시 */}
                <div className="flex justify-center space-x-2 mb-4">
                  {loadingMessages.map((_, index) => (
                    <div
                      key={index}
                      className={`w-2 h-2 rounded-full transition-all duration-300 ${
                        index <= loadingStep
                          ? "bg-primary-500 dark:bg-primary-400"
                          : "bg-gray-300 dark:bg-gray-600"
                      }`}
                    />
                  ))}
                </div>

                <div className="text-sm text-gray-500 dark:text-gray-400">
                  잠시만 기다려주세요... ({loadingStep + 1}/
                  {loadingMessages.length})
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {searchError && <ErrorMessage message={searchError} />}

      {searchResult && (
        <ConciergeResultDisplay
          result={searchResult}
          onKeywordClick={handleKeywordSearch}
        />
      )}

      {/* 대화형 검색 인터페이스 */}
      <AnimatePresence>
        {showChatInterface && (
          <ChatInterface onClose={() => setShowChatInterface(false)} />
        )}
      </AnimatePresence>

      {/* 기존 뉴스 섹션 */}
      <div className="mt-16">
        <div className="flex justify-center border-b border-gray-200 dark:border-gray-700 mb-8">
          <Tab
            key="최신 뉴스"
            label="최신 뉴스"
            isActive={activeTab === "최신 뉴스"}
            onClick={() => setActiveTab("최신 뉴스")}
          />
          <Tab
            key="주요 이슈"
            label="주요 이슈"
            isActive={activeTab === "주요 이슈"}
            onClick={() => setActiveTab("주요 이슈")}
          />
          <Tab
            key="인기 키워드"
            label="인기 키워드"
            isActive={activeTab === "인기 키워드"}
            onClick={() => setActiveTab("인기 키워드")}
          />
        </div>
        <AnimatePresence mode="wait">{renderContent()}</AnimatePresence>
      </div>
    </motion.div>
  );
};

export default HomePage;
