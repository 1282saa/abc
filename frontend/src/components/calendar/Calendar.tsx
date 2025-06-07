import React, { useState, useMemo } from "react";
import { motion } from "framer-motion";

interface CalendarEvent {
  id: string;
  title: string;
  date: string;
  eventType: "earnings" | "dividend" | "holiday" | "ipo" | "economic" | "split";
  stockCode?: string;
  stockName?: string;
  description?: string;
  marketType?: "domestic" | "us" | "global";
}

interface CalendarProps {
  events: CalendarEvent[];
  selectedDate: Date;
  onDateSelect: (date: Date) => void;
  onEventClick: (event: CalendarEvent) => void;
}

const eventTypeColors = {
  earnings: "#3b82f6", // blue
  dividend: "#10b981", // green
  holiday: "#ef4444", // red
  ipo: "#f59e0b", // yellow
  economic: "#8b5cf6", // purple
  split: "#ec4899", // pink
};

const Calendar: React.FC<CalendarProps> = ({
  events,
  selectedDate,
  onDateSelect,
  onEventClick,
}) => {
  const [currentMonth, setCurrentMonth] = useState(new Date(selectedDate));

  // 달력 데이터 계산
  const calendarData = useMemo(() => {
    const year = currentMonth.getFullYear();
    const month = currentMonth.getMonth();
    
    // 해당 월의 첫 번째 날과 마지막 날
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    
    // 달력 시작일 (첫 주의 일요일)
    const startDate = new Date(firstDay);
    startDate.setDate(startDate.getDate() - firstDay.getDay());
    
    // 달력 종료일 (마지막 주의 토요일)
    const endDate = new Date(lastDay);
    endDate.setDate(endDate.getDate() + (6 - lastDay.getDay()));
    
    // 달력 날짜 배열 생성
    const dates = [];
    const current = new Date(startDate);
    
    while (current <= endDate) {
      dates.push(new Date(current));
      current.setDate(current.getDate() + 1);
    }
    
    return {
      dates,
      firstDay,
      lastDay,
    };
  }, [currentMonth]);

  // 특정 날짜의 이벤트 가져오기
  const getEventsForDate = (date: Date) => {
    const dateStr = date.toISOString().split('T')[0];
    return events.filter(event => event.date === dateStr);
  };

  // 이전/다음 달로 이동
  const navigateMonth = (direction: 'prev' | 'next') => {
    const newMonth = new Date(currentMonth);
    newMonth.setMonth(newMonth.getMonth() + (direction === 'next' ? 1 : -1));
    setCurrentMonth(newMonth);
  };

  // 오늘 날짜로 이동
  const goToToday = () => {
    const today = new Date();
    setCurrentMonth(today);
    onDateSelect(today);
  };

  // 날짜 클릭 핸들러
  const handleDateClick = (date: Date) => {
    onDateSelect(date);
  };

  // 날짜가 현재 월에 속하는지 확인
  const isCurrentMonth = (date: Date) => {
    return date.getMonth() === currentMonth.getMonth();
  };

  // 날짜가 선택된 날짜인지 확인
  const isSelectedDate = (date: Date) => {
    return date.toDateString() === selectedDate.toDateString();
  };

  // 오늘 날짜인지 확인
  const isToday = (date: Date) => {
    const today = new Date();
    return date.toDateString() === today.toDateString();
  };

  const weekDays = ['일', '월', '화', '수', '목', '금', '토'];
  const monthNames = [
    '1월', '2월', '3월', '4월', '5월', '6월',
    '7월', '8월', '9월', '10월', '11월', '12월'
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6"
    >
      {/* 달력 헤더 */}
      <div className="flex items-center justify-between mb-6">
        <button
          onClick={() => navigateMonth('prev')}
          className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        
        <div className="text-center">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">
            {currentMonth.getFullYear()}년 {monthNames[currentMonth.getMonth()]}
          </h2>
          <button
            onClick={goToToday}
            className="text-sm text-primary-600 dark:text-primary-400 hover:underline mt-1"
          >
            오늘로 이동
          </button>
        </div>
        
        <button
          onClick={() => navigateMonth('next')}
          className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>

      {/* 요일 헤더 */}
      <div className="grid grid-cols-7 gap-1 mb-2">
        {weekDays.map((day, index) => (
          <div
            key={day}
            className={`text-center py-2 text-sm font-medium ${
              index === 0 ? 'text-red-500' : index === 6 ? 'text-blue-500' : 'text-gray-700 dark:text-gray-300'
            }`}
          >
            {day}
          </div>
        ))}
      </div>

      {/* 달력 날짜 */}
      <div className="grid grid-cols-7 gap-1">
        {calendarData.dates.map((date, index) => {
          const dayEvents = getEventsForDate(date);
          const isCurrentMonthDate = isCurrentMonth(date);
          const isSelected = isSelectedDate(date);
          const isTodayDate = isToday(date);
          
          return (
            <motion.button
              key={index}
              onClick={() => handleDateClick(date)}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className={`
                relative min-h-[100px] p-2 border border-gray-200 dark:border-gray-600 rounded-lg
                transition-all duration-200 text-left
                ${isCurrentMonthDate 
                  ? 'bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700' 
                  : 'bg-gray-50 dark:bg-gray-900 text-gray-400 dark:text-gray-600'
                }
                ${isSelected ? 'ring-2 ring-primary-500 bg-primary-50 dark:bg-primary-900/20' : ''}
                ${isTodayDate ? 'ring-2 ring-green-500' : ''}
              `}
            >
              {/* 날짜 숫자 */}
              <div className={`
                text-sm font-medium mb-1
                ${isTodayDate ? 'text-green-600 dark:text-green-400' : ''}
                ${isSelected ? 'text-primary-600 dark:text-primary-400' : ''}
              `}>
                {date.getDate()}
              </div>

              {/* 이벤트 표시 */}
              <div className="space-y-1">
                {dayEvents.slice(0, 3).map((event) => (
                  <motion.div
                    key={event.id}
                    onClick={(e) => {
                      e.stopPropagation();
                      onEventClick(event);
                    }}
                    whileHover={{ scale: 1.05 }}
                    className="text-xs p-1 rounded text-white cursor-pointer truncate"
                    style={{
                      backgroundColor: eventTypeColors[event.eventType],
                    }}
                    title={`${event.title} - ${event.description || ''}`}
                  >
                    {event.title.length > 10 ? `${event.title.substring(0, 10)}...` : event.title}
                  </motion.div>
                ))}
                
                {/* 더 많은 이벤트가 있을 때 */}
                {dayEvents.length > 3 && (
                  <div className="text-xs text-gray-500 dark:text-gray-400 text-center">
                    +{dayEvents.length - 3}개 더
                  </div>
                )}
              </div>
            </motion.button>
          );
        })}
      </div>

      {/* 범례 */}
      <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-600">
        <h4 className="text-sm font-medium mb-3 text-gray-700 dark:text-gray-300">이벤트 유형</h4>
        <div className="flex flex-wrap gap-3">
          {Object.entries(eventTypeColors).map(([type, color]) => (
            <div key={type} className="flex items-center gap-1">
              <div
                className="w-3 h-3 rounded"
                style={{ backgroundColor: color }}
              />
              <span className="text-xs text-gray-600 dark:text-gray-400">
                {{
                  earnings: "실적발표",
                  dividend: "배당",
                  holiday: "휴장일",
                  ipo: "IPO",
                  economic: "경제지표",
                  split: "액면분할",
                }[type as keyof typeof eventTypeColors]}
              </span>
            </div>
          ))}
        </div>
      </div>
    </motion.div>
  );
};

export default Calendar;