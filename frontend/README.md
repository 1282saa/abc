# 빅카인즈 뉴스 분석 시스템 - 프론트엔드

이 디렉토리는 빅카인즈 API를 활용한 뉴스 분석 시스템의 프론트엔드 코드를 포함합니다.

## 기술 스택

- **React 18** - 사용자 인터페이스 라이브러리
- **TypeScript** - 타입 안정성을 위한 JavaScript 확장
- **Vite** - 빠른 개발 및 빌드 도구
- **Tailwind CSS** - 유틸리티 기반 CSS 프레임워크
- **Framer Motion** - 애니메이션 라이브러리

## 디렉토리 구조

```
frontend/
├── public/               # 정적 파일
├── src/
│   ├── animations/       # 애니메이션 설정
│   ├── components/       # 리액트 컴포넌트
│   │   ├── common/          # 공통 컴포넌트
│   │   │   ├── LoadingSpinner.tsx
│   │   │   ├── ErrorMessage.tsx
│   │   │   ├── Navigation.tsx
│   │   │   └── RelatedQuestions.tsx  # 연관 질문 컴포넌트
│   │   ├── forms/           # 폼 컴포넌트
│   │   │   └── SearchForm.tsx       # 검색 폼
│   │   ├── layout/          # 레이아웃 컴포넌트
│   │   │   └── Layout.tsx
│   │   ├── modals/          # 모달 컴포넌트
│   │   │   └── NewsDetailModal.tsx  # 뉴스 상세 모달
│   │   └── news/            # 뉴스 관련 컴포넌트
│   │       └── NewsArticleCard.tsx  # 뉴스 기사 카드
│   ├── hooks/            # 커스텀 훅
│   ├── pages/            # 페이지 컴포넌트
│   │   ├── HomePage.tsx           # 홈 페이지
│   │   ├── SearchPage.tsx         # 검색 페이지
│   │   ├── WatchlistPage.tsx      # 관심 종목 페이지
│   │   └── StockCalendarPage.tsx  # 경제 캘린더 페이지
│   ├── styles/           # 스타일 정의
│   ├── App.tsx           # 앱 컴포넌트
│   └── main.tsx          # 엔트리 포인트
├── .eslintrc.json        # ESLint 설정
├── tailwind.config.js    # Tailwind CSS 설정
├── tsconfig.json         # TypeScript 설정
└── vite.config.ts        # Vite 설정
```

## 주요 기능

### 뉴스 검색

- **SearchPage.tsx** - 검색 페이지 구현
- **SearchForm.tsx** - 검색 폼 컴포넌트
- **NewsArticleCard.tsx** - 검색 결과 표시

### 연관 질문

- **RelatedQuestions.tsx** - 연관 질문 컴포넌트
  - 다양한 유형의 질문 제공 (기본, 정교화, 확장, 제외, 복합)
  - 질문 클릭 시 새로운 검색 실행

### 뉴스 상세 보기

- **NewsDetailModal.tsx** - 뉴스 상세 정보 모달
  - 기사 원문 링크 제공
  - 이미지 및 메타데이터 표시

## 설치 및 실행

1. 필요한 패키지 설치:

   ```bash
   npm install
   ```

2. 개발 서버 실행:

   ```bash
   npm run dev
   ```

3. 프로덕션 빌드:
   ```bash
   npm run build
   ```

## API 통신

프론트엔드는 Vite의 프록시 기능을 사용하여 백엔드 API와 통신합니다. 이는 `vite.config.ts` 파일에 설정되어 있습니다:

```typescript
server: {
  port: 5173,
  host: true,
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
      secure: false,
    },
  },
}
```

## 새로 구현된 연관 질문 기능

연관 질문 기능은 다음과 같이 구현되어 있습니다:

1. **SearchPage.tsx**에서 검색어를 입력하고 검색 결과를 표시
2. **RelatedQuestions.tsx** 컴포넌트가 검색어를 기반으로 연관 질문 목록을 가져옴
3. 사용자가 연관 질문을 클릭하면 해당 질문의 쿼리로 새로운 검색 실행
4. 검색 결과와 함께 연관 질문이 지속적으로 표시됨

## 스타일링

이 프로젝트는 Tailwind CSS를 사용하여 스타일링되어 있습니다:

```jsx
// 예시: RelatedQuestions.tsx의 컴포넌트 스타일링
<motion.div
  key={index}
  initial={{ opacity: 0, y: 10 }}
  animate={{ opacity: 1, y: 0 }}
  transition={{ duration: 0.3, delay: index * 0.1 }}
  whileHover={{ scale: 1.01 }}
  className="p-3 bg-white dark:bg-gray-800 rounded-lg shadow-sm hover:shadow-md border border-gray-200 dark:border-gray-700 transition-all cursor-pointer flex items-center"
  onClick={() => onQuestionClick(question)}
>
  {/* 컴포넌트 내용 */}
</motion.div>
```

## 다크 모드

다크 모드는 Tailwind CSS의 다크 모드 기능을 사용하여 구현되어 있습니다:

```jsx
// App.tsx
useEffect(() => {
  if (theme === "dark") {
    document.documentElement.classList.add("dark");
  } else {
    document.documentElement.classList.remove("dark");
  }
}, [theme]);
```

## 문제 해결

### API 연결 문제

- 백엔드 서버가 실행 중인지 확인 (`http://localhost:8000`)
- 네트워크 요청을 브라우저 개발자 도구에서 모니터링
- Vite 프록시 설정 확인

### 컴포넌트 렌더링 문제

- React 개발자 도구를 사용하여 컴포넌트 트리 확인
- props 전달이 올바르게 이루어지는지 확인
- state 업데이트 및 효과 실행 순서 확인
