import React, { useState } from "react";
import { motion } from "framer-motion";

interface Company {
  name: string;
  code: string;
  category: string;
}

type ReportType = "daily" | "weekly" | "monthly" | "quarterly" | "yearly";

interface ReportResult {
  success: boolean;
  company: string;
  report_type: ReportType;
  report_type_kr: string;
  period: {
    from: string;
    to: string;
  };
  summary: string;
  articles_count: number;
  detailed_articles?: Array<{
    id: string;
    ref_id: string;
    title: string;
    summary: string;
    provider: string;
    published_at: string;
    url: string;
    category: string;
    byline: string;
  }>;
  generated_at: string;
  model_used?: string;
}

interface ReportGeneratorProps {
  selectedCompany: Company | null;
  onClose: () => void;
}

const ReportGenerator: React.FC<ReportGeneratorProps> = ({
  selectedCompany,
  onClose,
}) => {
  const [isGenerating, setIsGenerating] = useState(false);
  const [selectedReportType, setSelectedReportType] =
    useState<ReportType | null>(null);
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");

  const reportTypes = [
    {
      type: "daily" as ReportType,
      label: "일간 레포트",
      description: "하루 동안의 뉴스 분석",
    },
    {
      type: "weekly" as ReportType,
      label: "주간 레포트",
      description: "일주일간의 뉴스 분석",
    },
    {
      type: "monthly" as ReportType,
      label: "월간 레포트",
      description: "한 달간의 뉴스 분석",
    },
    {
      type: "quarterly" as ReportType,
      label: "분기별 레포트",
      description: "3개월간의 뉴스 분석",
    },
    {
      type: "yearly" as ReportType,
      label: "연간 레포트",
      description: "1년간의 뉴스 분석",
    },
  ];

  const handleGenerateReport = async () => {
    if (!selectedCompany || !selectedReportType) return;

    setIsGenerating(true);

    try {
      const params = new URLSearchParams();
      if (fromDate) params.append("from", fromDate);
      if (toDate) params.append("until", toDate);

      const response = await fetch(
        `/api/news/company/${encodeURIComponent(
          selectedCompany.name
        )}/report/${selectedReportType}?${params}`,
        {
          method: "GET",
          headers: { "Content-Type": "application/json" },
        }
      );

      if (!response.ok) throw new Error("레포트 생성에 실패했습니다");

      const data: ReportResult = await response.json();

      // 새 창에서 레포트 표시
      const reportWindow = window.open(
        "",
        "_blank",
        "width=1200,height=800,scrollbars=yes"
      );
      if (reportWindow) {
        reportWindow.document.write(generateReportHTML(data));
        reportWindow.document.close();
      }
    } catch (err) {
      console.error("레포트 생성 오류:", err);
      alert(
        err instanceof Error ? err.message : "알 수 없는 오류가 발생했습니다"
      );
    } finally {
      setIsGenerating(false);
    }
  };

  const generateReportHTML = (report: ReportResult): string => {
    const formatSummaryWithCitations = (text: string): string => {
      return text.replace(/\[기사 (ref\d+)\]/g, (match, refId) => {
        return `<a href="#article-${refId}" class="citation-link" onclick="document.getElementById('article-${refId}').scrollIntoView({behavior: 'smooth'}); document.getElementById('article-${refId}').style.backgroundColor='#fef3c7'; setTimeout(() => document.getElementById('article-${refId}').style.backgroundColor='', 2000);">${match}</a>`;
      });
    };

    return `
      <!DOCTYPE html>
      <html lang="ko">
      <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>${report.company} ${report.report_type_kr} 레포트</title>
        <style>
          body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
            line-height: 1.6; 
            margin: 0; 
            padding: 20px; 
            background: #f9fafb; 
            color: #1f2937;
          }
          .container { 
            max-width: 1000px; 
            margin: 0 auto; 
            background: white; 
            padding: 40px; 
            border-radius: 12px; 
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); 
          }
          .header { 
            border-bottom: 2px solid #e5e7eb; 
            padding-bottom: 20px; 
            margin-bottom: 30px; 
          }
          .title { 
            font-size: 2.5rem; 
            font-weight: bold; 
            color: #1f2937; 
            margin-bottom: 10px; 
            background: linear-gradient(135deg, #3b82f6, #8b5cf6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
          }
          .subtitle { 
            font-size: 1.2rem; 
            color: #6b7280; 
          }
          .period { 
            background: linear-gradient(135deg, #f3f4f6, #e5e7eb); 
            padding: 15px; 
            border-radius: 8px; 
            margin: 20px 0; 
            border-left: 4px solid #3b82f6;
          }
          .summary { 
            background: linear-gradient(135deg, #f8fafc, #f1f5f9); 
            padding: 25px; 
            border-radius: 8px; 
            border-left: 4px solid #3b82f6; 
            margin: 20px 0; 
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
          }
          .articles-section { 
            margin-top: 40px; 
          }
          .article { 
            border: 1px solid #e5e7eb; 
            border-radius: 8px; 
            padding: 20px; 
            margin: 15px 0; 
            transition: all 0.3s; 
            background: white;
          }
          .article:hover { 
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); 
            transform: translateY(-2px);
          }
          .article-title { 
            font-size: 1.2rem; 
            font-weight: 600; 
            color: #1f2937; 
            margin-bottom: 10px; 
          }
          .article-meta { 
            font-size: 0.9rem; 
            color: #6b7280; 
            margin-bottom: 15px; 
          }
          .article-summary { 
            color: #374151; 
            line-height: 1.7;
          }
          .citation-link { 
            color: #3b82f6; 
            text-decoration: none; 
            font-weight: 600; 
            padding: 2px 6px; 
            border-radius: 4px; 
            background: #dbeafe; 
            transition: all 0.2s;
          }
          .citation-link:hover { 
            background: #bfdbfe; 
            transform: scale(1.05);
          }
          .ref-badge { 
            background: linear-gradient(135deg, #3b82f6, #1d4ed8); 
            color: white; 
            padding: 4px 8px; 
            border-radius: 12px; 
            font-size: 0.8rem; 
            font-weight: 600; 
            box-shadow: 0 2px 4px rgba(59, 130, 246, 0.3);
          }
          .footer { 
            margin-top: 40px; 
            padding-top: 20px; 
            border-top: 1px solid #e5e7eb; 
            text-align: center; 
            color: #6b7280; 
            font-size: 0.9rem; 
          }
          .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
          }
          .stat-card {
            background: linear-gradient(135deg, #f0f9ff, #e0f2fe);
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            border: 1px solid #bae6fd;
          }
          .stat-number {
            font-size: 2rem;
            font-weight: bold;
            color: #0369a1;
          }
          .stat-label {
            color: #0c4a6e;
            font-size: 0.9rem;
          }
        </style>
      </head>
      <body>
        <div class="container">
          <div class="header">
            <h1 class="title">${report.company} ${report.report_type_kr}</h1>
            <p class="subtitle">AI 기반 뉴스 분석 리포트</p>
          </div>
          
          <div class="stats-grid">
            <div class="stat-card">
              <div class="stat-number">${report.articles_count || 0}</div>
              <div class="stat-label">분석 기사 수</div>
            </div>
            <div class="stat-card">
              <div class="stat-number">${
                report.detailed_articles?.length || 0
              }</div>
              <div class="stat-label">참조 기사 수</div>
            </div>
          </div>
          
          <div class="period">
            <strong>📅 분석 기간:</strong> ${report.period?.from} ~ ${
      report.period?.to
    }
          </div>
          
          <div class="summary">
            <h2>📊 종합 분석</h2>
            <div>${formatSummaryWithCitations(report.summary || "")}</div>
          </div>
          
          <div class="articles-section">
            <h2>📰 참조 기사 목록</h2>
            ${
              report.detailed_articles
                ?.map(
                  (article) => `
              <div class="article" id="article-${article.ref_id}">
                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 10px;">
                  <h3 class="article-title">${article.title}</h3>
                  <span class="ref-badge">${article.ref_id}</span>
                </div>
                <div class="article-meta">
                  📰 ${article.provider} · 📅 ${article.published_at} ${
                    article.byline ? `· ✍️ ${article.byline}` : ""
                  }
                </div>
                <p class="article-summary">${article.summary}</p>
                ${
                  article.url
                    ? `<a href="${article.url}" target="_blank" style="color: #3b82f6; text-decoration: none; font-weight: 500;">🔗 원문 보기 →</a>`
                    : ""
                }
              </div>
            `
                )
                .join("") || ""
            }
          </div>
          
          <div class="footer">
            <p>🤖 생성 시간: ${new Date(
              report.generated_at || ""
            ).toLocaleString()}</p>
            <p>⚡ AI 모델: ${report.model_used || "GPT-4 Turbo"}</p>
            <p style="margin-top: 10px; font-size: 0.8rem; color: #9ca3af;">
              본 레포트는 AI가 뉴스 기사를 분석하여 생성한 것으로, 참고용으로만 활용해주세요.
            </p>
          </div>
        </div>
      </body>
      </html>
    `;
  };

  if (!selectedCompany) return null;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md w-full mx-4"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-bold">
            {selectedCompany.name} 레포트 생성
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg
              className="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">
              레포트 유형
            </label>
            <div className="grid grid-cols-1 gap-2">
              {reportTypes.map((report) => (
                <button
                  key={report.type}
                  onClick={() => setSelectedReportType(report.type)}
                  className={`p-3 text-left rounded-lg border transition-all ${
                    selectedReportType === report.type
                      ? "border-primary-500 bg-primary-50 dark:bg-primary-900/20"
                      : "border-gray-200 dark:border-gray-700 hover:border-primary-300"
                  }`}
                >
                  <div className="font-medium">{report.label}</div>
                  <div className="text-sm text-gray-500">
                    {report.description}
                  </div>
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">
                시작일 (선택)
              </label>
              <input
                type="date"
                value={fromDate}
                onChange={(e) => setFromDate(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">
                종료일 (선택)
              </label>
              <input
                type="date"
                value={toDate}
                onChange={(e) => setToDate(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>
          </div>

          <div className="flex gap-3 pt-4">
            <button
              onClick={onClose}
              className="flex-1 px-4 py-2 text-gray-600 dark:text-gray-400 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            >
              취소
            </button>
            <button
              onClick={handleGenerateReport}
              disabled={!selectedReportType || isGenerating}
              className={`flex-1 px-4 py-2 rounded-lg font-medium transition-all flex items-center justify-center gap-2 ${
                selectedReportType && !isGenerating
                  ? "bg-gradient-to-r from-primary-500 to-primary-600 hover:from-primary-600 hover:to-primary-700 text-white shadow-lg hover:shadow-xl"
                  : "bg-gray-200 dark:bg-gray-700 text-gray-400 cursor-not-allowed"
              }`}
            >
              {isGenerating ? (
                <>
                  <svg
                    className="w-4 h-4 animate-spin"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                    />
                  </svg>
                  생성 중...
                </>
              ) : (
                <>
                  <svg
                    className="w-4 h-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                    />
                  </svg>
                  레포트 생성
                </>
              )}
            </button>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
};

export default ReportGenerator;
