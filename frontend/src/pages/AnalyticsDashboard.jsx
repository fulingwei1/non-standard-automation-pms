/**
 * AnalyticsDashboard.jsx
 * 
 * 非标自动化项目管理系统 - 数据分析仪表盘
 * Modern Analytics Dashboard with Dark Mode, Real-time indicators, and Responsive Design.
 * 
 * Features:
 * - KPI Cards with trend indicators
 * - Multi-type Chart Visualizations (Line, Bar, Pie, Area)
 * - Real-time Activity Feed
 * - Dark Mode optimized
 */

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, 
  PieChart, Pie, Cell, AreaChart, Area 
} from 'recharts';
import { 
  Activity, CheckCircle, AlertCircle, Folder, 
  Zap, Clock, RefreshCw, TrendingUp,
  ArrowUpRight
} from 'lucide-react';

import { Card, CardContent, CardHeader, CardTitle, StatCard } from '@/components/ui/card';
import LineChart from '@/components/charts/LineChart';
import { useAnalytics } from '@/hooks/useAnalytics';

const ICON_MAP = {
  Folder,
  CheckCircle,
  AlertCircle,
  Activity
};

export default function AnalyticsDashboard() {
  const {
    kpis,
    lineChartData,
    statusDistribution,
    monthlyStats,
    resourceData,
    activities,
    totalProjects,
    loading,
    lastUpdated,
    refresh
  } = useAnalytics({ refreshInterval: 30000 });
  
  const [secondsSinceUpdate, setSecondsSinceUpdate] = useState(0);

  useEffect(() => {
    if (!lastUpdated) {
      setSecondsSinceUpdate(0);
      return;
    }

    const update = () => {
      setSecondsSinceUpdate(
        Math.floor((Date.now() - lastUpdated.getTime()) / 1000),
      );
    };

    update();
    const intervalId = setInterval(update, 1000);
    return () => clearInterval(intervalId);
  }, [lastUpdated]);

  // Animation variants
  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  };

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    show: { y: 0, opacity: 1, transition: { type: "spring", stiffness: 100 } }
  };

  // Render Loading Skeleton
  if (loading) {
    return (
      <div className="p-8 space-y-8 bg-surface-0 min-h-screen">
        <div className="flex justify-between items-center mb-8">
          <div className="h-8 w-48 bg-surface-200 rounded animate-shimmer" />
          <div className="h-8 w-32 bg-surface-200 rounded animate-shimmer" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-32 bg-surface-100 rounded-2xl animate-shimmer" />
          ))}
        </div>
        <div className="grid grid-cols-12 gap-6">
          <div className="col-span-12 lg:col-span-8 h-96 bg-surface-100 rounded-2xl animate-shimmer" />
          <div className="col-span-12 lg:col-span-4 h-96 bg-surface-100 rounded-2xl animate-shimmer" />
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-8 bg-surface-0 min-h-screen text-slate-100 font-sans selection:bg-primary-500/30">
      
      {/* Header Section */}
      <motion.div 
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4"
      >
        <div>
          <h1 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent">
            数据概览
          </h1>
          <p className="text-slate-400 mt-1">
            项目全生命周期监控与分析
          </p>
        </div>
        
        <div className="flex items-center gap-3 bg-surface-100 px-4 py-2 rounded-full border border-white/5 shadow-sm">
          <div className="relative flex h-3 w-3">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500" />
          </div>
          <span className="text-sm font-medium text-slate-300">实时监控中</span>
          <div className="h-4 w-px bg-white/10 mx-1" />
          <button 
            onClick={refresh}
            className="flex items-center gap-2 text-xs text-slate-400 hover:text-primary-400 transition-colors"
          >
            <RefreshCw className="h-3 w-3" />
            <span>最后更新: {secondsSinceUpdate}秒前</span>
          </button>
        </div>
      </motion.div>

      <motion.div 
        variants={containerVariants}
        initial="hidden"
        animate="show"
        className="space-y-6"
      >
        {/* KPI Cards Row */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {kpis.map((kpi, index) => (
            <motion.div key={kpi.id || index} variants={itemVariants}>
              <StatCard
                label={kpi.label}
                value={kpi.value}
                change={kpi.change}
                trend={kpi.trend}
                icon={ICON_MAP[kpi.icon] || Activity}
                className="bg-surface-100 border-white/5 hover:border-primary-500/20 hover:shadow-lg hover:shadow-primary-500/5 transition-all duration-300"
              />
            </motion.div>
          ))}
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-12 gap-6">
          
          {/* Left Column - Charts (8/12) */}
          <div className="col-span-12 lg:col-span-8 space-y-6">
            
            {/* Project Trends - Line Chart */}
            <motion.div variants={itemVariants}>
              <Card className="bg-surface-100 border-white/5 overflow-hidden">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <TrendingUp className="h-5 w-5 text-primary-400" />
                    项目趋势分析
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="h-[350px] w-full">
                    <LineChart 
                      data={lineChartData}
                      xField="date"
                      yField="value"
                      seriesField="category"
                      height={350}
                      colors={['#10b981', '#8b5cf6']}
                      style={{ height: '350px' }}
                    />
                  </div>
                </CardContent>
              </Card>
            </motion.div>

            {/* Row 2: Bar & Pie */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              
              {/* Monthly Stats - Bar Chart */}
              <motion.div variants={itemVariants}>
                <Card className="bg-surface-100 border-white/5 h-full">
                  <CardHeader>
                    <CardTitle>月度立项/结项对比</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="h-[300px]">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={monthlyStats}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#333" vertical={false} />
                          <XAxis 
                            dataKey="name" 
                            stroke="#94a3b8" 
                            fontSize={12} 
                            tickLine={false}
                            axisLine={false}
                          />
                          <YAxis 
                            stroke="#94a3b8" 
                            fontSize={12} 
                            tickLine={false}
                            axisLine={false}
                          />
                          <Tooltip 
                            contentStyle={{ backgroundColor: '#18181b', borderColor: '#333', color: '#fff' }}
                            itemStyle={{ color: '#fff' }}
                            cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                          />
                          <Bar dataKey="new" name="新立项" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
                          <Bar dataKey="completed" name="已结项" fill="#10b981" radius={[4, 4, 0, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>

              {/* Status Distribution - Donut Chart */}
              <motion.div variants={itemVariants}>
                <Card className="bg-surface-100 border-white/5 h-full">
                  <CardHeader>
                    <CardTitle>项目阶段分布</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="h-[300px] flex items-center justify-center relative">
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie
                            data={statusDistribution}
                            cx="50%"
                            cy="50%"
                            innerRadius={60}
                            outerRadius={80}
                            paddingAngle={5}
                            dataKey="value"
                          >
                            {statusDistribution.map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={entry.color} stroke="rgba(0,0,0,0)" />
                            ))}
                          </Pie>
                          <Tooltip 
                            contentStyle={{ backgroundColor: '#18181b', borderColor: '#333', color: '#fff', borderRadius: '8px' }}
                            itemStyle={{ color: '#fff' }}
                          />
                        </PieChart>
                      </ResponsiveContainer>
                      {/* Center Text */}
                      <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                        <span className="text-3xl font-bold text-white">{totalProjects}</span>
                        <span className="text-xs text-slate-400 uppercase tracking-wider">Total</span>
                      </div>
                    </div>
                    {/* Legend */}
                    <div className="flex flex-wrap justify-center gap-3 mt-4">
                      {statusDistribution.map((item, index) => (
                        <div key={index} className="flex items-center gap-1.5">
                          <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: item.color }} />
                          <span className="text-xs text-slate-400">{item.name}</span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            </div>

            {/* Resource Utilization - Area Chart */}
            <motion.div variants={itemVariants}>
              <Card className="bg-surface-100 border-white/5">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Zap className="h-5 w-5 text-yellow-500" />
                    资源负载趋势
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="h-[250px] w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={resourceData}
                        margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                        <defs>
                          <linearGradient id="colorMech" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3}/>
                            <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
                          </linearGradient>
                          <linearGradient id="colorElec" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                            <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                          </linearGradient>
                        </defs>
                        <XAxis dataKey="name" stroke="#52525b" tickLine={false} axisLine={false} />
                        <YAxis stroke="#52525b" tickLine={false} axisLine={false} />
                        <CartesianGrid strokeDasharray="3 3" stroke="#27272a" vertical={false} />
                        <Tooltip 
                          contentStyle={{ backgroundColor: '#18181b', borderColor: '#333', color: '#fff' }}
                        />
                        <Area 
                          type="monotone" 
                          dataKey="mechanical" 
                          name="机械设计"
                          stroke="#8b5cf6" 
                          fillOpacity={1} 
                          fill="url(#colorMech)" 
                        />
                        <Area 
                          type="monotone" 
                          dataKey="electrical" 
                          name="电气控制"
                          stroke="#3b82f6" 
                          fillOpacity={1} 
                          fill="url(#colorElec)" 
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>
            </motion.div>

          </div>

          {/* Right Column - Activity Feed (4/12) */}
          <div className="col-span-12 lg:col-span-4">
            <motion.div variants={itemVariants} className="sticky top-6">
              <Card className="bg-surface-100 border-white/5 h-full min-h-[500px]">
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <span>实时动态</span>
                    <Activity className="h-4 w-4 text-slate-500" />
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="relative border-l border-white/10 ml-3 space-y-8 py-2">
                    {activities.map((activity, index) => (
                      <div key={activity.id} className="relative pl-6 group">
                        {/* Timeline Dot */}
                        <div className={`
                          absolute -left-[5px] top-1 h-2.5 w-2.5 rounded-full border-2 border-surface-100 transition-colors duration-300
                          ${index === 0 ? 'bg-primary-500 animate-pulse' : 'bg-slate-600 group-hover:bg-primary-400'}
                        `} />
                        
                        <div className="flex flex-col gap-1">
                          <span className="text-xs font-mono text-slate-500 flex items-center gap-2">
                            <Clock className="h-3 w-3" />
                            {activity.time}
                          </span>
                          <p className="text-sm text-slate-200 leading-snug group-hover:text-white transition-colors">
                            {activity.message}
                          </p>
                          <div className={`
                            text-[10px] px-2 py-0.5 rounded-full w-fit mt-1 border
                            ${activity.type === 'alert' ? 'bg-red-500/10 text-red-400 border-red-500/20' : 
                              activity.type === 'success' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 
                              'bg-primary-500/10 text-primary-400 border-primary-500/20'}
                          `}>
                            {activity.type.toUpperCase()}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                  
                  <div className="mt-8 pt-4 border-t border-white/5 text-center">
                    <button className="text-xs text-slate-500 hover:text-primary-400 transition-colors flex items-center justify-center gap-1 w-full">
                      查看全部动态 <ArrowUpRight className="h-3 w-3" />
                    </button>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
