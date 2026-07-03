/**
 * VersionComparison — "版本对比" tab content
 */

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../../components/ui";
import { cn, formatCurrency, formatDate } from "../../lib/utils";

/**
 * A single metric summary card used in the comparison grid.
 */
function MetricCard({ title, value, pct, positiveIsGood }) {
  const isPositive = value >= 0;
  const colorClass = (isPositive && positiveIsGood) || (!isPositive && !positiveIsGood)
    ? "text-green-400"
    : "text-red-400";

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium text-slate-400">
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className={cn("text-2xl font-bold", colorClass)}>
          {isPositive ? "+" : ""}
          {typeof value === "number" && Number.isFinite(value)
            ? title.includes("毛利率")
              ? `${value.toFixed(2)}%`
              : formatCurrency(value)
            : "—"}
        </div>
        {pct != null && (
          <div className="text-sm text-slate-400 mt-1">
            {pct?.toFixed(2)}%
          </div>
        )}
      </CardContent>
    </Card>
  );
}

/**
 * Item-diff stats (added / removed / modified line items).
 */
function ItemDiffCards({ itemDiff }) {
  if (!itemDiff) return null;
  return (
    <div className="grid grid-cols-3 gap-4">
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-slate-400">
            新增明细
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-blue-400">
            {itemDiff.added_count || 0}
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-slate-400">
            删除明细
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-orange-400">
            {itemDiff.removed_count || 0}
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-slate-400">
            变更明细
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-purple-400">
            {itemDiff.modified_count || 0}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export function VersionComparison({
  versions,
  selectedVersions,
  setSelectedVersions,
  comparison,
}) {
  const [v1, v2] = selectedVersions;
  const versionList = Array.isArray(versions) ? versions : [];

  const handleV1Change = (value) => {
    const version = versionList.find((v) => v.id.toString() === value);
    setSelectedVersions([version, v2]);
  };

  const handleV2Change = (value) => {
    const version = versionList.find((v) => v.id.toString() === value);
    setSelectedVersions([v1, version]);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>版本对比</CardTitle>
        <CardDescription>对比不同版本的成本变化</CardDescription>
      </CardHeader>
      <CardContent>
        {/* Version selectors */}
        <div className="flex gap-4 mb-6">
          <div className="flex-1">
            <label className="text-sm text-slate-400 mb-2 block">版本1</label>
            <Select
              value={v1?.id?.toString()}
              onValueChange={handleV1Change}
            >
              <SelectTrigger>
                <SelectValue placeholder="选择版本" />
              </SelectTrigger>
              <SelectContent>
                {versionList.map((v) => (
                  <SelectItem key={v.id} value={v.id.toString()}>
                    {v.version_no} - {formatDate(v.created_at)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="flex-1">
            <label className="text-sm text-slate-400 mb-2 block">版本2</label>
            <Select
              value={v2?.id?.toString()}
              onValueChange={handleV2Change}
            >
              <SelectTrigger>
                <SelectValue placeholder="选择版本" />
              </SelectTrigger>
              <SelectContent>
                {versionList.map((v) => (
                  <SelectItem key={v.id} value={v.id.toString()}>
                    {v.version_no} - {formatDate(v.created_at)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Comparison results */}
        {comparison ? (
          <div className="space-y-4">
            {/* Summary metric cards */}
            <div className="grid grid-cols-3 gap-4">
              <MetricCard
                title="总价变化"
                value={comparison.comparison?.price_change}
                pct={comparison.comparison?.price_change_pct}
                positiveIsGood
              />
              <MetricCard
                title="成本变化"
                value={comparison.comparison?.cost_change}
                pct={comparison.comparison?.cost_change_pct}
                positiveIsGood={false}
              />
              <MetricCard
                title="毛利率变化"
                value={comparison.comparison?.margin_change}
                pct={comparison.comparison?.margin_change_pct}
                positiveIsGood
              />
            </div>

            {/* Item-diff summary (new API) */}
            <ItemDiffCards itemDiff={comparison.item_diff} />

            {/* Detailed breakdown table */}
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>成本分类</TableHead>
                  <TableHead>版本1金额</TableHead>
                  <TableHead>版本2金额</TableHead>
                  <TableHead>变化金额</TableHead>
                  <TableHead>变化率</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(comparison.breakdown_comparison || []).map((item, index) => (
                  <TableRow key={index}>
                    <TableCell>{item.category}</TableCell>
                    <TableCell>{formatCurrency(item.v1_amount || 0)}</TableCell>
                    <TableCell>{formatCurrency(item.v2_amount || 0)}</TableCell>
                    <TableCell
                      className={cn(
                        item.change >= 0 ? "text-red-400" : "text-green-400"
                      )}
                    >
                      {item.change >= 0 ? "+" : ""}
                      {formatCurrency(item.change || 0)}
                    </TableCell>
                    <TableCell
                      className={cn(
                        item.change_pct >= 0 ? "text-red-400" : "text-green-400"
                      )}
                    >
                      {item.change_pct >= 0 ? "+" : ""}
                      {item.change_pct?.toFixed(2)}%
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        ) : (
          v1 &&
          v2 && (
            <div className="text-center py-8 text-slate-400">
              加载对比数据中...
            </div>
          )
        )}
      </CardContent>
    </Card>
  );
}
