import React from "react";
import { motion } from "framer-motion";
import QueryInput from "../components/qa/QueryInput";
import AnswerDisplay from "../components/qa/AnswerDisplay";
import ErrorMessage from "../components/common/ErrorMessage";
import { containerVariants, itemVariants } from "../animations/pageAnimations";
import useQA from "../hooks/useQA";

/**
 * 질의응답 페이지 컴포넌트
 */
const QAPage: React.FC = () => {
  // 질의응답 커스텀 훅 사용
  const {
    query,
    setQuery,
    answer,
    sources,
    isLoading,
    error,
    handleSubmit,
    useSources,
    setUseSources,
  } = useQA();

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
          <h1 className="text-3xl md:text-4xl font-bold mb-4">뉴스 Q&A</h1>
          <p className="text-lg text-gray-600 dark:text-gray-400 max-w-3xl mx-auto">
            뉴스 데이터베이스에 질문을 입력하고 AI가 생성한 답변을 받아보세요.
          </p>
        </div>
      </motion.div>

      {/* 메인 콘텐츠 영역 */}
      <motion.div
        className="grid grid-cols-1 md:grid-cols-3 gap-6"
        variants={itemVariants}
      >
        {/* 질문 입력 영역 */}
        <div>
          <QueryInput
            query={query}
            setQuery={setQuery}
            handleSubmit={handleSubmit}
            isLoading={isLoading}
            useSources={useSources}
            setUseSources={setUseSources}
          />
        </div>

        {/* 답변 표시 영역 */}
        <div className="md:col-span-2">
          {/* 에러 메시지 */}
          <ErrorMessage message={error} />

          {/* 답변 컴포넌트 */}
          <AnswerDisplay
            answer={answer}
            sources={sources}
            isLoading={isLoading}
          />
        </div>
      </motion.div>
    </motion.div>
  );
};

export default QAPage;
