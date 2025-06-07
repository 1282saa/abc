import { useState, useCallback } from "react";
import { getStockCalendarEvents } from "../services/api";

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

interface UseStockCalendarReturn {
  events: CalendarEvent[];
  isLoading: boolean;
  error: string | null;
  fetchEvents: (params: {
    startDate: string;
    endDate: string;
    marketType?: string;
    eventTypes?: string[];
  }) => Promise<void>;
  clearError: () => void;
}

/**
 * 주식 캘린더 데이터를 관리하는 커스텀 훅
 */
const useStockCalendar = (): UseStockCalendarReturn => {
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchEvents = useCallback(async (params: {
    startDate: string;
    endDate: string;
    marketType?: string;
    eventTypes?: string[];
  }) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await getStockCalendarEvents(params);
      setEvents(response.events || []);
    } catch (err) {
      console.error("캘린더 이벤트 조회 오류:", err);
      setError(err instanceof Error ? err.message : "캘린더 이벤트 조회 중 오류가 발생했습니다.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    events,
    isLoading,
    error,
    fetchEvents,
    clearError,
  };
};

export default useStockCalendar;