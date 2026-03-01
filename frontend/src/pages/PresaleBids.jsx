import { useMemo, useState } from "react";
import {
  Award,
  BarChart3,
  CalendarClock,
  CheckCircle2,
  Clock3,
  FileSearch,
  Gavel,
  Target,
  TrendingUp,
  Users,
  XCircle,
} from "lucide-react";
import { PageHeader } from "../components/layout";
import {
  Alert,
  AlertDescription,
  AlertTitle,
  Badge,
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Progress,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "../components/ui";
import { cn } from "../lib/utils";

const bidStatusConfig = {
  tracking: {
    label: "线索跟踪",
    badgeClass: "bg-slate-500/20 text-slate-200 border border-slate-500/40",
  },
  preparing: {
    label: "标书准备",
    badgeClass: "bg-blue-500/20 text-blue-300 border border-blue-500/40",
  },
  submitted: {
    label: "已投标",
    badgeClass: "bg-violet-500/20 text-violet-300 border border-violet-500/40",
  },
  evaluating: {
    label: "评标阶段",
    badgeClass: "bg-amber-500/20 text-amber-300 border border-amber-500/40",
  },
  won: {
    label: "已中标",
    badgeClass: "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40",
  },
  lost: {
    label: "未中标",
    badgeClass: "bg-rose-500/20 text-rose-300 border border-rose-500/40",
  },
};

const presaleBids = [
  {
    id: "BID-2026-018",
    projectName: "宁德时代 PACK 线体升级项目",
    customer: "宁德时代",
    owner: "李海峰",
    bidAmount: 960,
    status: "evaluating",
    progress: 85,
    winRate: 72,
    deadline: "2026-03-15",
    competitors: 3,
    timeline: [
      { stage: "tracking", date: "2026-01-12", owner: "李海峰", note: "商机立项并完成信息收集" },
      { stage: "preparing", date: "2026-01-26", owner: "赵文博", note: "技术方案 V1 评审通过" },
      { stage: "submitted", date: "2026-02-18", owner: "李海峰", note: "商务+技术标已提交" },
      { stage: "evaluating", date: "2026-02-23", owner: "客户评委会", note: "进入现场答辩与澄清环节" },
    ],
  },
  {
    id: "BID-2026-017",
    projectName: "比亚迪模组测试工站改造",
    customer: "比亚迪",
    owner: "王晨",
    bidAmount: 540,
    status: "submitted",
    progress: 70,
    winRate: 63,
    deadline: "2026-03-08",
    competitors: 2,
    timeline: [
      { stage: "tracking", date: "2026-01-05", owner: "王晨", note: "客户需求明确，进入售前支持" },
      { stage: "preparing", date: "2026-01-21", owner: "黄雅婷", note: "完成 BOM 与风险评审" },
      { stage: "submitted", date: "2026-02-24", owner: "王晨", note: "投标文件递交完成" },
    ],
  },
  {
    id: "BID-2026-013",
    projectName: "蜂巢能源 EOL 自动化线",
    customer: "蜂巢能源",
    owner: "陈锐",
    bidAmount: 1280,
    status: "won",
    progress: 100,
    winRate: 88,
    deadline: "2026-02-20",
    competitors: 4,
    timeline: [
      { stage: "tracking", date: "2025-12-20", owner: "陈锐", note: "客户高层访谈完成" },
      { stage: "preparing", date: "2026-01-08", owner: "售前组", note: "完成方案冻结与报价策略" },
      { stage: "submitted", date: "2026-01-29", owner: "陈锐", note: "递交投标文件" },
      { stage: "evaluating", date: "2026-02-11", owner: "客户评审组", note: "完成二轮技术澄清" },
      { stage: "won", date: "2026-02-20", owner: "客户采购部", note: "收到中标通知书" },
    ],
  },
  {
    id: "BID-2026-010",
    projectName: "国轩高科试制线扩建",
    customer: "国轩高科",
    owner: "徐立",
    bidAmount: 720,
    status: "lost",
    progress: 100,
    winRate: 39,
    deadline: "2026-01-30",
    competitors: 5,
    timeline: [
      { stage: "tracking", date: "2025-12-01", owner: "徐立", note: "项目接触，竞争格局确认" },
      { stage: "preparing", date: "2025-12-26", owner: "售前组", note: "完成方案与报价" },
      { stage: "submitted", date: "2026-01-10", owner: "徐立", note: "按期投标" },
      { stage: "evaluating", date: "2026-01-20", owner: "客户评委会", note: "现场述标完成" },
      { stage: "lost", date: "2026-01-30", owner: "客户采购部", note: "价格因素失标，差额约 4.8%" },
    ],
  },
  {
    id: "BID-2026-021",
    projectName: "欣旺达智能装配段新增线体",
    customer: "欣旺达",
    owner: "周宁",
    bidAmount: 680,
    status: "preparing",
    progress: 46,
    winRate: 57,
    deadline: "2026-03-27",
    competitors: 2,
    timeline: [
      { stage: "tracking", date: "2026-02-09", owner: "周宁", note: "完成需求澄清会议" },
      { stage: "preparing", date: "2026-02-25", owner: "周宁", note: "方案编制中，待成本复核" },
    ],
  },
];

const formatBidAmount = (amountInTenThousand) =>
  `¥${(amountInTenThousand || 0).toLocaleString()}万`;

const getDaysLeft = (deadline) => {
  if (!deadline) {
    return null;
  }

  const end = new Date(deadline).getTime();
  const now = Date.now();
  const day = 1000 * 60 * 60 * 24;
  return Math.ceil((end - now) / day);
};

export default function PresaleBids() {
  const [selectedBidId, setSelectedBidId] = useState(presaleBids[0]?.id || "");

  const selectedBid = useMemo(
    () => presaleBids.find((item) => item.id === selectedBidId) || presaleBids[0],
    [selectedBidId],
  );

  const overviewStats = useMemo(() => {
    const total = presaleBids.length;
    const won = presaleBids.filter((item) => item.status === "won").length;
    const lost = presaleBids.filter((item) => item.status === "lost").length;
    const active = presaleBids.filter(
      (item) => !["won", "lost"].includes(item.status),
    ).length;
    const amount = presaleBids.reduce((sum, item) => sum + item.bidAmount, 0);
    const weightedAmount = presaleBids.reduce(
      (sum, item) => sum + item.bidAmount * (item.winRate / 100),
      0,
    );
    const winRate = won + lost > 0 ? Math.round((won / (won + lost)) * 100) : 0;

    return {
      total,
      active,
      winRate,
      totalAmount: amount,
      weightedAmount,
    };
  }, []);

  const statusDistribution = useMemo(
    () =>
      Object.keys(bidStatusConfig).map((status) => ({
        status,
        label: bidStatusConfig[status].label,
        count: presaleBids.filter((item) => item.status === status).length,
      })),
    [],
  );

  const winRateBuckets = useMemo(() => {
    const high = presaleBids.filter((item) => item.winRate >= 75).length;
    const medium = presaleBids.filter(
      (item) => item.winRate >= 50 && item.winRate < 75,
    ).length;
    const low = presaleBids.filter((item) => item.winRate < 50).length;

    return [
      { label: "高概率 (>=75%)", count: high, value: (high / presaleBids.length) * 100 },
      { label: "中概率 (50%-74%)", count: medium, value: (medium / presaleBids.length) * 100 },
      { label: "低概率 (<50%)", count: low, value: (low / presaleBids.length) * 100 },
    ];
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="container mx-auto px-4 py-6 space-y-6">
        <PageHeader
          title="售前投标中心"
          description="投标列表、详情追踪、状态流转与中标率统计一体化看板"
          actions={[
            { label: "导出周报", icon: FileSearch, variant: "outline" },
            { label: "新建投标", icon: Gavel },
          ]}
        />

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400">投标总数</p>
                  <p className="text-3xl font-semibold">{overviewStats.total}</p>
                </div>
                <Target className="h-8 w-8 text-blue-400" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400">进行中项目</p>
                  <p className="text-3xl font-semibold text-cyan-300">{overviewStats.active}</p>
                </div>
                <Clock3 className="h-8 w-8 text-cyan-400" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400">历史中标率</p>
                  <p className="text-3xl font-semibold text-emerald-300">{overviewStats.winRate}%</p>
                </div>
                <Award className="h-8 w-8 text-emerald-400" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400">加权签约额</p>
                  <p className="text-3xl font-semibold text-violet-300">
                    {formatBidAmount(Math.round(overviewStats.weightedAmount))}
                  </p>
                </div>
                <TrendingUp className="h-8 w-8 text-violet-400" />
              </div>
            </CardContent>
          </Card>
        </div>

        <Tabs defaultValue="list" className="space-y-6">
          <TabsList className="grid w-full max-w-[520px] grid-cols-3">
            <TabsTrigger value="list">投标列表</TabsTrigger>
            <TabsTrigger value="tracking">状态跟踪</TabsTrigger>
            <TabsTrigger value="analytics">中标率统计</TabsTrigger>
          </TabsList>

          <TabsContent value="list" className="space-y-4">
            <div className="grid gap-4 xl:grid-cols-[1.8fr,1fr]">
              <Card>
                <CardHeader>
                  <CardTitle>投标项目清单</CardTitle>
                  <CardDescription>点击行可查看右侧投标详情与里程碑</CardDescription>
                </CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>项目</TableHead>
                        <TableHead>阶段</TableHead>
                        <TableHead>投标金额</TableHead>
                        <TableHead>预计赢率</TableHead>
                        <TableHead>截止日期</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {presaleBids.map((bid) => (
                        <TableRow
                          key={bid.id}
                          onClick={() => setSelectedBidId(bid.id)}
                          className={cn(
                            "cursor-pointer hover:bg-slate-800/40",
                            selectedBid?.id === bid.id && "bg-slate-800/50",
                          )}
                        >
                          <TableCell>
                            <div className="space-y-1">
                              <p className="font-medium text-slate-100">{bid.projectName}</p>
                              <p className="text-xs text-slate-400">
                                {bid.customer} · {bid.id}
                              </p>
                            </div>
                          </TableCell>
                          <TableCell>
                            <Badge className={bidStatusConfig[bid.status]?.badgeClass}>
                              {bidStatusConfig[bid.status]?.label}
                            </Badge>
                          </TableCell>
                          <TableCell>{formatBidAmount(bid.bidAmount)}</TableCell>
                          <TableCell className="w-[180px]">
                            <div className="space-y-2">
                              <div className="flex items-center justify-between text-xs">
                                <span className="text-slate-400">赢率</span>
                                <span className="text-slate-100">{bid.winRate}%</span>
                              </div>
                              <Progress value={bid.winRate} className="h-1.5" />
                            </div>
                          </TableCell>
                          <TableCell>{bid.deadline}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>投标详情</CardTitle>
                  <CardDescription>项目负责人、竞争强度、状态轨迹</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {selectedBid ? (
                    <>
                      <div className="space-y-1">
                        <p className="text-lg font-semibold">{selectedBid.projectName}</p>
                        <p className="text-sm text-slate-400">
                          {selectedBid.customer} · 负责人 {selectedBid.owner}
                        </p>
                      </div>

                      <div className="grid grid-cols-2 gap-3">
                        <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-3">
                          <p className="text-xs text-slate-400">投标金额</p>
                          <p className="text-base font-semibold">
                            {formatBidAmount(selectedBid.bidAmount)}
                          </p>
                        </div>
                        <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-3">
                          <p className="text-xs text-slate-400">竞争对手</p>
                          <p className="text-base font-semibold">{selectedBid.competitors} 家</p>
                        </div>
                        <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-3">
                          <p className="text-xs text-slate-400">当前进度</p>
                          <p className="text-base font-semibold">{selectedBid.progress}%</p>
                        </div>
                        <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-3">
                          <p className="text-xs text-slate-400">赢单概率</p>
                          <p className="text-base font-semibold">{selectedBid.winRate}%</p>
                        </div>
                      </div>

                      {getDaysLeft(selectedBid.deadline) !== null &&
                      getDaysLeft(selectedBid.deadline) <= 7 &&
                      !["won", "lost"].includes(selectedBid.status) ? (
                        <Alert className="border-amber-500/40 bg-amber-500/10">
                          <CalendarClock className="h-4 w-4 text-amber-300" />
                          <AlertTitle>临近截止提醒</AlertTitle>
                          <AlertDescription>
                            当前投标距离截止仅剩 {getDaysLeft(selectedBid.deadline)} 天，请优先推进澄清与定稿。
                          </AlertDescription>
                        </Alert>
                      ) : null}

                      <div className="space-y-3">
                        <p className="text-sm font-medium text-slate-300">状态轨迹</p>
                        <div className="space-y-3">
                          {selectedBid.timeline.map((item, index) => {
                            const isClosed = ["won", "lost"].includes(selectedBid.status);
                            const isDone = isClosed || index < selectedBid.timeline.length - 1;
                            const Icon = isDone ? CheckCircle2 : Clock3;

                            return (
                              <div key={`${item.stage}-${item.date}`} className="flex items-start gap-3">
                                <div
                                  className={cn(
                                    "mt-0.5 rounded-full p-1",
                                    isDone ? "bg-emerald-500/20" : "bg-blue-500/20",
                                  )}
                                >
                                  <Icon
                                    className={cn(
                                      "h-4 w-4",
                                      isDone ? "text-emerald-300" : "text-blue-300",
                                    )}
                                  />
                                </div>
                                <div className="flex-1">
                                  <div className="flex items-center gap-2">
                                    <p className="text-sm font-medium">
                                      {bidStatusConfig[item.stage]?.label || item.stage}
                                    </p>
                                    <span className="text-xs text-slate-500">{item.date}</span>
                                  </div>
                                  <p className="text-xs text-slate-400 mt-1">
                                    {item.owner} · {item.note}
                                  </p>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    </>
                  ) : (
                    <p className="text-sm text-slate-400">暂无可展示的投标详情</p>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="tracking" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>投标状态跟踪</CardTitle>
                <CardDescription>按项目查看阶段位置、截止时间和推进优先级</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {presaleBids.map((bid) => {
                  const daysLeft = getDaysLeft(bid.deadline);
                  const isClosed = ["won", "lost"].includes(bid.status);

                  return (
                    <div
                      key={bid.id}
                      className="rounded-lg border border-slate-800 bg-slate-900/40 p-4 space-y-2"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <p className="font-medium text-slate-100">{bid.projectName}</p>
                          <p className="text-xs text-slate-400">
                            {bid.customer} · 负责人 {bid.owner}
                          </p>
                        </div>
                        <Badge className={bidStatusConfig[bid.status]?.badgeClass}>
                          {bidStatusConfig[bid.status]?.label}
                        </Badge>
                      </div>
                      <Progress value={bid.progress} className="h-2" />
                      <div className="flex flex-wrap gap-4 text-xs text-slate-400">
                        <span>进度 {bid.progress}%</span>
                        <span>预计赢率 {bid.winRate}%</span>
                        <span>截止 {bid.deadline}</span>
                        {!isClosed && daysLeft !== null ? (
                          <span className={cn(daysLeft <= 7 ? "text-amber-300" : "text-slate-400")}>
                            剩余 {daysLeft} 天
                          </span>
                        ) : (
                          <span className="text-emerald-300">已结案</span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>阶段分布</CardTitle>
                <CardDescription>帮助识别当前投标池堵点</CardDescription>
              </CardHeader>
              <CardContent className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                {statusDistribution.map((item) => (
                  <div
                    key={item.status}
                    className="rounded-lg border border-slate-800 bg-slate-900/50 p-3 flex items-center justify-between"
                  >
                    <span className="text-sm text-slate-300">{item.label}</span>
                    <Badge className={bidStatusConfig[item.status]?.badgeClass}>{item.count}</Badge>
                  </div>
                ))}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="analytics" className="space-y-4">
            <div className="grid gap-4 lg:grid-cols-[1.2fr,1fr]">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <BarChart3 className="h-5 w-5 text-blue-400" />
                    中标率结构分析
                  </CardTitle>
                  <CardDescription>按概率分层评估投标池质量</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {winRateBuckets.map((bucket) => (
                    <div key={bucket.label} className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-slate-300">{bucket.label}</span>
                        <span className="text-slate-100">{bucket.count} 个</span>
                      </div>
                      <Progress value={bucket.value} className="h-2" />
                    </div>
                  ))}

                  <div className="grid grid-cols-2 gap-3 pt-2">
                    <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-3">
                      <p className="text-xs text-slate-400">投标总额</p>
                      <p className="text-xl font-semibold">{formatBidAmount(overviewStats.totalAmount)}</p>
                    </div>
                    <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-3">
                      <p className="text-xs text-slate-400">预计签约额</p>
                      <p className="text-xl font-semibold text-emerald-300">
                        {formatBidAmount(Math.round(overviewStats.weightedAmount))}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Users className="h-5 w-5 text-cyan-400" />
                    项目赢率排行
                  </CardTitle>
                  <CardDescription>优先聚焦高概率项目的临门一脚</CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  {presaleBids
                    .slice()
                    .sort((a, b) => b.winRate - a.winRate)
                    .map((bid) => (
                      <div
                        key={bid.id}
                        className="rounded-lg border border-slate-800 bg-slate-900/50 p-3 space-y-2"
                      >
                        <div className="flex items-start justify-between gap-2">
                          <div>
                            <p className="text-sm font-medium text-slate-100">{bid.projectName}</p>
                            <p className="text-xs text-slate-400">{bid.customer}</p>
                          </div>
                          {bid.status === "won" ? (
                            <Badge className="bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                              <CheckCircle2 className="mr-1 h-3 w-3" />
                              已中标
                            </Badge>
                          ) : bid.status === "lost" ? (
                            <Badge className="bg-rose-500/20 text-rose-300 border border-rose-500/40">
                              <XCircle className="mr-1 h-3 w-3" />
                              未中标
                            </Badge>
                          ) : (
                            <Badge className="bg-blue-500/20 text-blue-300 border border-blue-500/40">
                              进行中
                            </Badge>
                          )}
                        </div>
                        <div className="flex items-center gap-3">
                          <Progress value={bid.winRate} className="h-2 flex-1" />
                          <span className="text-sm font-medium text-slate-100 min-w-10 text-right">
                            {bid.winRate}%
                          </span>
                        </div>
                      </div>
                    ))}
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
