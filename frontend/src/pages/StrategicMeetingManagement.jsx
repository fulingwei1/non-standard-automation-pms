import { useEffect, useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { managementRhythmApi, projectApi } from "../services/api";
import { PageHeader } from "../components/layout/PageHeader";
import {
  Card,
  CardContent,
  Badge,
  Button,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle } from
"../components/ui";
import { formatDate } from "@/lib/formatters";
import {
  Plus,
  Edit,
  Calendar,
  Target,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Users,
  FileText } from
"lucide-react";

const rhythmLevelConfig = {
  STRATEGIC: { label: "战略层", color: "bg-purple-500" },
  OPERATIONAL: { label: "经营层", color: "bg-blue-500" },
  OPERATION: { label: "运营层", color: "bg-green-500" },
  TASK: { label: "任务层", color: "bg-orange-500" }
};

const statusConfig = {
  SCHEDULED: { label: "已安排", color: "bg-gray-500" },
  ONGOING: { label: "进行中", color: "bg-blue-500" },
  COMPLETED: { label: "已完成", color: "bg-green-500" },
  CANCELLED: { label: "已取消", color: "bg-red-500" }
};

export default function StrategicMeetingManagement() {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [meetings, setMeetings] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [filters, setFilters] = useState({
    rhythm_level: searchParams.get("rhythm_level") || "",
    cycle_type: searchParams.get("cycle_type") || "",
    status: searchParams.get("status") || "",
    keyword: searchParams.get("keyword") || ""
  });
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [_projects, setProjects] = useState([]);

  useEffect(() => {
    fetchMeetings();
    fetchProjects();
  }, [page, filters]);

  const fetchMeetings = async () => {
    try {
      setLoading(true);
      const params = {
        page,
        page_size: pageSize,
        ...filters
      };
      Object.keys(params).forEach((key) => {
        if (!params[key]) {delete params[key];}
      });

      const res = await managementRhythmApi.meetings.list(params);
      const data = res.data || res;
      if (data.items) {
        setMeetings(data.items);
        setTotal(data.total || 0);
      } else if (Array.isArray(data)) {
        setMeetings(data);
        setTotal(data?.length);
      }
    } catch (err) {
      console.error("Failed to fetch meetings:", err);
      setMeetings([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchProjects = async () => {
    try {
      const res = await projectApi.list({ page: 1, page_size: 100 });
      const data = res.data || res;
      if (data.items) {
        setProjects(data.items);
      } else if (Array.isArray(data)) {
        setProjects(data);
      }
    } catch (err) {
      console.error("Failed to fetch projects:", err);
    }
  };

  const handleFilterChange = (key, value) => {
    const newFilters = { ...filters, [key]: value };
    setFilters(newFilters);
    setPage(1);
    const params = new URLSearchParams();
    Object.entries(newFilters).forEach(([k, v]) => {
      if (v) {params.set(k, v);}
    });
    setSearchParams(params);
  };


  const formatTime = (timeStr) => {
    if (!timeStr) {return "";}
    return timeStr.substring(0, 5);
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="战略会议管理"
        description="管理战略、经营、运营、任务各层级的会议，跟踪行动项执行"
        action={
        <Button onClick={() => setCreateDialogOpen(true)}>
            <Plus className="w-4 h-4 mr-2" />
            创建会议
        </Button>
        } />


      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm text-gray-600 mb-1">层级</label>
              <select
                value={filters.rhythm_level}
                onChange={(e) =>
                handleFilterChange("rhythm_level", e.target.value)
                }
                className="w-full px-3 py-2 border rounded-md text-sm">

                <option value="">全部</option>
                {Object.entries(rhythmLevelConfig).map(([key, config]) =>
                <option key={key} value={key || "unknown"}>
                    {config.label}
                </option>
                )}
              </select>
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">周期</label>
              <select
                value={filters.cycle_type}
                onChange={(e) =>
                handleFilterChange("cycle_type", e.target.value)
                }
                className="w-full px-3 py-2 border rounded-md text-sm">

                <option value="">全部</option>
                <option value="QUARTERLY">季度</option>
                <option value="MONTHLY">月度</option>
                <option value="WEEKLY">周度</option>
                <option value="DAILY">每日</option>
              </select>
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">状态</label>
              <select
                value={filters.status}
                onChange={(e) => handleFilterChange("status", e.target.value)}
                className="w-full px-3 py-2 border rounded-md text-sm">

                <option value="">全部</option>
                {Object.entries(statusConfig).map(([key, config]) =>
                <option key={key} value={key || "unknown"}>
                    {config.label}
                </option>
                )}
              </select>
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">关键词</label>
              <input
                type="text"
                value={filters.keyword}
                onChange={(e) => handleFilterChange("keyword", e.target.value)}
                placeholder="搜索会议名称"
                className="w-full px-3 py-2 border rounded-md text-sm" />

            </div>
          </div>
        </CardContent>
      </Card>

      {/* Meetings List */}
      <div className="space-y-4">
        {loading ?
        <div className="space-y-3">
            {[1, 2, 3].map((i) =>
          <Card key={i}>
                <CardContent className="p-4">
                  <div className="h-20 bg-gray-200 rounded animate-pulse" />
                </CardContent>
          </Card>
          )}
        </div> :
        meetings.length > 0 ?
        (meetings || []).map((meeting) => {
          const levelConfig = rhythmLevelConfig[meeting.rhythm_level];
          const status =
          statusConfig[meeting.status] || statusConfig.SCHEDULED;
          const completionRate =
          meeting.action_items_count > 0 ?
          (
          meeting.completed_action_items_count /
          meeting.action_items_count *
          100).
          toFixed(0) :
          100;

          return (
            <Card
              key={meeting.id}
              className="hover:shadow-md transition-shadow">

                <CardContent className="p-6">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        {levelConfig &&
                      <Badge className={levelConfig.color}>
                            {levelConfig.label}
                      </Badge>
                      }
                        <h3 className="text-lg font-semibold">
                          {meeting.meeting_name}
                        </h3>
                        <Badge className={status.color}>{status.label}</Badge>
                      </div>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-gray-600 mb-4">
                        <div className="flex items-center gap-2">
                          <Calendar className="w-4 h-4" />
                          <span>{formatDate(meeting.meeting_date)}</span>
                          {meeting.start_time &&
                        <span className="text-gray-400">
                              {formatTime(meeting.start_time)}
                        </span>
                        }
                        </div>
                        {meeting.organizer_name &&
                      <div className="flex items-center gap-2">
                            <Users className="w-4 h-4" />
                            <span>{meeting.organizer_name}</span>
                      </div>
                      }
                        {meeting.location &&
                      <div className="flex items-center gap-2">
                            <Target className="w-4 h-4" />
                            <span>{meeting.location}</span>
                      </div>
                      }
                        {meeting.action_items_count > 0 &&
                      <div className="flex items-center gap-2">
                            <CheckCircle2 className="w-4 h-4" />
                            <span>
                              {meeting.completed_action_items_count}/
                              {meeting.action_items_count} 行动项
                            </span>
                      </div>
                      }
                      </div>
                      {meeting.action_items_count > 0 &&
                    <div className="mb-4">
                          <div className="flex items-center justify-between text-sm mb-1">
                            <span className="text-gray-600">行动项完成率</span>
                            <span className="font-medium">
                              {completionRate}%
                            </span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div
                          className={`h-2 rounded-full ${
                          completionRate >= 90 ?
                          "bg-green-500" :
                          completionRate >= 70 ?
                          "bg-yellow-500" :
                          "bg-red-500"}`
                          }
                          style={{ width: `${completionRate}%` }} />

                          </div>
                    </div>
                    }
                      {meeting.agenda &&
                    <div className="text-sm text-gray-600 mb-2">
                          <FileText className="w-4 h-4 inline mr-1" />
                          {meeting.agenda.substring(0, 100)}
                          {meeting.agenda?.length > 100 && "..."}
                    </div>
                    }
                    </div>
                    <div className="flex items-center gap-2 ml-4">
                      <Button
                      variant="outline"
                      size="sm"
                      onClick={() =>
                      navigate(`/strategic-meetings/${meeting.id}`)
                      }>

                        <Edit className="w-4 h-4 mr-1" />
                        查看
                      </Button>
                    </div>
                  </div>
                </CardContent>
            </Card>);

        }) :

        <Card>
            <CardContent className="p-12 text-center">
              <Calendar className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500">暂无会议数据</p>
            </CardContent>
        </Card>
        }
      </div>

      {/* Pagination */}
      {total > pageSize &&
      <div className="flex items-center justify-between">
          <div className="text-sm text-gray-600">
            共 {total} 条记录，第 {page} / {Math.ceil(total / pageSize)} 页
          </div>
          <div className="flex gap-2">
            <Button
            variant="outline"
            size="sm"
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}>

              上一页
            </Button>
            <Button
            variant="outline"
            size="sm"
            onClick={() =>
            setPage((p) => Math.min(Math.ceil(total / pageSize), p + 1))
            }
            disabled={page >= Math.ceil(total / pageSize)}>

              下一页
            </Button>
          </div>
      </div>
      }

      {/* Create Meeting Dialog - Simplified for now */}
      <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>创建会议</DialogTitle>
          </DialogHeader>
          <div className="p-4">
            <p className="text-gray-500">会议创建表单将在后续实现</p>
            <Button onClick={() => setCreateDialogOpen(false)} className="mt-4">
              关闭
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>);

}