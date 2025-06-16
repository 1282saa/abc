import React, { ButtonHTMLAttributes, forwardRef } from "react";
import { motion, MotionProps } from "framer-motion";

interface AccessibleButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost" | "outline" | "danger";
  size?: "sm" | "md" | "lg";
  isLoading?: boolean;
  loadingText?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  fullWidth?: boolean;
  motionProps?: MotionProps;
}

/**
 * 접근성을 고려한 버튼 컴포넌트
 * - 키보드 네비게이션 지원
 * - 스크린 리더 호환
 * - ARIA 속성 자동 설정
 * - 로딩 상태 관리
 */
const AccessibleButton = forwardRef<HTMLButtonElement, AccessibleButtonProps>(
  (
    {
      variant = "primary",
      size = "md",
      isLoading = false,
      loadingText = "로딩 중...",
      leftIcon,
      rightIcon,
      fullWidth = false,
      children,
      className = "",
      disabled,
      motionProps,
      ...props
    },
    ref
  ) => {
    const baseClasses = "inline-flex items-center justify-center font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed relative overflow-hidden";
    
    const variantClasses = {
      primary: "bg-gradient-to-r from-primary-600 to-primary-700 text-white hover:from-primary-700 hover:to-primary-800 focus:ring-primary-500 shadow-lg hover:shadow-xl",
      secondary: "bg-gradient-to-r from-secondary-500 to-secondary-600 text-white hover:from-secondary-600 hover:to-secondary-700 focus:ring-secondary-500 shadow-lg hover:shadow-xl",
      ghost: "bg-transparent text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-800 focus:ring-gray-500 border border-gray-200 dark:border-gray-700",
      outline: "bg-transparent border-2 border-primary-500 text-primary-600 dark:text-primary-400 hover:bg-primary-50 dark:hover:bg-primary-900/20 focus:ring-primary-500",
      danger: "bg-gradient-to-r from-red-600 to-red-700 text-white hover:from-red-700 hover:to-red-800 focus:ring-red-500 shadow-lg hover:shadow-xl"
    };

    const sizeClasses = {
      sm: "px-3 py-1.5 text-sm rounded-md gap-1.5",
      md: "px-4 py-2 text-sm rounded-lg gap-2",
      lg: "px-6 py-3 text-base rounded-lg gap-2.5"
    };

    const widthClass = fullWidth ? "w-full" : "";
    
    const combinedClasses = [
      baseClasses,
      variantClasses[variant],
      sizeClasses[size],
      widthClass,
      className
    ].filter(Boolean).join(" ");

    const buttonContent = (
      <>
        {/* 로딩 스피너 */}
        {isLoading && (
          <motion.div
            initial={{ opacity: 0, scale: 0 }}
            animate={{ opacity: 1, scale: 1 }}
            className="absolute inset-0 flex items-center justify-center bg-inherit rounded-inherit"
          >
            <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
            <span className="ml-2 sr-only">{loadingText}</span>
          </motion.div>
        )}

        {/* 버튼 내용 */}
        <div className={`flex items-center gap-inherit ${isLoading ? "opacity-0" : ""}`}>
          {leftIcon && <span className="flex-shrink-0">{leftIcon}</span>}
          <span>{children}</span>
          {rightIcon && <span className="flex-shrink-0">{rightIcon}</span>}
        </div>
      </>
    );

    const MotionButton = motion.button;

    return (
      <MotionButton
        ref={ref}
        className={combinedClasses}
        disabled={disabled || isLoading}
        aria-disabled={disabled || isLoading}
        aria-busy={isLoading}
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        transition={{ type: "spring", stiffness: 400, damping: 17 }}
        {...motionProps}
        {...props}
      >
        {buttonContent}
      </MotionButton>
    );
  }
);

AccessibleButton.displayName = "AccessibleButton";

export default AccessibleButton;