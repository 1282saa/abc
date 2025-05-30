# AI NOVA

키워드 중심 뉴스 클러스터링 및 종합 요약 시스템

## 프로젝트 개요

AI NOVA는 빅카인즈 API를 기반으로 한 이슈 중심의 뉴스 분석 및 요약 서비스입니다. 
본 시스템은 개별 뉴스를 이슈별로 클러스터링하고, 이슈의 맥락과 흐름을 분석하여 사용자에게 종합적인 뉴스 인사이트를 제공합니다.

## 주요 기능

- 빅카인즈 API 연동 및 데이터 처리
- 이슈 맵 생성 및 시각화
- 이슈 흐름 분석 및 시각화
- 이슈 요약 및 인사이트 생성
- 서울경제 웹사이트 및 모바일 앱 통합 인터페이스

## 설치 및 실행

### 요구사항

- Python 3.8+
- Node.js 14+

### 설치

```bash
# 백엔드 설치
cd app/backend
pip install -r requirements.txt

# 프론트엔드 설치
cd ../frontend
npm install
```

### 환경 설정

config 디렉토리의 `.env.example` 파일을 `.env`로 복사하고 필요한
API 키와 설정을 입력하세요.

### 실행

```bash
# 백엔드 실행
cd app/backend
python server.py

# 프론트엔드 실행
cd ../frontend
npm run dev
```

## 프로젝트 구조

- `src/`: 핵심 소스 코드
  - `api/`: 빅카인즈 API 클라이언트
  - `core/`: 핵심 분석 엔진
  - `modules/`: 기능별 모듈
  - `utils/`: 유틸리티 함수
- `app/`: 애플리케이션
  - `backend/`: 백엔드 서버
  - `frontend/`: 프론트엔드 인터페이스
- `docs/`: 문서
- `tests/`: 테스트 코드
- `config/`: 설정 파일

## 라이센스

Copyright © 2025 서울경제신문. All rights reserved.