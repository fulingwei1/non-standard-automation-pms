import { RefreshCw } from "lucide-react";
import { Card, CardContent } from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../../components/ui/select";
import { ruleTypeOptions, targetTypeOptions } from "./constants";

export function RuleFilters({
  searchQuery,
  setSearchQuery,
  selectedType,
  setSelectedType,
  selectedTarget,
  setSelectedTarget,
  showEnabled,
  setShowEnabled,
  onRefresh,
}) {
  return (
    <Card className="bg-surface-1/50">
      <CardContent className="p-4">
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex-1 min-w-[200px]">
            <Input
              placeholder="搜索规则编码或名称..."
              value={searchQuery || "unknown"}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="bg-surface-2"
            />
          </div>
          <Select value={selectedType || "unknown"} onValueChange={setSelectedType}>
            <SelectTrigger className="w-[150px] bg-surface-2">
              <SelectValue placeholder="规则类型" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ALL">全部类型</SelectItem>
              {(ruleTypeOptions || []).map((opt) => (
                <SelectItem key={opt.value} value={opt.value}>
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={selectedTarget || "unknown"} onValueChange={setSelectedTarget}>
            <SelectTrigger className="w-[150px] bg-surface-2">
              <SelectValue placeholder="监控对象" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ALL">全部对象</SelectItem>
              {(targetTypeOptions || []).map((opt) => (
                <SelectItem key={opt.value} value={opt.value}>
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select
            value={
              showEnabled === null
                ? "ALL"
                : showEnabled
                  ? "ENABLED"
                  : "DISABLED"
            }
            onValueChange={(val) => {
              if (val === "ALL") {
                setShowEnabled(null);
              } else {
                setShowEnabled(val === "ENABLED");
              }
            }}
          >
            <SelectTrigger className="w-[120px] bg-surface-2">
              <SelectValue placeholder="状态" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ALL">全部状态</SelectItem>
              <SelectItem value="ENABLED">已启用</SelectItem>
              <SelectItem value="DISABLED">已禁用</SelectItem>
            </SelectContent>
          </Select>
          <Button
            variant="outline"
            size="sm"
            onClick={onRefresh}
            className="gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            刷新
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
