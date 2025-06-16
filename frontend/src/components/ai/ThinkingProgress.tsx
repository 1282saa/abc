import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  MagnifyingGlassIcon,
  DocumentTextIcon,
  CpuChipIcon,
  PencilSquareIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
} from "@heroicons/react/24/outline";

interface ThinkingProgressProps {
  step: string;
  progress: number;
  type?: "thinking" | "content" | "complete" | "error";
  isGenerating: boolean;
}

interface ThinkingStep {
  id: string;
  message: string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
  status: "thinking" | "completed" | "current" | "pending";
  emotion?: string;
}

// ChatGPT 스타일의 사고 과정 메시지들
const getThinkingMessage = (step: string): { message: string; emotion: string } => {
  const messages = [
    {
      keywords: ["뉴스", "데이터", "수집"],
      message: "관련 뉴스 기사들을 찾고 있어요...",
      emotion: "🔍"
    },
    {
      keywords: ["발견", "개", "기사"],
      message: "좋은 자료들을 발견했네요! 분석해보겠습니다.",
      emotion: "😊"
    },
    {
      keywords: ["분석", "중요", "정보", "추출"],
      message: "각 기사의 핵심 내용을 파악하고 있어요...",
      emotion: "🧠"
    },
    {
      keywords: ["AI", "종합", "인사이트", "도출"],
      message: "모든 정보를 종합해서 의미있는 패턴을 찾고 있어요...",
      emotion: "🤖"
    },
    {
      keywords: ["레포트", "작성"],
      message: "분석 결과를 정리해서 레포트로 만들고 있어요...",
      emotion: "📝"
    },
    {
      keywords: ["완성", "완료"],
      message: "모든 작업이 완료되었어요! 결과를 확인해보세요.",
      emotion: "✨"
    }
  ];

  for (const msg of messages) {
    if (msg.keywords.some(keyword => step.includes(keyword))) {
      return { message: msg.message, emotion: msg.emotion };
    }
  }

  return { message: step, emotion: "⚡" };
};

const ThinkingProgress: React.FC<ThinkingProgressProps> = ({
  step,
  progress,
  type = "thinking",
  isGenerating,
}) => {
  const [currentMessage, setCurrentMessage] = useState("");
  const [dots, setDots] = useState("");
  const [emotion, setEmotion] = useState("🤔");

  // 점점 추가되는 애니메이션 효과
  useEffect(() => {
    if (!isGenerating) return;

    const interval = setInterval(() => {
      setDots(prev => {
        if (prev.length >= 3) return "";
        return prev + ".";
      });
    }, 500);

    return () => clearInterval(interval);
  }, [isGenerating]);

  // 메시지 업데이트
  useEffect(() => {
    const { message, emotion: newEmotion } = getThinkingMessage(step);
    setCurrentMessage(message);
    setEmotion(newEmotion);
  }, [step]);

  const getStepIcon = () => {
    if (type === "complete") return CheckCircleIcon;
    if (type === "error") return ExclamationTriangleIcon;
    
    if (step.includes("뉴스") || step.includes("수집")) return MagnifyingGlassIcon;
    if (step.includes("분석") || step.includes("추출")) return DocumentTextIcon;
    if (step.includes("AI") || step.includes("종합")) return CpuChipIcon;
    if (step.includes("레포트") || step.includes("작성")) return PencilSquareIcon;
    
    return CpuChipIcon;
  };

  const getStatusColor = () => {
    if (type === "complete") return "text-green-500";
    if (type === "error") return "text-red-500";
    return "text-blue-500";
  };

  const IconComponent = getStepIcon();

  return (
    <div className="w-full max-w-2xl mx-auto">
      {/* 진행률 바 */}
      <div className="mb-6">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
            분석 진행률
          </span>
          <span className="text-sm font-bold text-blue-600 dark:text-blue-400">
            {progress}%
          </span>
        </div>
        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3 overflow-hidden">
          <motion.div
            className="h-full bg-gradient-to-r from-blue-500 via-purple-500 to-indigo-500"
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.5, ease: "easeOut" }}
          />
        </div>
      </div>

      {/* ChatGPT 스타일 메시지 */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg border border-gray-200 dark:border-gray-700 p-6"
      >
        <div className="flex items-start gap-4">
          {/* 아이콘 */}
          <motion.div
            className={`flex-shrink-0 w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center ${getStatusColor()}`}
            animate={{ 
              scale: isGenerating ? [1, 1.1, 1] : 1,
              rotate: isGenerating ? [0, 360] : 0 
            }}
            transition={{ 
              scale: { duration: 2, repeat: Infinity, ease: "easeInOut" },
              rotate: { duration: 3, repeat: Infinity, ease: "linear" }
            }}
          >
            <IconComponent className="w-5 h-5 text-white" />
          </motion.div>

          {/* 메시지 영역 */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2">
              <h3 className="font-semibold text-gray-900 dark:text-white">
                AI 어시스턴트
              </h3>
              {isGenerating && (
                <div className="flex items-center gap-1">
                  <motion.div
                    className="w-2 h-2 bg-green-500 rounded-full"
                    animate={{ scale: [1, 1.2, 1] }}
                    transition={{ duration: 1, repeat: Infinity }}
                  />
                  <span className="text-xs text-green-600 dark:text-green-400 font-medium">
                    작업 중
                  </span>
                </div>
              )}
            </div>

            {/* 사고 과정 메시지 */}
            <div className="flex items-start gap-3">
              <span className="text-2xl flex-shrink-0 mt-1">{emotion}</span>
              <div>
                <motion.p
                  key={currentMessage}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="text-gray-700 dark:text-gray-300 leading-relaxed"
                >
                  {currentMessage}
                  {isGenerating && type === "thinking" && (
                    <motion.span
                      className="text-blue-500 font-bold"
                      animate={{ opacity: [1, 0] }}
                      transition={{ duration: 1, repeat: Infinity }}
                    >
                      {dots}
                    </motion.span>
                  )}
                </motion.p>

                {/* 상세 원본 메시지 (작은 글씨) */}
                {currentMessage !== step && (
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 italic">
                    {step}
                  </p>
                )}
              </div>
            </div>

            {/* 진행 상태 표시 */}
            {isGenerating && (
              <div className="mt-4 flex items-center gap-2">
                <div className="flex gap-1">
                  {[0, 1, 2].map(i => (
                    <motion.div
                      key={i}
                      className="w-2 h-2 bg-blue-500 rounded-full"
                      animate={{
                        y: [0, -8, 0],
                        opacity: [0.3, 1, 0.3]
                      }}
                      transition={{
                        duration: 1,
                        repeat: Infinity,
                        delay: i * 0.2
                      }}
                    />
                  ))}
                </div>
                <span className="text-xs text-gray-500 dark:text-gray-400">
                  분석 중...
                </span>
              </div>
            )}
          </div>
        </div>

        {/* 완료/오류 상태 */}
        {type === "complete" && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="mt-4 p-3 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800"
          >
            <div className="flex items-center gap-2">
              <CheckCircleIcon className="w-5 h-5 text-green-600 dark:text-green-400" />
              <span className="text-green-800 dark:text-green-300 font-medium">
                분석이 완료되었습니다!
              </span>
            </div>
          </motion.div>
        )}

        {type === "error" && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="mt-4 p-3 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800"
          >
            <div className="flex items-center gap-2">
              <ExclamationTriangleIcon className="w-5 h-5 text-red-600 dark:text-red-400" />
              <span className="text-red-800 dark:text-red-300 font-medium">
                분석 중 오류가 발생했습니다.
              </span>
            </div>
          </motion.div>
        )}
      </motion.div>

      {/* 추가 정보 */}
      {isGenerating && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1 }}
          className="mt-4 text-center"
        >
          <p className="text-xs text-gray-500 dark:text-gray-400">
            💡 고품질 분석을 위해 여러 단계를 거쳐 진행됩니다
          </p>
        </motion.div>
      )}
    </div>
  );
};

export default ThinkingProgress;