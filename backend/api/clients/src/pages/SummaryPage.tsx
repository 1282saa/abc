import React from "react";
import { motion } from "framer-motion";
import UrlInput from "../components/summary/UrlInput";
import SummaryResult from "../components/summary/SummaryResult";
import ErrorMessage from "../components/common/ErrorMessage";
import { containerVariants, itemVariants } from "../animations/pageAnimations";
import useSummary from "../hooks/useSummary";

/**
 * 뉴스 요약 페이지 컴포넌트
 */
const SummaryPage: React.FC = () => {
  // 요약 커스텀 훅 사용
  const {
    url,
    setUrl,
    title,
    originalText,
    summary,
    keywords,
    isLoading,
    error,
    handleSubmit,
  } = useSummary();

  return (
    <motion.div
      className="space-y-8 max-w-5xl mx-auto"
      initial="hidden"
      animate="visible"
      variants={containerVariants}
    >
      {/* 페이지 헤더 */}
      <motion.div variants={itemVariants}>
        <div className="glass-panel p-8 md:p-10 text-center">
          <h1 className="text-3xl md:text-4xl font-bold mb-4">뉴스 요약</h1>
          <p className="text-lg text-gray-600 dark:text-gray-400 max-w-3xl mx-auto">
            긴 뉴스 기사를 AI가 핵심만 간결하게 요약해 드립니다.
          </p>
        </div>
      </motion.div>

      {/* 메인 콘텐츠 영역 */}
      <motion.div
        className="grid grid-cols-1 md:grid-cols-3 gap-6"
        variants={itemVariants}
      >
        {/* URL 입력 영역 */}
        <div>
          <UrlInput
            url={url}
            setUrl={setUrl}
            handleSubmit={handleSubmit}
            isLoading={isLoading}
          />
        </div>

        {/* 요약 결과 영역 */}
        <div className="md:col-span-2">
          {/* 에러 메시지 */}
          <ErrorMessage message={error} />

          {/* 요약 결과 */}
          <SummaryResult
            title={title}
            originalText={originalText}
            summary={summary}
            keywords={keywords}
            isLoading={isLoading}
          />
        </div>
      </motion.div>
    </motion.div>
  );
};

export default SummaryPage;
