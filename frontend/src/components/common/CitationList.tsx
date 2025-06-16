import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  DocumentTextIcon,
  CalendarIcon,
  BuildingOfficeIcon,
  LinkIcon,
  ChevronDownIcon,
  ChevronUpIcon,
  MagnifyingGlassIcon,
} from "@heroicons/react/24/outline";
import { CitationSource } from "../../services/api";
import CitationLink from "./CitationLink";

interface CitationListProps {
  citations: CitationSource[];
  title?: string;
  maxVisible?: number;
  className?: string;
  variant?: "compact" | "detailed" | "grid";
  showSearch?: boolean;
}

const CitationList: React.FC<CitationListProps> = ({
  citations,
  title = "참고 기사",
  maxVisible = 5,
  className = "",
  variant = "detailed",
  showSearch = false,
}) => {
  const [showAll, setShowAll] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");

  const filteredCitations = citations.filter(citation =>
    searchTerm === "" ||
    citation.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    citation.provider.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const visibleCitations = showAll 
    ? filteredCitations 
    : filteredCitations.slice(0, maxVisible);

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleDateString("ko-KR", {
        year: "numeric",
        month: "short",
        day: "numeric",
      });
    } catch {
      return dateString;
    }
  };

  const handleCitationClick = (citation: CitationSource) => {
    if (citation.url && citation.url !== "#") {
      window.open(citation.url, "_blank", "noopener,noreferrer");
    }
  };

  const renderCompactVariant = () => (
    <div className="space-y-2">
      {visibleCitations.map((citation, index) => (
        <motion.div
          key={citation.id}
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: index * 0.05 }}
          className="flex items-center gap-3 p-2 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
        >
          <CitationLink
            citationNumber={citations.indexOf(citation) + 1}
            citation={citation}
            variant="badge"
          />
          <div className="flex-1 min-w-0">
            <button
              onClick={() => handleCitationClick(citation)}
              className="text-left w-full"
            >
              <p className="font-medium text-gray-900 dark:text-white text-sm line-clamp-1 hover:text-blue-600 dark:hover:text-blue-400">
                {citation.title}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {citation.provider}
              </p>
            </button>
          </div>
        </motion.div>
      ))}
    </div>
  );

  const renderDetailedVariant = () => (
    <div className="space-y-4">
      {visibleCitations.map((citation, index) => (
        <motion.div
          key={citation.id}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.1 }}
          className="group"
        >
          <button
            onClick={() => handleCitationClick(citation)}
            className="w-full text-left p-4 rounded-xl border border-gray-200 dark:border-gray-700 hover:border-blue-300 dark:hover:border-blue-600 hover:shadow-md transition-all duration-200"
          >
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0">
                <CitationLink
                  citationNumber={citations.indexOf(citation) + 1}
                  citation={citation}
                  variant="badge"
                  showTooltip={false}
                />
              </div>
              
              <div className="flex-1 min-w-0">
                <h4 className="font-medium text-gray-900 dark:text-white line-clamp-2 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                  {citation.title}
                </h4>
                
                <div className="flex items-center gap-4 mt-2 text-sm text-gray-500 dark:text-gray-400">
                  <div className="flex items-center gap-1">
                    <BuildingOfficeIcon className="w-4 h-4" />
                    <span>{citation.provider}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <CalendarIcon className="w-4 h-4" />
                    <span>{formatDate(citation.published_at)}</span>
                  </div>
                </div>

                {citation.excerpt && (
                  <p className="text-sm text-gray-600 dark:text-gray-300 mt-2 line-clamp-2">
                    {citation.excerpt}
                  </p>
                )}
              </div>

              <div className="flex-shrink-0">
                <LinkIcon className="w-5 h-5 text-gray-400 group-hover:text-blue-500 transition-colors" />
              </div>
            </div>
          </button>
        </motion.div>
      ))}
    </div>
  );

  const renderGridVariant = () => (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {visibleCitations.map((citation, index) => (
        <motion.div
          key={citation.id}
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: index * 0.05 }}
        >
          <button
            onClick={() => handleCitationClick(citation)}
            className="w-full text-left p-4 rounded-lg bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 hover:shadow-lg transition-all duration-200"
          >
            <div className="flex items-start gap-3">
              <CitationLink
                citationNumber={citations.indexOf(citation) + 1}
                citation={citation}
                variant="badge"
                showTooltip={false}
              />
              
              <div className="flex-1 min-w-0">
                <h4 className="font-medium text-gray-900 dark:text-white text-sm line-clamp-2 hover:text-blue-600 dark:hover:text-blue-400">
                  {citation.title}
                </h4>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  {citation.provider} • {formatDate(citation.published_at)}
                </p>
              </div>
            </div>
          </button>
        </motion.div>
      ))}
    </div>
  );

  const renderCitationsContent = () => {
    switch (variant) {
      case "compact":
        return renderCompactVariant();
      case "grid":
        return renderGridVariant();
      default:
        return renderDetailedVariant();
    }
  };

  if (!citations || citations.length === 0) {
    return null;
  }

  return (
    <div className={`bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 ${className}`}>
      {/* 헤더 */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <DocumentTextIcon className="w-6 h-6 text-blue-500" />
          <h3 className="font-bold text-gray-900 dark:text-white">
            {title} ({citations.length}개)
          </h3>
        </div>
        
        {citations.length > maxVisible && (
          <button
            onClick={() => setShowAll(!showAll)}
            className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 transition-colors"
          >
            {showAll ? (
              <>
                접기 <ChevronUpIcon className="w-4 h-4" />
              </>
            ) : (
              <>
                더보기 <ChevronDownIcon className="w-4 h-4" />
              </>
            )}
          </button>
        )}
      </div>

      {/* 검색 */}
      {showSearch && citations.length > 5 && (
        <div className="mb-4">
          <div className="relative">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="기사 검색..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        </div>
      )}

      {/* 인용 목록 */}
      <div className="max-h-96 overflow-y-auto">
        {filteredCitations.length === 0 ? (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            <MagnifyingGlassIcon className="w-12 h-12 mx-auto mb-2 opacity-50" />
            <p>검색 결과가 없습니다.</p>
          </div>
        ) : (
          renderCitationsContent()
        )}
      </div>

      {/* 더보기 버튼 (하단) */}
      {!showAll && filteredCitations.length > maxVisible && (
        <div className="mt-4 text-center">
          <button
            onClick={() => setShowAll(true)}
            className="text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300 transition-colors"
          >
            {filteredCitations.length - maxVisible}개 더보기...
          </button>
        </div>
      )}
    </div>
  );
};

export default CitationList;