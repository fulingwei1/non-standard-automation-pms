/**
 * 销售侧售前工作台总览
 *
 * 聚合工单、方案、模板资产和漏斗健康数据，
 * 作为销售模块进入售前技术能力的统一入口。
 */

import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  ClipboardList,
  FileText,
  LayoutTemplate,
  RefreshCw,
  ShieldAlert,
  Workflow,
} from "lucide-react";
import { PageHeader } from "../components/layout";
import {
  Badge,
  Button,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Progress,
} from "../components/ui";
import { presaleWorkbenchApi } from "../services/api";

function formatDate(value) {
  if (!value) {
    return "未更新";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return String(value);
  }

  return date.toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatPercent(value, fractionDigits = 1) {
  return `${Number(value || 0).toFixed(fractionDigits)}%`;
}

function getHealthMeta(level) {
  if (level === "EXCELLENT") {
    return { label: "优秀", className: "bg-emerald-500" };
  }
  if (level === "GOOD") {
    return { label: "良好", className: "bg-blue-500" };
  }
  if (level === "FAIR") {
    return { label: "一般", className: "bg-amber-500" };
  }
  return { label: level || "偏弱", className: "bg-red-500" };
}

const quickLinks = [
  {
    title: "销售漏斗",
    description: "查看阶段流转、转化率和瓶颈分析。",
    to: "/sales/funnel",
    icon: Workflow,
  },
  {
    title: "售前任务",
    description: "进入售前工单、协同任务和交付追踪。",
    to: "/sales/presales-tasks",
    icon: ClipboardList,
  },
  {
    title: "模板中心",
    description: "统一查看评估模板、报价模板和标准资产。",
    to: "/sales/templates/center",
    icon: LayoutTemplate,
  },
  {
    title: "线索池",
    description: "从线索进入需求包、技术评估与阶段门推进。",
    to: "/sales/leads",
    icon: Activity,
  },
];

export default function SalesPresaleWorkbench() {
  const [loading, setLoading] = useState(true);
  const [overview, setOverview] = useState(null);
  const [error, setError] = useState(null);
  const [refreshToken, setRefreshToken] = useState(0);

  useEffect(() => {
    let cancelled = false;

    const loadOverview = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await presaleWorkbenchApi.loadOverview();
        if (cancelled) {
          return;
        }
        setOverview(data);
      } catch (loadError) {
        if (cancelled) {
          return;
        }
        setError(loadError.response?.data?.detail || loadError.message || "加载失败");
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    loadOverview();

    return () => {
      cancelled = true;
    };
  }, [refreshToken]);

  const ticketItems = overview?.tickets?.items || [];
  const solutionItems = overview?.solutions?.items || [];
  const assessmentTemplates = overview?.templates?.assessment?.items || [];
  const technicalTemplates = overview?.templates?.technical?.items || [];
  const health = overview?.funnel?.health || {};
  const summary = overview?.funnel?.summary || {};
  const dwellAlerts = overview?.funnel?.dwellAlerts?.items || [];
  const conversionStages = overview?.funnel?.conversion?.stages || [];
  const failures = overview?.meta?.failures || [];
  const healthMeta = getHealthMeta(health?.overall_health?.level);

  const topTemplateNames = useMemo(
    () =>
      [...assessmentTemplates.slice(0, 2), ...technicalTemplates.slice(0, 2)].map(
        (item) => item.template_name || item.name || `模板 #${item.id}`,
      ),
    [assessmentTemplates, technicalTemplates],
  );

  return (
    <div className="min-h-screen bg-gray-950 px-6 py-6 text-white">
      <PageHeader
        title="售前工作台总览"
        description="从销售模块进入售前能力的统一入口，集中查看工单、方案、模板和漏斗健康。"
        actions={[
          {
            label: "销售漏斗",
            icon: Workflow,
            to: "/sales/funnel",
            variant: "outline",
            className: "border-blue-500 text-blue-300 hover:bg-blue-500/10",
          },
          {
            label: "刷新",
            icon: RefreshCw,
            onClick: () => setRefreshToken((value) => value + 1),
            variant: "outline",
            disabled: loading,
          },
        ]}
      />

      <div className="space-y-6">
        {error && (
          <div className="rounded-lg border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-200">
            {error}
          </div>
        )}

        {failures.length > 0 && (
          <div className="rounded-lg border border-amber-500/40 bg-amber-500/10 px-4 py-3 text-sm text-amber-100">
            部分模块加载失败：
            {failures.map((item) => ` ${item.key}(${item.message})`).join("；")}
          </div>
        )}

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
          <Card className="border-gray-800 bg-gray-900">
            <CardContent className="pt-5">
              <div className="text-sm text-gray-400">售前工单</div>
              <div className="mt-2 text-3xl font-semibold">{overview?.tickets?.total || 0}</div>
            </CardContent>
          </Card>
          <Card className="border-gray-800 bg-gray-900">
            <CardContent className="pt-5">
              <div className="text-sm text-gray-400">关联方案</div>
              <div className="mt-2 text-3xl font-semibold">{overview?.solutions?.total || 0}</div>
            </CardContent>
          </Card>
          <Card className="border-gray-800 bg-gray-900">
            <CardContent className="pt-5">
              <div className="text-sm text-gray-400">模板资产</div>
              <div className="mt-2 text-3xl font-semibold">
                {(overview?.templates?.assessment?.total || 0) +
                  (overview?.templates?.technical?.total || 0)}
              </div>
            </CardContent>
          </Card>
          <Card className="border-gray-800 bg-gray-900">
            <CardContent className="pt-5">
              <div className="text-sm text-gray-400">活跃预警</div>
              <div className="mt-2 text-3xl font-semibold">{overview?.funnel?.dwellAlerts?.total || 0}</div>
            </CardContent>
          </Card>
          <Card className="border-gray-800 bg-gray-900">
            <CardContent className="pt-5">
              <div className="flex items-center justify-between gap-2">
                <div>
                  <div className="text-sm text-gray-400">漏斗健康</div>
                  <div className="mt-2 text-3xl font-semibold">
                    {health?.overall_health?.score || 0}
                  </div>
                </div>
                <Badge className={healthMeta.className}>{healthMeta.label}</Badge>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="grid gap-4 lg:grid-cols-2 xl:grid-cols-4">
          {quickLinks.map((item) => {
            const Icon = item.icon;
            return (
              <Link key={item.to} to={item.to}>
                <Card className="h-full border-gray-800 bg-gray-900 transition-colors hover:border-gray-700">
                  <CardContent className="flex h-full flex-col justify-between pt-5">
                    <div>
                      <div className="mb-3 flex items-center gap-2">
                        <Icon className="h-5 w-5 text-blue-400" />
                        <div className="font-medium">{item.title}</div>
                      </div>
                      <div className="text-sm text-gray-400">{item.description}</div>
                    </div>
                    <div className="mt-4 flex items-center gap-2 text-sm text-blue-300">
                      进入
                      <ArrowRight className="h-4 w-4" />
                    </div>
                  </CardContent>
                </Card>
              </Link>
            );
          })}
        </div>

        <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
          <Card className="border-gray-800 bg-gray-900">
            <CardHeader>
              <CardTitle>近期工单与方案</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="text-sm font-medium text-gray-300">售前工单</div>
                  <Link to="/sales/presales-tasks">
                    <Button variant="outline" size="sm">
                      查看全部
                    </Button>
                  </Link>
                </div>
                {ticketItems.slice(0, 5).map((ticket) => (
                  <div key={ticket.id} className="rounded-lg bg-gray-950 px-3 py-3">
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <div className="font-medium">
                          {ticket.ticket_no || `工单 #${ticket.id}`}
                        </div>
                        <div className="mt-1 text-sm text-gray-400">
                          {ticket.title || ticket.requirement_title || "未命名售前工单"}
                        </div>
                      </div>
                      <Badge>{ticket.status || "待处理"}</Badge>
                    </div>
                  </div>
                ))}
                {ticketItems.length === 0 && (
                  <div className="text-sm text-gray-400">暂无售前工单</div>
                )}
              </div>

              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="text-sm font-medium text-gray-300">关联方案</div>
                  <Link to="/presales/solutions">
                    <Button variant="outline" size="sm">
                      查看全部
                    </Button>
                  </Link>
                </div>
                {solutionItems.slice(0, 5).map((solution) => (
                  <div key={solution.id} className="rounded-lg bg-gray-950 px-3 py-3">
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <div className="font-medium">
                          {solution.solution_name || solution.name || `方案 #${solution.id}`}
                        </div>
                        <div className="mt-1 text-sm text-gray-400">
                          更新时间 {formatDate(solution.updated_at || solution.created_at)}
                        </div>
                      </div>
                      <Badge>{solution.status || solution.review_status || "未标记"}</Badge>
                    </div>
                  </div>
                ))}
                {solutionItems.length === 0 && (
                  <div className="text-sm text-gray-400">暂无关联方案</div>
                )}
              </div>
            </CardContent>
          </Card>

          <Card className="border-gray-800 bg-gray-900">
            <CardHeader>
              <CardTitle>漏斗健康与模板资产</CardTitle>
            </CardHeader>
            <CardContent className="space-y-5">
              <div className="rounded-lg bg-gray-950 p-4">
                <div className="mb-2 flex items-center gap-2">
                  <Workflow className="h-4 w-4 text-blue-400" />
                  <span className="font-medium">漏斗摘要</span>
                </div>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div className="rounded bg-gray-900 px-3 py-2">
                    线索
                    <div className="mt-1 text-lg font-semibold">{summary.leads || 0}</div>
                  </div>
                  <div className="rounded bg-gray-900 px-3 py-2">
                    商机
                    <div className="mt-1 text-lg font-semibold">{summary.opportunities || 0}</div>
                  </div>
                  <div className="rounded bg-gray-900 px-3 py-2">
                    报价
                    <div className="mt-1 text-lg font-semibold">{summary.quotes || 0}</div>
                  </div>
                  <div className="rounded bg-gray-900 px-3 py-2">
                    合同
                    <div className="mt-1 text-lg font-semibold">{summary.contracts || 0}</div>
                  </div>
                </div>
                <div className="mt-4 text-sm text-gray-400">
                  目标覆盖率 {formatPercent(health?.key_metrics?.target_coverage)}
                </div>
                <Progress
                  className="mt-2 h-2"
                  value={Math.min(Number(health?.key_metrics?.target_coverage || 0), 100)}
                />
              </div>

              <div className="space-y-3">
                <div className="text-sm font-medium text-gray-300">关键预警</div>
                {dwellAlerts.slice(0, 4).map((alert) => (
                  <div key={alert.id} className="rounded-lg bg-gray-950 px-3 py-3">
                    <div className="flex items-center gap-2">
                      <ShieldAlert className="h-4 w-4 text-amber-400" />
                      <div className="font-medium">{alert.stage || "未知阶段"}</div>
                      <Badge className={alert.severity === "CRITICAL" ? "bg-red-500" : "bg-amber-500"}>
                        {alert.severity}
                      </Badge>
                    </div>
                    <div className="mt-1 text-sm text-gray-400">
                      已停留 {alert.dwell_hours || 0} 小时 / 阈值 {alert.threshold_hours || 0} 小时
                    </div>
                  </div>
                ))}
                {dwellAlerts.length === 0 && (
                  <div className="text-sm text-gray-400">暂无活跃预警</div>
                )}
              </div>

              <div className="space-y-3">
                <div className="text-sm font-medium text-gray-300">模板资产</div>
                {topTemplateNames.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {topTemplateNames.map((name) => (
                      <Badge key={name} variant="outline">
                        {name}
                      </Badge>
                    ))}
                  </div>
                ) : (
                  <div className="text-sm text-gray-400">暂无模板资产</div>
                )}
              </div>

              <div className="space-y-3">
                <div className="text-sm font-medium text-gray-300">阶段转化快照</div>
                {conversionStages.slice(0, 4).map((stage) => (
                  <div key={stage.stage} className="rounded-lg bg-gray-950 px-3 py-3">
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <div className="font-medium">{stage.stage_name || stage.stage}</div>
                        <div className="mt-1 text-sm text-gray-400">
                          累计 {stage.count || 0} 个机会
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-sm font-semibold">
                          {stage.conversion_to_next == null
                            ? "最终阶段"
                            : formatPercent(stage.conversion_to_next)}
                        </div>
                        <div className="text-xs text-gray-500">
                          {stage.avg_days_in_stage == null
                            ? "未统计"
                            : `平均 ${stage.avg_days_in_stage} 天`}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
                {conversionStages.length === 0 && (
                  <div className="text-sm text-gray-400">暂无阶段转化数据</div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        <Card className="border-gray-800 bg-gray-900">
          <CardHeader>
            <CardTitle>评估与技术入口提示</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 lg:grid-cols-3">
            <div className="rounded-lg bg-gray-950 p-4">
              <div className="mb-2 flex items-center gap-2">
                <Activity className="h-4 w-4 text-blue-400" />
                <span className="font-medium">线索评估</span>
              </div>
              <div className="text-sm text-gray-400">
                从线索详情进入需求包、技术评估、阶段门和冻结管理。
              </div>
              <Link to="/sales/leads" className="mt-3 inline-flex items-center gap-2 text-sm text-blue-300">
                进入线索池
                <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
            <div className="rounded-lg bg-gray-950 p-4">
              <div className="mb-2 flex items-center gap-2">
                <FileText className="h-4 w-4 text-violet-400" />
                <span className="font-medium">方案协同</span>
              </div>
              <div className="text-sm text-gray-400">
                对接售前方案、成本估算和模板中心，减少线索到方案的断层。
              </div>
              <Link
                to="/presales/solutions"
                className="mt-3 inline-flex items-center gap-2 text-sm text-blue-300"
              >
                进入方案中心
                <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
            <div className="rounded-lg bg-gray-950 p-4">
              <div className="mb-2 flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-amber-400" />
                <span className="font-medium">漏斗预警</span>
              </div>
              <div className="text-sm text-gray-400">
                对异常停留和低转化阶段做统一跟进，不再靠人工分散排查。
              </div>
              <Link to="/sales/funnel" className="mt-3 inline-flex items-center gap-2 text-sm text-blue-300">
                打开漏斗页
                <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
