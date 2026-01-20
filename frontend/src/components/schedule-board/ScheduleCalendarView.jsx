import { useState, useEffect, useMemo } from "react";
import { Calendar, ChevronLeft, ChevronRight } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { Badge } from "../../components/ui/badge";
import { cn } from "../../lib/utils";
import { productionApi } from "../../services/api";

export default function ScheduleCalendarView({ projects: _projects, onProjectClick }) {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [calendarData, setCalendarData] = useState([]);
  const [loading, setLoading] = useState(true);

  const year = currentDate.getFullYear();
  const month = currentDate.getMonth();

  // Fetch calendar data
  useEffect(() => {
    const fetchCalendarData = async () => {
      try {
        setLoading(true);
        const startDate = new Date(year, month, 1);
        const endDate = new Date(year, month + 1, 0);

        const response = await productionApi.productionPlans.calendar({
          start_date: startDate.toISOString().split("T")[0],
          end_date: endDate.toISOString().split("T")[0]
        });

        const data = response.data || response;
        setCalendarData(data.calendar || []);
      } catch (err) {
        console.error("Failed to fetch calendar data:", err);
        setCalendarData([]);
      } finally {
        setLoading(false);
      }
    };
    fetchCalendarData();
  }, [year, month]);

  // Get days in month
  const getDaysInMonth = (year, month) => {
    return new Date(year, month + 1, 0).getDate();
  };

  const getFirstDayOfMonth = (year, month) => {
    return new Date(year, month, 1).getDay();
  };

  const formatDateKey = (date) => {
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
  };

  const isSameDay = (date1, date2) => {
    if (!date1 || !date2) {return false;}
    return (
      date1.getFullYear() === date2.getFullYear() &&
      date1.getMonth() === date2.getMonth() &&
      date1.getDate() === date2.getDate()
    );
  };

  // Generate calendar days
  const calendarDays = useMemo(() => {
    const daysInMonth = getDaysInMonth(year, month);
    const firstDay = getFirstDayOfMonth(year, month);
    const days = [];

    // Previous month days
    const prevMonthDays = getDaysInMonth(year, month - 1);
    for (let i = firstDay - 1; i >= 0; i--) {
      days.push({
        date: new Date(year, month - 1, prevMonthDays - i),
        isCurrentMonth: false
      });
    }

    // Current month days
    for (let i = 1; i <= daysInMonth; i++) {
      days.push({
        date: new Date(year, month, i),
        isCurrentMonth: true
      });
    }

    // Next month days
    const remainingDays = 42 - days.length;
    for (let i = 1; i <= remainingDays; i++) {
      days.push({
        date: new Date(year, month + 1, i),
        isCurrentMonth: false
      });
    }

    return days;
  }, [year, month]);

  // Get events for a date
  const getEventsForDate = (date) => {
    const dateKey = formatDateKey(date);
    const dayData = calendarData.find((d) => d.date === dateKey);
    if (!dayData) {return [];}

    return [
      ...(dayData.plans || []).map((p) => ({ ...p, type: "plan" })),
      ...(dayData.work_orders || []).map((w) => ({ ...w, type: "work_order" }))
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
            {/* Days of Week Header */}
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

            {/* Calendar Grid */}
            <div className="grid grid-cols-7">
              {calendarDays.map((day) => {
                const events = getEventsForDate(day.date);
                const isToday = isSameDay(day.date, today);
                const isWeekend =
                  day.date.getDay() === 0 || day.date.getDay() === 6;

                return (
                  <div
                    key={formatDateKey(day.date)}
                    className={cn(
                      "min-h-[120px] border border-border/30 p-2 transition-colors",
                      !day.isCurrentMonth && "bg-surface-2/30",
                      isToday && "bg-primary/10 border-primary/30",
                      isWeekend && day.isCurrentMonth && "bg-slate-800/30"
                    )}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span
                        className={cn(
                          "text-sm font-medium px-1.5 py-0.5 rounded",
                          isToday && "bg-primary text-white",
                          !day.isCurrentMonth && "text-slate-600",
                          day.isCurrentMonth && !isToday && "text-slate-300"
                        )}
                      >
                        {day.date.getDate()}
                      </span>
                      {events.length > 0 && (
                        <Badge variant="outline" className="text-[10px]">
                          {events.length}
                        </Badge>
                      )}
                    </div>

                    <div className="space-y-1">
                      {events.slice(0, 3).map((event, idx) => (
                        <div
                          key={idx}
                          onClick={() =>
                            onProjectClick && onProjectClick(event)
                          }
                          className={cn(
                            "px-1.5 py-0.5 rounded text-xs truncate cursor-pointer transition-all",
                            event.type === "plan"
                              ? "bg-blue-500/20 text-blue-400 border-l-2 border-l-blue-400"
                              : "bg-purple-500/20 text-purple-400 border-l-2 border-l-purple-400"
                          )}
                          title={
                            event.plan_name || event.task_name || event.order_no
                          }
                        >
                          {event.plan_name || event.task_name || event.order_no}
                        </div>
                      ))}
                      {events.length > 3 && (
                        <div className="text-[10px] text-slate-500 text-center">
                          +{events.length - 3} 更多
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
