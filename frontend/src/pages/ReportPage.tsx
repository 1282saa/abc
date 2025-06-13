import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useParams, useNavigate, useSearchParams } from "react-router-dom";
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
  images_caption?: string;
  published_at?: string;
  ref_id?: string;
}

type ReportType = "daily" | "weekly" | "monthly" | "quarterly" | "yearly";

// 이미지 URL 생성 유틸리티 함수
const getImageUrl = (rawPath: string | undefined): string | null => {
  if (!rawPath) {
    console.log("getImageUrl: rawPath is empty or undefined");
    return null;
  }

  // 여러 이미지 경로가 개행(\n)이나 콤마(,)로 구분되어 있는 경우 첫 번째만 사용
  const cleanPath = rawPath.split(/[\n,]+/)[0].trim();

  if (!cleanPath || cleanPath === "") {
    console.log("getImageUrl: cleanPath is empty after processing:", rawPath);
    return null;
  }

  // 이미지 경로가 이미 전체 URL인 경우
  if (cleanPath.startsWith("http://") || cleanPath.startsWith("https://")) {
    console.log("getImageUrl: Full URL detected:", cleanPath);
    return cleanPath;
  }

  // BigKinds 이미지 서버 URL과 결합 (실제 확인된 도메인 사용)
  const baseUrl = "https://www.bigkinds.or.kr/resources/images";
  const finalPath = cleanPath.startsWith("/") ? cleanPath : `/${cleanPath}`;
  const fullUrl = `${baseUrl}${finalPath}`;

  console.log("getImageUrl: Generated URL:", {
    rawPath,
    cleanPath,
    finalPath,
    fullUrl,
  });

  return fullUrl;
};

// 이미지 유효성 검증 함수
const hasValidImage = (article: NewsArticle): boolean => {
  return !!(
    article.images &&
    article.images.length > 0 &&
    article.images[0] &&
    article.images[0].trim() !== ""
  );
};

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

const ReportPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [selectedCompany, setSelectedCompany] = useState<Company | null>(null);
  const [reportResult, setReportResult] = useState<ReportResult | null>(null);
  const [isGeneratingReport, setIsGeneratingReport] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // URL에서 회사 정보 가져오기
  useEffect(() => {
    const companyName = searchParams.get("company");
    const companyCode = searchParams.get("code");
    const companyCategory = searchParams.get("category");

    if (companyName) {
      setSelectedCompany({
        name: companyName,
        code: companyCode || "",
        category: companyCategory || "",
      });
    }
  }, [searchParams]);

  // 인용 구문에 각주 링크 표시 함수
  const formatSummaryWithCitations = (summary: string) => {
    if (!summary) return "";

    const citationPattern = /\[기사\s+(ref\d+)\]/g;
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
      const citationLinks = document.querySelectorAll(".citation-link");

      citationLinks.forEach((link) => {
        link.addEventListener("click", (e) => {
          e.stopPropagation();
          const refId = link.getAttribute("data-ref");

          if (refId) {
            const articleElement = document.getElementById(`article-${refId}`);

            if (articleElement) {
              articleElement.scrollIntoView({
                behavior: "smooth",
                block: "center",
              });

              articleElement.classList.add(
                "ring-2",
                "ring-primary-500",
                "ring-offset-2",
                "dark:ring-offset-gray-800"
              );

              setTimeout(() => {
                articleElement.classList.remove(
                  "ring-2",
                  "ring-primary-500",
                  "ring-offset-2",
                  "dark:ring-offset-gray-800"
                );
              }, 2000);
            }
          }
        });
      });

      return () => {
        citationLinks.forEach((link) => {
          link.removeEventListener("click", () => {});
        });
      };
    }
  }, [reportResult]);

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

  const handleGenerateReport = async (type: ReportType) => {
    if (!selectedCompany) return;

    setIsGeneratingReport(true);
    setReportResult(null);
    setError(null);

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

  const handleArticleClick = (article: NewsArticle) => {
    if (article.id) {
      navigate(`/news/${article.id}`);
    }
  };

  const handleBack = () => {
    navigate(-1);
  };

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={containerVariants}
      className="min-h-screen bg-gray-50 dark:bg-gray-900"
    >
      {/* 헤더 */}
      <div className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-6xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={handleBack}
                className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
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
                    d="M10 19l-7-7m0 0l7-7m-7 7h18"
                  />
                </svg>
              </button>
              <h1 className="text-2xl font-bold">
                {reportResult && selectedCompany
                  ? `${selectedCompany.name} ${reportResult.report_type_kr} 레포트`
                  : selectedCompany
                  ? `${selectedCompany.name} 레포트 생성`
                  : "기간별 레포트 생성"}
              </h1>
            </div>
            {reportResult && (
              <button
                onClick={() => window.print()}
                className="px-4 py-2 bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-300 rounded-lg hover:bg-primary-200 dark:hover:bg-primary-800 transition-colors"
              >
                <span className="flex items-center gap-2">
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    className="h-5 w-5"
                    viewBox="0 0 20 20"
                    fill="currentColor"
                  >
                    <path
                      fillRule="evenodd"
                      d="M5 4v3H4a2 2 0 00-2 2v3a2 2 0 002 2h1v2a2 2 0 002 2h6a2 2 0 002-2v-2h1a2 2 0 002-2V9a2 2 0 00-2-2h-1V4a2 2 0 00-2-2H7a2 2 0 00-2 2zm8 0H7v3h6V4zm0 8H7v4h6v-4z"
                      clipRule="evenodd"
                    />
                  </svg>
                  인쇄
                </span>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* 메인 컨텐츠 */}
      <div className="max-w-6xl mx-auto p-6">
        <motion.div variants={itemVariants}>
          {error && <ErrorMessage message={error} />}

          {!reportResult && !isGeneratingReport && selectedCompany && (
            <>
              <p className="mb-6 text-gray-600 dark:text-gray-400 text-lg">
                {selectedCompany.name}에 대한 레포트 유형을 선택해주세요.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {reportTypes.map((type) => (
                  <motion.button
                    key={type.id}
                    whileHover={{ scale: 1.02 }}
                    onClick={() => handleGenerateReport(type.id as ReportType)}
                    className="p-8 rounded-xl border-2 border-gray-200 dark:border-gray-700 hover:border-primary-500 dark:hover:border-primary-500 transition-all bg-white dark:bg-gray-800 shadow-sm hover:shadow-md"
                  >
                    <div className="text-xl font-semibold mb-3">
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

          {!reportResult && !isGeneratingReport && !selectedCompany && (
            <div className="text-center py-12">
              <p className="text-gray-600 dark:text-gray-400 text-lg mb-4">
                회사 정보가 없습니다.
              </p>
              <button
                onClick={handleBack}
                className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
              >
                돌아가기
              </button>
            </div>
          )}

          {isGeneratingReport && (
            <div className="text-center py-12">
              <LoadingSpinner />
              <p className="mt-4 text-gray-600 dark:text-gray-400 text-lg">
                {selectedCompany?.name || "선택된 기업"}의 레포트를 생성하고
                있습니다...
              </p>
            </div>
          )}

          {reportResult && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-8"
            >
              <div className="bg-white dark:bg-gray-800 rounded-xl p-8 shadow-sm">
                <div className="flex justify-between items-center mb-4">
                  <h2 className="text-2xl font-semibold">레포트 요약</h2>
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

              <div className="bg-white dark:bg-gray-800 rounded-xl p-8 shadow-sm">
                <h3 className="text-xl font-semibold mb-4">
                  분석에 사용된 뉴스 기사
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
                  총 {reportResult.total_articles}개의 뉴스 기사가
                  분석되었습니다.
                  <span className="ml-2 text-primary-600 dark:text-primary-400">
                    (클릭하면 상세 내용을 볼 수 있습니다)
                  </span>
                </p>

                <div className="space-y-4">
                  {(
                    reportResult.detailed_articles || reportResult.articles
                  ).map((article) => (
                    <div
                      key={article.id || article.ref_id}
                      className="border border-gray-200 dark:border-gray-700 rounded-lg p-6 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
                      onClick={() => handleArticleClick(article)}
                      id={
                        article.ref_id ? `article-${article.ref_id}` : undefined
                      }
                    >
                      <div className="flex gap-4">
                        {/* 이미지 영역 */}
                        {(() => {
                          const imageUrl = getImageUrl(article.images?.[0]);
                          return hasValidImage(article) && imageUrl ? (
                            <div className="flex-shrink-0 w-32 h-24 overflow-hidden rounded-lg shadow-sm">
                              <img
                                src={imageUrl}
                                alt={
                                  article.images_caption ||
                                  article.title ||
                                  "뉴스 이미지"
                                }
                                className="w-full h-full object-cover"
                                loading="lazy"
                                onError={(e) => {
                                  console.log(
                                    "Report image load failed for URL:",
                                    imageUrl
                                  );
                                  const img =
                                    e.currentTarget as HTMLImageElement;
                                  img.style.display = "none";
                                  // 부모 div에 플레이스홀더 추가
                                  const parent = img.parentElement;
                                  if (
                                    parent &&
                                    !parent.querySelector(
                                      ".fallback-placeholder"
                                    )
                                  ) {
                                    parent.innerHTML = `
                                      <div class="fallback-placeholder w-full h-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center">
                                        <svg class="w-10 h-10 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                                        </svg>
                                      </div>
                                    `;
                                  }
                                }}
                                onLoad={() => {
                                  console.log(
                                    "Report image loaded successfully:",
                                    imageUrl
                                  );
                                }}
                              />
                            </div>
                          ) : null;
                        })()}

                        {/* 텍스트 영역 */}
                        <div className="flex-1 min-w-0">
                          <div className="flex justify-between items-start mb-2">
                            <h4 className="font-medium text-lg line-clamp-2 pr-2">
                              {article.title}
                            </h4>
                            {article.ref_id && (
                              <span className="inline-flex items-center justify-center bg-primary-100 dark:bg-primary-900 text-primary-800 dark:text-primary-200 text-xs px-3 py-1 rounded-full ml-2 flex-shrink-0">
                                {article.ref_id}
                              </span>
                            )}
                          </div>
                          <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2 mb-3">
                            {article.summary}
                          </p>
                          <div className="flex justify-between text-xs text-gray-500">
                            <span>{article.provider}</span>
                            <span>{article.published_at}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="bg-white dark:bg-gray-800 rounded-xl p-8 shadow-sm">
                <div className="text-sm text-gray-500 text-center">
                  {reportResult.total_articles}개 기사 분석 완료 ·{" "}
                  {new Date(reportResult.generated_at).toLocaleString()} ·{" "}
                  {reportResult.model_used}
                </div>
              </div>
            </motion.div>
          )}
        </motion.div>
      </div>
    </motion.div>
  );
};

export default ReportPage;
