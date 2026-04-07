import { useNavigate } from "react-router-dom";




import { cn } from "../../lib/utils";
import { statusConfigs, urgentLevelConfigs } from "./constants";

/**
 * ReportsTab
 *
 * Renders the 缺料上报 (shortage reports) list with search, status filter,
 * and pagination controls.
 *
 * Props:
 *   reports        — array of report objects
 *   loading        — boolean
 *   searchKeyword  — current search string
 *   setSearchKeyword
 *   statusFilter   — current status filter value
 *   setStatusFilter
 *   page           — current page number
 *   setPage
 *   pageSize       — items per page
 *   total          — total record count
 */
export function ReportsTab({
  reports,
  loading,
  searchKeyword,
  setSearchKeyword,
  statusFilter,
  setStatusFilter,
  page,
  setPage,
  pageSize,
  total,
}) {
  const navigate = useNavigate();

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>缺料上报</CardTitle>
            <CardDescription>车间缺料上报记录</CardDescription>
          </div>
          <div className="flex items-center gap-2">
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="搜索上报单号、物料..."
                className="pl-8 w-64"
                value={searchKeyword || ""}
                onChange={(e) => setSearchKeyword(e.target.value)}
              />
            </div>

            {/* Status filter */}
            <Select
              value={statusFilter || "all"}
              onValueChange={setStatusFilter}
            >
              <SelectTrigger className="w-32">
                <SelectValue placeholder="全部状态" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部状态</SelectItem>
                <SelectItem value="REPORTED">已上报</SelectItem>
                <SelectItem value="CONFIRMED">已确认</SelectItem>
                <SelectItem value="HANDLING">处理中</SelectItem>
                <SelectItem value="RESOLVED">已解决</SelectItem>
              </SelectContent>
            </Select>

            <Button onClick={() => navigate("/shortage/reports/new")}>
              <Plus className="h-4 w-4 mr-2" />
              新建上报
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        {loading ? (
          <div className="text-center py-8 text-muted-foreground">加载中...</div>
        ) : reports.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            暂无缺料上报记录
          </div>
        ) : (
          <div className="space-y-3">
            {reports.map((report) => {
              const urgent =
                urgentLevelConfigs[report.urgent_level] ||
                urgentLevelConfigs.NORMAL;
              const status =
                statusConfigs[report.status] || statusConfigs.REPORTED;
              return (
                <div
                  key={report.id}
                  className="flex items-center justify-between p-4 rounded-lg border border-border hover:bg-surface-2 transition-colors"
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="font-medium">{report.report_no}</span>
                      <Badge variant="outline" className={cn(urgent.color)}>
                        {urgent.label}
                      </Badge>
                      <Badge
                        variant="outline"
                        className={cn(status.color, "text-white")}
                      >
                        {status.label}
                      </Badge>
                    </div>
                    <div className="text-sm text-muted-foreground">
                      {report.project_name} - {report.material_name} | 缺料:{" "}
                      {report.shortage_qty}
                    </div>
                    <div className="text-xs text-muted-foreground mt-1">
                      上报人: {report.reporter_name} |{" "}
                      {new Date(report.report_time).toLocaleString()}
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => navigate(`/shortage/reports/${report.id}`)}
                  >
                    <Eye className="h-4 w-4 mr-2" />
                    查看
                  </Button>
                </div>
              );
            })}
          </div>
        )}

        {/* Pagination */}
        {total > pageSize && (
          <div className="flex items-center justify-between mt-4 pt-4 border-t">
            <div className="text-sm text-muted-foreground">
              共 {total} 条记录，第 {page} / {Math.ceil(total / pageSize)} 页
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1 || loading}
              >
                上一页
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() =>
                  setPage((p) => Math.min(Math.ceil(total / pageSize), p + 1))
                }
                disabled={page >= Math.ceil(total / pageSize) || loading}
              >
                下一页
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
