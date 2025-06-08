import React from "react";
import { RelatedQuestion } from "../../services/api";

interface RelatedQuestionsCardProps {
  questions: RelatedQuestion[];
  onQuestionClick: (query: string, question: string) => void;
  isLoading?: boolean;
}

const RelatedQuestionsCard: React.FC<RelatedQuestionsCardProps> = ({
  questions,
  onQuestionClick,
  isLoading = false,
}) => {
  if (isLoading) {
    return (
      <div className="border rounded-lg p-4 mb-4 bg-white dark:bg-gray-800">
        <h3 className="text-lg font-medium mb-3">관련 질문</h3>
        <div className="space-y-2 animate-pulse">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="h-10 bg-gray-200 dark:bg-gray-700 rounded"
            ></div>
          ))}
        </div>
      </div>
    );
  }

  if (!questions || questions.length === 0) {
    return null;
  }

  return (
    <div className="border rounded-lg p-4 mb-4 bg-white dark:bg-gray-800">
      <h3 className="text-lg font-medium mb-3">관련 질문</h3>
      <div className="space-y-2">
        {questions.map((question) => (
          <button
            key={question.id}
            onClick={() => onQuestionClick(question.query, question.question)}
            className="w-full text-left p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors flex items-center group"
          >
            <span className="text-primary-600 dark:text-primary-400 mr-2">
              Q.
            </span>
            <span className="flex-1">{question.question}</span>
            <span className="text-gray-400 text-sm ml-2 opacity-0 group-hover:opacity-100 transition-opacity">
              {question.count}건
            </span>
            <svg
              className="w-4 h-4 text-gray-400 ml-2 opacity-0 group-hover:opacity-100 transition-opacity"
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
        ))}
      </div>
    </div>
  );
};

export default RelatedQuestionsCard;
