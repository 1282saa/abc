# AI NOVA - 빠른 시작 가이드

## 🚀 즉시 실행하기

### 1단계: 백엔드 실행
```bash
cd /Users/yeong-gwang/Desktop/work/서울경제신문/빅카인즈/big_proto

# Python 의존성 설치 (최초 1회)
pip install -r requirements.txt

# 백엔드 서버 실행
python -m backend.server
```
✅ 서버가 `http://localhost:8000`에서 실행됩니다.

### 2단계: 프론트엔드 실행
```bash
cd frontend

# Node.js 의존성 설치 (최초 1회)
npm install

# 개발 서버 실행
npm run dev
```
✅ 웹앱이 `http://localhost:5173`에서 실행됩니다.

## 🔑 설정된 API 키들
✅ **BigKinds API**: 이미 설정됨
✅ **OpenAI GPT-4 Turbo**: 이미 설정됨
✅ **기타 API들**: 모두 설정 완료

## 📱 주요 기능 테스트
1. **홈페이지**: `http://localhost:5173` - 최신 뉴스 대시보드
2. **관심종목**: 상단 메뉴 → "관심 종목" - AI 요약 기능 포함
3. **투자캘린더**: 상단 메뉴 → "투자 캘린더" - 경제 일정

## 📖 API 문서 확인
- Swagger UI: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`

## 🛠️ 문제 해결
- **포트 충돌**: 다른 서버가 실행 중이면 포트를 변경하세요
- **의존성 오류**: `pip install -r requirements.txt` 재실행
- **프론트엔드 오류**: `npm install` 재실행

## 📧 연락처
문제가 발생하면 digital@sedaily.com으로 연락주세요.