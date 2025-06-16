import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  LinkIcon,
  CalendarIcon,
  BuildingOfficeIcon,
  EyeIcon,
  ArrowTopRightOnSquareIcon,
} from "@heroicons/react/24/outline";
import { CitationSource } from "../../services/api";

interface CitationLinkProps {
  citationNumber: number;
  citation: CitationSource;
  className?: string;
  variant?: "inline" | "button" | "badge";
  showTooltip?: boolean;
}

const CitationLink: React.FC<CitationLinkProps> = ({
  citationNumber,
  citation,
  className = "",
  variant = "inline",
  showTooltip = true,
}) => {
  const [showPreview, setShowPreview] = useState(false);

  const handleClick = () => {
    if (citation.url && citation.url !== "#") {
      window.open(citation.url, "_blank", "noopener,noreferrer");
    }
  };

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleDateString("ko-KR", {
        month: "short",
        day: "numeric",
      });
    } catch {
      return dateString;
    }
  };

  const renderInlineVariant = () => (
    <motion.button
      onClick={handleClick}
      onMouseEnter={() => showTooltip && setShowPreview(true)}
      onMouseLeave={() => setShowPreview(false)}
      className={`
        relative inline-flex items-center text-blue-600 hover:text-blue-800 
        dark:text-blue-400 dark:hover:text-blue-300 
        font-medium transition-colors duration-150
        hover:underline cursor-pointer
        ${className}
      `}
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
    >
      [{citationNumber}]
      <LinkIcon className="w-3 h-3 ml-0.5" />
      
      {/* 툴팁 미리보기 */}
      <AnimatePresence>
        {showPreview && showTooltip && (
          <motion.div
            initial={{ opacity: 0, y: 10, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 10, scale: 0.9 }}
            className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 z-50"
          >
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl border border-gray-200 dark:border-gray-700 p-4 max-w-xs">
              <div className="flex items-start gap-3">
                <LinkIcon className="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5" />
                <div>
                  <h4 className="font-medium text-gray-900 dark:text-white text-sm line-clamp-2">
                    {citation.title}
                  </h4>
                  <div className="flex items-center gap-2 mt-2 text-xs text-gray-500 dark:text-gray-400">
                    <BuildingOfficeIcon className="w-3 h-3" />
                    <span>{citation.provider}</span>
                    <CalendarIcon className="w-3 h-3 ml-1" />
                    <span>{formatDate(citation.published_at)}</span>
                  </div>
                  {citation.excerpt && (
                    <p className="text-xs text-gray-600 dark:text-gray-300 mt-2 line-clamp-2">
                      {citation.excerpt}
                    </p>
                  )}
                </div>
              </div>
              {/* 화살표 */}
              <div className="absolute top-full left-1/2 transform -translate-x-1/2">
                <div className="w-2 h-2 bg-white dark:bg-gray-800 border-r border-b border-gray-200 dark:border-gray-700 rotate-45 transform origin-center"></div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.button>
  );

  const renderButtonVariant = () => (
    <motion.button
      onClick={handleClick}
      className={`
        flex items-center gap-2 px-3 py-2 
        bg-blue-50 hover:bg-blue-100 dark:bg-blue-900/20 dark:hover:bg-blue-900/30
        text-blue-700 dark:text-blue-300
        rounded-lg border border-blue-200 dark:border-blue-800
        transition-colors duration-150
        ${className}
      `}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
    >
      <span className="font-medium">[{citationNumber}]</span>
      <ArrowTopRightOnSquareIcon className="w-4 h-4" />
      <span className="text-sm truncate max-w-40">{citation.title}</span>
    </motion.button>
  );

  const renderBadgeVariant = () => (
    <motion.button
      onClick={handleClick}
      className={`
        inline-flex items-center gap-1 px-2 py-1
        bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600
        text-gray-700 dark:text-gray-300
        rounded-full text-xs font-medium
        transition-colors duration-150
        ${className}
      `}
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
    >
      {citationNumber}
      <EyeIcon className="w-3 h-3" />
    </motion.button>
  );

  switch (variant) {
    case "button":
      return renderButtonVariant();
    case "badge":
      return renderBadgeVariant();
    default:
      return renderInlineVariant();
  }
};

export default CitationLink;