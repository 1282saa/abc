import React from "react";
import CitationLink from "../components/common/CitationLink";
import { CitationSource } from "../services/api";

/**
 * 텍스트 내의 [숫자] 패턴을 찾아서 CitationLink 컴포넌트로 변환합니다.
 * 
 * @param content - 변환할 텍스트 내용
 * @param citations - 인용 출처 배열
 * @param variant - CitationLink의 표시 스타일
 * @returns React 요소 배열
 */
export const renderWithCitations = (
  content: string,
  citations: CitationSource[],
  variant: "inline" | "button" | "badge" = "inline"
): React.ReactNode[] => {
  // [숫자] 패턴을 찾는 정규식
  const citationPattern = /\[(\d+)\]/g;
  const parts = content.split(citationPattern);
  const result: React.ReactNode[] = [];

  for (let i = 0; i < parts.length; i++) {
    if (i % 2 === 0) {
      // 일반 텍스트
      if (parts[i]) {
        result.push(parts[i]);
      }
    } else {
      // 인용 번호
      const citationNum = parseInt(parts[i]);
      const citation = citations[citationNum - 1];
      
      if (citation) {
        result.push(
          <CitationLink
            key={`citation-${citationNum}-${i}`}
            citationNumber={citationNum}
            citation={citation}
            variant={variant}
          />
        );
      } else {
        // 인용 출처가 없는 경우 원본 텍스트 유지
        result.push(`[${citationNum}]`);
      }
    }
  }

  return result;
};

/**
 * 텍스트에서 인용 번호들을 추출합니다.
 * 
 * @param content - 텍스트 내용
 * @returns 인용 번호 배열
 */
export const extractCitationNumbers = (content: string): number[] => {
  const citationPattern = /\[(\d+)\]/g;
  const citations: number[] = [];
  let match;

  while ((match = citationPattern.exec(content)) !== null) {
    const num = parseInt(match[1]);
    if (!citations.includes(num)) {
      citations.push(num);
    }
  }

  return citations.sort((a, b) => a - b);
};

/**
 * 인용 출처의 유효성을 검사합니다.
 * 
 * @param citation - 검사할 인용 출처
 * @returns 유효성 검사 결과
 */
export const validateCitation = (citation: CitationSource): {
  isValid: boolean;
  errors: string[];
} => {
  const errors: string[] = [];

  if (!citation.id || citation.id.trim() === "") {
    errors.push("ID가 필요합니다.");
  }

  if (!citation.title || citation.title.trim() === "") {
    errors.push("제목이 필요합니다.");
  }

  if (!citation.provider || citation.provider.trim() === "") {
    errors.push("언론사 정보가 필요합니다.");
  }

  if (!citation.published_at || citation.published_at.trim() === "") {
    errors.push("발행일이 필요합니다.");
  }

  // URL 유효성 검사 (선택사항이지만 있다면 유효해야 함)
  if (citation.url && citation.url !== "#") {
    try {
      new URL(citation.url);
    } catch {
      errors.push("유효하지 않은 URL입니다.");
    }
  }

  return {
    isValid: errors.length === 0,
    errors,
  };
};

/**
 * 인용 출처 배열의 유효성을 검사합니다.
 * 
 * @param citations - 검사할 인용 출처 배열
 * @returns 유효성 검사 결과
 */
export const validateCitations = (citations: CitationSource[]): {
  isValid: boolean;
  invalidCitations: Array<{ index: number; errors: string[] }>;
} => {
  const invalidCitations: Array<{ index: number; errors: string[] }> = [];

  citations.forEach((citation, index) => {
    const validation = validateCitation(citation);
    if (!validation.isValid) {
      invalidCitations.push({
        index,
        errors: validation.errors,
      });
    }
  });

  return {
    isValid: invalidCitations.length === 0,
    invalidCitations,
  };
};

/**
 * 텍스트 내용과 인용 출처의 일관성을 검사합니다.
 * 
 * @param content - 텍스트 내용
 * @param citations - 인용 출처 배열
 * @returns 일관성 검사 결과
 */
export const validateContentCitations = (
  content: string,
  citations: CitationSource[]
): {
  isConsistent: boolean;
  missingCitations: number[];
  unusedCitations: number[];
} => {
  const referencedNumbers = extractCitationNumbers(content);
  const availableNumbers = citations.map((_, index) => index + 1);

  const missingCitations = referencedNumbers.filter(
    num => num > citations.length || num < 1
  );

  const unusedCitations = availableNumbers.filter(
    num => !referencedNumbers.includes(num)
  );

  return {
    isConsistent: missingCitations.length === 0,
    missingCitations,
    unusedCitations,
  };
};

/**
 * 인용 출처를 번호순으로 정렬합니다.
 * 
 * @param citations - 정렬할 인용 출처 배열
 * @param content - 참조할 텍스트 내용 (선택사항)
 * @returns 정렬된 인용 출처 배열
 */
export const sortCitationsByReference = (
  citations: CitationSource[],
  content?: string
): CitationSource[] => {
  if (!content) {
    return [...citations];
  }

  const referencedNumbers = extractCitationNumbers(content);
  const sortedCitations: CitationSource[] = [];
  const usedIndices = new Set<number>();

  // 참조된 순서대로 먼저 배치
  referencedNumbers.forEach(num => {
    const index = num - 1;
    if (index >= 0 && index < citations.length && !usedIndices.has(index)) {
      sortedCitations.push(citations[index]);
      usedIndices.add(index);
    }
  });

  // 참조되지 않은 인용 출처들 추가
  citations.forEach((citation, index) => {
    if (!usedIndices.has(index)) {
      sortedCitations.push(citation);
    }
  });

  return sortedCitations;
};

/**
 * 인용 출처에서 중복을 제거합니다.
 * 
 * @param citations - 중복 제거할 인용 출처 배열
 * @param keyField - 중복 판단 기준 필드 (기본값: 'id')
 * @returns 중복이 제거된 인용 출처 배열
 */
export const deduplicateCitations = (
  citations: CitationSource[],
  keyField: keyof CitationSource = 'id'
): CitationSource[] => {
  const seen = new Set<string>();
  return citations.filter(citation => {
    const key = String(citation[keyField]);
    if (seen.has(key)) {
      return false;
    }
    seen.add(key);
    return true;
  });
};

/**
 * 인용 출처에서 통계 정보를 생성합니다.
 * 
 * @param citations - 분석할 인용 출처 배열
 * @returns 통계 정보
 */
export const getCitationStatistics = (citations: CitationSource[]) => {
  const providerCount: Record<string, number> = {};
  const dateCount: Record<string, number> = {};

  citations.forEach(citation => {
    // 언론사별 통계
    providerCount[citation.provider] = (providerCount[citation.provider] || 0) + 1;

    // 날짜별 통계 (월별)
    try {
      const date = new Date(citation.published_at);
      const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
      dateCount[monthKey] = (dateCount[monthKey] || 0) + 1;
    } catch {
      // 날짜 파싱 실패 시 무시
    }
  });

  const topProviders = Object.entries(providerCount)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 5);

  return {
    totalCitations: citations.length,
    uniqueProviders: Object.keys(providerCount).length,
    topProviders,
    dateDistribution: dateCount,
    averageTitleLength: citations.reduce((sum, c) => sum + c.title.length, 0) / citations.length,
  };
};

export default {
  renderWithCitations,
  extractCitationNumbers,
  validateCitation,
  validateCitations,
  validateContentCitations,
  sortCitationsByReference,
  deduplicateCitations,
  getCitationStatistics,
};