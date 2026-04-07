
export default function LoadingOverlay({ message }) {
  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        className="bg-gray-800 rounded-xl p-8 text-center max-w-md"
      >
        <div className="relative w-20 h-20 mx-auto mb-4">
          <div className="absolute inset-0 border-4 border-blue-500/30 rounded-full"></div>
          <div className="absolute inset-0 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
          <Sparkles className="absolute inset-0 m-auto w-8 h-8 text-blue-400 animate-pulse" />
        </div>
        <div className="text-white text-lg font-medium mb-2">AI 正在分析</div>
        <div className="text-gray-400 text-sm">{message}</div>
      </motion.div>
    </div>
  );
}
