import React, { useState, useEffect } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  DocumentChartBarIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon,
  LinkIcon,
  PrinterIcon,
  ShareIcon,
} from "@heroicons/react/24/outline";
import {
  ReportRequest,
  ReportStreamData,
  CompanyReport,
  generateCompanyReportStream,
  CitationSource,
} from "../services/api";
import LoadingSpinner from "../components/common/LoadingSpinner";

const ReportGenerationPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  
  // 상태 관리
  const [isGenerating, setIsGenerating] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState("");
  const [report, setReport] = useState<CompanyReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [generationStartTime, setGenerationStartTime] = useState<Date | null>(null);

  // URL 파라미터에서 요청 정보 추출
  const request: ReportRequest = {
    company_name: searchParams.get("company_name") || "",
    company_code: searchParams.get("company_code") || undefined,
    period_type: (searchParams.get("period_type") as any) || "monthly",
    date_from: searchParams.get("date_from") || "",
    date_to: searchParams.get("date_to") || "",
    language: "ko",
    include_charts: true,
    max_articles: 50,
  };

  // 컴포넌트 마운트 시 레포트 생성 시작
  useEffect(() => {
    if (request.company_name && request.date_from && request.date_to) {
      handleGenerateReport();
    } else {
      setError("잘못된 요청입니다. 필수 파라미터가 누락되었습니다.");
    }
  }, []);

  const handleGenerateReport = async () => {
    setIsGenerating(true);
    setGenerationStartTime(new Date());
    setError(null);
    setProgress(0);
    setCurrentStep("레포트 생성을 시작합니다...");

    try {
      await generateCompanyReportStream(
        request,
        // onProgress
        (data: ReportStreamData) => {
          if (data.step) setCurrentStep(data.step);
          if (data.progress !== undefined) setProgress(data.progress);
        },
        // onComplete
        (result: CompanyReport) => {
          setReport(result);
          setIsGenerating(false);
          setProgress(100);
          setCurrentStep("레포트 생성이 완료되었습니다!");
        },
        // onError
        (errorMessage: string) => {
          setError(errorMessage);
          setIsGenerating(false);
        }
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "알 수 없는 오류가 발생했습니다.");
      setIsGenerating(false);
    }
  };

  const formatPeriodName = (periodType: string) => {
    const names = {
      daily: "일간",
      weekly: "주간", 
      monthly: "월간",
      quarterly: "분기별",
      yearly: "연간",
    };
    return names[periodType as keyof typeof names] || periodType;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("ko-KR", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  const handleCitationClick = (citation: CitationSource) => {
    if (citation.url && citation.url !== "#") {
      window.open(citation.url, "_blank");
    }
  };

  const renderCitationInContent = (content: string, citations: CitationSource[]) => {
    // [숫자] 패턴을 찾아서 클릭 가능한 링크로 변환
    const citationPattern = /\\[(\\d+)\\]/g;
    const parts = content.split(citationPattern);
    const result = [];

    for (let i = 0; i < parts.length; i++) {
      if (i % 2 === 0) {
        // 일반 텍스트
        result.push(parts[i]);
      } else {
        // 인용 번호
        const citationNum = parseInt(parts[i]);
        const citation = citations[citationNum - 1];
        
        if (citation) {
          result.push(
            <button
              key={`citation-${citationNum}`}
              onClick={() => handleCitationClick(citation)}
              className="inline-flex items-center text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 font-medium transition-colors duration-150"
              title={`${citation.title} - ${citation.provider}`}
            >
              [{citationNum}]
              <LinkIcon className="w-3 h-3 ml-0.5" />
            </button>
          );
        } else {
          result.push(`[${citationNum}]`);
        }
      }
    }

    return result;
  };

  // ChatGPT 스타일 진행 메시지
  const renderProgressStep = (step: string) => {
    const progressMessages = [
      { text: "뉴스 데이터를 수집하고 있습니다", icon: "🔍" },
      { text: "기사를 발견했습니다", icon: "📰" },
      { text: "기사 내용을 분석하고 중요 정보를 추출하고 있습니다", icon: "🧠" },
      { text: "AI가 종합적인 분석을 수행하고 인사이트를 도출하고 있습니다", icon: "🤖" },
      { text: "레포트를 작성하고 있습니다", icon: "📝" },
      { text: "레포트를 완성하고 있습니다", icon: "✨" },
      { text: "레포트 생성이 완료되었습니다", icon: "✅" },
    ];

    const matchedMessage = progressMessages.find(msg => step.includes(msg.text.slice(0, 10)));
    const icon = matchedMessage?.icon || "⚡";

    return (
      <div className="flex items-center gap-3 text-gray-700 dark:text-gray-300">
        <span className="text-2xl">{icon}</span>
        <span className="font-medium">{step}</span>
      </div>
    );
  };

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center p-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="max-w-md w-full bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 text-center"
        >
          <XCircleIcon className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
            레포트 생성 실패
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mb-6">{error}</p>
          <button
            onClick={() => window.close()}
            className="px-4 py-2 bg-gray-500 hover:bg-gray-600 text-white rounded-lg transition-colors duration-150"
          >
            창 닫기
          </button>
        </motion.div>
      </div>
    );
  }

  if (isGenerating) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center p-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="max-w-lg w-full bg-white dark:bg-gray-800 rounded-xl shadow-lg p-8"
        >
          <div className="text-center mb-8">
            <DocumentChartBarIcon className="w-16 h-16 text-blue-500 mx-auto mb-4" />
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
              {request.company_name} {formatPeriodName(request.period_type)} 레포트
            </h1>
            <p className="text-gray-600 dark:text-gray-400">
              {formatDate(request.date_from)} ~ {formatDate(request.date_to)}
            </p>
          </div>

          {/* 진행률 바 */}
          <div className="mb-6">
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                진행률
              </span>
              <span className="text-sm font-medium text-blue-600 dark:text-blue-400">
                {progress}%
              </span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
              <motion.div
                className="bg-gradient-to-r from-blue-500 to-purple-600 h-2 rounded-full"
                initial={{ width: 0 }}
                animate={{ width: `${progress}%` }}
                transition={{ duration: 0.3 }}
              />
            </div>
          </div>

          {/* ChatGPT 스타일 현재 단계 */}
          <div className="mb-6 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
            {renderProgressStep(currentStep)}
          </div>

          {/* 예상 시간 */}
          {generationStartTime && (
            <div className="flex items-center justify-center gap-2 text-sm text-gray-500 dark:text-gray-400">
              <ClockIcon className="w-4 h-4" />
              경과 시간: {Math.floor((Date.now() - generationStartTime.getTime()) / 1000)}초
            </div>
          )}
        </motion.div>
      </div>
    );
  }

  if (!report) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center p-4">
        <LoadingSpinner variant="pulse" size="lg" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* 헤더 */}
      <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-6xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                {report.metadata.company_name} {formatPeriodName(report.metadata.period_type)} 레포트
              </h1>
              <p className="text-gray-600 dark:text-gray-400 mt-1">
                {formatDate(report.metadata.date_from)} ~ {formatDate(report.metadata.date_to)} 
                <span className="ml-2 text-sm">
                  • {report.metadata.total_articles}개 기사 분석
                  • 생성 시간: {report.metadata.generation_time_seconds}초
                </span>
              </p>
            </div>
            
            <div className="flex items-center gap-2">
              <button
                onClick={() => window.print()}
                className="flex items-center gap-2 px-3 py-2 text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white transition-colors duration-150"
                title="인쇄"
              >
                <PrinterIcon className="w-5 h-5" />
              </button>
              <button
                onClick={() => {
                  navigator.share?.({
                    title: `${report.metadata.company_name} 분석 레포트`,
                    url: window.location.href,
                  });
                }}
                className="flex items-center gap-2 px-3 py-2 text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white transition-colors duration-150"
                title="공유"
              >
                <ShareIcon className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* 메인 콘텐츠 */}
      <main className="max-w-6xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* 메인 레포트 영역 */}
          <div className="lg:col-span-3 space-y-8">
            {/* 경영진 요약 */}
            <motion.section
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6"
            >
              <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                <CheckCircleIcon className="w-6 h-6 text-green-500" />
                경영진 요약
              </h2>
              <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                {report.executive_summary}
              </p>
            </motion.section>

            {/* 레포트 섹션들 */}
            {report.sections.map((section, index) => (
              <motion.section
                key={index}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 + index * 0.1 }}
                className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6"
              >
                <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
                  {section.title}
                </h2>
                
                <div className="prose dark:prose-invert max-w-none">
                  <div className="text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-wrap">
                    {renderCitationInContent(section.content, report.citations)}
                  </div>
                </div>

                {/* 주요 포인트 */}
                {section.key_points.length > 0 && (
                  <div className="mt-6">
                    <h3 className="font-semibold text-gray-900 dark:text-white mb-3">
                      주요 포인트
                    </h3>
                    <ul className="space-y-2">
                      {section.key_points.map((point, idx) => (
                        <li key={idx} className="flex items-start gap-2">
                          <span className="w-1.5 h-1.5 bg-blue-500 rounded-full mt-2 flex-shrink-0" />
                          <span className="text-gray-700 dark:text-gray-300">{point}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </motion.section>
            ))}
          </div>

          {/* 사이드바 */}
          <div className="lg:col-span-1 space-y-6">
            {/* 주요 키워드 */}
            {report.keywords.length > 0 && (
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.3 }}
                className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6"
              >
                <h3 className="font-bold text-gray-900 dark:text-white mb-4">
                  주요 키워드
                </h3>
                <div className="flex flex-wrap gap-2">
                  {report.keywords.map((keyword, index) => (
                    <span
                      key={index}
                      className="px-3 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 text-sm rounded-full"
                    >
                      {keyword}
                    </span>
                  ))}
                </div>
              </motion.div>
            )}

            {/* 인용 출처 */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.4 }}
              className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6"
            >
              <h3 className="font-bold text-gray-900 dark:text-white mb-4">
                참고 기사 ({report.citations.length}개)
              </h3>
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {report.citations.map((citation, index) => (
                  <div key={citation.id} className="group">
                    <button
                      onClick={() => handleCitationClick(citation)}
                      className="w-full text-left p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors duration-150"
                    >
                      <div className="flex items-start gap-3">
                        <span className="flex-shrink-0 w-6 h-6 bg-blue-500 text-white text-xs rounded-full flex items-center justify-center font-medium">
                          {index + 1}
                        </span>
                        <div className="flex-1 min-w-0">
                          <h4 className="font-medium text-gray-900 dark:text-white text-sm line-clamp-2 group-hover:text-blue-600 dark:group-hover:text-blue-400">
                            {citation.title}
                          </h4>
                          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                            {citation.provider} • {formatDate(citation.published_at)}
                          </p>
                        </div>
                        <LinkIcon className="w-4 h-4 text-gray-400 group-hover:text-blue-500 flex-shrink-0" />
                      </div>
                    </button>
                  </div>
                ))}
              </div>
            </motion.div>

            {/* 생성 정보 */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.5 }}
              className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6"
            >
              <h3 className="font-bold text-gray-900 dark:text-white mb-4">
                생성 정보
              </h3>
              <div className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
                <div>
                  생성 일시: {formatDate(report.metadata.generated_at)}
                </div>
                <div>
                  분석 모델: {report.metadata.model_used}
                </div>
                <div>
                  생성 시간: {report.metadata.generation_time_seconds}초
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default ReportGenerationPage;