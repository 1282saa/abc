import React, { useState } from "react";
import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { containerVariants, itemVariants } from "../animations/pageAnimations";
import useTimeline from "../hooks/useTimeline";
import TimelineForm from "../components/timeline/TimelineForm";
import TimelineList from "../components/timeline/TimelineList";
import TimelineEmpty from "../components/timeline/TimelineEmpty";
import TimelineLoading from "../components/timeline/TimelineLoading";
import ErrorMessage from "../components/common/ErrorMessage";

interface FeatureCardProps {
  title: string;
  description: string;
  icon: React.ReactNode;
  linkTo?: string;
  linkText: string;
  onClick?: () => void;
  isInline?: boolean;
}

const FeatureCard: React.FC<FeatureCardProps> = ({
  title,
  description,
  icon,
  linkTo,
  linkText,
  onClick,
  isInline = false,
}) => {
  const content = (
    <div className="flex flex-col h-full">
      <div className="mb-4 text-primary-600 dark:text-primary-400">
        {icon}
      </div>
      <h3 className="text-xl font-bold mb-3">{title}</h3>
      <p className="text-gray-600 dark:text-gray-400 mb-6 flex-grow">
        {description}
      </p>
      <div className="inline-flex items-center text-primary-600 dark:text-primary-400 font-medium mt-auto">
        {linkText}
        <svg
          className="w-5 h-5 ml-1"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M14 5l7 7m0 0l-7 7m7-7H3"
          ></path>
        </svg>
      </div>
    </div>
  );

  return (
    <motion.div
      className="card hover:shadow-lg cursor-pointer transition-all"
      whileHover={{ y: -5, transition: { duration: 0.2 } }}
      onClick={onClick}
    >
      {isInline ? content : <Link to={linkTo!}>{content}</Link>}
    </motion.div>
  );
};

/**
 * 홈페이지 컴포넌트
 */
const HomePage: React.FC = () => {
  const [showTimeline, setShowTimeline] = useState(false);
  const timeline = useTimeline();

  const handleTimelineClick = () => {
    setShowTimeline(!showTimeline);
  };

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={containerVariants}
      className="space-y-12"
    >
      {/* 히어로 섹션 */}
      <motion.div variants={itemVariants} className="text-center">
        <div className="glass-panel p-10 md:p-16">
          <h1 className="text-4xl md:text-5xl font-bold mb-6">
            <span className="text-primary-600 dark:text-primary-400">
              AI NOVA
            </span>
            로
            <br /> 뉴스를 더 스마트하게
          </h1>
          <p className="text-xl text-gray-600 dark:text-gray-400 max-w-3xl mx-auto">
            인공지능 기술로 뉴스를 분석하고 질문에 답하며 통찰력을 제공하는
            서비스입니다.
          </p>
        </div>
      </motion.div>

      {/* 기능 소개 섹션 */}
      <motion.div variants={itemVariants}>
        <h2 className="text-2xl font-bold mb-6 text-center">주요 기능</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <FeatureCard
            title="뉴스 Q&A"
            description="뉴스 데이터베이스에 질문하고 정확한 답변을 받아보세요. AI가 최신 뉴스 기사를 분석하여 답변합니다."
            icon={
              <svg
                className="w-10 h-10"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
                ></path>
              </svg>
            }
            linkTo="/qa"
            linkText="질문하러 가기"
          />
          <FeatureCard
            title="뉴스 요약"
            description="복잡한 뉴스 기사를 AI가 핵심만 간결하게 요약해 드립니다. 중요한 포인트를 놓치지 마세요."
            icon={
              <svg
                className="w-10 h-10"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                ></path>
              </svg>
            }
            linkTo="/summary"
            linkText="요약 시작하기"
          />
          <FeatureCard
            title="뉴스 타임라인"
            description="키워드 기반으로 뉴스 사건의 시간순 흐름을 확인하세요. 복잡한 이슈의 전개 과정을 한눈에 파악할 수 있습니다."
            icon={
              <svg
                className="w-10 h-10"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                ></path>
              </svg>
            }
            linkText={showTimeline ? "타임라인 숨기기" : "타임라인 보기"}
            onClick={handleTimelineClick}
            isInline={true}
          />
        </div>
      </motion.div>

      {/* 타임라인 섹션 */}
      {showTimeline && (
        <motion.div 
          variants={itemVariants}
          initial="hidden"
          animate="visible"
          exit="hidden"
        >
          <h2 className="text-2xl font-bold mb-6 text-center">뉴스 타임라인</h2>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* 검색 폼 영역 */}
            <div>
              <TimelineForm
                keywords={timeline.keywords}
                dateFrom={timeline.dateFrom}
                dateTo={timeline.dateTo}
                isLoading={timeline.isLoading}
                setKeywords={timeline.setKeywords}
                setDateFrom={timeline.setDateFrom}
                setDateTo={timeline.setDateTo}
                handleSubmit={timeline.handleSubmit}
                handleKeywordClick={timeline.handleKeywordClick}
              />
            </div>

            {/* 결과 표시 영역 */}
            <div className="lg:col-span-2">
              {/* 에러 메시지 */}
              <ErrorMessage message={timeline.error} />

              {/* 로딩 상태 */}
              {timeline.isLoading && <TimelineLoading />}

              {/* 타임라인 목록 */}
              {!timeline.isLoading && timeline.timeline.length > 0 && (
                <TimelineList items={timeline.timeline} />
              )}

              {/* 빈 상태 */}
              {!timeline.isLoading && timeline.timeline.length === 0 && !timeline.error && (
                <TimelineEmpty />
              )}
            </div>
          </div>
        </motion.div>
      )}

      {/* 빅카인즈 AI 임베딩 섹션 */}
      <motion.div variants={itemVariants} className="mt-12">
        <h2 className="text-2xl font-bold mb-6 text-center">빅카인즈 AI 바로 사용하기</h2>
        <div className="glass-panel p-4">
          <iframe
            src="https://www.bigkinds.or.kr/bigkindsAi/home.do"
            className="w-full h-[800px] rounded-lg border-0"
            title="빅카인즈 AI"
            loading="lazy"
            allowFullScreen
          />
        </div>
      </motion.div>
    </motion.div>
  );
};

export default HomePage;
