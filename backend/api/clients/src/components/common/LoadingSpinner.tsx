import React from "react";

interface LoadingSpinnerProps {
  size?: "small" | "medium" | "large";
  text?: string;
}

/**
 * 로딩 상태를 표시하는 스피너 컴포넌트
 */
const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = "medium",
  text = "로딩 중...",
}) => {
  const sizeClasses = {
    small: "w-4 h-4",
    medium: "w-6 h-6",
    large: "w-10 h-10",
  };

  return (
    <div className="flex items-center justify-center p-4">
      <div className="flex flex-col items-center">
        <svg
          className={`${sizeClasses[size]} animate-spin text-primary-600 dark:text-primary-400`}
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          ></circle>
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          ></path>
        </svg>
        {text && (
          <span className="mt-2 text-gray-600 dark:text-gray-400">{text}</span>
        )}
      </div>
    </div>
  );
};

export default LoadingSpinner;
