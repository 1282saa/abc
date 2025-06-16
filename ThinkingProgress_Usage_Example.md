# ThinkingProgress 컴포넌트 사용법

## 개요
`ThinkingProgress` 컴포넌트는 AI 요약 생성 과정에서 ChatGPT 스타일의 사고 과정을 시각적으로 표현하는 컴포넌트입니다. 기존의 단순한 진행률 표시를 대체하여 더 자연스럽고 사용자 친화적인 경험을 제공합니다.

## 컴포넌트 경로
```
/Users/yeong-gwang/Documents/work/서울경제신문/빅카인즈/big_proto/frontend/src/components/ai/ThinkingProgress.tsx
```

## Import 방법
```typescript
import ThinkingProgress from "../components/ai/ThinkingProgress";
```

## Props 인터페이스
```typescript
interface ThinkingProgressProps {
  step: string;           // 현재 진행 단계 메시지
  progress: number;       // 진행률 (0-100)
  type?: "thinking" | "content" | "complete" | "error";  // 표시 타입
  isGenerating: boolean;  // 생성 중 여부
}
```

## 사용 예시

### 1. CategoryDetailPage.tsx에서의 사용
```typescript
// import 추가
import ThinkingProgress from "../components/ai/ThinkingProgress";

// 기존 코드 교체
{isGeneratingSummary && (
  <div className="py-6 space-y-6">
    {/* ThinkingProgress 컴포넌트 사용 */}
    <ThinkingProgress
      step={streamingStep}
      progress={streamingProgress}
      type="thinking"
      isGenerating={isGeneratingSummary}
    />
    
    {/* 나머지 스트리밍 콘텐츠... */}
  </div>
)}
```

### 2. WatchlistPage.tsx에서의 사용
```typescript
// import 추가
import ThinkingProgress from "../components/ai/ThinkingProgress";

// 기존 코드 교체
{isGenerating && (
  <div className="space-y-4">
    <ThinkingProgress
      step={streamingStep}
      progress={streamingProgress}
      type={streamingType === "thinking" ? "thinking" : "content"}
      isGenerating={isGenerating}
    />
    
    {/* 나머지 스트리밍 콘텐츠... */}
  </div>
)}
```

## 주요 기능

### 1. 자동 메시지 변환
원본 step 메시지를 사용자 친화적인 메시지로 자동 변환:
- "뉴스 데이터 수집" → "관련 뉴스 기사들을 찾고 있어요... 🔍"
- "AI 종합 인사이트 도출" → "모든 정보를 종합해서 의미있는 패턴을 찾고 있어요... 🤖"

### 2. 진행률 시각화
- 그라데이션 진행률 바
- 숫자와 시각적 표현의 조합

### 3. 애니메이션 효과
- 회전하는 아이콘
- 점프하는 도트 애니메이션
- 부드러운 전환 효과

### 4. 다크 모드 지원
- 자동 다크/라이트 모드 감지
- 일관된 디자인 시스템

## Type별 표시 스타일

### thinking
- 파란색 그라데이션
- 회전하는 아이콘
- 점프하는 도트 애니메이션

### content
- 파란색 그라데이션 (thinking과 동일)
- 콘텐츠 생성에 특화된 메시지

### complete
- 초록색 성공 스타일
- 체크 아이콘
- 완료 메시지

### error
- 빨간색 오류 스타일
- 경고 아이콘
- 오류 메시지

## 기존 코드에서 교체된 부분

### Before (기존 코드)
```typescript
{/* 진행률 및 단계 표시 */}
<div className="space-y-4">
  <div className="flex items-center justify-between">
    <h3 className="text-lg font-semibold">AI 요약 생성 중...</h3>
    <span className="text-sm text-gray-500">{streamingProgress}%</span>
  </div>
  
  {/* 진행률 바 */}
  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
    <motion.div
      className="bg-primary-500 h-2 rounded-full"
      style={{ width: `${streamingProgress}%` }}
      transition={{ duration: 0.3 }}
    />
  </div>
  
  {/* 현재 단계 */}
  {streamingStep && (
    <p className="text-sm text-gray-600 dark:text-gray-400 flex items-center gap-2">
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
        className="w-4 h-4 border-2 border-primary-500 border-t-transparent rounded-full"
      />
      {streamingStep}
    </p>
  )}
</div>
```

### After (ThinkingProgress 사용)
```typescript
<ThinkingProgress
  step={streamingStep}
  progress={streamingProgress}
  type="thinking"
  isGenerating={isGeneratingSummary}
/>
```

## 적용 결과

### 개선사항
1. **사용자 경험 향상**: ChatGPT 스타일의 친근한 메시지
2. **코드 간소화**: 복잡한 진행률 표시 로직을 단일 컴포넌트로 통합
3. **일관성**: 모든 페이지에서 동일한 스타일의 진행률 표시
4. **재사용성**: 다른 AI 기능에서도 쉽게 활용 가능
5. **애니메이션**: 더 부드럽고 매력적인 시각적 효과

### 적용된 파일
- `/Users/yeong-gwang/Documents/work/서울경제신문/빅카인즈/big_proto/frontend/src/pages/CategoryDetailPage.tsx`
- `/Users/yeong-gwang/Documents/work/서울경제신문/빅카인즈/big_proto/frontend/src/pages/WatchlistPage.tsx`

## 추가 활용 가능한 곳
- 리포트 생성 페이지
- 다른 AI 분석 기능
- 데이터 로딩이 필요한 모든 상황