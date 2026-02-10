import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { managementRhythmApi } from "../services/api";
import { PageHeader } from "../components/layout/PageHeader";
import {
  Card,
  CardContent,
  DashboardStatCard,
  Badge,
  SkeletonCard,
} from "../components/ui";
import {
  Target,
  TrendingUp,
  Settings,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Calendar,
  Activity,
} from "lucide-react";

const rhythmLevelConfig = {
  STRATEGIC: {
    label: "战略层",
    color: "bg-purple-500",
    icon: Target,
    description: "长周期(5-10年)、中周期(3-5年)、短周期(1年内)",
  },
  OPERATIONAL: {
    label: "经营层",
    color: "bg-blue-500",
    icon: TrendingUp,
    description: "年度经营计划、月度经营分析、滚动预测",
  },
  OPERATION: {
    label: "运营层",
    color: "bg-green-500",
    icon: Settings,
    description: "周运营例会、项目管理、异常处理",
  },
  TASK: {
    label: "任务层",
    color: "bg-orange-500",
    icon: CheckCircle2,
    description: "日清会、根因分析、1-1教练",
  },
};

const healthStatusConfig = {
  GREEN: { label: "正常", color: "bg-green-500", textColor: "text-green-700" },
  YELLOW: {
    label: "有风险",
    color: "bg-yellow-500",
    textColor: "text-yellow-700",
  },
  RED: { label: "阻塞", color: "bg-red-500", textColor: "text-red-700" },
};

export default function ManagementRhythmDashboard() {
  const [loading, setLoading] = useState(true);
  const [dashboardData, setDashboardData] = useState({
    strategic: null,
    operational: null,
    operation: null,
    task: null,
  });

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const res = await managementRhythmApi.dashboard.get();
      const data = res.data || res;
      setDashboardData({
        strategic: data.strategic || null,
        operational: data.operational || null,
        operation: data.operation || null,
        task: data.task || null,
      });
    } catch (err) {
      console.error("Failed to fetch dashboard data:", err);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) {return "-";}
    const date = new Date(dateStr);
    return date.toLocaleDateString("zh-CN", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
    });
  };

  const calculateDaysUntil = (dateStr) => {
    if (!dateStr) {return null;}
    const targetDate = new Date(dateStr);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    targetDate.setHours(0, 0, 0, 0);
    const diffTime = targetDate - today;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  const renderLevelCard = (level, data) => {
    const config = rhythmLevelConfig[level];
    if (!config) {return null;}

    const Icon = config.icon;
    const healthConfig = data ? healthStatusConfig[data.health_status] : null;
    const daysUntil = data?.next_meeting_date
      ? calculateDaysUntil(data.next_meeting_date)
      : null;

    return (
      <motion.div
        key={level}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <Card className="h-full">
          <CardContent className="p-6">
            {/* Header */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className={`p-3 rounded-lg ${config.color} text-white`}>
                  <Icon className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold">{config.label}</h3>
                  <p className="text-sm text-gray-500">{config.description}</p>
                </div>
              </div>
              {healthConfig && (
                <Badge className={`${healthConfig.color} text-white`}>
                  {healthConfig.label}
                </Badge>
              )}
            </div>

            {loading ? (
              <div className="space-y-3">
                <div className="h-4 bg-gray-200 rounded animate-pulse" />
                <div className="h-4 bg-gray-200 rounded animate-pulse w-3/4" />
                <div className="h-4 bg-gray-200 rounded animate-pulse w-1/2" />
              </div>
            ) : data ? (
              <div className="space-y-4">
                {/* Current Cycle */}
                {data.current_cycle && (
                  <div className="flex items-center gap-2 text-sm">
                    <Calendar className="w-4 h-4 text-gray-400" />
                    <span className="text-gray-600">当前周期:</span>
                    <span className="font-medium">{data.current_cycle}</span>
                  </div>
                )}

                {/* Next Meeting */}
                {data.next_meeting_date && (
                  <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                    <div className="flex items-center gap-2">
                      <Clock className="w-4 h-4 text-blue-600" />
                      <span className="text-sm text-gray-700">下次会议:</span>
                      <span className="text-sm font-medium">
                        {formatDate(data.next_meeting_date)}
                      </span>
                    </div>
                    {daysUntil !== null && (
                      <Badge
                        variant={daysUntil <= 3 ? "destructive" : "default"}
                      >
                        {daysUntil > 0
                          ? `${daysUntil}天后`
                          : daysUntil === 0
                            ? "今天"
                            : "已过期"}
                      </Badge>
                    )}
                  </div>
                )}

                {/* Statistics Grid */}
                <div className="grid grid-cols-2 gap-3">
                  <DashboardStatCard
                    label="会议总数"
                    value={data.meetings_count || 0}
                    icon={Activity}
                    className="bg-gray-50"
                  />
                  <DashboardStatCard
                    label="已完成"
                    value={data.completed_meetings_count || 0}
                    icon={CheckCircle2}
                    className="bg-green-50"
                  />
                  <DashboardStatCard
                    label="行动项总数"
                    value={data.total_action_items || 0}
                    icon={Target}
                    className="bg-blue-50"
                  />
                  <DashboardStatCard
                    label="已完成"
                    value={data.completed_action_items || 0}
                    icon={CheckCircle2}
                    className="bg-green-50"
                  />
                </div>

                {/* Action Items Progress */}
                {data.total_action_items > 0 && (
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-600">行动项完成率</span>
                      <span className="font-medium">
                        {data.completion_rate || "0%"}
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${
                          data.health_status === "GREEN"
                            ? "bg-green-500"
                            : data.health_status === "YELLOW"
                              ? "bg-yellow-500"
                              : "bg-red-500"
                        }`}
                        style={{
                          width: `${parseFloat(data.completion_rate || "0")}%`,
                        }}
                      />
                    </div>
                    {data.overdue_action_items > 0 && (
                      <div className="flex items-center gap-2 text-sm text-red-600">
                        <AlertTriangle className="w-4 h-4" />
                        <span>{data.overdue_action_items} 项逾期</span>
                      </div>
                    )}
                  </div>
                )}

                {/* Last Meeting */}
                {data.last_meeting_date && (
                  <div className="pt-3 border-t">
                    <div className="flex items-center gap-2 text-sm text-gray-600">
                      <Clock className="w-4 h-4" />
                      <span>
                        上次会议: {formatDate(data.last_meeting_date)}
                      </span>
                    </div>
                  </div>
                )}

                {/* View Details Link */}
                <Link
                  to={`/meeting-map?rhythm_level=${level}`}
                  className="block mt-4 text-center text-sm text-blue-600 hover:text-blue-800"
                >
                  查看详情 →
                </Link>
              </div>
            ) : (
              <div className="text-center py-8 text-gray-400">
                <p>暂无数据</p>
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>
    );
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="管理节律仪表盘"
        description="战略-经营-运营-管理节律可视化，连接战略意图与执行落地"
      />

      {/* Four Level Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {renderLevelCard("STRATEGIC", dashboardData.strategic)}
        {renderLevelCard("OPERATIONAL", dashboardData.operational)}
        {renderLevelCard("OPERATION", dashboardData.operation)}
        {renderLevelCard("TASK", dashboardData.task)}
      </div>

      {/* Quick Actions */}
      <Card>
        <CardContent className="p-6">
          <h3 className="text-lg font-semibold mb-4">快速操作</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Link
              to="/meeting-map"
              className="flex items-center gap-3 p-4 border rounded-lg hover:bg-gray-50 transition-colors"
            >
              <Calendar className="w-5 h-5 text-blue-600" />
              <div>
                <div className="font-medium">会议地图</div>
                <div className="text-sm text-gray-500">查看所有会议安排</div>
              </div>
            </Link>
            <Link
              to="/strategic-meetings"
              className="flex items-center gap-3 p-4 border rounded-lg hover:bg-gray-50 transition-colors"
            >
              <Target className="w-5 h-5 text-purple-600" />
              <div>
                <div className="font-medium">战略会议</div>
                <div className="text-sm text-gray-500">管理会议和行动项</div>
              </div>
            </Link>
            <Link
              to="/rhythm-config"
              className="flex items-center gap-3 p-4 border rounded-lg hover:bg-gray-50 transition-colors"
            >
              <Settings className="w-5 h-5 text-gray-600" />
              <div>
                <div className="font-medium">节律配置</div>
                <div className="text-sm text-gray-500">配置会议模板和指标</div>
              </div>
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
