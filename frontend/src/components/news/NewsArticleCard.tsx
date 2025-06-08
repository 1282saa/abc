import React from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { NewsArticle } from "../../services/api";

interface NewsArticleCardProps {
  article: NewsArticle;
  onClick?: () => void;
  className?: string;
  showImage?: boolean;
  useNavigationInsteadOfModal?: boolean;
}

const NewsArticleCard: React.FC<NewsArticleCardProps> = ({
  article,
  onClick,
  className = "",
  showImage = true,
  useNavigationInsteadOfModal = true,
}) => {
  const navigate = useNavigate();
  const hasImage = showImage && article.images && article.images.length > 0;

  const handleClick = () => {
    if (useNavigationInsteadOfModal) {
      navigate(`/news/${article.id}`);
    } else if (onClick) {
      onClick();
    }
  };

  return (
    <motion.div
      whileHover={{ scale: 1.01 }}
      className={`bg-white dark:bg-gray-800 rounded-lg shadow-sm hover:shadow-md transition-all border border-gray-200 dark:border-gray-700 overflow-hidden ${className} cursor-pointer`}
      onClick={handleClick}
    >
      <div className={`p-4 ${hasImage ? "flex items-start gap-4" : ""}`}>
        {hasImage && article.images && (
          <div className="flex-shrink-0 w-24 h-24 rounded-md overflow-hidden">
            <img
              src={article.images[0]}
              alt={article.title}
              className="w-full h-full object-cover"
              onError={(e) => {
                const target = e.target as HTMLImageElement;
                target.src = "/placeholder-news.jpg";
              }}
            />
          </div>
        )}

        <div className={`${hasImage ? "flex-1" : ""}`}>
          <h3 className="font-semibold text-lg mb-1 line-clamp-2 text-gray-900 dark:text-gray-100">
            {article.title}
          </h3>

          <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2 mb-2">
            {article.summary}
          </p>

          <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-500">
            <div className="flex items-center gap-2">
              <span className="font-medium">{article.provider}</span>
              {article.byline && <span>| {article.byline}</span>}
              {article.category && (
                <span className="px-2 py-0.5 bg-gray-100 dark:bg-gray-700 rounded-full">
                  {article.category}
                </span>
              )}
            </div>
            <span>{article.published_at || "날짜 정보 없음"}</span>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

export default NewsArticleCard;
