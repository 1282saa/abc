import React, { useState, useRef, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  getConciergeBriefing,
  ConciergeBriefingResponse,
  buildSmartContextualQuery,
} from "../../services/briefingApi";
import { getArticleLink } from "../../services/newsApi";
import {
  conversationHistory,
  ChatMessage,
  ConversationSummary,
} from "../../utils/conversationHistory";

// ChatMessage 인터페이스는 conversationHistory에서 import
// (중복 제거)

interface ChatInterfaceProps {
  onClose: () => void;
  sessionId?: string; // 기존 세션을 로드할 때 사용
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ onClose, sessionId: initialSessionId }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(initialSessionId || null);
  const [showHistory, setShowHistory] = useState(false);
  const [conversationSummaries, setConversationSummaries] = useState<ConversationSummary[]>([]);
  const [currentInput, setCurrentInput] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [loadingStep, setLoadingStep] = useState(0);
  const [useContext, setUseContext] = useState(true); // 맥락 사용 여부
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected' | 'reconnecting'>('connected');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const retryTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const isInitialized = useRef(false);

  const loadingMessages = [
    { message: "질문을 분석하고 있습니다...", icon: "🤔" },
    { message: "이전 대화 맥락을 확인하고 있습니다...", icon: "🧠" },
    { message: "관련 기사를 검색하고 있습니다...", icon: "🔍" },
    { message: "검색 결과를 분석하고 있습니다...", icon: "📊" },
    { message: "답변을 준비하고 있습니다...", icon: "✨" },
  ];

  // 메시지 목록 끝으로 스크롤
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // 컴포넌트 초기화 - 기존 세션 로드 또는 새 세션 생성
  useEffect(() => {
    if (isInitialized.current) return;
    isInitialized.current = true;

    if (initialSessionId) {
      // 기존 세션 로드
      const session = conversationHistory.getSession(initialSessionId);
      if (session) {
        setMessages(session.messages);
        setCurrentSessionId(initialSessionId);
        console.log(`🔄 기존 세션 로드됨: ${session.title}`);
        return;
      }
    }

    // 새 세션 시작
    const welcomeMessage: ChatMessage = {
      id: "welcome_" + Date.now(),
      type: "assistant",
      content: "안녕하세요! AI 뉴스 컨시어지입니다. 궁금한 뉴스나 주제에 대해 질문해주세요. 스마트한 맥락 분석으로 더 정확한 답변을 드릴 수 있습니다.",
      timestamp: new Date(),
    };

    const sessionId = conversationHistory.createNewSession(welcomeMessage);
    setCurrentSessionId(sessionId);
    setMessages([welcomeMessage]);
    console.log(`🆕 새 세션 생성됨: ${sessionId}`);
  }, [initialSessionId]);

  // 대화 목록 로드
  const loadConversationSummaries = useCallback(() => {
    const summaries = conversationHistory.getConversationSummaries();
    setConversationSummaries(summaries);
  }, []);

  // 히스토리 토글시 대화 목록 로드
  useEffect(() => {
    if (showHistory) {
      loadConversationSummaries();
    }
  }, [showHistory, loadConversationSummaries]);

  // 컴포넌트 언마운트 시 타이머 정리 및 세션 저장
  useEffect(() => {
    return () => {
      if (retryTimeoutRef.current) {
        clearTimeout(retryTimeoutRef.current);
      }
      // 현재 메시지들을 세션에 저장
      if (currentSessionId && messages.length > 0) {
        conversationHistory.updateSessionMessages(currentSessionId, messages);
      }
    };
  }, [currentSessionId, messages]);

  // 연결 상태 복구 시뮬레이션
  const simulateReconnection = useCallback(() => {
    setConnectionStatus('reconnecting');
    setTimeout(() => {
      setConnectionStatus('connected');
    }, 2000);
  }, []);

  // 메시지 재시도 처리
  const handleRetryMessage = useCallback(async (messageId: string) => {
    const messageToRetry = messages.find(msg => msg.id === messageId.replace('_error', ''));
    if (!messageToRetry?.query) return;

    // 기존 에러 메시지 제거
    setMessages(prev => prev.filter(msg => msg.id !== messageId));
    
    // 재시도 실행
    await executeSearch(messageToRetry.query, messageToRetry.retryCount || 0);
  }, [messages]);

  // 검색 실행 로직 분리
  const executeSearch = useCallback(async (query: string, retryCount: number = 0) => {
    const loadingMessage: ChatMessage = {
      id: Date.now().toString() + "_loading",
      type: "assistant",
      content: "",
      timestamp: new Date(),
      isLoading: true,
    };

    setMessages(prev => [...prev, loadingMessage]);
    setIsProcessing(true);
    setIsTyping(true);
    setLoadingStep(0);

    // 로딩 단계 진행
    const stepInterval = setInterval(() => {
      setLoadingStep((prev) => {
        if (prev < loadingMessages.length - 1) {
          return prev + 1;
        }
        return prev;
      });
    }, 800); // 조금 더 빠른 진행

    try {
      let finalQuery: string;

      if (useContext) {
        // 이전 질문들 추출 (에러 메시지 제외)
        const previousQueries = messages
          .filter((msg) => msg.type === "user" && msg.query && !msg.error)
          .map((msg) => msg.query!)
          .slice(-3); // 최근 3개만

        finalQuery = buildSmartContextualQuery(query, previousQueries);
        console.log("🧠 스마트 맥락 쿼리:", finalQuery);
        console.log("📝 이전 질문들:", previousQueries);
      } else {
        finalQuery = query;
        console.log("🔍 단순 검색:", finalQuery);
      }

      // API 호출 시 타임아웃 처리
      const timeoutPromise = new Promise((_, reject) => {
        retryTimeoutRef.current = setTimeout(() => {
          reject(new Error('요청 시간이 초과되었습니다 (30초)'));
        }, 30000);
      });

      const result = await Promise.race([
        getConciergeBriefing(finalQuery, 1, 20),
        timeoutPromise
      ]) as ConciergeBriefingResponse;

      if (retryTimeoutRef.current) {
        clearTimeout(retryTimeoutRef.current);
        retryTimeoutRef.current = null;
      }

      console.log("✅ 대화형 검색 결과:", result);

      // 로딩 메시지 제거하고 실제 응답 추가
      const assistantMessage: ChatMessage = {
        id: Date.now().toString() + "_response",
        type: "assistant",
        content: result.summary || "검색 결과를 요약했습니다.",
        result: result,
        timestamp: new Date(),
      };

      setMessages((prev) => {
        const withoutLoading = prev.filter((msg) => !msg.isLoading);
        const newMessages = [...withoutLoading, assistantMessage];
        
        // 세션에 메시지 저장
        if (currentSessionId) {
          conversationHistory.addMessageToSession(currentSessionId, assistantMessage);
        }
        
        return newMessages;
      });

      setConnectionStatus('connected');
    } catch (error: any) {
      console.error("❌ 대화형 검색 오류:", error);

      if (retryTimeoutRef.current) {
        clearTimeout(retryTimeoutRef.current);
        retryTimeoutRef.current = null;
      }

      // 네트워크 오류인 경우 연결 상태 업데이트
      if (error.message.includes('네트워크') || error.message.includes('연결')) {
        setConnectionStatus('disconnected');
      }

      // 재시도 로직 (최대 2회)
      const canRetry = retryCount < 2;
      const shouldAutoRetry = error.message.includes('시간이 초과') || error.message.includes('네트워크');

      const errorMessage: ChatMessage = {
        id: Date.now().toString() + "_error",
        type: "assistant",
        content: `검색 중 오류가 발생했습니다: ${error.message}${canRetry ? '\n\n재시도 버튼을 클릭하거나 잠시 후 다시 시도해주세요.' : ''}`,
        timestamp: new Date(),
        error: true,
        retryCount: retryCount + 1,
      };

      setMessages((prev) => {
        const withoutLoading = prev.filter((msg) => !msg.isLoading);
        const newMessages = [...withoutLoading, errorMessage];
        
        // 에러 메시지도 세션에 저장 (디버깅용)
        if (currentSessionId) {
          conversationHistory.addMessageToSession(currentSessionId, errorMessage);
        }
        
        return newMessages;
      });

      // 자동 재시도 (네트워크 오류인 경우)
      if (shouldAutoRetry && canRetry) {
        retryTimeoutRef.current = setTimeout(() => {
          console.log(`🔄 자동 재시도 (${retryCount + 1}회차)`);
          executeSearch(query, retryCount + 1);
        }, 3000);
      }
    } finally {
      clearInterval(stepInterval);
      setIsProcessing(false);
      setIsTyping(false);
      setLoadingStep(0);
    }
  }, [messages, useContext, loadingMessages]);

  // 메시지 전송 처리
  const handleSendMessage = async () => {
    if (!currentInput.trim() || isProcessing) return;

    const query = currentInput.trim();
    
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      type: "user",
      content: query,
      query: query,
      timestamp: new Date(),
    };

    setMessages((prev) => {
      const newMessages = [...prev, userMessage];
      
      // 사용자 메시지를 세션에 저장
      if (currentSessionId) {
        conversationHistory.addMessageToSession(currentSessionId, userMessage);
      }
      
      return newMessages;
    });
    setCurrentInput("");
    
    // 검색 실행
    await executeSearch(query);
  };

  // 기존 대화 로드
  const handleLoadConversation = useCallback((summaryId: string) => {
    const session = conversationHistory.getSession(summaryId);
    if (session) {
      setMessages(session.messages);
      setCurrentSessionId(summaryId);
      setShowHistory(false);
      console.log(`📂 대화 로드됨: ${session.title}`);
    }
  }, []);

  // 대화 삭제
  const handleDeleteConversation = useCallback((summaryId: string) => {
    conversationHistory.deleteSession(summaryId);
    loadConversationSummaries();
    
    // 현재 로드된 대화가 삭제된 경우 새 세션 시작
    if (currentSessionId === summaryId) {
      handleNewTopic();
    }
  }, [currentSessionId, loadConversationSummaries]);

  // 새 주제 시작
  const handleNewTopic = useCallback(() => {
    // 진행 중인 요청이 있으면 취소
    if (retryTimeoutRef.current) {
      clearTimeout(retryTimeoutRef.current);
      retryTimeoutRef.current = null;
    }
    
    setIsProcessing(false);
    setIsTyping(false);
    setLoadingStep(0);
    setConnectionStatus('connected');
    setShowHistory(false);
    
    const welcomeMessage: ChatMessage = {
      id: "new_topic_" + Date.now(),
      type: "assistant",
      content: "새로운 주제로 대화를 시작합니다. 무엇을 도와드릴까요?",
      timestamp: new Date(),
    };
    
    // 새 세션 생성
    const newSessionId = conversationHistory.createNewSession(welcomeMessage);
    setCurrentSessionId(newSessionId);
    setMessages([welcomeMessage]);
    
    console.log(`🆕 새 주제 세션 생성됨: ${newSessionId}`);
  }, []);

  // Enter 키 처리
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // 기사 카드 컴포넌트
  const ArticleCard: React.FC<{ article: any }> = ({ article }) => {
    return (
      <motion.a
        href={getArticleLink(article)}
        target="_blank"
        rel="noopener noreferrer"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        whileHover={{ y: -2 }}
        className="block bg-gray-50 dark:bg-gray-700 rounded-lg p-4 border border-gray-200 dark:border-gray-600 hover:shadow-md transition-all duration-200 mb-3"
      >
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center space-x-2">
            <span className="text-xs font-medium text-primary-600 dark:text-primary-400 bg-primary-50 dark:bg-primary-900/30 px-2 py-1 rounded border border-primary-200 dark:border-primary-800">
              {article.provider}
            </span>
            {article.byline && (
              <span className="text-xs text-gray-600 dark:text-gray-400 font-medium">
                {article.byline}
              </span>
            )}
          </div>
          <div className="text-right">
            <time className="text-xs text-gray-700 dark:text-gray-300 font-semibold block">
              {new Date(article.published_at).toLocaleDateString("ko-KR", {
                year: "numeric",
                month: "long",
                day: "numeric",
              })}
            </time>
            <time className="text-xs text-gray-500 dark:text-gray-400 block">
              {new Date(article.published_at).toLocaleTimeString("ko-KR", {
                hour: "2-digit",
                minute: "2-digit",
              })}
            </time>
            {article.enveloped_at && (
              <time className="text-xs text-gray-400 dark:text-gray-500 block mt-1">
                수집:{" "}
                {new Date(article.enveloped_at).toLocaleDateString("ko-KR", {
                  month: "short",
                  day: "numeric",
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </time>
            )}
          </div>
        </div>
        <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-2 line-clamp-2">
          {article.title}
        </h4>

        {/* 하이라이트된 내용 우선 표시 */}
        <div className="text-xs text-gray-600 dark:text-gray-400 line-clamp-3 leading-relaxed">
          {article.hilight ? (
            <span
              dangerouslySetInnerHTML={{
                __html: article.hilight
                  .replace(
                    /<em>/g,
                    '<mark class="bg-yellow-200 dark:bg-yellow-800">'
                  )
                  .replace(/<\/em>/g, "</mark>"),
              }}
            />
          ) : (
            <span>{article.content.substring(0, 150)}...</span>
          )}
        </div>

        {article.category && (
          <div className="mt-3">
            <span className="text-xs bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-300 px-2 py-1 rounded">
              {article.category}
            </span>
          </div>
        )}
      </motion.a>
    );
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
    >
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-4xl h-[80vh] flex flex-col">
        {/* 헤더 */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center">
            <div className="relative w-10 h-10 bg-gradient-to-r from-primary-500 to-secondary-500 rounded-full flex items-center justify-center mr-3">
              <span className="text-white text-lg">🤖</span>
              {/* 연결 상태 표시 */}
              <div className={`absolute -top-1 -right-1 w-3 h-3 rounded-full border-2 border-white ${
                connectionStatus === 'connected' ? 'bg-green-500' :
                connectionStatus === 'reconnecting' ? 'bg-yellow-500 animate-pulse' :
                'bg-red-500'
              }`} />
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                AI 뉴스 컨시어지 대화
              </h2>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {connectionStatus === 'connected' && '스마트한 맥락 분석으로 더 정확한 정보를 찾아보세요'}
                {connectionStatus === 'disconnected' && '⚠️ 연결이 끊어졌습니다. 재시도해주세요.'}
                {connectionStatus === 'reconnecting' && '🔄 연결을 다시 시도하고 있습니다...'}
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            {/* 맥락 사용 토글 */}
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-600 dark:text-gray-400">
                맥락
              </span>
              <button
                onClick={() => setUseContext(!useContext)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  useContext ? "bg-primary-500" : "bg-gray-300 dark:bg-gray-600"
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    useContext ? "translate-x-6" : "translate-x-1"
                  }`}
                />
              </button>
            </div>

            {/* 대화 히스토리 버튼 */}
            <button
              onClick={() => setShowHistory(!showHistory)}
              className="px-3 py-1 text-sm bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors mr-2"
              title="대화 히스토리"
            >
              📚 히스토리
            </button>

            {/* 연결 복구 버튼 */}
            {connectionStatus === 'disconnected' && (
              <button
                onClick={simulateReconnection}
                className="px-3 py-1 text-sm bg-yellow-500 hover:bg-yellow-600 text-white rounded-lg transition-colors mr-2"
                title="연결 다시 시도"
              >
                🔄 재연결
              </button>
            )}
            
            {/* 새 주제 버튼 */}
            <button
              onClick={handleNewTopic}
              disabled={isProcessing}
              className="px-3 py-1 text-sm bg-purple-500 hover:bg-purple-600 disabled:bg-purple-300 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
              title="새로운 주제로 대화 시작"
            >
              🆕 새 주제
            </button>

            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
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
        </div>

        {/* 대화 히스토리 사이드바 */}
        <AnimatePresence>
          {showHistory && (
            <motion.div
              initial={{ x: "100%" }}
              animate={{ x: 0 }}
              exit={{ x: "100%" }}
              className="absolute top-0 right-0 w-80 h-full bg-white dark:bg-gray-800 border-l border-gray-200 dark:border-gray-700 shadow-lg z-10"
            >
              <div className="p-4 border-b border-gray-200 dark:border-gray-700">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                    📚 대화 히스토리
                  </h3>
                  <button
                    onClick={() => setShowHistory(false)}
                    className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                  >
                    ✕
                  </button>
                </div>
              </div>
              <div className="flex-1 overflow-y-auto p-4">
                {conversationSummaries.length === 0 ? (
                  <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-8">
                    저장된 대화가 없습니다.
                  </p>
                ) : (
                  <div className="space-y-2">
                    {conversationSummaries.map((summary) => (
                      <div
                        key={summary.id}
                        className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                          summary.id === currentSessionId
                            ? 'bg-primary-50 dark:bg-primary-900/20 border-primary-200 dark:border-primary-800'
                            : 'bg-gray-50 dark:bg-gray-700 border-gray-200 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-600'
                        }`}
                        onClick={() => handleLoadConversation(summary.id)}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1 min-w-0">
                            <h4 className="text-sm font-medium text-gray-900 dark:text-white truncate">
                              {summary.title}
                            </h4>
                            <p className="text-xs text-gray-600 dark:text-gray-400 mt-1 line-clamp-2">
                              {summary.preview}
                            </p>
                            <div className="flex items-center justify-between mt-2">
                              <span className="text-xs text-gray-500 dark:text-gray-400">
                                {summary.messageCount}개 메시지
                              </span>
                              <span className="text-xs text-gray-500 dark:text-gray-400">
                                {summary.lastUpdated.toLocaleDateString('ko-KR')}
                              </span>
                            </div>
                          </div>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDeleteConversation(summary.id);
                            }}
                            className="ml-2 text-red-400 hover:text-red-600 text-xs"
                            title="삭제"
                          >
                            🗑️
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* 메시지 영역 */}
        <div className={`flex-1 overflow-y-auto p-6 space-y-4 transition-all duration-300 ${
          showHistory ? 'mr-80' : ''
        }`}>
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${
                message.type === "user" ? "justify-end" : "justify-start"
              }`}
            >
              <div
                className={`max-w-[70%] rounded-2xl p-4 ${
                  message.type === "user"
                    ? "bg-primary-500 text-white ml-4"
                    : "bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white mr-4"
                }`}
              >
                {message.isLoading ? (
                  <div className="flex items-center space-x-3">
                    <div className="relative">
                      <div className="w-6 h-6 border-2 border-primary-200 border-t-primary-600 rounded-full animate-spin"></div>
                      {isTyping && (
                        <div className="absolute -top-1 -right-1 w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                      )}
                    </div>
                    <div>
                      <p className="text-sm font-medium">
                        {loadingMessages[loadingStep]?.icon}{" "}
                        {loadingMessages[loadingStep]?.message}
                      </p>
                      <div className="flex space-x-1 mt-2">
                        {loadingMessages.map((_, index) => (
                          <div
                            key={index}
                            className={`w-1.5 h-1.5 rounded-full transition-all duration-300 ${
                              index <= loadingStep
                                ? "bg-primary-500"
                                : "bg-gray-300 dark:bg-gray-600"
                            }`}
                          />
                        ))}
                      </div>
                      {connectionStatus === 'reconnecting' && (
                        <p className="text-xs text-yellow-600 dark:text-yellow-400 mt-1">
                          🔄 연결을 재시도하고 있습니다...
                        </p>
                      )}
                    </div>
                  </div>
                ) : (
                  <>
                    {message.error ? (
                      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3">
                        <div className="flex items-start space-x-2">
                          <span className="text-red-500 text-lg">⚠️</span>
                          <div className="flex-1">
                            <p className="text-sm leading-relaxed whitespace-pre-wrap text-red-700 dark:text-red-300">
                              {message.content}
                            </p>
                            {message.retryCount && message.retryCount < 3 && (
                              <button
                                onClick={() => handleRetryMessage(message.id)}
                                className="mt-2 px-3 py-1 bg-red-100 hover:bg-red-200 dark:bg-red-800 dark:hover:bg-red-700 text-red-700 dark:text-red-300 text-xs rounded transition-colors"
                              >
                                🔄 다시 시도
                              </button>
                            )}
                          </div>
                        </div>
                      </div>
                    ) : (
                      <p className="text-sm leading-relaxed whitespace-pre-wrap">
                        {message.content}
                      </p>
                    )}

                    {/* 검색 결과가 있는 경우 관련 기사 표시 */}
                    {message.result &&
                      message.result.documents &&
                      message.result.documents.length > 0 && (
                        <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-600">
                          <h4 className="text-sm font-semibold mb-3 text-gray-700 dark:text-gray-300">
                            관련 기사 ({message.result.documents.length}개)
                          </h4>
                          <div className="space-y-2 max-h-60 overflow-y-auto">
                            {message.result.documents
                              .slice(0, 5)
                              .map((article: any, index: number) => (
                                <ArticleCard key={index} article={article} />
                              ))}
                          </div>
                          {message.result.documents.length > 5 && (
                            <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                              +{message.result.documents.length - 5}개 더
                              있습니다
                            </p>
                          )}
                        </div>
                      )}

                    {/* 키워드 표시 */}
                    {message.result &&
                      message.result.keywords &&
                      message.result.keywords.length > 0 && (
                        <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-600">
                          <h4 className="text-xs font-semibold mb-2 text-gray-700 dark:text-gray-300">
                            주요 키워드
                          </h4>
                          <div className="flex flex-wrap gap-1">
                            {message.result.keywords
                              .slice(0, 5)
                              .map((keyword: any, index: number) => (
                                <button
                                  key={index}
                                  onClick={() => {
                                    if (!isProcessing) {
                                      setCurrentInput(keyword.keyword);
                                    }
                                  }}
                                  disabled={isProcessing}
                                  className="text-xs bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 px-2 py-1 rounded-full hover:bg-blue-200 dark:hover:bg-blue-800/40 transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                  {keyword.keyword}
                                </button>
                              ))}
                          </div>
                        </div>
                      )}
                  </>
                )}

                <div className="text-xs opacity-70 mt-2">
                  {message.timestamp.toLocaleTimeString("ko-KR", {
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </div>
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* 입력 영역 */}
        <div className="p-6 border-t border-gray-200 dark:border-gray-700">
          <div className="flex space-x-4">
            <div className="flex-1 relative">
              <textarea
                value={currentInput}
                onChange={(e) => setCurrentInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="궁금한 점을 질문해보세요... (Shift+Enter로 줄바꿈)"
                className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400"
                rows={2}
                disabled={isProcessing}
              />
            </div>
            <button
              onClick={handleSendMessage}
              disabled={!currentInput.trim() || isProcessing}
              className="px-6 py-3 bg-gradient-to-r from-primary-500 to-secondary-500 text-white rounded-xl hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center justify-center min-w-[80px]"
            >
              {isProcessing ? (
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              ) : (
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
                    d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                  />
                </svg>
              )}
            </button>
          </div>

          <div className="flex items-center justify-between mt-3 text-xs text-gray-500 dark:text-gray-400">
            <div className="flex items-center space-x-4">
              <span className={connectionStatus !== 'connected' ? 'text-yellow-600 dark:text-yellow-400' : ''}>
                {connectionStatus === 'connected' ? 
                  (useContext ? "스마트 맥락 분석 활성화" : "단순 검색 모드") :
                  `연결 상태: ${connectionStatus === 'disconnected' ? '끊어짐' : '재연결 중'}`
                }
              </span>
              <span>
                {messages.filter((m) => m.type === "user" && !m.error).length}개 질문
              </span>
              {isTyping && (
                <span className="flex items-center space-x-1 text-primary-500">
                  <span className="animate-pulse">💬</span>
                  <span>AI가 응답 중...</span>
                </span>
              )}
            </div>
            <span className={connectionStatus === 'connected' ? '' : 'text-yellow-600 dark:text-yellow-400'}>
              {connectionStatus === 'connected' ? 
                '맥락을 끄고 새로운 주제로 검색해보세요' :
                '연결이 복구되면 다시 시도할 수 있습니다'
              }
            </span>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

export default ChatInterface;
