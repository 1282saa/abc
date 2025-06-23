import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import LoadingSpinner from "../components/common/LoadingSpinner";
import {
  getNewsDetail,
  NewsArticle,
  getArticleLink,
} from "../services/newsApi";

interface CustomQuestion {
  id: string;
  question: string;
  query: string;
  type: string;
}

interface RelatedArticle {
  id: string;
  title: string;
  provider: string;
  published_at?: string;
  summary?: string;
}

const NewsDetailPage: React.FC = () => {
  const { newsId } = useParams<{ newsId: string }>();
  const navigate = useNavigate();
  const [article, setArticle] = useState<NewsArticle | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedQuestion, setSelectedQuestion] = useState<string | null>(null);
  const [relatedArticles, setRelatedArticles] = useState<RelatedArticle[]>([]);
  const [customQuestions, setCustomQuestions] = useState<CustomQuestion[]>([]);
  const [loadingQuestions, setLoadingQuestions] = useState(false);
  const [loadingRelated, setLoadingRelated] = useState(false);

  useEffect(() => {
    const fetchArticleDetail = async () => {
      if (!newsId) return;

      setLoading(true);
      try {
        const data = await getNewsDetail(newsId);
        setArticle(data.news);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "알 수 없는 오류가 발생했습니다"
        );

        // 임시로 더미 데이터 설정 (API가 없는 경우)
        const dummyContent = `최근 조직 내부를 뒤흔든 삼성전자(005930) 내 최대 노조인 전국삼성전자노동조합(전삼노) 집행부가 임기 9개월가량을 남기고 전원 사임했다.

8일 업계에 따르면 순우룡 전삼노 3기 위원장은 4일 조합 플랫폼에서 '3기 임원 사임 입장문'을 게재하고 "임원 전원은 오늘부로 임기를 조기에 마무리하고 사임하기로 결정했다"며 "내년 임금 교섭 및 제4기 위원장 선거 일정이 겹치는 상황에서 새로운 집행부가 충분한 준비를 할 수 있도록 책임 있게 물러나기로 했다"고 밝혔다.

기존 3기 임원의 임기는 내년 3월까지이며, 4기 임원을 뽑는 선거는 올해 9월 예정된 것으로 알려졌다.

임기가 약 9개월 남은 집행부의 돌연 사임은 최근 사측과 집행부의 '2025년 임금·단체협약' 이면합의 의혹으로 불거진 조직 내 갈등이 영향을 끼친 것으로 보인다. 앞서 노사는 지난 3월 평균 임금 인상률 5.1%(기본연봉률 3.0%, 성과연봉률 2.1%) 등을 골자로 하는 2025년 임금·단체협약을 체결했다.

임단협 체결 이후 집행부가 사측과 별도 합의를 통해 상임집행부를 대상으로 성과연봉률을 더 높게 적용했다는 사실이 알려지면서 노조 내부서 내홍이 불거졌다. 실제 3명의 위원장단은 전체 집행부가 '새로운 집행부 도입과 조합 회무 처리기 위한 것'이라고 해명했지만, 조합원들은 노조 활동이 내부 밥벌이 아이템?라며 실제로 3명 3인 600명대 연간 조합원 수는 지난해 300명 기준 30만600명으로 급감했다.

새 집행부 출범까지 3개월 이상 남은 만큼 전삼노는 비상대책위원회 체제로 전환하고 조만간 1인 위원장에 권순학 비상대책위원장이 취임하는 방침이다. 권 비상대책위원장은 "지난 집행부는 조합 내 신뢰와 소통이 크게 훼손된 상황에 대해 책임을 통감하여 스스로 물러나는 결정을 했다"며 "비상대책위원장으로서 새로운 시작을 준비하는 정당타라"라 밝혔다.

다만 삼성전자 노사가 4월 사업장 삼과각 제도 개선 TF와 선택적 복리후생 TF 운영에는 차질이 생길 가능성이 커졌다. 당초 노사는 매주 워크숍 TF 회의를 직접 열고 6월까지 개선안을 마련하기로 했다.`;

        setArticle({
          news_id: newsId || "1",
          title: "삼성전자 노조 집행부 전원 사임...'비대위 체제 전환'",
          summary:
            "최근 조직 내부를 뒤흔든 삼성전자(005930) 내 최대 노조인 전국삼성전자노동조합(전삼노) 집행부가 임기 9개월가량을 남기고 전원 사임했다.",
          content: dummyContent,
          provider: "서울경제",
          url: "#",
          category: "기업",
          byline: "강병규 기자",
          images: [],
          published_at: "2025-06-08T00:00:00.000+09:00",
        });
      } finally {
        setLoading(false);
      }
    };

    fetchArticleDetail();
  }, [newsId]);

  // 기사 로드 후 관련 키워드 추출 및 질문 가져오기
  useEffect(() => {
    const fetchRelatedQuestions = async () => {
      if (!article) return;

      setLoadingQuestions(true);
      try {
        // 제목과 요약에서 키워드 추출 (간단한 구현)
        // 실제로는 명사 추출 등 더 정교한 방법을 사용해야 함
        const keywords = article.title.split(" ");
        const mainKeyword =
          article.category === "기업"
            ? keywords.find(
                (k) => k.length > 1 && !k.match(/[^가-힣a-zA-Z0-9]/)
              ) || "기업"
            : keywords[0] || "뉴스";

        // 연관 질문 API 호출 (v2 엔드포인트 사용)
        const response = await fetch(
          `/api/related-questions/v2?keyword=${encodeURIComponent(mainKeyword)}`
        );
        if (!response.ok) {
          throw new Error("관련 질문을 불러오는데 실패했습니다");
        }

        const data = await response.json();
        if (data.success && data.questions && data.questions.length > 0) {
          // ID 필드 추가
          const questionsWithId = data.questions.map((q: any, idx: number) => ({
            ...q,
            id: `q${idx + 1}`,
          }));
          setCustomQuestions(questionsWithId);
        } else {
          // API 결과가 없는 경우 기본 질문 설정
          setCustomQuestions([
            {
              id: "q1",
              question: "이 기사와 관련된 주요 이슈는 무엇인가요?",
              query: mainKeyword,
              type: "basic",
            },
            {
              id: "q2",
              question: "해당 기업의 미래 전망은 어떤가요?",
              query: `${mainKeyword} 전망`,
              type: "refine",
            },
            {
              id: "q3",
              question: "이 뉴스가 시장에 미치는 영향은?",
              query: `${mainKeyword} 영향`,
              type: "refine",
            },
          ]);
        }
      } catch (err) {
        console.error("관련 질문 로딩 오류:", err);
        // 오류 시 기본 질문 설정
        setCustomQuestions([
          {
            id: "q1",
            question: "이 기사와 관련된 주요 이슈는 무엇인가요?",
            query: "관련 이슈",
            type: "basic",
          },
          {
            id: "q2",
            question: "해당 기업의 미래 전망은 어떤가요?",
            query: "미래 전망",
            type: "basic",
          },
        ]);
      } finally {
        setLoadingQuestions(false);
      }
    };

    fetchRelatedQuestions();
  }, [article]);

  // 맞춤형 질문 클릭 시 연관 기사 표시
  const handleQuestionClick = async (questionId: string) => {
    setSelectedQuestion(questionId);
    setLoadingRelated(true);

    try {
      const selectedQ = customQuestions.find((q) => q.id === questionId);
      if (!selectedQ) return;

      // 선택한 질문의 query로 뉴스 검색 API 호출
      const response = await fetch(
        `/api/news/search?query=${encodeURIComponent(selectedQ.query)}&limit=5`
      );
      if (!response.ok) {
        throw new Error("관련 기사를 불러오는데 실패했습니다");
      }

      const data = await response.json();
      if (data.success && data.documents) {
        setRelatedArticles(
          data.documents.map((doc: any) => ({
            id: doc.id,
            title: doc.title,
            provider: doc.provider,
            published_at: doc.published_at,
            summary: doc.summary,
          }))
        );
      } else {
        setRelatedArticles([]);
      }
    } catch (err) {
      console.error("관련 기사 로딩 오류:", err);
      setRelatedArticles([]);
    } finally {
      setLoadingRelated(false);
    }
  };

  // 연관 기사 클릭 시 해당 기사로 이동
  const handleRelatedArticleClick = (articleId: string) => {
    navigate(`/news/${articleId}`);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner />
      </div>
    );
  }

  if (error || !article) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-red-600 mb-4">오류 발생</h2>
          <p className="text-gray-600 dark:text-gray-400">
            {error || "기사를 찾을 수 없습니다."}
          </p>
          <button
            onClick={() => navigate(-1)}
            className="mt-6 px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
          >
            뒤로 가기
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* 상단 헤더 */}
      <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
        <div className="container mx-auto py-4 px-4 flex justify-between items-center">
          <button
            onClick={() => navigate(-1)}
            className="flex items-center text-gray-700 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400 transition-colors"
          >
            <svg
              className="w-5 h-5 mr-1"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 19l-7-7 7-7"
              />
            </svg>
            <span>뒤로</span>
          </button>

          {article && (
            <a
              href={getArticleLink(article)}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
            >
              원문 보기
              <svg
                className="w-4 h-4 ml-2"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                />
              </svg>
            </a>
          )}
        </div>
      </header>

      {/* 메인 콘텐츠 */}
      <div className="container mx-auto px-4 py-6">
        <div className="flex flex-col lg:flex-row gap-6">
          {/* 좌측: 기사 본문 */}
          <div className="lg:w-2/3">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 mb-6"
            >
              <h1 className="text-2xl sm:text-3xl font-bold mb-4">
                {article.title}
              </h1>

              <div className="flex flex-wrap items-center justify-between text-sm text-gray-500 mb-6 pb-4 border-b border-gray-200 dark:border-gray-700">
                <div className="flex items-center gap-2 mb-2 sm:mb-0">
                  <span className="font-medium">{article.provider}</span>
                  {article.byline && <span>| {article.byline}</span>}
                </div>
                <span>
                  {article.published_at
                    ? new Date(article.published_at).toLocaleDateString("ko-KR")
                    : "날짜 정보 없음"}
                </span>
              </div>

              <div className="prose dark:prose-invert max-w-none">
                <div className="whitespace-pre-line">{article.content}</div>
              </div>
            </motion.div>
          </div>

          {/* 우측: 맞춤형 질문 및 연관 기사 */}
          <div className="lg:w-1/3 lg:sticky lg:top-4 self-start">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 mb-6"
            >
              <h2 className="text-xl font-semibold mb-4 flex items-center">
                <svg
                  className="w-5 h-5 mr-2 text-primary-600"
                  viewBox="0 0 24 24"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    d="M8.228 9L12 12.772 15.772 9 12 5.228 8.228 9z"
                    fill="currentColor"
                  />
                  <path
                    d="M12 3L6 9l6 6 6-6-6-6zM12 12.722L18 18.722l-6 6-6-6 6-6z"
                    fill="currentColor"
                  />
                </svg>
                AI 맞춤형 질문
              </h2>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                다음 질문들을 클릭하면 관련 기사를 확인할 수 있습니다.
              </p>

              {loadingQuestions ? (
                <div className="flex justify-center py-6">
                  <div className="w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full animate-spin"></div>
                </div>
              ) : (
                <div className="space-y-2">
                  {customQuestions.map((q) => (
                    <div
                      key={q.id}
                      onClick={() => handleQuestionClick(q.id)}
                      className={`p-3 rounded-lg cursor-pointer transition-all ${
                        selectedQuestion === q.id
                          ? "bg-primary-50 dark:bg-primary-900/30 border-l-4 border-primary-500"
                          : "bg-gray-50 dark:bg-gray-700/50 hover:bg-gray-100 dark:hover:bg-gray-700"
                      }`}
                    >
                      <p className="font-medium">{q.question}</p>
                      {q.type && (
                        <span
                          className={`text-xs px-2 py-0.5 rounded-full mt-1 inline-block
                          ${
                            q.type === "refine"
                              ? "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300"
                              : q.type === "expand"
                              ? "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300"
                              : q.type === "exclude"
                              ? "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300"
                              : "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300"
                          }`}
                        >
                          {q.type === "refine"
                            ? "AND"
                            : q.type === "expand"
                            ? "OR"
                            : q.type === "exclude"
                            ? "NOT"
                            : "BASIC"}
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </motion.div>

            {selectedQuestion && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6"
              >
                <h2 className="text-xl font-semibold mb-4 flex items-center">
                  <svg
                    className="w-5 h-5 mr-2 text-primary-600"
                    viewBox="0 0 24 24"
                    fill="none"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <path
                      d="M4 6H20M4 12H20M4 18H20"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                  연관 기사
                </h2>

                {loadingRelated ? (
                  <div className="flex justify-center py-6">
                    <div className="w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full animate-spin"></div>
                  </div>
                ) : relatedArticles.length > 0 ? (
                  <div className="space-y-3">
                    {relatedArticles.map((article) => (
                      <div
                        key={article.id}
                        onClick={() => handleRelatedArticleClick(article.id)}
                        className="p-3 rounded-lg cursor-pointer bg-gray-50 dark:bg-gray-700/50 hover:bg-gray-100 dark:hover:bg-gray-700 transition-all"
                      >
                        <h3 className="font-medium mb-1">{article.title}</h3>
                        {article.summary && (
                          <p className="text-xs text-gray-600 dark:text-gray-400 mb-2 line-clamp-2">
                            {article.summary}
                          </p>
                        )}
                        <div className="flex justify-between text-xs text-gray-500">
                          <span>{article.provider}</span>
                          <span>
                            {article.published_at
                              ? new Date(
                                  article.published_at
                                ).toLocaleDateString("ko-KR")
                              : ""}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-600 dark:text-gray-400">
                    관련 기사를 찾을 수 없습니다.
                  </p>
                )}

                <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                  <button
                    className="text-sm text-primary-600 dark:text-primary-400 hover:underline"
                    onClick={() => setSelectedQuestion(null)}
                  >
                    다른 질문 선택하기
                  </button>
                </div>
              </motion.div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default NewsDetailPage;
