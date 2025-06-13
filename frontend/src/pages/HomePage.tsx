import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Link, useNavigate } from "react-router-dom";
import { containerVariants, itemVariants } from "../animations/pageAnimations";
import LoadingSpinner from "../components/common/LoadingSpinner";
import ErrorMessage from "../components/common/ErrorMessage";
import {
  getLatestNews,
  type LatestNewsResponse,
  type IssueTopic,
  type PopularKeyword,
} from "../services/api";

interface NewsItem {
  id?: string;
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
    className={`px-6 py-3 font-medium transition-all ${
      isActive
        ? "text-primary-600 dark:text-primary-400 border-b-2 border-primary-600 dark:border-primary-400"
        : "text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200"
    }`}
  >
    {label}
  </button>
);

const NewsCard: React.FC<{ item: NewsItem }> = ({ item }) => {
  const navigate = useNavigate();

  const handleCardClick = () => {
    // 모달 대신 페이지 이동 방식 사용
    if (item.id) {
      navigate(`/news/${item.id}`);
    }
  };

  return (
    <motion.div
      variants={itemVariants}
      whileHover={{ scale: 1.02 }}
      className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 hover:shadow-lg transition-all cursor-pointer"
      onClick={handleCardClick}
    >
      <div className="flex items-start justify-between mb-3">
        <span className="text-xs text-primary-600 dark:text-primary-400 font-medium">
          {item.provider}
        </span>
        <span className="text-xs text-gray-500 dark:text-gray-400">
          {item.date}
        </span>
      </div>

      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3 line-clamp-2">
        {item.title}
      </h3>

      {item.summary && (
        <p className="text-gray-600 dark:text-gray-400 text-sm mb-4 line-clamp-3">
          {item.summary}
        </p>
      )}

      <div className="flex items-center justify-between">
        <span className="text-xs text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded">
          {item.category}
        </span>
        <button
          onClick={(e) => {
            e.stopPropagation();
            if (item.id) {
              navigate(`/news/${item.id}`);
            }
          }}
          className="text-primary-600 dark:text-primary-400 text-sm hover:underline"
        >
          본문 보기 →
        </button>
      </div>
    </motion.div>
  );
};

const IssueCard: React.FC<{ item: IssueTopic }> = ({ item }) => {
  const [showDetails, setShowDetails] = useState(false);

  return (
    <motion.div
      variants={itemVariants}
      className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow cursor-pointer"
      whileHover={{ scale: 1.02 }}
      onClick={() => setShowDetails(!showDetails)}
    >
      <div className="flex items-center justify-between mb-4">
        <span className="text-2xl font-bold text-primary-600 dark:text-primary-400">
          #{item.rank}
        </span>
        <span className="px-3 py-1 rounded-full text-xs bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
          뉴스: {item.count}개
        </span>
      </div>
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
        {item.title || item.topic_name}
      </h3>

      {/* 기본 정보 */}
      <div className="flex items-center justify-between mb-3">
        <p className="text-gray-600 dark:text-gray-400 text-sm">
          관련 뉴스:{" "}
          <span className="font-semibold text-primary-600 dark:text-primary-400">
            {item.count}개
          </span>
        </p>
        <span className="text-xs text-gray-500 dark:text-gray-400">
          {showDetails ? "▲ 접기" : "▼ 언론사별 보기"}
        </span>
      </div>

      {/* 언론사별 breakdown (토글) */}
      {showDetails &&
        item.provider_breakdown &&
        item.provider_breakdown.length > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700"
          >
            <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
              📰 언론사별 기사 수
            </h4>
            <div className="space-y-2 max-h-40 overflow-y-auto">
              {item.provider_breakdown.map((provider, index) => (
                <div
                  key={provider.provider_code}
                  className="flex items-center justify-between text-xs bg-gray-50 dark:bg-gray-700 px-3 py-2 rounded"
                >
                  <span className="font-medium text-gray-700 dark:text-gray-300">
                    {provider.provider}
                  </span>
                  <span className="text-primary-600 dark:text-primary-400 font-bold">
                    {provider.count}건
                  </span>
                </div>
              ))}
            </div>
          </motion.div>
        )}
    </motion.div>
  );
};

const KeywordTag: React.FC<{ item: PopularKeyword }> = ({ item }) => (
  <motion.span
    variants={itemVariants}
    whileHover={{ scale: 1.05 }}
    className="inline-flex items-center justify-between bg-gradient-to-r from-primary-50 to-primary-100 dark:from-primary-900 dark:to-primary-800 text-primary-700 dark:text-primary-300 px-4 py-3 rounded-lg font-medium cursor-pointer transition-all hover:shadow-md"
  >
    <div>
      <div className="font-semibold">{item.keyword}</div>
      <div className="text-xs opacity-70">#{item.rank}</div>
    </div>
    <div className="ml-2 text-right">
      <div className="text-xs opacity-70">{item.count}회</div>
      {item.trend && (
        <div className="text-xs">
          {item.trend === "up" ? "↑" : item.trend === "down" ? "↓" : "→"}
        </div>
      )}
    </div>
  </motion.span>
);

/**
 * 홈페이지 컴포넌트
 */
const HomePage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<"issues" | "keywords">("issues");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [latestNews, setLatestNews] = useState<LatestNewsResponse>({
    today_issues: [],
    popular_keywords: [],
    timestamp: "",
  });

  useEffect(() => {
    fetchLatestNews();
  }, []);

  const fetchLatestNews = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const data = await getLatestNews();
      setLatestNews(data);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "알 수 없는 오류가 발생했습니다"
      );
      // 개발 중 더미 데이터 사용 (이슈 랭킹 구조)
      setLatestNews({
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
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return <LoadingSpinner />;
  }

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={containerVariants}
      className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8"
    >
      {/* 헤더 */}
      <div className="text-center mb-12">
        <motion.h1
          variants={itemVariants}
          className="text-4xl font-bold text-gray-900 dark:text-white mb-4"
        >
          🚀 AI NOVA
        </motion.h1>
        <motion.p
          variants={itemVariants}
          className="text-xl text-gray-600 dark:text-gray-400"
        >
          빅카인즈 기반 스마트 뉴스 분석 플랫폼
        </motion.p>
      </div>

      {/* 에러 메시지 */}
      {error && (
        <motion.div variants={itemVariants} className="mb-8">
          <ErrorMessage message={error} />
        </motion.div>
      )}

      {/* 최신 뉴스 대시보드 */}
      <motion.div
        variants={itemVariants}
        className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8"
      >
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
          최신 뉴스 대시보드
        </h2>

        {/* 탭 네비게이션 */}
        <div className="flex space-x-8 border-b border-gray-200 dark:border-gray-700">
          <Tab
            label="오늘의 이슈"
            isActive={activeTab === "issues"}
            onClick={() => setActiveTab("issues")}
          />
          <Tab
            label="인기 키워드"
            isActive={activeTab === "keywords"}
            onClick={() => setActiveTab("keywords")}
          />
        </div>

        {/* 탭 컨텐츠 */}
        <div className="mt-8">
          {activeTab === "issues" && (
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
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {latestNews.today_issues.map((item) => (
                  <IssueCard key={item.topic_id} item={item} />
                ))}
              </div>
            </motion.div>
          )}

          {activeTab === "keywords" && (
            <motion.div
              key="keywords"
              initial="hidden"
              animate="visible"
              variants={containerVariants}
            >
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                  인기 키워드 랭킹
                </h3>
                <p className="text-gray-600 dark:text-gray-400 text-sm">
                  카테고리별로 인기 있는 키워드들을 확인하세요.
                </p>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                {latestNews.popular_keywords.map((item, index) => (
                  <KeywordTag key={index} item={item} />
                ))}
              </div>
            </motion.div>
          )}
        </div>
      </motion.div>

      {/* CTA 섹션 */}
      <motion.div
        variants={itemVariants}
        className="mt-12 text-center bg-gradient-to-r from-primary-500 to-primary-600 dark:from-primary-600 dark:to-primary-700 rounded-lg p-8 text-white"
      >
        <h3 className="text-2xl font-bold mb-4">관심 종목을 추적해보세요</h3>
        <p className="text-lg opacity-90 mb-6">
          AI 기반 뉴스 요약과 타임라인으로 기업 동향을 한눈에 파악하세요
        </p>
        <Link
          to="/watchlist"
          className="inline-flex items-center bg-white text-primary-600 px-6 py-3 rounded-lg font-semibold hover:bg-gray-100 transition-colors"
        >
          관심 종목 추가하기
          <svg
            className="w-5 h-5 ml-2"
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
        </Link>
      </motion.div>
    </motion.div>
  );
};

export default HomePage;
