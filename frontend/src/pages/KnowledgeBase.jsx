/**
 * 知识库
 * 历史方案、产品知识、工艺知识、竞品情报、模板库
 */
import React, { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import {
  BookOpen,
  Search,
  Filter,
  Plus,
  Calendar,
  Eye,
  Download,
  Star,
  StarOff,
  Folder,
  FileText,
  File,
  Image,
  Video,
  MoreHorizontal,
  ChevronRight,
  ChevronDown,
  Tag,
  Clock,
  Users,
  Building2,
  Briefcase,
  Package,
  Settings,
  Cpu,
  Shield,
  FileCode,
  Layout,
  FolderOpen,
  Copy,
  Bookmark,
  BookmarkCheck,
  TrendingUp,
  Award,
  Lightbulb,
} from "lucide-react";
import { PageHeader } from "../components/layout";
import { Button } from "../components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../components/ui/card";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "../components/ui/dropdown-menu";
import { cn } from "../lib/utils";
import { fadeIn, staggerContainer } from "../lib/animations";
import { presaleApi, serviceApi } from "../services/api";

// 知识库分类配置
const knowledgeCategories = [
  {
    id: "solutions",
    name: "历史方案库",
    icon: FileText,
    color: "text-violet-400",
    bgColor: "bg-violet-400/10",
    description: "按行业/设备类型分类的优秀方案",
    count: 45,
  },
  {
    id: "products",
    name: "产品知识库",
    icon: Package,
    color: "text-blue-400",
    bgColor: "bg-blue-400/10",
    description: "公司设备型号、规格参数、应用案例",
    count: 32,
  },
  {
    id: "process",
    name: "工艺知识库",
    icon: Settings,
    color: "text-emerald-400",
    bgColor: "bg-emerald-400/10",
    description: "标准测试工艺、行业规范",
    count: 28,
  },
  {
    id: "competitors",
    name: "竞品情报库",
    icon: Shield,
    color: "text-red-400",
    bgColor: "bg-red-400/10",
    description: "竞争对手产品信息、价格参考",
    count: 15,
  },
  {
    id: "templates",
    name: "模板库",
    icon: Layout,
    color: "text-amber-400",
    bgColor: "bg-amber-400/10",
    description: "方案模板、投标模板、调研表单",
    count: 20,
  },
];

// 行业分类
const industries = [
  { id: "all", name: "全部行业" },
  { id: "new_energy", name: "新能源汽车" },
  { id: "consumer", name: "消费电子" },
  { id: "auto_parts", name: "汽车零部件" },
  { id: "energy_storage", name: "储能" },
  { id: "medical", name: "医疗器械" },
  { id: "semiconductor", name: "半导体" },
];

// 设备类型
const deviceTypes = [
  { id: "all", name: "全部类型" },
  { id: "ict", name: "ICT测试" },
  { id: "fct", name: "FCT测试" },
  { id: "eol", name: "EOL测试" },
  { id: "aging", name: "老化设备" },
  { id: "burning", name: "烧录设备" },
  { id: "vision", name: "视觉检测" },
  { id: "assembly", name: "组装线" },
];

// Mock 知识库文档数据
// Mock data - 已移除，使用真实API
// 获取文件类型图标
const getFileTypeIcon = (type) => {
  switch (type) {
    case "doc":
      return { icon: FileText, color: "text-blue-400" };
    case "pdf":
      return { icon: File, color: "text-red-400" };
    case "excel":
      return { icon: FileCode, color: "text-emerald-400" };
    case "image":
      return { icon: Image, color: "text-amber-400" };
    case "video":
      return { icon: Video, color: "text-violet-400" };
    default:
      return { icon: File, color: "text-slate-400" };
  }
};

// 文档卡片组件
function DocumentCard({ document, onToggleStar }) {
  const fileTypeConfig = getFileTypeIcon(document.fileType);
  const FileIcon = fileTypeConfig.icon;

  return (
    <motion.div
      variants={fadeIn}
      className="p-4 rounded-xl bg-surface-100/50 backdrop-blur-lg border border-white/5 hover:bg-white/[0.03] cursor-pointer transition-all group"
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 rounded-lg bg-surface-50 flex items-center justify-center">
            <FileIcon className={cn("w-5 h-5", fileTypeConfig.color)} />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              {document.isRecommended && (
                <Badge className="text-xs bg-amber-500">
                  <Award className="w-3 h-3 mr-1" />
                  推荐
                </Badge>
              )}
              {document.isStarred && (
                <Star className="w-4 h-4 text-amber-400 fill-amber-400" />
              )}
            </div>
            <h4 className="text-sm font-medium text-white group-hover:text-primary transition-colors line-clamp-2">
              {document.title}
            </h4>
          </div>
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="opacity-0 group-hover:opacity-100 transition-opacity"
              onClick={(e) => e.stopPropagation()}
            >
              <MoreHorizontal className="w-4 h-4 text-slate-400" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem>
              <Eye className="w-4 h-4 mr-2" />
              预览
            </DropdownMenuItem>
            <DropdownMenuItem>
              <Download className="w-4 h-4 mr-2" />
              下载
            </DropdownMenuItem>
            <DropdownMenuItem>
              <Copy className="w-4 h-4 mr-2" />
              复制链接
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={() => onToggleStar(document.id)}>
              {document.isStarred ? (
                <>
                  <StarOff className="w-4 h-4 mr-2" />
                  取消收藏
                </>
              ) : (
                <>
                  <Star className="w-4 h-4 mr-2" />
                  收藏
                </>
              )}
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      <p className="text-xs text-slate-500 line-clamp-2 mb-3">
        {document.description}
      </p>

      <div className="flex flex-wrap gap-1.5 mb-3">
        {document.tags.slice(0, 3).map((tag, index) => (
          <span
            key={index}
            className="text-xs px-2 py-0.5 bg-primary/10 text-primary rounded-full"
          >
            {tag}
          </span>
        ))}
      </div>

      <div className="flex items-center justify-between text-xs pt-3 border-t border-white/5">
        <div className="flex items-center gap-3 text-slate-500">
          <span className="flex items-center gap-1">
            <Eye className="w-3 h-3" />
            {document.views}
          </span>
          <span className="flex items-center gap-1">
            <Download className="w-3 h-3" />
            {document.downloads}
          </span>
        </div>
        <span className="text-slate-500">{document.fileSize}</span>
      </div>
    </motion.div>
  );
}

// 分类侧边栏
function CategorySidebar({ categories, selectedCategory, onSelectCategory }) {
  return (
    <div className="space-y-2">
      <div
        className={cn(
          "flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-colors",
          selectedCategory === "all"
            ? "bg-primary/20 text-primary"
            : "text-slate-400 hover:bg-white/[0.04] hover:text-white",
        )}
        onClick={() => onSelectCategory("all")}
      >
        <BookOpen className="w-5 h-5" />
        <span className="text-sm font-medium">全部文档</span>
        <span className="ml-auto text-xs">
          {categories.reduce((acc, c) => acc + c.count, 0)}
        </span>
      </div>
      {categories.map((category) => {
        const CategoryIcon = category.icon;
        return (
          <div
            key={category.id}
            className={cn(
              "flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-colors",
              selectedCategory === category.id
                ? "bg-primary/20 text-primary"
                : "text-slate-400 hover:bg-white/[0.04] hover:text-white",
            )}
            onClick={() => onSelectCategory(category.id)}
          >
            <CategoryIcon
              className={cn(
                "w-5 h-5",
                selectedCategory === category.id ? "" : category.color,
              )}
            />
            <span className="text-sm font-medium">{category.name}</span>
            <span className="ml-auto text-xs">{category.count}</span>
          </div>
        );
      })}
      <div className="border-t border-white/5 my-2 pt-2">
        <div
          className={cn(
            "flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-colors",
            selectedCategory === "starred"
              ? "bg-primary/20 text-primary"
              : "text-slate-400 hover:bg-white/[0.04] hover:text-white",
          )}
          onClick={() => onSelectCategory("starred")}
        >
          <Star className="w-5 h-5 text-amber-400" />
          <span className="text-sm font-medium">我的收藏</span>
        </div>
        <div
          className={cn(
            "flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-colors",
            selectedCategory === "recent"
              ? "bg-primary/20 text-primary"
              : "text-slate-400 hover:bg-white/[0.04] hover:text-white",
          )}
          onClick={() => onSelectCategory("recent")}
        >
          <Clock className="w-5 h-5 text-blue-400" />
          <span className="text-sm font-medium">最近浏览</span>
        </div>
      </div>
    </div>
  );
}

export default function KnowledgeBase() {
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [selectedIndustry, setSelectedIndustry] = useState("all");
  const [selectedDeviceType, setSelectedDeviceType] = useState("all");
  const [searchTerm, setSearchTerm] = useState("");
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Load templates and solutions from API
  const loadDocuments = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const allDocuments = [];

      // Load templates
      if (selectedCategory === "all" || selectedCategory === "templates") {
        try {
          const templatesResponse = await presaleApi.templates.list({
            page: 1,
            page_size: 100,
          });
          const templates =
            templatesResponse.data?.items || templatesResponse.data || [];

          templates.forEach((template) => {
            allDocuments.push({
              id: `template-${template.id}`,
              category: "templates",
              title: template.name || "",
              description: template.description || "",
              industry: template.industry?.toLowerCase() || null,
              deviceType: template.test_type?.toLowerCase() || null,
              tags: template.tags || [],
              fileType: "doc",
              fileSize: "0.5MB",
              author: template.creator_name || "",
              createdAt: template.created_at || "",
              views: 0,
              downloads: 0,
              isStarred: false,
              isRecommended: template.is_active || false,
            });
          });
        } catch (err) {
          console.error("Failed to load templates:", err);
        }
      }

      // Load solutions (published/approved ones)
      if (selectedCategory === "all" || selectedCategory === "solutions") {
        try {
          const solutionsResponse = await presaleApi.solutions.list({
            page: 1,
            page_size: 100,
            status: "APPROVED,SUBMITTED",
          });
          const solutions =
            solutionsResponse.data?.items || solutionsResponse.data || [];

          solutions.forEach((solution) => {
            allDocuments.push({
              id: `solution-${solution.id}`,
              category: "solutions",
              title: solution.name || "",
              description: solution.description || "",
              industry: solution.industry?.toLowerCase() || null,
              deviceType: solution.solution_type?.toLowerCase() || null,
              tags: solution.tags || [],
              fileType: "doc",
              fileSize: "2.5MB",
              author: solution.creator_name || "",
              createdAt: solution.created_at || "",
              views: 0,
              downloads: 0,
              isStarred: false,
              isRecommended: solution.status === "APPROVED",
            });
          });
        } catch (err) {
          console.error("Failed to load solutions:", err);
        }
      }

      // Load knowledge base articles from service API
      if (
        selectedCategory === "all" ||
        selectedCategory === "products" ||
        selectedCategory === "process"
      ) {
        try {
          const kbResponse = await serviceApi.knowledgeBase.list({
            page: 1,
            page_size: 100,
            status: "PUBLISHED",
            keyword: searchTerm || undefined,
          });
          const articles = kbResponse.data?.items || kbResponse.data || [];

          articles.forEach((article) => {
            // Map category to our categories
            let category = "products";
            if (
              article.category === "PROCESS" ||
              article.category === "STANDARD"
            ) {
              category = "process";
            } else if (
              article.category === "PRODUCT" ||
              article.category === "EQUIPMENT"
            ) {
              category = "products";
            }

            // Only add if matches selected category
            if (selectedCategory === "all" || selectedCategory === category) {
              allDocuments.push({
                id: `kb-${article.id}`,
                category: category,
                title: article.title || "",
                description: article.content
                  ? article.content.substring(0, 200)
                  : "",
                industry: null,
                deviceType: null,
                tags: article.tags || [],
                fileType: "doc",
                fileSize: "1.0MB",
                author: article.author_name || "",
                createdAt: article.created_at || "",
                views: article.view_count || 0,
                downloads: 0,
                isStarred: false,
                isRecommended: article.is_featured || false,
              });
            }
          });
        } catch (err) {
          console.error("Failed to load knowledge base articles:", err);
        }
      }

      // Merge with mock data for competitors category (no API yet)
      if (selectedCategory === "all" || selectedCategory === "competitors") {
        const filteredMock = mockDocuments.filter(
          (doc) => doc.category === "competitors",
        );
        allDocuments.push(...filteredMock);
      }

      setDocuments(allDocuments);
    } catch (err) {
      console.error("Failed to load documents:", err);
      setError(err.response?.data?.detail || err.message || "加载知识库失败");
      // Keep existing documents on error, don't reset to mock
    } finally {
      setLoading(false);
    }
  }, [selectedCategory, searchTerm]);

  useEffect(() => {
    loadDocuments();
  }, [loadDocuments]);

  // 筛选文档
  const filteredDocuments = documents.filter((doc) => {
    // 分类筛选
    let matchesCategory = true;
    if (selectedCategory === "starred") {
      matchesCategory = doc.isStarred;
    } else if (selectedCategory !== "all") {
      matchesCategory = doc.category === selectedCategory;
    }

    // 行业筛选
    const matchesIndustry =
      selectedIndustry === "all" || doc.industry === selectedIndustry;

    // 设备类型筛选
    const matchesDeviceType =
      selectedDeviceType === "all" || doc.deviceType === selectedDeviceType;

    // 搜索
    const matchesSearch =
      doc.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      doc.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
      doc.tags.some((tag) =>
        tag.toLowerCase().includes(searchTerm.toLowerCase()),
      );

    return (
      matchesCategory && matchesIndustry && matchesDeviceType && matchesSearch
    );
  });

  // 切换收藏
  const handleToggleStar = (docId) => {
    setDocuments((prev) =>
      prev.map((doc) =>
        doc.id === docId ? { ...doc, isStarred: !doc.isStarred } : doc,
      ),
    );
  };

  // 获取当前分类信息
  const currentCategory = knowledgeCategories.find(
    (c) => c.id === selectedCategory,
  );

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      {/* 页面头部 */}
      <PageHeader
        title="知识库"
        description="历史方案、产品知识、工艺知识、竞品情报、模板库"
        actions={
          <motion.div variants={fadeIn} className="flex gap-2">
            <Button variant="outline" className="flex items-center gap-2">
              <Lightbulb className="w-4 h-4" />
              智能推荐
            </Button>
            <Button className="flex items-center gap-2">
              <Plus className="w-4 h-4" />
              上传文档
            </Button>
          </motion.div>
        }
      />

      <div className="flex gap-6">
        {/* 侧边栏 */}
        <motion.div
          variants={fadeIn}
          className="w-64 flex-shrink-0 hidden lg:block"
        >
          <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5 sticky top-6">
            <CardContent className="p-4">
              <CategorySidebar
                categories={knowledgeCategories}
                selectedCategory={selectedCategory}
                onSelectCategory={setSelectedCategory}
              />
            </CardContent>
          </Card>
        </motion.div>

        {/* 主内容区 */}
        <div className="flex-1 space-y-6">
          {/* 当前分类信息 */}
          {currentCategory && (
            <motion.div variants={fadeIn}>
              <Card
                className={cn(
                  "border",
                  currentCategory.bgColor,
                  "border-white/5",
                )}
              >
                <CardContent className="p-4 flex items-center gap-4">
                  <div
                    className={cn(
                      "w-12 h-12 rounded-lg flex items-center justify-center",
                      currentCategory.bgColor,
                    )}
                  >
                    <currentCategory.icon
                      className={cn("w-6 h-6", currentCategory.color)}
                    />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-white">
                      {currentCategory.name}
                    </h3>
                    <p className="text-sm text-slate-400">
                      {currentCategory.description}
                    </p>
                  </div>
                  <Badge variant="secondary" className="ml-auto">
                    {
                      documents.filter(
                        (doc) =>
                          selectedCategory === "all" ||
                          doc.category === selectedCategory,
                      ).length
                    }{" "}
                    个文档
                  </Badge>
                </CardContent>
              </Card>
            </motion.div>
          )}

          {/* 工具栏 */}
          <motion.div
            variants={fadeIn}
            className="bg-surface-100/50 backdrop-blur-lg rounded-xl border border-white/5 shadow-lg p-4"
          >
            <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4">
              {/* 搜索 */}
              <div className="relative flex-1 max-w-md">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <Input
                  type="text"
                  placeholder="搜索文档标题、描述、标签..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-9 w-full"
                />
              </div>

              {/* 筛选 */}
              <div className="flex items-center gap-3 flex-wrap">
                <select
                  value={selectedIndustry}
                  onChange={(e) => setSelectedIndustry(e.target.value)}
                  className="bg-surface-50 border border-white/10 rounded-md px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary"
                >
                  {industries.map((industry) => (
                    <option key={industry.id} value={industry.id}>
                      {industry.name}
                    </option>
                  ))}
                </select>
                <select
                  value={selectedDeviceType}
                  onChange={(e) => setSelectedDeviceType(e.target.value)}
                  className="bg-surface-50 border border-white/10 rounded-md px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary"
                >
                  {deviceTypes.map((type) => (
                    <option key={type.id} value={type.id}>
                      {type.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </motion.div>

          {/* 推荐文档 */}
          {selectedCategory === "all" && (
            <motion.div variants={fadeIn}>
              <Card className="bg-gradient-to-r from-amber-500/10 to-orange-500/10 border border-amber-500/20">
                <CardHeader className="pb-2">
                  <CardTitle className="text-lg flex items-center gap-2 text-amber-400">
                    <Award className="w-5 h-5" />
                    推荐文档
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {documents
                      .filter((doc) => doc.isRecommended)
                      .slice(0, 3)
                      .map((doc) => {
                        const fileTypeConfig = getFileTypeIcon(doc.fileType);
                        const FileIcon = fileTypeConfig.icon;
                        return (
                          <div
                            key={doc.id}
                            className="flex items-start gap-3 p-3 bg-surface-50/50 rounded-lg cursor-pointer hover:bg-white/[0.03] transition-colors"
                          >
                            <div className="w-8 h-8 rounded-lg bg-surface-100 flex items-center justify-center">
                              <FileIcon
                                className={cn("w-4 h-4", fileTypeConfig.color)}
                              />
                            </div>
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-medium text-white truncate">
                                {doc.title}
                              </p>
                              <p className="text-xs text-slate-500 mt-0.5">
                                {doc.views} 次浏览
                              </p>
                            </div>
                          </div>
                        );
                      })}
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          )}

          {/* 加载状态 */}
          {loading && (
            <div className="text-center py-16 text-slate-400">
              <BookOpen className="w-12 h-12 mx-auto mb-4 text-slate-600 animate-pulse" />
              <p className="text-lg font-medium">加载中...</p>
            </div>
          )}

          {/* 错误提示 */}
          {error && !loading && (
            <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 text-red-400 text-sm">
              {error}
            </div>
          )}

          {/* 文档列表 */}
          {!loading && !error && (
            <motion.div
              variants={fadeIn}
              className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4"
            >
              {filteredDocuments.length > 0 ? (
                filteredDocuments.map((doc) => (
                  <DocumentCard
                    key={doc.id}
                    document={doc}
                    onToggleStar={handleToggleStar}
                  />
                ))
              ) : (
                <div className="col-span-full text-center py-16 text-slate-400">
                  <BookOpen className="w-12 h-12 mx-auto mb-4 text-slate-600" />
                  <p className="text-lg font-medium">暂无文档</p>
                  <p className="text-sm">请调整筛选条件或上传新文档</p>
                </div>
              )}
            </motion.div>
          )}
        </div>
      </div>
    </motion.div>
  );
}
