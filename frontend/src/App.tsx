import React, { useState, useEffect } from "react";
import { Routes, Route } from "react-router-dom";
import Layout from "./components/layout/Layout";

// 페이지 컴포넌트들
import HomePage from "./pages/HomePage";
import StockCalendarPage from "./pages/StockCalendarPage";
import WatchlistPage from "./pages/WatchlistPage";
import CategoryDetailPage from "./pages/CategoryDetailPage";
import ReportPage from "./pages/ReportPage";
import NotFoundPage from "./pages/NotFoundPage";
import SearchPage from "./pages/SearchPage";
import NewsDetailPage from "./pages/NewsDetailPage";
import ReportGenerationPage from "./pages/ReportGenerationPage";
import PeriodReportGenerationPage from "./pages/PeriodReportGenerationPage";

// 다크모드 설정
type Theme = "light" | "dark";

const App: React.FC = () => {
  // 다크모드 상태 관리
  const [theme, setTheme] = useState<Theme>(() => {
    // 로컬 스토리지에서 테마 설정 불러오기
    const savedTheme = localStorage.getItem("theme") as Theme | null;
    // 사용자 시스템 설정 확인
    const prefersDark = window.matchMedia(
      "(prefers-color-scheme: dark)"
    ).matches;

    return savedTheme || (prefersDark ? "dark" : "light");
  });

  // 테마 변경 함수
  const toggleTheme = () => {
    const newTheme = theme === "light" ? "dark" : "light";
    setTheme(newTheme);
    localStorage.setItem("theme", newTheme);
  };

  // 테마 변경 시 문서 클래스 업데이트
  useEffect(() => {
    if (theme === "dark") {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  }, [theme]);

  return (
    <Layout theme={theme} toggleTheme={toggleTheme}>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/watchlist" element={<WatchlistPage />} />
        <Route path="/category/:categoryKey" element={<CategoryDetailPage />} />
        <Route path="/stock-calendar" element={<StockCalendarPage />} />
        <Route path="/report" element={<ReportPage />} />
        <Route path="/reports/generate" element={<ReportGenerationPage />} />
        <Route path="/reports/period-generate" element={<PeriodReportGenerationPage />} />
        <Route path="/search" element={<SearchPage />} />
        <Route path="/news/:newsId" element={<NewsDetailPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </Layout>
  );
};

export default App;
