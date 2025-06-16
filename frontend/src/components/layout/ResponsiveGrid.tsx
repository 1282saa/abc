import React, { ReactNode } from "react";
import { motion } from "framer-motion";

interface ResponsiveGridProps {
  children: ReactNode;
  cols?: {
    default?: number;
    sm?: number;
    md?: number;
    lg?: number;
    xl?: number;
    "2xl"?: number;
  };
  gap?: number;
  className?: string;
  animate?: boolean;
}

interface GridItemProps {
  children: ReactNode;
  span?: {
    default?: number;
    sm?: number;
    md?: number;
    lg?: number;
    xl?: number;
    "2xl"?: number;
  };
  className?: string;
  index?: number;
}

/**
 * 반응형 그리드 시스템 컴포넌트
 * - 다양한 화면 크기에 최적화된 레이아웃
 * - 애니메이션 지원
 * - 접근성 고려
 */
export const ResponsiveGrid: React.FC<ResponsiveGridProps> = ({
  children,
  cols = { default: 1, sm: 2, md: 3, lg: 4 },
  gap = 6,
  className = "",
  animate = true,
}) => {
  const getGridClasses = () => {
    const baseClass = "grid";
    const gapClass = `gap-${gap}`;
    
    const colClasses = [
      cols.default && `grid-cols-${cols.default}`,
      cols.sm && `sm:grid-cols-${cols.sm}`,
      cols.md && `md:grid-cols-${cols.md}`,
      cols.lg && `lg:grid-cols-${cols.lg}`,
      cols.xl && `xl:grid-cols-${cols.xl}`,
      cols["2xl"] && `2xl:grid-cols-${cols["2xl"]}`,
    ].filter(Boolean);

    return [baseClass, gapClass, ...colClasses, className].join(" ");
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
      },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        type: "spring",
        stiffness: 300,
        damping: 24,
      },
    },
  };

  if (animate) {
    return (
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className={getGridClasses()}
      >
        {React.Children.map(children, (child, index) => (
          <motion.div key={index} variants={itemVariants}>
            {child}
          </motion.div>
        ))}
      </motion.div>
    );
  }

  return <div className={getGridClasses()}>{children}</div>;
};

/**
 * 그리드 아이템 컴포넌트
 */
export const GridItem: React.FC<GridItemProps> = ({
  children,
  span = { default: 1 },
  className = "",
  index,
}) => {
  const getSpanClasses = () => {
    const spanClasses = [
      span.default && `col-span-${span.default}`,
      span.sm && `sm:col-span-${span.sm}`,
      span.md && `md:col-span-${span.md}`,
      span.lg && `lg:col-span-${span.lg}`,
      span.xl && `xl:col-span-${span.xl}`,
      span["2xl"] && `2xl:col-span-${span["2xl"]}`,
    ].filter(Boolean);

    return [...spanClasses, className].join(" ");
  };

  return <div className={getSpanClasses()}>{children}</div>;
};

/**
 * 반응형 컨테이너 컴포넌트
 */
interface ResponsiveContainerProps {
  children: ReactNode;
  maxWidth?: "sm" | "md" | "lg" | "xl" | "2xl" | "full";
  padding?: "none" | "sm" | "md" | "lg";
  className?: string;
}

export const ResponsiveContainer: React.FC<ResponsiveContainerProps> = ({
  children,
  maxWidth = "lg",
  padding = "md",
  className = "",
}) => {
  const maxWidthClasses = {
    sm: "max-w-sm",
    md: "max-w-md",
    lg: "max-w-4xl",
    xl: "max-w-6xl",
    "2xl": "max-w-7xl",
    full: "max-w-full",
  };

  const paddingClasses = {
    none: "",
    sm: "px-4 py-2",
    md: "px-6 py-4",
    lg: "px-8 py-6",
  };

  const containerClasses = [
    "mx-auto w-full",
    maxWidthClasses[maxWidth],
    paddingClasses[padding],
    className,
  ].join(" ");

  return <div className={containerClasses}>{children}</div>;
};

/**
 * 플렉시블 스택 컴포넌트
 */
interface FlexStackProps {
  children: ReactNode;
  direction?: "row" | "col";
  align?: "start" | "center" | "end" | "stretch";
  justify?: "start" | "center" | "end" | "between" | "around" | "evenly";
  gap?: number;
  wrap?: boolean;
  className?: string;
  responsive?: {
    sm?: Partial<FlexStackProps>;
    md?: Partial<FlexStackProps>;
    lg?: Partial<FlexStackProps>;
  };
}

export const FlexStack: React.FC<FlexStackProps> = ({
  children,
  direction = "col",
  align = "start",
  justify = "start",
  gap = 4,
  wrap = false,
  className = "",
  responsive = {},
}) => {
  const getFlexClasses = () => {
    const baseClasses = ["flex"];
    
    // Direction
    baseClasses.push(direction === "row" ? "flex-row" : "flex-col");
    
    // Alignment
    const alignClasses = {
      start: "items-start",
      center: "items-center",
      end: "items-end",
      stretch: "items-stretch",
    };
    baseClasses.push(alignClasses[align]);
    
    // Justification
    const justifyClasses = {
      start: "justify-start",
      center: "justify-center",
      end: "justify-end",
      between: "justify-between",
      around: "justify-around",
      evenly: "justify-evenly",
    };
    baseClasses.push(justifyClasses[justify]);
    
    // Gap
    baseClasses.push(`gap-${gap}`);
    
    // Wrap
    if (wrap) {
      baseClasses.push("flex-wrap");
    }
    
    // Responsive classes
    Object.entries(responsive).forEach(([breakpoint, props]) => {
      if (props.direction) {
        baseClasses.push(`${breakpoint}:${props.direction === "row" ? "flex-row" : "flex-col"}`);
      }
      if (props.align) {
        const alignClass = {
          start: "items-start",
          center: "items-center",
          end: "items-end",
          stretch: "items-stretch",
        }[props.align];
        baseClasses.push(`${breakpoint}:${alignClass}`);
      }
      if (props.justify) {
        const justifyClass = {
          start: "justify-start",
          center: "justify-center",
          end: "justify-end",
          between: "justify-between",
          around: "justify-around",
          evenly: "justify-evenly",
        }[props.justify];
        baseClasses.push(`${breakpoint}:${justifyClass}`);
      }
      if (props.gap !== undefined) {
        baseClasses.push(`${breakpoint}:gap-${props.gap}`);
      }
    });
    
    return [...baseClasses, className].join(" ");
  };

  return <div className={getFlexClasses()}>{children}</div>;
};

export default ResponsiveGrid;