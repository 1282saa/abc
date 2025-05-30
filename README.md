# AI NOVA - 빅카인즈 기반 뉴스 질의응답 시스템

## 프로젝트 개요

AI NOVA는 빅카인즈 API를 기반으로 하는 고급 뉴스 분석 및 질의응답 시스템입니다. 사용자가 자연어로 질문을 하면 관련 뉴스 기사를 검색하고 분석하여 정확하고 종합적인 답변을 제공합니다. 이 시스템은 이슈 중심의 뉴스 클러스터링, 요약 및 인사이트 생성 기능을 통해 방대한 뉴스 데이터를 효과적으로 활용할 수 있게 합니다.

## 핵심 기능

- **뉴스 기반 질의응답**: 자연어 질문에 대해 관련 뉴스 기사를 분석하여 답변 제공
- **뉴스 요약**: 특정 주제나 키워드에 관한 뉴스 기사들을 종합적으로 요약
- **타임라인 생성**: 이슈의 시간적 흐름과 발전 과정을 시각화
- **이슈 분석**: 주요 이슈의 맥락과 관련성을 파악하여 인사이트 제공
- **실시간 데이터 처리**: 빅카인즈 API를 통한 최신 뉴스 데이터 수집 및 분석

## 기술 스택

### 백엔드

- **Python 3.8+**: 핵심 로직 구현
- **FastAPI**: 고성능 REST API 서버
- **ChromaDB**: 벡터 데이터베이스 (뉴스 임베딩 저장)
- **OpenAI**: 텍스트 임베딩 및 LLM 기반 응답 생성
- **HuggingFace Transformers**: 오픈소스 임베딩 및 LLM 지원

### 프론트엔드

- **React**: 사용자 인터페이스 구현
- **TypeScript**: 타입 안정성 보장
- **TailwindCSS**: 모던 UI 스타일링
- **Vite**: 빠른 개발 경험 제공

## 프로젝트 구조

```
/
├── backend/                  # 백엔드 코드
│   ├── api/                  # API 관련 코드
│   │   ├── clients/          # 외부 API 클라이언트
│   │   │   └── bigkinds_client.py  # 빅카인즈 API 클라이언트
│   │   └── routes/           # API 라우트 정의
│   │       └── qa_routes.py  # 질의응답 API 엔드포인트
│   ├── services/             # 핵심 서비스 모듈
│   │   ├── qa/               # 질의응답 시스템
│   │   │   ├── vector_db.py  # 벡터 데이터베이스 관리
│   │   │   ├── embeddings.py # 텍스트 임베딩 처리
│   │   │   ├── doc_processor.py # 문서 처리 및 청크 분할
│   │   │   ├── retriever.py  # 관련 문서 검색
│   │   │   ├── llm_handler.py # LLM 인터페이스
│   │   │   ├── prompts.py    # 프롬프트 템플릿
│   │   │   └── engine.py     # QA 시스템 통합 엔진
│   │   ├── news/             # 뉴스 분석 모듈
│   │   │   └── news_engine.py # 뉴스 분석 엔진
│   │   └── content/          # 콘텐츠 생성 모듈
│   ├── utils/                # 유틸리티 함수
│   │   └── logger.py         # 로깅 설정
│   └── server.py             # 메인 서버 파일
│
├── frontend/                 # 프론트엔드 코드
│   ├── src/                  # 소스 코드
│   │   ├── components/       # React 컴포넌트
│   │   ├── pages/            # 페이지 컴포넌트
│   │   ├── hooks/            # React 커스텀 훅
│   │   ├── utils/            # 유틸리티 함수
│   │   ├── services/         # API 통신 로직
│   │   └── App.tsx           # 메인 앱 컴포넌트
│   ├── public/               # 정적 파일
│   ├── package.json          # 패키지 정보
│   └── tailwind.config.js    # TailwindCSS 설정
│
├── config/                   # 설정 파일
│   ├── settings.py           # 일반 설정
│   └── .env                  # 환경 변수 (API 키 등)
│
├── docs/                     # 문서
├── output/                   # 출력 파일 저장 디렉토리
└── cache/                    # 캐시 디렉토리 (벡터 DB 등)
```

## 주요 구성 요소 설명

### 1. 빅카인즈 클라이언트 (backend/api/clients/bigkinds_client.py)

- 빅카인즈 Open API에 접근하여 뉴스 데이터를 가져옵니다.
- 논리 연산자 지원, 중복 제거, 필터링 등 고급 검색 기능을 제공합니다.
- 재시도 로직 및 에러 처리를 통해 안정적인 API 호출을 보장합니다.

### 2. QA 시스템 (backend/services/qa/)

- **vector_db.py**: ChromaDB 기반 벡터 데이터베이스로 뉴스 임베딩을 저장하고 검색합니다.
- **embeddings.py**: OpenAI 또는 HuggingFace 모델을 사용하여 텍스트 임베딩을 생성합니다.
- **doc_processor.py**: 뉴스 기사를 적절한 크기로 분할하고 전처리합니다.
- **retriever.py**: 질의와 관련된 뉴스 기사를 검색합니다.
- **llm_handler.py**: LLM을 사용하여 질의에 대한 응답을 생성합니다.
- **prompts.py**: 다양한 사용 사례에 대한 프롬프트 템플릿을 제공합니다.
- **engine.py**: 모든 QA 구성 요소를 통합하는 메인 엔진입니다.

### 3. API 라우트 (backend/api/routes/)

- **qa_routes.py**: 질의응답, 요약, 타임라인 생성 등의 API 엔드포인트를 제공합니다.

### 4. 프론트엔드 (frontend/)

- React 기반의 현대적인 UI를 제공합니다.
- 질의응답, 뉴스 검색, 요약 및 타임라인 시각화 기능을 사용자 친화적으로 제공합니다.

## 설치 방법

### 요구사항

- Python 3.8+
- Node.js 16+
- 빅카인즈 API 키
- OpenAI API 키 (또는 대체 LLM)

### 백엔드 설치

```bash
# 프로젝트 클론
git clone https://github.com/your-org/ai-nova.git
cd ai-nova

# 가상환경 생성 및 활성화 (선택사항)
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 의존성 설치
pip install -r requirements.txt

# 환경변수 설정
cp config/.env.example config/.env
# .env 파일을 편집하여 API 키 등을 설정
```

### 프론트엔드 설치

```bash
cd frontend
npm install
```

## 실행 방법

### 백엔드 서버 실행

```bash
# 프로젝트 루트 디렉토리에서
python -m backend.server
```

### 프론트엔드 개발 서버 실행

```bash
cd frontend
npm run dev
```

## API 사용법

### 질의응답 API

```http
POST /api/qa/query
{
  "query": "삼성전자의 최근 실적은 어떤가요?",
  "search_params": {
    "date_range": ["2023-01-01", "2023-12-31"]
  }
}
```

### 뉴스 요약 API

```http
POST /api/qa/summarize
{
  "query": "우크라이나 전쟁",
  "search_params": {
    "date_range": ["2022-01-01", "2022-12-31"],
    "provider": ["서울경제"]
  }
}
```

### 타임라인 생성 API

```http
POST /api/qa/timeline
{
  "query": "코로나19 백신 개발",
  "search_params": {
    "date_range": ["2020-01-01", "2022-12-31"]
  }
}
```

## 기여 방법

1. 이슈 트래커에서 새 기능 요청 또는 버그 리포트를 확인하세요.
2. 저장소를 포크하고 개발 브랜치를 만드세요.
3. 코드를 변경하고 테스트를 추가하세요.
4. 변경사항을 커밋하고 풀 리퀘스트를 제출하세요.

## 라이센스

Copyright © 2025 서울경제신문. All rights reserved.

## 연락처

서울경제신문 디지털혁신팀 (digital@sedaily.com)
