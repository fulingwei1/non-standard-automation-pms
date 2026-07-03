
import { Search } from "lucide-react";
import { Input } from "../ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../ui/select";
import {
  DISPATCH_FILTER_OPTIONS,
  PRIORITY_FILTER_OPTIONS,
  INSTALLATION_TYPE,
  INSTALLATION_TYPE_LABELS,
} from "@/lib/constants/installationDispatch";

export default function DispatchFilters({
  searchQuery,
  setSearchQuery,
  filterStatus,
  setFilterStatus,
  filterPriority,
  setFilterPriority,
  filterProject,
  setFilterProject,
  filterTaskType,
  setFilterTaskType,
  projects = [],
}) {
  const handleAllValue = (setter) => (value) => setter(value === "all" ? "" : value);

  return (
    <div className="flex flex-col md:flex-row gap-4 mb-4">
      <div className="flex-1">
        <div className="relative">
          <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="搜索派工单..."
            value={searchQuery || ""}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
        <Select value={filterStatus || "all"} onValueChange={handleAllValue(setFilterStatus)}>
          <SelectTrigger>
            <SelectValue placeholder="状态" />
          </SelectTrigger>
          <SelectContent>
            {DISPATCH_FILTER_OPTIONS.map((option) => (
              <SelectItem key={option.value} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={filterPriority || "all"} onValueChange={handleAllValue(setFilterPriority)}>
          <SelectTrigger>
            <SelectValue placeholder="优先级" />
          </SelectTrigger>
          <SelectContent>
            {PRIORITY_FILTER_OPTIONS.map((option) => (
              <SelectItem key={option.value} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={filterProject ? String(filterProject) : "all"} onValueChange={handleAllValue(setFilterProject)}>
          <SelectTrigger>
            <SelectValue placeholder="项目" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">全部项目</SelectItem>
            {(projects || []).map((project) => (
              <SelectItem key={project.id} value={String(project.id)}>
                {project.project_name || project.name || project.project_code}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={filterTaskType || "all"} onValueChange={handleAllValue(setFilterTaskType)}>
          <SelectTrigger>
            <SelectValue placeholder="任务类型" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">全部类型</SelectItem>
            {Object.entries(INSTALLATION_TYPE).map(([_key, value]) => (
              <SelectItem key={value} value={value}>
                {INSTALLATION_TYPE_LABELS[value]}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
    </div>
  );
}
