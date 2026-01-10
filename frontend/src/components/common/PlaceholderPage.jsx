import { motion } from "framer-motion";

/**
 * 占位页面组件（用于开发中的功能）
 */
export const PlaceholderPage = ({ title }) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    exit={{ opacity: 0, y: -20 }}
    className="flex flex-col items-center justify-center h-[60vh] text-center"
  >
    <div className="text-6xl mb-4">🚧</div>
    <h1 className="text-2xl font-semibold text-white mb-2">{title}</h1>
    <p className="text-slate-400">该功能正在开发中，敬请期待</p>
  </motion.div>
);
