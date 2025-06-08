import React, { useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import LoadingSpinner from "../common/LoadingSpinner";

interface NewsArticle {
  id: string;
  title: string;
  summary: string;
  content?: string;
  provider: string;
  url?: string;
  category?: string;
  byline?: string;
  images?: string[];
  published_at?: string;
}

interface NewsDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  article: NewsArticle | null;
}

const NewsDetailModal: React.FC<NewsDetailModalProps> = ({
  isOpen,
  onClose,
  article,
}) => {
  // 기사가 없거나 모달이 닫혀있으면 렌더링하지 않음
  if (!isOpen || !article) return null;

  // 전체 내용 가져오기
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

  // 모달이 열리면 내용 가져오기
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

export default NewsDetailModal;
