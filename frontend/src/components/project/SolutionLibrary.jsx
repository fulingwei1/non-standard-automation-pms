import { useState, useEffect } from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Badge,
  Button,
  Input } from
"../ui";
import { BookOpen, Search, Plus, Star, Copy } from "lucide-react";
import { formatDate as _formatDate } from "../../lib/utils";
import { projectWorkspaceApi as _projectWorkspaceApi } from "../../services/api";

export default function SolutionLibrary({ projectId, onApplyTemplate }) {
  const [loading, setLoading] = useState(true);
  const [templates, setTemplates] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [filterType, setFilterType] = useState("all");

  useEffect(() => {
    fetchTemplates();
  }, [projectId]);

  const fetchTemplates = async () => {
    try {
      setLoading(true);
      // TODO: 实现解决方案模板API
      // const response = await solutionTemplateApi.list({ project_id: projectId })
      // setTemplates(response.data)
      setTemplates([]);
    } catch (error) {
      console.error("Failed to load solution templates:", error);
    } finally {
      setLoading(false);
    }
  };

  const filteredTemplates = templates.filter((template) => {
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      if (
      !template.template_name.toLowerCase().includes(query) &&
      !template.solution.toLowerCase().includes(query))
      {
        return false;
      }
    }
    if (filterType !== "all" && template.issue_type !== filterType) {
      return false;
    }
    return true;
  });

  if (loading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="text-center text-gray-500">加载中...</div>
        </CardContent>
      </Card>);

  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <BookOpen className="h-5 w-5" />
            解决方案模板库
          </CardTitle>
          <Button size="sm">
            <Plus className="h-4 w-4 mr-2" />
            创建模板
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {/* 搜索和筛选 */}
        <div className="flex items-center gap-4 mb-6">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              placeholder="搜索解决方案模板..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9" />

          </div>
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="h-9 px-3 rounded-lg border border-gray-300 text-sm">

            <option value="all">全部类型</option>
            <option value="DEFECT">缺陷</option>
            <option value="DEVIATION">偏差</option>
            <option value="RISK">风险</option>
            <option value="BLOCKER">阻塞</option>
          </select>
        </div>

        {/* 模板列表 */}
        {filteredTemplates.length > 0 ?
        <div className="space-y-3">
            {filteredTemplates.map((template) =>
          <div
            key={template.id}
            className="p-4 border rounded-lg hover:bg-gray-50 transition-colors">

                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <p className="font-medium">{template.template_name}</p>
                      <Badge variant="outline">{template.issue_type}</Badge>
                      {template.category &&
                  <Badge variant="secondary">{template.category}</Badge>
                  }
                    </div>
                    {template.applicable_scenarios &&
                <p className="text-sm text-gray-600 mb-2">
                        {template.applicable_scenarios}
                      </p>
                }
                    <div className="p-3 bg-gray-50 rounded text-sm">
                      {template.solution.substring(0, 300)}
                      {template.solution.length > 300 && "..."}
                    </div>
                  </div>
                </div>
                <div className="flex items-center justify-between mt-3">
                  <div className="flex items-center gap-4 text-sm text-gray-500">
                    {template.usage_count > 0 &&
                <span>使用 {template.usage_count} 次</span>
                }
                    {template.success_rate &&
                <span>成功率 {template.success_rate}%</span>
                }
                    {template.avg_resolution_time &&
                <span>平均 {template.avg_resolution_time}h</span>
                }
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                  variant="outline"
                  size="sm"
                  onClick={() =>
                  onApplyTemplate && onApplyTemplate(template)
                  }>

                      <Copy className="h-4 w-4 mr-1" />
                      应用模板
                    </Button>
                  </div>
                </div>
              </div>
          )}
          </div> :

        <div className="text-center py-12 text-gray-500">
            {searchQuery || filterType !== "all" ?
          "没有找到匹配的模板" :
          "暂无解决方案模板"}
          </div>
        }
      </CardContent>
    </Card>);

}