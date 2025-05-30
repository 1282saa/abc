import React from "react";

/**
 * 페이지 하단 푸터 컴포넌트
 */
const Footer: React.FC = () => {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-white dark:bg-gray-800 shadow-inner py-6">
      <div className="container mx-auto px-4 max-w-7xl">
        <div className="flex flex-col md:flex-row justify-between items-center">
          <div className="mb-4 md:mb-0">
            <p className="text-sm text-gray-500 dark:text-gray-400">
              © {currentYear} AI NOVA. 모든 권리 보유.
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              뉴스 기반 인공지능 서비스
            </p>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
