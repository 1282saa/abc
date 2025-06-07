import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import LoadingSpinner from "./LoadingSpinner";

interface AIAnalysisModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  eventTitle?: string;
  eventDetails?: string;
  stockName?: string;
  stockCode?: string;
  analysisType: "event" | "stock" | "term";
}

interface AnalysisResult {
  explanation?: string;
  analysis?: string;
  success: boolean;
}

const AIAnalysisModal: React.FC<AIAnalysisModalProps> = ({
  isOpen,
  onClose,
  title,
  eventTitle,
  eventDetails,
  stockName,
  stockCode,
  analysisType,
}) => {
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const fetchAnalysis = async () => {
    if (!isOpen || analysis) return; // 이미 분석 결과가 있으면 다시 호출하지 않음

    setIsLoading(true);
    setError("");

    try {
      let endpoint = "";
      let body = {};

      switch (analysisType) {
        case "event":
          endpoint = "http://localhost:8000/api/stock-calendar/ai-analysis/event";
          body = {
            event_title: eventTitle,
            event_details: eventDetails || "",
          };
          break;
        case "stock":
          endpoint = "http://localhost:8000/api/stock-calendar/ai-analysis/stock";
          body = {
            stock_name: stockName,
            stock_code: stockCode,
            current_price: "",
          };
          break;
        case "term":
          endpoint = "http://localhost:8000/api/stock-calendar/ai-analysis/term";
          body = {
            term: title,
            context: "",
          };
          break;
      }

      const response = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
      });

      const data = await response.json();
      setAnalysis(data);
    } catch (err) {
      console.error("AI 분석 오류:", err);
      setError("AI 분석을 가져오는 중 오류가 발생했습니다.");
    } finally {
      setIsLoading(false);
    }
  };

  // 모달이 열릴 때 분석 요청
  React.useEffect(() => {
    if (isOpen) {
      fetchAnalysis();
    } else {
      // 모달이 닫힐 때 상태 초기화
      setAnalysis(null);
      setError("");
    }
  }, [isOpen]);

  const formatAnalysisText = (text: string) => {
    // 이모지와 텍스트를 적절히 포맷팅
    return text.split('\n').map((line, index) => {
      if (line.trim() === '') return <br key={index} />;
      
      // 이모지로 시작하는 섹션 헤더 감지
      if (line.match(/^[📌💡⚠️🎯📈💼⏰]/)) {
        return (
          <div key={index} className="font-bold text-lg mt-4 mb-2 text-primary-600 dark:text-primary-400">
            {line}
          </div>
        );
      }
      
      // 일반 텍스트
      return (
        <p key={index} className="mb-2 leading-relaxed">
          {line}
        </p>
      );
    });
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
          onClick={onClose}
        >
          <motion.div
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.95, opacity: 0 }}
            className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full max-h-[80vh] overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            {/* 헤더 */}
            <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-600">
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                🤖 AI 분석: {title}
              </h2>
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* 내용 */}
            <div className="p-6 overflow-y-auto max-h-[60vh]">
              {isLoading && (
                <div className="flex items-center justify-center py-8">
                  <LoadingSpinner />
                  <span className="ml-3 text-gray-600 dark:text-gray-400">
                    AI가 분석 중입니다...
                  </span>
                </div>
              )}

              {error && (
                <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
                  <p className="text-red-700 dark:text-red-400">{error}</p>
                  <button
                    onClick={fetchAnalysis}
                    className="mt-2 text-sm text-red-600 dark:text-red-400 hover:underline"
                  >
                    다시 시도
                  </button>
                </div>
              )}

              {analysis && !isLoading && (
                <div className="prose dark:prose-invert max-w-none">
                  {analysis.success ? (
                    <div className="text-gray-700 dark:text-gray-300">
                      {formatAnalysisText(analysis.explanation || analysis.analysis || "")}
                    </div>
                  ) : (
                    <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
                      <p className="text-yellow-700 dark:text-yellow-400">
                        현재 AI 분석을 사용할 수 없습니다. 나중에 다시 시도해주세요.
                      </p>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* 푸터 */}
            <div className="px-6 py-4 bg-gray-50 dark:bg-gray-700 flex justify-end">
              <button
                onClick={onClose}
                className="px-4 py-2 bg-gray-200 dark:bg-gray-600 text-gray-800 dark:text-gray-200 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-500 transition-colors"
              >
                닫기
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default AIAnalysisModal;