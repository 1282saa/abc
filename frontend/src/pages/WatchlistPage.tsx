import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { containerVariants, itemVariants } from "../animations/pageAnimations";
import LoadingSpinner from "../components/common/LoadingSpinner";
import ErrorMessage from "../components/common/ErrorMessage";

interface Company {
  name: string;
  code: string;
  category: string;
}

interface NewsArticle {
  id: string;
  title: string;
  summary: string;
  content?: string;
  provider: string;
  url: string;
  category: string;
  byline: string;
  images: string[];
  published_at?: string;
  ref_id?: string;
}

interface TimelineItem {
  date: string;
  articles: NewsArticle[];
  count: number;
}

interface SelectedArticle extends NewsArticle {
  isSelected: boolean;
}

type SummaryType = "issue" | "quote" | "data";

// 레포트 타입 정의
type ReportType = "daily" | "weekly" | "monthly" | "quarterly" | "yearly";

// 레포트 결과 인터페이스
interface ReportResult {
  success: boolean;
  company: string;
  report_type: ReportType;
  report_type_kr: string;
  reference_date: string;
  period: {
    from: string;
    to: string;
  };
  total_articles: number;
  articles: NewsArticle[];
  detailed_articles?: NewsArticle[];
  summary: string;
  generated_at: string;
  model_used: string;
}

interface SummaryResult {
  title: string;
  summary: string;
  type: SummaryType;
  key_points?: string[];
  key_quotes?: { source: string; quote: string }[];
  key_data?: { metric: string; value: string; context: string }[];
  articles_analyzed: number;
  generated_at: string;
}

const CompanyCard: React.FC<{
  company: Company;
  isActive: boolean;
  onClick: () => void;
}> = ({ company, isActive, onClick }) => (
  <motion.div
    className={`card p-4 cursor-pointer transition-all ${
      isActive
        ? "ring-2 ring-primary-500 bg-primary-50 dark:bg-primary-900/20"
        : "hover:shadow-md"
    }`}
    whileHover={{ scale: 1.02 }}
    onClick={onClick}
  >
    <h3 className="font-semibold text-lg">{company.name}</h3>
    <p className="text-sm text-gray-600 dark:text-gray-400">
      {company.category}
    </p>
    <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
      종목코드: {company.code}
    </p>
  </motion.div>
);

const NewsArticleCard: React.FC<{
  article: SelectedArticle;
  onToggle: () => void;
  onViewDetail: () => void;
}> = ({ article, onToggle, onViewDetail }) => (
  <motion.div
    className="card p-4 relative cursor-pointer"
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    exit={{ opacity: 0, y: -20 }}
    onClick={onViewDetail}
  >
    <div
      className="absolute top-4 right-4"
      onClick={(e) => {
        e.stopPropagation();
        onToggle();
      }}
    >
      <input
        type="checkbox"
        checked={article.isSelected}
        onChange={(e) => {
          e.stopPropagation();
          onToggle();
        }}
        className="w-5 h-5 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
      />
    </div>
    <div className="pr-8">
      <h4 className="font-semibold mb-2 line-clamp-2">{article.title}</h4>
      <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-3 mb-3">
        {article.summary}
      </p>
      <div className="flex justify-between items-center text-xs text-gray-500">
        <span>{article.provider}</span>
        <span>{article.category}</span>
      </div>
    </div>
  </motion.div>
);

const NewsCarousel: React.FC<{ articles: NewsArticle[] }> = ({ articles }) => {
  const [currentIndex, setCurrentIndex] = useState(0);

  const nextSlide = () => {
    setCurrentIndex((prev) => (prev + 1) % articles.length);
  };

  const prevSlide = () => {
    setCurrentIndex((prev) => (prev - 1 + articles.length) % articles.length);
  };

  if (articles.length === 0) return null;

  return (
    <div className="relative bg-gray-50 dark:bg-gray-800 rounded-lg p-6">
      <h3 className="text-lg font-semibold mb-4">주요 뉴스 요약</h3>
      <div className="relative overflow-hidden">
        <AnimatePresence mode="wait">
          <motion.div
            key={currentIndex}
            initial={{ x: 300, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: -300, opacity: 0 }}
            transition={{ duration: 0.3 }}
          >
            <h4 className="font-medium mb-2">{articles[currentIndex].title}</h4>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {articles[currentIndex].summary}
            </p>
            <div className="mt-3 text-xs text-gray-500">
              {articles[currentIndex].provider} ·{" "}
              {articles[currentIndex].category}
            </div>
          </motion.div>
        </AnimatePresence>
      </div>
      <div className="flex justify-between items-center mt-4">
        <button
          onClick={prevSlide}
          className="p-2 rounded-full bg-white dark:bg-gray-700 shadow hover:shadow-md transition-all"
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
              strokeWidth={2}
              d="M15 19l-7-7 7-7"
            />
          </svg>
        </button>
        <div className="flex gap-2">
          {articles.map((_, index) => (
            <span
              key={index}
              className={`w-2 h-2 rounded-full ${
                index === currentIndex
                  ? "bg-primary-500"
                  : "bg-gray-300 dark:bg-gray-600"
              }`}
            />
          ))}
        </div>
        <button
          onClick={nextSlide}
          className="p-2 rounded-full bg-white dark:bg-gray-700 shadow hover:shadow-md transition-all"
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
              strokeWidth={2}
              d="M9 5l7 7-7 7"
            />
          </svg>
        </button>
      </div>
    </div>
  );
};

const SummaryModal: React.FC<{
  isOpen: boolean;
  onClose: () => void;
  selectedArticles: NewsArticle[];
  onGenerateSummary: (type: SummaryType) => void;
  summaryResult: SummaryResult | null;
  isGenerating: boolean;
}> = ({
  isOpen,
  onClose,
  selectedArticles,
  onGenerateSummary,
  summaryResult,
  isGenerating,
}) => {
  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.9, opacity: 0 }}
          className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-2xl w-full max-h-[80vh] overflow-y-auto"
          onClick={(e) => e.stopPropagation()}
        >
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold">AI 요약 생성</h2>
            <button
              onClick={onClose}
              className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700"
            >
              <svg
                className="w-6 h-6"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>

          {!summaryResult && !isGenerating && (
            <>
              <p className="mb-4 text-gray-600 dark:text-gray-400">
                {selectedArticles.length}개의 기사를 선택하셨습니다. 원하시는
                요약 방식을 선택해주세요.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  onClick={() => onGenerateSummary("issue")}
                  className="p-6 rounded-lg border-2 border-gray-200 dark:border-gray-700 hover:border-primary-500 dark:hover:border-primary-500 transition-all"
                >
                  <svg
                    className="w-12 h-12 mx-auto mb-3 text-primary-500"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={1.5}
                      d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                    />
                  </svg>
                  <h3 className="font-semibold mb-2">이슈 중심 요약</h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    핵심 이슈와 주요 동향을 중심으로 요약합니다
                  </p>
                </motion.button>

                <motion.button
                  whileHover={{ scale: 1.02 }}
                  onClick={() => onGenerateSummary("quote")}
                  className="p-6 rounded-lg border-2 border-gray-200 dark:border-gray-700 hover:border-primary-500 dark:hover:border-primary-500 transition-all"
                >
                  <svg
                    className="w-12 h-12 mx-auto mb-3 text-primary-500"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={1.5}
                      d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                    />
                  </svg>
                  <h3 className="font-semibold mb-2">인용 중심 요약</h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    주요 인물의 발언과 의견을 중심으로 요약합니다
                  </p>
                </motion.button>

                <motion.button
                  whileHover={{ scale: 1.02 }}
                  onClick={() => onGenerateSummary("data")}
                  className="p-6 rounded-lg border-2 border-gray-200 dark:border-gray-700 hover:border-primary-500 dark:hover:border-primary-500 transition-all"
                >
                  <svg
                    className="w-12 h-12 mx-auto mb-3 text-primary-500"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={1.5}
                      d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                    />
                  </svg>
                  <h3 className="font-semibold mb-2">수치 중심 요약</h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    통계와 수치 데이터를 중심으로 요약합니다
                  </p>
                </motion.button>
              </div>
            </>
          )}

          {isGenerating && (
            <div className="text-center py-12">
              <LoadingSpinner />
              <p className="mt-4 text-gray-600 dark:text-gray-400">
                AI가 요약을 생성하고 있습니다...
              </p>
            </div>
          )}

          {summaryResult && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-6"
            >
              <div>
                <h3 className="text-xl font-semibold mb-2">
                  {summaryResult.title}
                </h3>
                <p className="text-gray-600 dark:text-gray-400">
                  {summaryResult.summary}
                </p>
              </div>

              {summaryResult.key_points && (
                <div>
                  <h4 className="font-semibold mb-3">핵심 포인트</h4>
                  <ul className="space-y-2">
                    {summaryResult.key_points.map((point, index) => (
                      <li key={index} className="flex items-start">
                        <span className="text-primary-500 mr-2">•</span>
                        <span className="text-gray-700 dark:text-gray-300">
                          {point}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {summaryResult.key_quotes && (
                <div>
                  <h4 className="font-semibold mb-3">주요 인용문</h4>
                  <div className="space-y-3">
                    {summaryResult.key_quotes.map((quote, index) => (
                      <div
                        key={index}
                        className="pl-4 border-l-4 border-primary-500"
                      >
                        <p className="italic text-gray-700 dark:text-gray-300">
                          "{quote.quote}"
                        </p>
                        <p className="text-sm text-gray-500 mt-1">
                          - {quote.source}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {summaryResult.key_data && (
                <div>
                  <h4 className="font-semibold mb-3">주요 수치</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {summaryResult.key_data.map((data, index) => (
                      <div
                        key={index}
                        className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg"
                      >
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                          {data.metric}
                        </p>
                        <p className="text-2xl font-bold text-primary-600 dark:text-primary-400">
                          {data.value}
                        </p>
                        <p className="text-xs text-gray-500 mt-1">
                          {data.context}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                <p className="text-sm text-gray-500">
                  {summaryResult.articles_analyzed}개 기사 분석 완료 ·{" "}
                  {new Date(summaryResult.generated_at).toLocaleString()}
                </p>
              </div>
            </motion.div>
          )}
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

// 레포트 모달 컴포넌트
const ReportModal: React.FC<{
  isOpen: boolean;
  onClose: () => void;
  selectedCompany: Company | null;
  onGenerateReport: (type: ReportType) => void;
  reportResult: ReportResult | null;
  isGenerating: boolean;
  onViewArticleDetail?: (article: NewsArticle) => void;
}> = ({
  isOpen,
  onClose,
  selectedCompany,
  onGenerateReport,
  reportResult,
  isGenerating,
  onViewArticleDetail,
}) => {
  if (!isOpen || !selectedCompany) return null;

  // 인용 구문에 각주 링크 표시 함수
  const formatSummaryWithCitations = (summary: string) => {
    if (!summary) return "";

    // [기사 ref숫자] 패턴 찾기
    const citationPattern = /\[기사\s+(ref\d+)\]/g;

    // 각주 링크로 변환
    const formattedSummary = summary.replace(
      citationPattern,
      (match, refId) => {
        return `<sup class="citation-link" data-ref="${refId}">[${refId}]</sup>`;
      }
    );

    return formattedSummary;
  };

  // 인용 링크 클릭 이벤트 처리
  useEffect(() => {
    if (reportResult) {
      // 인용 링크에 클릭 이벤트 추가
      const citationLinks = document.querySelectorAll(".citation-link");

      citationLinks.forEach((link) => {
        link.addEventListener("click", (e) => {
          e.stopPropagation(); // 모달 닫힘 방지
          const refId = link.getAttribute("data-ref");

          if (refId) {
            // 해당 기사 요소 찾기
            const articleElement = document.getElementById(`article-${refId}`);

            if (articleElement) {
              // 기사로 스크롤
              articleElement.scrollIntoView({
                behavior: "smooth",
                block: "center",
              });

              // 강조 효과 주기
              articleElement.classList.add(
                "ring-2",
                "ring-primary-500",
                "ring-offset-2",
                "dark:ring-offset-gray-800"
              );

              // 강조 효과 제거 타이머
              setTimeout(() => {
                articleElement.classList.remove(
                  "ring-2",
                  "ring-primary-500",
                  "ring-offset-2",
                  "dark:ring-offset-gray-800"
                );
              }, 2000);
            }

            // 또는 직접 해당 기사 상세 보기 열기
            const article = (
              reportResult.detailed_articles || reportResult.articles
            ).find((a) => a.ref_id === refId);

            if (article && onViewArticleDetail) {
              // 기사 상세 모달 열기 - 주석 처리하고 스크롤 기능만 유지 (원하는 동작 선택)
              // onViewArticleDetail(article);
            }
          }
        });
      });

      // 클린업 함수
      return () => {
        citationLinks.forEach((link) => {
          link.removeEventListener("click", () => {});
        });
      };
    }
  }, [reportResult, onViewArticleDetail]);

  const reportTypes = [
    {
      id: "daily",
      label: "일간 레포트",
      description: "하루 동안의 주요 뉴스 요약",
    },
    {
      id: "weekly",
      label: "주간 레포트",
      description: "한 주간의 주요 동향 요약",
    },
    {
      id: "monthly",
      label: "월간 레포트",
      description: "한 달간의 주요 이슈 및 변화 분석",
    },
    {
      id: "quarterly",
      label: "분기별 레포트",
      description: "3개월간의 성과 및 전략 분석",
    },
    {
      id: "yearly",
      label: "연간 레포트",
      description: "1년간의 종합적인 기업 분석",
    },
  ];

  // 기사 클릭 핸들러
  const handleArticleClick = (article: NewsArticle) => {
    if (onViewArticleDetail) {
      onViewArticleDetail(article);
    }
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.9, opacity: 0 }}
          className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-4xl w-full max-h-[85vh] overflow-y-auto"
          onClick={(e) => e.stopPropagation()}
        >
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold">
              {reportResult
                ? `${selectedCompany.name} ${reportResult.report_type_kr} 레포트`
                : `${selectedCompany.name} 레포트 생성`}
            </h2>
            <button
              onClick={onClose}
              className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700"
            >
              <svg
                className="w-6 h-6"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>

          {!reportResult && !isGenerating && (
            <>
              <p className="mb-4 text-gray-600 dark:text-gray-400">
                {selectedCompany.name}에 대한 레포트 유형을 선택해주세요.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {reportTypes.map((type) => (
                  <motion.button
                    key={type.id}
                    whileHover={{ scale: 1.02 }}
                    onClick={() => onGenerateReport(type.id as ReportType)}
                    className="p-6 rounded-lg border-2 border-gray-200 dark:border-gray-700 hover:border-primary-500 dark:hover:border-primary-500 transition-all"
                  >
                    <div className="text-xl font-semibold mb-2">
                      {type.label}
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {type.description}
                    </p>
                  </motion.button>
                ))}
              </div>
            </>
          )}

          {isGenerating && (
            <div className="text-center py-12">
              <LoadingSpinner />
              <p className="mt-4 text-gray-600 dark:text-gray-400">
                {selectedCompany.name}의 레포트를 생성하고 있습니다...
              </p>
            </div>
          )}

          {reportResult && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-6"
            >
              <div>
                <div className="flex justify-between items-center mb-2">
                  <h3 className="text-xl font-semibold">레포트 요약</h3>
                  <span className="text-sm text-gray-500">
                    {reportResult.period.from} ~ {reportResult.period.to}
                  </span>
                </div>
                <div className="bg-gray-50 dark:bg-gray-700 p-6 rounded-lg">
                  <div className="prose dark:prose-invert max-w-none">
                    <div
                      className="whitespace-pre-line citation-text"
                      dangerouslySetInnerHTML={{
                        __html: formatSummaryWithCitations(
                          reportResult.summary
                        ),
                      }}
                    />
                  </div>
                </div>
              </div>

              <div>
                <h3 className="text-lg font-semibold mb-3">
                  분석에 사용된 뉴스 기사
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                  총 {reportResult.total_articles}개의 뉴스 기사가
                  분석되었습니다.
                  <span className="ml-2 text-primary-600 dark:text-primary-400">
                    (클릭하면 상세 내용을 볼 수 있습니다)
                  </span>
                </p>

                <div className="space-y-4 mt-4">
                  {/* 모든 기사 표시 (detailed_articles가 있으면 사용, 없으면 articles 사용) */}
                  {(
                    reportResult.detailed_articles || reportResult.articles
                  ).map((article) => (
                    <div
                      key={article.id || article.ref_id}
                      className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
                      onClick={() => handleArticleClick(article)}
                      id={
                        article.ref_id ? `article-${article.ref_id}` : undefined
                      }
                    >
                      <div className="flex justify-between items-start">
                        <h4 className="font-medium mb-2 flex-1">
                          {article.title}
                        </h4>
                        {article.ref_id && (
                          <span className="inline-flex items-center justify-center bg-primary-100 dark:bg-primary-900 text-primary-800 dark:text-primary-200 text-xs px-2 py-1 rounded-full ml-2">
                            {article.ref_id}
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2 mb-2">
                        {article.summary}
                      </p>
                      <div className="flex justify-between text-xs text-gray-500">
                        <span>{article.provider}</span>
                        <span>{article.published_at}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                <p className="text-sm text-gray-500">
                  {reportResult.total_articles}개 기사 분석 완료 ·{" "}
                  {new Date(reportResult.generated_at).toLocaleString()}
                </p>
              </div>
            </motion.div>
          )}
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

const NewsDetailModal: React.FC<{
  isOpen: boolean;
  onClose: () => void;
  article: NewsArticle | null;
}> = ({ isOpen, onClose, article }) => {
  if (!isOpen || !article) return null;

  const fetchFullContent = async () => {
    if (!article.content && article.id) {
      try {
        const response = await fetch(`/api/news/detail/${article.id}`);
        if (response.ok) {
          const data = await response.json();
          if (data.news && data.news.content) {
            article.content = data.news.content;
          }
        }
      } catch (error) {
        console.error("뉴스 본문 조회 실패:", error);
      }
    }
  };

  useEffect(() => {
    if (isOpen && article && !article.content) {
      fetchFullContent();
    }
  }, [isOpen, article]);

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.9, opacity: 0 }}
          className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-2xl w-full max-h-[80vh] overflow-y-auto"
          onClick={(e) => e.stopPropagation()}
        >
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-bold">{article.title}</h2>
            <button
              onClick={onClose}
              className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700"
            >
              <svg
                className="w-6 h-6"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>

          <div className="flex items-center justify-between text-sm text-gray-500 mb-4">
            <div className="flex items-center gap-2">
              <span className="font-medium">{article.provider}</span>
              {article.byline && <span>| {article.byline}</span>}
            </div>
            <span>{article.published_at || "날짜 정보 없음"}</span>
          </div>

          {article.content ? (
            <div className="prose dark:prose-invert max-w-none">
              <div className="whitespace-pre-line">{article.content}</div>
            </div>
          ) : (
            <div className="text-center py-8">
              <LoadingSpinner />
              <p className="mt-4 text-gray-600">본문을 불러오는 중입니다...</p>
            </div>
          )}

          {article.url && (
            <div className="mt-6 text-right">
              <a
                href={article.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
              >
                원문 보기
                <svg
                  className="w-4 h-4 ml-2"
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
              </a>
            </div>
          )}
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

/**
 * 관심종목 페이지 컴포넌트
 */
const WatchlistPage: React.FC = () => {
  const [watchlist, setWatchlist] = useState<Company[]>([]);
  const [selectedCompany, setSelectedCompany] = useState<Company | null>(null);
  const [timeline, setTimeline] = useState<TimelineItem[]>([]);
  const [selectedArticles, setSelectedArticles] = useState<
    Map<string, SelectedArticle>
  >(new Map());
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showSummaryModal, setShowSummaryModal] = useState(false);
  const [summaryResult, setSummaryResult] = useState<SummaryResult | null>(
    null
  );
  const [isGeneratingSummary, setIsGeneratingSummary] = useState(false);
  const [selectedArticle, setSelectedArticle] = useState<NewsArticle | null>(
    null
  );
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [showReportModal, setShowReportModal] = useState(false);
  const [reportResult, setReportResult] = useState<ReportResult | null>(null);
  const [isGeneratingReport, setIsGeneratingReport] = useState(false);

  useEffect(() => {
    fetchWatchlistSuggestions();
  }, []);

  useEffect(() => {
    if (selectedCompany) {
      fetchCompanyNews(selectedCompany);
    }
  }, [selectedCompany]);

  const fetchWatchlistSuggestions = async () => {
    try {
      const response = await fetch("/api/news/watchlist/suggestions");
      if (!response.ok) throw new Error("추천 종목을 불러오는데 실패했습니다");

      const data = await response.json();
      setWatchlist(data.suggestions);
      if (data.suggestions.length > 0) {
        setSelectedCompany(data.suggestions[0]);
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "알 수 없는 오류가 발생했습니다"
      );
    }
  };

  const fetchCompanyNews = async (company: Company) => {
    setIsLoading(true);
    setError(null);
    setSelectedArticles(new Map());

    try {
      const response = await fetch("/api/news/company", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ company_name: company.name }),
      });

      if (!response.ok) throw new Error("기업 뉴스를 불러오는데 실패했습니다");

      const data = await response.json();
      setTimeline(data.timeline);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "알 수 없는 오류가 발생했습니다"
      );
      // 더미 데이터
      setTimeline([
        {
          date: "2024-01-15",
          count: 3,
          articles: [
            {
              id: "1",
              title: `${company.name}, 신규 사업 진출 발표`,
              summary:
                "새로운 사업 영역으로 확장하며 성장 동력 확보에 나섰다...",
              provider: "서울경제",
              url: "#",
              category: "기업",
              byline: "홍길동 기자",
              images: [],
            },
            {
              id: "2",
              title: `${company.name} 4분기 실적 전망 상향`,
              summary: "애널리스트들이 4분기 실적 전망을 상향 조정했다...",
              provider: "한국경제",
              url: "#",
              category: "증권",
              byline: "김철수 기자",
              images: [],
            },
          ],
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const toggleArticleSelection = (article: NewsArticle) => {
    const newSelected = new Map(selectedArticles);

    if (newSelected.has(article.id)) {
      newSelected.delete(article.id);
    } else if (newSelected.size < 5) {
      newSelected.set(article.id, { ...article, isSelected: true });
    }

    setSelectedArticles(newSelected);
  };

  const handleGenerateSummary = async (type: SummaryType) => {
    setIsGeneratingSummary(true);
    setSummaryResult(null);

    try {
      const response = await fetch("/api/news/ai-summary", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          news_ids: Array.from(selectedArticles.keys()),
          summary_type: type,
        }),
      });

      if (!response.ok) throw new Error("AI 요약 생성에 실패했습니다");

      const data = await response.json();
      setSummaryResult(data);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "알 수 없는 오류가 발생했습니다"
      );
    } finally {
      setIsGeneratingSummary(false);
    }
  };

  // 레포트 생성 함수 추가
  const handleGenerateReport = async (type: ReportType) => {
    if (!selectedCompany) return;

    setIsGeneratingReport(true);
    setReportResult(null);

    try {
      const response = await fetch(
        `/api/news/company/${selectedCompany.name}/report/${type}`
      );

      if (!response.ok) throw new Error("레포트 생성에 실패했습니다");

      const data = await response.json();
      setReportResult(data);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "알 수 없는 오류가 발생했습니다"
      );
    } finally {
      setIsGeneratingReport(false);
    }
  };

  const viewArticleDetail = (article: NewsArticle) => {
    setSelectedArticle(article);
    setShowDetailModal(true);
  };

  const allArticles = timeline.flatMap((item) => item.articles);
  const topArticles = allArticles.slice(0, 5);

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={containerVariants}
      className="space-y-8"
    >
      <motion.div variants={itemVariants}>
        <h1 className="text-3xl font-bold mb-6">관심 종목</h1>

        {/* 관심 종목 리스트 */}
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 mb-8">
          {watchlist.map((company) => (
            <CompanyCard
              key={company.code}
              company={company}
              isActive={selectedCompany?.code === company.code}
              onClick={() => setSelectedCompany(company)}
            />
          ))}
        </div>
      </motion.div>

      {selectedCompany && (
        <>
          {/* 뉴스 캐러셀 */}
          <motion.div variants={itemVariants}>
            <NewsCarousel articles={topArticles} />
          </motion.div>

          {/* AI 요약 섹션 */}
          <motion.div
            variants={itemVariants}
            className="bg-gradient-to-r from-primary-50 to-primary-100 dark:from-primary-900/20 dark:to-primary-800/20 rounded-lg p-6"
          >
            <h2 className="text-xl font-semibold mb-4">AI 요약 분석</h2>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              최근 {selectedCompany.name} 관련 뉴스를 AI가 분석하여 핵심 내용을
              요약해드립니다.
            </p>
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p className="text-sm text-gray-500">
                {selectedArticles.size}개 기사 선택됨 (최대 5개)
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => setShowReportModal(true)}
                  className="px-6 py-2 rounded-lg font-medium transition-all bg-secondary-600 text-white hover:bg-secondary-700"
                >
                  <span className="flex items-center">
                    <svg
                      className="w-4 h-4 mr-2"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                      />
                    </svg>
                    기간별 레포트
                  </span>
                </button>
                <button
                  onClick={() => setShowSummaryModal(true)}
                  disabled={selectedArticles.size === 0}
                  className={`px-6 py-2 rounded-lg font-medium transition-all ${
                    selectedArticles.size > 0
                      ? "bg-primary-600 text-white hover:bg-primary-700"
                      : "bg-gray-300 text-gray-500 cursor-not-allowed"
                  }`}
                >
                  AI 요약 생성
                </button>
              </div>
            </div>
          </motion.div>

          {/* 타임라인 섹션 */}
          <motion.div variants={itemVariants}>
            <h2 className="text-xl font-semibold mb-4">뉴스 타임라인</h2>

            {error && <ErrorMessage message={error} />}

            {isLoading ? (
              <div className="flex justify-center py-12">
                <LoadingSpinner />
              </div>
            ) : (
              <div className="space-y-8 max-h-[600px] overflow-y-auto pr-4">
                {timeline.map((timelineItem) => (
                  <div key={timelineItem.date}>
                    <div className="flex items-center mb-4">
                      <div className="flex-shrink-0 w-24 text-sm font-medium text-gray-600 dark:text-gray-400">
                        {new Date(timelineItem.date).toLocaleDateString(
                          "ko-KR",
                          {
                            month: "long",
                            day: "numeric",
                          }
                        )}
                      </div>
                      <div className="flex-grow h-px bg-gray-200 dark:bg-gray-700 ml-4" />
                      <div className="ml-4 text-sm text-gray-500">
                        {timelineItem.count}건
                      </div>
                    </div>
                    <div className="ml-28 space-y-4">
                      {timelineItem.articles.map((article) => (
                        <NewsArticleCard
                          key={article.id}
                          article={{
                            ...article,
                            isSelected: selectedArticles.has(article.id),
                          }}
                          onToggle={() => toggleArticleSelection(article)}
                          onViewDetail={() => viewArticleDetail(article)}
                        />
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </motion.div>
        </>
      )}

      {/* AI 요약 모달 */}
      <SummaryModal
        isOpen={showSummaryModal}
        onClose={() => {
          setShowSummaryModal(false);
          setSummaryResult(null);
        }}
        selectedArticles={Array.from(selectedArticles.values())}
        onGenerateSummary={handleGenerateSummary}
        summaryResult={summaryResult}
        isGenerating={isGeneratingSummary}
      />

      {/* 레포트 모달 */}
      <ReportModal
        isOpen={showReportModal}
        onClose={() => {
          setShowReportModal(false);
          setReportResult(null);
        }}
        selectedCompany={selectedCompany}
        onGenerateReport={handleGenerateReport}
        reportResult={reportResult}
        isGenerating={isGeneratingReport}
        onViewArticleDetail={viewArticleDetail}
      />

      {/* 뉴스 상세 모달 추가 */}
      <NewsDetailModal
        isOpen={showDetailModal}
        onClose={() => setShowDetailModal(false)}
        article={selectedArticle}
      />
    </motion.div>
  );
};

export default WatchlistPage;
