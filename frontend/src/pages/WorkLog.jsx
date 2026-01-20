/**
 * Work Log Page - 工作日志页面
 * Features: 每日工作日志提交，@提及项目/设备/人员，自动关联到项目进展
 */
import { useState, useEffect } from "react";
import {
  FileText,
  AtSign,
  Save,
  Edit,
  Trash2,
  Sparkles,
  CheckCircle2,
  XCircle,
  Clock,
  Briefcase,
  RefreshCw,
} from "lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";

import { Textarea } from "../components/ui/textarea";
import { cn, formatDate } from "../lib/utils";
import { workLogApi } from "../services/api";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "../components/ui/dialog";

export default function WorkLog() {
  const [loading, setLoading] = useState(false);
  const [workLogs, setWorkLogs] = useState([]);
  const [mentionOptions, setMentionOptions] = useState({
    projects: [],
    machines: [],
    users: [],
  });

  // 表单数据
  const [workDate, setWorkDate] = useState(
    new Date().toISOString().split("T")[0],
  );
  const [content, setContent] = useState("");
  const [mentionedProjects, setMentionedProjects] = useState([]);
  const [mentionedMachines, setMentionedMachines] = useState([]);
  const [mentionedUsers, setMentionedUsers] = useState([]);
  const [status, setStatus] = useState("SUBMITTED");

  // 编辑相关
  const [editingId, setEditingId] = useState(null);

  // 分页
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [total, setTotal] = useState(0);

  // 筛选
  const [filterStartDate, setFilterStartDate] = useState("");
  const [filterEndDate, setFilterEndDate] = useState("");

  // AI分析相关
  const [aiAnalysis, setAiAnalysis] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [showAiSuggestions, setShowAiSuggestions] = useState(false);
  const [suggestedProjects, setSuggestedProjects] = useState([]);
  const [selectedWorkItems, setSelectedWorkItems] = useState([]);

  useEffect(() => {
    fetchMentionOptions();
    fetchWorkLogs();
    fetchSuggestedProjects();
  }, [page, filterStartDate, filterEndDate]);

  // 当工作内容变化时，自动触发AI分析（防抖）
  useEffect(() => {
    if (!content.trim() || content.length < 10) {
      setAiAnalysis(null);
      return;
    }

    const timer = setTimeout(() => {
      handleAiAnalyze();
    }, 1500); // 1.5秒防抖

    return () => clearTimeout(timer);
  }, [content, workDate]);

  const fetchMentionOptions = async () => {
    try {
      const res = await workLogApi.getMentionOptions();
      const data = res.data?.data || res.data || {};
      setMentionOptions({
        projects: data.projects || [],
        machines: data.machines || [],
        users: data.users || [],
      });
    } catch (error) {
      console.error("Failed to fetch mention options:", error);
    }
  };

  const fetchSuggestedProjects = async () => {
    try {
      const res = await workLogApi.getSuggestedProjects();
      const data = res.data?.data || res.data || {};
      setSuggestedProjects(data.projects || []);
    } catch (error) {
      console.error("Failed to fetch suggested projects:", error);
    }
  };

  const handleAiAnalyze = async () => {
    if (!content.trim() || content.length < 10) {
      return;
    }

    setAnalyzing(true);
    try {
      const res = await workLogApi.aiAnalyze(content, workDate);
      const analysisData = res.data?.data || res.data || {};

      if (analysisData.work_items && analysisData.work_items.length > 0) {
        setAiAnalysis(analysisData);
        // 默认选中所有工作项
        setSelectedWorkItems(analysisData.work_items.map((_, index) => index));
        setShowAiSuggestions(true);
      }
    } catch (error) {
      console.error("AI分析失败:", error);
      // AI分析失败不影响工作日志提交
    } finally {
      setAnalyzing(false);
    }
  };

  const handleApplyAiSuggestions = () => {
    if (!aiAnalysis || selectedWorkItems.length === 0) {
      return;
    }

    // 应用选中的工作项
    const itemsToApply = aiAnalysis.work_items.filter((_, index) =>
      selectedWorkItems.includes(index),
    );

    // 这里可以自动创建工作日志和工时记录
    // 或者提示用户确认
    setShowAiSuggestions(false);

    // 显示确认对话框
    const totalHours = itemsToApply.reduce(
      (sum, item) => sum + (item.hours || 0),
      0,
    );
    const projects = itemsToApply
      .map((item) => item.project_name || "未分配项目")
      .filter((v, i, a) => a.indexOf(v) === i);

    if (
      confirm(
        `AI分析建议：\n` +
          `- 共 ${itemsToApply.length} 个工作项\n` +
          `- 总工时：${totalHours.toFixed(1)} 小时\n` +
          `- 涉及项目：${projects.join("、")}\n\n` +
          `是否应用这些建议并自动创建工时记录？`,
      )
    ) {
      // 应用建议：创建工作日志（含工时信息）
      handleSubmitWithTimesheet(itemsToApply);
    }
  };

  const handleSubmitWithTimesheet = async (workItems) => {
    try {
      // 为每个工作项创建工时记录
      // 这里需要调用批量创建工时API
      const timesheets = workItems.map((item) => ({
        project_id: item.project_id,
        work_date: workDate,
        work_hours: item.hours,
        work_type: item.work_type || "NORMAL",
        description: item.work_content,
      }));

      // 先创建工作日志
      const workLogData = {
        work_date: workDate,
        content: content.trim(),
        mentioned_projects: workItems
          .map((item) => item.project_id)
          .filter(Boolean),
        status: "SUBMITTED",
        // 如果有多个工作项，使用第一个的工时作为工作日志的工时
        work_hours: workItems[0]?.hours || null,
        project_id: workItems[0]?.project_id || null,
      };

      await workLogApi.create(workLogData);

      // 然后批量创建工时记录
      if (timesheets.length > 0) {
        const { timesheetApi } = await import("../services/api");
        await timesheetApi.batchCreate({ timesheets });
      }

      alert("工作日志和工时记录创建成功！");
      resetForm();
      fetchWorkLogs();
    } catch (error) {
      console.error("Failed to create work log with timesheet:", error);
      alert("创建失败: " + (error.response?.data?.detail || error.message));
    }
  };

  const fetchWorkLogs = async () => {
    try {
      setLoading(true);
      const params = {
        page,
        page_size: pageSize,
      };
      if (filterStartDate) {params.start_date = filterStartDate;}
      if (filterEndDate) {params.end_date = filterEndDate;}

      const res = await workLogApi.list(params);
      const data = res.data?.data || res.data || {};
      setWorkLogs(data.items || []);
      setTotal(data.total || 0);
    } catch (error) {
      console.error("Failed to fetch work logs:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (!content.trim()) {
      alert("请填写工作内容");
      return;
    }

    if (content.length > 300) {
      alert("工作内容不能超过300字");
      return;
    }

    try {
      const data = {
        work_date: workDate,
        content: content.trim(),
        mentioned_projects: mentionedProjects,
        mentioned_machines: mentionedMachines,
        mentioned_users: mentionedUsers,
        status,
      };

      if (editingId) {
        await workLogApi.update(editingId, data);
        alert("工作日志更新成功");
      } else {
        await workLogApi.create(data);
        alert("工作日志提交成功");
      }

      // 重置表单
      resetForm();
      fetchWorkLogs();

      // 清除AI分析结果
      setAiAnalysis(null);
      setSelectedWorkItems([]);
    } catch (error) {
      console.error("Failed to submit work log:", error);
      alert("提交失败: " + (error.response?.data?.detail || error.message));
    }
  };

  const handleEdit = (workLog) => {
    if (workLog.status !== "DRAFT") {
      alert("只能编辑草稿状态的工作日志");
      return;
    }

    setEditingId(workLog.id);
    setWorkDate(workLog.work_date);
    setContent(workLog.content);
    setStatus(workLog.status);

    // 设置提及
    const projects =
      workLog.mentions
        ?.filter((m) => m.mention_type === "PROJECT")
        .map((m) => m.mention_id) || [];
    const machines =
      workLog.mentions
        ?.filter((m) => m.mention_type === "MACHINE")
        .map((m) => m.mention_id) || [];
    const users =
      workLog.mentions
        ?.filter((m) => m.mention_type === "USER")
        .map((m) => m.mention_id) || [];

    setMentionedProjects(projects);
    setMentionedMachines(machines);
    setMentionedUsers(users);
  };

  const handleDelete = async (id) => {
    if (!confirm("确定要删除这条工作日志吗？")) {return;}

    try {
      await workLogApi.delete(id);
      alert("删除成功");
      fetchWorkLogs();
    } catch (error) {
      console.error("Failed to delete work log:", error);
      alert("删除失败: " + (error.response?.data?.detail || error.message));
    }
  };

  const resetForm = () => {
    setEditingId(null);
    setWorkDate(new Date().toISOString().split("T")[0]);
    setContent("");
    setMentionedProjects([]);
    setMentionedMachines([]);
    setMentionedUsers([]);
    setStatus("SUBMITTED");
    setAiAnalysis(null);
    setSelectedWorkItems([]);
    setShowAiSuggestions(false);
  };

  const getStatusBadge = (status) => {
    if (status === "SUBMITTED") {
      return <Badge className="bg-green-500">已提交</Badge>;
    }
    return <Badge variant="outline">草稿</Badge>;
  };

  const wordCount = content.length;
  const maxWords = 300;

  return (
    <div className="space-y-6 p-6">
      <PageHeader
        title="工作日志"
        description="记录每日工作内容，@提及项目、设备或人员，自动关联到项目进展"
      />

      {/* 提交表单 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            提交工作日志
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">
                工作日期 <span className="text-red-500">*</span>
              </label>
              <Input
                type="date"
                value={workDate}
                onChange={(e) => setWorkDate(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">状态</label>
              <Select value={status} onValueChange={setStatus}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="DRAFT">草稿</SelectItem>
                  <SelectItem value="SUBMITTED">已提交</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">
              工作内容 <span className="text-red-500">*</span>
              <span className="text-sm text-gray-500 ml-2">
                ({wordCount}/{maxWords} 字)
              </span>
            </label>
            <div className="relative">
              <Textarea
                value={content}
                onChange={(e) => {
                  const value = e.target.value;
                  if (value.length <= maxWords) {
                    setContent(value);
                    // 清除之前的分析结果
                    if (value.length < 10) {
                      setAiAnalysis(null);
                    }
                  }
                }}
                placeholder="请输入工作内容（不超过300字）...&#10;&#10;💡 提示：输入工作内容后，AI会自动分析并建议工时和项目关联"
                rows={6}
                className={cn(
                  wordCount > maxWords && "border-red-500",
                  analyzing && "border-blue-500",
                )}
              />
              {analyzing && (
                <div className="absolute top-2 right-2 flex items-center gap-2 text-blue-500 text-sm">
                  <RefreshCw className="h-4 w-4 animate-spin" />
                  <span>AI分析中...</span>
                </div>
              )}
              {aiAnalysis && !analyzing && (
                <div className="absolute top-2 right-2">
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => setShowAiSuggestions(true)}
                    className="bg-blue-50 hover:bg-blue-100 border-blue-300"
                  >
                    <Sparkles className="h-4 w-4 mr-1" />
                    查看AI建议
                  </Button>
                </div>
              )}
            </div>
            {wordCount > maxWords && (
              <p className="text-sm text-red-500 mt-1">
                字数超出限制，请删除多余内容
              </p>
            )}
            {aiAnalysis && !analyzing && (
              <div className="mt-2 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
                <div className="flex items-center gap-2 text-sm text-blue-700 dark:text-blue-300">
                  <Sparkles className="h-4 w-4" />
                  <span>
                    AI已分析出 {aiAnalysis.work_items?.length || 0} 个工作项，
                    总工时 {aiAnalysis.total_hours?.toFixed(1) || 0} 小时
                    {aiAnalysis.confidence &&
                      `（置信度：${(aiAnalysis.confidence * 100).toFixed(0)}%）`}
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* AI建议对话框 */}
          <Dialog open={showAiSuggestions} onOpenChange={setShowAiSuggestions}>
            <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle className="flex items-center gap-2">
                  <Sparkles className="h-5 w-5 text-blue-500" />
                  AI工时建议
                </DialogTitle>
              </DialogHeader>

              {aiAnalysis && (
                <div className="space-y-4">
                  <div className="text-sm text-slate-600 dark:text-slate-400">
                    {aiAnalysis.analysis_notes && (
                      <p className="mb-2">{aiAnalysis.analysis_notes}</p>
                    )}
                    <p>
                      总工时：
                      <span className="font-bold">
                        {aiAnalysis.total_hours?.toFixed(1)}
                      </span>{" "}
                      小时
                      {aiAnalysis.confidence && (
                        <span className="ml-2">
                          （置信度：{(aiAnalysis.confidence * 100).toFixed(0)}
                          %）
                        </span>
                      )}
                    </p>
                  </div>

                  <div className="space-y-3">
                    {aiAnalysis.work_items?.map((item, index) => (
                      <div
                        key={index}
                        className={cn(
                          "p-4 border rounded-lg",
                          selectedWorkItems.includes(index)
                            ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20"
                            : "border-slate-200 dark:border-slate-700",
                        )}
                      >
                        <div className="flex items-start gap-3">
                          <input
                            type="checkbox"
                            checked={selectedWorkItems.includes(index)}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setSelectedWorkItems([
                                  ...selectedWorkItems,
                                  index,
                                ]);
                              } else {
                                setSelectedWorkItems(
                                  selectedWorkItems.filter((i) => i !== index),
                                );
                              }
                            }}
                            className="mt-1"
                          />
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                              <span className="font-medium text-sm">
                                {item.work_content}
                              </span>
                              {item.confidence && (
                                <Badge variant="outline" className="text-xs">
                                  {(item.confidence * 100).toFixed(0)}%
                                </Badge>
                              )}
                            </div>
                            <div className="grid grid-cols-3 gap-4 text-sm">
                              <div className="flex items-center gap-2">
                                <Clock className="h-4 w-4 text-slate-500" />
                                <span className="font-medium">
                                  {item.hours?.toFixed(1)} 小时
                                </span>
                              </div>
                              <div className="flex items-center gap-2">
                                <Briefcase className="h-4 w-4 text-slate-500" />
                                <span className="text-slate-600 dark:text-slate-400">
                                  {item.project_name || "未分配项目"}
                                </span>
                              </div>
                              <div>
                                <Badge variant="outline" className="text-xs">
                                  {item.work_type === "NORMAL"
                                    ? "正常"
                                    : item.work_type === "OVERTIME"
                                      ? "加班"
                                      : item.work_type === "WEEKEND"
                                        ? "周末"
                                        : item.work_type === "HOLIDAY"
                                          ? "节假日"
                                          : item.work_type}
                                </Badge>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>

                  {suggestedProjects.length > 0 && (
                    <div className="mt-4 p-3 bg-slate-50 dark:bg-slate-800 rounded-lg">
                      <p className="text-sm font-medium mb-2">
                        您参与的项目（按使用频率排序）：
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {suggestedProjects.slice(0, 5).map((project) => (
                          <Badge
                            key={project.id}
                            variant="outline"
                            className="text-xs"
                          >
                            {project.code} - {project.name}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              <DialogFooter>
                <Button
                  variant="outline"
                  onClick={() => {
                    setShowAiSuggestions(false);
                    setSelectedWorkItems([]);
                  }}
                >
                  取消
                </Button>
                <Button
                  onClick={handleApplyAiSuggestions}
                  disabled={selectedWorkItems.length === 0}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  <CheckCircle2 className="h-4 w-4 mr-2" />
                  应用选中建议 ({selectedWorkItems.length})
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>

          {/* @提及 */}
          <div className="space-y-3">
            <label className="block text-sm font-medium flex items-center gap-2">
              <AtSign className="h-4 w-4" />
              @提及（可选）
            </label>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-xs text-gray-500 mb-1">项目</label>
                <Select
                  value={mentionedProjects[0]?.toString() || "__none__"}
                  onValueChange={(value) => {
                    if (value && value !== "__none__") {
                      setMentionedProjects([parseInt(value)]);
                    } else {
                      setMentionedProjects([]);
                    }
                  }}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="选择项目" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="__none__">无</SelectItem>
                    {mentionOptions.projects.map((project) => (
                      <SelectItem
                        key={project.id}
                        value={project.id.toString()}
                      >
                        {project.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <label className="block text-xs text-gray-500 mb-1">设备</label>
                <Select
                  value={mentionedMachines[0]?.toString() || "__none__"}
                  onValueChange={(value) => {
                    if (value && value !== "__none__") {
                      setMentionedMachines([parseInt(value)]);
                    } else {
                      setMentionedMachines([]);
                    }
                  }}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="选择设备" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="__none__">无</SelectItem>
                    {mentionOptions.machines.map((machine) => (
                      <SelectItem
                        key={machine.id}
                        value={machine.id.toString()}
                      >
                        {machine.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <label className="block text-xs text-gray-500 mb-1">人员</label>
                <Select
                  value={mentionedUsers[0]?.toString() || "__none__"}
                  onValueChange={(value) => {
                    if (value && value !== "__none__") {
                      setMentionedUsers([parseInt(value)]);
                    } else {
                      setMentionedUsers([]);
                    }
                  }}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="选择人员" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="__none__">无</SelectItem>
                    {mentionOptions.users.map((user) => (
                      <SelectItem key={user.id} value={user.id.toString()}>
                        {user.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>

          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={resetForm}>
              重置
            </Button>
            <Button
              onClick={handleSubmit}
              disabled={!content.trim() || wordCount > maxWords}
            >
              <Save className="h-4 w-4 mr-2" />
              {editingId ? "更新" : "提交"}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* 历史日志列表 */}
      <Card>
        <CardHeader>
          <CardTitle>历史日志</CardTitle>
        </CardHeader>
        <CardContent>
          {/* 筛选 */}
          <div className="flex gap-4 mb-4">
            <Input
              type="date"
              placeholder="开始日期"
              value={filterStartDate}
              onChange={(e) => setFilterStartDate(e.target.value)}
              className="w-40"
            />
            <Input
              type="date"
              placeholder="结束日期"
              value={filterEndDate}
              onChange={(e) => setFilterEndDate(e.target.value)}
              className="w-40"
            />
            <Button
              variant="outline"
              onClick={() => {
                setFilterStartDate("");
                setFilterEndDate("");
              }}
            >
              清除筛选
            </Button>
          </div>

          {loading ? (
            <div className="text-center py-8">加载中...</div>
          ) : workLogs.length === 0 ? (
            <div className="text-center py-8 text-gray-500">暂无工作日志</div>
          ) : (
            <div className="space-y-3">
              {workLogs.map((log) => (
                <div
                  key={log.id}
                  className="p-4 border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="font-medium">
                          {log.user_name || "未知用户"}
                        </span>
                        {getStatusBadge(log.status)}
                        <span className="text-sm text-gray-500">
                          {formatDate(log.work_date)}
                        </span>
                      </div>

                      <p className="text-sm text-gray-700 dark:text-gray-300 mb-2">
                        {log.content}
                      </p>

                      {log.mentions && log.mentions.length > 0 && (
                        <div className="flex flex-wrap gap-2 mt-2">
                          {log.mentions.map((mention, idx) => (
                            <Badge
                              key={idx}
                              variant="outline"
                              className="text-xs"
                            >
                              <AtSign className="h-3 w-3 mr-1" />
                              {mention.mention_name}
                            </Badge>
                          ))}
                        </div>
                      )}
                    </div>

                    <div className="flex gap-2">
                      {log.status === "DRAFT" && (
                        <>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleEdit(log)}
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDelete(log.id)}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              ))}

              {/* 分页 */}
              {total > pageSize && (
                <div className="flex justify-center gap-2 mt-4">
                  <Button
                    variant="outline"
                    disabled={page === 1}
                    onClick={() => setPage(page - 1)}
                  >
                    上一页
                  </Button>
                  <span className="flex items-center px-4">
                    第 {page} 页，共 {Math.ceil(total / pageSize)} 页
                  </span>
                  <Button
                    variant="outline"
                    disabled={page >= Math.ceil(total / pageSize)}
                    onClick={() => setPage(page + 1)}
                  >
                    下一页
                  </Button>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
