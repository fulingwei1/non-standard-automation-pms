/**
 * AlertFilterBar - Search and filter controls for alert list
 */



import { fadeIn } from "../../lib/animations";
import {
  ALERT_LEVELS,
  ALERT_STATUS } from
"../../components/alert-center";

export default function AlertFilterBar({
  searchQuery,
  setSearchQuery,
  selectedLevel,
  setSelectedLevel,
  selectedStatus,
  setSelectedStatus,
  selectedProject,
  setSelectedProject,
  dateRange,
  setDateRange,
  sortBy,
  setSortBy,
  projects
}) {
  return (
    <motion.div variants={fadeIn} initial="hidden" animate="visible">
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <Input
                  placeholder="搜索预警标题、描述、项目..."
                  value={searchQuery || "unknown"}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10 bg-slate-800/50 border-slate-700" />

              </div>
            </div>
            <div className="flex gap-2 flex-wrap">
              <select
                value={selectedLevel || "unknown"}
                onChange={(e) => setSelectedLevel(e.target.value)}
                className="px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-sm text-white">

                <option value="ALL">全部级别</option>
                {Object.entries(ALERT_LEVELS).map(([key, config]) =>
                <option key={key} value={key || "unknown"}>
                    {config.label}
                </option>
                )}
              </select>
              <select
                value={selectedStatus || "unknown"}
                onChange={(e) => setSelectedStatus(e.target.value)}
                className="px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-sm text-white">

                <option value="ALL">全部状态</option>
                {Object.entries(ALERT_STATUS).map(([key, config]) =>
                <option key={key} value={key || "unknown"}>
                    {config.label}
                </option>
                )}
              </select>
              <select
                value={selectedProject || "unknown"}
                onChange={(e) => setSelectedProject(e.target.value)}
                className="px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-sm text-white">

                <option value="ALL">全部项目</option>
                {(projects || []).map((project) =>
                <option key={project.id} value={project.id}>
                    {project.name}
                </option>
                )}
              </select>
              <Input
                type="date"
                value={dateRange.start}
                onChange={(e) => setDateRange((prev) => ({ ...prev, start: e.target.value }))}
                className="w-40"
                placeholder="开始日期" />

              <Input
                type="date"
                value={dateRange.end}
                onChange={(e) => setDateRange((prev) => ({ ...prev, end: e.target.value }))}
                className="w-40"
                placeholder="结束日期" />

              <Button
                variant="outline"
                onClick={() => setSortBy((prev) => prev === sortBy ? 'triggered_at' : prev)}>

                <ArrowUpDown className="h-4 w-4 mr-2" />
                {sortBy === 'triggered_at' ? '默认排序' : '按时间排序'}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
