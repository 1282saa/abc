import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useNavigate } from "react-router-dom";
import {
  DocumentChartBarIcon,
  CalendarDaysIcon,
  ClockIcon,
  ChevronDownIcon,
  SparklesIcon,
} from "@heroicons/react/24/outline";
import {
  PeriodReportType,
  AutoReportRequest,
  api,
} from "../../services/api";

interface CompanyPeriodReportButtonProps {
  companyName: string;
  companyCode?: string;
  className?: string;
}

interface PeriodOption {
  type: PeriodReportType;
  name: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
  estimatedTime: string;
}

const periodOptions: PeriodOption[] = [
  {
    type: "daily",
    name: "일간 레포트",
    description: "어제 하루 동안의 기업 뉴스 분석",
    icon: ClockIcon,
    color: "from-blue-500 to-blue-600",
    estimatedTime: "약 3분",
  },
  {
    type: "weekly",
    name: "주간 레포트", 
    description: "지난 일주일간의 기업 동향 종합 분석",
    icon: CalendarDaysIcon,
    color: "from-green-500 to-green-600",
    estimatedTime: "약 5분",
  },
  {
    type: "monthly",
    name: "월간 레포트",
    description: "지난 한 달간의 기업 활동 상세 분석",
    icon: DocumentChartBarIcon,
    color: "from-purple-500 to-purple-600",
    estimatedTime: "약 8분",
  },
  {
    type: "quarterly", 
    name: "분기별 레포트",
    description: "지난 분기 동안의 전략과 성과 심층 분석",
    icon: DocumentChartBarIcon,
    color: "from-orange-500 to-orange-600",
    estimatedTime: "약 12분",
  },
  {
    type: "yearly",
    name: "연간 레포트",
    description: "지난 1년간 기업의 모든 활동 종합 분석",
    icon: SparklesIcon,
    color: "from-red-500 to-red-600",
    estimatedTime: "약 20분",
  },
];

const CompanyPeriodReportButton: React.FC<CompanyPeriodReportButtonProps> = ({
  companyName,
  companyCode,
  className = "",
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const navigate = useNavigate();

  const handleReportGeneration = async (periodType: PeriodReportType) => {
    setIsGenerating(true);
    setIsOpen(false);

    try {
      // 기존 창에서 레포트 생성 페이지로 네비게이션
      const params = new URLSearchParams({
        company_name: companyName,
        company_code: companyCode || '',
        report_type: periodType,
        max_articles: "200", // 더 많은 기사 분석
        include_sentiment: "true",
        include_keywords: "true",
        language: "ko",
        max_tokens: "4000", // 높은 max token으로 상세한 출력
      });
      
      navigate(`/reports/period-generate?${params.toString()}`);
      
    } catch (error) {
      console.error("레포트 생성 실패:", error);
      alert("레포트 생성 중 오류가 발생했습니다.");
      setIsGenerating(false);
    }
  };

  return (
    <div className={`relative ${className}`}>
      {/* 메인 버튼 */}
      <motion.button
        onClick={() => setIsOpen(!isOpen)}
        disabled={isGenerating}
        className={`
          inline-flex items-center gap-2 px-4 py-2 
          bg-gradient-to-r from-purple-500 to-pink-600 
          hover:from-purple-600 hover:to-pink-700
          text-white font-medium rounded-lg
          shadow-lg hover:shadow-xl
          transition-all duration-200
          disabled:opacity-50 disabled:cursor-not-allowed
          ${isOpen ? "ring-2 ring-purple-300" : ""}
        `}
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
      >
        <DocumentChartBarIcon className="w-4 h-4" />
        {isGenerating ? "생성 중..." : "기간별 레포트"}
        <ChevronDownIcon
          className={`w-4 h-4 transition-transform duration-200 ${
            isOpen ? "rotate-180" : ""
          }`}
        />
      </motion.button>

      {/* 드롭다운 메뉴 */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.95 }}
            transition={{ duration: 0.2 }}
            className="absolute top-full left-0 mt-2 w-80 bg-white dark:bg-gray-800 rounded-xl shadow-2xl border border-gray-200 dark:border-gray-700 z-50 overflow-hidden"
          >
            <div className="p-3 border-b border-gray-200 dark:border-gray-700">
              <h3 className="font-semibold text-gray-900 dark:text-white">
                {companyName} 기간별 분석 레포트
              </h3>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                분석할 기간을 선택해주세요
              </p>
            </div>

            <div className="max-h-64 overflow-y-auto">
              {periodOptions.map((option) => {
                const IconComponent = option.icon;
                return (
                  <motion.button
                    key={option.type}
                    onClick={() => handleReportGeneration(option.type)}
                    className="w-full px-4 py-3 text-left hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors duration-150 border-b border-gray-100 dark:border-gray-700 last:border-b-0"
                    whileHover={{ x: 4 }}
                  >
                    <div className="flex items-start gap-3">
                      <div
                        className={`flex-shrink-0 w-10 h-10 rounded-lg bg-gradient-to-br ${option.color} flex items-center justify-center`}
                      >
                        <IconComponent className="w-5 h-5 text-white" />
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <h4 className="font-medium text-gray-900 dark:text-white">
                            {option.name}
                          </h4>
                          <span className="text-xs text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-600 px-2 py-1 rounded-full">
                            {option.estimatedTime}
                          </span>
                        </div>
                        <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">
                          {option.description}
                        </p>
                      </div>
                    </div>
                  </motion.button>
                );
              })}
            </div>

            <div className="p-3 bg-gray-50 dark:bg-gray-700 text-xs text-gray-500 dark:text-gray-400">
              💡 AI가 투자자 관점의 상세한 인사이트를 제공합니다
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* 배경 클릭 시 닫기 */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setIsOpen(false)}
        />
      )}
    </div>
  );
};

export default CompanyPeriodReportButton;