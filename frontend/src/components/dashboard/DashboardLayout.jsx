/**
 * DashboardLayout - 统一的工作台布局组件
 * 提供标准的工作台页面结构
 *
 * @param {Object} props
 * @param {string} props.title - 标题
 * @param {string} props.description - 描述
 * @param {React.ReactNode} props.actions - 操作按钮区域
 * @param {React.ReactNode} props.children - 子内容
 * @param {boolean} props.loading - 加载状态
 */
import { motion } from "framer-motion";
import { PageHeader } from "../layout/PageHeader";

// Stagger animation variants
const staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.05, delayChildren: 0.1 },
  },
};

const staggerChild = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 },
};

export function DashboardLayout({
  title,
  description,
  actions,
  children,
  loading = false,
}) {
  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={staggerContainer}
      className="space-y-6"
    >
      <motion.div variants={staggerChild}>
        <PageHeader title={title} description={description} actions={actions} />
      </motion.div>

      <motion.div variants={staggerChild}>{children}</motion.div>
    </motion.div>
  );
}

export default DashboardLayout;
