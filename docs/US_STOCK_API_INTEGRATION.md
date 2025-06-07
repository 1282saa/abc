# US Stock API Integration

## 개요

AI NOVA 프로젝트에 미국 주식 시장 데이터를 제공하는 US Stock API Client가 통합되었습니다. 이 클라이언트는 실시간 주가, 실적 캘린더, 배당 일정, 경제 지표 등을 제공합니다.

## 기능

### 1. 실시간 주가 데이터
- 개별 종목 현재가 조회
- 여러 종목 동시 조회 (최대 20개)
- 주요 미국 주식 현재가 (AAPL, MSFT, GOOGL 등)

### 2. 투자 캘린더 이벤트
- 실적 발표 일정
- 배당 지급 일정
- 미국 경제 지표 발표 일정

### 3. 시장 정보
- 미국 시장 개장/폐장 상태
- 시장 시간 정보

## API 데이터 소스

### 1차 데이터 소스: Alpha Vantage API
- 실시간 주가 데이터
- 실적 캘린더 (향후 구현)
- 환경 변수: `ALPHA_VANTAGE_API_KEY`

### 2차 데이터 소스: Yahoo Finance API  
- Alpha Vantage 실패 시 대체 데이터
- 무료 API 사용

### 3차 데이터 소스: Mock Data
- API 실패 시 대체 데이터
- 개발 및 테스트 환경용

## 새로운 API 엔드포인트

### 주식 현재가
```
GET /api/stock-calendar/us-stocks/quote/{symbol}
GET /api/stock-calendar/us-stocks/quotes?symbols=AAPL,MSFT,GOOGL
GET /api/stock-calendar/us-stocks/major
```

### 투자 캘린더
```
GET /api/stock-calendar/us-stocks/earnings
GET /api/stock-calendar/us-stocks/dividends  
GET /api/stock-calendar/us-stocks/economic-calendar
```

### 시장 정보
```
GET /api/stock-calendar/us-stocks/market-status
```

### AI 분석
```
POST /api/stock-calendar/ai-analysis/us-stock
```

## 캘린더 통합

### 메인 캘린더 API 변경사항
기존 `/api/stock-calendar/events` 엔드포인트에 미국 주식 이벤트가 자동으로 포함됩니다:

- `market_type=us`: 미국 시장 이벤트만 조회
- `market_type=all` 또는 미지정: 모든 시장 이벤트 조회
- `include_earnings=true`: 실적 발표 이벤트 포함

### 새로운 이벤트 타입
- **earnings**: 실적 발표 (미국)
- **dividend**: 배당 지급 (미국)  
- **economic**: 경제 지표 발표 (미국)

## 환경 설정

### 필수 환경 변수
```bash
# Alpha Vantage API (선택사항 - 없으면 Mock 데이터 사용)
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_api_key
```

### Alpha Vantage API 키 발급
1. [Alpha Vantage](https://www.alphavantage.co/support/#api-key) 방문
2. 무료 API 키 신청 (분당 5회 제한)
3. 환경 변수에 설정

## 사용 예시

### Python 코드
```python
from backend.services.us_stock_api_client import us_stock_api_client

async def get_apple_stock():
    async with us_stock_api_client as client:
        quote = await client.get_stock_quote("AAPL")
        print(f"AAPL: ${quote['price']:.2f} ({quote['change_percent']}%)")

async def get_earnings_calendar():
    async with us_stock_api_client as client:
        from datetime import date, timedelta
        start = date.today()
        end = start + timedelta(days=30)
        
        earnings = await client.get_earnings_calendar(start, end)
        for event in earnings:
            print(f"{event['company_name']} - {event['report_date']}")
```

### HTTP 요청
```bash
# 애플 주식 현재가
curl "http://localhost:8000/api/stock-calendar/us-stocks/quote/AAPL"

# 여러 종목 동시 조회
curl "http://localhost:8000/api/stock-calendar/us-stocks/quotes?symbols=AAPL,MSFT,GOOGL"

# 실적 캘린더
curl "http://localhost:8000/api/stock-calendar/us-stocks/earnings?days=30"

# 통합 캘린더 (미국 이벤트 포함)
curl "http://localhost:8000/api/stock-calendar/events?start_date=2025-06-01&end_date=2025-06-30&market_type=us"
```

## 프론트엔드 연동

### 새로운 Hook 추가 권장
```typescript
// hooks/useUSStocks.ts
export const useUSStocks = () => {
  const getMajorStocks = async () => {
    return api.get('/api/stock-calendar/us-stocks/major');
  };
  
  const getStockQuote = async (symbol: string) => {
    return api.get(`/api/stock-calendar/us-stocks/quote/${symbol}`);
  };
  
  return { getMajorStocks, getStockQuote };
};
```

### 캘린더 컴포넌트 업데이트
기존 캘린더 컴포넌트는 자동으로 미국 주식 이벤트를 표시합니다:
- 🇺🇸 아이콘으로 미국 이벤트 구분
- 실적 발표: 파란색 배지
- 배당: 초록색 배지  
- 경제 지표: 보라색 배지

## 테스트

### 테스트 실행
```bash
cd /Users/yeong-gwang/Desktop/work/서울경제신문/빅카인즈/big_proto
python test_us_stock_api.py
```

### 예상 결과
- ✅ 모든 API 기능 정상 작동 확인
- 📊 Mock 데이터로 실적/배당 캘린더 생성
- 🔄 실제 API 연동 준비 완료

## 성능 고려사항

### API 호출 제한
- Alpha Vantage: 분당 5회 (무료 플랜)
- 자동 속도 제한 (12초 간격)
- 실패 시 Yahoo Finance 자동 전환
- 최종 실패 시 Mock 데이터 반환

### 캐싱 전략
- 주가 데이터: 1분 캐싱 권장
- 캘린더 데이터: 1시간 캐싱 권장
- 경제 지표: 24시간 캐싱 권장

## 문제 해결

### 일반적인 문제
1. **API 호출 실패**: Mock 데이터로 자동 대체
2. **속도 제한**: 자동으로 대기 후 재시도
3. **환경 변수 없음**: Mock 모드로 자동 전환

### 로그 확인
```bash
tail -f logs/services_us_stock_api.log
```

### 디버그 모드
```python
import logging
logging.getLogger("services.us_stock_api").setLevel(logging.DEBUG)
```

## 향후 개선사항

### 단기 개선
- [ ] Alpha Vantage Earnings Calendar API 연동
- [ ] 실시간 WebSocket 연결
- [ ] 더 많은 경제 지표 추가

### 중기 개선  
- [ ] 기술적 분석 지표 추가
- [ ] 옵션 만료일 캘린더
- [ ] FOMC 회의 일정 자동 연동

### 장기 개선
- [ ] 글로벌 주식 시장 확장 (유럽, 아시아)
- [ ] 실시간 뉴스 연동
- [ ] AI 기반 이벤트 중요도 평가

## 관련 파일

### 새로 생성된 파일
- `backend/services/us_stock_api_client.py`: 메인 클라이언트
- `test_us_stock_api.py`: 테스트 스크립트
- `docs/US_STOCK_API_INTEGRATION.md`: 이 문서

### 수정된 파일
- `backend/api/routes/stock_calendar_routes.py`: API 엔드포인트 추가
- 기존 캘린더 로직에 미국 주식 이벤트 통합

## 지원

문제가 발생하거나 추가 기능이 필요한 경우:
1. 테스트 스크립트 실행으로 기본 기능 확인
2. 로그 파일 확인
3. Mock 데이터 모드로 기본 기능 테스트
4. 필요시 Alpha Vantage API 키 재발급

---

**작성일**: 2025-06-04  
**작성자**: AI Assistant  
**버전**: 1.0.0