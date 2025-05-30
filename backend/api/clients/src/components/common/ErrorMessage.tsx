import React from "react";

interface ErrorMessageProps {
  message: string | null;
}

/**
 * 에러 메시지를 표시하는 공통 컴포넌트
 */
const ErrorMessage: React.FC<ErrorMessageProps> = ({ message }) => {
  if (!message) return null;

  return (
    <div className="card bg-red-50 dark:bg-red-900/20 text-red-800 dark:text-red-200 mb-4">
      <p>{message}</p>
    </div>
  );
};

export default ErrorMessage;
