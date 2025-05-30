import React from "react";
import { TimelineItem as TimelineItemType } from "../../hooks/useTimeline";
import TimelineItem from "./TimelineItem";

interface TimelineListProps {
  items: TimelineItemType[];
}

/**
 * 타임라인 항목 리스트 컴포넌트
 */
const TimelineList: React.FC<TimelineListProps> = ({ items }) => {
  if (items.length === 0) return null;

  return (
    <div className="card">
      <h2 className="text-xl font-semibold mb-6">타임라인 결과</h2>

      <div className="space-y-8 relative">
        {/* 수직선 */}
        <div className="absolute left-6 top-1 bottom-10 w-0.5 bg-gray-200 dark:bg-gray-700"></div>

        {/* 타임라인 항목들 */}
        {items.map((item, index) => (
          <TimelineItem key={index} item={item} />
        ))}
      </div>
    </div>
  );
};

export default TimelineList;
