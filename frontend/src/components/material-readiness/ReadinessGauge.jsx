/**
 * Material Readiness Gauge Component
 * 物料准备状态仪表盘组件
 * 可视化显示物料准备进度和状态
 */

import { useMemo } from "react";
import { Card, CardContent } from "../../components/ui/card";
import { Progress } from "../../components/ui/progress";
import { Badge } from "../../components/ui/badge";
import { cn, formatPercentage } from "../../lib/utils";
import {
  getReadinessStatusConfig,
  calculateReadinessProgress,
  getReadinessColor,
  isMaterialReady,
  isMaterialDelayed,
  isMaterialInProgress } from
"@/lib/constants/materialReadiness";

/**
 * 物料准备状态环形仪表盘组件
 * @param {object} props - 组件属性
 * @param {number} props.progress - 进度值 (0-100)
 * @param {string} props.status - 状态名称
 * @param {string} props.title - 标题
 * @param {string} props.description - 描述
 * @param {boolean} props.showDetails - 是否显示详细信息
 * @param {string} props.size - 尺寸 ('sm', 'md', 'lg', 'xl')
 * @param {string} props.variant - 变体 ('default', 'success', 'warning', 'danger')
 * @returns {JSX.Element}
 */
export function ReadinessGauge({
  progress,
  status,
  title,
  description,
  showDetails = true,
  size = "md",
  variant = "default"
}) {
  // 获取状态配置
  const statusConfig = getReadinessStatusConfig(status);

  // 根据进度确定颜色
  const _progressColor = getReadinessColor(progress);

  // 根据尺寸计算大小
  const sizeConfig = {
    sm: {
      size: 120,
      strokeWidth: 8,
      textSize: "text-sm",
      progressSize: "h-1"
    },
    md: {
      size: 160,
      strokeWidth: 10,
      textSize: "text-base",
      progressSize: "h-2"
    },
    lg: {
      size: 200,
      strokeWidth: 12,
      textSize: "text-lg",
      progressSize: "h-2"
    },
    xl: {
      size: 240,
      strokeWidth: 16,
      textSize: "text-xl",
      progressSize: "h-3"
    }
  };

  const config = sizeConfig[size];

  // 计算SVG路径
  const radius = config.size / 2 - config.strokeWidth;
  const circumference = 2 * Math.PI * radius;
  const strokeDasharray = circumference;
  const strokeDashoffset = circumference - progress / 100 * circumference;

  // 根据变体设置样式
  const variantStyles = {
    default: {
      background: "bg-gray-200",
      progress: "bg-blue-500",
      text: "text-gray-700"
    },
    success: {
      background: "bg-green-200",
      progress: "bg-green-500",
      text: "text-green-700"
    },
    warning: {
      background: "bg-orange-200",
      progress: "bg-orange-500",
      text: "text-orange-700"
    },
    danger: {
      background: "bg-red-200",
      progress: "bg-red-500",
      text: "text-red-700"
    }
  };

  const styles = variantStyles[variant];

  return (
    <Card className="w-full">
      <CardContent className="p-6">
        <div className="flex flex-col items-center space-y-4">
          {/* 环形进度条 */}
          <div className="relative">
            <svg
              width={config.size}
              height={config.size}
              className="transform -rotate-90">

              {/* 背景圆 */}
              <circle
                cx={config.size / 2}
                cy={config.size / 2}
                r={radius}
                stroke="currentColor"
                strokeWidth={config.strokeWidth}
                fill="none"
                className={styles.background} />

              {/* 进度圆 */}
              <circle
                cx={config.size / 2}
                cy={config.size / 2}
                r={radius}
                stroke="currentColor"
                strokeWidth={config.strokeWidth}
                fill="none"
                strokeDasharray={strokeDasharray}
                strokeDashoffset={strokeDashoffset}
                strokeLinecap="round"
                className={`${styles.progress} transition-all duration-500 ease-in-out`} />

            </svg>
            {/* 中心文本 */}
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className={`${config.textSize} font-bold`}>
                {formatPercentage(progress)}
              </span>
              <span className="text-xs text-gray-500">完成度</span>
            </div>
          </div>

          {/* 信息 */}
          {showDetails &&
          <div className="text-center space-y-1">
              {title &&
            <h3 className="text-sm font-semibold text-gray-700">
                  {title}
            </h3>
            }
              {description &&
            <p className="text-xs text-gray-500">
                  {description}
            </p>
            }
              <Badge
              className={cn(
                statusConfig.color,
                statusConfig.textColor
              )}>

                {statusConfig.label}
              </Badge>
          </div>
          }
        </div>
      </CardContent>
    </Card>);

}

/**
 * 物料准备状态仪表板组件
 * 显示多个物料的准备状态统计
 */
export function ReadinessDashboard({
  materials,
  title,
  subtitle,
  showFilters = false,
  onFilterChange: _onFilterChange,
  className
}) {
  // 计算统计数据
  const stats = useMemo(() => {
    const total = materials?.length;
    const ready = (materials || []).filter((m) => isMaterialReady(m.readiness_status)).length;
    const inProgress = (materials || []).filter((m) => isMaterialInProgress(m.readiness_status)).length;
    const delayed = (materials || []).filter((m) => isMaterialDelayed(m.readiness_status)).length;

    // 计算平均进度
    const totalProgress = (materials || []).reduce((sum, m) => {
      return sum + calculateReadinessProgress(m.readiness_status);
    }, 0);
    const avgProgress = total > 0 ? Math.round(totalProgress / total) : 0;

    return {
      total,
      ready,
      inProgress,
      delayed,
      avgProgress,
      completionRate: total > 0 ? Math.round(ready / total * 100) : 0,
      onTimeRate: total > 0 ? Math.round((total - delayed) / total * 100) : 0
    };
  }, [materials]);

  // 统计卡片数据
  const statCards = [
  {
    title: "物料总数",
    value: stats.total,
    color: "bg-blue-500",
    textColor: "text-blue-50",
    icon: "📦"
  },
  {
    title: "已就绪",
    value: stats.ready,
    color: "bg-green-500",
    textColor: "text-green-50",
    icon: "✅"
  },
  {
    title: "进行中",
    value: stats.inProgress,
    color: "bg-orange-500",
    textColor: "text-orange-50",
    icon: "⏳"
  },
  {
    title: "延期",
    value: stats.delayed,
    color: "bg-red-500",
    textColor: "text-red-50",
    icon: "⚠️"
  }];


  return (
    <div className={cn("space-y-6", className)}>
      {/* 标题 */}
      {(title || subtitle) &&
      <div className="space-y-2">
          {title &&
        <h2 className="text-2xl font-bold text-gray-900">
              {title}
        </h2>
        }
          {subtitle &&
        <p className="text-gray-600">
              {subtitle}
        </p>
        }
      </div>
      }

      {/* 过滤器 */}
      {showFilters &&
      <div className="flex space-x-2">
          <button className="px-3 py-1 text-sm bg-gray-100 rounded-full hover:bg-gray-200">
            全部 ({stats.total})
          </button>
          <button className="px-3 py-1 text-sm bg-green-100 text-green-700 rounded-full hover:bg-green-200">
            已就绪 ({stats.ready})
          </button>
          <button className="px-3 py-1 text-sm bg-orange-100 text-orange-700 rounded-full hover:bg-orange-200">
            进行中 ({stats.inProgress})
          </button>
          <button className="px-3 py-1 text-sm bg-red-100 text-red-700 rounded-full hover:bg-red-200">
            延期 ({stats.delayed})
          </button>
      </div>
      }

      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {(statCards || []).map((stat, index) =>
        <Card key={index}>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">
                    {stat.title}
                  </p>
                  <p className="text-2xl font-bold text-gray-900">
                    {stat.value}
                  </p>
                </div>
                <div className={cn(
                "p-3 rounded-full",
                stat.color,
                stat.textColor
              )}>
                  <span className="text-lg">
                    {stat.icon}
                  </span>
                </div>
              </div>
              {stat.title === "已就绪" && stats.total > 0 &&
            <p className="text-xs text-gray-500 mt-2">
                  完成率 {stats.completionRate}%
            </p>
            }
            </CardContent>
        </Card>
        )}
      </div>

      {/* 仪表盘 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* 总体进度 */}
        <ReadinessGauge
          progress={stats.avgProgress}
          status={stats.avgProgress >= 100 ? "READY_FOR_PRODUCTION" :
          stats.avgProgress >= 50 ? "SUPPLIER_PROCESSING" :
          stats.avgProgress >= 20 ? "PROCUREMENT_APPROVED" : "NOT_STARTED"}
          title="总体准备进度"
          description={`${stats.total} 个物料的平均准备进度`}
          size="lg" />


        {/* 完成率 */}
        <ReadinessGauge
          progress={stats.completionRate}
          status={stats.completionRate === 100 ? "READY_FOR_PRODUCTION" :
          stats.completionRate >= 80 ? "INSPECTED" :
          stats.completionRate >= 50 ? "FULLY_SHIPPED" : "IN_PROGRESS"}
          title="物料完成率"
          description={`${stats.ready} / ${stats.total} 个物料已就绪`}
          size="lg"
          variant={stats.completionRate >= 80 ? "success" :
          stats.completionRate >= 50 ? "warning" : "default"} />


        {/* 准时率 */}
        <ReadinessGauge
          progress={stats.onTimeRate}
          status={stats.onTimeRate === 100 ? "READY_FOR_PRODUCTION" :
          stats.onTimeRate >= 80 ? "INSPECTED" :
          stats.onTimeRate >= 50 ? "SUPPLIER_PROCESSING" : "DELAYED"}
          title="交付准时率"
          description={`${stats.total - stats.delayed} / ${stats.total} 个物料准时交付`}
          size="lg"
          variant={stats.onTimeRate >= 80 ? "success" :
          stats.onTimeRate >= 50 ? "warning" : "danger"} />

      </div>

      {/* 进度条 */}
      <Card>
        <CardContent className="p-6">
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-700">
              物料准备状态分布
            </h3>

            {/* 已就绪 */}
            <div className="space-y-1">
              <div className="flex justify-between text-sm">
                <span className="flex items-center">
                  <span className="w-3 h-3 bg-green-500 rounded-full mr-2" />
                  已就绪
                </span>
                <span>{stats.ready} ({stats.completionRate}%)</span>
              </div>
              <Progress value={stats.completionRate} className="h-2" />
            </div>

            {/* 进行中 */}
            <div className="space-y-1">
              <div className="flex justify-between text-sm">
                <span className="flex items-center">
                  <span className="w-3 h-3 bg-orange-500 rounded-full mr-2" />
                  进行中
                </span>
                <span>{stats.inProgress} ({Math.round(stats.inProgress / stats.total * 100)}%)</span>
              </div>
              <Progress
                value={Math.round(stats.inProgress / stats.total * 100)}
                className="h-2" />

            </div>

            {/* 延期 */}
            <div className="space-y-1">
              <div className="flex justify-between text-sm">
                <span className="flex items-center">
                  <span className="w-3 h-3 bg-red-500 rounded-full mr-2" />
                  延期
                </span>
                <span>{stats.delayed} ({Math.round(stats.delayed / stats.total * 100)}%)</span>
              </div>
              <Progress
                value={Math.round(stats.delayed / stats.total * 100)}
                className="h-2" />

            </div>
          </div>
        </CardContent>
      </Card>
    </div>);

}

export default ReadinessGauge;