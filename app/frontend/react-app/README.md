# AI NOVA - 뉴스 기반 질의응답 시스템

AI NOVA는 빅카인즈(BIGKinds) 뉴스 데이터를 활용한 질의응답, 요약, 타임라인 생성 기능을 제공하는 웹 애플리케이션입니다.

## 주요 기능

- **질의응답(QA)**: 뉴스 데이터 기반 질문에 대한 답변 제공
- **요약(Summary)**: 키워드 기반 뉴스 내용 요약
- **타임라인(Timeline)**: 시간순으로 뉴스 이벤트 정렬 및 시각화

## 프로젝트 구조

```
app/
├── backend/            # FastAPI 백엔드
└── frontend/
    └── react-app/      # React 프론트엔드
```

## 기술 스택

### 프론트엔드

- React 18
- TypeScript
- TailwindCSS
- Framer Motion (애니메이션)
- Axios (HTTP 클라이언트)
- React Router (라우팅)

### 백엔드

- FastAPI
- Python
- ChromaDB (벡터 데이터베이스)
- OpenAI/HuggingFace (임베딩 및 LLM)

## 시작하기

### 프론트엔드 실행

```bash
cd app/frontend/react-app
npm install
npm start
```

### 백엔드 실행

```bash
cd app/backend
pip install -r requirements.txt
python main.py
```

## 특징

- **모던 UI/UX**: 깔끔하고 직관적인 사용자 인터페이스
- **반응형 디자인**: 모바일 및 데스크톱 환경 모두 지원
- **다크 모드**: 사용자 선호에 따른 테마 전환 기능
- **애니메이션 효과**: 부드러운 전환 및 마이크로인터랙션

## API 참조

프론트엔드는 다음 백엔드 API 엔드포인트와 통신합니다:

- `POST /api/qa`: 질의응답 API
- `POST /api/summarize`: 요약 API
- `POST /api/timeline`: 타임라인 API

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.
