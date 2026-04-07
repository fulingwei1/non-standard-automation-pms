

import { statusConfigs, levelConfigs } from "./constants";

export default function AlertFilters({
  searchKeyword,
  setSearchKeyword,
  filterProject,
  setFilterProject,
  filterStatus,
  setFilterStatus,
  filterLevel,
  setFilterLevel,
  projects,
}) {
  return (
    <Card className="bg-slate-800/50 border-slate-700/50">
      <CardContent className="pt-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
            <Input
              placeholder="搜索物料编码、名称..."
              value={searchKeyword || ""}
              onChange={(e) => setSearchKeyword(e.target.value)}
              className="pl-10 bg-slate-900/50 border-slate-700 text-slate-200"
            />
          </div>

          {/* Project filter */}
          <Select value={filterProject || "all"} onValueChange={setFilterProject}>
            <SelectTrigger className="bg-slate-900/50 border-slate-700">
              <SelectValue placeholder="选择项目" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">全部项目</SelectItem>
              {(projects || []).map((proj) => {
                const projId = proj.id?.toString();
                if (!projId) return null;
                return (
                  <SelectItem key={proj.id} value={projId}>
                    {proj.project_name}
                  </SelectItem>
                );
              })}
            </SelectContent>
          </Select>

          {/* Status filter */}
          <Select value={filterStatus || "all"} onValueChange={setFilterStatus}>
            <SelectTrigger className="bg-slate-900/50 border-slate-700">
              <SelectValue placeholder="选择状态" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">全部状态</SelectItem>
              {Object.entries(statusConfigs)
                .filter(([key]) => key && key !== "")
                .map(([key, config]) => (
                  <SelectItem key={key} value={key}>
                    {config.label}
                  </SelectItem>
                ))}
            </SelectContent>
          </Select>

          {/* Level filter */}
          <Select value={filterLevel || "all"} onValueChange={setFilterLevel}>
            <SelectTrigger className="bg-slate-900/50 border-slate-700">
              <SelectValue placeholder="选择预警级别" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">全部级别</SelectItem>
              {Object.entries(levelConfigs).map(([key, config]) => (
                <SelectItem key={key} value={key}>
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
