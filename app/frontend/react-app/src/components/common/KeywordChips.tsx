import React from "react";

interface KeywordChipsProps {
  keywords: string[];
  onKeywordClick?: (keyword: string) => void;
  active?: boolean;
  className?: string;
}

/**
 * 키워드 칩을 표시하는 컴포넌트
 * 클릭 가능한 버튼 또는 단순 표시용으로 사용 가능
 */
const KeywordChips: React.FC<KeywordChipsProps> = ({
  keywords,
  onKeywordClick,
  active = false,
  className = "",
}) => {
  if (!keywords || keywords.length === 0) return null;

  return (
    <div className={`flex flex-wrap gap-2 ${className}`}>
      {keywords.map((keyword, index) => {
        // 클릭 가능한 버튼이면 button, 아니면 span
        const ChipElement = onKeywordClick ? "button" : "span";

        return (
          <ChipElement
            key={index}
            className={`chip microinteraction ${active ? "chip-active" : ""}`}
            onClick={onKeywordClick ? () => onKeywordClick(keyword) : undefined}
          >
            {keyword}
          </ChipElement>
        );
      })}
    </div>
  );
};

export default KeywordChips;
