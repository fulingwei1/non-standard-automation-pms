import {
  Search,
  RefreshCw,
  CheckCircle2,
  CalendarClock,
  Coins,
  Layers,
  MessageSquareText,
  FileText,
  ClipboardCheck,
} from "lucide-react";
import { motion } from "framer-motion";
import {
  Badge,
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Input,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../../components/ui";
import { STATUS_CONFIG } from "./constants";
import { formatDate, formatWan, getStatusConfig } from "./utils";

export default function SolutionListTab({
  stats,
  searchKeyword,
  setSearchKeyword,
  statusFilter,
  setStatusFilter,
  loading,
  solutions,
  onViewSolution,
  onCreateQuote,
  setSelectedSolutionId,
  setActiveTab,
  onSubmitReview,
  reviewActionLoadingId,
}) {
  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[
          { label: "总方案数", value: stats.total, icon: Layers, color: "text-slate-100" },
          { label: "草稿", value: stats.draft, icon: FileText, color: "text-slate-300" },
          { label: "评审中", value: stats.reviewing, icon: ClipboardCheck, color: "text-amber-300" },
          { label: "已通过", value: stats.approved, icon: CheckCircle2, color: "text-emerald-300" },
        ].map((item) => (
          <Card key={item.label} className="border-white/10 bg-white/5 backdrop-blur">
            <CardContent className="pt-5">
              <div className="mb-2 flex items-center justify-between">
                <p className="text-xs text-slate-400">{item.label}</p>
                <item.icon className={`h-4 w-4 ${item.color}`} />
              </div>
              <p className={`text-3xl font-semibold ${item.color}`}>{item.value}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card className="border-white/10 bg-white/5 backdrop-blur">
        <CardContent className="pt-6">
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div className="relative w-full md:max-w-md">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
              <Input
                className="pl-9"
                placeholder="搜索方案名称 / 编号"
                value={searchKeyword}
                onChange={(event) => setSearchKeyword(event.target.value)}
              />
            </div>

            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-full md:w-[200px]">
                <SelectValue placeholder="筛选状态" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部状态</SelectItem>
                {Object.entries(STATUS_CONFIG).map(([key, config]) => (
                  <SelectItem key={key} value={key}>
                    {config.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {loading ? (
        <div className="rounded-xl border border-white/10 bg-white/5 py-14 text-center text-slate-300">
          <RefreshCw className="mx-auto mb-3 h-6 w-6 animate-spin" />
          正在加载方案列表...
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {solutions.length > 0 ? (
            solutions.map((solution) => {
              const statusConfig = getStatusConfig(solution.status);
              const canCreateQuote = solution.status === "APPROVED" && onCreateQuote;
              const canSubmitReview = ["DRAFT", "REJECTED"].includes(solution.status) && onSubmitReview;
              return (
                <motion.div
                  key={solution.id}
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.2 }}
                >
                  <Card className="h-full border-white/10 bg-slate-900/70 transition-colors hover:border-cyan-400/50 hover:bg-slate-900">
                    <CardHeader>
                      <div className="mb-2 flex items-center justify-between gap-3">
                        <Badge className={statusConfig.className}>{statusConfig.label}</Badge>
                        <Badge variant="outline" className="border-white/20 text-slate-200">
                          {solution.version}
                        </Badge>
                      </div>
                      <CardTitle className="line-clamp-2 text-base">{solution.name}</CardTitle>
                      <CardDescription className="text-xs text-slate-400">
                        {solution.solutionNo} · {solution.industry}
                      </CardDescription>
                    </CardHeader>

                    <CardContent className="space-y-4">
                      <p className="line-clamp-3 text-sm text-slate-300">{solution.requirementSummary}</p>

                      <div className="grid grid-cols-2 gap-2 text-xs text-slate-400">
                        <div className="rounded-lg border border-white/10 bg-white/5 p-2">
                          <div className="mb-1 flex items-center gap-1">
                            <Coins className="h-3.5 w-3.5" />
                            预估成本
                          </div>
                          <div className="text-sm font-medium text-slate-100">
                            {formatWan(solution.estimatedCost)} 万
                          </div>
                        </div>
                        <div className="rounded-lg border border-white/10 bg-white/5 p-2">
                          <div className="mb-1 flex items-center gap-1">
                            <MessageSquareText className="h-3.5 w-3.5" />
                            建议报价
                          </div>
                          <div className="text-sm font-medium text-cyan-200">
                            {formatWan(solution.suggestedPrice)} 万
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center justify-between text-xs text-slate-400">
                        <span className="inline-flex items-center gap-1">
                          <CalendarClock className="h-3.5 w-3.5" />
                          {formatDate(solution.updatedAt || solution.createdAt)}
                        </span>
                        <span>{solution.testType}</span>
                      </div>

                      <div className="flex flex-wrap gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          className="min-w-[96px] flex-1"
                          onClick={() => onViewSolution(solution)}
                        >
                          查看详情
                        </Button>
                        {canCreateQuote && (
                          <Button
                            size="sm"
                            className="min-w-[96px] flex-1"
                            onClick={() => onCreateQuote(solution)}
                          >
                            <FileText className="h-3.5 w-3.5" />
                            生成报价
                          </Button>
                        )}
                        {canSubmitReview && (
                          <Button
                            size="sm"
                            variant="secondary"
                            className="min-w-[96px] flex-1"
                            disabled={reviewActionLoadingId === solution.id}
                            onClick={() => onSubmitReview(solution)}
                          >
                            <ClipboardCheck className="h-3.5 w-3.5" />
                            提交评审
                          </Button>
                        )}
                        <Button
                          size="sm"
                          className="min-w-[96px] flex-1"
                          onClick={() => {
                            setSelectedSolutionId(String(solution.id));
                            setActiveTab("versions");
                          }}
                        >
                          版本管理
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              );
            })
          ) : (
            <div className="col-span-full rounded-xl border border-dashed border-white/20 py-16 text-center text-slate-400">
              暂无符合条件的方案，尝试调整筛选条件
            </div>
          )}
        </div>
      )}
    </div>
  );
}
