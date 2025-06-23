import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import LoadingSpinner from "../components/common/LoadingSpinner";
import ErrorMessage from "../components/common/ErrorMessage";
import ThinkingProgress from "../components/ai/ThinkingProgress";
import { containerVariants, itemVariants } from "../animations/pageAnimations";
import { generateAISummaryStream } from "../services/api";
import { getArticleLink } from "../services/newsApi";
import CompanyPeriodReportButton from "../components/reports/CompanyPeriodReportButton";

// 인터페이스 정의
interface Entity {
  id: string;
  name: string;
  code: string;
  variants: string[];
  category: string;
  category_name: string;
}

interface NewsArticle {
  id: string;
  title: string;
  summary: string;
  content?: string;
  provider: string;
  provider_code?: string;
  url: string;
  category: string;
  byline: string;
  images: string[];
  images_caption?: string;
  published_at?: string;
}

interface TimelineItem {
  date: string;
  articles: NewsArticle[];
  count: number;
}

interface CategoryInfo {
  key: string;
  name: string;
  count: number;
}

// 카테고리 메타데이터
const CATEGORY_META: { [key: string]: { icon: string; description: string } } = {
  domestic_stock: { icon: "🏢", description: "국내 상장 기업 주식" },
  foreign_stock: { icon: "🌎", description: "미국 등 해외 상장 기업 주식" },
  commodity: { icon: "🏭", description: "원자재 및 상품" },
  forex_bond: { icon: "💱", description: "외환 및 채권 관련" },
  real_estate: { icon: "🏘️", description: "부동산 관련" },
  crypto: { icon: "🪙", description: "암호화폐 및 가상자산" }
};

const CategoryDetailPage: React.FC = () => {
  const { categoryKey } = useParams<{ categoryKey: string }>();
  const navigate = useNavigate();
  
  // 상태 관리
  const [entities, setEntities] = useState<Entity[]>([]);
  const [selectedEntity, setSelectedEntity] = useState<Entity | null>(null);
  const [categoryInfo, setCategoryInfo] = useState<CategoryInfo | null>(null);
  const [timeline, setTimeline] = useState<TimelineItem[]>([]);
  const [isLoadingEntities, setIsLoadingEntities] = useState(true);
  const [isLoadingNews, setIsLoadingNews] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [activeTab, setActiveTab] = useState<'seoul' | 'all'>('all');
  const [showDetails, setShowDetails] = useState(false);
  const [selectedArticles, setSelectedArticles] = useState<Map<string, NewsArticle>>(new Map());
  const [summaryResult, setSummaryResult] = useState<any>(null);
  const [isGeneratingSummary, setIsGeneratingSummary] = useState(false);
  const [showSummarySidebar, setShowSummarySidebar] = useState(false);
  
  // 스트리밍 관련 상태
  const [streamingStep, setStreamingStep] = useState<string>("");
  const [streamingProgress, setStreamingProgress] = useState<number>(0);
  const [streamingContent, setStreamingContent] = useState<string>("");
  const [articleReferences, setArticleReferences] = useState<any[]>([]);
  
  // 사이드바 크기 조절 관련 상태
  const [sidebarWidth, setSidebarWidth] = useState(384); // 기본 w-96 (384px)
  const [isResizing, setIsResizing] = useState(false);

  // 초기화 함수
  const handleReset = () => {
    setSelectedArticles(new Map());
    setSummaryResult(null);
    setStreamingContent("");
    setArticleReferences([]);
    setIsGeneratingSummary(false);
  };

  // 카테고리 정보 및 엔티티 목록 불러오기
  useEffect(() => {
    if (categoryKey) {
      fetchCategoryData();
    }
  }, [categoryKey]);

  // 선택된 엔티티의 뉴스 불러오기
  useEffect(() => {
    if (selectedEntity) {
      fetchEntityNews();
    }
  }, [selectedEntity, activeTab]);

  const fetchCategoryData = async () => {
    setIsLoadingEntities(true);
    setError(null);
    
    try {
      // 카테고리 정보 가져오기
      const categoriesRes = await fetch("/api/entity/categories");
      const categoriesData = await categoriesRes.json();
      const category = categoriesData.categories.find((c: any) => c.key === categoryKey);
      
      if (category) {
        setCategoryInfo({
          key: category.key,
          name: category.name,
          count: category.count
        });
      }
      
      // 엔티티 목록 가져오기
      const response = await fetch(`/api/entity/category/${categoryKey}`);
      if (!response.ok) throw new Error("엔티티 목록을 불러오는데 실패했습니다");
      
      const data = await response.json();
      setEntities(data.entities);
      
      // 첫 번째 엔티티 자동 선택
      if (data.entities.length > 0) {
        setSelectedEntity(data.entities[0]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "알 수 없는 오류가 발생했습니다");
    } finally {
      setIsLoadingEntities(false);
    }
  };

  const fetchEntityNews = async () => {
    if (!selectedEntity || !categoryKey) return;
    
    setIsLoadingNews(true);
    setError(null);
    
    try {
      const provider = activeTab === 'seoul' ? ['서울경제'] : undefined;
      const params = new URLSearchParams({
        category: categoryKey,
        exclude_prism: 'false',
        ...(provider && { provider: provider.join(',') })
      });
      
      const url = `/api/entity/news/${selectedEntity.id}?${params}`;
      const response = await fetch(url, { method: 'POST' });
      
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`뉴스를 불러오는데 실패했습니다 (${response.status}): ${errorText}`);
      }
      
      const data = await response.json();
      setTimeline(data.timeline || []);
    } catch (err) {
      console.error('fetchEntityNews error:', err);
      setError(err instanceof Error ? err.message : "알 수 없는 오류가 발생했습니다");
    } finally {
      setIsLoadingNews(false);
    }
  };

  // 엔티티 검색 필터링
  const filteredEntities = entities.filter(entity => 
    entity.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    entity.code.toLowerCase().includes(searchQuery.toLowerCase()) ||
    entity.variants.some(v => v.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  // 뉴스 상세 보기
  const viewArticleDetail = (article: NewsArticle) => {
    // 전체 언론사 탭에서는 저작권 준수를 위해 외부 링크로 이동
    if (activeTab === 'all') {
      window.open(getArticleLink(article), '_blank');
    } else {
      // 서울경제 탭에서는 내부 페이지로 이동
      navigate(`/news/${article.id}`);
    }
  };

  // 기사 선택/해제
  const toggleArticleSelection = (article: NewsArticle) => {
    const newSelected = new Map(selectedArticles);
    
    if (newSelected.has(article.id)) {
      newSelected.delete(article.id);
    } else if (newSelected.size < 5) {
      newSelected.set(article.id, article);
    }
    
    setSelectedArticles(newSelected);
  };

  // AI 요약 생성 - 스트리밍 버전
  const handleGenerateSummary = async () => {
    console.log("handleGenerateSummary 호출됨", selectedArticles.size);
    
    if (selectedArticles.size === 0) {
      console.warn("선택된 기사가 없습니다");
      return;
    }

    setIsGeneratingSummary(true);
    setSummaryResult(null);
    setStreamingStep("");
    setStreamingProgress(0);
    setStreamingContent("");
    setArticleReferences([]);

    // 사이드바가 닫혀있으면 열기
    if (!showSummarySidebar) {
      setShowSummarySidebar(true);
    }

    try {
      console.log("API 호출 시작:", Array.from(selectedArticles.keys()));
      
      await generateAISummaryStream(
        { news_ids: Array.from(selectedArticles.keys()) },
        // onProgress
        (data) => {
          console.log("Progress:", data);
          setStreamingStep(data.step);
          setStreamingProgress(data.progress);
        },
        // onChunk
        (chunk) => {
          console.log("Chunk received:", chunk);
          setStreamingContent(prev => prev + chunk);
        },
        // onComplete
        (result) => {
          console.log("Complete:", result);
          setSummaryResult(result);
          setArticleReferences(result.article_references || []);
          setIsGeneratingSummary(false);
        },
        // onError
        (error) => {
          console.error("Stream error:", error);
          setError(error);
          setIsGeneratingSummary(false);
        }
      );
    } catch (err) {
      console.error("Catch error:", err);
      setError(err instanceof Error ? err.message : "알 수 없는 오류가 발생했습니다");
      setIsGeneratingSummary(false);
    }
  };

  // 요약 텍스트에서 기사 참조를 링크로 변환
  const renderTextWithReferences = (text: string) => {
    if (!articleReferences.length) return text;
    
    // [ref1], [ref2] 등의 패턴을 찾아서 클릭 가능한 링크로 변환
    const refPattern = /\[ref(\d+)\]/g;
    const parts = text.split(refPattern);
    
    return parts.map((part, index) => {
      // 숫자인 경우 (ref 번호)
      if (index % 2 === 1) {
        const refNumber = parseInt(part);
        const ref = articleReferences.find(r => r.ref_id === `ref${refNumber}`);
        
        if (ref) {
          return (
            <button
              key={index}
              onClick={() => {
                // 기사 참조 섹션으로 스크롤
                const element = document.getElementById(`ref-${ref.ref_id}`);
                if (element) {
                  element.scrollIntoView({ behavior: 'smooth', block: 'center' });
                  // 하이라이트 효과
                  element.classList.add('ring-2', 'ring-primary-300', 'ring-opacity-75');
                  setTimeout(() => {
                    element.classList.remove('ring-2', 'ring-primary-300', 'ring-opacity-75');
                  }, 2000);
                }
              }}
              className="inline-flex items-center px-2 py-1 mx-1 text-xs font-mono bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-300 rounded hover:bg-primary-200 dark:hover:bg-primary-800 transition-colors"
              title={`${ref.title} (${ref.provider})`}
            >
              [ref{refNumber}]
            </button>
          );
        }
        return `[ref${refNumber}]`;
      }
      
      // 일반 텍스트
      return part;
    });
  };

  // 이미지 URL 처리 (WatchlistPage에서 가져옴)
  const getImageUrl = (rawPath: string | undefined): string | null => {
    if (!rawPath) return null;
    
    try {
      const unescaped = rawPath.replace(/\\\\n/g, "\\n").replace(/\\n/g, "\n");
      const pathParts = unescaped.split(/[\n,]+/);
      const firstPath = pathParts[0]?.trim() || "";
      
      if (!firstPath || firstPath === "" || firstPath === "/") {
        return null;
      }
      
      if (firstPath.startsWith("http://") || firstPath.startsWith("https://")) {
        return `/api/proxy/image?url=${encodeURIComponent(firstPath)}`;
      }
      
      const normalizedPath = firstPath.startsWith("/") ? firstPath : `/${firstPath}`;
      const baseUrl = "https://www.bigkinds.or.kr/resources/images";
      const fullImageUrl = `${baseUrl}${normalizedPath}`;
      
      return `/api/proxy/image?url=${encodeURIComponent(fullImageUrl)}`;
    } catch (error) {
      return null;
    }
  };

  const hasValidImage = (article: NewsArticle): boolean => {
    return !!(
      article.images &&
      article.images.length > 0 &&
      article.images[0] &&
      article.images[0].trim() !== ""
    );
  };

  // 사이드바 크기 조절 핸들러
  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizing(true);
  };

  const handleMouseMove = (e: MouseEvent) => {
    if (!isResizing) return;
    
    const newWidth = window.innerWidth - e.clientX;
    const minWidth = 300; // 최소 너비
    const maxWidth = 800; // 최대 너비
    
    if (newWidth >= minWidth && newWidth <= maxWidth) {
      setSidebarWidth(newWidth);
    }
  };

  const handleMouseUp = () => {
    setIsResizing(false);
  };

  // 마우스 이벤트 리스너 등록/해제
  useEffect(() => {
    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
    } else {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
  }, [isResizing]);

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={containerVariants}
      className="flex h-screen bg-gray-50 dark:bg-gray-900"
    >
      {/* 사이드바 */}
      <motion.aside
        variants={itemVariants}
        className="w-80 bg-white dark:bg-gray-800 shadow-lg overflow-hidden flex flex-col"
      >
        {/* 헤더 */}
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <button
            onClick={() => navigate('/watchlist')}
            className="flex items-center text-gray-600 dark:text-gray-400 hover:text-primary-600 dark:hover:text-primary-400 mb-4"
          >
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            카테고리 목록으로
          </button>
          
          <div className="flex items-center gap-3">
            <div className="text-3xl">{CATEGORY_META[categoryKey || '']?.icon || '📊'}</div>
            <div>
              <h2 className="text-xl font-bold">{categoryInfo?.name}</h2>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {CATEGORY_META[categoryKey || '']?.description}
              </p>
            </div>
          </div>
        </div>

        {/* 검색 */}
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="relative">
            <input
              type="text"
              placeholder="종목 검색..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
            <svg
              className="absolute left-3 top-2.5 w-5 h-5 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
          </div>
        </div>

        {/* 엔티티 목록 */}
        <div className="flex-1 overflow-y-auto">
          {isLoadingEntities ? (
            <div className="flex justify-center py-8">
              <LoadingSpinner />
            </div>
          ) : (
            <div className="p-2">
              {filteredEntities.map((entity) => (
                <motion.button
                  key={entity.id}
                  onClick={() => setSelectedEntity(entity)}
                  className={`w-full text-left p-3 rounded-lg mb-1 transition-all ${
                    selectedEntity?.id === entity.id
                      ? 'bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300'
                      : 'hover:bg-gray-100 dark:hover:bg-gray-700'
                  }`}
                  whileHover={{ x: 4 }}
                >
                  <div className="font-medium">{entity.name}</div>
                  <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    {entity.code}
                  </div>
                </motion.button>
              ))}
            </div>
          )}
        </div>
      </motion.aside>

      {/* 메인 콘텐츠 */}
      <main className="flex-1 overflow-y-auto">
        {selectedEntity ? (
          <div className="max-w-6xl mx-auto p-8">
            {/* 엔티티 헤더 */}
            <motion.div variants={itemVariants} className="mb-8">
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h1 className="text-3xl font-bold mb-2">{selectedEntity.name}</h1>
                    <p className="text-lg text-gray-600 dark:text-gray-400">
                      {selectedEntity.code}
                    </p>
                  </div>
                  <button
                    onClick={() => setShowDetails(!showDetails)}
                    className="text-sm text-primary-600 dark:text-primary-400 hover:underline"
                  >
                    {showDetails ? '동의어 숨기기' : '동의어 보기'}
                  </button>
                </div>
                
                {showDetails && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="pt-4 border-t border-gray-200 dark:border-gray-700"
                  >
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">검색 동의어:</p>
                    <div className="flex flex-wrap gap-2">
                      {selectedEntity.variants.map((variant, index) => (
                        <span
                          key={index}
                          className="px-3 py-1 bg-gray-100 dark:bg-gray-700 rounded-full text-sm"
                        >
                          {variant}
                        </span>
                      ))}
                    </div>
                  </motion.div>
                )}
              </div>
            </motion.div>


            {/* 탭 선택 및 AI 요약 버튼 */}
            <motion.div variants={itemVariants} className="mb-6">
              <div className="flex justify-between items-center">
                <div className="flex bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
                <button
                  onClick={() => setActiveTab('all')}
                  className={`px-6 py-2 rounded-md text-sm font-medium transition-all ${
                    activeTab === 'all'
                      ? 'bg-white dark:bg-gray-700 text-primary-600 dark:text-primary-400 shadow-sm'
                      : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
                  }`}
                >
                  전체 언론사
                </button>
                <button
                  onClick={() => setActiveTab('seoul')}
                  className={`px-6 py-2 rounded-md text-sm font-medium transition-all ${
                    activeTab === 'seoul'
                      ? 'bg-white dark:bg-gray-700 text-primary-600 dark:text-primary-400 shadow-sm'
                      : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
                  }`}
                >
                  서울경제
                </button>
                </div>
                
                <div className="flex items-center gap-3">
                  {/* 기간별 레포트 생성 버튼 */}
                  {selectedEntity && (
                    <CompanyPeriodReportButton
                      companyName={selectedEntity.name}
                      companyCode={selectedEntity.code}
                    />
                  )}
                  
                  {/* AI 요약 토글 버튼 */}
                  <motion.button
                  onClick={() => setShowSummarySidebar(prev => !prev)}
                  disabled={selectedArticles.size === 0}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all ${
                    selectedArticles.size > 0
                      ? 'bg-primary-500 hover:bg-primary-600 text-white shadow-md hover:shadow-lg'
                      : 'bg-gray-200 dark:bg-gray-700 text-gray-400 cursor-not-allowed'
                  }`}
                  whileHover={selectedArticles.size > 0 ? { scale: 1.02 } : {}}
                  whileTap={selectedArticles.size > 0 ? { scale: 0.98 } : {}}
                >
                  <svg
                    className="w-5 h-5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                    />
                  </svg>
                  <span className="hidden sm:inline">
                    {selectedArticles.size > 0
                      ? `${selectedArticles.size}개 기사 요약`
                      : '기사를 선택하세요'}
                  </span>
                  </motion.button>
                </div>
              </div>
            </motion.div>

            {/* 선택된 기사 고정 표시 */}
            {selectedArticles.size > 0 && (
              <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                variants={itemVariants}
                className="mb-6 p-4 bg-gradient-to-r from-primary-50 to-blue-50 dark:from-primary-900/20 dark:to-blue-900/20 border border-primary-200 dark:border-primary-800 rounded-lg"
              >
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-lg font-semibold text-primary-700 dark:text-primary-300">
                    선택된 기사 ({selectedArticles.size}/5)
                  </h3>
                  <div className="flex gap-2">
                    <button
                      onClick={handleReset}
                      className="px-3 py-1 text-sm bg-red-100 hover:bg-red-200 dark:bg-red-900/30 dark:hover:bg-red-900/50 text-red-700 dark:text-red-300 rounded-lg transition-colors"
                    >
                      전체 초기화
                    </button>
                    <button
                      onClick={handleGenerateSummary}
                      disabled={selectedArticles.size === 0}
                      className={`px-3 py-1 text-sm rounded-lg transition-colors ${
                        selectedArticles.size > 0
                          ? "bg-primary-100 hover:bg-primary-200 dark:bg-primary-900/30 dark:hover:bg-primary-900/50 text-primary-700 dark:text-primary-300"
                          : "bg-gray-100 dark:bg-gray-700 text-gray-400 cursor-not-allowed"
                      }`}
                    >
                      요약 생성
                    </button>
                  </div>
                </div>
                <div className="flex flex-wrap gap-2">
                  {Array.from(selectedArticles.values()).map((article, index) => (
                    <div
                      key={article.id}
                      className="group flex items-center gap-2 px-3 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-lg text-sm hover:shadow-md transition-all"
                    >
                      <span className="text-primary-600 dark:text-primary-400 font-mono text-xs">
                        [{index + 1}]
                      </span>
                      <span className="line-clamp-1 flex-1">
                        {article.title}
                      </span>
                      <button
                        onClick={() => {
                          const newSelected = new Map(selectedArticles);
                          newSelected.delete(article.id);
                          setSelectedArticles(newSelected);
                        }}
                        className="opacity-0 group-hover:opacity-100 p-1 text-red-500 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-900/30 rounded transition-all"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}

            {/* 뉴스 타임라인 */}
            <motion.div variants={itemVariants}>
              <h2 className="text-2xl font-bold mb-6">뉴스 타임라인</h2>
              
              {error && <ErrorMessage message={error} />}
              
              {isLoadingNews ? (
                <div className="flex justify-center py-12">
                  <LoadingSpinner />
                </div>
              ) : timeline.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                  {activeTab === 'seoul' 
                    ? '서울경제에 관련 기사가 없습니다.' 
                    : '관련 기사가 없습니다.'}
                </div>
              ) : (
                <div className="space-y-8">
                  {timeline.map((timelineItem) => (
                    <div key={timelineItem.date}>
                      <div className="flex items-center mb-4">
                        <div className="flex-shrink-0 w-32 text-sm font-medium text-gray-600 dark:text-gray-400">
                          {new Date(timelineItem.date).toLocaleDateString('ko-KR', {
                            year: 'numeric',
                            month: 'long',
                            day: 'numeric'
                          })}
                        </div>
                        <div className="flex-grow h-px bg-gray-200 dark:bg-gray-700 ml-4" />
                        <div className="ml-4 text-sm text-gray-500">
                          {timelineItem.count}건
                        </div>
                      </div>
                      
                      <div className="ml-36 space-y-4">
                        {timelineItem.articles.map((article) => (
                          <motion.div
                            key={article.id}
                            className="card p-4 relative cursor-pointer hover:shadow-md transition-all"
                            onClick={(e) => {
                              // 체크박스 클릭이 아닌 경우만 상세보기로 이동
                              if (!(e.target as HTMLElement).closest('.checkbox-container')) {
                                viewArticleDetail(article);
                              }
                            }}
                            whileHover={{ scale: 1.02 }}
                          >
                            {/* 체크박스 */}
                            <div
                              className="checkbox-container absolute top-4 right-4 z-10"
                              onClick={(e) => {
                                e.stopPropagation();
                                toggleArticleSelection(article);
                              }}
                            >
                              <input
                                type="checkbox"
                                checked={selectedArticles.has(article.id)}
                                onChange={(e) => {
                                  e.stopPropagation();
                                  toggleArticleSelection(article);
                                }}
                                className="w-5 h-5 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                              />
                            </div>

                            <div className="flex gap-4 pr-8">
                              {/* 이미지 */}
                              {hasValidImage(article) && getImageUrl(article.images?.[0]) ? (
                                <div className="flex-shrink-0 w-24 h-20 overflow-hidden rounded-lg">
                                  <img
                                    src={getImageUrl(article.images?.[0])!}
                                    alt={article.title}
                                    className="w-full h-full object-cover"
                                  />
                                </div>
                              ) : (
                                <div className="flex-shrink-0 w-24 h-20 bg-gray-100 dark:bg-gray-700 rounded-lg flex items-center justify-center">
                                  <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                                  </svg>
                                </div>
                              )}
                              
                              {/* 내용 */}
                              <div className="flex-1 min-w-0">
                                <h4 className="font-semibold mb-2 line-clamp-2">{article.title}</h4>
                                <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2 mb-3">
                                  {article.summary}
                                </p>
                                <div className="flex justify-between items-center text-xs text-gray-500">
                                  <div className="flex items-center gap-2">
                                    {activeTab === 'all' && (
                                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                                        {article.provider}
                                      </span>
                                    )}
                                    {article.byline && <span>· {article.byline}</span>}
                                  </div>
                                  <span>{article.category}</span>
                                </div>
                              </div>
                            </div>
                          </motion.div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </motion.div>
          </div>
        ) : (
          <div className="flex items-center justify-center h-full">
            <p className="text-gray-500 text-lg">종목을 선택해주세요</p>
          </div>
        )}
      </main>


      {/* AI 요약 사이드바 */}
      {showSummarySidebar && (
        <motion.div
          initial={{ x: sidebarWidth }}
          animate={{ x: 0 }}
          exit={{ x: sidebarWidth }}
          transition={{ type: "spring", damping: 25, stiffness: 120 }}
          className="fixed top-0 right-0 h-screen bg-white dark:bg-gray-800 shadow-xl border-l border-gray-200 dark:border-gray-700 z-40 overflow-hidden"
          style={{ width: sidebarWidth }}
        >
          {/* 크기 조절 핸들 */}
          <div
            className="absolute top-0 left-0 w-1 h-full cursor-col-resize bg-transparent hover:bg-primary-200 dark:hover:bg-primary-700 transition-colors group"
            onMouseDown={handleMouseDown}
          >
            <div className="absolute top-1/2 left-0 transform -translate-y-1/2 -translate-x-1/2 w-3 h-12 bg-gray-300 dark:bg-gray-600 group-hover:bg-primary-400 dark:group-hover:bg-primary-500 rounded-full flex items-center justify-center transition-colors">
              <div className="w-0.5 h-6 bg-white dark:bg-gray-800 rounded-full"></div>
            </div>
          </div>

          {/* 사이드바 토글 버튼 */}
          <button
            onClick={() => setShowSummarySidebar(false)}
            className="absolute top-1/2 left-0 transform -translate-y-1/2 -translate-x-full w-10 h-20 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-l-xl flex items-center justify-center shadow-lg hover:shadow-xl transition-all ml-3"
            aria-label="사이드바 닫기"
          >
            <div className="flex items-center justify-center w-full h-full bg-gradient-to-r from-primary-50 to-primary-100 dark:from-primary-900/30 dark:to-primary-800/30">
              <svg
                className="w-5 h-5 text-primary-600 dark:text-primary-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 19l-7-7 7-7"
                />
              </svg>
            </div>
          </button>

          <div className="h-full overflow-y-auto">
            <div 
              className="pl-8 pr-6 py-6 space-y-6"
              style={{
                fontSize: sidebarWidth > 500 ? '16px' : sidebarWidth > 400 ? '14px' : '12px'
              }}
            >
              <div className="flex justify-between items-center">
                <h2 className="text-2xl font-bold">
                  {summaryResult ? "통합 인사이트 보고서" : "AI 요약 분석"}
                </h2>
                <div className="flex items-center gap-2">
                  {(selectedArticles.size > 0 || summaryResult) && (
                    <button
                      onClick={handleReset}
                      className="p-2 text-red-500 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-900/30 rounded-lg transition-all"
                      title="전체 초기화"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                    </button>
                  )}
                  <div
                    className={`w-3 h-3 rounded-full ${
                      selectedArticles.size > 0
                        ? "bg-green-400 animate-pulse"
                        : "bg-gray-300"
                    }`}
                  />
                  <span className="text-sm text-gray-500">
                    {selectedArticles.size}/5
                  </span>
                </div>
              </div>

              {!summaryResult && !isGeneratingSummary && (
                <>
                  <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
                    <h3 className="font-semibold mb-2">선택된 기사</h3>
                    <div className="space-y-2 max-h-[300px] overflow-y-auto">
                      {selectedArticles.size > 0 ? (
                        Array.from(selectedArticles.values()).map((article, index) => (
                          <div
                            key={article.id}
                            className="group p-3 bg-gray-50 dark:bg-gray-700 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors"
                          >
                            <div className="flex items-start justify-between">
                              <div className="flex-1">
                                <div className="flex items-center gap-2 mb-1">
                                  <span className="text-primary-600 dark:text-primary-400 font-mono text-xs">
                                    [{index + 1}]
                                  </span>
                                  <p className="font-medium text-sm line-clamp-2">
                                    {article.title}
                                  </p>
                                </div>
                                <p className="text-xs text-gray-500 mt-1">
                                  {article.provider}
                                </p>
                              </div>
                              <button
                                onClick={() => {
                                  const newSelected = new Map(selectedArticles);
                                  newSelected.delete(article.id);
                                  setSelectedArticles(newSelected);
                                }}
                                className="opacity-0 group-hover:opacity-100 p-1 text-red-500 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-900/30 rounded transition-all ml-2"
                                title="선택 해제"
                              >
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                </svg>
                              </button>
                            </div>
                          </div>
                        ))
                      ) : (
                        <p className="text-sm text-gray-500">
                          타임라인에서 기사를 선택해주세요.
                        </p>
                      )}
                    </div>
                  </div>

                  <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
                    <motion.button
                      whileHover={{ scale: 1.02 }}
                      onClick={handleGenerateSummary}
                      disabled={selectedArticles.size === 0}
                      className={`w-full px-4 py-3 rounded-lg font-medium transition-all flex items-center justify-center gap-2 ${
                        selectedArticles.size > 0
                          ? "bg-primary-500 hover:bg-primary-600 text-white"
                          : "bg-gray-200 dark:bg-gray-700 text-gray-400 cursor-not-allowed"
                      }`}
                    >
                      <svg
                        className="w-5 h-5"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                        />
                      </svg>
                      AI 요약 생성하기
                    </motion.button>
                  </div>
                </>
              )}

              {isGeneratingSummary && (
                <div className="py-6 space-y-6">
                  {/* ThinkingProgress 컴포넌트 사용 */}
                  <ThinkingProgress
                    step={streamingStep}
                    progress={streamingProgress}
                    type="thinking"
                    isGenerating={isGeneratingSummary}
                  />

                  {/* 실시간 스트리밍 텍스트 출력 */}
                  {streamingContent && (
                    <div className="space-y-3">
                      <h4 className="font-semibold text-sm text-gray-700 dark:text-gray-300">실시간 생성 내용:</h4>
                      <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg max-h-[400px] overflow-y-auto">
                        <pre className="whitespace-pre-wrap text-sm text-gray-800 dark:text-gray-200 font-mono">
                          {streamingContent}
                          <motion.span
                            animate={{ opacity: [1, 0] }}
                            transition={{ duration: 0.8, repeat: Infinity }}
                            className="inline-block w-2 h-4 bg-primary-500 ml-1"
                          />
                        </pre>
                      </div>
                    </div>
                  )}

                  {/* 기사 참조 정보 (실시간 업데이트) */}
                  {articleReferences.length > 0 && (
                    <div className="space-y-3">
                      <h4 className="font-semibold text-sm text-gray-700 dark:text-gray-300">참조 기사:</h4>
                      <div className="space-y-2 max-h-[200px] overflow-y-auto">
                        {articleReferences.map((ref, index) => (
                          <motion.div
                            key={ref.ref_id}
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: index * 0.1 }}
                            className="p-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-lg"
                          >
                            <div className="flex items-start justify-between">
                              <div className="flex-1">
                                <p className="font-medium text-sm line-clamp-2">
                                  [{ref.ref_id}] {ref.title}
                                </p>
                                <p className="text-xs text-gray-500 mt-1">
                                  {ref.provider} • {ref.byline}
                                </p>
                              </div>
                              {ref.url && (
                                <button
                                  onClick={() => window.open(ref.url, '_blank')}
                                  className="ml-2 p-1 text-primary-500 hover:text-primary-700 transition-colors"
                                  title="기사 원문 보기"
                                >
                                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                                  </svg>
                                </button>
                              )}
                            </div>
                          </motion.div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {summaryResult && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="space-y-6"
                >
                  <div>
                    <h3 className="text-xl font-semibold mb-2">
                      {summaryResult.title}
                    </h3>
                    <p className="text-gray-600 dark:text-gray-400">
                      {summaryResult.summary}
                    </p>
                  </div>

                  {summaryResult.key_points &&
                    summaryResult.key_points.length > 0 && (
                      <div>
                        <h4 className="font-semibold mb-3">핵심 포인트</h4>
                        <ul className="space-y-2">
                          {summaryResult.key_points.map((point, index) => (
                            <li key={index} className="flex items-start">
                              <span className="text-primary-500 mr-2">•</span>
                              <span className="text-gray-700 dark:text-gray-300">
                                {point}
                              </span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                  {summaryResult.key_quotes &&
                    summaryResult.key_quotes.length > 0 && (
                      <div>
                        <h4 className="font-semibold mb-3">주요 인용문</h4>
                        <div className="space-y-3">
                          {summaryResult.key_quotes.map((quote, index) => (
                            <div
                              key={index}
                              className="pl-4 border-l-4 border-primary-500"
                            >
                              <p className="italic text-gray-700 dark:text-gray-300">
                                "{quote.quote}"
                              </p>
                              <p className="text-sm text-gray-500 mt-1">
                                - {quote.source}
                              </p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                  {summaryResult.key_data && summaryResult.key_data.length > 0 && (
                    <div>
                      <h4 className="font-semibold mb-3">주요 수치</h4>
                      <div className="grid grid-cols-1 gap-4">
                        {summaryResult.key_data.map((data, index) => (
                          <div
                            key={index}
                            className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg"
                          >
                            <p className="text-sm text-gray-600 dark:text-gray-400">
                              {data.metric}
                            </p>
                            <p className="text-xl font-bold text-primary-600 dark:text-primary-400">
                              {data.value}
                            </p>
                            <p className="text-xs text-gray-500 mt-1">
                              {data.context}
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* 기사 참조 섹션 */}
                  {summaryResult.article_references && summaryResult.article_references.length > 0 && (
                    <div>
                      <h4 className="font-semibold mb-3">참조 기사</h4>
                      <div className="grid grid-cols-1 gap-3">
                        {summaryResult.article_references.map((ref, index) => (
                          <motion.div
                            key={ref.ref_id}
                            id={`ref-${ref.ref_id}`}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: index * 0.05 }}
                            className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg border border-gray-200 dark:border-gray-600 hover:shadow-md transition-all"
                          >
                            <div className="flex items-start justify-between">
                              <div className="flex-1">
                                <div className="flex items-center gap-2 mb-2">
                                  <span className="text-xs font-mono bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-300 px-2 py-1 rounded">
                                    {ref.ref_id}
                                  </span>
                                  <span className="text-xs text-gray-500">
                                    {ref.provider}
                                  </span>
                                </div>
                                <h5 className="font-medium text-sm line-clamp-2 mb-1">
                                  {ref.title}
                                </h5>
                                <p className="text-xs text-gray-500">
                                  {ref.byline} • {new Date(ref.published_at).toLocaleDateString()}
                                </p>
                              </div>
                              <div className="flex gap-1 ml-3">
                                {ref.url && (
                                  <button
                                    onClick={() => window.open(ref.url, '_blank')}
                                    className="p-2 text-primary-500 hover:text-primary-700 hover:bg-primary-50 dark:hover:bg-primary-900/20 rounded-lg transition-all"
                                    title="기사 원문 보기"
                                  >
                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                                    </svg>
                                  </button>
                                )}
                                <button
                                  onClick={() => window.open(getArticleLink(ref), '_blank')}
                                  className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 dark:hover:bg-gray-600 rounded-lg transition-all"
                                  title="기사 원문 보기"
                                >
                                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                                  </svg>
                                </button>
                              </div>
                            </div>
                          </motion.div>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                    <p className="text-sm text-gray-500">
                      {summaryResult.articles_analyzed}개 기사 분석 완료 ·{" "}
                      {new Date(summaryResult.generated_at).toLocaleString()}
                    </p>
                  </div>
                </motion.div>
              )}
            </div>
          </div>
        </motion.div>
      )}
    </motion.div>
  );
};

export default CategoryDetailPage;