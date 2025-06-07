import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { containerVariants, itemVariants } from "../animations/pageAnimations";
import LoadingSpinner from "../components/common/LoadingSpinner";
import ErrorMessage from "../components/common/ErrorMessage";
import ExchangeRateWidget from "../components/common/ExchangeRateWidget";
import AIAnalysisModal from "../components/common/AIAnalysisModal";
import Calendar from "../components/calendar/Calendar";
import useStockCalendar from "../hooks/useStockCalendar";

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

const StockCalendarPage: React.FC = () => {
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [selectedMarket, setSelectedMarket] = useState<"all" | "domestic" | "us">("all");
  const [selectedEventTypes, setSelectedEventTypes] = useState<string[]>([]);
  const [aiModalOpen, setAiModalOpen] = useState(false);
  const [selectedEvent, setSelectedEvent] = useState<CalendarEvent | null>(null);
  
  const { events, isLoading, error, fetchEvents, clearError } = useStockCalendar();

  useEffect(() => {
    // 선택된 달의 시작일과 종료일 계산
    const year = selectedDate.getFullYear();
    const month = selectedDate.getMonth();
    const startDate = new Date(year, month, 1);
    const endDate = new Date(year, month + 1, 0);
    
    fetchEvents({
      startDate: startDate.toISOString().split('T')[0],
      endDate: endDate.toISOString().split('T')[0],
      marketType: selectedMarket === "all" ? undefined : selectedMarket,
      eventTypes: selectedEventTypes.length > 0 ? selectedEventTypes : undefined,
    });
  }, [selectedDate, selectedMarket, selectedEventTypes, fetchEvents]);

  const handleEventClick = (event: CalendarEvent) => {
    setSelectedEvent(event);
    setAiModalOpen(true);
  };

  const closeAiModal = () => {
    setAiModalOpen(false);
    setSelectedEvent(null);
  };

  const handleDateSelect = (date: Date) => {
    setSelectedDate(date);
  };

  const toggleEventType = (eventType: string) => {
    setSelectedEventTypes((prev) =>
      prev.includes(eventType)
        ? prev.filter((t) => t !== eventType)
        : [...prev, eventType]
    );
  };

  // 선택된 날짜의 이벤트들
  const selectedDateEvents = events.filter(event => 
    event.date === selectedDate.toISOString().split('T')[0]
  );

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={containerVariants}
      className="space-y-8"
    >
      {/* 페이지 헤더 */}
      <motion.div variants={itemVariants}>
        <h1 className="text-3xl font-bold mb-4">📅 주식 캘린더</h1>
        <p className="text-gray-600 dark:text-gray-400">
          국내외 주요 투자 일정을 달력에서 한눈에 확인하세요
        </p>
      </motion.div>

      {/* 메인 콘텐츠 영역 */}
      <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
        {/* 좌측: 환율 정보와 필터 */}
        <div className="xl:col-span-1 space-y-6">
          {/* 환율 위젯 */}
          <motion.div variants={itemVariants}>
            <ExchangeRateWidget />
          </motion.div>

          {/* 필터 섹션 */}
          <motion.div variants={itemVariants} className="card">
            <h3 className="text-lg font-semibold mb-4">필터</h3>
            
            {/* 시장 선택 */}
            <div className="mb-4">
              <h4 className="text-sm font-medium mb-2">시장</h4>
              <div className="space-y-2">
                {[
                  { value: "all", label: "전체" },
                  { value: "domestic", label: "국내" },
                  { value: "us", label: "미국" }
                ].map(market => (
                  <label key={market.value} className="flex items-center">
                    <input
                      type="radio"
                      name="market"
                      value={market.value}
                      checked={selectedMarket === market.value}
                      onChange={(e) => setSelectedMarket(e.target.value as "all" | "domestic" | "us")}
                      className="mr-2"
                    />
                    <span className="text-sm">{market.label}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* 이벤트 유형 선택 */}
            <div>
              <h4 className="text-sm font-medium mb-2">이벤트 유형</h4>
              <div className="space-y-2">
                {[
                  { value: "earnings", label: "실적발표", color: "#3b82f6" },
                  { value: "dividend", label: "배당", color: "#10b981" },
                  { value: "holiday", label: "휴장일", color: "#ef4444" },
                  { value: "ipo", label: "IPO", color: "#f59e0b" },
                  { value: "economic", label: "경제지표", color: "#8b5cf6" },
                  { value: "split", label: "액면분할", color: "#ec4899" }
                ].map(type => (
                  <label key={type.value} className="flex items-center">
                    <input
                      type="checkbox"
                      checked={selectedEventTypes.includes(type.value)}
                      onChange={() => toggleEventType(type.value)}
                      className="mr-2"
                    />
                    <div
                      className="w-3 h-3 rounded mr-2"
                      style={{ backgroundColor: type.color }}
                    />
                    <span className="text-sm">{type.label}</span>
                  </label>
                ))}
              </div>
            </div>
          </motion.div>

          {/* 선택된 날짜의 이벤트 목록 */}
          <motion.div variants={itemVariants} className="card">
            <h3 className="text-lg font-semibold mb-4">
              {selectedDate.toLocaleDateString('ko-KR', { 
                month: 'long', 
                day: 'numeric' 
              })} 일정
            </h3>
            
            {selectedDateEvents.length > 0 ? (
              <div className="space-y-3">
                {selectedDateEvents.map((event) => (
                  <div
                    key={event.id}
                    className="p-3 rounded-lg border border-gray-200 dark:border-gray-600 hover:shadow-md transition-shadow cursor-pointer"
                    onClick={() => handleEventClick(event)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h4 className="font-medium text-sm">{event.title}</h4>
                        {event.stockName && (
                          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                            {event.stockName} ({event.stockCode})
                          </p>
                        )}
                        {event.description && (
                          <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                            {event.description}
                          </p>
                        )}
                      </div>
                      <button className="text-xs bg-gradient-to-r from-blue-500 to-purple-600 text-white px-2 py-1 rounded-full hover:from-blue-600 hover:to-purple-700 transition-all">
                        🤖 AI
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-4">
                선택한 날짜에 일정이 없습니다.
              </p>
            )}
          </motion.div>
        </div>

        {/* 우측: 달력 */}
        <div className="xl:col-span-3">
          <motion.div variants={itemVariants}>
            {isLoading ? (
              <div className="flex items-center justify-center h-96">
                <LoadingSpinner />
                <span className="ml-3">달력 데이터를 불러오는 중...</span>
              </div>
            ) : (
              <>
                <ErrorMessage message={error} />
                <Calendar
                  events={events}
                  selectedDate={selectedDate}
                  onDateSelect={handleDateSelect}
                  onEventClick={handleEventClick}
                />
              </>
            )}
          </motion.div>
        </div>
      </div>

      {/* AI 분석 모달 */}
      {selectedEvent && (
        <AIAnalysisModal
          isOpen={aiModalOpen}
          onClose={closeAiModal}
          title={selectedEvent.title}
          eventTitle={selectedEvent.title}
          eventDetails={selectedEvent.description}
          stockName={selectedEvent.stockName}
          stockCode={selectedEvent.stockCode}
          analysisType={selectedEvent.stockCode ? "stock" : "event"}
        />
      )}
    </motion.div>
  );
};

export default StockCalendarPage;