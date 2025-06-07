# AI NOVA - 스마트 뉴스 분석 플랫폼

AI NOVA는 빅카인즈(BigKinds) API를 기반으로 하는 차세대 뉴스 분석 플랫폼입니다. 서울경제신문을 위해 개발된 이 시스템은 관심 기업의 뉴스를 실시간으로 추적하고, GPT-4 Turbo를 활용한 AI 요약 기능을 제공합니다.

## 🚀 주요 기능

### 📊 홈페이지 - 최신 뉴스 대시보드
- **오늘의 이슈**: 빅카인즈 이슈 랭킹을 통한 실시간 주요 이슈 분석
- **인기 키워드**: 카테고리별 핫 키워드 모니터링 및 트렌드 분석

### 📈 관심 종목 - 기업 뉴스 추적
- **기업별 뉴스 타임라인**: 날짜별 뉴스 정렬 및 시각화
- **뉴스 캐러셀**: 주요 기사 요약 슬라이드
- **AI 요약 기능**: 
  - 🎯 **이슈 중심 요약**: 핵심 이슈와 동향 분석
  - 💬 **인용 중심 요약**: 주요 인물 발언 및 의견 정리
  - 📊 **수치 중심 요약**: 중요 통계 및 데이터 분석

### 📅 투자 캘린더 - 경제 일정 관리
- 주요 경제 이벤트 및 공시 일정 통합 관리
- DART API 연동을 통한 기업 공시 정보

## 🏗️ 시스템 아키텍처

### 백엔드 (Python/FastAPI)
```
backend/
├── api/
│   ├── clients/           # 외부 API 클라이언트
│   │   └── bigkinds_client.py  # 빅카인즈 API 통합
│   └── routes/           # API 엔드포인트
│       ├── news_routes.py     # 뉴스 관련 API
│       └── stock_calendar_routes.py  # 투자 캘린더 API
├── services/             # 비즈니스 로직
│   ├── dart_api_client.py     # DART 공시 정보
│   ├── kis_api_client.py      # 한국투자증권 API
│   ├── exchange_rate_service.py # 환율 정보
│   └── perplexity_client.py   # AI 분석 보조
├── utils/               # 유틸리티
│   └── logger.py            # 로깅 시스템
└── server.py            # FastAPI 메인 서버
```

### 프론트엔드 (React/TypeScript)
```
frontend/src/
├── components/
│   ├── calendar/         # 캘린더 컴포넌트
│   ├── common/          # 공통 UI 컴포넌트
│   └── layout/          # 레이아웃 컴포넌트
├── hooks/               # React 커스텀 훅
├── pages/               # 페이지 컴포넌트
│   ├── HomePage.tsx          # 뉴스 대시보드
│   ├── WatchlistPage.tsx     # 관심 종목
│   └── StockCalendarPage.tsx # 투자 캘린더
├── services/            # API 통신 계층
└── styles/              # 스타일 정의
```

## 🛠️ 기술 스택

### Backend
- **FastAPI** - 고성능 REST API 프레임워크
- **BigKinds API** - 뉴스 데이터 소스
- **OpenAI GPT-4 Turbo** - AI 요약 생성
- **ChromaDB** - 벡터 데이터베이스
- **DART API** - 금융감독원 전자공시시스템
- **KIS API** - 한국투자증권 주식 데이터

### Frontend
- **React 18** - 사용자 인터페이스
- **TypeScript** - 타입 안정성
- **Vite** - 빠른 개발 도구
- **Tailwind CSS** - 유틸리티 기반 CSS
- **Framer Motion** - 애니메이션 라이브러리

### Infrastructure
- **Python 3.8+**
- **Node.js 16+**
- **Docker** (선택사항)

## ⚙️ 설치 및 실행

### 1. 프로젝트 클론
```bash
git clone <repository-url>
cd big_proto
```

### 2. 환경 변수 설정
`.env` 파일을 확인하고 필요한 API 키들이 설정되어 있는지 확인하세요:

```env
# 필수 API 키
BIGKINDS_KEY=your_bigkinds_api_key
OPENAI_API_KEY=your_openai_api_key

# 선택적 API 키들
PERPLEXITY_API_KEY=your_perplexity_key
KIS_APP_KEY=your_kis_app_key
DART_API_KEY=your_dart_api_key
```

### 3. 백엔드 설정 및 실행
```bash
# Python 가상환경 생성 (권장)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 의존성 설치
pip install -r requirements.txt

# 서버 실행
python -m backend.server
```

서버는 기본적으로 `http://localhost:8000`에서 실행됩니다.

### 4. 프론트엔드 설정 및 실행
```bash
cd frontend

# 의존성 설치
npm install

# 개발 서버 실행
npm run dev
```

프론트엔드는 기본적으로 `http://localhost:5173`에서 실행됩니다.

## 🔑 API 키 발급 방법

### 필수 API 키

1. **BigKinds API 키**
   - [BigKinds 웹사이트](https://www.bigkinds.or.kr/) 접속
   - 회원가입 후 API 신청
   - 뉴스 데이터 접근을 위해 반드시 필요
   - **✅ 현재 설정 완료**: `254bec69-1c13-470f-904a-c4bc9e46cc80`

2. **OpenAI API 키**
   - [OpenAI 플랫폼](https://platform.openai.com/) 접속
   - 계정 생성 후 API 키 발급
   - AI 요약 기능을 위해 필요
   - **✅ 현재 설정 완료**: GPT-4 Turbo 모델 사용 가능

### 선택적 API 키

3. **DART API 키** (기업 공시 정보)
   - [DART 시스템](https://opendart.fss.or.kr/) 접속

4. **한국투자증권 API** (주식 데이터)
   - [KIS Developers](https://apiportal.koreainvestment.com/) 접속

## 📖 API 문서

서버 실행 후 다음 URL에서 API 문서를 확인할 수 있습니다:
- **Swagger UI**: `http://localhost:8000/api/docs`
- **ReDoc**: `http://localhost:8000/api/redoc`

### 주요 API 엔드포인트

#### 뉴스 관련 API
- `GET /api/news/latest` - 최신 뉴스 정보
- `POST /api/news/company` - 기업별 뉴스 타임라인
- `POST /api/news/ai-summary` - AI 뉴스 요약
- `GET /api/news/watchlist/suggestions` - 관심 종목 추천

#### 투자 캘린더 API
- `GET /api/stock-calendar/events` - 경제 일정 조회
- `POST /api/stock-calendar/analysis` - AI 분석

### BigKinds API 활용

#### 지원하는 필드들
프로젝트에서 사용하는 주요 뉴스 필드:
- `title` - 기사 제목
- `content` - 기사 본문
- `published_at` - 발행 일시
- `dateline` - 출고 시간
- `category` - 뉴스 카테고리
- `images` - 첨부 이미지
- `provider_link_page` - 원문 링크
- `provider_name` - 언론사명
- `byline` - 기자명

#### 주요 기능
1. **이슈 랭킹 (issue_ranking)**: 빅카인즈 가이드라인 준수한 실시간 이슈 분석
2. **인기 검색어 (query_rank)**: 기간별 인기 검색어 랭킹 조회
3. **카테고리 키워드 (today_category_keyword)**: 카테고리별 핫 키워드 분석
4. **뉴스 클러스터 검색**: news_cluster ID를 통한 관련 뉴스 그룹 조회
5. **서울경제신문 필터링**: 자동으로 서울경제 뉴스만 추출
6. **필드 선택**: 필요한 필드만 가져와서 성능 최적화
7. **올바른 요청 구조**: `{"access_key": "...", "argument": {...}}` 형식 준수
8. **에러 처리**: result 값 확인 및 안정적인 API 호출

## 🔍 주요 특징

### AI 요약 시스템
- **GPT-4 Turbo 모델 사용**: 최신 AI 기술로 정확한 요약 제공
- **세 가지 요약 방식**: 이슈, 인용, 수치 중심의 맞춤형 분석
- **실시간 처리**: 선택한 뉴스 기사를 즉시 분석

### 뉴스 데이터 처리
- **BigKinds API 통합**: 국내 주요 언론사 뉴스 데이터
- **고급 검색 기능**: 논리 연산자, 필터링, 중복 제거
- **실시간 업데이트**: 최신 뉴스 자동 수집 및 분석

### 사용자 경험
- **반응형 디자인**: 모바일/태블릿/데스크톱 지원
- **다크 모드**: 사용자 선호에 따른 테마 변경
- **부드러운 애니메이션**: Framer Motion 기반 상호작용

## 📁 프로젝트 구조 상세

### 백엔드 서비스 계층
- **BigKinds Client**: 뉴스 API 통합 및 데이터 처리
- **AI Summary Service**: GPT-4 기반 뉴스 요약 생성
- **Stock Calendar Service**: 경제 일정 및 공시 정보 관리
- **Logger Utility**: 체계적인 로그 관리 시스템

### 프론트엔드 컴포넌트
- **HomePage**: 최신 뉴스 탭 인터페이스
- **WatchlistPage**: 관심 종목 추적 및 AI 요약
- **StockCalendarPage**: 투자 캘린더 및 일정 관리
- **Common Components**: 재사용 가능한 UI 컴포넌트

## 🚀 배포 방법

### 개발 환경
```bash
# 백엔드
python -m backend.server

# 프론트엔드
cd frontend && npm run dev
```

### 프로덕션 환경
```bash
# 백엔드 빌드
pip install -r requirements.txt
python -m backend.server

# 프론트엔드 빌드
cd frontend
npm run build
npm run preview
```

### Docker 사용 (선택사항)
```bash
# Dockerfile을 사용한 컨테이너 빌드
docker build -t ai-nova .
docker run -p 8000:8000 -p 5173:5173 ai-nova
```

## 🐛 트러블슈팅

### 자주 발생하는 문제

1. **API 키 오류**
   ```
   Error: API 키가 필요합니다
   ```
   - `.env` 파일의 API 키 설정 확인
   - 환경 변수 로드 확인

2. **CORS 오류**
   ```
   Access-Control-Allow-Origin 오류
   ```
   - `backend/server.py`의 CORS 설정 확인
   - 프론트엔드 프록시 설정 확인

3. **의존성 오류**
   ```
   ModuleNotFoundError
   ```
   - `pip install -r requirements.txt` 재실행
   - `npm install` 재실행

### 로그 확인
```bash
# 백엔드 로그
tail -f logs/server.log

# 특정 서비스 로그
tail -f logs/api_news_ai_summary.log
```

## 📝 개발 가이드

### 새로운 API 엔드포인트 추가
1. `backend/api/routes/` 디렉토리에 라우터 파일 생성
2. `backend/server.py`에 라우터 등록
3. 프론트엔드에서 API 호출 코드 작성

### 새로운 페이지 추가
1. `frontend/src/pages/` 디렉토리에 페이지 컴포넌트 생성
2. `frontend/src/App.tsx`에 라우트 추가
3. 네비게이션 메뉴에 링크 추가

### 환경별 설정
- 개발: `.env.development`
- 테스트: `.env.test`
- 프로덕션: `.env.production`

## 📊 성능 최적화

### 백엔드 최적화
- **비동기 처리**: FastAPI의 async/await 활용
- **캐싱**: Redis 기반 API 응답 캐싱
- **연결 풀링**: 데이터베이스 연결 최적화

### 프론트엔드 최적화
- **코드 분할**: Vite의 동적 import 활용
- **이미지 최적화**: WebP 형식 및 lazy loading
- **번들 최적화**: Tree shaking 및 압축

## 🔐 보안 고려사항

### API 보안
- **API 키 관리**: 환경 변수로 안전한 저장
- **CORS 설정**: 허용된 도메인만 접근 가능
- **요청 제한**: Rate limiting 구현

### 데이터 보안
- **민감 정보 암호화**: API 키 및 토큰 보호
- **입력 검증**: SQL Injection 및 XSS 방지
- **HTTPS 사용**: 프로덕션 환경에서 필수

## 📞 지원 및 연락처

### 개발팀 연락처
- **서울경제신문 디지털혁신팀**
- 이메일: digital@sedaily.com
- 전화: 02-3147-2000

### 기술 지원
- GitHub Issues를 통한 버그 리포트
- 이메일을 통한 기술 문의
- 정기 업데이트 및 유지보수

## 📄 라이센스

Copyright © 2025 서울경제신문. All rights reserved.

이 프로젝트는 서울경제신문의 저작물이며, 상업적 사용을 위해서는 별도의 라이센스가 필요합니다.

---

## 📈 버전 히스토리

### v0.1.0 (2025-01-XX)
- 초기 프로젝트 구조 설정
- BigKinds API 통합
- 기본 뉴스 대시보드 구현

### v0.2.0 (현재)
- GPT-4 Turbo AI 요약 기능 추가
- 관심 종목 추적 시스템 구현
- UI/UX 개선 및 최적화
- 프로젝트 구조 정리 및 문서화

---

**🎯 이 플랫폼을 통해 서울경제신문의 뉴스 분석 역량을 한 단계 업그레이드하세요!**