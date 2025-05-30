# AI NOVA 시작 가이드

이 문서는 AI NOVA 시스템의 설치 및 실행 방법을 안내합니다.

## 1. 요구사항

AI NOVA를 실행하기 위해 필요한 시스템 요구사항:

- Python 3.8 이상
- Node.js 14 이상 (프론트엔드 추가 개발 시)
- Redis (선택사항 - 캐싱에 사용)

## 2. 환경 설정

### 2.1 저장소 클론

```bash
git clone [repository-url]
cd ainova
```

### 2.2 환경변수 설정

1. `config` 디렉토리에서 `.env.example` 파일을 복사하여 `.env` 파일 생성:

```bash
cp config/.env.example config/.env
```

2. `.env` 파일을 수정하여 필요한 설정 입력:

```
# API 인증
BIGKINDS_API_KEY=your_api_key_here

# 데이터베이스 설정
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ainova
DB_USER=ainova_user
DB_PASSWORD=your_db_password_here

# 서버 설정
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
DEBUG=True

# 로깅 설정
LOG_LEVEL=INFO

# 캐싱 설정
CACHE_HOST=localhost
CACHE_PORT=6379
CACHE_TTL=3600
```

### 2.3 초기 설정 실행

다음 명령어로 필요한 의존성을 설치하고 초기 설정을 완료합니다:

```bash
./run.sh setup
```

이 명령어는 다음 작업을 자동으로 수행합니다:
- 가상환경 생성
- 필요한 패키지 설치
- 캐시 및 로그 디렉토리 생성

## 3. 애플리케이션 실행

### 3.1 백엔드 서버 실행

```bash
./run.sh backend
```

이 명령어는 FastAPI 기반의 백엔드 서버를 8000번 포트에서 실행합니다.

### 3.2 프론트엔드 실행

```bash
./run.sh frontend
```

이 명령어는 Streamlit 기반의 프론트엔드 인터페이스를 8501번 포트에서 실행합니다.

### 3.3 브라우저에서 접속

- 백엔드 API 문서: http://localhost:8000/docs
- 프론트엔드 대시보드: http://localhost:8501

## 4. API 사용 예제

### 4.1 오늘의 이슈 조회

```bash
curl -X GET "http://localhost:8000/api/today-issues?date=2025-05-01&top_n=5"
```

### 4.2 뉴스 검색

```bash
curl -X POST "http://localhost:8000/api/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "윤석열",
    "start_date": "2025-05-01",
    "end_date": "2025-05-10",
    "max_results": 100
  }'
```

### 4.3 이슈 분석

```bash
curl -X POST "http://localhost:8000/api/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "윤석열",
    "start_date": "2025-05-01",
    "end_date": "2025-05-10",
    "max_results": 100
  }'
```

## 5. 디렉토리 구조

```
ainova/
├── app/                # 애플리케이션
│   ├── backend/        # 백엔드 서버
│   └── frontend/       # 프론트엔드 인터페이스
├── config/             # 설정 파일
├── docs/               # 문서
├── src/                # 소스 코드
│   ├── api/            # API 클라이언트
│   ├── core/           # 핵심 분석 엔진
│   ├── modules/        # 기능별 모듈
│   └── utils/          # 유틸리티 함수
├── tests/              # 테스트 코드
├── .env.example        # 환경변수 예제
├── README.md           # 프로젝트 설명
└── requirements.txt    # 의존성 목록
```

## 6. 문제 해결

### 6.1 백엔드 서버가 실행되지 않는 경우

- API 키가 올바르게 설정되었는지 확인
- 필요한 환경변수가 모두 설정되었는지 확인
- 로그 파일 확인: `logs/ainova.log`

### 6.2 API 응답 오류

- 빅카인즈 API 상태 확인
- API 호출 제한 초과 여부 확인
- API 로그 확인: `logs/api/api_error.log`

## 7. 추가 자원

- [빅카인즈 API 문서](https://bigkinds.or.kr/api/document)
- [프로젝트 위키](project-wiki-url)
- [이슈 트래커](issue-tracker-url)