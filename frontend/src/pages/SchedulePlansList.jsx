import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { Calendar, ChevronRight } from "lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../components/ui";
import { scheduleGenerationApi } from "../services/api";
import { toast } from "sonner";

export default function SchedulePlansList() {
  const [searchParams] = useSearchParams();
  const projectId = searchParams.get("project_id");
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadPlans = async () => {
      setLoading(true);
      try {
        const response = await scheduleGenerationApi.listSchedulePlans(projectId);
        const data = response.data || response;
        setPlans(data.items || []);
      } catch (error) {
        console.error("加载计划列表失败:", error);
        toast.error("加载计划列表失败");
      } finally {
        setLoading(false);
      }
    };

    loadPlans();
  }, [projectId]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="container mx-auto px-4 py-6 space-y-6">
        <PageHeader
          title="计划方案列表"
          description={projectId ? `项目 ${projectId} 的已保存计划方案` : "已保存的 AI 排计划方案"}
        />

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="w-5 h-5 text-blue-500" />
              已保存方案
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="py-8 text-center text-slate-400">加载中...</div>
            ) : plans.length === 0 ? (
              <div className="py-8 text-center text-slate-400">暂无已保存方案</div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>方案编号</TableHead>
                    <TableHead>项目</TableHead>
                    <TableHead>模式</TableHead>
                    <TableHead>工期</TableHead>
                    <TableHead>状态</TableHead>
                    <TableHead>操作</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {plans.map((plan) => (
                    <TableRow key={plan.id}>
                      <TableCell className="font-medium">{plan.plan_no}</TableCell>
                      <TableCell>{plan.project_name}</TableCell>
                      <TableCell>{plan.mode_name || plan.schedule_mode}</TableCell>
                      <TableCell>{plan.total_days}天</TableCell>
                      <TableCell>
                        <Badge variant="outline">{plan.status}</Badge>
                      </TableCell>
                      <TableCell>
                        <Button asChild variant="outline" size="sm">
                          <Link to={`/schedule-plans/${plan.id}`}>
                            查看详情
                            <ChevronRight className="w-4 h-4 ml-1" />
                          </Link>
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
