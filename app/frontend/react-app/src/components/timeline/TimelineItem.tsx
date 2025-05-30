import React from "react";
import { TimelineItem as TimelineItemType } from "../../hooks/useTimeline";

interface TimelineItemProps {
  item: TimelineItemType;
}

/**
 * 타임라인 단일 항목 컴포넌트
 */
const TimelineItem: React.FC<TimelineItemProps> = ({ item }) => {
  return (
    <div className="flex">
      <div className="relative mr-4">
        <div className="h-12 w-12 rounded-full bg-primary-100 dark:bg-primary-900 flex items-center justify-center text-primary-600 dark:text-primary-300 shadow-md">
          <svg
            className="w-6 h-6"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
            ></path>
          </svg>
        </div>
      </div>
      <div className="flex-1">
        <div className="mb-1 text-sm font-medium text-gray-500 dark:text-gray-400">
          {new Date(item.date).toLocaleDateString("ko-KR", {
            year: "numeric",
            month: "long",
            day: "numeric",
          })}
        </div>
        <h3 className="text-lg font-semibold mb-2">{item.title}</h3>
        <p className="text-gray-700 dark:text-gray-300">{item.summary}</p>
      </div>
    </div>
  );
};

export default TimelineItem;
