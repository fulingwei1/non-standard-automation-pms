import { useEffect, useState } from "react";
import { useSearchParams, Link } from "react-router-dom";
import { formatDate } from "@/lib/formatters";
import { managementRhythmApi } from "../services/api";
import { PageHeader } from "../components/layout/PageHeader";
import { Card, CardContent, Badge, Button } from "../components/ui";
import {
  Calendar,
  Filter,
  Target,
  TrendingUp,
  Settings,
  CheckCircle2,
  Clock,
  AlertTriangle,
} from "lucide-react";

const rhythmLevelConfig = {
  STRATEGIC: { label: "战略层", color: "bg-purple-500", icon: Target },
  OPERATIONAL: { label: "经营层", color: "bg-blue-500", icon: TrendingUp },
  OPERATION: { label: "运营层", color: "bg-green-500", icon: Settings },
  TASK: { label: "任务层", color: "bg-orange-500", icon: CheckCircle2 },
};

const statusConfig = {
  SCHEDULED: { label: "已安排", color: "bg-gray-500" },
  ONGOING: { label: "进行中", color: "bg-blue-500" },
  COMPLETED: { label: "已完成", color: "bg-green-500" },
  CANCELLED: { label: "已取消", color: "bg-red-500" },
};

export default function MeetingMap() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [loading, setLoading] = useState(true);
  const [meetings, setMeetings] = useState([]);
  const [byLevel, setByLevel] = useState([]);
  const [byCycle, setByCycle] = useState([]);
  const [filters, setFilters] = useState({
    rhythm_level: searchParams.get("rhythm_level") || "",
    cycle_type: searchParams.get("cycle_type") || "",
  });

  useEffect(() => {
    fetchMeetingMap();
  }, [filters]);

  const fetchMeetingMap = async () => {
    try {
      setLoading(true);
      const params = {};
      if (filters.rhythm_level) {params.rhythm_level = filters.rhythm_level;}
      if (filters.cycle_type) {params.cycle_type = filters.cycle_type;}

      const res = await managementRhythmApi.meetingMap.get(params);
      const data = res.data || res;
      setMeetings(data.items || []);
      setByLevel(data.by_level || {});
      setByCycle(data.by_cycle || {});
    } catch (err) {
      console.error("Failed to fetch meeting map:", err);
      setMeetings([]);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (key, value) => {
    const newFilters = { ...filters, [key]: value };
    setFilters(newFilters);
    const params = new URLSearchParams();
    if (newFilters.rhythm_level)
      {params.set("rhythm_level", newFilters.rhythm_level);}
    if (newFilters.cycle_type) {params.set("cycle_type", newFilters.cycle_type);}
    setSearchParams(params);
  };


  const formatTime = (timeStr) => {
    if (!timeStr) {return "";}
    return timeStr.substring(0, 5);
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="会议地图"
        description="按周期和层级组织的会议视图，清晰展示管理节律"
      />

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-4">
            <Filter className="w-5 h-5 text-gray-400" />
            <div className="flex items-center gap-2">
              <label className="text-sm text-gray-600">层级:</label>
              <select
                value={filters.rhythm_level}
                onChange={(e) =>
                  handleFilterChange("rhythm_level", e.target.value)
                }
                className="px-3 py-1 border rounded-md text-sm"
              >
                <option value="">全部</option>
                {Object.entries(rhythmLevelConfig).map(([key, config]) => (
                  <option key={key} value={key}>
                    {config.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex items-center gap-2">
              <label className="text-sm text-gray-600">周期:</label>
              <select
                value={filters.cycle_type}
                onChange={(e) =>
                  handleFilterChange("cycle_type", e.target.value)
                }
                className="px-3 py-1 border rounded-md text-sm"
              >
                <option value="">全部</option>
                <option value="QUARTERLY">季度</option>
                <option value="MONTHLY">月度</option>
                <option value="WEEKLY">周度</option>
                <option value="DAILY">每日</option>
              </select>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setFilters({ rhythm_level: "", cycle_type: "" });
                setSearchParams({});
              }}
            >
              清除筛选
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* By Level View */}
      {Object.keys(byLevel).length > 0 && (
        <div className="space-y-4">
          <h2 className="text-xl font-semibold">按层级查看</h2>
          {Object.entries(byLevel).map(([level, items]) => {
            const config = rhythmLevelConfig[level];
            if (!config) {return null;}
            const Icon = config.icon;

            return (
              <Card key={level}>
                <CardContent className="p-6">
                  <div className="flex items-center gap-3 mb-4">
                    <div
                      className={`p-2 rounded-lg ${config.color} text-white`}
                    >
                      <Icon className="w-5 h-5" />
                    </div>
                    <h3 className="text-lg font-semibold">{config.label}</h3>
                    <Badge>{items?.length} 场会议</Badge>
                  </div>
                  <div className="space-y-2">
                    {(items || []).map((meeting) => {
                      const status =
                        statusConfig[meeting.status] || statusConfig.SCHEDULED;
                      return (
                        <Link
                          key={meeting.id}
                          to={`/strategic-meetings/${meeting.id}`}
                          className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50 transition-colors"
                        >
                          <div className="flex items-center gap-3">
                            <Calendar className="w-4 h-4 text-gray-400" />
                            <div>
                              <div className="font-medium">
                                {meeting.meeting_name}
                              </div>
                              <div className="text-sm text-gray-500">
                                {formatDate(meeting.meeting_date)}
                                {meeting.start_time &&
                                  ` ${formatTime(meeting.start_time)}`}
                                {meeting.organizer_name &&
                                  ` · ${meeting.organizer_name}`}
                              </div>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            {meeting.action_items_count > 0 && (
                              <div className="text-sm text-gray-500">
                                {meeting.completed_action_items_count}/
                                {meeting.action_items_count} 行动项
                              </div>
                            )}
                            <Badge className={status.color}>
                              {status.label}
                            </Badge>
                          </div>
                        </Link>
                      );
                    })}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* By Cycle View */}
      {Object.keys(byCycle).length > 0 && (
        <div className="space-y-4">
          <h2 className="text-xl font-semibold">按周期查看</h2>
          {Object.entries(byCycle).map(([cycle, items]) => {
            const cycleLabels = {
              QUARTERLY: "季度",
              MONTHLY: "月度",
              WEEKLY: "周度",
              DAILY: "每日",
            };

            return (
              <Card key={cycle}>
                <CardContent className="p-6">
                  <div className="flex items-center gap-3 mb-4">
                    <Clock className="w-5 h-5 text-gray-400" />
                    <h3 className="text-lg font-semibold">
                      {cycleLabels[cycle] || cycle}
                    </h3>
                    <Badge>{items?.length} 场会议</Badge>
                  </div>
                  <div className="space-y-2">
                    {(items || []).map((meeting) => {
                      const status =
                        statusConfig[meeting.status] || statusConfig.SCHEDULED;
                      const config = rhythmLevelConfig[meeting.rhythm_level];
                      return (
                        <Link
                          key={meeting.id}
                          to={`/strategic-meetings/${meeting.id}`}
                          className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50 transition-colors"
                        >
                          <div className="flex items-center gap-3">
                            {config && (
                              <div
                                className={`p-1 rounded ${config.color} text-white`}
                              >
                                <config.icon className="w-3 h-3"  />
                              </div>
                            )}
                            <div>
                              <div className="font-medium">
                                {meeting.meeting_name}
                              </div>
                              <div className="text-sm text-gray-500">
                                {formatDate(meeting.meeting_date)}
                                {meeting.start_time &&
                                  ` ${formatTime(meeting.start_time)}`}
                              </div>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            {meeting.action_items_count > 0 && (
                              <div className="text-sm text-gray-500">
                                {meeting.completed_action_items_count}/
                                {meeting.action_items_count} 行动项
                              </div>
                            )}
                            <Badge className={status.color}>
                              {status.label}
                            </Badge>
                          </div>
                        </Link>
                      );
                    })}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {!loading && meetings.length === 0 && (
        <Card>
          <CardContent className="p-12 text-center">
            <Calendar className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500">暂无会议数据</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
