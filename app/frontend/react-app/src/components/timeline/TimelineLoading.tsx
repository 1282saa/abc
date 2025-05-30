import React from "react";

/**
 * 타임라인 로딩 상태 컴포넌트
 */
const TimelineLoading: React.FC = () => {
  return (
    <div className="card">
      <div className="animate-pulse space-y-8">
        {[1, 2, 3].map((i) => (
          <div key={i} className="flex">
            <div className="mr-4">
              <div className="h-12 w-12 rounded-full bg-gray-300 dark:bg-gray-700"></div>
              <div className="h-24 w-1 mx-auto mt-2 bg-gray-300 dark:bg-gray-700"></div>
            </div>
            <div className="flex-1">
              <div className="h-4 bg-gray-300 dark:bg-gray-700 rounded-full w-1/4 mb-2"></div>
              <div className="h-4 bg-gray-300 dark:bg-gray-700 rounded-full w-3/4 mb-4"></div>
              <div className="h-4 bg-gray-300 dark:bg-gray-700 rounded-full w-full"></div>
              <div className="h-4 bg-gray-300 dark:bg-gray-700 rounded-full w-5/6 mt-2"></div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default TimelineLoading;
