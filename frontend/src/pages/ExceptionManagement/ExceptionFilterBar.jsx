

import { statusConfigs, severityConfigs, typeConfigs } from "./constants";

/**
 * ExceptionFilterBar
 * Renders the search input and four filter dropdowns for the exception list.
 */
export function ExceptionFilterBar({
  searchKeyword,
  setSearchKeyword,
  filterProject,
  setFilterProject,
  filterType,
  setFilterType,
  filterSeverity,
  setFilterSeverity,
  filterStatus,
  setFilterStatus,
  projects,
}) {
  return (
    <Card>
      <CardContent className="pt-6">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
            <Input
              placeholder="搜索异常编号、标题..."
              value={searchKeyword || ""}
              onChange={(e) => setSearchKeyword(e.target.value)}
              className="pl-10"
            />
          </div>

          {/* Project filter */}
          <Select
            value={filterProject || "unknown"}
            onValueChange={setFilterProject}
          >
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
          <Select
            value={filterType || "unknown"}
            onValueChange={setFilterType}
          >
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

          {/* Severity filter */}
          <Select
            value={filterSeverity || "unknown"}
            onValueChange={setFilterSeverity}
          >
            <SelectTrigger>
              <SelectValue placeholder="选择严重程度" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">全部</SelectItem>
              {Object.entries(severityConfigs).map(([key, config]) => (
                <SelectItem key={key} value={key || "unknown"}>
                  {config.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          {/* Status filter */}
          <Select
            value={filterStatus || "unknown"}
            onValueChange={setFilterStatus}
          >
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
