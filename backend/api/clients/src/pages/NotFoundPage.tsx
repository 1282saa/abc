import React from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { containerVariants, itemVariants } from "../animations/pageAnimations";

/**
 * 404 페이지를 찾을 수 없음 페이지
 */
const NotFoundPage: React.FC = () => {
  return (
    <motion.div
      className="flex flex-col items-center justify-center text-center py-16 px-4 max-w-4xl mx-auto"
      initial="hidden"
      animate="visible"
      variants={containerVariants}
    >
      <motion.div variants={itemVariants} className="mb-8">
        <div className="text-9xl font-bold text-gray-200 dark:text-gray-800">
          404
        </div>
      </motion.div>

      <motion.h1
        variants={itemVariants}
        className="text-3xl md:text-4xl font-bold mb-4"
      >
        페이지를 찾을 수 없습니다
      </motion.h1>

      <motion.p
        variants={itemVariants}
        className="text-lg text-gray-600 dark:text-gray-400 mb-8"
      >
        요청하신 페이지가 존재하지 않거나 이동되었을 수 있습니다.
      </motion.p>

      <motion.div variants={itemVariants}>
        <Link to="/" className="btn-primary">
          홈으로 돌아가기
        </Link>
      </motion.div>
    </motion.div>
  );
};

export default NotFoundPage;
