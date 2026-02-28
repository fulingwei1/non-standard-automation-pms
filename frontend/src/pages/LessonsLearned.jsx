import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { lessonsApi } from "../services/api/lessons";
import { PageHeader } from "../components/layout/PageHeader";
import { staggerContainer, fadeIn } from "../lib/animations";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "../components/ui/dialog";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import { Badge } from "../components/ui/badge";
import {
  BookOpen,
  Search,
  Plus,
  Filter,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  Lightbulb,
  BarChart3,
  X,
} from "lucide-react";

// 分类颜色配置
const categoryColors = {
  technical: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  management: "bg-purple-500/20 text-purple-400 border-purple-500/30",
  quality: "bg-green-500/20 text-green-400 border-green-500/30",
  cost: "bg-red-500/20 text-red-400 border-red-500/30",
  schedule: "bg-amber-500/20 text-amber-400 border-amber-500/30",
  customer: "bg-cyan-500/20 text-cyan-400 border-cyan-500/30",
};

const categoryLabels = {
  technical: "技术",
  management: "管理",
  quality: "质量",
  cost: "成本",
  schedule: "进度",
  customer: "客户",
};

// 类型图标配置
const typeIcons = {
  success: CheckCircle,
  failure: AlertTriangle,
  improvement: TrendingUp,
};

const typeLabels = {
  success: "成功经验",
  failure: "失败教训",
  improvement: "改进建议",
};

const typeColors = {
  success: "text-green-400",
  failure: "text-red-400",
  improvement: "text-blue-400",
};

// 影响程度配置
const impactConfig = {
  high: { label: "高", color: "bg-red-500" },
  medium: { label: "中", color: "bg-amber-500" },
  low: { label: "低", color: "bg-green-500" },
};

const categoryOptions = [
  { value: "", label: "全部分类" },
  { value: "technical", label: "技术" },
  { value: "management", label: "管理" },
  { value: "quality", label: "质量" },
  { value: "cost", label: "成本" },
  { value: "schedule", label: "进度" },
  { value: "customer", label: "客户" },
];

const lessonTypeOptions = [
  { value: "", label: "全部类型" },
  { value: "success", label: "成功经验" },
  { value: "failure", label: "失败教训" },
  { value: "improvement", label: "改进建议" },
];

const impactOptions = [
  { value: "", label: "全部影响" },
  { value: "high", label: "高" },
  { value: "medium", label: "中" },
  { value: "low", label: "低" },
];

export default function LessonsLearned() {
  const [loading, setLoading] = useState(true);
  const [lessons, setLessons] = useState([]);
  const [stats, setStats] = useState(null);
  const [total, setTotal] = useState(0);
  const [searchKeyword, setSearchKeyword] = useState("");
  const [category, setCategory] = useState("");
  const [lessonType, setLessonType] = useState("");
  const [impactLevel, setImpactLevel] = useState("");
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [editingLesson, setEditingLesson] = useState(null);
  const [formData, setFormData] = useState({
    project_id: "",
    title: "",
    category: "",
    lesson_type: "",
    description: "",
    root_cause: "",
    action_taken: "",
    recommendation: "",
    impact_level: "",
    applicable_to: "",
    tags: "",
  });

  useEffect(() => {
    fetchLessons();
    fetchStats();
  }, [category, lessonType, impactLevel]);

  const fetchLessons = async () => {
    try {
      setLoading(true);
      const params = {
        category: category || undefined,
        lesson_type: lessonType || undefined,
        keyword: searchKeyword || undefined,
      };
      const response = await lessonsApi.list(params);
      setLessons(response.data.items || []);
      setTotal(response.data.total || 0);
    } catch (error) {
      console.error("Failed to load lessons:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await lessonsApi.stats();
      setStats(response.data);
    } catch (error) {
      console.error("Failed to load stats:", error);
    }
  };

  const handleSearch = () => {
    fetchLessons();
  };

  const handleReset = () => {
    setSearchKeyword("");
    setCategory("");
    setLessonType("");
    setImpactLevel("");
  };

  const handleCreate = () => {
    setFormData({
      project_id: "",
      title: "",
      category: "",
      lesson_type: "",
      description: "",
      root_cause: "",
      action_taken: "",
      recommendation: "",
      impact_level: "",
      applicable_to: "",
      tags: "",
    });
    setShowCreateDialog(true);
  };

  const handleEdit = (lesson) => {
    setFormData({
      project_id: lesson.project_id || "",
      title: lesson.title || "",
      category: lesson.category || "",
      lesson_type: lesson.lesson_type || "",
      description: lesson.description || "",
      root_cause: lesson.root_cause || "",
      action_taken: lesson.action_taken || "",
      recommendation: lesson.recommendation || "",
      impact_level: lesson.impact_level || "",
      applicable_to: lesson.applicable_to || "",
      tags: lesson.tags || "",
    });
    setEditingLesson(lesson);
    setShowEditDialog(true);
  };

  const handleSubmit = async () => {
    try {
      if (editingLesson) {
        await lessonsApi.update(editingLesson.id, formData);
      } else {
        await lessonsApi.create(formData);
      }
      setShowCreateDialog(false);
      setShowEditDialog(false);
      fetchLessons();
      fetchStats();
    } catch (error) {
      console.error("Failed to save lesson:", error);
      alert("保存失败，请重试");
    }
  };

  const handleInputChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  return (
    <div className="p-6 space-y-6 bg-gray-950 min-h-screen">
      <PageHeader
        title="经验教训库"
        description="项目复盘经验教训管理与知识沉淀"
        icon={BookOpen}
      />

      {loading && !lessons.length ? (
        <div className="flex items-center justify-center py-20">
          <div className="text-gray-400">加载中...</div>
        </div>
      ) : (
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className="space-y-6"
        >
          {/* 统计概览 */}
          {stats && (
            <motion.div variants={fadeIn} className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <Card className="bg-gray-900/50 border-gray-800">
                <CardContent className="p-4">
                  <p className="text-sm text-gray-400">总数</p>
                  <p className="text-2xl font-bold text-white">{stats.total || 0}</p>
                </CardContent>
              </Card>
              {(stats.by_category || []).slice(0, 4).map((cat) => (
                <Card key={cat.category} className="bg-gray-900/50 border-gray-800">
                  <CardContent className="p-4">
                    <p className="text-sm text-gray-400">{categoryLabels[cat.category] || cat.category}</p>
                    <p className="text-2xl font-bold text-white">{cat.count}</p>
                  </CardContent>
                </Card>
              ))}
            </motion.div>
          )}

          {/* 筛选工具栏 */}
          <Card className="bg-gray-900/50 border-gray-800">
            <CardContent className="p-4">
              <div className="flex flex-wrap gap-3 items-center">
                <div className="flex-1 min-w-[200px]">
                  <div className="relative">
                    <Input
                      placeholder="搜索标题、描述、建议..."
                      value={searchKeyword}
                      onChange={(e) => setSearchKeyword(e.target.value)}
                      onKeyPress={(e) => e.key === "Enter" && handleSearch()}
                      className="bg-gray-800 border-gray-700 text-white pl-10"
                    />
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                  </div>
                </div>
                <Select value={category} onValueChange={setCategory}>
                  <SelectTrigger className="w-[120px] bg-gray-800 border-gray-700 text-white">
                    <SelectValue placeholder="分类" />
                  </SelectTrigger>
                  <SelectContent className="bg-gray-800 border-gray-700">
                    {categoryOptions.map((opt) => (
                      <SelectItem key={opt.value} value={opt.value} className="text-white">
                        {opt.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Select value={lessonType} onValueChange={setLessonType}>
                  <SelectTrigger className="w-[120px] bg-gray-800 border-gray-700 text-white">
                    <SelectValue placeholder="类型" />
                  </SelectTrigger>
                  <SelectContent className="bg-gray-800 border-gray-700">
                    {lessonTypeOptions.map((opt) => (
                      <SelectItem key={opt.value} value={opt.value} className="text-white">
                        {opt.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Select value={impactLevel} onValueChange={setImpactLevel}>
                  <SelectTrigger className="w-[100px] bg-gray-800 border-gray-700 text-white">
                    <SelectValue placeholder="影响" />
                  </SelectTrigger>
                  <SelectContent className="bg-gray-800 border-gray-700">
                    {impactOptions.map((opt) => (
                      <SelectItem key={opt.value} value={opt.value} className="text-white">
                        {opt.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Button onClick={handleSearch} className="bg-blue-600 hover:bg-blue-700">
                  <Filter className="h-4 w-4 mr-2" />
                  筛选
                </Button>
                <Button variant="outline" onClick={handleReset} className="border-gray-700 text-gray-300 hover:bg-gray-800">
                  <X className="h-4 w-4 mr-2" />
                  重置
                </Button>
                <Button onClick={handleCreate} className="bg-green-600 hover:bg-green-700 ml-auto">
                  <Plus className="h-4 w-4 mr-2" />
                  新建
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* 经验教训卡片列表 */}
          {lessons.length === 0 ? (
            <Card className="bg-gray-900/50 border-gray-800">
              <CardContent className="p-12 text-center text-gray-400">
                <BookOpen className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>暂无经验教训数据</p>
                <p className="text-sm mt-2">点击右上角"新建"添加第一条经验教训</p>
              </CardContent>
            </Card>
          ) : (
            <motion.div
              variants={staggerContainer}
              className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
            >
              {lessons.map((lesson) => {
                const TypeIcon = typeIcons[lesson.lesson_type] || Lightbulb;
                return (
                  <motion.div key={lesson.id} variants={fadeIn}>
                    <Card className="bg-gray-900/50 border-gray-800 hover:border-gray-700 transition-colors h-full">
                      <CardHeader className="pb-3">
                        <div className="flex items-start justify-between gap-2">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                              <Badge className={categoryColors[lesson.category] || "bg-gray-700"}>
                                {categoryLabels[lesson.category] || lesson.category}
                              </Badge>
                              {lesson.impact_level && (
                                <div className="flex items-center gap-1">
                                  <div className={`w-2 h-2 rounded-full ${impactConfig[lesson.impact_level]?.color}`} />
                                  <span className="text-xs text-gray-400">
                                    {impactConfig[lesson.impact_level]?.label}
                                  </span>
                                </div>
                              )}
                            </div>
                            <CardTitle className="text-lg text-white line-clamp-2">
                              {lesson.title}
                            </CardTitle>
                          </div>
                          <TypeIcon className={`h-5 w-5 ${typeColors[lesson.lesson_type]}`} />
                        </div>
                      </CardHeader>
                      <CardContent className="space-y-3">
                        {lesson.project_name && (
                          <p className="text-sm text-gray-400">
                            项目：{lesson.project_name}
                          </p>
                        )}
                        <p className="text-sm text-gray-300 line-clamp-3">
                          {lesson.description}
                        </p>
                        {lesson.recommendation && (
                          <div className="bg-blue-500/10 border border-blue-500/20 rounded p-2">
                            <p className="text-xs text-blue-400 font-medium">建议：</p>
                            <p className="text-xs text-gray-300 line-clamp-2">
                              {lesson.recommendation}
                            </p>
                          </div>
                        )}
                        <div className="flex items-center justify-between pt-2 border-t border-gray-800">
                          <span className="text-xs text-gray-500">
                            {lesson.lesson_type && typeLabels[lesson.lesson_type]}
                          </span>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleEdit(lesson)}
                            className="text-gray-400 hover:text-white h-7"
                          >
                            查看
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  </motion.div>
                );
              })}
            </motion.div>
          )}
        </motion.div>
      )}

      {/* 创建/编辑对话框 */}
      <Dialog open={showCreateDialog || showEditDialog} onOpenChange={(open) => {
        setShowCreateDialog(open);
        setShowEditDialog(open);
        if (!open) setEditingLesson(null);
      }}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto bg-gray-900 border-gray-800">
          <DialogHeader>
            <DialogTitle className="text-white">
              {editingLesson ? "编辑经验教训" : "新建经验教训"}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-gray-300">项目 ID</Label>
                <Input
                  value={formData.project_id}
                  onChange={(e) => handleInputChange("project_id", e.target.value)}
                  className="bg-gray-800 border-gray-700 text-white"
                  placeholder="可选"
                />
              </div>
              <div>
                <Label className="text-gray-300">标题 *</Label>
                <Input
                  value={formData.title}
                  onChange={(e) => handleInputChange("title", e.target.value)}
                  className="bg-gray-800 border-gray-700 text-white"
                  placeholder="简要描述经验教训"
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-gray-300">分类</Label>
                <Select value={formData.category} onValueChange={(v) => handleInputChange("category", v)}>
                  <SelectTrigger className="bg-gray-800 border-gray-700 text-white">
                    <SelectValue placeholder="选择分类" />
                  </SelectTrigger>
                  <SelectContent className="bg-gray-800 border-gray-700">
                    {categoryOptions.slice(1).map((opt) => (
                      <SelectItem key={opt.value} value={opt.value} className="text-white">
                        {opt.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label className="text-gray-300">类型</Label>
                <Select value={formData.lesson_type} onValueChange={(v) => handleInputChange("lesson_type", v)}>
                  <SelectTrigger className="bg-gray-800 border-gray-700 text-white">
                    <SelectValue placeholder="选择类型" />
                  </SelectTrigger>
                  <SelectContent className="bg-gray-800 border-gray-700">
                    {lessonTypeOptions.slice(1).map((opt) => (
                      <SelectItem key={opt.value} value={opt.value} className="text-white">
                        {opt.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div>
              <Label className="text-gray-300">影响程度</Label>
              <Select value={formData.impact_level} onValueChange={(v) => handleInputChange("impact_level", v)}>
                <SelectTrigger className="bg-gray-800 border-gray-700 text-white">
                  <SelectValue placeholder="选择影响程度" />
                </SelectTrigger>
                <SelectContent className="bg-gray-800 border-gray-700">
                  {impactOptions.slice(1).map((opt) => (
                    <SelectItem key={opt.value} value={opt.value} className="text-white">
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label className="text-gray-300">描述 *</Label>
              <Textarea
                value={formData.description}
                onChange={(e) => handleInputChange("description", e.target.value)}
                className="bg-gray-800 border-gray-700 text-white min-h-[100px]"
                placeholder="详细描述经验教训的内容"
              />
            </div>
            <div>
              <Label className="text-gray-300">根本原因</Label>
              <Textarea
                value={formData.root_cause}
                onChange={(e) => handleInputChange("root_cause", e.target.value)}
                className="bg-gray-800 border-gray-700 text-white min-h-[80px]"
                placeholder="分析导致问题的根本原因"
              />
            </div>
            <div>
              <Label className="text-gray-300">已采取行动</Label>
              <Textarea
                value={formData.action_taken}
                onChange={(e) => handleInputChange("action_taken", e.target.value)}
                className="bg-gray-800 border-gray-700 text-white min-h-[80px]"
                placeholder="已经采取的解决或改进措施"
              />
            </div>
            <div>
              <Label className="text-gray-300">建议</Label>
              <Textarea
                value={formData.recommendation}
                onChange={(e) => handleInputChange("recommendation", e.target.value)}
                className="bg-gray-800 border-gray-700 text-white min-h-[80px]"
                placeholder="对未来项目的建议"
              />
            </div>
            <div>
              <Label className="text-gray-300">适用范围</Label>
              <Input
                value={formData.applicable_to}
                onChange={(e) => handleInputChange("applicable_to", e.target.value)}
                className="bg-gray-800 border-gray-700 text-white"
                placeholder="如：所有软件开发项目"
              />
            </div>
            <div>
              <Label className="text-gray-300">标签</Label>
              <Input
                value={formData.tags}
                onChange={(e) => handleInputChange("tags", e.target.value)}
                className="bg-gray-800 border-gray-700 text-white"
                placeholder="用逗号分隔多个标签"
              />
            </div>
            <div className="flex justify-end gap-3 pt-4">
              <Button
                variant="outline"
                onClick={() => {
                  setShowCreateDialog(false);
                  setShowEditDialog(false);
                  setEditingLesson(null);
                }}
                className="border-gray-700 text-gray-300 hover:bg-gray-800"
              >
                取消
              </Button>
              <Button onClick={handleSubmit} className="bg-blue-600 hover:bg-blue-700">
                {editingLesson ? "保存" : "创建"}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
