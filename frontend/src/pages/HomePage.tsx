import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { containerVariants, itemVariants } from "../animations/pageAnimations";
import LoadingSpinner from "../components/common/LoadingSpinner";
import ErrorMessage from "../components/common/ErrorMessage";

interface NewsItem {
  id: string;
  title: string;
  summary?: string;
  provider?: string;
  date?: string;
  category?: string;
  url?: string;
}

interface IssueItem {
  topic_id: string;
  topic_name: string;
  rank: number;
  score: number;
  news_cluster: string[];
}

interface KeywordItem {
  keyword: string;
  category: string;
  score: number;
  rank?: number;
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

const NewsCard: React.FC<{ item: NewsItem }> = ({ item }) => (
  <motion.div
    variants={itemVariants}
    whileHover={{ scale: 1.02 }}
    className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 hover:shadow-lg transition-all cursor-pointer"
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
      <Link
        to={item.url || "#"}
        className="text-primary-600 dark:text-primary-400 text-sm hover:underline"
      >
        자세히 보기 →
      </Link>
    </div>
  </motion.div>
);

const IssueCard: React.FC<{ item: IssueItem }> = ({ item }) => (
  <motion.div
    variants={itemVariants}
    className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow cursor-pointer"
    whileHover={{ scale: 1.02 }}
  >
    <div className="flex items-center justify-between mb-4">
      <span className="text-2xl font-bold text-primary-600 dark:text-primary-400">
        #{item.rank}
      </span>
      <span className="px-3 py-1 rounded-full text-xs bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
        점수: {item.score}
      </span>
    </div>
    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
      {item.topic_name}
    </h3>
    <div className="flex items-center justify-between">
      <p className="text-gray-600 dark:text-gray-400 text-sm">
        관련 뉴스: <span className="font-semibold">{item.news_cluster.length}개</span>
      </p>
      <span className="text-xs text-gray-500 dark:text-gray-400">
        ID: {item.topic_id}
      </span>
    </div>
  </motion.div>
);

const KeywordTag: React.FC<{ item: KeywordItem }> = ({ item }) => (
  <motion.span
    variants={itemVariants}
    whileHover={{ scale: 1.05 }}
    className="inline-flex items-center justify-between bg-gradient-to-r from-primary-50 to-primary-100 dark:from-primary-900 dark:to-primary-800 text-primary-700 dark:text-primary-300 px-4 py-3 rounded-lg font-medium cursor-pointer transition-all hover:shadow-md"
  >
    <div>
      <div className="font-semibold">{item.keyword}</div>
      {item.rank && (
        <div className="text-xs opacity-70">#{item.rank}</div>
      )}
    </div>
    <span className="ml-2 text-xs opacity-70">{item.category}</span>
  </motion.span>
);

/**
 * 홈페이지 컴포넌트
 */
const HomePage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<"issues" | "keywords">("issues");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [latestNews, setLatestNews] = useState<{
    today_issues: IssueItem[];
    popular_keywords: KeywordItem[];
  }>({
    today_issues: [],
    popular_keywords: []
  });

  useEffect(() => {
    fetchLatestNews();
  }, []);

  const fetchLatestNews = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetch("/api/news/latest");
      if (!response.ok) {
        throw new Error("최신 뉴스를 불러오는데 실패했습니다");
      }
      
      const data = await response.json();
      setLatestNews(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "알 수 없는 오류가 발생했습니다");
      // 개발 중 더미 데이터 사용 (이슈 랭킹 구조)
      setLatestNews({
        today_issues: [
          {
            topic_id: "issue_001",
            topic_name: "반도체 수출 증가",
            rank: 1,
            score: 95.2,
            news_cluster: ["cluster_001", "cluster_002"]
          },
          {
            topic_id: "issue_002", 
            topic_name: "AI 스타트업 투자",
            rank: 2,
            score: 89.7,
            news_cluster: ["cluster_003", "cluster_004"]
          },
          {
            topic_id: "issue_003",
            topic_name: "디지털 금융 혁신",
            rank: 3,
            score: 82.5,
            news_cluster: ["cluster_005"]
          },
          {
            topic_id: "issue_004",
            topic_name: "카보네이트리티 정책",
            rank: 4,
            score: 78.9,
            news_cluster: ["cluster_006"]
          },
          {
            topic_id: "issue_005",
            topic_name: "K-콘텐츠 해외진출",
            rank: 5,
            score: 75.3,
            news_cluster: ["cluster_007"]
          }
        ],
        popular_keywords: [
          { keyword: "생성 AI", rank: 1, category: "기술", score: 95 },
          { keyword: "ESG 경영", rank: 2, category: "경영", score: 92 },
          { keyword: "메타버스", rank: 3, category: "기술", score: 88 },
          { keyword: "탄소중립", rank: 4, category: "환경", score: 85 },
          { keyword: "디지털전환", rank: 5, category: "산업", score: 82 },
          { keyword: "비대면 금융", rank: 6, category: "금융", score: 79 },
          { keyword: "자동차 전동화", rank: 7, category: "자동차", score: 76 }
        ]
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
          📊 최신 뉴스 대시보드
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
          <svg className="w-5 h-5 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </Link>
      </motion.div>
    </motion.div>
  );
};

export default HomePage;