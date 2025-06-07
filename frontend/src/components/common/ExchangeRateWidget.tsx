import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";

interface ExchangeRate {
  currency: string;
  rate: number;
  name: string;
}

interface ExchangeRateData {
  timestamp: string;
  base: string;
  rates: Record<string, number>;
  source: string;
  success: boolean;
}

const ExchangeRateWidget: React.FC = () => {
  const [exchangeRates, setExchangeRates] = useState<ExchangeRate[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<string>("");

  const currencyNames = {
    USD: "미국 달러",
    JPY: "일본 엔 (100엔)",
    EUR: "유로",
    CNY: "중국 위안",
    GBP: "영국 파운드",
  };

  useEffect(() => {
    fetchExchangeRates();
    // 10분마다 환율 정보 업데이트
    const interval = setInterval(fetchExchangeRates, 10 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  const fetchExchangeRates = async () => {
    try {
      const response = await fetch("http://localhost:8000/api/stock-calendar/exchange-rates");
      const data: ExchangeRateData = await response.json();

      if (data.success && data.rates) {
        const rates: ExchangeRate[] = Object.entries(data.rates).map(([currency, rate]) => ({
          currency,
          rate: currency === "JPY" ? rate : Math.round(rate),
          name: currencyNames[currency as keyof typeof currencyNames] || currency,
        }));

        setExchangeRates(rates);
        setLastUpdated(new Date(data.timestamp).toLocaleTimeString("ko-KR"));
      }
    } catch (error) {
      console.error("환율 정보 조회 실패:", error);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-300 dark:bg-gray-600 rounded mb-2"></div>
          <div className="space-y-2">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="flex justify-between">
                <div className="h-3 bg-gray-300 dark:bg-gray-600 rounded w-20"></div>
                <div className="h-3 bg-gray-300 dark:bg-gray-600 rounded w-16"></div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4"
    >
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          📈 실시간 환율
        </h3>
        <button
          onClick={fetchExchangeRates}
          className="text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 transition-colors"
        >
          🔄 새로고침
        </button>
      </div>
      
      <div className="space-y-2">
        {exchangeRates.map((rate) => (
          <motion.div
            key={rate.currency}
            whileHover={{ scale: 1.02 }}
            className="flex justify-between items-center p-2 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          >
            <div className="flex items-center">
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300 w-12">
                {rate.currency}
              </span>
              <span className="text-xs text-gray-500 dark:text-gray-400 ml-2">
                {rate.name}
              </span>
            </div>
            <span className="text-sm font-bold text-gray-900 dark:text-white">
              ₩{rate.rate.toLocaleString()}
            </span>
          </motion.div>
        ))}
      </div>
      
      {lastUpdated && (
        <div className="text-xs text-gray-500 dark:text-gray-400 text-center mt-3 pt-2 border-t border-gray-200 dark:border-gray-600">
          마지막 업데이트: {lastUpdated}
        </div>
      )}
    </motion.div>
  );
};

export default ExchangeRateWidget;