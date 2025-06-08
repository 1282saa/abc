# 빅카인즈 뉴스 분석 시스템 - 백엔드

이 디렉토리는 빅카인즈 API를 활용한 뉴스 분석 시스템의 백엔드 코드를 포함합니다.

## 디렉토리 구조

```
backend/
├── api/
│   ├── clients/           # 외부 API 클라이언트
│   │   ├── bigkinds/      # 모듈화된 빅카인즈 클라이언트
│   │   │   ├── __init__.py
│   │   │   ├── client.py      # 기본 클라이언트
│   │   │   ├── constants.py   # 상수 정의
│   │   │   └── formatters.py  # 응답 포맷팅
│   │   ├── bigkinds_client.py # 빅카인즈 클라이언트 (리디렉션)
│   │   └── __init__.py
│   ├── routes/            # API 라우트
│   │   ├── news_routes.py      # 뉴스 관련 API
│   │   └── stock_calendar_routes.py # 경제 캘린더 API
│   ├── utils/             # API 유틸리티
│   │   └── keywords_utils.py   # 키워드 처리 유틸리티
│   └── __init__.py
├── constants/            # 상수 정의
├── services/             # 서비스 계층
│   ├── dart_api.py           # DART API 서비스
│   ├── perplexity.py         # AI 서비스
│   └── us_stock_api.py       # 주식 데이터 서비스
├── utils/                # 유틸리티 함수
│   └── logger.py             # 로깅 유틸리티
├── __init__.py
└── server.py             # FastAPI 서버
```

## 주요 구성 요소

### API 클라이언트

- `api/clients/bigkinds/` - 빅카인즈 API 클라이언트
  - `client.py` - 핵심 클라이언트 클래스
  - `constants.py` - API 관련 상수
  - `formatters.py` - 응답 포맷팅 함수

### API 라우트

- `api/routes/news_routes.py` - 뉴스 관련 API 엔드포인트
  - 최신 뉴스 조회
  - 검색 기능
  - 연관 질문 생성
  - 기업 뉴스 보고서

### 유틸리티

- `api/utils/keywords_utils.py` - 키워드 처리 유틸리티
  - 불용어 제거
  - 키워드 점수화
  - 불리언 연산자 쿼리 생성
  - 자연어 질문 생성

## API 엔드포인트

### 뉴스 API

#### 최신 뉴스 및 이슈

```
GET /api/news/latest
```

오늘의 이슈 및 인기 키워드를 포함한 최신 뉴스 정보를 반환합니다.

#### 뉴스 검색

```
GET /api/news/search/news?keyword={keyword}
```

키워드 기반 뉴스 검색 결과를 반환합니다.

#### 연관 질문 생성

```
GET /api/news/related-questions/{keyword}
```

검색 키워드에 기반한 연관 질문을 생성합니다.

#### 질문 기반 검색

```
GET /api/news/search-by-question?query={query}&question={question}
```

연관 질문에서 생성된 쿼리로 뉴스를 검색합니다.

## 설치 및 실행

1. 필요한 패키지 설치:

   ```bash
   pip install -r requirements.txt
   ```

2. 환경 변수 설정:

   ```bash
   # .env 파일 생성
   BIGKINDS_KEY=your_bigkinds_api_key
   OPENAI_API_KEY=your_openai_api_key
   ```

3. 서버 실행:
   ```bash
   # 프로젝트 루트 디렉토리에서
   python -m backend.server
   ```

## 빅카인즈 API 클라이언트 코드 구조

빅카인즈 API 클라이언트는 모듈화되어 유지보수가 용이하게 구현되어 있습니다:

1. `client.py` - 기본 요청 처리 및 핵심 메서드
2. `constants.py` - API URL 및 기본 필드 정의
3. `formatters.py` - API 응답 포맷팅 함수

## 연관 질문 구현

1. 키워드 분석: 빅카인즈 API로 연관어와 빈출어 조회
2. 키워드 필터링: 불용어 제거 및 의미 있는 키워드 추출
3. 점수화: 키워드별 중요도 점수 계산
4. 쿼리 변형: 불리언 연산자(AND, OR, NOT)를 활용한 쿼리 생성
5. 질문 생성: 자연어 템플릿을 활용한 질문 생성

## 문제 해결

### API 키 오류

- 환경 변수가 제대로 설정되었는지 확인
- API 키가 유효한지 확인

### 빅카인즈 API 오류

- 서버 로그에서 상세 오류 메시지 확인
- API 응답 상태 코드 확인

### 연관 질문 생성 실패

- 키워드가 너무 광범위하거나 구체적인지 확인
- 충분한 연관어가 추출되는지 확인

## 모듈화 가이드 (진행 중)

news_routes.py 파일이 너무 큰 파일(1200줄 이상)이므로 다음과 같이 기능별로 분리하고 있습니다:

1. 이미 분리된 라우터:

   - `latest_news_routes.py`: 최신 뉴스 및 이슈 관련 (`/latest`)

2. 분리 예정 라우터:
   - `company_news_routes.py`: 기업 뉴스 관련 (`/company`, `/company/{company_name}/summary`, `/company/{company_name}/report/{report_type}`)
   - `search_routes.py`: 검색 관련 (`/search`, `/search/news`, `/search-by-question`)
   - `related_questions_routes.py`: 연관 질문 관련 (`/related-questions/{keyword}`)
   - `ai_summary_routes.py`: AI 요약 관련 (`/ai-summary`)
   - `watchlist_routes.py`: 관심 종목 관련 (`/watchlist`, `/watchlist/suggestions`)

### 분리 작업 진행 방법

1. 먼저 `backend/api/models/news_models.py`에 해당 기능에서 사용하는 모델 클래스를 추가합니다.
2. 다음으로 해당 기능의 라우터 파일을 생성하고 필요한 의존성을 import 합니다.
3. 필요한 엔드포인트들을 원래 news_routes.py에서 찾아 새 라우터 파일로 이동합니다.
4. `backend/server.py` 파일에서 새 라우터를 import하고 등록합니다.

### 분리 작업 후 검증

1. 백엔드 서버를 재시작합니다: `python -m backend.server`
2. API 엔드포인트가 제대로 동작하는지 확인합니다: `http://localhost:8000/api/docs`

분리 작업이 모두 완료되면 원래의 news_routes.py 파일은 삭제하고 분리된 라우터만 사용하도록 합니다.
