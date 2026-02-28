import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { Users, FolderKanban, Wallet, Clock3 } from "lucide-react";

import { PageHeader } from "../components/layout";
import { Badge } from "../components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../components/ui/table";
import { staggerContainer, fadeIn } from "../lib/animations";
import { laborCostApi } from "../services/api/laborCost";

const formatCurrency = (value) =>
  `¥${Number(value || 0).toLocaleString("zh-CN", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;

const formatHours = (value) => `${Number(value || 0).toFixed(1)}h`;

const completionVariant = (rate) => {
  if (rate >= 80) {
    return "success";
  }
  if (rate >= 50) {
    return "warning";
  }
  return "secondary";
};

export default function LaborCostDetail() {
  const [summaryData, setSummaryData] = useState(null);
  const [engineerData, setEngineerData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    (async () => {
      try {
        const [summaryRes, engineerRes] = await Promise.all([
          laborCostApi.summary(),
          laborCostApi.byEngineer(),
        ]);
        setSummaryData(summaryRes.data || summaryRes);
        setEngineerData(engineerRes.data || engineerRes);
      } catch (err) {
        setError(err?.response?.data?.detail || err?.message || "加载失败");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const summary = summaryData?.summary || {};
  const projects = summaryData?.projects || [];
  const engineerSummary = engineerData?.summary || {};
  const engineers = engineerData?.engineers || [];

  const cards = useMemo(
    () => [
      {
        label: "项目数",
        value: summary.total_projects || 0,
        icon: FolderKanban,
        helper: `${summary.total_records || 0} 条人工成本记录`,
        color: "text-sky-400",
      },
      {
        label: "人工成本总额",
        value: formatCurrency(summary.total_labor_cost || 0),
        icon: Wallet,
        helper: `项目均值 ${formatCurrency(summary.avg_labor_cost_per_project || 0)}`,
        color: "text-emerald-400",
      },
      {
        label: "工单总工时",
        value: formatHours(engineerSummary.total_hours || 0),
        icon: Clock3,
        helper: `${engineerSummary.total_work_orders || 0} 张工单`,
        color: "text-amber-400",
      },
      {
        label: "工程师投入",
        value: engineerSummary.total_engineers || 0,
        icon: Users,
        helper: `工时成本 ${formatCurrency(engineerSummary.avg_cost_per_hour || 0)}/h`,
        color: "text-violet-400",
      },
    ],
    [summary, engineerSummary],
  );

  return (
    <div className="space-y-6">
      <PageHeader title="人工成本明细" description="按项目与工程师双视角分析人工成本结构" />

      {loading ? (
        <div className="py-14 text-center text-slate-400">人工成本数据加载中...</div>
      ) : (
        <motion.div variants={staggerContainer} initial="hidden" animate="visible" className="space-y-6">
          {error && (
            <motion.div variants={fadeIn} className="rounded-xl border border-red-500/30 bg-red-900/10 px-4 py-3 text-sm text-red-300">
              {error}
            </motion.div>
          )}

          <motion.div variants={fadeIn} className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {cards.map((card) => {
              const Icon = card.icon;
              return (
                <Card
                  key={card.label}
                  hover={false}
                  className="border-white/10 bg-gradient-to-br from-slate-900/80 to-slate-950/60"
                >
                  <CardContent className="p-5">
                    <div className="mb-3 flex items-center justify-between">
                      <span className="text-xs tracking-wide text-slate-400">{card.label}</span>
                      <Icon className={`h-4 w-4 ${card.color}`} />
                    </div>
                    <div className={`text-2xl font-semibold ${card.color}`}>{card.value}</div>
                    <div className="mt-1 text-xs text-slate-500">{card.helper}</div>
                  </CardContent>
                </Card>
              );
            })}
          </motion.div>

          <motion.div variants={fadeIn}>
            <Card hover={false} className="border-white/10 bg-slate-950/60">
              <CardHeader className="flex flex-row items-center justify-between space-y-0">
                <CardTitle className="text-base text-white">按项目人工成本</CardTitle>
                <Badge variant="info">{projects.length} 个项目</Badge>
              </CardHeader>
              <CardContent className="pt-0">
                <Table>
                  <TableHeader>
                    <TableRow className="border-white/10 hover:bg-transparent">
                      <TableHead className="text-slate-400">项目</TableHead>
                      <TableHead className="text-right text-slate-400">人工成本</TableHead>
                      <TableHead className="text-right text-slate-400">占比</TableHead>
                      <TableHead className="text-right text-slate-400">记录数</TableHead>
                      <TableHead className="text-right text-slate-400">最近成本日期</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {projects.length === 0 ? (
                      <TableRow className="border-white/10">
                        <TableCell colSpan={5} className="py-10 text-center text-sm text-slate-500">
                          暂无项目人工成本数据
                        </TableCell>
                      </TableRow>
                    ) : (
                      projects.map((project) => (
                        <TableRow key={project.project_id} className="border-white/5 hover:bg-white/[0.03]">
                          <TableCell>
                            <div className="font-medium text-slate-200">{project.project_name}</div>
                            <div className="text-xs text-slate-500">{project.project_code || "-"}</div>
                          </TableCell>
                          <TableCell className="text-right font-mono text-emerald-300">
                            {formatCurrency(project.labor_cost)}
                          </TableCell>
                          <TableCell className="text-right">
                            <Badge variant="secondary">{(project.labor_cost_pct || 0).toFixed(2)}%</Badge>
                          </TableCell>
                          <TableCell className="text-right text-slate-300">{project.record_count || 0}</TableCell>
                          <TableCell className="text-right text-slate-400">
                            {project.last_cost_date || "-"}
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div variants={fadeIn}>
            <Card hover={false} className="border-white/10 bg-slate-950/60">
              <CardHeader className="flex flex-row items-center justify-between space-y-0">
                <CardTitle className="text-base text-white">按工程师成本拆解</CardTitle>
                <Badge variant="secondary">
                  估算时薪 ¥{engineerSummary.hourly_rate_used || 0}/h
                </Badge>
              </CardHeader>
              <CardContent className="pt-0">
                <Table>
                  <TableHeader>
                    <TableRow className="border-white/10 hover:bg-transparent">
                      <TableHead className="text-slate-400">工程师</TableHead>
                      <TableHead className="text-right text-slate-400">覆盖项目</TableHead>
                      <TableHead className="text-right text-slate-400">工单数</TableHead>
                      <TableHead className="text-right text-slate-400">总工时</TableHead>
                      <TableHead className="text-right text-slate-400">估算人工成本</TableHead>
                      <TableHead className="text-right text-slate-400">完工率</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {engineers.length === 0 ? (
                      <TableRow className="border-white/10">
                        <TableCell colSpan={6} className="py-10 text-center text-sm text-slate-500">
                          暂无工程师工单成本数据
                        </TableCell>
                      </TableRow>
                    ) : (
                      engineers.map((engineer) => (
                        <TableRow key={engineer.engineer_id} className="border-white/5 hover:bg-white/[0.03]">
                          <TableCell className="font-medium text-slate-200">{engineer.engineer_name}</TableCell>
                          <TableCell className="text-right text-slate-300">{engineer.project_count || 0}</TableCell>
                          <TableCell className="text-right text-slate-300">{engineer.work_order_count || 0}</TableCell>
                          <TableCell className="text-right text-amber-300">
                            {formatHours(engineer.total_hours)}
                          </TableCell>
                          <TableCell className="text-right font-mono text-emerald-300">
                            {formatCurrency(engineer.estimated_labor_cost)}
                          </TableCell>
                          <TableCell className="text-right">
                            <Badge variant={completionVariant(engineer.completion_rate || 0)}>
                              {(engineer.completion_rate || 0).toFixed(1)}%
                            </Badge>
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </motion.div>
        </motion.div>
      )}
    </div>
  );
}
