"""
AI 뉴스 컨시어지 서비스

사용자의 질문에 대한 답변으로 뉴스 요약, 분석, 관련 기사 목록을 생성합니다.
"""
from typing import Dict, List, Any, Optional
import json
import re
import os
import openai

from backend.api.clients.bigkinds.client import BigKindsClient
from backend.api.clients.bigkinds.formatters import format_news_response
from backend.utils.logger import setup_logger 

class BriefingService:
    def __init__(self, bigkinds_client: BigKindsClient):
        self.bigkinds_client = bigkinds_client
        self.logger = setup_logger("briefing_service")
        # self.llm_client = LlmClient() # 실제 LLM 클라이언트 초기화

    async def generate_briefing_for_question(self, question: str) -> Dict[str, Any]:
        """
        사용자의 질문을 받아 검색, 요약, 분석을 수행하고 최종 브리핑을 생성합니다.

        Args:
            question: 사용자의 자연어 질문

        Returns:
            AI가 생성한 요약, 분석, 관련 기사 목록을 포함하는 딕셔너리
        """
        # 질문 저장 (응답에서 사용하기 위해)
        self._current_question = question
        
        # 1. 지능형 검색으로 관련 뉴스 기사 확보 (상위 30개)
        search_result = self.bigkinds_client.search_news_with_fallback(
            keyword=question,
            return_size=30,
            sort=[{"date": "desc"}, {"_score": "desc"}] # 최신순 우선 + 정확도
        )

        formatted_response = format_news_response(search_result)
        articles = formatted_response.get("documents", [])

        if not articles:
            return {
                "query": self._current_question,
                "summary": "관련된 기사를 찾지 못했습니다. 다른 키워드로 질문해보세요.",
                "documents": [],
                "points": [],
                "related_articles": []
            }

        # 2. 서울경제 기사만 필터링 (저작권 고려)
        seoul_articles = [
            article for article in articles 
            if article.get("provider_name", "") == "서울경제"
        ]
        
        # 서울경제 기사가 부족하면 전체 기사에서 3개만 선택하여 맥락 제공
        if len(seoul_articles) < 3:
            seoul_articles = articles[:5]  # 최대 5개로 제한
            self.logger.warning(f"서울경제 기사 부족 ({len(seoul_articles)}개), 전체 기사 사용")
        else:
            self.logger.info(f"서울경제 기사 {len(seoul_articles)}개 사용")

        # 3. LLM에 전달할 기사 내용 준비 (서울경제 기사 우선)
        context_for_llm = ""
        reference_articles = []
        
        for i, article in enumerate(seoul_articles[:5]):  # 최대 5개 기사
            title = article.get("title", "")
            content_preview = article.get("content", "")[:500] # 본문 앞 500자로 증가
            provider = article.get("provider_name", "")
            
            context_for_llm += f"--- 기사 {i+1} ({provider}) ---\n"
            context_for_llm += f"제목: {title}\n"
            context_for_llm += f"내용: {content_preview}...\n\n"
            
            reference_articles.append({
                "index": i+1,
                "title": title,
                "provider": provider,
                "url": article.get("url", ""),
                "published_at": article.get("published_at", "")
            })

        # 4. LLM을 통해 요약 및 분석 생성
        llm_prompt = self._create_llm_prompt(question, context_for_llm)
        
        # 실제 OpenAI API 호출
        try:
            llm_response = await self._call_openai_api(llm_prompt)
        except Exception as e:
            self.logger.error(f"OpenAI API 호출 실패: {str(e)}")
            # Fallback으로 Mock 데이터 사용
            llm_response = self._mock_llm_call(question, seoul_articles)

        # 4. LLM 응답과 원본 기사 데이터를 조합하여 최종 결과 생성
        response = self._format_final_response(llm_response, articles)
        
        return response

    async def _call_openai_api(self, prompt: str) -> Dict[str, Any]:
        """OpenAI API를 호출하여 실제 요약을 생성합니다."""
        
        # OpenAI API 키 설정
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            self.logger.warning("OPENAI_API_KEY 환경변수가 설정되지 않음, Mock 데이터 사용")
            raise Exception("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
        
        try:
            # OpenAI 클라이언트 초기화 (최신 버전 방식)
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=api_key)
            
            self.logger.info("OpenAI API 호출 시작")
            
            # GPT-4o-mini 모델 사용
            response = await client.chat.completions.create(
                model="gpt-4o-mini",  # 비용 효율적인 모델 사용
                messages=[
                    {
                        "role": "system", 
                        "content": "당신은 서울경제신문의 AI 뉴스 분석가입니다. 주어진 기사를 바탕으로 MZ세대를 위한 간결하고 정확한 FAQ를 생성합니다. 반드시 JSON 형식으로 응답해야 합니다."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=0.3,  # 일관성 있는 응답을 위해 낮은 온도
                max_tokens=2000,  # 적절한 길이 제한
                timeout=30,  # 30초 타임아웃
            )
            
            content = response.choices[0].message.content
            self.logger.info(f"OpenAI API 응답 수신: {len(content)} 글자")
            
            # JSON 응답 파싱 시도
            try:
                # JSON 블록 추출
                json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                    parsed_result = json.loads(json_str)
                    self.logger.info("JSON 블록에서 파싱 성공")
                    return parsed_result
                else:
                    # JSON 블록이 없으면 전체 내용을 JSON으로 파싱 시도
                    parsed_result = json.loads(content)
                    self.logger.info("전체 내용에서 JSON 파싱 성공")
                    return parsed_result
            except json.JSONDecodeError as e:
                self.logger.warning(f"OpenAI 응답을 JSON으로 파싱할 수 없음: {str(e)}, 텍스트 파싱 시도")
                return self._parse_text_response(content)
                
        except Exception as e:
            self.logger.error(f"OpenAI API 호출 오류: {str(e)}")
            raise

    def _parse_text_response(self, text: str) -> Dict[str, Any]:
        """텍스트 응답을 파싱하여 구조화된 데이터로 변환합니다."""
        
        # 요약 추출
        summary_match = re.search(r'기사 핵심요약[^\n]*\n\n(.*?)(?=\n\n.*FAQ|$)', text, re.DOTALL)
        summary = summary_match.group(1).strip() if summary_match else "요약을 생성할 수 없습니다."
        
        # FAQ 추출
        questions = re.findall(r'Q(\d+)\.\s*(.*?)\s*\n\s*A\.\s*(.*?)(?=\n\s*Q\d+\.|\Z)', text, re.DOTALL)
        
        points = []
        for q_num, question, answer in questions:
            points.append({
                "question": f"Q{q_num}. {question.strip()}",
                "answer": answer.strip(),
                "citations": [int(q_num)]  # 간단한 인용 번호
            })
        
        return {
            "summary": summary,
            "points": points
        }

    def _create_llm_prompt(self, question: str, context: str) -> str:
        """LLM에 전달할 프롬프트를 생성합니다."""
        
        prompt_template = """
        당신은 서울경제신문의 AI 뉴스 분석가입니다.
        주어진 서울경제 기사들을 바탕으로 사용자의 질문에 대해 간결하고 정확한 답변을 제공해야 합니다.

        ### 사용자의 질문:
        "{}"

        ### 참고 기사 (서울경제 우선):
        {}

        ### 응답 규칙:
        1. **간결성**: 각 답변은 70-80자 내외로 제한
        2. **구어체 사용**: "해요", "이에요", "라고 해요" 등 친근한 톤
        3. **구체적 정보**: 인명, 날짜, 수치, 기관명 등 구체적 사실 포함
        4. **인용 표시**: 각 답변에서 참조한 기사 번호를 citations에 명시
        5. **서울경제 기사 우선**: 가능한 한 서울경제 기사 내용을 중심으로 답변

        ### 최종 응답:
        반드시 아래 JSON 형식으로만 답변하세요:
        ```json
        {{
            "summary": "질문에 대한 핵심 요약 (100자 내외)",
            "points": [
                {{
                    "question": "Q1. 핵심 내용이 무엇인가요?",
                    "answer": "구체적이고 간결한 답변 (70-80자)",
                    "citations": [1, 2]
                }},
                {{
                    "question": "Q2. 배경이나 원인은 무엇인가요?",
                    "answer": "구체적이고 간결한 답변 (70-80자)",
                    "citations": [1]
                }},
                {{
                    "question": "Q3. 향후 전망은 어떻게 되나요?",
                    "answer": "구체적이고 간결한 답변 (70-80자)",
                    "citations": [2, 3]
                }}
            ]
        }}
        ```
        """
        try:
            return prompt_template.format(question, context).strip()
        except (KeyError, ValueError) as e:
            print("[DEBUG] prompt_template.format error:", str(e))
            # 안전한 방식으로 문자열 대체
            result = prompt_template.replace("{}", question, 1).replace("{}", context, 1)
            return result.strip()

    def _mock_llm_call(self, question: str, articles: List[Dict]) -> Dict[str, Any]:
        """실제 LLM API 호출을 대체하는 Mock 함수. 개발 및 테스트용."""
        
        # 실제 기사 정보를 바탕으로 더 현실적인 Mock 데이터 생성
        if not articles:
            return {
                "summary": f"{question}에 대한 관련 기사를 찾을 수 없어요. 다른 키워드로 질문해보세요.",
                "points": []
            }
        
        # 실제 기사에서 정보 추출
        main_article = articles[0] if articles else {}
        provider = main_article.get('provider_name', '서울경제')
        title = main_article.get('title', '관련 기사')
        
        result = {
            "summary": f"{question}에 대한 분석 결과, {provider} 등 주요 언론의 보도를 통해 최신 동향을 파악할 수 있어요. 관련 기사 {len(articles)}개를 분석한 결과를 요약해드릴게요.",
            "points": [
                {
                    "question": "Q1. 핵심 내용이 무엇인가요?",
                    "answer": f"{provider}에 따르면, {title}와 관련된 주요 이슈가 보도되고 있어요. 구체적인 내용은 첫 번째 기사에서 확인할 수 있어요.",
                    "citations": [1]
                },
                {
                    "question": "Q2. 배경이나 원인은 무엇인가요?",
                    "answer": f"관련 보도에 따르면, 이 이슈는 최근 경제 동향과 밀접한 관련이 있어요. 자세한 배경은 참고 기사들에서 확인할 수 있어요.",
                    "citations": [1, 2] if len(articles) > 1 else [1]
                },
                {
                    "question": "Q3. 향후 전망은 어떻게 되나요?",
                    "answer": f"전문가들은 이 분야의 지속적인 발전을 예상하고 있어요. {provider} 등의 보도를 통해 더 자세한 전망을 확인할 수 있어요.",
                    "citations": [1, 2, 3] if len(articles) > 2 else ([1, 2] if len(articles) > 1 else [1])
                }
            ]
        }
        
        # 서울경제 기사가 있는 경우 특별 처리
        seoul_articles = [a for a in articles if a.get('provider_name') == '서울경제']
        if seoul_articles:
            result["summary"] = f"{question}에 대한 서울경제 분석: 서울경제 등 {len(articles)}개 기사를 종합한 결과, 최신 동향과 전망을 요약해드려요."
        
        return result

    def _format_final_response(self, llm_response: Dict[str, Any], articles: List[Dict]) -> Dict[str, Any]:
        """LLM 응답과 원본 기사 목록을 조합하여 최종 API 응답 포맷을 생성합니다."""
        
        # 기사 목록에서 필요한 정보만 추출하여 'documents' 생성 (프론트엔드 형식에 맞춤)
        documents = []
        for i, article in enumerate(articles):
            documents.append({
                "news_id": article.get("news_id", str(i)),
                "title": article.get("title", "제목 없음"),
                "content": article.get("content", "내용 없음"),
                "provider": article.get("provider_name", "제공자 없음"),
                "published_at": article.get("published_at", ""),
                "provider_link_page": article.get("provider_link_page", ""),
                "url": article.get("url", ""),
                "byline": article.get("byline", ""),
                "category": article.get("category", ""),
                "dateline": article.get("dateline", ""),
                "enveloped_at": article.get("enveloped_at", ""),
                "hilight": article.get("hilight", "")
            })

        # 키워드 추출 및 관련성 분석 추가
        keywords = self._extract_keywords_from_articles(articles)
        network_data = self._generate_network_data(articles, keywords)
        
        # LLM 응답에서 points 필드 처리 (문자열 형식 응답 처리)
        points = []
        if isinstance(llm_response, dict):
            # 딕셔너리 형태로 정상 반환된 경우
            points = llm_response.get("points", [])
        elif isinstance(llm_response, str):
            # 문자열로 반환된 경우 JSON 파싱 시도
            try:
                # 문자열에서 JSON 부분 추출 시도
                json_match = re.search(r'```json\s*(.*?)\s*```', llm_response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                    parsed_data = json.loads(json_str)
                    points = parsed_data.get("points", [])
                else:
                    # JSON 블록이 없는 경우 전체 문자열을 JSON으로 파싱 시도
                    parsed_data = json.loads(llm_response)
                    points = parsed_data.get("points", [])
            except (json.JSONDecodeError, ValueError):
                # JSON 파싱 실패 시 FAQ 형식 파싱 시도
                try:
                    # FAQ 형식 파싱 (Q1. ... A. ... 패턴)
                    questions = re.findall(r'Q\d+\.\s*(.*?)\s*\n\s*A\.\s*(.*?)(?=\n\s*Q\d+\.|\Z)', llm_response, re.DOTALL)
                    points = [
                        {
                            "question": "Q{}. {}".format(i+1, q.strip()),
                            "answer": a.strip(),
                            "citations": []
                        }
                        for i, (q, a) in enumerate(questions)
                    ]
                except Exception:
                    # FAQ 파싱도 실패한 경우 기본 응답 생성
                    points = []

        return {
            "query": self._current_question,
            "summary": llm_response.get("summary", "요약 정보를 생성하지 못했습니다.") if isinstance(llm_response, dict) else "요약 정보를 생성하지 못했습니다.",
            "documents": documents,
            "points": points,
            "keywords": keywords,
            "network_data": network_data,
            "related_articles": documents  # 기존 호환성 유지
        }

    def _extract_keywords_from_articles(self, articles: List[Dict]) -> List[Dict[str, Any]]:
        """BigKinds 연관어 분석 API (TOPIC RANK)를 사용하여 고품질 키워드를 추출합니다."""
        
        # 1. 기사 제목들에서 주요 키워드 추출
        titles = [article.get("title", "") for article in articles if article.get("title")]
        if not titles:
            return []
        
        # 2. 가장 대표적인 제목이나 질문을 기반으로 연관어 분석
        representative_text = self._current_question or titles[0]
        
        try:
            # BigKinds word_cloud API를 사용한 고품질 키워드 추출
            word_cloud_keywords = self.bigkinds_client.get_word_cloud_keywords(
                keyword=representative_text,
                limit=25
            )
            
            if word_cloud_keywords:
                self.logger.info("BigKinds word_cloud API로 {} 개 키워드 추출 성공".format(len(word_cloud_keywords)))
                return word_cloud_keywords
            
        except Exception as e:
            self.logger.error("BigKinds word_cloud API 오류: {}".format(str(e)))
        
        # 3. Fallback: 기존 방식으로 키워드 추출
        self.logger.info("Fallback으로 기존 키워드 추출 방식 사용")
        return self._extract_keywords_fallback(articles)
    
    def _extract_keywords_fallback(self, articles: List[Dict]) -> List[Dict[str, Any]]:
        """기존 키워드 추출 방식 (Fallback용)"""
        from collections import Counter
        import re
        
        # 한국어 키워드 패턴 (2글자 이상, 특수문자 제외)
        keyword_pattern = re.compile(r'[가-힣]{2,}')
        
        # 개선된 불용어 리스트 (사용자 피드백 반영)
        stopwords = {
            # 기본 불용어
            '기자', '기업', '회사', '사업', '시장', '정부', '국가', '지난', '올해', '내년',
            '이번', '당시', '현재', '관련', '통해', '위해', '대한', '국내', '해외', '전년',
            '이날', '오늘', '어제', '내일', '이후', '이전', '동안', '과정', '결과', '상황',
            '문제', '방법', '계획', '예정', '필요', '가능', '중요', '주요', '최근', '향후',
            # 추가 불용어 (사용자 피드백)
            '발표', '진행', '참여', '제공', '운영', '실시', '마련', '확대', '강화', '개선',
            '추진', '검토', '논의', '협력', '지원', '활용', '도입', '구축', '발전', '성장',
            '증가', '감소', '변화', '영향', '효과', '이용', '사용', '적용', '경우', '때문',
            '따라', '따르', '위해서', '대해서', '에서는', '에게는', '라고', '다고', '한다',
            '있다', '없다', '된다', '안다', '모른다', '같다', '다르다', '크다', '작다'
        }
        
        all_keywords = []
        for article in articles:
            title = article.get("title", "")
            content = article.get("content", "")
            text = "{} {}".format(title, content)
            
            # 키워드 추출
            keywords = keyword_pattern.findall(text)
            # 불용어 제거 및 길이 제한 (3글자 이상 8글자 이하로 제한)
            keywords = [kw for kw in keywords if kw not in stopwords and 3 <= len(kw) <= 8]
            all_keywords.extend(keywords)
        
        # 빈도수 계산 (상위 25개)
        keyword_counts = Counter(all_keywords).most_common(25)
        
        return [
            {
                "keyword": keyword,
                "count": count,
                "weight": count / max(keyword_counts[0][1], 1)  # 정규화된 가중치
            }
            for keyword, count in keyword_counts
        ]

    def _generate_network_data(self, articles: List[Dict], keywords: List[Dict]) -> Dict[str, Any]:
        """키워드 간의 네트워크 데이터를 생성합니다."""
        nodes = []
        links = []
        
        # 키워드 노드만 생성 (더 많은 키워드로 확장)
        for i, keyword_data in enumerate(keywords[:25]):  # 상위 25개 키워드
            keyword = keyword_data["keyword"]
            
            # 엔티티 타입 및 카테고리 분류 (실제 엔티티 인식 로직)
            entity_type, category = self._classify_entity(keyword)
            
            # 엔티티 타입에 따른 색상 설정
            color_map = {
                "person": "#F59E0B",     # 주황색 - 인물
                "location": "#06B6D4",   # 청록색 - 장소
                "organization": "#3B82F6", # 파란색 - 기관
                "keyword": "#EF4444"     # 빨간색 - 일반 키워드
            }
            color = color_map.get(entity_type, "#6B7280")  # 기본 회색
            
            nodes.append({
                "id": "keyword_{}".format(i),
                "name": keyword,
                "type": entity_type,
                "category": category,
                "weight": keyword_data["weight"],
                "size": 20 + keyword_data["weight"] * 30,  # 더 큰 노드 크기
                "color": color
            })
        
        # 키워드 간 연관성 링크 생성 (동일 기사에 나타나는 키워드들을 연결)
        keyword_cooccurrence = {}  # 키워드 동시 출현 빈도 저장
        
        for article_idx, article in enumerate(articles):
            title = article.get("title", "")
            content = article.get("content", "")
            text = f"{title} {content}".lower()
            
            # 이 기사에 나타나는 키워드들 찾기
            article_keywords = []
            for keyword_idx, keyword_data in enumerate(keywords[:25]):
                keyword = keyword_data["keyword"]
                if keyword in text:
                    # 제목에 있으면 가중치 3배, 본문에만 있으면 1배
                    title_count = title.lower().count(keyword)
                    content_count = text.count(keyword) - title_count
                    occurrence_weight = (title_count * 3 + content_count) * keyword_data["weight"]
                    
                    if occurrence_weight > 0.2:  # 최소 임계값
                        article_keywords.append((keyword_idx, occurrence_weight))
            
            # 같은 기사에 나타나는 키워드들 간의 연결 강도 계산
            for i in range(len(article_keywords)):
                for j in range(i+1, len(article_keywords)):
                    kw1_idx, kw1_weight = article_keywords[i]
                    kw2_idx, kw2_weight = article_keywords[j]
                    
                    # 키워드 쌍을 정렬하여 중복 방지
                    pair = tuple(sorted([kw1_idx, kw2_idx]))
                    
                    if pair not in keyword_cooccurrence:
                        keyword_cooccurrence[pair] = 0
                    
                    # 동시 출현 강도 누적
                    keyword_cooccurrence[pair] += (kw1_weight + kw2_weight) / 2
        
        # 키워드 간 링크 생성 (강한 연결만)
        for (kw1_idx, kw2_idx), strength in keyword_cooccurrence.items():
            if strength > 0.4:  # 강한 연결만 표시
                links.append({
                    "source": "keyword_{}".format(kw1_idx),
                    "target": "keyword_{}".format(kw2_idx),
                    "strength": min(strength, 2.0),  # 최대 강도 제한
                    "width": max(1, min(4, strength * 1.5)),  # 선 두께
                    "type": "keyword_relation"
                })
        
        # 추가: 유사한 키워드들 간 연결 (편집 거리 기반)
        import difflib
        for i in range(len(keywords[:25])):
            for j in range(i+1, len(keywords[:25])):
                kw1 = keywords[i]["keyword"]
                kw2 = keywords[j]["keyword"]
                
                # 문자열 유사도 계산
                similarity = difflib.SequenceMatcher(None, kw1, kw2).ratio()
                
                # 높은 유사도의 키워드들 연결 (예: "네이버"와 "네이버는")
                if similarity > 0.7 and len(kw1) > 2 and len(kw2) > 2:
                    combined_weight = (keywords[i]["weight"] + keywords[j]["weight"]) / 2
                    
                    links.append({
                        "source": "keyword_{}".format(i),
                        "target": "keyword_{}".format(j),
                        "strength": combined_weight * similarity,
                        "width": max(1, combined_weight * 2),
                        "type": "similarity_relation"
                    })
        
        return {
            "nodes": nodes,
            "links": links
        }
    
    def _classify_entity(self, keyword: str) -> tuple[str, str]:
        """키워드를 엔티티 타입별로 분류합니다."""
        import re
        
        # 인물 패턴 (한국 이름, 외국 이름)
        person_patterns = [
            r'[가-힣]{2,3}(?:회장|대표|사장|부사장|상무|이사|부장|차장|과장|팀장|실장|본부장)',
            r'[가-힣]{2,3}(?:대통령|총리|장관|차관|국장|과장|청장|원장)',
            r'[가-힣]{2,3}(?:교수|박사|연구원|전문가|애널리스트)',
            r'[가-힣]{2,3}(?:의원|국회의원|시장|도지사|구청장)',
            r'[A-Z][a-z]+\s+[A-Z][a-z]+',  # 영문 이름
            r'[가-힣]{2,4}(?:\s+[가-힣]{1,2})?(?:씨|님)?$'  # 일반 한국 이름
        ]
        
        # 장소 패턴
        location_patterns = [
            r'[가-힣]+(?:시|도|군|구|읍|면|동|리)$',
            r'[가-힣]+(?:역|공항|항만|항구|터미널|센터|빌딩|타워)$',
            r'(?:서울|부산|대구|인천|광주|대전|울산|세종|경기|강원|충북|충남|전북|전남|경북|경남|제주)',
            r'(?:미국|중국|일본|독일|프랑스|영국|이탈리아|스페인|러시아|인도|브라질)',
            r'[가-힣]+(?:대학교|대학|학교|병원|연구소)$'
        ]
        
        # 기관/조직 패턴
        organization_patterns = [
            r'[가-힣]+(?:부|청|처|원|공사|공단|공기업)$',
            r'[가-힣]+(?:회사|기업|그룹|계열|법인|협회|조합|단체)$',
            r'[가-힣]+(?:은행|증권|보험|카드|금융|투자|자산운용)$',
            r'[가-힣]+(?:전자|화학|제약|건설|통신|IT|바이오|에너지)$',
            r'(?:삼성|LG|현대|SK|롯데|한화|포스코|KT|네이버|카카오)',
            r'[A-Z]{2,}(?:[a-z]*)?',  # 대문자 약어 (예: IBM, CEO, AI)
            r'[가-힣]+(?:정부|국회|법원|검찰|경찰|군|해군|공군|육군)$'
        ]
        
        # 패턴 매칭을 통한 분류
        for pattern in person_patterns:
            if re.search(pattern, keyword):
                return "person", "person"
        
        for pattern in location_patterns:
            if re.search(pattern, keyword):
                return "location", "location"
        
        for pattern in organization_patterns:
            if re.search(pattern, keyword):
                return "organization", "organization"
        
        # 기본값: 일반 키워드
        return "keyword", "keyword"