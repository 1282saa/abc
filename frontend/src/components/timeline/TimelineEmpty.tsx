import React from "react";

/**
 * 타임라인 결과가 없을 때 표시하는 빈 상태 컴포넌트
 */
const TimelineEmpty: React.FC = () => {
  return (
    <div className="card flex flex-col items-center justify-center text-center p-12">
      <svg
        className="w-16 h-16 text-gray-400 dark:text-gray-600 mb-4"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.5}
          d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
        ></path>
      </svg>
      <h3 className="text-lg font-medium mb-2">
        타임라인 결과가 여기에 표시됩니다
      </h3>
      <p className="text-gray-500 dark:text-gray-400 max-w-md">
        왼쪽의 키워드 입력 폼에서 관심 있는 주제의 키워드를 입력하고 타임라인
        생성 버튼을 클릭하세요.
      </p>
    </div>
  );
};

export default TimelineEmpty;
