import React from "react";
import { motion } from "framer-motion";

interface LoadingSpinnerProps {
  size?: "small" | "medium" | "large";
  text?: string;
  variant?: "default" | "pulse" | "dots" | "skeleton";
}

/**
 * 현대적이고 향상된 로딩 상태를 표시하는 스피너 컴포넌트
 */
const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = "medium",
  text = "로딩 중...",
  variant = "default",
}) => {
  const sizeClasses = {
    small: "w-4 h-4",
    medium: "w-8 h-8",
    large: "w-12 h-12",
  };

  const textSizeClasses = {
    small: "text-xs",
    medium: "text-sm",
    large: "text-base",
  };

  if (variant === "pulse") {
    return (
      <div className="flex items-center justify-center p-4">
        <div className="flex flex-col items-center space-y-3">
          <motion.div
            animate={{
              scale: [1, 1.2, 1],
              opacity: [0.7, 1, 0.7],
            }}
            transition={{
              duration: 1.5,
              repeat: Infinity,
              ease: "easeInOut",
            }}
            className={`${sizeClasses[size]} bg-gradient-to-r from-primary-500 to-secondary-500 rounded-full`}
          />
          {text && (
            <motion.span
              animate={{ opacity: [0.5, 1, 0.5] }}
              transition={{ duration: 2, repeat: Infinity }}
              className={`${textSizeClasses[size]} text-gray-600 dark:text-gray-400 font-medium`}
            >
              {text}
            </motion.span>
          )}
        </div>
      </div>
    );
  }

  if (variant === "dots") {
    return (
      <div className="flex items-center justify-center p-4">
        <div className="flex flex-col items-center space-y-4">
          <div className="flex space-x-2">
            {[0, 1, 2].map((index) => (
              <motion.div
                key={index}
                animate={{
                  y: [-8, 8, -8],
                }}
                transition={{
                  duration: 1.2,
                  repeat: Infinity,
                  delay: index * 0.2,
                  ease: "easeInOut",
                }}
                className="w-3 h-3 bg-gradient-to-r from-primary-500 to-secondary-500 rounded-full"
              />
            ))}
          </div>
          {text && (
            <span className={`${textSizeClasses[size]} text-gray-600 dark:text-gray-400 font-medium`}>
              {text}
            </span>
          )}
        </div>
      </div>
    );
  }

  if (variant === "skeleton") {
    return (
      <div className="animate-pulse p-4 space-y-4">
        <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded-full w-3/4"></div>
        <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded-full w-1/2"></div>
        <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded-full w-5/6"></div>
      </div>
    );
  }

  // Default variant with enhanced design
  return (
    <div className="flex items-center justify-center p-4">
      <div className="flex flex-col items-center space-y-3">
        <div className="relative">
          {/* 외부 링 */}
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
            className={`${sizeClasses[size]} border-2 border-transparent rounded-full`}
            style={{
              background: "linear-gradient(45deg, #3B82F6, #8B5CF6, #EC4899)",
              backgroundSize: "200% 200%",
            }}
          >
            <motion.div
              animate={{ backgroundPosition: ["0% 0%", "100% 100%"] }}
              transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
              className="w-full h-full rounded-full bg-gradient-to-r from-primary-500 via-secondary-500 to-primary-500"
            />
          </motion.div>
          
          {/* 내부 원 */}
          <div className={`absolute inset-1 bg-white dark:bg-gray-900 rounded-full ${sizeClasses[size]}`} />
          
          {/* 중앙 아이콘 */}
          <div className="absolute inset-0 flex items-center justify-center">
            <motion.div
              animate={{ rotate: -360 }}
              transition={{ duration: 1.5, repeat: Infinity, ease: "linear" }}
              className="w-3 h-3 bg-gradient-to-r from-primary-500 to-secondary-500 rounded-full"
            />
          </div>
        </div>
        
        {text && (
          <motion.span
            animate={{ opacity: [0.6, 1, 0.6] }}
            transition={{ duration: 2, repeat: Infinity }}
            className={`${textSizeClasses[size]} text-gray-600 dark:text-gray-400 font-medium tracking-wide`}
          >
            {text}
          </motion.span>
        )}
      </div>
    </div>
  );
};

export default LoadingSpinner;
