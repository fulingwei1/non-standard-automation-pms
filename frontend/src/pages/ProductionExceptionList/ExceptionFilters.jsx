/**
 * ExceptionFilters — search bar + four Select filter controls
 */
import { Search } from "lucide-react";
import { Input } from "../../components/ui/input";
import {
  Card,
  CardContent,
} from "../../components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../../components/ui/select";
import { typeConfigs, levelConfigs, statusConfigs } from "./constants";

export function ExceptionFilters({
  projects,
  searchKeyword,
  setSearchKeyword,
  filterProject,
  setFilterProject,
  filterType,
  setFilterType,
  filterLevel,
  setFilterLevel,
  filterStatus,
  setFilterStatus,
}) {
  return (
    <Card>
      <CardContent className="pt-6">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          {/* Keyword search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
            <Input
              placeholder="搜索异常编号、标题..."
              value={searchKeyword || "unknown"}
              onChange={(e) => setSearchKeyword(e.target.value)}
              className="pl-10"
            />
          </div>

          {/* Project filter */}
          <Select value={filterProject || "unknown"} onValueChange={setFilterProject}>
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

          {/* Type filter */}
          <Select value={filterType || "unknown"} onValueChange={setFilterType}>
            <SelectTrigger>
              <SelectValue placeholder="选择类型" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">全部类型</SelectItem>
              {Object.entries(typeConfigs).map(([key, config]) => (
                <SelectItem key={key} value={key || "unknown"}>
                  {config.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          {/* Level filter */}
          <Select value={filterLevel || "unknown"} onValueChange={setFilterLevel}>
            <SelectTrigger>
              <SelectValue placeholder="选择级别" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">全部级别</SelectItem>
              {Object.entries(levelConfigs).map(([key, config]) => (
                <SelectItem key={key} value={key || "unknown"}>
                  {config.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          {/* Status filter */}
          <Select value={filterStatus || "unknown"} onValueChange={setFilterStatus}>
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
        </div>
      </CardContent>
    </Card>
  );
}
