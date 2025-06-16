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
    role="tab"
    aria-selected={isActive}
    aria-controls={`tabpanel-${label.replace(/\s+/g, '-').toLowerCase()}`}
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

  const handleCardClick = () => {
    // 모달 대신 페이지 이동 방식 사용
    if (item.id) {
      navigate(`/news/${item.id}`);
    }
  };

  return (
    <motion.div
      variants={itemVariants}
      whileHover={{ 
        y: -4,
        transition: { type: "spring", stiffness: 300, damping: 20 }
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
            onClick={(e) => {
              e.stopPropagation();
              if (item.id) {
                navigate(`/news/${item.id}`);
              }
            }}
            className="inline-flex items-center text-sm text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 font-medium transition-colors"
          >
            자세히 보기
            <svg className="w-4 h-4 ml-1 transition-transform group-hover:translate-x-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
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
        transition: { type: "spring", stiffness: 300, damping: 20 }
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
              <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path d="M2 5a2 2 0 012-2h12a2 2 0 012 2v10a2 2 0 01-2 2H4a2 2 0 01-2-2V5zm3.293 1.293a1 1 0 011.414 0l3 3a1 1 0 010 1.414l-3 3a1 1 0 01-1.414-1.414L7.586 10 5.293 7.707a1 1 0 010-1.414zM11 12a1 1 0 100 2h3a1 1 0 100-2h-3z" />
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
                <svg className="w-4 h-4 ml-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                </svg>
              </>
            ) : (
              <>
                언론사별 보기
                <svg className="w-4 h-4 ml-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </>
            )}
          </button>
        </div>

        {/* 언론사별 breakdown (토글) */}
        <AnimatePresence>
          {showDetails && item.provider_breakdown && item.provider_breakdown.length > 0 && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.3, ease: "easeInOut" }}
              className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-700"
            >
              <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4 flex items-center">
                <svg className="w-4 h-4 mr-2 text-primary-500" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M2 5a2 2 0 012-2h12a2 2 0 012 2v2a2 2 0 01-2 2H4a2 2 0 01-2-2V5zm14 1a1 1 0 11-2 0 1 1 0 012 0zM2 13a2 2 0 012-2h12a2 2 0 012 2v2a2 2 0 01-2 2H4a2 2 0 01-2-2v-2zm14 1a1 1 0 11-2 0 1 1 0 012 0z" clipRule="evenodd" />
                </svg>
                언론사별 보도 현황
              </h4>
              <div className="grid grid-cols-1 gap-2 max-h-40 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-300 dark:scrollbar-thumb-gray-600">
                {item.provider_breakdown.map((provider, index) => (
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
                            width: `${Math.min((provider.count / Math.max(...item.provider_breakdown.map(p => p.count))) * 100, 100)}%` 
                          }}
                        />
                      </div>
                    </div>
                  </motion.div>
                ))}
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
          <svg className="w-4 h-4 text-green-500" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M3.293 9.707a1 1 0 010-1.414l6-6a1 1 0 011.414 0l6 6a1 1 0 01-1.414 1.414L11 5.414V17a1 1 0 11-2 0V5.414L4.707 9.707a1 1 0 01-1.414 0z" clipRule="evenodd" />
          </svg>
        );
      case "down":
        return (
          <svg className="w-4 h-4 text-red-500" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M16.707 10.293a1 1 0 010 1.414l-6 6a1 1 0 01-1.414 0l-6-6a1 1 0 111.414-1.414L9 14.586V3a1 1 0 012 0v11.586l4.293-4.293a1 1 0 011.414 0z" clipRule="evenodd" />
          </svg>
        );
      default:
        return (
          <svg className="w-4 h-4 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clipRule="evenodd" />
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
        transition: { type: "spring", stiffness: 400, damping: 17 }
      }}
      whileTap={{ scale: 0.95 }}
      className={`group relative overflow-hidden bg-gradient-to-br ${getTrendColor(item.trend)} border rounded-xl p-4 cursor-pointer transition-all duration-300 hover:shadow-lg`}
    >
      {/* 배경 그라데이션 효과 */}
      <div className="absolute inset-0 bg-gradient-to-br from-white/50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
      
      {/* 랭킹 배지 */}
      <div className="absolute top-2 right-2 w-6 h-6 bg-white/80 dark:bg-gray-800/80 rounded-full flex items-center justify-center">
        <span className="text-xs font-bold text-gray-600 dark:text-gray-400">
          {item.rank}
        </span>
      </div>
      
      {/* 메인 콘텐츠 */}
      <div className="relative">
        <div className="flex items-start justify-between mb-3">
          <h3 className="font-semibold text-base leading-tight pr-8 group-hover:text-gray-900 dark:group-hover:text-white transition-colors">
            {item.keyword}
          </h3>
        </div>
        
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className="text-sm font-medium opacity-80">
              {item.count.toLocaleString()}회
            </span>
            {item.trend && (
              <div className="flex items-center">
                {getTrendIcon(item.trend)}
              </div>
            )}
          </div>
          
          {/* 진행률 바 */}
          <div className="w-16 h-1.5 bg-white/30 dark:bg-gray-700/30 rounded-full overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${Math.min((item.count / 1500) * 100, 100)}%` }}
              transition={{ delay: 0.2, duration: 0.8, ease: "easeOut" }}
              className="h-full bg-current rounded-full opacity-60"
            />
          </div>
        </div>
      </div>
    </motion.div>
  );
};

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
      <header className="text-center mb-12" role="banner">
        <motion.h1
          variants={itemVariants}
          className="text-3xl sm:text-4xl lg:text-5xl font-bold text-gray-900 dark:text-white mb-4 gradient-text"
        >
          🚀 AI NOVA
        </motion.h1>
        <motion.p
          variants={itemVariants}
          className="text-lg sm:text-xl text-gray-600 dark:text-gray-400 max-w-2xl mx-auto leading-relaxed"
        >
          빅카인즈 기반 스마트 뉴스 분석 플랫폼
        </motion.p>
      </header>

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
        <nav className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-8 border-b border-gray-200 dark:border-gray-700" role="tablist" aria-label="뉴스 데이터 유형 선택">
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
        </nav>

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
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
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
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3 sm:gap-4">
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
