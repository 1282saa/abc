import React from "react";
import { Link, useLocation } from "react-router-dom";

interface HeaderProps {
  theme: "light" | "dark";
  toggleTheme: () => void;
}

/**
 * 상단 네비게이션 헤더 컴포넌트
 */
const Header: React.FC<HeaderProps> = ({ theme, toggleTheme }) => {
  const location = useLocation();

  // 현재 경로에 따라 네비게이션 링크 활성화
  const isActive = (path: string): string => {
    return location.pathname === path
      ? "text-primary-600 dark:text-primary-400 font-medium"
      : "text-gray-700 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400";
  };

  return (
    <header className="bg-white dark:bg-gray-800 shadow-md">
      <div className="container mx-auto px-4 max-w-7xl">
        <div className="flex items-center justify-between h-16">
          {/* 로고 영역 */}
          <div className="flex items-center">
            <Link to="/" className="flex items-center">
              <span className="text-2xl font-bold text-primary-600 dark:text-primary-400">
                AI NOVA
              </span>
              <span className="ml-2 text-sm font-medium text-gray-500 dark:text-gray-400">
                뉴스 AI 서비스
              </span>
            </Link>
          </div>

          {/* 네비게이션 링크 */}
          <nav className="flex space-x-6 ml-10">
            <Link to="/" className={`${isActive("/")} transition-colors`}>
              홈
            </Link>
            <Link to="/qa" className={`${isActive("/qa")} transition-colors`}>
              뉴스 Q&A
            </Link>
            <Link
              to="/summary"
              className={`${isActive("/summary")} transition-colors`}
            >
              뉴스 요약
            </Link>
            <Link
              to="/timeline"
              className={`${isActive("/timeline")} transition-colors`}
            >
              뉴스 타임라인
            </Link>
            <Link
              to="/stock-calendar"
              className={`${isActive("/stock-calendar")} transition-colors`}
            >
              주식 캘린더
            </Link>
          </nav>

          {/* 다크모드 토글 버튼 */}
          <div>
            <button
              onClick={toggleTheme}
              className="p-2 rounded-full focus:outline-none focus:ring-2 focus:ring-primary-500"
              aria-label={`${
                theme === "dark" ? "라이트 모드로 전환" : "다크 모드로 전환"
              }`}
            >
              {theme === "dark" ? (
                <svg
                  className="w-6 h-6 text-yellow-300"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"
                  ></path>
                </svg>
              ) : (
                <svg
                  className="w-6 h-6 text-gray-700"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"
                  ></path>
                </svg>
              )}
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
