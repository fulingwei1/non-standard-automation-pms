



import {
  MATERIAL_STATUS,
  getMaterialStatusColor,
  getMaterialStatusLabel,
  getMaterialTypeLabel,
} from "../../components/material-readiness";
import { getReadinessBadge, getTypeIcon } from "./BadgeHelpers";

export default function OverviewPanel({
  stats,
  urgentMaterials,
  arrivingMaterials,
  typeDistribution,
  onQuickAction,
}) {
  return (
    <div className="space-y-6">
      {/* 关键指标 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">总物料数</CardTitle>
            <Package className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total}</div>
            <p className="text-xs text-muted-foreground">
              可用: {stats.available}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">齐套率</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {stats.readinessRate}%
            </div>
            <div className="text-xs text-muted-foreground">
              {getReadinessBadge(stats.readinessStatus)}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">缺料</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {stats.outOfStock}
            </div>
            <p className="text-xs text-muted-foreground">
              关键缺料: {stats.criticalShortages}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">在途物料</CardTitle>
            <Truck className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">
              {stats.onOrder}
            </div>
            <p className="text-xs text-muted-foreground">
              即将到货: {arrivingMaterials.length}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* 状态分布 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>物料状态分布</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(MATERIAL_STATUS).map(([key, value]) => {
                const count = stats[key.toLowerCase()] || 0;
                const percentage =
                  stats.total > 0
                    ? ((count / stats.total) * 100).toFixed(1)
                    : 0;

                return (
                  <div
                    key={value}
                    className="flex items-center justify-between"
                  >
                    <div className="flex items-center space-x-2">
                      <div
                        className="w-3 h-3 rounded-full"
                        style={{
                          backgroundColor: getMaterialStatusColor(value),
                        }}
                      />
                      <span className="text-sm">
                        {getMaterialStatusLabel(value)}
                      </span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Badge variant="secondary">{count}</Badge>
                      <span className="text-xs text-muted-foreground">
                        {percentage}%
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>紧急提醒</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-red-50 rounded-lg">
                <div className="flex items-center space-x-2">
                  <AlertTriangle className="h-4 w-4 text-red-600" />
                  <span className="text-sm font-medium">关键缺料</span>
                </div>
                <Badge variant="destructive">{stats.criticalShortages}</Badge>
              </div>

              <div className="flex items-center justify-between p-3 bg-orange-50 rounded-lg">
                <div className="flex items-center space-x-2">
                  <Clock className="h-4 w-4 text-orange-600" />
                  <span className="text-sm font-medium">紧急物料</span>
                </div>
                <Badge variant="secondary">{urgentMaterials.length}</Badge>
              </div>

              <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                <div className="flex items-center space-x-2">
                  <Truck className="h-4 w-4 text-blue-600" />
                  <span className="text-sm font-medium">即将到货</span>
                </div>
                <Badge variant="outline">{arrivingMaterials.length}</Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 类型分布 */}
      <Card>
        <CardHeader>
          <CardTitle>物料类型分布</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(typeDistribution).map(([type, count]) => {
              if (count === 0) {
                return null;
              }
              const percentage =
                stats.total > 0
                  ? ((count / stats.total) * 100).toFixed(1)
                  : 0;

              return (
                <div key={type} className="text-center p-4 border rounded-lg">
                  <div className="flex justify-center mb-2">
                    {getTypeIcon(type)}
                  </div>
                  <p className="text-sm font-medium">
                    {getMaterialTypeLabel(type)}
                  </p>
                  <p className="text-2xl font-bold">{count}</p>
                  <p className="text-xs text-muted-foreground">{percentage}%</p>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* 快速操作 */}
      <Card>
        <CardHeader>
          <CardTitle>快速操作</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Button
              variant="outline"
              className="h-auto p-4 flex flex-col items-center space-y-2"
              onClick={() => onQuickAction("createMaterial")}
            >
              <Plus className="h-6 w-6" />
              <span className="text-sm">新建物料</span>
            </Button>

            <Button
              variant="outline"
              className="h-auto p-4 flex flex-col items-center space-y-2"
              onClick={() => onQuickAction("criticalShortages")}
            >
              <AlertTriangle className="h-6 w-6" />
              <span className="text-sm">关键缺料</span>
            </Button>

            <Button
              variant="outline"
              className="h-auto p-4 flex flex-col items-center space-y-2"
              onClick={() => onQuickAction("materialRequest")}
            >
              <Truck className="h-6 w-6" />
              <span className="text-sm">物料申请</span>
            </Button>

            <Button
              variant="outline"
              className="h-auto p-4 flex flex-col items-center space-y-2"
              onClick={() => onQuickAction("readinessAnalysis")}
            >
              <BarChart3 className="h-6 w-6" />
              <span className="text-sm">齐套分析</span>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
