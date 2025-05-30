# AI NOVA 콘텐츠 제작자 지원 기능

AI NOVA 시스템의 콘텐츠 제작자 지원 모듈은 빅카인즈 API를 활용하여 콘텐츠 제작자(저널리스트, 마케터, 인플루언서 등)가 효율적으로 콘텐츠를 기획하고 제작할 수 있도록 지원합니다.

## 주요 기능

1. **이슈 리서치**: 빅카인즈 API를 활용해 키워드 기반 이슈 분석을 수행합니다.
   - 이슈 클러스터링
   - 이슈 흐름 분석
   - 종합 요약

2. **콘텐츠 기획**: 분석된 이슈를 바탕으로 콘텐츠 기획을 지원합니다.
   - 주제 제안
   - 콘텐츠 구조 제안
   - 핵심 인용구 추출

3. **자료 생성**: 콘텐츠에 활용할 수 있는 시각 자료를 자동으로 생성합니다.
   - 인용구 이미지
   - 타임라인 차트
   - 통계 차트
   - 관점 비교 차트

4. **팩트 체크**: 콘텐츠에 포함된 사실을 자동으로 검증합니다.
   - 신뢰도 평가
   - 관련 뉴스 연결
   - 출처 확인

5. **내보내기**: 콘텐츠 패키지를 다양한 형식으로 내보낼 수 있습니다.
   - JSON
   - 마크다운
   - HTML

## 시스템 구성

- **백엔드**: FastAPI 기반의 RESTful API
- **프론트엔드**: Streamlit 기반의 웹 인터페이스
- **워크플로우 관리**: 5단계 콘텐츠 제작 워크플로우 관리 시스템

## 설치 및 실행

### 요구사항

- Python 3.9 이상
- 빅카인즈 API 키

### 환경 설정

1. 환경 변수 설정:
   ```
   # .env 파일 생성
   BIGKINDS_API_KEY=your_api_key
   SERVER_HOST=0.0.0.0
   SERVER_PORT=8000
   ```

2. 패키지 설치:
   ```bash
   pip install -r requirements.txt
   ```

### 백엔드 실행

```bash
cd app/backend
python server.py
```

### 프론트엔드 실행

```bash
cd app/frontend
streamlit run content_creator_app.py
```

## 사용 방법

1. 프론트엔드 접속: http://localhost:8501
2. 이슈 리서치 페이지에서 새 워크플로우 생성
3. 검색어와 기간 설정 후 이슈 분석 실행
4. 단계별로 콘텐츠 제작 워크플로우 진행
5. 최종 결과물 내보내기

## API 엔드포인트

콘텐츠 제작자 API는 `/content-creator` 경로 아래에 다양한 엔드포인트를 제공합니다:

- **워크플로우 관리**:
  - `POST /content-creator/workflows` - 새 워크플로우 생성
  - `GET /content-creator/workflows` - 워크플로우 목록 조회
  - `GET /content-creator/workflows/{workflow_id}` - 워크플로우 상세 조회
  - `PATCH /content-creator/workflows/{workflow_id}` - 워크플로우 업데이트
  - `DELETE /content-creator/workflows/{workflow_id}` - 워크플로우 삭제
  - `POST /content-creator/workflows/{workflow_id}/execute` - 워크플로우 단계 실행

- **템플릿 관리**:
  - `POST /content-creator/templates` - 워크플로우를 템플릿으로 저장
  - `GET /content-creator/templates` - 템플릿 목록 조회

- **콘텐츠 도구**:
  - `POST /content-creator/tools/content-brief` - 콘텐츠 개요 생성
  - `POST /content-creator/tools/quote-image` - 인용구 이미지 생성
  - `POST /content-creator/tools/timeline-image` - 타임라인 이미지 생성
  - `POST /content-creator/tools/stats-image` - 통계 차트 이미지 생성
  - `POST /content-creator/tools/verify-facts` - 사실 검증
  - `POST /content-creator/tools/export-package` - 콘텐츠 패키지 내보내기

## 결과물 다운로드

생성된 파일은 `/output` 디렉토리에 저장되며, 다음 경로를 통해 다운로드할 수 있습니다:

```
GET /download/{file_path}
```