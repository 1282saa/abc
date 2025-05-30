// 페이지 애니메이션 설정
export const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
    },
  },
};

export const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.5,
    },
  },
};

// 페이지 전환 애니메이션
export const pageTransition = {
  type: "tween",
  ease: "anticipate",
  duration: 0.5,
};

// 호버 애니메이션
export const hoverScale = {
  scale: 1.03,
  transition: { duration: 0.2 },
};

// 버튼 탭 애니메이션
export const tapScale = {
  scale: 0.97,
};
