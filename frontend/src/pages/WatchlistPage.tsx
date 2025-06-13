import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { containerVariants, itemVariants } from "../animations/pageAnimations";
import LoadingSpinner from "../components/common/LoadingSpinner";
import ErrorMessage from "../components/common/ErrorMessage";
import { useNavigate, useLocation } from "react-router-dom";

interface Company {
  name: string;
  code: string;
  category: string;
}

interface Category {
  key: string;
  name: string;
  count: number;
  description?: string;
  icon?: string;
}

interface NewsArticle {
  id: string;
  title: string;
  summary: string;
  content?: string;
  provider: string;
  provider_code?: string;
  url: string;
  category: string;
  byline: string;
  images: string[];
  images_caption?: string;
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

// 기존 타입 정의 수정
type SummaryType = "issue" | "quote" | "data" | "integrated";

// 레포트 타입 정의
type ReportType = "daily" | "weekly" | "monthly" | "quarterly" | "yearly";

// 이미지 URL 생성 유틸리티 함수
const getImageUrl = (rawPath: string | undefined): string | null => {
  if (!rawPath) {
    console.log("getImageUrl: rawPath is empty or undefined");
    return null;
  }

  console.log("getImageUrl: 원본 입력값:", JSON.stringify(rawPath));

  try {
    // 전체 경로 가져오기 (이스케이프된 문자 처리)
    // 예: "/02100311/2025/06/08/02100311.20250608161705001.01.jpg\n/02100311/2025/06/08/02100311.20250608161705001.02.jpg"
    let firstPath = "";

    // 1. 개행 문자를 실제 줄바꿈으로 변환
    const unescaped = rawPath.replace(/\\\\n/g, "\\n").replace(/\\n/g, "\n");

    // 2. 줄바꿈 또는 콤마로 분리하여 첫 번째 경로 추출
    const pathParts = unescaped.split(/[\n,]+/);
    firstPath = pathParts[0]?.trim() || "";

    // 3. 추출된 경로 검증
    if (!firstPath || firstPath === "" || firstPath === "/") {
      console.log("getImageUrl: 첫 번째 경로 추출 실패, 전체 경로 사용 시도");

      // 전체 문자열이 유효한 경로인지 확인
      const fullPathMatch = rawPath.match(
        /\/\d+\/\d{4}\/\d{2}\/\d{2}\/[\w\.]+\.(jpg|png|gif|jpeg)/i
      );
      if (fullPathMatch) {
        firstPath = fullPathMatch[0];
        console.log("getImageUrl: 정규식으로 경로 추출 성공:", firstPath);
      } else {
        console.log("getImageUrl: 유효한 경로를 찾을 수 없음");
        return null;
      }
    }

    console.log("getImageUrl: 추출된 경로:", firstPath);

    // 이미지 경로가 이미 전체 URL인 경우
    if (firstPath.startsWith("http://") || firstPath.startsWith("https://")) {
      console.log("getImageUrl: 전체 URL 감지:", firstPath);
      return `/api/proxy/image?url=${encodeURIComponent(firstPath)}`;
    }

    // 경로 정규화 (슬래시로 시작하는지 확인)
    const normalizedPath = firstPath.startsWith("/")
      ? firstPath
      : `/${firstPath}`;

    // BigKinds 이미지 서버 기본 URL
    const baseUrl = "https://www.bigkinds.or.kr/resources/images";

    // 최종 URL 생성
    const fullImageUrl = `${baseUrl}${normalizedPath}`;
    console.log("getImageUrl: 최종 URL:", fullImageUrl);

    // 프록시 URL 반환
    return `/api/proxy/image?url=${encodeURIComponent(fullImageUrl)}`;
  } catch (error) {
    console.error("getImageUrl: 이미지 URL 생성 중 오류 발생", error);
    return null;
  }
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

// 레포트 결과 인터페이스
interface ReportResult {
  success?: boolean;
  company?: string;
  report_type?: ReportType;
  report_type_kr?: string;
  reference_date?: string;
  period?: {
    from: string;
    to: string;
  };
  total_articles?: number;
  articles?: NewsArticle[];
  detailed_articles?: NewsArticle[];
  summary?: string;
  generated_at?: string;
  model_used?: string;
  title?: string;
  content?: string;
  sources?: any[];
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

const CategoryCard: React.FC<{
  category: Category;
  onClick: () => void;
}> = ({ category, onClick }) => (
  <motion.div
    className="group relative overflow-hidden cursor-pointer transition-all duration-300 hover:shadow-2xl bg-gradient-to-br from-white via-gray-50/50 to-primary-50/30 dark:from-gray-800 dark:via-gray-800/90 dark:to-primary-900/20 border border-gray-200/60 dark:border-gray-700/60 rounded-xl backdrop-blur-sm"
    whileHover={{ scale: 1.02, y: -8 }}
    whileTap={{ scale: 0.98 }}
    onClick={onClick}
  >
    {/* 배경 그라데이션 효과 */}
    <div className="absolute inset-0 bg-gradient-to-br from-primary-400/5 via-transparent to-secondary-400/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

    {/* 메인 콘텐츠 */}
    <div className="relative p-6">
      <div className="flex items-start justify-between mb-4">
        <div className="text-4xl transform transition-transform duration-300 group-hover:scale-110 group-hover:rotate-3">
          {category.icon}
        </div>
        <span className="text-xs font-medium text-primary-600 dark:text-primary-400 bg-primary-100/80 dark:bg-primary-900/40 px-3 py-1.5 rounded-full border border-primary-200/50 dark:border-primary-800/50 backdrop-blur-sm">
          {category.count}개 종목
        </span>
      </div>

      <h3 className="font-bold text-xl mb-3 text-gray-900 dark:text-white group-hover:text-primary-700 dark:group-hover:text-primary-300 transition-colors">
        {category.name}
      </h3>

      <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2 leading-relaxed">
        {category.description}
      </p>

      {/* 호버 시 나타나는 화살표 */}
      <div className="absolute bottom-4 right-4 opacity-0 group-hover:opacity-100 transform translate-x-2 group-hover:translate-x-0 transition-all duration-300">
        <svg
          className="w-5 h-5 text-primary-500"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M13 7l5 5m0 0l-5 5m5-5H6"
          />
        </svg>
      </div>
    </div>

    {/* 테두리 빛 효과 */}
    <div className="absolute inset-0 rounded-xl border border-primary-300/0 group-hover:border-primary-300/30 dark:group-hover:border-primary-600/30 transition-all duration-300" />
  </motion.div>
);

const NewsArticleCard: React.FC<{
  article: SelectedArticle;
  onToggle: () => void;
  onViewDetail: () => void;
  showProviderBadge?: boolean;
}> = ({ article, onToggle, onViewDetail, showProviderBadge = false }) => (
  <motion.div
    className="group relative p-5 bg-white/90 dark:bg-gray-800/90 border border-gray-200/60 dark:border-gray-700/60 rounded-xl cursor-pointer transition-all duration-300 hover:shadow-xl hover:shadow-primary-500/10 dark:hover:shadow-primary-400/10 hover:border-primary-300/50 dark:hover:border-primary-600/50 backdrop-blur-sm overflow-hidden"
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    exit={{ opacity: 0, y: -20 }}
    whileHover={{ scale: 1.01, y: -2 }}
    onClick={onViewDetail}
  >
    {/* 배경 그라데이션 효과 */}
    <div className="absolute inset-0 bg-gradient-to-br from-primary-50/20 via-transparent to-secondary-50/20 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

    {/* 체크박스 */}
    <div
      className="absolute top-5 right-5 z-10 opacity-60 group-hover:opacity-100 transition-opacity"
      onClick={(e) => {
        e.stopPropagation();
        onToggle();
      }}
    >
      <div
        className={`relative w-6 h-6 rounded-lg border-2 transition-all ${
          article.isSelected
            ? "bg-primary-500 border-primary-500 shadow-lg shadow-primary-500/30"
            : "bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 hover:border-primary-400"
        }`}
      >
        <input
          type="checkbox"
          checked={article.isSelected}
          onChange={(e) => {
            e.stopPropagation();
            onToggle();
          }}
          className="sr-only"
        />
        {article.isSelected && (
          <svg
            className="absolute inset-1 w-4 h-4 text-white"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fillRule="evenodd"
              d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
              clipRule="evenodd"
            />
          </svg>
        )}
      </div>
    </div>

    {/* 메인 콘텐츠 */}
    <div className="relative flex gap-5">
      {/* 이미지 영역 - 좌측 */}
      {(() => {
        const imageUrl = getImageUrl(article.images?.[0]);
        return hasValidImage(article) && imageUrl ? (
          <div className="flex-shrink-0 w-24 h-20 overflow-hidden rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
            <img
              src={imageUrl}
              alt={article.images_caption || article.title || "뉴스 이미지"}
              className="w-full h-full object-cover"
              loading="lazy"
              style={{
                minWidth: "96px",
                minHeight: "80px",
                backgroundColor: "#f8f9fa", // 이미지 로드 전 배경색
              }}
              onError={(e) => {
                console.error("Image load failed!", {
                  imageUrl,
                  rawPath: article.images?.[0],
                });

                const img = e.currentTarget as HTMLImageElement;

                // 최종적으로 실패하면 플레이스홀더 표시
                img.style.display = "none";
                const parent = img.parentElement;
                if (parent && !parent.querySelector(".fallback-placeholder")) {
                  parent.innerHTML = `
                    <div class="fallback-placeholder w-full h-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center">
                      <svg class="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                    </div>
                  `;
                }
              }}
              onLoad={() => {
                console.log("Image loaded successfully:", imageUrl);
              }}
            />
          </div>
        ) : (
          // 이미지가 없을 때 기본 플레이스홀더
          <div className="flex-shrink-0 w-24 h-20 bg-gradient-to-br from-gray-100 to-gray-200 dark:from-gray-700 dark:to-gray-800 rounded-lg flex items-center justify-center border border-gray-200/50 dark:border-gray-600/50">
            <svg
              className="w-8 h-8 text-gray-400 opacity-60"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
              />
            </svg>
          </div>
        );
      })()}

      {/* 텍스트 영역 - 우측 */}
      <div className="flex-1 min-w-0 pr-10">
        <h4 className="font-semibold text-lg mb-3 line-clamp-2 text-gray-900 dark:text-white group-hover:text-primary-700 dark:group-hover:text-primary-300 transition-colors leading-tight">
          {article.title}
        </h4>

        <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-3 mb-4 leading-relaxed">
          {article.summary}
        </p>

        <div className="flex justify-between items-center">
          <div className="flex items-center gap-3">
            {showProviderBadge ? (
              <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-gradient-to-r from-blue-100 to-blue-200 text-blue-800 dark:from-blue-900/50 dark:to-blue-800/50 dark:text-blue-200 border border-blue-200/50 dark:border-blue-700/50">
                {article.provider}
              </span>
            ) : (
              <span className="text-xs text-gray-500 font-medium">
                {article.provider}
              </span>
            )}
            {article.byline && (
              <span className="text-xs text-gray-400 hidden sm:inline">
                · {article.byline}
              </span>
            )}
          </div>

          <div className="flex items-center gap-2">
            <span className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-gray-100/80 dark:bg-gray-700/80 text-gray-600 dark:text-gray-400 border border-gray-200/50 dark:border-gray-600/50">
              {article.category}
            </span>

            {/* 호버 시 나타나는 읽기 버튼 */}
            <div className="opacity-0 group-hover:opacity-100 transform translate-x-2 group-hover:translate-x-0 transition-all duration-300">
              <svg
                className="w-4 h-4 text-primary-500"
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
            </div>
          </div>
        </div>
        {/* 디버깅용 - 이미지 정보 표시 */}
        {process.env.NODE_ENV === "development" && (
          <div className="text-xs text-blue-500 mt-1 space-y-1 bg-blue-50 dark:bg-blue-900/20 p-2 rounded">
            <div>
              <strong>원본 배열:</strong> {JSON.stringify(article.images)}
            </div>
            <div>
              <strong>첫번째 원소:</strong> "
              {article.images?.[0] || "undefined"}"
            </div>
            <div>
              <strong>원소 길이:</strong> {article.images?.[0]?.length || 0}
            </div>
            {article.images?.[0] && (
              <div>
                <strong>분리 후:</strong> "
                {(() => {
                  try {
                    // 디버그 표시를 위한 경로 파싱
                    const raw = article.images[0];
                    // 이스케이프된 문자 처리
                    const unescaped = raw
                      .replace(/\\\\n/g, "\\n")
                      .replace(/\\n/g, "\n");
                    // 줄바꿈 또는 콤마로 분리
                    const pathParts = unescaped.split(/[\n,]+/);
                    // 첫 번째 경로 반환
                    return pathParts[0]?.trim() || "분리 실패";
                  } catch (e) {
                    return "파싱 오류";
                  }
                })()}
                "
              </div>
            )}
            <div>
              <strong>최종 URL:</strong>{" "}
              {getImageUrl(article.images?.[0]) || "null"}
            </div>
            <div>
              <strong>유효성:</strong>{" "}
              {hasValidImage(article) ? "유효" : "무효"}
            </div>
          </div>
        )}
      </div>
    </div>

    {/* 보더 그로우 효과 */}
    <div className="absolute inset-0 rounded-xl border border-transparent group-hover:border-primary-200/50 dark:group-hover:border-primary-700/50 transition-all duration-300 pointer-events-none" />
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
            <div className="flex gap-4">
              {/* 이미지 영역 - 좌측 */}
              {(() => {
                const currentArticle = articles[currentIndex];
                const imageUrl = getImageUrl(currentArticle?.images?.[0]);
                return hasValidImage(currentArticle) && imageUrl ? (
                  <div className="flex-shrink-0 w-32 h-24 overflow-hidden rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
                    <img
                      src={imageUrl}
                      alt={
                        currentArticle.images_caption ||
                        currentArticle.title ||
                        "뉴스 이미지"
                      }
                      className="w-full h-full object-cover"
                      loading="lazy"
                      style={{
                        minWidth: "96px",
                        minHeight: "80px",
                        backgroundColor: "#f8f9fa", // 이미지 로드 전 배경색
                      }}
                      onError={(e) => {
                        console.error("Image load failed!", {
                          imageUrl,
                          rawPath: currentArticle.images?.[0],
                        });

                        const img = e.currentTarget as HTMLImageElement;

                        // 최종적으로 실패하면 플레이스홀더 표시
                        img.style.display = "none";
                        const parent = img.parentElement;
                        if (
                          parent &&
                          !parent.querySelector(".fallback-placeholder")
                        ) {
                          parent.innerHTML = `
                            <div class="fallback-placeholder w-full h-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center">
                              <svg class="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                              </svg>
                            </div>
                          `;
                        }
                      }}
                      onLoad={() => {
                        console.log("Image loaded successfully:", imageUrl);
                      }}
                    />
                  </div>
                ) : (
                  // 이미지가 없을 때 기본 플레이스홀더
                  <div className="flex-shrink-0 w-32 h-24 bg-gray-100 dark:bg-gray-700 rounded-lg flex items-center justify-center">
                    <svg
                      className="w-8 h-8 text-gray-400"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                      />
                    </svg>
                  </div>
                );
              })()}

              {/* 텍스트 영역 - 우측 */}
              <div className="flex-1 min-w-0">
                <h4 className="font-medium mb-2">
                  {articles[currentIndex].title}
                </h4>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {articles[currentIndex].summary}
                </p>
                <div className="mt-3 text-xs text-gray-500">
                  {articles[currentIndex].provider} ·{" "}
                  {articles[currentIndex].category}
                </div>
                {/* 디버깅용 - 이미지 정보 표시 */}
                {process.env.NODE_ENV === "development" && (
                  <div className="text-xs text-blue-500 mt-1 space-y-1 bg-blue-50 dark:bg-blue-900/20 p-2 rounded">
                    <div>
                      <strong>캐러셀 원본:</strong>{" "}
                      {JSON.stringify(articles[currentIndex].images)}
                    </div>
                    <div>
                      <strong>첫번째 원소:</strong> "
                      {articles[currentIndex].images?.[0] || "undefined"}"
                    </div>
                    <div>
                      <strong>원소 길이:</strong>{" "}
                      {articles[currentIndex].images?.[0]?.length || 0}
                    </div>
                    {articles[currentIndex].images?.[0] && (
                      <div>
                        <strong>분리 후:</strong> "
                        {(() => {
                          try {
                            // 디버그 표시를 위한 경로 파싱
                            const raw = articles[currentIndex].images[0];
                            // 이스케이프된 문자 처리
                            const unescaped = raw
                              .replace(/\\\\n/g, "\\n")
                              .replace(/\\n/g, "\n");
                            // 줄바꿈 또는 콤마로 분리
                            const pathParts = unescaped.split(/[\n,]+/);
                            // 첫 번째 경로 반환
                            return pathParts[0]?.trim() || "분리 실패";
                          } catch (e) {
                            return "파싱 오류";
                          }
                        })()}
                        "
                      </div>
                    )}
                    <div>
                      <strong>최종 URL:</strong>{" "}
                      {getImageUrl(articles[currentIndex].images?.[0]) ||
                        "null"}
                    </div>
                    <div>
                      <strong>유효성:</strong>{" "}
                      {hasValidImage(articles[currentIndex]) ? "유효" : "무효"}
                    </div>
                  </div>
                )}
              </div>
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

// 기존 SummaryModal 컴포넌트를 제거하고 AISummarySidebar 컴포넌트 추가
const AISummarySidebar: React.FC<{
  isVisible: boolean;
  selectedArticles: NewsArticle[];
  onGenerateSummary: () => void;
  summaryResult: SummaryResult | null;
  isGenerating: boolean;
  onClose: () => void;
}> = ({
  isVisible,
  selectedArticles,
  onGenerateSummary,
  summaryResult,
  isGenerating,
  onClose,
}) => {
  return (
    <motion.div
      initial={{ x: 400 }}
      animate={{ x: isVisible ? 0 : 350 }}
      transition={{ type: "spring", damping: 25, stiffness: 120 }}
      className="fixed top-0 right-0 h-screen w-96 bg-white dark:bg-gray-800 shadow-xl border-l border-gray-200 dark:border-gray-700 z-40 overflow-hidden"
    >
      {/* 사이드바 토글 버튼 */}
      <button
        onClick={onClose}
        className={`absolute top-1/2 left-0 transform -translate-y-1/2 -translate-x-1/2 w-10 h-20 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-l-xl flex items-center justify-center shadow-lg hover:shadow-xl transition-all ${
          isVisible ? "rotate-0" : "rotate-180"
        }`}
        aria-label={isVisible ? "사이드바 닫기" : "사이드바 열기"}
      >
        <div className="flex items-center justify-center w-full h-full bg-gradient-to-r from-primary-50 to-primary-100 dark:from-primary-900/30 dark:to-primary-800/30">
          <svg
            className="w-5 h-5 text-primary-600 dark:text-primary-400"
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
        </div>
      </button>

      <div className="h-full overflow-y-auto">
        <div className="p-6 space-y-6">
          <div className="flex justify-between items-center">
            <h2 className="text-2xl font-bold">AI 요약 분석</h2>
            <div className="flex items-center gap-2">
              <div
                className={`w-3 h-3 rounded-full ${
                  selectedArticles.length > 0
                    ? "bg-green-400 animate-pulse"
                    : "bg-gray-300"
                }`}
              />
              <span className="text-sm text-gray-500">
                {selectedArticles.length}/5
              </span>
            </div>
          </div>

          {!summaryResult && !isGenerating && (
            <>
              <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
                <h3 className="font-semibold mb-2">선택된 기사</h3>
                <div className="space-y-2 max-h-[300px] overflow-y-auto">
                  {selectedArticles.length > 0 ? (
                    selectedArticles.map((article) => (
                      <div
                        key={article.id}
                        className="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg"
                      >
                        <p className="font-medium text-sm line-clamp-2">
                          {article.title}
                        </p>
                        <p className="text-xs text-gray-500 mt-1">
                          {article.provider}
                        </p>
                      </div>
                    ))
                  ) : (
                    <p className="text-sm text-gray-500">
                      타임라인에서 기사를 선택해주세요.
                    </p>
                  )}
                </div>
              </div>

              <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  onClick={onGenerateSummary}
                  disabled={selectedArticles.length === 0}
                  className={`w-full px-4 py-3 rounded-lg font-medium transition-all flex items-center justify-center gap-2 ${
                    selectedArticles.length > 0
                      ? "bg-primary-500 hover:bg-primary-600 text-white"
                      : "bg-gray-200 dark:bg-gray-700 text-gray-400 cursor-not-allowed"
                  }`}
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
                      d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                    />
                  </svg>
                  AI 요약 생성하기
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

              {summaryResult.key_points &&
                summaryResult.key_points.length > 0 && (
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

              {summaryResult.key_quotes &&
                summaryResult.key_quotes.length > 0 && (
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

              {summaryResult.key_data && summaryResult.key_data.length > 0 && (
                <div>
                  <h4 className="font-semibold mb-3">주요 수치</h4>
                  <div className="grid grid-cols-1 gap-4">
                    {summaryResult.key_data.map((data, index) => (
                      <div
                        key={index}
                        className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg"
                      >
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                          {data.metric}
                        </p>
                        <p className="text-xl font-bold text-primary-600 dark:text-primary-400">
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
        </div>
      </div>
    </motion.div>
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
  const navigate = useNavigate();
  const location = useLocation();

  // URL에서 레포트 상태 복원을 위한 상태 체크
  useEffect(() => {
    // URL에 reportType 파라미터가 있으면 레포트 유지
    const params = new URLSearchParams(location.search);
    const reportType = params.get("reportType");

    // 레포트 결과가 없고, reportType이 있으면 레포트 다시 로드
    if (!reportResult && reportType && selectedCompany) {
      onGenerateReport(reportType as ReportType);
    }
  }, [location, reportResult, selectedCompany]);

  // 모달 열릴 때 URL 상태 업데이트
  useEffect(() => {
    if (isOpen && reportResult && selectedCompany) {
      // 현재 URL에 reportType 추가
      const params = new URLSearchParams(location.search);
      if (reportResult.report_type) {
        params.set("reportType", reportResult.report_type);
      }
      params.set("company", selectedCompany.name);

      // URL 업데이트 (리로드 없이)
      navigate(`${location.pathname}?${params.toString()}`, { replace: true });
    }
  }, [isOpen, reportResult, selectedCompany]);

  // 모달 닫을 때 처리
  const handleClose = () => {
    // URL에서 reportType 제거
    const params = new URLSearchParams(location.search);
    params.delete("reportType");
    params.delete("company");

    // URL 업데이트 (리로드 없이)
    navigate(`${location.pathname}?${params.toString()}`, { replace: true });

    // 모달 닫기
    onClose();
  };

  if (!isOpen) return null;

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
            const article =
              reportResult?.detailed_articles?.find(
                (a) => a.ref_id === refId
              ) || reportResult?.articles?.find((a) => a.ref_id === refId);

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
    // 새 창으로 기사 열기
    if (article.id) {
      window.open(`/news/${article.id}`, "_blank");
    } else if (onViewArticleDetail) {
      onViewArticleDetail(article);
    }
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black bg-opacity-80 flex z-50 p-0 overflow-hidden"
        onClick={handleClose}
      >
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.9, opacity: 0 }}
          className="bg-white dark:bg-gray-800 w-full h-full overflow-y-auto"
          onClick={(e) => e.stopPropagation()}
        >
          <div className="sticky top-0 z-10 bg-white dark:bg-gray-800 shadow-md p-4 flex justify-between items-center">
            <h2 className="text-2xl font-bold">
              {reportResult && selectedCompany
                ? `${selectedCompany.name} ${reportResult.report_type_kr} 레포트`
                : selectedCompany
                ? `${selectedCompany.name} 레포트 생성`
                : "기간별 레포트 생성"}
            </h2>
            <div className="flex items-center gap-4">
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
              <button
                onClick={handleClose}
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
          </div>

          <div className="max-w-6xl mx-auto p-6">
            {!reportResult && !isGenerating && (
              <>
                <p className="mb-4 text-gray-600 dark:text-gray-400">
                  {selectedCompany?.name
                    ? `${selectedCompany.name}에 대한`
                    : ""}{" "}
                  레포트 유형을 선택해주세요.
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
                  {selectedCompany?.name || "선택된 기업"}의 레포트를 생성하고
                  있습니다...
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
                      {reportResult?.period?.from} ~ {reportResult?.period?.to}
                    </span>
                  </div>
                  <div className="bg-gray-50 dark:bg-gray-700 p-6 rounded-lg">
                    <div className="prose dark:prose-invert max-w-none">
                      <div
                        className="whitespace-pre-line citation-text"
                        dangerouslySetInnerHTML={{
                          __html: formatSummaryWithCitations(
                            reportResult?.summary || ""
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
                    총 {reportResult?.total_articles || 0}개의 뉴스 기사가
                    분석되었습니다.
                    <span className="ml-2 text-primary-600 dark:text-primary-400">
                      (클릭하면 새 창에서 상세 내용을 볼 수 있습니다)
                    </span>
                  </p>

                  <div className="space-y-4 mt-4">
                    {/* 모든 기사 표시 (detailed_articles가 있으면 사용, 없으면 articles 사용) */}
                    {(
                      reportResult?.detailed_articles ||
                      reportResult?.articles ||
                      []
                    ).map((article) => (
                      <div
                        key={article.id || article.ref_id}
                        className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
                        onClick={() => handleArticleClick(article)}
                        id={
                          article.ref_id
                            ? `article-${article.ref_id}`
                            : undefined
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
                    {reportResult.total_articles || 0}개 기사 분석 완료 ·{" "}
                    {reportResult.generated_at
                      ? new Date(reportResult.generated_at).toLocaleString()
                      : "-"}
                  </p>
                </div>
              </motion.div>
            )}
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

/**
 * 관심종목 페이지 컴포넌트
 */
const WatchlistPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [categories, setCategories] = useState<Category[]>([]);
  const [watchlist, setWatchlist] = useState<Company[]>([]);
  const [selectedCompany, setSelectedCompany] = useState<Company | null>(null);
  const [timeline, setTimeline] = useState<TimelineItem[]>([]);
  const [selectedArticles, setSelectedArticles] = useState<
    Map<string, SelectedArticle>
  >(new Map());
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showSummarySidebar, setShowSummarySidebar] = useState(false);
  const [summaryResult, setSummaryResult] = useState<SummaryResult | null>(
    null
  );
  const [isGeneratingSummary, setIsGeneratingSummary] = useState(false);
  const [reportResult, setReportResult] = useState<ReportResult | null>(null);
  const [isGeneratingReport, setIsGeneratingReport] = useState(false);
  const [activeTab, setActiveTab] = useState<"seoul" | "all">("seoul"); // 탭 상태 추가
  const [showLegacyView, setShowLegacyView] = useState(false); // 기존 뷰 표시 여부

  useEffect(() => {
    fetchCategories();
    fetchWatchlistSuggestions();

    // 테스트용 하드코딩 데이터
    const testCategories = [
      {
        key: "domestic_stock",
        name: "국내주식",
        count: 30,
        icon: "🏢",
        description: "국내 상장 기업 주식",
      },
      {
        key: "foreign_stock",
        name: "해외주식",
        count: 30,
        icon: "🌎",
        description: "미국 등 해외 상장 기업 주식",
      },
      {
        key: "crypto",
        name: "가상자산",
        count: 30,
        icon: "🪙",
        description: "암호화폐 및 가상자산",
      },
    ];

    // API가 실패하면 5초 후 테스트 데이터 사용
    setTimeout(() => {
      if (categories.length === 0 && !error) {
        console.log("API 응답이 없어서 테스트 데이터 사용");
        setCategories(testCategories);
      }
    }, 5000);
  }, []);

  const fetchCategories = async () => {
    try {
      console.log("카테고리 fetch 시작");
      const response = await fetch("/api/entity/categories");
      console.log("API 응답 상태:", response.status);

      if (!response.ok) {
        const errorText = await response.text();
        console.error("API 응답 에러:", errorText);
        throw new Error(
          `카테고리를 불러오는데 실패했습니다: ${response.status}`
        );
      }

      const data = await response.json();
      console.log("받은 카테고리 데이터:", data);

      // 데이터 구조 검증
      if (!data || !Array.isArray(data.categories)) {
        console.error("잘못된 카테고리 데이터 구조:", data);
        throw new Error("카테고리 데이터 형식이 올바르지 않습니다");
      }

      // 카테고리별 아이콘 및 설명 추가
      const categoriesWithMeta = data.categories.map((cat: any) => {
        const categoryMeta: {
          [key: string]: { icon: string; description: string };
        } = {
          domestic_stock: { icon: "🏢", description: "국내 상장 기업 주식" },
          foreign_stock: {
            icon: "🌎",
            description: "미국 등 해외 상장 기업 주식",
          },
          commodity: { icon: "🏭", description: "원자재 및 상품" },
          forex_bond: { icon: "💱", description: "외환 및 채권 관련" },
          real_estate: { icon: "🏘️", description: "부동산 관련" },
          crypto: { icon: "🪙", description: "암호화폐 및 가상자산" },
        };

        return {
          ...cat,
          icon: categoryMeta[cat.key]?.icon || "📈",
          description: categoryMeta[cat.key]?.description || cat.name,
        };
      });

      console.log("메타데이터 추가된 카테고리:", categoriesWithMeta);
      setCategories(categoriesWithMeta);
    } catch (err) {
      console.error("카테고리 불러오기 오류:", err);
      setError(
        err instanceof Error ? err.message : "알 수 없는 오류가 발생했습니다"
      );
    }
  };

  useEffect(() => {
    if (selectedCompany) {
      // 탭에 따라 다른 필터 적용
      if (activeTab === "seoul") {
        fetchCompanyNews(selectedCompany, ["서울경제"]);
      } else {
        fetchCompanyNews(selectedCompany); // 전체 언론사
      }
    }
  }, [selectedCompany, activeTab]);

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

  const fetchCompanyNews = async (
    company: Company,
    providerFilter?: string[]
  ) => {
    setIsLoading(true);
    setError(null);
    setSelectedArticles(new Map());

    try {
      const requestBody: any = {
        company_name: company.name,
        limit: 50, // 더 많은 기사를 가져옴
      };

      // 언론사 필터 추가
      if (providerFilter) {
        requestBody.provider = providerFilter;
      }

      const response = await fetch("/api/news/company", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestBody),
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

  const handleGenerateSummary = async () => {
    setIsGeneratingSummary(true);
    setSummaryResult(null);

    // 사이드바가 닫혀있으면 열기
    if (!showSummarySidebar) {
      setShowSummarySidebar(true);
    }

    try {
      const response = await fetch("/api/news/ai-summary", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          news_ids: Array.from(selectedArticles.keys()),
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

    // 디버깅을 위한 로그 추가
    console.log(`레포트 생성 요청: ${selectedCompany.name}, 타입: ${type}`);
    const apiUrl = `/api/news/company/${selectedCompany.name}/report/${type}`;
    console.log(
      `호출 URL: ${apiUrl}, 전체 URL: ${window.location.origin}${apiUrl}`
    );

    try {
      // API 요청 시작 로그
      console.log("API 요청 시작...");

      const response = await fetch(apiUrl);

      // 응답 상태 확인
      console.log(`API 응답 상태: ${response.status} ${response.statusText}`);

      if (!response.ok) {
        // 오류 응답 상세 처리
        const errorText = await response.text();
        console.error(`API 오류 응답: ${errorText}`);
        throw new Error(`레포트 생성 실패 (${response.status}): ${errorText}`);
      }

      const data = await response.json();
      console.log("레포트 데이터 수신:", data);

      setReportResult(data);

      // URL 상태 업데이트 (뒤로가기를 위한 상태 유지)
      const params = new URLSearchParams(location.search);
      params.set("reportType", type);
      params.set("company", selectedCompany.name);

      // 브라우저 히스토리 업데이트 (URL 변경)
      navigate(`${location.pathname}?${params.toString()}`, { replace: false });
    } catch (error) {
      console.error("레포트 생성 오류:", error);
      setReportResult({
        title: "오류",
        content: `레포트 생성 중 오류가 발생했습니다: ${
          error instanceof Error ? error.message : "알 수 없는 오류"
        }`,
        sources: [],
      });
    } finally {
      setIsGeneratingReport(false);
    }
  };

  const viewArticleDetail = (article: NewsArticle) => {
    navigate(`/news/${article.id}`);
  };

  const allArticles = timeline.flatMap((item) => item.articles);
  const topArticles = allArticles.slice(0, 5);

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={containerVariants}
      className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-primary-50/30 dark:from-gray-900 dark:via-gray-900 dark:to-primary-900/10"
    >
      {/* 배경 데코레이션 */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-gradient-to-br from-primary-100/20 to-secondary-100/20 rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-1/4 w-80 h-80 bg-gradient-to-tl from-secondary-100/20 to-primary-100/20 rounded-full blur-3xl" />
      </div>

      <div className="relative z-10 space-y-10 p-6 max-w-7xl mx-auto">
        <motion.div variants={itemVariants}>
          <div className="flex justify-between items-center mb-8">
            <div>
              <h1 className="text-4xl font-bold bg-gradient-to-r from-gray-900 via-primary-800 to-secondary-800 dark:from-white dark:via-primary-300 dark:to-secondary-300 bg-clip-text text-transparent mb-2">
                관심 종목
              </h1>
              <p className="text-gray-600 dark:text-gray-400">
                투자 관심 종목들의 최신 뉴스와 AI 분석을 확인하세요
              </p>
            </div>
            <motion.button
              onClick={() => setShowLegacyView(!showLegacyView)}
              className="group flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white/80 dark:bg-gray-800/80 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 hover:border-primary-300 dark:hover:border-primary-600 transition-all backdrop-blur-sm shadow-sm hover:shadow-md"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <svg
                className="w-4 h-4 transition-transform group-hover:rotate-180"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                />
              </svg>
              {showLegacyView ? "카테고리 보기" : "기존 종목 보기"}
            </motion.button>
          </div>

          {!showLegacyView ? (
            /* 카테고리 카드 뷰 */
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
              {error ? (
                <div className="col-span-full text-center py-12">
                  <p className="text-red-500">{error}</p>
                  <button
                    onClick={fetchCategories}
                    className="mt-2 px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700"
                  >
                    다시 시도
                  </button>
                </div>
              ) : categories.length === 0 ? (
                <div className="col-span-full text-center py-12">
                  <p className="text-gray-500">카테고리를 불러오는 중...</p>
                </div>
              ) : (
                categories.map((category) => (
                  <CategoryCard
                    key={category.key}
                    category={category}
                    onClick={() => navigate(`/category/${category.key}`)}
                  />
                ))
              )}
            </div>
          ) : (
            /* 기존 관심 종목 리스트 */
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
          )}
        </motion.div>

        {selectedCompany && showLegacyView && (
          <>
            {/* 뉴스 캐러셀 */}
            <motion.div variants={itemVariants}>
              <NewsCarousel articles={topArticles} />
            </motion.div>

            {/* 타임라인 섹션 */}
            <motion.div
              variants={itemVariants}
              className={`transition-all duration-300 ${
                showSummarySidebar ? "pr-96" : ""
              }`}
            >
              <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4 mb-6">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-1">
                    뉴스 타임라인
                  </h2>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    시간순으로 정렬된 최신 뉴스를 확인하세요
                  </p>
                </div>

                <div className="flex items-center gap-4">
                  {/* AI 요약 토글 버튼 */}
                  <motion.button
                    onClick={() => setShowSummarySidebar((prev) => !prev)}
                    disabled={selectedArticles.size === 0}
                    className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all ${
                      selectedArticles.size > 0
                        ? "bg-primary-500 hover:bg-primary-600 text-white shadow-md hover:shadow-lg"
                        : "bg-gray-200 dark:bg-gray-700 text-gray-400 cursor-not-allowed"
                    }`}
                    whileHover={
                      selectedArticles.size > 0 ? { scale: 1.02 } : {}
                    }
                    whileTap={selectedArticles.size > 0 ? { scale: 0.98 } : {}}
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
                        d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                      />
                    </svg>
                    <span className="hidden sm:inline">
                      {selectedArticles.size > 0
                        ? `${selectedArticles.size}개 기사 요약`
                        : "기사를 선택하세요"}
                    </span>
                  </motion.button>

                  {/* 탭 선택 UI */}
                  <div className="relative bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-xl p-1.5 border border-gray-200/60 dark:border-gray-700/60 shadow-lg">
                    <motion.div
                      className="absolute inset-y-1.5 bg-gradient-to-r from-primary-500 to-secondary-500 rounded-lg shadow-md"
                      initial={false}
                      animate={{
                        x: activeTab === "seoul" ? 0 : "100%",
                        width: activeTab === "seoul" ? "48%" : "52%",
                      }}
                      transition={{
                        type: "spring",
                        bounce: 0.2,
                        duration: 0.6,
                      }}
                    />

                    <div className="relative flex">
                      <button
                        onClick={() => setActiveTab("seoul")}
                        className={`relative z-10 px-6 py-2.5 rounded-lg text-sm font-medium transition-all duration-300 ${
                          activeTab === "seoul"
                            ? "text-white shadow-lg"
                            : "text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200"
                        }`}
                      >
                        <span className="flex items-center gap-2">
                          <div
                            className={`w-2 h-2 rounded-full transition-all ${
                              activeTab === "seoul"
                                ? "bg-white"
                                : "bg-primary-400 opacity-60"
                            }`}
                          />
                          서울경제 타임라인
                        </span>
                      </button>

                      <button
                        onClick={() => setActiveTab("all")}
                        className={`relative z-10 px-6 py-2.5 rounded-lg text-sm font-medium transition-all duration-300 ${
                          activeTab === "all"
                            ? "text-white shadow-lg"
                            : "text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200"
                        }`}
                      >
                        <span className="flex items-center gap-2">
                          <div
                            className={`w-2 h-2 rounded-full transition-all ${
                              activeTab === "all"
                                ? "bg-white"
                                : "bg-secondary-400 opacity-60"
                            }`}
                          />
                          전체 언론사 타임라인
                        </span>
                      </button>
                    </div>
                  </div>
                </div>

                {error && <ErrorMessage message={error} />}

                {isLoading ? (
                  <div className="flex justify-center py-12">
                    <LoadingSpinner />
                  </div>
                ) : (
                  <div className="space-y-10 max-h-[700px] overflow-y-auto pr-2 scrollbar-thin scrollbar-track-gray-100 dark:scrollbar-track-gray-800 scrollbar-thumb-gray-300 dark:scrollbar-thumb-gray-600 hover:scrollbar-thumb-gray-400 dark:hover:scrollbar-thumb-gray-500">
                    {timeline.length === 0 ? (
                      <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="text-center py-16"
                      >
                        <div className="w-20 h-20 bg-gradient-to-br from-gray-100 to-gray-200 dark:from-gray-700 dark:to-gray-800 rounded-full flex items-center justify-center mx-auto mb-4">
                          <svg
                            className="w-10 h-10 text-gray-400"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={1.5}
                              d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z"
                            />
                          </svg>
                        </div>
                        <h3 className="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-2">
                          기사가 없습니다
                        </h3>
                        <p className="text-gray-500 dark:text-gray-400">
                          {activeTab === "seoul"
                            ? "서울경제에 관련 기사가 없습니다."
                            : "관련 기사가 없습니다."}
                        </p>
                      </motion.div>
                    ) : (
                      timeline.map((timelineItem, index) => (
                        <motion.div
                          key={timelineItem.date}
                          initial={{ opacity: 0, y: 30 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: index * 0.1 }}
                          className="relative"
                        >
                          {/* 타임라인 연결선 */}
                          {index < timeline.length - 1 && (
                            <div className="absolute left-16 top-12 w-0.5 h-full bg-gradient-to-b from-primary-300 to-transparent dark:from-primary-600" />
                          )}

                          {/* 날짜 헤더 */}
                          <div className="flex items-center mb-6">
                            <div className="relative flex-shrink-0">
                              <div className="w-32 h-12 bg-gradient-to-r from-primary-500 to-secondary-500 rounded-xl flex items-center justify-center shadow-lg">
                                <span className="text-white font-bold text-sm">
                                  {new Date(
                                    timelineItem.date
                                  ).toLocaleDateString("ko-KR", {
                                    month: "short",
                                    day: "numeric",
                                  })}
                                </span>
                              </div>

                              {/* 독 */}
                              <div className="absolute -right-1 top-1/2 transform -translate-y-1/2 w-3 h-3 bg-white dark:bg-gray-900 border-2 border-primary-500 rounded-full" />
                            </div>

                            <div className="flex-grow h-0.5 bg-gradient-to-r from-primary-200 via-gray-200 to-transparent dark:from-primary-700 dark:via-gray-700 ml-4" />

                            <div className="ml-4 bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm px-4 py-2 rounded-full border border-gray-200/60 dark:border-gray-700/60 shadow-sm">
                              <span className="text-sm font-semibold text-primary-600 dark:text-primary-400">
                                {timelineItem.count}건
                              </span>
                            </div>
                          </div>

                          {/* 기사 목록 */}
                          <div className="ml-36 space-y-5">
                            {timelineItem.articles.map(
                              (article, articleIndex) => (
                                <motion.div
                                  key={article.id}
                                  initial={{ opacity: 0, x: 20 }}
                                  animate={{ opacity: 1, x: 0 }}
                                  transition={{
                                    delay: index * 0.1 + articleIndex * 0.05,
                                  }}
                                >
                                  <NewsArticleCard
                                    article={{
                                      ...article,
                                      isSelected: selectedArticles.has(
                                        article.id
                                      ),
                                    }}
                                    onToggle={() =>
                                      toggleArticleSelection(article)
                                    }
                                    onViewDetail={() =>
                                      viewArticleDetail(article)
                                    }
                                    showProviderBadge={activeTab === "all"}
                                  />
                                </motion.div>
                              )
                            )}
                          </div>
                        </motion.div>
                      ))
                    )}
                  </div>
                )}
              </div>
            </motion.div>
          </>
        )}

        {/* AI 요약 사이드바 */}
        <AISummarySidebar
          isVisible={showSummarySidebar}
          selectedArticles={Array.from(selectedArticles.values())}
          onGenerateSummary={handleGenerateSummary}
          summaryResult={summaryResult}
          isGenerating={isGeneratingSummary}
          onClose={() => {
            setShowSummarySidebar(false);
            setSummaryResult(null);
          }}
        />
      </div>
    </motion.div>
  );
};

export default WatchlistPage;
