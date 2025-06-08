import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import LoadingSpinner from "./LoadingSpinner";
import { getRelatedQuestions, RelatedQuestion } from "../../services/api";

interface Question {
  question: string;
  query: string;
  type: string;
}

interface RelatedQuestionsProps {
  keyword: string;
  onQuestionClick: (question: Question) => void;
  maxQuestions?: number;
  className?: string;
}

const RelatedQuestions: React.FC<RelatedQuestionsProps> = ({
  keyword,
  onQuestionClick,
  maxQuestions = 7,
  className = "",
}) => {
  const [questions, setQuestions] = useState<Question[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!keyword) return;

    const fetchRelatedQuestions = async () => {
      setLoading(true);
      setError(null);

      try {
        const response = await getRelatedQuestions(
          keyword,
          undefined,
          undefined,
          maxQuestions
        );

        if (
          response.success &&
          response.questions &&
          response.questions.length > 0
        ) {
          const mappedQuestions = response.questions.map((q) => ({
            question: q.question,
            query: q.query,
            type: q.query.includes(" NOT ")
              ? "exclude"
              : q.query.includes(" OR ")
              ? "expand"
              : "refine",
          }));

          setQuestions(mappedQuestions);
        } else {
          setQuestions([]);
          if (!response.success) {
            setError("연관 질문을 생성할 수 없습니다");
          }
        }
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "알 수 없는 오류가 발생했습니다"
        );
        setQuestions([]);
      } finally {
        setLoading(false);
      }
    };

    fetchRelatedQuestions();
  }, [keyword, maxQuestions]);

  // 질문 유형에 따른 아이콘 결정
  const getQuestionIcon = (type: string) => {
    switch (type) {
      case "basic":
        return (
          <svg
            className="w-5 h-5 text-blue-500"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        );
      case "refine":
        return (
          <svg
            className="w-5 h-5 text-green-500"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
        );
      case "expand":
        return (
          <svg
            className="w-5 h-5 text-purple-500"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4"
            />
          </svg>
        );
      case "exclude":
        return (
          <svg
            className="w-5 h-5 text-red-500"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        );
      case "complex":
        return (
          <svg
            className="w-5 h-5 text-yellow-500"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
            />
          </svg>
        );
      default:
        return (
          <svg
            className="w-5 h-5 text-gray-500"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        );
    }
  };

  if (loading) {
    return (
      <div className={`my-6 ${className}`}>
        <div className="flex items-center mb-4">
          <h3 className="text-lg font-semibold">관련 질문</h3>
          <div className="ml-2 w-5 h-5">
            <LoadingSpinner size="small" />
          </div>
        </div>
        <div className="p-4 bg-gray-100 dark:bg-gray-800 rounded-lg animate-pulse">
          <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-2"></div>
          <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-1/2 mb-2"></div>
          <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-2/3 mb-2"></div>
          <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-3/5"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`my-6 ${className}`}>
        <h3 className="text-lg font-semibold mb-2">관련 질문</h3>
        <p className="text-sm text-red-500">{error}</p>
      </div>
    );
  }

  if (questions.length === 0) {
    return null;
  }

  return (
    <div className={`my-6 ${className}`}>
      <h3 className="text-lg font-semibold mb-4">이런 내용이 궁금하신가요?</h3>
      <div className="space-y-2">
        {questions.map((question, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: index * 0.1 }}
            whileHover={{ scale: 1.01 }}
            className="p-3 bg-white dark:bg-gray-800 rounded-lg shadow-sm hover:shadow-md border border-gray-200 dark:border-gray-700 transition-all cursor-pointer flex items-center"
            onClick={() => onQuestionClick(question)}
          >
            <div className="mr-3 flex-shrink-0">
              {getQuestionIcon(question.type)}
            </div>
            <span className="text-gray-800 dark:text-gray-200">
              {question.question}
            </span>
          </motion.div>
        ))}
      </div>
    </div>
  );
};

export default RelatedQuestions;
