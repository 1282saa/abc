import React from "react";
import { Link, useLocation } from "react-router-dom";
import { motion } from "framer-motion";

interface HeaderProps {
  theme: "light" | "dark";
  toggleTheme: () => void;
}

/**
 * 현대적인 상단 네비게이션 헤더 컴포넌트
 */
const Header: React.FC<HeaderProps> = ({ theme, toggleTheme }) => {
  const location = useLocation();

  // 현재 경로에 따라 네비게이션 링크 활성화
  const isActive = (path: string): boolean => {
    return location.pathname === path;
  };

  const navItems = [
    { path: "/", label: "홈", icon: "🏠" },
    { path: "/watchlist", label: "관심 종목", icon: "📊" },
    { path: "/stock-calendar", label: "투자 캘린더", icon: "📅" },
  ];

  return (
    <motion.header
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ type: "spring", stiffness: 300, damping: 30 }}
      className="sticky top-0 z-50 bg-white/80 dark:bg-gray-900/80 backdrop-blur-lg border-b border-gray-200/50 dark:border-gray-700/50"
    >
      <div className="container mx-auto px-4 max-w-7xl">
        <div className="flex items-center justify-between h-16">
          {/* 로고 영역 */}
          <motion.div
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="flex items-center"
          >
            <Link to="/" className="flex items-center group">
              <div className="relative">
                <motion.div
                  animate={{
                    rotate: [0, 360],
                  }}
                  transition={{
                    duration: 20,
                    repeat: Infinity,
                    ease: "linear",
                  }}
                  className="w-8 h-8 bg-gradient-to-r from-primary-500 to-secondary-500 rounded-lg flex items-center justify-center text-white font-bold text-sm mr-3"
                >
                  AI
                </motion.div>
              </div>
              <div>
                <span className="text-xl font-bold bg-gradient-to-r from-primary-600 to-secondary-600 dark:from-primary-400 dark:to-secondary-400 bg-clip-text text-transparent">
                  NOVA
                </span>
                <div className="text-xs text-gray-500 dark:text-gray-400 font-medium">
                  뉴스 AI 서비스
                </div>
              </div>
            </Link>
          </motion.div>

          {/* 네비게이션 링크 */}
          <nav className="hidden md:flex items-center space-x-2">
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className="relative group"
              >
                <motion.div
                  whileHover={{ y: -2 }}
                  whileTap={{ y: 0 }}
                  className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-all duration-200 ${
                    isActive(item.path)
                      ? "bg-primary-50 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400"
                      : "text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 hover:text-primary-600 dark:hover:text-primary-400"
                  }`}
                >
                  <span className="text-sm">{item.icon}</span>
                  <span className="font-medium text-sm">{item.label}</span>
                </motion.div>
                
                {isActive(item.path) && (
                  <motion.div
                    layoutId="activeNav"
                    className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-primary-500 to-secondary-500 rounded-full"
                    transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
                  />
                )}
              </Link>
            ))}
          </nav>

          {/* 모바일 메뉴 버튼 & 다크모드 토글 */}
          <div className="flex items-center space-x-2">
            {/* 다크모드 토글 버튼 */}
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={toggleTheme}
              className="relative p-2 rounded-lg bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500"
              aria-label={`${
                theme === "dark" ? "라이트 모드로 전환" : "다크 모드로 전환"
              }`}
            >
              <motion.div
                initial={false}
                animate={{
                  scale: theme === "dark" ? 0 : 1,
                  rotate: theme === "dark" ? -90 : 0,
                }}
                transition={{ duration: 0.3 }}
                className="absolute inset-0 p-2"
              >
                <svg
                  className="w-5 h-5 text-gray-700"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"
                  />
                </svg>
              </motion.div>
              
              <motion.div
                initial={false}
                animate={{
                  scale: theme === "dark" ? 1 : 0,
                  rotate: theme === "dark" ? 0 : 90,
                }}
                transition={{ duration: 0.3 }}
                className="p-2"
              >
                <svg
                  className="w-5 h-5 text-yellow-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"
                  />
                </svg>
              </motion.div>
            </motion.button>

            {/* 모바일 메뉴 버튼 */}
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="md:hidden p-2 rounded-lg bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
            >
              <svg className="w-5 h-5 text-gray-700 dark:text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </motion.button>
          </div>
        </div>
      </div>

      {/* 모바일 네비게이션 메뉴 - 추후 구현 */}
      {/* Mobile navigation menu can be added here */}
    </motion.header>
  );
};

export default Header;
