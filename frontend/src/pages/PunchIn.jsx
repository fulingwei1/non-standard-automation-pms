import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  MapPin,
  Clock,
  CheckCircle2,
  History,
  ArrowRight,
  Timer,
  Calendar as CalendarIcon,
  ShieldCheck,
  AlertCircle,
} from "lucide-react";
import { cn } from "../lib/utils";

const PunchIn = () => {
  const [isPunchedIn, setIsPunchedIn] = useState(false);
  const [currentTime, setCurrentTime] = useState(new Date());
  const [workingTime, setWorkingTime] = useState(0);
  const [status, setStatus] = useState("idle"); // idle, punching, success

  // Update clock every second
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
      if (isPunchedIn) {
        setWorkingTime((prev) => prev + 1);
      }
    }, 1000);
    return () => clearInterval(timer);
  }, [isPunchedIn]);

  const formatTime = (date) => {
    return date.toLocaleTimeString("zh-CN", {
      hour12: false,
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  };

  const formatDuration = (seconds) => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    return `${h.toString().padStart(2, "0")}:${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  };

  const handlePunch = () => {
    setStatus("punching");
    // Simulate API call
    setTimeout(() => {
      setIsPunchedIn(!isPunchedIn);
      setStatus("success");
      setTimeout(() => setStatus("idle"), 2000);
    }, 1500);
  };

  const activities = [
    {
      id: 1,
      type: "签退",
      time: "18:02:15",
      date: "2026-01-03",
      location: "南京总部 A 座",
    },
    {
      id: 2,
      type: "签到",
      time: "08:55:30",
      date: "2026-01-03",
      location: "南京总部 A 座",
    },
    {
      id: 3,
      type: "签退",
      time: "17:45:10",
      date: "2026-01-02",
      location: "无锡研发中心",
    },
  ];

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Header Section */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
        >
          <h1 className="text-3xl font-bold text-white mb-2">岗位打卡</h1>
          <p className="text-slate-400">管理您的日常工作考勤与位置状态</p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          className="flex items-center gap-3 bg-white/5 border border-white/10 px-4 py-2 rounded-2xl backdrop-blur-md"
        >
          <CalendarIcon className="w-4 h-4 text-primary" />
          <span className="text-slate-200 font-medium">
            {currentTime.toLocaleDateString("zh-CN", {
              year: "numeric",
              month: "long",
              day: "numeric",
              weekday: "long",
            })}
          </span>
        </motion.div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Punch Card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="lg:col-span-2 relative group"
        >
          <div className="absolute -inset-0.5 bg-gradient-to-r from-violet-500 to-indigo-500 rounded-3xl blur opacity-20 group-hover:opacity-30 transition duration-1000"></div>
          <div className="relative h-full bg-surface-100 border border-white/10 rounded-3xl p-8 backdrop-blur-xl flex flex-col items-center justify-center min-h-[400px]">
            {/* Real-time Clock Visualization */}
            <div className="mb-8 text-center">
              <motion.div
                key={isPunchedIn}
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                className="text-6xl font-display font-bold text-white tracking-tight mb-2"
              >
                {formatTime(currentTime)}
              </motion.div>
              <div className="flex items-center justify-center gap-2 text-slate-400">
                <MapPin className="w-4 h-4 text-primary" />
                <span className="text-sm">南京总部 A 座 · 研发中心 01</span>
              </div>
            </div>

            {/* Punch Button */}
            <div className="relative">
              <AnimatePresence mode="wait">
                {status === "punching" ? (
                  <motion.div
                    key="punching"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="w-48 h-48 rounded-full border-4 border-primary/30 border-t-primary animate-spin"
                  />
                ) : (
                  <motion.button
                    key="button"
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={handlePunch}
                    className={cn(
                      "w-48 h-48 rounded-full flex flex-col items-center justify-center gap-2 transition-all duration-500 shadow-2xl",
                      isPunchedIn
                        ? "bg-slate-800 border-4 border-white/10 text-white hover:bg-slate-700"
                        : "bg-gradient-to-br from-violet-600 to-indigo-600 border-4 border-white/20 text-white shadow-violet-500/20",
                    )}
                  >
                    <Clock className="w-10 h-10 mb-1" />
                    <span className="text-xl font-bold">
                      {isPunchedIn ? "下班打卡" : "上班打卡"}
                    </span>
                    <span className="text-xs opacity-60 font-medium tracking-widest uppercase">
                      {isPunchedIn ? "Confirm Exit" : "Start Session"}
                    </span>
                  </motion.button>
                )}
              </AnimatePresence>

              {/* Success Badge Overlay */}
              <AnimatePresence>
                {status === "success" && (
                  <motion.div
                    initial={{ scale: 0.5, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    exit={{ scale: 0.5, opacity: 0 }}
                    className="absolute inset-0 flex items-center justify-center pointer-events-none"
                  >
                    <div className="bg-success text-white px-6 py-2 rounded-full flex items-center gap-2 shadow-xl shadow-success/20">
                      <CheckCircle2 className="w-5 h-5" />
                      <span className="font-bold">打卡成功</span>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* Status Footer */}
            <div className="mt-8 grid grid-cols-2 gap-12 border-t border-white/5 pt-8 w-full">
              <div className="text-center">
                <p className="text-slate-500 text-xs uppercase tracking-wider mb-1">
                  今日时长
                </p>
                <p className="text-xl font-mono font-semibold text-white">
                  {isPunchedIn ? formatDuration(workingTime) : "00:00:00"}
                </p>
              </div>
              <div className="text-center border-l border-white/5">
                <p className="text-slate-500 text-xs uppercase tracking-wider mb-1">
                  当前状态
                </p>
                <div className="flex items-center justify-center gap-2">
                  <div
                    className={cn(
                      "w-2 h-2 rounded-full",
                      isPunchedIn ? "bg-success animate-pulse" : "bg-slate-600",
                    )}
                  />
                  <p className="text-sm font-semibold text-white">
                    {isPunchedIn ? "工作中" : "未签到"}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Sidebar Cards */}
        <div className="space-y-6">
          {/* Work Summary */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-white/5 border border-white/10 rounded-2xl p-6 backdrop-blur-md"
          >
            <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
              <Timer className="w-4 h-4 text-violet-400" />
              工时统计
            </h3>
            <div className="space-y-4">
              <div className="flex justify-between items-end">
                <div>
                  <p className="text-slate-400 text-xs mb-1">本周累计</p>
                  <p className="text-xl font-bold text-white">42.5 小时</p>
                </div>
                <span className="text-xs text-success bg-success/10 px-2 py-0.5 rounded-full font-medium">
                  +12%
                </span>
              </div>
              <div className="w-full bg-white/5 h-1.5 rounded-full overflow-hidden">
                <div className="bg-primary h-full w-[85%] rounded-full shadow-[0_0_8px_rgba(139,92,246,0.5)]" />
              </div>
              <div className="flex justify-between text-[10px] text-slate-500">
                <span>目标: 40h</span>
                <span>已完成 85%</span>
              </div>
            </div>
          </motion.div>

          {/* Location Safety */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-white/5 border border-white/10 rounded-2xl p-6 backdrop-blur-md"
          >
            <div className="flex items-start gap-4">
              <div className="w-10 h-10 rounded-xl bg-violet-500/10 flex items-center justify-center shrink-0">
                <ShieldCheck className="w-5 h-5 text-violet-400" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-white mb-1">
                  地理围栏已启用
                </h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  您目前处于有效打卡区域内。系统已自动为您匹配最近的办公地。
                </p>
              </div>
            </div>
          </motion.div>

          {/* Warning Card (Conditional) */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3 }}
            className="bg-warning/10 border border-warning/20 rounded-2xl p-6"
          >
            <div className="flex gap-4">
              <AlertCircle className="w-5 h-5 text-warning shrink-0" />
              <div>
                <h3 className="text-sm font-semibold text-warning mb-1">
                  异常提醒
                </h3>
                <p className="text-xs text-warning/70 leading-relaxed">
                  昨日 18:00 未检测到签退记录，请核实补卡。
                </p>
              </div>
            </div>
          </motion.div>
        </div>
      </div>

      {/* Recent Activity */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="bg-white/[0.02] border border-white/5 rounded-3xl overflow-hidden"
      >
        <div className="px-8 py-6 border-b border-white/5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-white/5 flex items-center justify-center">
              <History className="w-4 h-4 text-slate-400" />
            </div>
            <h2 className="text-lg font-bold text-white">最近打卡记录</h2>
          </div>
          <button className="text-xs font-semibold text-primary hover:text-primary-light flex items-center gap-1 transition-colors">
            查看完整报告 <ArrowRight className="w-3 h-3" />
          </button>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="text-slate-500 text-xs uppercase tracking-widest border-b border-white/5">
                <th className="px-8 py-4 font-semibold">日期</th>
                <th className="px-8 py-4 font-semibold">打卡时间</th>
                <th className="px-8 py-4 font-semibold">类型</th>
                <th className="px-8 py-4 font-semibold">打卡地点</th>
                <th className="px-8 py-4 font-semibold text-right">状态</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {activities.map((activity) => (
                <tr
                  key={activity.id}
                  className="group hover:bg-white/[0.02] transition-colors"
                >
                  <td className="px-8 py-4 text-sm text-slate-300">
                    {activity.date}
                  </td>
                  <td className="px-8 py-4 text-sm font-mono text-slate-200">
                    {activity.time}
                  </td>
                  <td className="px-8 py-4">
                    <span
                      className={cn(
                        "px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider",
                        activity.type === "签到"
                          ? "bg-primary/10 text-primary-light"
                          : "bg-slate-700/50 text-slate-400",
                      )}
                    >
                      {activity.type}
                    </span>
                  </td>
                  <td className="px-8 py-4">
                    <div className="flex items-center gap-2 text-sm text-slate-400">
                      <MapPin className="w-3 h-3 opacity-50" />
                      {activity.location}
                    </div>
                  </td>
                  <td className="px-8 py-4 text-right">
                    <div className="inline-flex items-center gap-1.5 bg-success/10 px-2 py-1 rounded-lg">
                      <div className="w-1 h-1 rounded-full bg-success" />
                      <span className="text-[10px] font-bold text-success uppercase">
                        Normal
                      </span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </motion.div>
    </div>
  );
};

export default PunchIn;
