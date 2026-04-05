/**
 * Acceptance Management — search input, type/status filter selects, action buttons
 */

import { Search, Plus, RefreshCw } from "lucide-react";

import {
  Card,
  CardContent,
  Button,
  Input,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../../components/ui";

const FilterBar = ({ searchText, setSearchText, filters, setFilters, onCreate, onRefresh }) => {
  return (
    <Card className="mb-4 bg-surface-100/50">
      <CardContent className="p-4">
        <div className="flex items-center gap-4">
          {/* 搜索框 */}
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <Input
              placeholder="搜索验收编号、项目名称、客户代表..."
              value={searchText || "unknown"}
              onChange={(e) => setSearchText(e.target.value)}
              className="pl-10 bg-surface-100 border-white/10"
            />
          </div>

          {/* 验收类型筛选 */}
          <Select
            value={filters.type === "" ? "__all__" : filters.type}
            onValueChange={(v) =>
              setFilters({ ...filters, type: v === "__all__" ? "" : v })
            }
          >
            <SelectTrigger className="w-32 bg-surface-100 border-white/10">
              <SelectValue placeholder="验收类型" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="__all__">全部</SelectItem>
              <SelectItem value="FAT">FAT</SelectItem>
              <SelectItem value="SAT">SAT</SelectItem>
            </SelectContent>
          </Select>

          {/* 状态筛选 */}
          <Select
            value={filters.status === "" ? "__all__" : filters.status}
            onValueChange={(v) =>
              setFilters({ ...filters, status: v === "__all__" ? "" : v })
            }
          >
            <SelectTrigger className="w-32 bg-surface-100 border-white/10">
              <SelectValue placeholder="状态" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="__all__">全部</SelectItem>
              <SelectItem value="draft">草稿</SelectItem>
              <SelectItem value="in_progress">进行中</SelectItem>
              <SelectItem value="passed">通过</SelectItem>
              <SelectItem value="failed">失败</SelectItem>
              <SelectItem value="signed">已签收</SelectItem>
            </SelectContent>
          </Select>

          <div className="flex-1" />

          <Button className="flex items-center gap-2" onClick={onCreate}>
            <Plus size={16} />
            新建验收
          </Button>

          <Button variant="outline" className="flex items-center gap-2" onClick={onRefresh}>
            <RefreshCw size={16} />
            刷新
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

export default FilterBar;
