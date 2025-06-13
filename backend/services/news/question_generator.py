"""
질문 생성기 모듈

뉴스 기사 및 키워드 기반으로 연관 질문을 생성하는 모듈입니다.
"""

from typing import List, Dict, Tuple, Any, Set
import logging
from .keyword_analyzer import KeywordAnalyzer

logger = logging.getLogger(__name__)

class QuestionGenerator:
    """연관 질문 생성 클래스"""
    
    @staticmethod
    def create_question_templates() -> Dict[str, List[str]]:
        """질문 템플릿 정의 함수
        
        Returns:
            질문 템플릿 사전
        """
        templates = {
            # 비즈니스 전략 관련 질문
            "business_strategy": [
                "{company}가 {market}에 진출하는 전략적 의미는 무엇인가요?",
                "{company}의 {action}은 어떤 사업적 효과를 가져올까요?",
                "{company}가 {sector}에 {amount} 투자하는 이유는 무엇인가요?",
                "{keyword1}와 {keyword2} 사이의 관계가 {industry}에 미치는 영향은?",
                "{company}의 {strategy} 전략이 경쟁사와 비교해 가지는 강점은?"
            ],
            
            # 시장 트렌드 관련 질문
            "market_trend": [
                "{industry} 시장의 성장 가능성은 어느 정도인가요?",
                "{keyword}의 글로벌 트렌드는 어떻게 변화하고 있나요?",
                "{market} 시장에서 한국 기업들의 경쟁력은 어떤가요?",
                "{country}의 {industry} 시장이 한국 기업에 주는 기회는?",
                "{keyword} 관련 기술의 미래 전망은 어떻게 될까요?"
            ],
            
            # 기업 특화 질문
            "company_specific": [
                "{company}의 {action}이 회사 주가에 미칠 영향은?",
                "{company}는 {challenge}에 어떻게 대응하고 있나요?",
                "{company}와 {competitor} 간의 경쟁 구도는 어떻게 전개될까요?",
                "{company}의 {technology} 기술 개발 현황은 어떻게 되나요?",
                "{company}의 {region} 시장 점유율 확대 전략은 무엇인가요?"
            ],
            
            # 비교 분석 질문
            "comparison": [
                "{company1}와 {company2}의 {industry} 시장 점유율 차이는 어떻게 되나요?",
                "{keyword1}과 {keyword2} 기술의 차이점과 각각의 장단점은 무엇인가요?",
                "{company}의 {product}와 경쟁사 제품을 비교했을 때 차별점은 무엇인가요?",
                "{region1}과 {region2} 시장에서 {industry} 산업의 성장 패턴 차이는 무엇인가요?",
                "{strategy1}과 {strategy2} 전략 중 {industry} 산업에 더 효과적인 것은 무엇인가요?"
            ],
            
            # 시간적 흐름 질문
            "timeline": [
                "{company}의 {strategy} 전략은 지난 {time_period} 동안 어떻게 변화했나요?",
                "{industry} 시장의 {time_period} 성장 추이는 어떤 패턴을 보이나요?",
                "{company}가 {action}을 결정하기까지의 배경과 과정은 어떻게 되나요?",
                "{event} 이후 {industry} 산업은 어떻게 변화했나요?",
                "향후 {time_period} 동안 {keyword} 관련 시장은 어떻게 발전할 것으로 전망되나요?"
            ],
            
            # 영향 분석 질문
            "impact": [
                "{event}가 {industry} 산업에 미치는 장단기적 영향은 무엇인가요?",
                "{company}의 {action}이 {stakeholder}에게 어떤 영향을 미칠까요?",
                "{policy}가 {market} 시장 구조에 어떤 변화를 가져올 것으로 예상되나요?",
                "{technology}의 발전이 {industry} 산업의 일자리에 미치는 영향은 무엇인가요?",
                "{crisis}가 {industry} 산업의 공급망에 미친 영향과 대응 전략은 무엇인가요?"
            ],
            
            # 예측 질문
            "prediction": [
                "{industry} 시장은 향후 {time_period} 동안 어떻게 발전할 것으로 전망되나요?",
                "{company}의 {technology} 기술 개발이 성공한다면 어떤 새로운 시장이 열릴까요?",
                "{trend}의 확산으로 {industry} 산업은 어떤 방향으로 재편될 것으로 예상되나요?",
                "{country}의 {policy} 정책이 글로벌 {industry} 시장에 어떤 영향을 미칠까요?",
                "{company}가 {goal}을 달성하기 위해 어떤 전략을 수립해야 할까요?"
            ]
        }
        
        return templates
    
    @classmethod
    def generate_questions_from_article(
        cls,
        article: Dict[str, str],
        keyword_groups: Dict[str, List[str]],
        features: Dict[str, List[Tuple[str, float]]],
        related_terms: List[str] = None,
        top_keywords: List[str] = None
    ) -> List[str]:
        """기사 내용을 기반으로 질문 생성 함수
        
        Args:
            article: 기사 정보 (제목, 본문 등)
            keyword_groups: 그룹화된 키워드
            features: 추출된 특성과 가중치
            related_terms: 연관 키워드 (선택사항)
            top_keywords: 인기 키워드 (선택사항)
            
        Returns:
            생성된 질문 목록
        """
        title = article.get("title", "")
        content = article.get("content", "")
        
        if related_terms is None:
            related_terms = []
        if top_keywords is None:
            top_keywords = []
        
        questions = []
        
        # 1. 기업별 특화 질문 생성
        for company in keyword_groups["기업_관련"]:
            if company in title or company in content:
                # 기업-산업 관련 질문
                for industry in keyword_groups["산업_관련"]:
                    if industry in content:
                        questions.append(
                            f"{company}의 {industry} 사업 전략은 어떻게 발전하고 있나요?"
                        )
                        break
                
                # 기업-전략 관련 질문
                for strategy in keyword_groups["전략_관련"]:
                    if strategy in content:
                        questions.append(
                            f"{company}의 {strategy} 결정이 가져올 시장 변화는 무엇인가요?"
                        )
                        break
                
                # 기업 지역 진출 관련 질문
                for region in keyword_groups["지역_관련"]:
                    if region in content:
                        questions.append(
                            f"{company}의 {region} 시장 진출 전략과 경쟁 우위는 무엇인가요?"
                        )
                        break
        
        # 2. 산업 트렌드 관련 질문
        for industry in keyword_groups["산업_관련"]:
            if industry in title or industry in content:
                questions.append(
                    f"{industry} 산업의 최근 트렌드와 미래 전망은 어떻게 되나요?"
                )
                
                # 지역-산업 관련 질문
                for region in keyword_groups["지역_관련"]:
                    if region in content:
                        questions.append(
                            f"{region}의 {industry} 시장 성장률과 주요 성공 요인은 무엇인가요?"
                        )
                        break
        
        # 3. 기술 및 전략 관련 질문
        for strategy in keyword_groups["전략_관련"]:
            if strategy in title or strategy in content:
                # 기술 전략 질문
                if "기술" in content or "기술" in strategy:
                    questions.append(
                        f"{strategy} 기술 개발이 산업 생태계에 미치는 영향은 무엇인가요?"
                    )
                
                # 투자 전략 질문
                if "투자" in strategy or "투자" in content:
                    amount = "대규모"
                    for word in content.split():
                        if "조" in word or "억" in word:
                            amount = word
                            break
                    
                    questions.append(
                        f"{amount} 규모의 투자가 시장에 미치는 파급 효과는 무엇인가요?"
                    )
        
        # 4. 템플릿 기반 질문 생성
        templates = cls.create_question_templates()
        
        # 변수 값 사전 준비
        template_variables = cls._prepare_template_variables(
            keyword_groups, top_keywords, content
        )
        
        # 템플릿에 변수 값 채우기
        for category, template_list in templates.items():
            for template in template_list:
                filled_template = template
                
                # 모든 변수 채우기
                for var, value in template_variables.items():
                    if var in filled_template:
                        if value:
                            filled_template = filled_template.replace(var, value)
                        else:
                            # 값이 없는 변수가 있으면 이 템플릿은 건너뜀
                            filled_template = ""
                            break
                
                # 모든 변수가 채워진 경우에만 질문 추가
                if filled_template and "{" not in filled_template and "}" not in filled_template:
                    questions.append(filled_template)
        
        # 5. 특성 기반 직접 질문 생성
        title_features = [f[0] for f in features["title"][:3]] if "title" in features else []
        content_features = [f[0] for f in features["content"][:5]] if "content" in features else []
        
        for feature in title_features:
            if feature in keyword_groups["기업_관련"]:
                questions.append(f"{feature}의 최근 경영 전략 변화는 무엇인가요?")
            elif feature in keyword_groups["산업_관련"]:
                questions.append(f"{feature} 산업의 주요 성장 동력과 도전 과제는 무엇인가요?")
        
        for feature in content_features:
            if feature not in title_features and len(feature) > 1:
                if feature in keyword_groups["전략_관련"]:
                    questions.append(f"{feature} 전략이 기업 경쟁력에 미치는 영향은 무엇인가요?")
                elif feature in keyword_groups["지역_관련"]:
                    questions.append(f"{feature} 지역의 시장 특성과 진출 전략은 어떻게 되나요?")
        
        # 중복 제거 및 정리
        unique_questions = list(set(questions))
        
        # 너무 짧은 질문 제외
        final_questions = [q for q in unique_questions if len(q) > 15]
        
        # 최대 10개 질문만 반환
        return final_questions[:10]
    
    @classmethod
    def _prepare_template_variables(cls, keyword_groups: Dict[str, List[str]], 
                                   top_keywords: List[str], content: str) -> Dict[str, str]:
        """템플릿 변수 값 준비 함수
        
        Args:
            keyword_groups: 그룹화된 키워드
            top_keywords: 인기 키워드
            content: 기사 본문
            
        Returns:
            변수명과 값 매핑 사전
        """
        return {
            "{company}": keyword_groups["기업_관련"][0] if keyword_groups["기업_관련"] else "",
            "{company1}": keyword_groups["기업_관련"][0] if keyword_groups["기업_관련"] else "",
            "{company2}": keyword_groups["기업_관련"][1] if len(keyword_groups["기업_관련"]) > 1 else "",
            "{industry}": keyword_groups["산업_관련"][0] if keyword_groups["산업_관련"] else "",
            "{action}": keyword_groups["전략_관련"][0] if keyword_groups["전략_관련"] else "전략",
            "{strategy}": keyword_groups["전략_관련"][0] if keyword_groups["전략_관련"] else "사업 전략",
            "{strategy1}": keyword_groups["전략_관련"][0] if keyword_groups["전략_관련"] else "",
            "{strategy2}": keyword_groups["전략_관련"][1] if len(keyword_groups["전략_관련"]) > 1 else "",
            "{region}": keyword_groups["지역_관련"][0] if keyword_groups["지역_관련"] else "",
            "{region1}": keyword_groups["지역_관련"][0] if keyword_groups["지역_관련"] else "",
            "{region2}": keyword_groups["지역_관련"][1] if len(keyword_groups["지역_관련"]) > 1 else "",
            "{market}": keyword_groups["지역_관련"][0] if keyword_groups["지역_관련"] else "시장",
            "{country}": keyword_groups["지역_관련"][0] if keyword_groups["지역_관련"] else "글로벌",
            "{keyword}": top_keywords[0] if top_keywords else "",
            "{keyword1}": top_keywords[0] if top_keywords else "",
            "{keyword2}": top_keywords[1] if len(top_keywords) > 1 else "",
            "{technology}": "AI" if "AI" in content or "인공지능" in content else "신기술",
            "{sector}": keyword_groups["산업_관련"][0] if keyword_groups["산업_관련"] else "산업",
            "{amount}": "대규모" if "투자" in content else "",
            "{competitor}": keyword_groups["기업_관련"][1] if len(keyword_groups["기업_관련"]) > 1 else "경쟁사",
            "{challenge}": "시장 변화" if "변화" in content else "경쟁 심화",
            "{product}": "제품" if "제품" in content else "서비스",
            "{time_period}": "1년" if "올해" in content else "5년",
            "{event}": "정책 변화" if "정책" in content else "시장 변화",
            "{stakeholder}": "소비자" if "소비자" in content else "투자자",
            "{policy}": "규제" if "규제" in content else "지원 정책",
            "{crisis}": "공급망 위기" if "위기" in content else "경제 불황",
            "{trend}": "디지털 전환" if "디지털" in content else "기술 혁신",
            "{goal}": "시장 점유율 확대" if "점유율" in content else "기술 경쟁력 강화"
        }
    
    @staticmethod
    def score_questions(
        questions: List[str], 
        article_content: str,
        title_features: List[Tuple[str, float]],
        content_features: List[Tuple[str, float]]
    ) -> List[Tuple[str, float]]:
        """질문 점수 계산 함수
        
        Args:
            questions: 질문 목록
            article_content: 기사 본문
            title_features: 제목에서 추출한 특성
            content_features: 본문에서 추출한 특성
            
        Returns:
            점수가 계산된 질문 목록
        """
        scored_questions = []
        
        # 제목과 본문 특성에서 키워드 추출
        title_keywords = [k[0] for k in title_features]
        content_keywords = [k[0] for k in content_features]
        
        for question in questions:
            score = 1.0  # 기본 점수
            
            # 제목 키워드와의 관련성 계산
            for keyword, weight in title_features:
                if keyword in question:
                    score += weight * 2  # 제목 키워드는 가중치 2배
            
            # 본문 키워드와의 관련성 계산
            for keyword, weight in content_features:
                if keyword in question:
                    score += weight
            
            # 질문 길이 보정 (너무 짧거나 긴 질문 점수 조정)
            length = len(question)
            if length < 20:
                score *= 0.8
            elif length > 100:
                score *= 0.9
            
            # 질문 다양성 보정 (이미 추가된 질문과 유사한 경우 점수 감소)
            for existing_question, _ in scored_questions:
                similarity = QuestionGenerator._calculate_similarity(question, existing_question)
                if similarity > 0.7:  # 높은 유사도
                    score *= 0.8
                    break
            
            scored_questions.append((question, score))
        
        # 점수 기준으로 정렬
        scored_questions.sort(key=lambda x: x[1], reverse=True)
        
        return scored_questions
    
    @staticmethod
    def _calculate_similarity(text1: str, text2: str) -> float:
        """두 텍스트 간의 유사도 계산 함수
        
        Args:
            text1: 첫 번째 텍스트
            text2: 두 번째 텍스트
            
        Returns:
            유사도 점수 (0~1)
        """
        # 간단한 자카드 유사도 계산
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        # 교집합 크기
        intersection = len(words1.intersection(words2))
        
        # 합집합 크기
        union = len(words1.union(words2))
        
        if union == 0:
            return 0
        
        return intersection / union 