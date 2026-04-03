import { motion } from 'framer-motion';
import { BarChart3, Clock, Users, AlertTriangle } from 'lucide-react';

const FEATURES = [
  { icon: BarChart3, title: "实时进度追踪", desc: "甘特图、看板多视图" },
  { icon: Clock, title: "智能工时管理", desc: "自动统计、负荷预警" },
  { icon: Users, title: "团队高效协作", desc: "任务分配、实时同步" },
  { icon: AlertTriangle, title: "AI 智能预警", desc: "风险识别、提前预警" },
];

export default function FeatureShowcase() {
  return (
    <div className="hidden lg:flex flex-col justify-between flex-1 max-w-[580px] p-12 text-white">
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, delay: 0.2 }}
      >
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/10 backdrop-blur-md border border-white/10 mb-8">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-sm font-medium">项目进度管理系统</span>
        </div>

        <h1 className="text-5xl font-bold leading-tight mb-6">
          让每个项目<br />
          <span className="text-gradient-primary">尽在掌控</span>
        </h1>

        <p className="text-lg text-slate-400 mb-12 max-w-md">
          专为非标自动化设备企业打造的智能项目管理平台，实现项目全生命周期的精细化管控。
        </p>

        <div className="space-y-5">
          {FEATURES.map((feature, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: 0.4 + i * 0.1 }}
              className="flex items-start gap-4"
            >
              <div className="p-3 rounded-xl bg-primary/15 border border-primary/25">
                <feature.icon className="h-5 w-5 text-primary" />
              </div>
              <div>
                <h4 className="font-semibold mb-1">{feature.title}</h4>
                <p className="text-sm text-slate-500">{feature.desc}</p>
              </div>
            </motion.div>
          ))}
        </div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 0.8 }}
        >
          <p className="text-sm text-slate-500">
            受到 <span className="text-white font-medium">200+</span>{" "}
            家企业的信赖
          </p>
        </motion.div>
      </motion.div>
    </div>
  );
}
