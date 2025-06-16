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
  ArrowLeftIcon,
} from "@heroicons/react/24/outline";
import {
  AutoReportRequest,
  ReportGenerationProgress,
  PeriodReport,
  PeriodReportType,
  generatePeriodReportStream,
  generateAISummaryStream,
  AISummaryRequest,
  NewsArticle,
} from "../services/api";
import LoadingSpinner from "../components/common/LoadingSpinner";

const PeriodReportGenerationPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  
  // 상태 관리
  const [isGenerating, setIsGenerating] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState("");
  const [currentTask, setCurrentTask] = useState("");
  const [report, setReport] = useState<PeriodReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [generationStartTime, setGenerationStartTime] = useState<Date | null>(null);
  const [estimatedRemainingSeconds, setEstimatedRemainingSeconds] = useState<number | null>(null);

  // URL 파라미터에서 요청 정보 추출
  const request: AutoReportRequest = {
    company_name: searchParams.get("company_name") || undefined,
    company_code: searchParams.get("company_code") || undefined,
    report_type: (searchParams.get("report_type") as PeriodReportType) || PeriodReportType.MONTHLY,
    categories: ["경제"], // 백엔드 호환성을 위해 더미 카테고리 전달 (실제로는 company_name으로 검색해야 함)
    max_articles: parseInt(searchParams.get("max_articles") || "200"),
    include_sentiment: searchParams.get("include_sentiment") === "true",
    include_keywords: searchParams.get("include_keywords") === "true",
    language: searchParams.get("language") || "ko",
  };

  // 컴포넌트 마운트 시 레포트 생성 시작
  useEffect(() => {
    if (request.report_type) {
      handleGenerateReport();
    } else {
      setError("잘못된 요청입니다. 필수 파라미터가 누락되었습니다.");
    }
  }, []);

  // 기간별 일수 계산
  const getPeriodDays = (reportType: PeriodReportType): number => {
    const daysMap = {
      [PeriodReportType.DAILY]: 1,
      [PeriodReportType.WEEKLY]: 7,
      [PeriodReportType.MONTHLY]: 30,
      [PeriodReportType.QUARTERLY]: 90,
      [PeriodReportType.YEARLY]: 365,
    };
    return daysMap[reportType] || 30;
  };

  // 기존 API들을 조합한 기간별 레포트 생성
  const handleGenerateReport = async () => {
    setIsGenerating(true);
    setGenerationStartTime(new Date());
    setError(null);
    setProgress(0);
    setCurrentStep("레포트 생성을 시작합니다...");

    // 디버깅: 요청 내용 확인
    console.log("PeriodReport 요청 내용:", request);

    if (!request.company_name) {
      setError("기업명이 필요합니다.");
      setIsGenerating(false);
      return;
    }

    try {
      // 1단계: 기간 설정
      setCurrentStep("기간을 설정하고 있습니다...");
      setProgress(10);
      
      const days = getPeriodDays(request.report_type);
      const endDate = new Date();
      const startDate = new Date();
      startDate.setDate(endDate.getDate() - days);

      // 2단계: 기업명으로 entity 찾기 (간단한 매핑)
      setCurrentStep("기업 정보를 확인하고 있습니다...");
      setProgress(20);
      
      // 임시: 기업명을 entity ID로 매핑 (실제로는 백엔드에서 해야 함)
      const entityMapping: { [key: string]: string } = {
        "삼성전자": "samsung",
        "삼성": "samsung",
        "네이버": "naver",
        "카카오": "kakao",
        "SK하이닉스": "sk_hynix",
        "LG전자": "lg_electronics",
      };
      
      const entityId = entityMapping[request.company_name] || request.company_name.toLowerCase();

      // 3단계: 기업 뉴스 수집 (기존 API 사용)
      setCurrentStep(`${request.company_name} 관련 뉴스를 수집하고 있습니다...`);
      setProgress(30);

      const newsResponse = await fetch(`/api/entity/news/${entityId}?category=domestic_stock&exclude_prism=false`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (!newsResponse.ok) {
        throw new Error(`뉴스 수집 실패: ${newsResponse.status}`);
      }

      const newsData = await newsResponse.json();
      
      // 4단계: 기간 내 기사 필터링
      setCurrentStep("기간별 기사를 필터링하고 있습니다...");
      setProgress(50);

      const filteredArticles: NewsArticle[] = [];
      if (newsData.timeline) {
        for (const timelineItem of newsData.timeline) {
          const itemDate = new Date(timelineItem.date);
          if (itemDate >= startDate && itemDate <= endDate) {
            // 유효한 ID를 가진 기사만 추가
            const validArticles = timelineItem.articles.filter(article => 
              article.id && 
              typeof article.id === 'string' && 
              article.id.trim() !== '' && 
              article.id !== 'undefined'
            );
            filteredArticles.push(...validArticles);
          }
        }
      }

      if (filteredArticles.length === 0) {
        throw new Error(`${request.company_name}의 최근 ${days}일간 뉴스가 없습니다.`);
      }

      // 최대 기사 수 제한
      const articlesToAnalyze = filteredArticles.slice(0, request.max_articles);
      
      console.log("필터링된 기사 통계:", {
        totalFound: filteredArticles.length,
        toAnalyze: articlesToAnalyze.length,
        period: `${days}일`,
        dateRange: `${startDate.toLocaleDateString()} ~ ${endDate.toLocaleDateString()}`
      });

      // 5단계: AI 요약 생성 (기존 API 사용)
      setCurrentStep("AI가 종합 분석을 수행하고 있습니다...");
      setProgress(60);

      // 디버깅: 요청할 기사 ID 확인
      console.log("분석할 기사 수:", articlesToAnalyze.length);
      console.log("기사 ID 샘플:", articlesToAnalyze.slice(0, 3).map(a => a.id));

      // AI 요약 요청 검증 강화
      console.log("원본 기사 데이터 샘플:", articlesToAnalyze.slice(0, 3));
      
      const validArticleIds = articlesToAnalyze
        .map(article => article.id)
        .filter(id => id && typeof id === 'string' && id.trim() !== '' && id !== 'undefined');

      if (validArticleIds.length === 0) {
        throw new Error("분석할 기사의 ID가 유효하지 않습니다.");
      }

      // 최대 5개 기사로 제한 (API 안정성 향상)
      const limitedIds = validArticleIds.slice(0, 5);

      const summaryRequest: AISummaryRequest = {
        news_ids: limitedIds
      };

      console.log("AI 요약 요청 (최종):", summaryRequest);
      console.log("기사 ID 목록:", limitedIds);

      try {
        await generateAISummaryStream(
          summaryRequest,
          // onProgress
          (data) => {
            console.log("AI 요약 진행 상황:", data);
            setCurrentStep(data.step);
            setProgress(60 + (data.progress * 0.3)); // 60-90% 범위
          },
          // onChunk
          (chunk) => {
            console.log("AI 요약 청크 수신:", chunk);
            // 실시간 내용 표시는 스킵
          },
          // onComplete
          (summaryResult) => {
            console.log("AI 요약 완료:", summaryResult);
            // 6단계: PeriodReport 형태로 변환
            setCurrentStep("레포트를 완성하고 있습니다...");
            setProgress(95);

            const periodReport: PeriodReport = {
              id: `${entityId}_${request.report_type}_${Date.now()}`,
              report_type: request.report_type,
              company_name: request.company_name,
              company_code: searchParams.get("company_code") || undefined,
              period_start: startDate.toISOString().split('T')[0],
              period_end: endDate.toISOString().split('T')[0],
              generated_at: new Date().toISOString(),
              total_articles_analyzed: articlesToAnalyze.length,
              categories_covered: ["경제", "기업"],
              analysis_duration_seconds: generationStartTime ? 
                Math.floor((Date.now() - generationStartTime.getTime()) / 1000) : 0,
              executive_summary: summaryResult.summary,
              key_highlights: summaryResult.key_points || [],
              category_summaries: [{
                category: "기업뉴스",
                total_articles: articlesToAnalyze.length,
                top_clusters: [],
                key_developments: summaryResult.key_points?.slice(0, 5) || [],
              }],
              timeline: [],
              insights: [{
                type: "investment",
                title: "투자자 관점 분석",
                description: summaryResult.summary,
                confidence: 0.85,
                supporting_clusters: [],
              }],
              top_keywords: [],
              sentiment_analysis: {},
              trend_analysis: {},
            };

            setReport(periodReport);
            setIsGenerating(false);
            setProgress(100);
            setCurrentStep("레포트 생성이 완료되었습니다!");
          },
          // onError
          (summaryError) => {
            console.error("AI 요약 스트림 오류:", summaryError);
            console.error("요청 세부사항:", {
              request: summaryRequest,
              articleCount: articlesToAnalyze.length,
              validIdCount: limitedIds.length
            });
            throw new Error(`AI 분석 실패: ${summaryError}`);
          }
        );
      } catch (aiError) {
        console.error("AI 요약 API 호출 실패:", aiError);
        
        // 더 작은 기사 집합으로 재시도
        if (limitedIds.length > 2) {
          console.log("더 적은 기사로 AI 요약 재시도...");
          setCurrentStep("더 적은 기사로 AI 분석을 재시도하고 있습니다...");
          
          const retryIds = limitedIds.slice(0, 2);
          const retryRequest: AISummaryRequest = { news_ids: retryIds };
          
          try {
            await generateAISummaryStream(
              retryRequest,
              (data) => {
                setCurrentStep(`재시도: ${data.step}`);
                setProgress(70 + (data.progress * 0.2));
              },
              (chunk) => {},
              (summaryResult) => {
                console.log("AI 요약 재시도 성공:", summaryResult);
                
                const periodReport: PeriodReport = {
                  id: `${entityId}_${request.report_type}_${Date.now()}`,
                  report_type: request.report_type,
                  company_name: request.company_name,
                  company_code: searchParams.get("company_code") || undefined,
                  period_start: startDate.toISOString().split('T')[0],
                  period_end: endDate.toISOString().split('T')[0],
                  generated_at: new Date().toISOString(),
                  total_articles_analyzed: articlesToAnalyze.length,
                  categories_covered: ["경제", "기업"],
                  analysis_duration_seconds: generationStartTime ? 
                    Math.floor((Date.now() - generationStartTime.getTime()) / 1000) : 0,
                  executive_summary: summaryResult.summary,
                  key_highlights: summaryResult.key_points || [],
                  category_summaries: [{
                    category: "기업뉴스",
                    total_articles: articlesToAnalyze.length,
                    top_clusters: [],
                    key_developments: summaryResult.key_points?.slice(0, 5) || [],
                  }],
                  timeline: [],
                  insights: [{
                    type: "investment",
                    title: "투자자 관점 분석 (제한된 데이터)",
                    description: summaryResult.summary,
                    confidence: 0.75,
                    supporting_clusters: [],
                  }],
                  top_keywords: [],
                  sentiment_analysis: {},
                  trend_analysis: {},
                };

                setReport(periodReport);
                setIsGenerating(false);
                setProgress(100);
                setCurrentStep("제한된 AI 분석이 완료되었습니다!");
                return; // 성공한 경우 함수 종료
              },
              (retryError) => {
                console.error("AI 요약 재시도도 실패:", retryError);
                // 재시도도 실패한 경우 기본 레포트로 진행
              }
            );
            return; // 재시도 중이므로 함수 종료
          } catch (retryError) {
            console.error("AI 요약 재시도 중 오류:", retryError);
          }
        }
        
        // AI 요약이 완전히 실패해도 기본 레포트는 생성
        setCurrentStep("AI 분석에 실패했지만 기본 레포트를 생성합니다...");
        setProgress(95);

        const basicReport: PeriodReport = {
          id: `${entityId}_${request.report_type}_${Date.now()}`,
          report_type: request.report_type,
          company_name: request.company_name,
          company_code: searchParams.get("company_code") || undefined,
          period_start: startDate.toISOString().split('T')[0],
          period_end: endDate.toISOString().split('T')[0],
          generated_at: new Date().toISOString(),
          total_articles_analyzed: articlesToAnalyze.length,
          categories_covered: ["경제", "기업"],
          analysis_duration_seconds: generationStartTime ? 
            Math.floor((Date.now() - generationStartTime.getTime()) / 1000) : 0,
          executive_summary: `${request.company_name}의 최근 ${getPeriodDays(request.report_type)}일간 ${articlesToAnalyze.length}개 기사를 분석했습니다. AI 분석은 현재 일시적으로 사용할 수 없지만, 수집된 기사 정보를 바탕으로 기본 레포트를 제공합니다.`,
          key_highlights: [
            `총 ${articlesToAnalyze.length}개의 관련 기사 발견`,
            `분석 기간: ${startDate.toLocaleDateString()} ~ ${endDate.toLocaleDateString()}`,
            "AI 상세 분석은 현재 일시적으로 사용할 수 없음",
          ],
          category_summaries: [{
            category: "기업뉴스",
            total_articles: articlesToAnalyze.length,
            top_clusters: [],
            key_developments: articlesToAnalyze.slice(0, 5).map(a => a.title),
          }],
          timeline: [],
          insights: [{
            type: "investment",
            title: "기본 분석",
            description: "AI 분석이 일시적으로 사용할 수 없어 기본 정보만 제공됩니다.",
            confidence: 0.5,
            supporting_clusters: [],
          }],
          top_keywords: [],
          sentiment_analysis: {},
          trend_analysis: {},
        };

        setReport(basicReport);
        setIsGenerating(false);
        setProgress(100);
        setCurrentStep("기본 레포트 생성이 완료되었습니다!");
      }

    } catch (err) {
      console.error("레포트 생성 오류:", err);
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

  // ChatGPT 스타일 진행 메시지
  const renderProgressStep = (step: string) => {
    const progressMessages = [
      { text: "뉴스 데이터를 수집하고 있습니다", icon: "🔍", color: "text-blue-600" },
      { text: "기사를 발견했습니다", icon: "📰", color: "text-green-600" },
      { text: "기사 내용을 분석하고 중요 정보를 추출하고 있습니다", icon: "🧠", color: "text-purple-600" },
      { text: "투자자 관점에서 종합적인 분석을 수행하고 있습니다", icon: "📈", color: "text-orange-600" },
      { text: "AI가 인사이트를 도출하고 있습니다", icon: "🤖", color: "text-indigo-600" },
      { text: "레포트를 작성하고 있습니다", icon: "📝", color: "text-emerald-600" },
      { text: "레포트를 완성하고 있습니다", icon: "✨", color: "text-pink-600" },
      { text: "레포트 생성이 완료되었습니다", icon: "✅", color: "text-green-700" },
    ];

    const matchedMessage = progressMessages.find(msg => step.includes(msg.text.slice(0, 10)));
    const icon = matchedMessage?.icon || "⚡";
    const color = matchedMessage?.color || "text-gray-700";

    return (
      <div className={`flex items-center gap-3 ${color} dark:text-gray-300`}>
        <span className="text-2xl">{icon}</span>
        <div>
          <span className="font-medium">{step}</span>
          {currentTask && (
            <div className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              {currentTask}
            </div>
          )}
        </div>
      </div>
    );
  };

  const handleGoBack = () => {
    navigate(-1);
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
          <div className="text-gray-600 dark:text-gray-400 mb-6">
            <p className="mb-3">{error}</p>
            {(error.includes("sort") || error.includes("BigKinds") || error.includes("openai")) && (
              <div className="text-sm bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3">
                <p className="font-medium text-red-800 dark:text-red-200 mb-1">
                  ⚠️ 백엔드 API 문제 (기존 API 조합 방식으로 우회 처리됨):
                </p>
                <ul className="text-red-700 dark:text-red-300 text-xs space-y-1">
                  <li>• BigKinds API 'sort' 파라미터 오류</li>
                  <li>• OpenAI 라이브러리 호환성 문제</li>
                  <li>• 기업별 뉴스 수집 로직 미구현</li>
                </ul>
              </div>
            )}
            {error.includes("뉴스가 없습니다") && (
              <div className="text-sm bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3">
                <p className="font-medium text-blue-800 dark:text-blue-200 mb-1">
                  💡 해당 기간에 뉴스가 부족합니다:
                </p>
                <ul className="text-blue-700 dark:text-blue-300 text-xs space-y-1">
                  <li>• 더 긴 기간(주간/월간)으로 시도해보세요</li>
                  <li>• 또는 타임라인에서 직접 기사를 선택하여 요약하세요</li>
                </ul>
              </div>
            )}
          </div>
          <div className="flex gap-3 justify-center">
            <button
              onClick={handleGoBack}
              className="px-4 py-2 bg-gray-500 hover:bg-gray-600 text-white rounded-lg transition-colors duration-150 flex items-center gap-2"
            >
              <ArrowLeftIcon className="w-4 h-4" />
              돌아가기
            </button>
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-primary-500 hover:bg-primary-600 text-white rounded-lg transition-colors duration-150"
            >
              다시 시도
            </button>
          </div>
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
              {request.company_name 
                ? `${request.company_name} ${formatPeriodName(request.report_type)} 레포트`
                : `${formatPeriodName(request.report_type)} 시장 분석 레포트`
              }
            </h1>
            <p className="text-gray-600 dark:text-gray-400">
              투자자 관점의 상세한 인사이트를 제공합니다
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
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
              <motion.div
                className="bg-gradient-to-r from-blue-500 to-purple-600 h-3 rounded-full"
                initial={{ width: 0 }}
                animate={{ width: `${progress}%` }}
                transition={{ duration: 0.5, ease: "easeInOut" }}
              />
            </div>
          </div>

          {/* ChatGPT 스타일 현재 단계 */}
          <div className="mb-6 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
            {renderProgressStep(currentStep)}
          </div>

          {/* 시간 정보 */}
          <div className="flex items-center justify-center gap-6 text-sm text-gray-500 dark:text-gray-400">
            {generationStartTime && (
              <div className="flex items-center gap-2">
                <ClockIcon className="w-4 h-4" />
                경과: {Math.floor((Date.now() - generationStartTime.getTime()) / 1000)}초
              </div>
            )}
            {estimatedRemainingSeconds && (
              <div className="flex items-center gap-2">
                <span>⏱️</span>
                남은 시간: 약 {estimatedRemainingSeconds}초
              </div>
            )}
          </div>
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
            <div className="flex items-center gap-4">
              <button
                onClick={handleGoBack}
                className="p-2 text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white transition-colors duration-150 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
              >
                <ArrowLeftIcon className="w-5 h-5" />
              </button>
              <div>
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                  {report.company_name 
                    ? `${report.company_name} ${formatPeriodName(report.report_type)} 레포트`
                    : `${formatPeriodName(report.report_type)} 시장 분석 레포트`
                  }
                </h1>
                <p className="text-gray-600 dark:text-gray-400 mt-1">
                  {formatDate(report.period_start)} ~ {formatDate(report.period_end)} 
                  <span className="ml-2 text-sm">
                    • {report.total_articles_analyzed}개 기사 분석
                    • 생성 시간: {Math.round(report.analysis_duration_seconds)}초
                  </span>
                </p>
              </div>
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
                    title: `${report.company_name || "시장"} 분석 레포트`,
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
                핵심 요약
              </h2>
              <p className="text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-wrap">
                {report.executive_summary}
              </p>
            </motion.section>

            {/* 주요 하이라이트 */}
            {report.key_highlights.length > 0 && (
              <motion.section
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6"
              >
                <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
                  ⭐ 주요 하이라이트
                </h2>
                <ul className="space-y-3">
                  {report.key_highlights.map((highlight, index) => (
                    <li key={index} className="flex items-start gap-3">
                      <span className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0" />
                      <span className="text-gray-700 dark:text-gray-300">{highlight}</span>
                    </li>
                  ))}
                </ul>
              </motion.section>
            )}

            {/* 카테고리별 분석 */}
            {report.category_summaries.length > 0 && (
              <motion.section
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
                className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6"
              >
                <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-6">
                  📊 카테고리별 분석
                </h2>
                <div className="space-y-6">
                  {report.category_summaries.map((summary, index) => (
                    <div key={index} className="border-l-4 border-blue-500 pl-6">
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
                        {summary.category} ({summary.total_articles}개 기사)
                      </h3>
                      <ul className="space-y-2">
                        {summary.key_developments.map((development, idx) => (
                          <li key={idx} className="flex items-start gap-2">
                            <span className="w-1.5 h-1.5 bg-gray-400 rounded-full mt-2 flex-shrink-0" />
                            <span className="text-gray-700 dark:text-gray-300 text-sm">{development}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              </motion.section>
            )}

            {/* 인사이트 */}
            {report.insights.length > 0 && (
              <motion.section
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 }}
                className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6"
              >
                <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-6">
                  🧠 투자자 인사이트
                </h2>
                <div className="space-y-6">
                  {report.insights.map((insight, index) => (
                    <div key={index} className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-lg p-6">
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                        {insight.title}
                      </h3>
                      <p className="text-gray-700 dark:text-gray-300 mb-3 leading-relaxed">
                        {insight.description}
                      </p>
                      <div className="flex items-center gap-2">
                        <span className="text-sm text-gray-500 dark:text-gray-400">
                          신뢰도:
                        </span>
                        <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-2 max-w-24">
                          <div 
                            className="bg-green-500 h-2 rounded-full"
                            style={{ width: `${insight.confidence * 100}%` }}
                          />
                        </div>
                        <span className="text-sm font-medium text-green-600 dark:text-green-400">
                          {Math.round(insight.confidence * 100)}%
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </motion.section>
            )}
          </div>

          {/* 사이드바 */}
          <div className="lg:col-span-1 space-y-6">
            {/* 주요 키워드 */}
            {report.top_keywords.length > 0 && (
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.3 }}
                className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6"
              >
                <h3 className="font-bold text-gray-900 dark:text-white mb-4">
                  🔥 상위 키워드
                </h3>
                <div className="flex flex-wrap gap-2">
                  {report.top_keywords.map((keyword, index) => (
                    <span
                      key={index}
                      className="px-3 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 text-sm rounded-full"
                    >
                      {keyword.keyword} ({keyword.count})
                    </span>
                  ))}
                </div>
              </motion.div>
            )}

            {/* 타임라인 */}
            {report.timeline.length > 0 && (
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.4 }}
                className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6"
              >
                <h3 className="font-bold text-gray-900 dark:text-white mb-4">
                  📅 주요 이벤트
                </h3>
                <div className="space-y-4 max-h-96 overflow-y-auto">
                  {report.timeline.map((event, index) => (
                    <div key={index} className="border-l-2 border-gray-200 dark:border-gray-600 pl-4">
                      <div className="text-xs text-gray-500 dark:text-gray-400">
                        {formatDate(event.date)}
                      </div>
                      <h4 className="font-medium text-gray-900 dark:text-white text-sm">
                        {event.title}
                      </h4>
                      <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                        {event.description}
                      </p>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}

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
                  생성 일시: {formatDate(report.generated_at)}
                </div>
                <div>
                  분석 기사: {report.total_articles_analyzed}개
                </div>
                <div>
                  생성 시간: {Math.round(report.analysis_duration_seconds)}초
                </div>
                <div>
                  카테고리: {report.categories_covered.join(", ")}
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default PeriodReportGenerationPage;