import { useState, useEffect, useMemo } from "react";
import { Calendar, ChevronLeft, ChevronRight } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { Badge } from "../../components/ui/badge";
import { cn } from "../../lib/utils";
import { productionApi } from "../../services/api";
import { getItemsCompat } from "../../utils/apiResponse";

const formatDateKey = (date) => {
  const value = date instanceof Date ? date : new Date(date);
  if (Number.isNaN(value.getTime())) {
    return "";
  }
  return `${value.getFullYear()}-${String(value.getMonth() + 1).padStart(2, "0")}-${String(value.getDate()).padStart(2, "0")}`;
};

const buildCalendarBuckets = ({ plans, workOrders, startDate, endDate }) => {
  const startKey = formatDateKey(startDate);
  const endKey = formatDateKey(endDate);
  const bucketMap = new Map();

  const ensureBucket = (dateKey) => {
    if (!bucketMap.has(dateKey)) {
      bucketMap.set(dateKey, { date: dateKey, plans: [], work_orders: [] });
    }
    return bucketMap.get(dateKey);
  };

  const addRange = (start, end, kind, payload) => {
    const rangeStart = new Date(start || end);
    const rangeEnd = new Date(end || start);
    if (Number.isNaN(rangeStart.getTime()) || Number.isNaN(rangeEnd.getTime())) {
      return;
    }

    const cursor = new Date(rangeStart);
    while (cursor <= rangeEnd) {
      const dateKey = formatDateKey(cursor);
      if (dateKey >= startKey && dateKey <= endKey) {
        ensureBucket(dateKey)[kind].push(payload);
      }
      cursor.setDate(cursor.getDate() + 1);
    }
  };

  plans.forEach((plan) => {
    addRange(
      plan.plan_start_date || plan.start_date,
      plan.plan_end_date || plan.end_date,
      "plans",
      {
        ...plan,
        plan_id: plan.plan_id || plan.id,
        plan_name: plan.plan_name || plan.name,
      },
    );
  });

  workOrders.forEach((order) => {
    addRange(
      order.plan_start_date || order.planned_start_date,
      order.plan_end_date || order.planned_end_date,
      "work_orders",
      {
        ...order,
        work_order_id: order.work_order_id || order.id,
        order_no: order.work_order_no || order.order_no,
      },
    );
  });

  return Array.from(bucketMap.values()).sort((a, b) => a.date.localeCompare(b.date));
};

export default function ScheduleCalendarView({ projects: _projects, onProjectClick }) {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [calendarData, setCalendarData] = useState([]);
  const [loading, setLoading] = useState(true);

  const year = currentDate.getFullYear();
  const month = currentDate.getMonth();

  useEffect(() => {
    const fetchCalendarData = async () => {
      try {
        setLoading(true);
        const startDate = new Date(year, month, 1);
        const endDate = new Date(year, month + 1, 0);

        const [planResult, orderResult] = await Promise.allSettled([
          productionApi.productionPlans.list({ page_size: 1000 }),
          productionApi.workOrders.list({ page_size: 1000 }),
        ]);

        const plans = planResult.status === "fulfilled" ? getItemsCompat(planResult.value) : [];
        const workOrders = orderResult.status === "fulfilled" ? getItemsCompat(orderResult.value) : [];

        setCalendarData(
          buildCalendarBuckets({
            plans,
            workOrders,
            startDate,
            endDate,
          }),
        );
      } catch (err) {
        console.error("Failed to fetch calendar data:", err);
        setCalendarData([]);
      } finally {
        setLoading(false);
      }
    };

    fetchCalendarData();
  }, [year, month]);

  const getDaysInMonth = (targetYear, targetMonth) => {
    return new Date(targetYear, targetMonth + 1, 0).getDate();
  };

  const getFirstDayOfMonth = (targetYear, targetMonth) => {
    return new Date(targetYear, targetMonth, 1).getDay();
  };

  const isSameDay = (date1, date2) => {
    if (!date1 || !date2) {return false;}
    return (
      date1.getFullYear() === date2.getFullYear() &&
      date1.getMonth() === date2.getMonth() &&
      date1.getDate() === date2.getDate()
    );
  };

  const calendarDays = useMemo(() => {
    const daysInMonth = getDaysInMonth(year, month);
    const firstDay = getFirstDayOfMonth(year, month);
    const days = [];

    const prevMonthDays = getDaysInMonth(year, month - 1);
    for (let i = firstDay - 1; i >= 0; i--) {
      days.push({
        date: new Date(year, month - 1, prevMonthDays - i),
        isCurrentMonth: false,
      });
    }

    for (let i = 1; i <= daysInMonth; i++) {
      days.push({
        date: new Date(year, month, i),
        isCurrentMonth: true,
      });
    }

    const remainingDays = 42 - days.length;
    for (let i = 1; i <= remainingDays; i++) {
      days.push({
        date: new Date(year, month + 1, i),
        isCurrentMonth: false,
      });
    }

    return days;
  }, [year, month]);

  const getEventsForDate = (date) => {
    const dateKey = formatDateKey(date);
    const dayData = (calendarData || []).find((item) => item.date === dateKey);
    if (!dayData) {return [];}

    return [
      ...(dayData.plans || []).map((plan) => ({ ...plan, type: "plan" })),
      ...(dayData.work_orders || []).map((workOrder) => ({ ...workOrder, type: "work_order" })),
    ];
  };

  const goToPrevious = () => {
    setCurrentDate(new Date(year, month - 1, 1));
  };

  const goToNext = () => {
    setCurrentDate(new Date(year, month + 1, 1));
  };

  const goToToday = () => {
    setCurrentDate(new Date());
  };

  const today = new Date();

  return (
    <Card className="bg-surface-1/50">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Calendar className="w-5 h-5" />
            排产日历
          </CardTitle>
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={goToPrevious}>
              <ChevronLeft className="w-4 h-4" />
            </Button>
            <span className="text-lg font-medium text-white min-w-[150px] text-center">
              {year}年{month + 1}月
            </span>
            <Button variant="ghost" size="sm" onClick={goToNext}>
              <ChevronRight className="w-4 h-4" />
            </Button>
            <Button variant="outline" size="sm" onClick={goToToday}>
              今天
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="flex items-center justify-center h-96">
            <div className="text-slate-400">加载中...</div>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-7 bg-surface-2/30 border-b border-border">
              {["日", "一", "二", "三", "四", "五", "六"].map((day) => (
                <div
                  key={day}
                  className="text-center py-2 text-sm font-medium text-slate-400"
                >
                  {day}
                </div>
              ))}
            </div>

            <div className="grid grid-cols-7">
              {(calendarDays || []).map((day) => {
                const events = getEventsForDate(day.date);
                const isToday = isSameDay(day.date, today);
                const isWeekend = day.date.getDay() === 0 || day.date.getDay() === 6;

                return (
                  <div
                    key={formatDateKey(day.date)}
                    className={cn(
                      "min-h-[120px] border border-border/30 p-2 transition-colors",
                      !day.isCurrentMonth && "bg-surface-2/30",
                      isToday && "bg-primary/10 border-primary/30",
                      isWeekend && day.isCurrentMonth && "bg-slate-800/30",
                    )}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span
                        className={cn(
                          "text-sm font-medium px-1.5 py-0.5 rounded",
                          isToday && "bg-primary text-white",
                          !day.isCurrentMonth && "text-slate-600",
                          day.isCurrentMonth && !isToday && "text-slate-300",
                        )}
                      >
                        {day.date.getDate()}
                      </span>
                      {events?.length > 0 && (
                        <Badge variant="outline" className="text-[10px]">
                          {events?.length}
                        </Badge>
                      )}
                    </div>

                    <div className="space-y-1">
                      {events.slice(0, 3).map((event, idx) => (
                        <div
                          key={idx}
                          onClick={() => onProjectClick && onProjectClick(event)}
                          className={cn(
                            "px-1.5 py-0.5 rounded text-xs truncate cursor-pointer transition-all",
                            event.type === "plan"
                              ? "bg-blue-500/20 text-blue-400 border-l-2 border-l-blue-400"
                              : "bg-purple-500/20 text-purple-400 border-l-2 border-l-purple-400",
                          )}
                          title={event.plan_name || event.task_name || event.order_no}
                        >
                          {event.plan_name || event.task_name || event.order_no}
                        </div>
                      ))}
                      {events?.length > 3 && (
                        <div className="text-[10px] text-slate-500 text-center">
                          +{events?.length - 3} 更多
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
