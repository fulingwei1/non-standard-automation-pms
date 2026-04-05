import { Search } from "lucide-react";
import { Card, CardContent } from "../../components/ui/card";
import { Input } from "../../components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../../components/ui/select";
import { statusConfigs, typeConfigs } from "./constants";

export default function PlanFilters({
  searchKeyword,
  setSearchKeyword,
  filterType,
  setFilterType,
  filterProject,
  setFilterProject,
  filterWorkshop,
  setFilterWorkshop,
  filterStatus,
  setFilterStatus,
  projects,
  workshops,
}) {
  return (
    <Card>
      <CardContent className="pt-6">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
            <Input
              placeholder="搜索计划编号、名称..."
              value={searchKeyword || "unknown"}
              onChange={(e) => setSearchKeyword(e.target.value)}
              className="pl-10"
            />
          </div>

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

          {/* Workshop filter */}
          <Select value={filterWorkshop || "unknown"} onValueChange={setFilterWorkshop}>
            <SelectTrigger>
              <SelectValue placeholder="选择车间" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">全部车间</SelectItem>
              {(workshops || []).map((ws) => (
                <SelectItem key={ws.id} value={ws.id.toString()}>
                  {ws.workshop_name}
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
