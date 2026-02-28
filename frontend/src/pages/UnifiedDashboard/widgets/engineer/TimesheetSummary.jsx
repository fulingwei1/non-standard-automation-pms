/**
 * 工时汇总组件 (Timesheet Summary)
 * 从后端 API 加载当前用户本周工时数据
 */
import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../../../components/ui/card';
import { timesheetApi } from '../../../../services/api';
import { Loader2 } from 'lucide-react';

function getWeekStart() {
  const now = new Date();
  const day = now.getDay() || 7; // 周日=7
  const monday = new Date(now);
  monday.setDate(now.getDate() - day + 1);
  return monday.toISOString().split('T')[0];
}

export default function TimesheetSummary({ data: _data }) {
  const [weeklyHours, setWeeklyHours] = useState(null);
  const [loading, setLoading] = useState(true);
  const targetHours = 40;

  useEffect(() => {
    let cancelled = false;
    async function fetchData() {
      try {
        const weekStart = getWeekStart();
        const response = await timesheetApi.getWeek({ week_start: weekStart });
        if (cancelled) return;
        const data = response.data?.data || response.data;
        const timesheets = data?.timesheets || [];
        const total = (timesheets || []).reduce(
          (sum, ts) => sum + (parseFloat(ts.work_hours) || 0),
          0
        );
        setWeeklyHours(Math.round(total * 10) / 10);
      } catch (error) {
        console.error('加载本周工时失败:', error);
        if (!cancelled) setWeeklyHours(0);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    fetchData();
    return () => { cancelled = true; };
  }, []);

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium">本周工时</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-center h-24">
          {loading ? (
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          ) : (
            <div className="text-center">
              <p className="text-3xl font-bold">{weeklyHours}</p>
              <p className="text-sm text-muted-foreground">小时 / {targetHours}小时</p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
