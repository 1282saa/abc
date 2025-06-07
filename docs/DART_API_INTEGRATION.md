# DART API 클라이언트 통합 가이드

이 문서는 AI NOVA 프로젝트에 통합된 DART(전자공시시스템) API 클라이언트의 사용법과 기능을 설명합니다.

## 개요

DART API 클라이언트는 한국의 전자공시시스템(DART)에서 제공하는 공시 정보를 조회하여 주식 캘린더에 실제 공시 이벤트를 통합합니다. 실제 API 키가 없는 경우 목업 데이터를 자동으로 제공하는 fallback 기능을 포함합니다.

## 파일 구조

```
backend/services/
├── dart_api_client.py          # DART API 클라이언트 구현
├── kis_api_client.py           # 한국투자증권 API 클라이언트 (기존)
└── __init__.py                 # 서비스 패키지 초기화

backend/api/routes/
└── stock_calendar_routes.py    # 주식 캘린더 API (DART 통합)

test_dart_api.py               # DART API 단독 테스트
test_stock_calendar_with_dart.py # 통합 테스트
```

## 주요 기능

### 1. DART API 클라이언트 (`DARTAPIClient`)

#### 기본 메서드

- **`get_disclosure_list()`**: 공시 검색
- **`get_company_info()`**: 기업 개황 조회
- **`get_recent_disclosures()`**: 최근 중요 공시 조회
- **`search_company_by_name()`**: 회사명으로 기업 검색
- **`get_upcoming_disclosure_events()`**: 향후 공시 이벤트 조회 (캘린더용)

#### Mock 데이터 Fallback

API 키가 없거나 API 호출이 실패할 경우 자동으로 목업 데이터를 제공:

- 삼성전자, SK하이닉스, NAVER 등 주요 기업의 샘플 공시 정보
- 실제 API 응답과 동일한 데이터 구조
- 로그를 통한 목업 데이터 사용 알림

### 2. 주식 캘린더 통합

#### 새로운 API 엔드포인트

**주요 캘린더 API**
- `GET /api/stock-calendar/events` - 전체 이벤트 조회 (DART 포함)
- `GET /api/stock-calendar/upcoming-events` - 예정된 이벤트

**DART 전용 API**
- `GET /api/stock-calendar/dart/disclosures` - DART 공시 정보
- `GET /api/stock-calendar/dart/recent` - 최근 공시
- `GET /api/stock-calendar/dart/company/{corp_code}` - 기업 정보
- `GET /api/stock-calendar/dart/search/company` - 기업 검색

#### 이벤트 유형 추가

기존 이벤트 유형에 "disclosure" (공시) 추가:
- earnings (실적발표)
- dividend (배당)
- holiday (휴장일)
- ipo (IPO)
- economic (경제지표)
- split (액면분할)
- **disclosure (공시)** ← 새로 추가

## 환경 설정

### 1. API 키 설정

`.env` 파일에 DART API 키 추가:

```env
# 주식/경제 데이터 API 키
DART_API_KEY=9723d7cc3870c2445ced298eaaeedc0c4e06054a
```

### 2. 의존성

필요한 Python 패키지:
```
aiohttp>=3.8.0
python-dotenv>=0.19.0
fastapi>=0.68.0
```

## 사용 예제

### 1. 기본 사용법

```python
from backend.services.dart_api_client import dart_api_client

# 비동기 컨텍스트에서 사용
async with dart_api_client as client:
    # 최근 7일간 중요 공시 조회
    recent_disclosures = await client.get_recent_disclosures(
        corp_cls="Y",  # 유가증권
        days=7,
        important_only=True
    )
    
    # 기업 검색
    companies = await client.search_company_by_name("삼성")
    
    # 기업 정보 조회
    company_info = await client.get_company_info("00126380")  # 삼성전자
```

### 2. API 엔드포인트 호출

```bash
# 전체 캘린더 이벤트 (DART 포함)
curl "http://localhost:8000/api/stock-calendar/events?start_date=2025-06-01&end_date=2025-06-30"

# DART 공시만 조회
curl "http://localhost:8000/api/stock-calendar/dart/disclosures?start_date=2025-06-01&end_date=2025-06-30&corp_cls=Y&important_only=true"

# 기업 검색
curl "http://localhost:8000/api/stock-calendar/dart/search/company?company_name=삼성"

# 최근 공시
curl "http://localhost:8000/api/stock-calendar/dart/recent?corp_cls=Y&days=7&important_only=true"
```

### 3. 응답 데이터 구조

**공시 이벤트 형식:**
```json
{
  "id": "disclosure_20250604000001",
  "title": "분기보고서 (제54기 1분기)",
  "date": "2025-06-04",
  "eventType": "disclosure",
  "stockCode": "005930",
  "stockName": "삼성전자",
  "description": "삼성전자 - 분기보고서 (제54기 1분기)",
  "marketType": "domestic",
  "corp_cls": "Y",
  "disclosure_url": "http://dart.fss.or.kr/dsaf001/main.do?rcpNo=20250604000001"
}
```

**기업 정보 형식:**
```json
{
  "success": true,
  "data": {
    "corp_name": "삼성전자",
    "corp_name_eng": "SAMSUNG ELECTRONICS CO., LTD.",
    "stock_name": "삼성전자",
    "stock_code": "005930",
    "ceo_nm": "한종희",
    "corp_cls": "Y",
    "adres": "경기도 수원시 영통구 삼성로 129",
    "hm_url": "http://www.samsung.com/sec",
    "ir_url": "http://www.samsung.com/sec/ir"
  }
}
```

## 테스트

### 1. DART API 단독 테스트

```bash
cd /Users/yeong-gwang/Desktop/work/서울경제신문/빅카인즈/big_proto
python test_dart_api.py
```

### 2. 주식 캘린더 통합 테스트

```bash
# 서버 실행 (다른 터미널에서)
python -m backend.server

# 테스트 실행
python test_stock_calendar_with_dart.py
```

## 에러 처리

### 1. API 키 없음

```
WARNING: DART API 키가 설정되지 않았습니다. 목업 데이터를 사용합니다.
```
→ 목업 데이터로 자동 fallback

### 2. API 호출 실패

```
ERROR: DART API 공시검색 실패: Connection timeout
```
→ 빈 결과 또는 목업 데이터 반환

### 3. 잘못된 파라미터

```
HTTP 400: 날짜 형식 오류: time data '2025-13-01' does not match format '%Y-%m-%d'
```
→ 명확한 오류 메시지 제공

## 로깅

DART API 관련 로그는 다음 위치에 저장됩니다:

- **로거명**: `services.dart_api`
- **로그 파일**: `logs/services_dart_api.log` (설정된 경우)
- **로그 레벨**: INFO (성공), WARNING (fallback), ERROR (실패)

## 중요 공시 키워드

다음 키워드를 포함한 공시를 중요 공시로 분류합니다:

- 실적발표, 실적공시
- 분기보고서, 반기보고서, 사업보고서
- 임시주주총회, 정기주주총회
- 배당, 유상증자, 무상증자
- 합병, 분할, 인수, 매각
- 대규모내부거래, 주요사항보고
- 공시정정, 특별관계자거래

## 성능 최적화

### 1. 캐싱

- 동일한 날짜 범위 요청에 대한 결과 캐싱 가능
- 기업 정보는 상대적으로 변경이 적어 캐싱에 적합

### 2. 요청 제한

- DART API는 분당 요청 수 제한이 있을 수 있음
- 대량 요청 시 적절한 지연(delay) 추가 권장

### 3. 배치 처리

- 여러 기업의 정보를 한 번에 조회할 때는 순차 처리
- 에러 발생 시에도 다른 요청 계속 처리

## 향후 개선 사항

1. **캐싱 시스템**: Redis 또는 메모리 캐시 도입
2. **실시간 알림**: 웹소켓을 통한 신규 공시 알림
3. **필터링 개선**: 더 세밀한 공시 분류 및 필터링
4. **성능 최적화**: 병렬 처리 및 요청 큐 관리
5. **데이터 분석**: 공시 트렌드 및 통계 기능

## 문의

DART API 통합 관련 문의는 개발팀에 연락해주세요.

- 개발자: Claude Code
- 생성일: 2025년 6월 4일
- 버전: 1.0.0