/**
 * ECN List Header Component
 * ECN列表头部组件
 */
import { useState } from "react";
import { Plus, Search, Filter, RefreshCw, Download } from "lucide-react";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../ui/select";

export function ECNListHeader({
  searchKeyword,
  onSearchChange,
  filterProject,
  onProjectChange,
  filterType,
  onTypeChange,
  filterStatus,
  onStatusChange,
  filterPriority,
  onPriorityChange,
  projects,
  filterOptions,
  onCreateECN,
  onRefresh,
  exporting,
  onExport,
}) {
  const [showFilters, setShowFilters] = useState(false);

  return (
    <div className="space-y-4">
      {/* 搜索和操作栏 */}
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div className="flex flex-col sm:flex-row gap-3 flex-1 w-full sm:w-auto">
          {/* 搜索框 */}
          <div className="relative flex-1 sm:flex-initial">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <Input
              placeholder="搜索ECN编号、标题、申请人..."
              value={searchKeyword || "unknown"}
              onChange={(e) => onSearchChange(e.target.value)}
              className="pl-10 w-full sm:w-80"
            />
          </div>

          {/* 筛选按钮 */}
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center gap-2"
          >
            <Filter className="w-4 h-4" />
            筛选
            {(filterProject || filterType || filterStatus || filterPriority) && (
              <span className="w-2 h-2 bg-blue-500 rounded-full" />
            )}
          </Button>
        </div>

        {/* 操作按钮 */}
        <div className="flex gap-2 w-full sm:w-auto">
          <Button
            variant="outline"
            size="sm"
            onClick={onRefresh}
            disabled={exporting}
            className="flex items-center gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            刷新
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={onExport}
            disabled={exporting}
            className="flex items-center gap-2"
          >
            <Download className="w-4 h-4" />
            {exporting ? "导出中..." : "导出"}
          </Button>

          <Button
            size="sm"
            onClick={onCreateECN}
            className="flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            创建ECN
          </Button>
        </div>
      </div>

      {/* 筛选条件 */}
      {showFilters && (
        <div className="bg-slate-50 dark:bg-slate-800 p-4 rounded-lg border">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* 项目筛选 */}
            <div>
              <label className="text-sm font-medium mb-2 block">项目</label>
              <Select
                value={filterProject || "all"}
                onValueChange={(value) =>
                  onProjectChange(value === "all" ? "" : value)
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="选择项目" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">所有项目</SelectItem>
                  {projects?.map((project) => (
                    <SelectItem key={project.id} value={project.id.toString()}>
                      {project.project_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* 类型筛选 */}
            <div>
              <label className="text-sm font-medium mb-2 block">类型</label>
              <Select
                value={filterType || "all"}
                onValueChange={(value) =>
                  onTypeChange(value === "all" ? "" : value)
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="选择类型" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">所有类型</SelectItem>
                  {(filterOptions.types || []).map((type) => (
                    <SelectItem key={type.value} value={type.value}>
                      {type.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* 状态筛选 */}
            <div>
              <label className="text-sm font-medium mb-2 block">状态</label>
              <Select
                value={filterStatus || "all"}
                onValueChange={(value) =>
                  onStatusChange(value === "all" ? "" : value)
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="选择状态" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">所有状态</SelectItem>
                  {(filterOptions.statuses || []).map((status) => (
                    <SelectItem key={status.value} value={status.value}>
                      {status.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* 优先级筛选 */}
            <div>
              <label className="text-sm font-medium mb-2 block">优先级</label>
              <Select
                value={filterPriority || "all"}
                onValueChange={(value) =>
                  onPriorityChange(value === "all" ? "" : value)
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="选择优先级" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">所有优先级</SelectItem>
                  {(filterOptions.priorities || []).map((priority) => (
                    <SelectItem key={priority.value} value={priority.value}>
                      {priority.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* 清除筛选 */}
          <div className="mt-4 flex justify-end">
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                onProjectChange("");
                onTypeChange("");
                onStatusChange("");
                onPriorityChange("");
                onSearchChange("");
              }}
            >
              清除所有筛选
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}