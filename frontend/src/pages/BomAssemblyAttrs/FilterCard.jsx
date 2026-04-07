/**
 * Filter Card - 筛选条件卡片
 */


import { stageOptions } from "./constants";

export function FilterCard({
  projects,
  boms,
  selectedProject,
  setSelectedProject,
  selectedBom,
  setSelectedBom,
  filterStage,
  setFilterStage,
  filterBlocking,
  setFilterBlocking,
  searchText,
  setSearchText,
}) {
  return (
    <Card>
      <CardContent className="pt-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <Label className="mb-2 block">选择项目</Label>
            <Select
              value={selectedProject || "unknown"}
              onValueChange={(v) => {
                setSelectedProject(v);
                setSelectedBom("");
              }}
            >
              <SelectTrigger>
                <SelectValue placeholder="选择项目" />
              </SelectTrigger>
              <SelectContent>
                {(projects || []).map((proj) => (
                  <SelectItem key={proj.id} value={proj.id.toString()}>
                    {proj.name || proj.project_name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label className="mb-2 block">选择BOM</Label>
            <Select
              value={selectedBom || "unknown"}
              onValueChange={setSelectedBom}
              disabled={!selectedProject}
            >
              <SelectTrigger>
                <SelectValue placeholder="选择BOM" />
              </SelectTrigger>
              <SelectContent>
                {(boms || []).map((bom) => (
                  <SelectItem key={bom.id} value={bom.id.toString()}>
                    {bom.bom_no} - {bom.name || bom.description}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label className="mb-2 block">筛选阶段</Label>
            <Select value={filterStage || "unknown"} onValueChange={setFilterStage}>
              <SelectTrigger>
                <SelectValue placeholder="全部阶段" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部阶段</SelectItem>
                {(stageOptions || []).map((stage) => (
                  <SelectItem key={stage.value} value={stage.value}>
                    {stage.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label className="mb-2 block">筛选类型</Label>
            <Select
              value={filterBlocking || "unknown"}
              onValueChange={setFilterBlocking}
            >
              <SelectTrigger>
                <SelectValue placeholder="全部类型" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部类型</SelectItem>
                <SelectItem value="blocking">仅阻塞性</SelectItem>
                <SelectItem value="postpone">仅可后补</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Search */}
        <div className="mt-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <Input
              placeholder="搜索物料编码或名称..."
              value={searchText || "unknown"}
              onChange={(e) => setSearchText(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
