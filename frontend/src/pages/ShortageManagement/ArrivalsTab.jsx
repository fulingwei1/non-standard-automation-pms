import { useNavigate } from "react-router-dom";


import { cn } from "../../lib/utils";

/**
 * ArrivalsTab
 *
 * Renders the 到货跟踪 (arrival tracking) list with a delay-filter toggle.
 *
 * Props:
 *   arrivals        — array of arrival objects
 *   loading         — boolean
 *   arrivalFilters  — { status: string, is_delayed: boolean }
 *   setArrivalFilters
 */
export function ArrivalsTab({ arrivals, loading, arrivalFilters, setArrivalFilters }) {
  const navigate = useNavigate();

  const toggleDelayed = () => {
    setArrivalFilters((prev) => ({ ...prev, is_delayed: !prev.is_delayed }));
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>到货跟踪</CardTitle>
            <CardDescription>物料到货跟踪记录</CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" onClick={toggleDelayed}>
              <AlertTriangle className="h-4 w-4 mr-2" />
              {arrivalFilters.is_delayed ? "全部" : "延迟预警"}
            </Button>
            <Button onClick={() => navigate("/shortage/arrivals/new")}>
              <Plus className="h-4 w-4 mr-2" />
              新建跟踪
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        {loading ? (
          <div className="text-center py-8 text-muted-foreground">加载中...</div>
        ) : arrivals.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            暂无到货跟踪记录
          </div>
        ) : (
          <div className="space-y-3">
            {arrivals.map((arrival) => (
              <div
                key={arrival.id}
                className={cn(
                  "flex items-center justify-between p-4 rounded-lg border border-border hover:bg-surface-2 transition-colors",
                  arrival.is_delayed && "bg-red-500/5 border-red-500/20"
                )}
              >
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="font-medium">{arrival.arrival_no}</span>
                    {arrival.is_delayed && (
                      <Badge
                        variant="outline"
                        className="bg-red-500/20 text-red-400"
                      >
                        延迟 {arrival.delay_days} 天
                      </Badge>
                    )}
                    <Badge variant="outline">{arrival.status}</Badge>
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {arrival.material_name} | 预期: {arrival.expected_qty} |
                    状态: {arrival.status}
                  </div>
                  <div className="text-xs text-muted-foreground mt-1">
                    供应商: {arrival.supplier_name} | 预期日期:{" "}
                    {arrival.expected_date}
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => navigate(`/shortage/arrivals/${arrival.id}`)}
                >
                  <Eye className="h-4 w-4 mr-2" />
                  查看
                </Button>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
