import React from "react";
import { motion } from "framer-motion";
import { containerVariants, itemVariants } from "../animations/pageAnimations";
import useTimeline from "../hooks/useTimeline";

// 컴포넌트 임포트
import TimelineForm from "../components/timeline/TimelineForm";
import TimelineList from "../components/timeline/TimelineList";
import TimelineEmpty from "../components/timeline/TimelineEmpty";
import TimelineLoading from "../components/timeline/TimelineLoading";
import ErrorMessage from "../components/common/ErrorMessage";

/**
 * 뉴스 타임라인 페이지
 */
const TimelinePage: React.FC = () => {
  // 타임라인 커스텀 훅 사용
  const {
    keywords,
    setKeywords,
    dateFrom,
    setDateFrom,
    dateTo,
    setDateTo,
    timeline,
    isLoading,
    error,
    handleSubmit,
    handleKeywordClick,
  } = useTimeline();

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
          <h1 className="text-3xl md:text-4xl font-bold mb-4">뉴스 타임라인</h1>
          <p className="text-lg text-gray-600 dark:text-gray-400 max-w-3xl mx-auto">
            키워드와 관련된 뉴스들을 시간순으로 정렬하여 사건의 흐름을 파악할 수
            있습니다.
          </p>
        </div>
      </motion.div>

      {/* 메인 콘텐츠 영역 */}
      <motion.div
        className="grid grid-cols-1 md:grid-cols-3 gap-6"
        variants={itemVariants}
      >
        {/* 검색 폼 영역 */}
        <div>
          <TimelineForm
            keywords={keywords}
            dateFrom={dateFrom}
            dateTo={dateTo}
            isLoading={isLoading}
            setKeywords={setKeywords}
            setDateFrom={setDateFrom}
            setDateTo={setDateTo}
            handleSubmit={handleSubmit}
            handleKeywordClick={handleKeywordClick}
          />
        </div>

        {/* 결과 표시 영역 */}
        <div className="md:col-span-2">
          {/* 에러 메시지 */}
          <ErrorMessage message={error} />

          {/* 로딩 상태 */}
          {isLoading && <TimelineLoading />}

          {/* 타임라인 목록 */}
          {!isLoading && timeline.length > 0 && (
            <TimelineList items={timeline} />
          )}

          {/* 빈 상태 */}
          {!isLoading && timeline.length === 0 && !error && <TimelineEmpty />}
        </div>
      </motion.div>
    </motion.div>
  );
};

export default TimelinePage;
