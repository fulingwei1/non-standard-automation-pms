/**
 * TeamAssignment Component
 * 团队分配管理组件
 */

import { useState, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Badge,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogBody,
  DialogFooter,
  Input,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue } from
"../../components/ui";
import {
  Plus,
  Search,
  User,
  MapPin,
  Phone,
  Mail,
  UserCheck,
  UserX,
  Briefcase,
  Award,
  Star,
  ChevronDown } from
"lucide-react";
import { cn } from "../../lib/utils";
import {
  formatDate,
  formatDuration,
  hasPermission } from
"@/lib/constants/installationDispatch";import { toast } from "sonner";

export function TeamAssignment({
  engineers,
  tasks,
  onAssignTask,
  onUnassignTask: _onUnassignTask,
  onUpdateEngineer: _onUpdateEngineer,
  currentUser,
  showFilters = true,
  compact = false,
  className = ""
}) {
  const [showAssignDialog, setShowAssignDialog] = useState(false);
  const [showEngineerDetail, setShowEngineerDetail] = useState(null);
  const [selectedTask, setSelectedTask] = useState(null);
  const [selectedEngineer, setSelectedEngineer] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [skillFilter, setSkillFilter] = useState("ALL");
  const [locationFilter, setLocationFilter] = useState("ALL");

  // Filter and sort engineers
  const filteredEngineers = useMemo(() => {
    return engineers.
    filter((engineer) => {
      // Search filter
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        const fullName = `${engineer.first_name} ${engineer.last_name}`.toLowerCase();
        const skills = engineer.skills?.join(" ").toLowerCase() || "";
        const location = engineer.location?.toLowerCase() || "";

        if (!fullName.includes(query) && !skills.includes(query) && !location.includes(query)) {
          return false;
        }
      }

      // Status filter
      if (statusFilter !== "ALL") {
        if (statusFilter === "AVAILABLE" && engineer.current_task_count > 0) {
          return false;
        }
        if (statusFilter === "BUSY" && engineer.current_task_count === 0) {
          return false;
        }
      }

      // Skill filter
      if (skillFilter !== "ALL" && engineer.skills) {
        if (!engineer.skills.includes(skillFilter)) {
          return false;
        }
      }

      // Location filter
      if (locationFilter !== "ALL" && engineer.location) {
        if (!engineer.location.includes(locationFilter)) {
          return false;
        }
      }

      return true;
    }).
    sort((a, b) => {
      // Sort by availability first, then by skill level
      if (a.current_task_count === 0 && b.current_task_count > 0) {return -1;}
      if (a.current_task_count > 0 && b.current_task_count === 0) {return 1;}
      return (b.skill_level || 0) - (a.skill_level || 0);
    });
  }, [engineers, searchQuery, statusFilter, skillFilter, locationFilter]);

  // Filter tasks for assignment
  const availableTasks = useMemo(() => {
    return (tasks || []).filter((task) =>
    task.status === "SCHEDULED" && !task.assigned_engineer_id
    );
  }, [tasks]);

  // Get engineer's current tasks
  const getEngineerTasks = (engineerId) => {
    return (tasks || []).filter((task) => task.assigned_engineer_id === engineerId);
  };

  // Calculate engineer workload
  const calculateWorkload = (engineer) => {
    const tasks = getEngineerTasks(engineer.id);
    const totalHours = (tasks || []).reduce((sum, task) => sum + (task.estimated_duration || 0), 0);
    const urgentTasks = (tasks || []).filter((task) => task.priority === "URGENT").length;
    const overdueTasks = (tasks || []).filter((task) => isTaskOverdue(task.status, task.planned_end_date)).length;

    return {
      totalHours,
      urgentTasks,
      overdueTasks,
      taskCount: tasks?.length
    };
  };

  // Check if task is overdue
  function isTaskOverdue(status, plannedEndDate) {
    const plannedEnd = new Date(plannedEndDate);
    const now = new Date();
    return plannedEnd < now && status !== "COMPLETED" && status !== "CANCELLED";
  }

  // Get engineer status
  const getEngineerStatus = (engineer) => {
    const workload = calculateWorkload(engineer);

    if (engineer.is_off_duty) {
      return {
        label: "休假中",
        color: "text-slate-400",
        bg: "bg-slate-500/20",
        borderColor: "border-slate-500/30",
        icon: "🏖️"
      };
    }

    if (workload.urgentTasks > 0) {
      return {
        label: "超负荷",
        color: "text-red-400",
        bg: "bg-red-500/20",
        borderColor: "border-red-500/30",
        icon: "🚨"
      };
    }

    if (workload.overdueTasks > 0) {
      return {
        label: "有逾期",
        color: "text-orange-400",
        bg: "bg-orange-500/20",
        borderColor: "border-orange-500/30",
        icon: "⚠️"
      };
    }

    if (engineer.current_task_count === 0) {
      return {
        label: "空闲",
        color: "text-green-400",
        bg: "bg-green-500/20",
        borderColor: "border-green-500/30",
        icon: "✅"
      };
    }

    return {
      label: "忙碌",
      color: "text-yellow-400",
      bg: "bg-yellow-500/20",
      borderColor: "border-yellow-500/30",
      icon: "🔧"
    };
  };

  // Handle task assignment
  const handleTaskAssignment = () => {
    if (!selectedTask || !selectedEngineer) {
      toast.warning("请选择任务和工程师");
      return;
    }

    onAssignTask({
      task_id: selectedTask.id,
      engineer_id: selectedEngineer.id,
      scheduled_date: selectedTask.scheduled_date,
      notes: ""
    });

    setSelectedTask(null);
    setSelectedEngineer(null);
    setShowAssignDialog(false);
  };

  // Get unique skills for filter
  const uniqueSkills = useMemo(() => {
    const skillsSet = new Set();
    (engineers || []).forEach((engineer) => {
      engineer.skills?.forEach((skill) => skillsSet.add(skill));
    });
    return Array.from(skillsSet).sort();
  }, [engineers]);

  // Get unique locations for filter
  const uniqueLocations = useMemo(() => {
    const locationsSet = new Set();
    (engineers || []).forEach((engineer) => {
      if (engineer.location) {locationsSet.add(engineer.location);}
    });
    return Array.from(locationsSet).sort();
  }, [engineers]);

  if (compact) {
    return (
      <div className={cn("space-y-3", className)}>
        {filteredEngineers.slice(0, 5).map((engineer) => {
          const status = getEngineerStatus(engineer);
          const workload = calculateWorkload(engineer);

          return (
            <motion.div
              key={engineer.id}
              whileHover={{ scale: 1.02 }}
              className="p-3 rounded-lg bg-slate-800/50 border border-slate-700 cursor-pointer"
              onClick={() => setShowEngineerDetail(engineer)}>

              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-slate-700 flex items-center justify-center flex-shrink-0">
                  <User className="w-5 h-5" />
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <h4 className="text-sm font-medium text-white truncate">
                      {engineer.first_name} {engineer.last_name}
                    </h4>
                    <Badge className={cn(
                      status.bg,
                      status.borderColor,
                      "text-xs"
                    )}>
                      {status.label}
                    </Badge>
                  </div>

                  <div className="flex items-center gap-3 mt-1 text-xs text-slate-400">
                    <span>{workload.taskCount} 个任务</span>
                    <span>{workload.totalHours} 小时</span>
                    {engineer.location &&
                    <div className="flex items-center gap-1">
                        <MapPin className="w-3 h-3" />
                        <span className="truncate">{engineer.location}</span>
                    </div>
                    }
                  </div>
                </div>

                <div className="text-right">
                  <div className="flex items-center gap-1 text-xs text-slate-400">
                    <Star className="w-3 h-3" />
                    <span>{engineer.skill_level || 3}</span>
                  </div>
                </div>
              </div>
            </motion.div>);

        })}

        {filteredEngineers.length > 5 &&
        <div className="text-center py-2">
            <Button variant="outline" size="sm" onClick={() => setShowAssignDialog(true)}>
              查看全部 {filteredEngineers.length} 位工程师
            </Button>
        </div>
        }
      </div>);

  }

  return (
    <>
      {/* Filters */}
      {showFilters &&
      <div className="p-4 bg-slate-800/50 rounded-lg mb-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
              <Input
              placeholder="搜索工程师、技能或地点..."
              value={searchQuery || "unknown"}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10" />

            </div>

            <Select value={statusFilter || "unknown"} onValueChange={setStatusFilter}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="ALL">所有状态</SelectItem>
                <SelectItem value="AVAILABLE">空闲工程师</SelectItem>
                <SelectItem value="BUSY">忙碌工程师</SelectItem>
              </SelectContent>
            </Select>

            <Select value={skillFilter || "unknown"} onValueChange={setSkillFilter}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="ALL">所有技能</SelectItem>
                {(uniqueSkills || []).map((skill) =>
              <SelectItem key={skill} value={skill || "unknown"}>
                    {skill}
              </SelectItem>
              )}
              </SelectContent>
            </Select>

            <Select value={locationFilter || "unknown"} onValueChange={setLocationFilter}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="ALL">所有地点</SelectItem>
                {(uniqueLocations || []).map((location) =>
              <SelectItem key={location} value={location || "unknown"}>
                    {location}
              </SelectItem>
              )}
              </SelectContent>
            </Select>
          </div>
      </div>
      }

      {/* Engineers Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <AnimatePresence>
          {(filteredEngineers || []).map((engineer) => {
            const status = getEngineerStatus(engineer);
            const workload = calculateWorkload(engineer);
            const tasks = getEngineerTasks(engineer.id);

            return (
              <motion.div
                key={engineer.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="bg-slate-800/50 rounded-lg border border-slate-700 hover:bg-slate-800/70 transition-colors">

                <CardHeader className="p-4 pb-2">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3 flex-1">
                      <div className="w-12 h-12 rounded-full bg-slate-700 flex items-center justify-center flex-shrink-0">
                        <User className="w-6 h-6" />
                      </div>

                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <h3 className="font-medium text-white truncate">
                            {engineer.first_name} {engineer.last_name}
                          </h3>
                          <Badge className={cn(
                            status.bg,
                            status.borderColor,
                            "text-xs"
                          )}>
                            {status.icon} {status.label}
                          </Badge>
                        </div>

                        <div className="flex items-center gap-3 mt-1 text-xs text-slate-400">
                          <div className="flex items-center gap-1">
                            <Briefcase className="w-3 h-3" />
                            <span>技能等级: {engineer.skill_level || 3}</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <Award className="w-3 h-3" />
                            <span>{engineer.experience_years || 0}年经验</span>
                          </div>
                        </div>
                      </div>
                    </div>

                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setShowEngineerDetail(engineer)}>

                      <ChevronDown className="w-4 h-4" />
                    </Button>
                  </div>
                </CardHeader>

                <CardContent className="p-4 pt-0 space-y-3">
                  {/* Contact Info */}
                  <div className="space-y-1 text-xs">
                    {engineer.phone &&
                    <div className="flex items-center gap-2 text-slate-400">
                        <Phone className="w-3 h-3" />
                        <span>{engineer.phone}</span>
                    </div>
                    }
                    {engineer.email &&
                    <div className="flex items-center gap-2 text-slate-400">
                        <Mail className="w-3 h-3" />
                        <span>{engineer.email}</span>
                    </div>
                    }
                  </div>

                  {/* Location */}
                  {engineer.location &&
                  <div className="flex items-center gap-2 text-xs text-slate-400">
                      <MapPin className="w-3 h-3" />
                      <span>{engineer.location}</span>
                  </div>
                  }

                  {/* Workload */}
                  <div className="grid grid-cols-3 gap-2 text-center text-xs">
                    <div className="bg-slate-700/50 rounded p-2">
                      <div className="text-white font-medium">{workload.taskCount}</div>
                      <div className="text-slate-400">任务数</div>
                    </div>
                    <div className="bg-slate-700/50 rounded p-2">
                      <div className="text-white font-medium">{workload.totalHours}h</div>
                      <div className="text-slate-400">总时长</div>
                    </div>
                    <div className="bg-slate-700/50 rounded p-2">
                      <div className="text-white font-medium">{engineer.rating || 4.5}</div>
                      <div className="text-slate-400">评分</div>
                    </div>
                  </div>

                  {/* Skills */}
                  {engineer.skills && engineer.skills?.length > 0 &&
                  <div>
                      <div className="text-xs text-slate-400 mb-1">技能专长</div>
                      <div className="flex flex-wrap gap-1">
                        {engineer.skills.slice(0, 3).map((skill, index) =>
                      <Badge
                        key={index}
                        variant="outline"
                        className="text-xs">

                            {skill}
                      </Badge>
                      )}
                        {engineer.skills?.length > 3 &&
                      <Badge variant="outline" className="text-xs">
                            +{engineer.skills?.length - 3}
                      </Badge>
                      }
                      </div>
                  </div>
                  }

                  {/* Current Tasks Preview */}
                  {tasks?.length > 0 &&
                  <div>
                      <div className="text-xs text-slate-400 mb-2 flex items-center justify-between">
                        <span>当前任务</span>
                        <span className="text-slate-500">{tasks?.length} 个</span>
                      </div>
                      <div className="space-y-1 max-h-20 overflow-y-auto">
                        {tasks.slice(0, 2).map((task) =>
                      <div key={task.id} className="text-xs bg-slate-700/30 rounded p-1">
                            <div className="text-white truncate">{task.title}</div>
                            <div className="text-slate-400 text-[10px]">
                              {formatDate(task.scheduled_date)} · {formatDuration(task.estimated_duration)}
                            </div>
                      </div>
                      )}
                        {tasks?.length > 2 &&
                      <div className="text-xs text-slate-500 text-center">
                            还有 {tasks?.length - 2} 个任务...
                      </div>
                      }
                      </div>
                  </div>
                  }

                  {/* Action Buttons */}
                  <div className="flex items-center gap-2 pt-2 border-t border-slate-700">
                    {hasPermission(currentUser, "installation:assign") &&
                    <Button
                      size="sm"
                      onClick={() => setShowAssignDialog(true)}
                      disabled={availableTasks.length === 0}
                      className="flex-1">

                        <Plus className="w-3 h-3 mr-1" />
                        分配任务
                    </Button>
                    }

                    {engineer.is_off_duty &&
                    <Button
                      variant="outline"
                      size="sm"
                      className="flex-1"
                      disabled>

                        <UserX className="w-3 h-3 mr-1" />
                        休假中
                    </Button>
                    }
                  </div>
                </CardContent>
              </motion.div>);

          })}
        </AnimatePresence>
      </div>

      {/* No Results */}
      {filteredEngineers.length === 0 &&
      <div className="text-center py-12 text-slate-500">
          <User className="w-12 h-12 mx-auto mb-3 text-slate-600" />
          <p>没有找到符合条件的工程师</p>
          <p className="text-sm mt-1">请尝试调整搜索条件</p>
      </div>
      }

      {/* Assign Task Dialog */}
      <Dialog open={showAssignDialog} onOpenChange={setShowAssignDialog}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle>分配任务给工程师</DialogTitle>
          </DialogHeader>
          <DialogBody className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium mb-2 block">选择任务</label>
                <Select value={selectedTask?.id || ""} onValueChange={(value) => {
                  const task = (availableTasks || []).find((t) => t.id === value);
                  setSelectedTask(task);
                }}>
                  <SelectTrigger>
                    <SelectValue placeholder="选择要分配的任务" />
                  </SelectTrigger>
                  <SelectContent>
                    {(availableTasks || []).map((task) =>
                    <SelectItem key={task.id} value={task.id}>
                        {task.title} · {task.scheduled_date} · {task.location}
                    </SelectItem>
                    )}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">选择工程师</label>
                <Select value={selectedEngineer?.id || ""} onValueChange={(value) => {
                  const engineer = (filteredEngineers || []).find((e) => e.id === value);
                  setSelectedEngineer(engineer);
                }}>
                  <SelectTrigger>
                    <SelectValue placeholder="选择工程师" />
                  </SelectTrigger>
                  <SelectContent>
                    {(filteredEngineers || []).map((engineer) =>
                    <SelectItem key={engineer.id} value={engineer.id}>
                        {engineer.first_name} {engineer.last_name} · {engineer.location} · 可用
                    </SelectItem>
                    )}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {selectedTask && selectedEngineer &&
            <Card>
                <CardHeader className="p-3 pb-1">
                  <CardTitle className="text-sm">任务详情</CardTitle>
                </CardHeader>
                <CardContent className="p-3 pt-0 space-y-2 text-xs">
                  <div>
                    <span className="text-slate-400">任务名称:</span>
                    <span className="text-white ml-2">{selectedTask.title}</span>
                  </div>
                  <div>
                    <span className="text-slate-400">安排时间:</span>
                    <span className="text-white ml-2">{formatDate(selectedTask.scheduled_date)}</span>
                  </div>
                  <div>
                    <span className="text-slate-400">预计时长:</span>
                    <span className="text-white ml-2">{formatDuration(selectedTask.estimated_duration)}</span>
                  </div>
                  <div>
                    <span className="text-slate-400">安装地点:</span>
                    <span className="text-white ml-2">{selectedTask.location || "未指定"}</span>
                  </div>
                </CardContent>
            </Card>
            }
          </DialogBody>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowAssignDialog(false)}>
              取消
            </Button>
            <Button onClick={handleTaskAssignment} disabled={!selectedTask || !selectedEngineer}>
              <UserCheck className="w-4 h-4 mr-1" />
              确认分配
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Engineer Detail Dialog */}
      {showEngineerDetail &&
      <Dialog open={!!showEngineerDetail} onOpenChange={() => setShowEngineerDetail(null)}>
          <DialogContent className="max-w-3xl">
            <DialogHeader>
              <DialogTitle>
                {showEngineerDetail.first_name} {showEngineerDetail.last_name} 的详细信息
              </DialogTitle>
            </DialogHeader>
            <DialogBody className="space-y-4">
              {/* Basic Info */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-slate-400">员工编号</label>
                  <p className="text-sm text-white">{showEngineerDetail.employee_id}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-slate-400">职位</label>
                  <p className="text-sm text-white">{showEngineerDetail.position}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-slate-400">技能等级</label>
                  <p className="text-sm text-white">等级 {showEngineerDetail.skill_level || 3}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-slate-400">工作经验</label>
                  <p className="text-sm text-white">{showEngineerDetail.experience_years || 0} 年</p>
                </div>
              </div>

              {/* Contact Info */}
              <div>
                <label className="text-sm font-medium text-slate-400">联系方式</label>
                <div className="mt-2 space-y-1 text-sm">
                  {showEngineerDetail.phone &&
                <div className="flex items-center gap-2">
                      <Phone className="w-4 h-4 text-slate-400" />
                      <span>{showEngineerDetail.phone}</span>
                </div>
                }
                  {showEngineerDetail.email &&
                <div className="flex items-center gap-2">
                      <Mail className="w-4 h-4 text-slate-400" />
                      <span>{showEngineerDetail.email}</span>
                </div>
                }
                </div>
              </div>

              {/* Location */}
              {showEngineerDetail.location &&
            <div>
                  <label className="text-sm font-medium text-slate-400">工作地点</label>
                  <div className="mt-2 text-sm text-white flex items-center gap-2">
                    <MapPin className="w-4 h-4 text-slate-400" />
                    <span>{showEngineerDetail.location}</span>
                  </div>
            </div>
            }

              {/* Skills */}
              {showEngineerDetail.skills && showEngineerDetail.skills?.length > 0 &&
            <div>
                  <label className="text-sm font-medium text-slate-400">技能专长</label>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {(showEngineerDetail.skills || []).map((skill, index) =>
                <Badge key={index} className="text-xs">
                        {skill}
                </Badge>
                )}
                  </div>
            </div>
            }

              {/* Performance */}
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="text-sm font-medium text-slate-400">完成率</label>
                  <p className="text-2xl font-bold text-white mt-1">
                    {showEngineerDetail.completion_rate || 95}%
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-slate-400">客户评分</label>
                  <p className="text-2xl font-bold text-white mt-1">
                    {showEngineerDetail.rating || 4.5}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-slate-400">准时率</label>
                  <p className="text-2xl font-bold text-white mt-1">
                    {showEngineerDetail.on_time_rate || 92}%
                  </p>
                </div>
              </div>

              {/* Current Tasks */}
              <div>
                <label className="text-sm font-medium text-slate-400">
                  当前任务 ({getEngineerTasks(showEngineerDetail.id).length})
                </label>
                <div className="mt-2 space-y-2">
                  {getEngineerTasks(showEngineerDetail.id).map((task) =>
                <div key={task.id} className="bg-slate-700/30 rounded p-3">
                      <div className="flex items-center justify-between">
                        <h4 className="text-sm font-medium text-white">{task.title}</h4>
                        <Badge className="text-xs">
                          {formatDate(task.scheduled_date)}
                        </Badge>
                      </div>
                      <div className="mt-1 text-xs text-slate-400">
                        {task.location} · 预计 {formatDuration(task.estimated_duration)}
                      </div>
                </div>
                )}
                </div>
              </div>
            </DialogBody>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowEngineerDetail(null)}>
                关闭
              </Button>
            </DialogFooter>
          </DialogContent>
      </Dialog>
      }
    </>);

}