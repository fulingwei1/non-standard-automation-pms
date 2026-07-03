import { Search } from "lucide-react";
import {
  Card,
  CardContent,
} from "../../components/ui/card";
import { Input } from "../../components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../../components/ui/select";
import { statusConfigs, priorityConfigs } from "./statusConstants";

export default function WorkOrderFilters({
  searchKeyword,
  setSearchKeyword,
  filterProject,
  setFilterProject,
  filterStatus,
  setFilterStatus,
  filterPriority,
  setFilterPriority,
  projects,
}) {
  const clearable = (setter) => (value) => setter(value === "all" ? "" : value);

  return (
    <Card>
      <CardContent className="pt-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
            <Input
              placeholder="搜索工单号、任务名称..."
              value={searchKeyword}
              onChange={(e) => setSearchKeyword(e.target.value)}
              className="pl-10"
            />
          </div>
          <Select value={filterProject || "all"} onValueChange={clearable(setFilterProject)}>
            <SelectTrigger>
              <SelectValue placeholder="选择项目" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">全部项目</SelectItem>
              {(projects || []).map((proj) => (
                <SelectItem key={proj.id} value={proj.id.toString()}>
                  {proj.project_name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={filterStatus || "all"} onValueChange={clearable(setFilterStatus)}>
            <SelectTrigger>
              <SelectValue placeholder="选择状态" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">全部状态</SelectItem>
              {Object.entries(statusConfigs).map(([key, config]) => (
                <SelectItem key={key} value={key || "unknown"}>
                  {config.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={filterPriority || "all"} onValueChange={clearable(setFilterPriority)}>
            <SelectTrigger>
              <SelectValue placeholder="选择优先级" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">全部优先级</SelectItem>
              {Object.entries(priorityConfigs).map(([key, config]) => (
                <SelectItem key={key} value={key || "unknown"}>
                  {config.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </CardContent>
    </Card>
  );
}
