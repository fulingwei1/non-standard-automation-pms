/**
 * 战略日历视图页面
 * 月历网格布局，显示战略相关事件
 */
import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  ChevronLeft,
  ChevronRight,
  Calendar as CalendarIcon,
  Target,
  Award,
  Briefcase,
  Clock,
  X,
} from "lucide-react";
import { PageHeader } from "@/components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Skeleton,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui";
import { fadeIn, staggerContainer } from "@/lib/animations";
import { reviewApi, strategyApi } from "@/services/api/strategy";

// 事件类型配置
const EVENT_TYPE_CONFIG = {
  strategy_review: {
    label: "战略审视",
    color: "bg-red-500",
    icon: Target,
    borderColor: "border-red-500/50",
  },
  kpi_collection: {
    label: "KPI 采集",
    color: "bg-blue-500",
    icon: Award,
    borderColor: "border-blue-500/50",
  },
  annual_work_review: {
    label: "重点工作回顾",
    color: "bg-emerald-500",
    icon: Briefcase,
    borderColor: "border-emerald-500/50",
  },
};

const WEEKDAYS = ["一", "二", "三", "四", "五", "六", "日"];
const MONTHS = [
  "一月", "二月", "三月", "四月", "五月", "六月",
  "七月", "八月", "九月", "十月", "十一月", "十二月",
];

export default function StrategyCalendar() {
  const [loading, setLoading] = useState(true);
  const [selectedStrategyId, setSelectedStrategyId] = useState(null);
  const [strategies, setStrategies] = useState([]);
  const [currentDate, setCurrentDate] = useState(new Date());
  const [events, setEvents] = useState([]);
  const [selectedDate, setSelectedDate] = useState(null);
  const [selectedDateEvents, setSelectedDateEvents] = useState([]);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);

  // 获取战略列表
  useEffect(() => {
    fetchStrategies();
  }, []);

  // 获取日历事件
  useEffect(() => {
    if (selectedStrategyId != null) {
      fetchEvents();
    } else {
      setLoading(false);
    }
  }, [selectedStrategyId, currentDate]);

  const fetchStrategies = async () => {
    try {
      const { data } = await strategyApi.list();
      const list = data?.items ?? data ?? [];
      const arr = Array.isArray(list) ? list : [];
      setStrategies(arr);
      if (arr.length > 0 && selectedStrategyId == null) {
        setSelectedStrategyId(arr[0].id);
      }
    } catch (error) {
      console.error("获取战略列表失败:", error);
      setStrategies([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchEvents = async () => {
    if (selectedStrategyId == null) return;
    setLoading(true);
    try {
      const year = currentDate.getFullYear();
      const month = currentDate.getMonth() + 1;
      const { data } = await reviewApi.listEvents({
        strategy_id: selectedStrategyId,
        year,
        month,
      });
      const list = data?.items ?? data ?? [];
      setEvents(Array.isArray(list) ? list : []);
    } catch (error) {
      console.error("获取日历事件失败:", error);
      setEvents([]);
    } finally {
      setLoading(false);
    }
  };

  const handlePrevMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, 1));
  };

  const handleNextMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1));
  };

  const handleToday = () => {
    setCurrentDate(new Date());
  };

  const handleDateClick = (date) => {
    const dateStr = formatDate(date);
    const dayEvents = events.filter((e) => formatDate(new Date(e.event_date)) === dateStr);
    setSelectedDate(date);
    setSelectedDateEvents(dayEvents);
    setIsDetailModalOpen(true);
  };

  const formatDate = (date) => {
    const d = new Date(date);
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, "0");
    const day = String(d.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
  };

  const formatDateTime = (dateStr) => {
    if (!dateStr) return "";
    const d = new Date(dateStr);
    return `${d.getMonth() + 1}月${d.getDate()}日 ${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
  };

  // 生成日历网格
  const generateCalendarDays = () => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const startDayOfWeek = firstDay.getDay() || 7; // 周一为 1
    const totalDays = lastDay.getDate();

    const days = [];

    // 上月补白
    const prevMonthLastDay = new Date(year, month, 0).getDate();
    for (let i = startDayOfWeek - 1; i > 0; i--) {
      days.push({
        day: prevMonthLastDay - i + 1,
        isCurrentMonth: false,
        date: new Date(year, month - 1, prevMonthLastDay - i + 1),
      });
    }

    // 当月日期
    for (let i = 1; i <= totalDays; i++) {
      days.push({
        day: i,
        isCurrentMonth: true,
        date: new Date(year, month, i),
        isToday:
          i === new Date().getDate() &&
          month === new Date().getMonth() &&
          year === new Date().getFullYear(),
      });
    }

    // 下月补白
    const remainingDays = 42 - days.length; // 6 行 × 7 列 = 42
    for (let i = 1; i <= remainingDays; i++) {
      days.push({
        day: i,
        isCurrentMonth: false,
        date: new Date(year, month + 1, i),
      });
    }

    return days;
  };

  const getDayEvents = (date) => {
    const dateStr = formatDate(date);
    return events.filter((e) => formatDate(new Date(e.event_date)) === dateStr);
  };

  const calendarDays = generateCalendarDays();

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-12 w-full" />
        <Skeleton className="h-96" />
      </div>
    );
  }

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      {/* 页面头部 */}
      <PageHeader
        title="战略日历"
        description="战略审视、KPI 采集、重点工作回顾日程管理"
        actions={
          <motion.div variants={fadeIn} className="flex gap-2">
            <Select
              value={selectedStrategyId != null ? selectedStrategyId.toString() : "__none__"}
              onValueChange={(val) => val !== "__none__" && setSelectedStrategyId(parseInt(val))}
            >
              <SelectTrigger className="w-[200px] bg-slate-900/50 border-slate-700">
                <SelectValue placeholder="选择战略" />
              </SelectTrigger>
              <SelectContent>
                {strategies.length === 0 ? (
                  <SelectItem value="__none__">暂无战略，请先创建</SelectItem>
                ) : (
                  strategies.map((s) => (
                    <SelectItem key={s.id} value={s.id.toString()}>
                      {s.name} ({s.year})
                    </SelectItem>
                  ))
                )}
              </SelectContent>
            </Select>
            <Button variant="outline" onClick={handleToday}>
              今天
            </Button>
          </motion.div>
        }
      />

      {/* 日历导航 */}
      <motion.div variants={fadeIn}>
        <Card className="bg-slate-800/40 border-slate-700/50">
          <CardContent className="py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <Button variant="outline" size="icon" onClick={handlePrevMonth}>
                  <ChevronLeft className="w-4 h-4" />
                </Button>
                <div className="text-center min-w-[200px]">
                  <h2 className="text-xl font-bold text-white">
                    {currentDate.getFullYear()}年 {MONTHS[currentDate.getMonth()]}
                  </h2>
                </div>
                <Button variant="outline" size="icon" onClick={handleNextMonth}>
                  <ChevronRight className="w-4 h-4" />
                </Button>
              </div>
              <div className="flex items-center gap-4">
                {Object.entries(EVENT_TYPE_CONFIG).map(([key, config]) => {
                  const Icon = config.icon;
                  return (
                    <div key={key} className="flex items-center gap-2 text-sm">
                      <div className={`w-3 h-3 rounded ${config.color}`} />
                      <span className="text-slate-400">{config.label}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* 日历网格 */}
      <motion.div variants={staggerContainer}>
        <Card className="bg-slate-800/40 border-slate-700/50 overflow-hidden">
          <CardContent className="p-0">
            {/* 星期标题 */}
            <div className="grid grid-cols-7 border-b border-slate-700/50">
              {WEEKDAYS.map((day) => (
                <div
                  key={day}
                  className="py-3 text-center text-sm font-medium text-slate-400"
                >
                  周{day}
                </div>
              ))}
            </div>

            {/* 日期网格 */}
            <div className="grid grid-cols-7">
              {calendarDays.map((dayInfo, idx) => {
                const dayEvents = getDayEvents(dayInfo.date);
                const isToday = dayInfo.isToday;

                return (
                  <motion.div
                    key={idx}
                    variants={fadeIn}
                    className={`min-h-[100px] border-b border-r border-slate-700/30 p-2 cursor-pointer transition-colors ${
                      !dayInfo.isCurrentMonth ? "bg-slate-900/30" : ""
                    } ${isToday ? "bg-primary/10" : "hover:bg-slate-700/30"}`}
                    onClick={() => handleDateClick(dayInfo.date)}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span
                        className={`text-sm font-medium ${
                          isToday
                            ? "text-primary font-bold"
                            : dayInfo.isCurrentMonth
                            ? "text-white"
                            : "text-slate-500"
                        }`}
                      >
                        {dayInfo.day}
                      </span>
                      {isToday && (
                        <Badge className="bg-primary/20 text-primary text-xs">
                          今天
                        </Badge>
                      )}
                    </div>

                    {/* 事件标记 */}
                    <div className="space-y-1">
                      {dayEvents.slice(0, 3).map((event, eIdx) => {
                        const eventConfig = EVENT_TYPE_CONFIG[event.event_type];
                        if (!eventConfig) return null;

                        return (
                          <div
                            key={eIdx}
                            className={`text-xs px-1.5 py-0.5 rounded ${eventConfig.color} text-white truncate`}
                          >
                            {event.title || eventConfig.label}
                          </div>
                        );
                      })}
                      {dayEvents.length > 3 && (
                        <div className="text-xs text-slate-400 pl-1">
                          +{dayEvents.length - 3} 更多
                        </div>
                      )}
                    </div>
                  </motion.div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* 事件详情弹窗 */}
      <Dialog open={isDetailModalOpen} onOpenChange={setIsDetailModalOpen}>
        <DialogContent className="bg-slate-900 border-slate-700 max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <CalendarIcon className="w-5 h-5" />
              {selectedDate
                ? `${selectedDate.getMonth() + 1}月${selectedDate.getDate()}日 事件详情`
                : "事件详情"}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-3 py-4">
            {selectedDateEvents.length > 0 ? (
              selectedDateEvents.map((event) => {
                const eventConfig = EVENT_TYPE_CONFIG[event.event_type];
                const Icon = eventConfig?.icon || CalendarIcon;

                return (
                  <div
                    key={event.id}
                    className={`p-4 rounded-lg border ${eventConfig?.borderColor || "border-slate-700"} bg-slate-800/50`}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <div className={`p-2 rounded ${eventConfig?.color || "bg-slate-500"}`}>
                          <Icon className="w-4 h-4 text-white" />
                        </div>
                        <div>
                          <p className="font-medium text-white">
                            {event.title || eventConfig?.label || "事件"}
                          </p>
                          <p className="text-xs text-slate-400">
                            {eventConfig?.label}
                          </p>
                        </div>
                      </div>
                      <Badge
                        variant="outline"
                        className={
                          event.status === "COMPLETED"
                            ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/30"
                            : event.status === "UPCOMING"
                            ? "bg-blue-500/20 text-blue-400 border-blue-500/30"
                            : "bg-slate-500/20 text-slate-400 border-slate-500/30"
                        }
                      >
                        {event.status === "COMPLETED"
                          ? "已完成"
                          : event.status === "UPCOMING"
                          ? "即将进行"
                          : "计划中"}
                      </Badge>
                    </div>
                    {event.description && (
                      <p className="text-sm text-slate-400 mt-2">{event.description}</p>
                    )}
                    <div className="flex items-center gap-4 mt-3 text-xs text-slate-400">
                      {event.event_date && (
                        <div className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          <span>{formatDateTime(event.event_date)}</span>
                        </div>
                      )}
                      {event.location && (
                        <div className="flex items-center gap-1">
                          <CalendarIcon className="w-3 h-3" />
                          <span>{event.location}</span>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="text-center py-8 text-slate-500">
                <CalendarIcon className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>当天暂无事件</p>
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsDetailModalOpen(false)}>
              关闭
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </motion.div>
  );
}
