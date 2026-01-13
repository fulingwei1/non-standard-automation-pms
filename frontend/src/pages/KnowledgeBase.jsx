/**
 * 知识库
 * 历史方案、产品知识、工艺知识、竞品情报、模板库
 */
import React, { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
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
  HardDrive,
  CheckCircle2,
  ThumbsUp,
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
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
  DialogBody,
} from "../components/ui/dialog";
import { Textarea } from "../components/ui/textarea";
import { toast } from "../components/ui/toast";
import { cn } from "../lib/utils";
import { fadeIn, staggerContainer } from "../lib/animations";
import { presaleApi, serviceApi } from "../services/api";

// 知识库分类配置（基础配置，count 将动态计算）
const knowledgeCategoriesConfig = [
  {
    id: "solutions",
    name: "历史方案库",
    icon: FileText,
    color: "text-violet-400",
    bgColor: "bg-violet-400/10",
    description: "按行业/设备类型分类的优秀方案",
  },
  {
    id: "products",
    name: "产品知识库",
    icon: Package,
    color: "text-blue-400",
    bgColor: "bg-blue-400/10",
    description: "公司设备型号、规格参数、应用案例",
  },
  {
    id: "process",
    name: "工艺知识库",
    icon: Settings,
    color: "text-emerald-400",
    bgColor: "bg-emerald-400/10",
    description: "标准测试工艺、行业规范",
  },
  {
    id: "competitors",
    name: "竞品情报库",
    icon: Shield,
    color: "text-red-400",
    bgColor: "bg-red-400/10",
    description: "竞争对手产品信息、价格参考",
  },
  {
    id: "templates",
    name: "模板库",
    icon: Layout,
    color: "text-amber-400",
    bgColor: "bg-amber-400/10",
    description: "方案模板、投标模板、调研表单",
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

// Mock 知识库文档数据 - 竞品分析类别的后备数据（API待实现）
const mockDocuments = [];
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
function DocumentCard({ document, onToggleStar, onDownload, onLike, onAdopt }) {
  const fileTypeConfig = getFileTypeIcon(document.fileType);
  const FileIcon = fileTypeConfig.icon;

  const handleDownload = (e) => {
    e.stopPropagation();
    if (document.hasFile && document.realId) {
      onDownload(document.realId, document.fileName || document.title);
    } else {
      toast.info("该文档没有可下载的文件");
    }
  };

  const handleLike = (e) => {
    e.stopPropagation();
    if (document.realId) {
      onLike(document.realId);
    }
  };

  const handleAdopt = (e) => {
    e.stopPropagation();
    if (document.realId) {
      onAdopt(document.realId);
    }
  };

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
              {document.hasFile && !document.allowDownload && (
                <Shield className="w-4 h-4 text-slate-500" title="仅作者可下载" />
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
            {document.hasFile && (
              <DropdownMenuItem onClick={handleDownload}>
                <Download className="w-4 h-4 mr-2" />
                下载
              </DropdownMenuItem>
            )}
            <DropdownMenuItem onClick={handleLike}>
              <ThumbsUp className="w-4 h-4 mr-2" />
              点赞
            </DropdownMenuItem>
            <DropdownMenuItem onClick={handleAdopt}>
              <CheckCircle2 className="w-4 h-4 mr-2" />
              标记采用
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
        <div className="flex items-center gap-4 text-slate-500">
          <span className="flex items-center gap-1" title="浏览量">
            <Eye className="w-3 h-3" />
            {document.views}
          </span>
          <span className="flex items-center gap-1" title="点赞数">
            <ThumbsUp className="w-3 h-3" />
            {document.likes || 0}
          </span>
          <span className="flex items-center gap-1" title="下载数">
            <Download className="w-3 h-3" />
            {document.downloads}
          </span>
          <span className="flex items-center gap-1 text-emerald-400" title="采用数">
            <CheckCircle2 className="w-3 h-3" />
            {document.adopts || 0}
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
  const [showUploadDialog, setShowUploadDialog] = useState(false);

  // 动态计算每个分类的文档数量
  const knowledgeCategories = knowledgeCategoriesConfig.map((cat) => ({
    ...cat,
    count: documents.filter((doc) => doc.category === cat.id).length,
  }));

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
              // 根据文件类型确定图标类型
              let fileType = "doc";
              if (article.file_type) {
                if (article.file_type.includes("pdf")) fileType = "pdf";
                else if (article.file_type.includes("image")) fileType = "image";
                else if (article.file_type.includes("video")) fileType = "video";
                else if (article.file_type.includes("excel") || article.file_type.includes("spreadsheet")) fileType = "excel";
              }

              // 格式化文件大小
              const formatSize = (bytes) => {
                if (!bytes) return "-";
                const k = 1024;
                const sizes = ["B", "KB", "MB", "GB"];
                const i = Math.floor(Math.log(bytes) / Math.log(k));
                return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
              };

              allDocuments.push({
                id: `kb-${article.id}`,
                realId: article.id,
                category: category,
                title: article.title || "",
                description: article.content
                  ? article.content.substring(0, 200)
                  : "",
                industry: null,
                deviceType: null,
                tags: article.tags || [],
                fileType: fileType,
                fileSize: formatSize(article.file_size),
                fileName: article.file_name,
                hasFile: !!article.file_path,
                allowDownload: article.allow_download !== false,
                author: article.author_name || "",
                createdAt: article.created_at || "",
                views: article.view_count || 0,
                downloads: article.download_count || 0,
                likes: article.like_count || 0,
                adopts: article.adopt_count || 0,
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

  // 下载文档处理
  const handleDownload = async (articleId, fileName) => {
    try {
      const token = localStorage.getItem("token");
      const downloadUrl = serviceApi.knowledgeBase.downloadUrl(articleId);

      // 使用 fetch 下载并处理权限错误
      const response = await fetch(downloadUrl, {
        headers: token && !token.startsWith("demo_token_")
          ? { Authorization: `Bearer ${token}` }
          : {},
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        if (response.status === 403) {
          toast.error(errorData.detail || "此文档不允许下载");
        } else {
          toast.error(errorData.detail || "下载失败");
        }
        return;
      }

      // 创建 blob 并下载
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = window.document.createElement("a");
      a.href = url;
      a.download = fileName || "download";
      window.document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      window.document.body.removeChild(a);

      // 刷新列表以更新下载计数
      loadDocuments();
      toast.success("文件下载成功");
    } catch (err) {
      console.error("Download error:", err);
      toast.error("下载失败，请稍后重试");
    }
  };

  // 点赞文档处理
  const handleLike = async (articleId) => {
    try {
      await serviceApi.knowledgeBase.like(articleId);
      loadDocuments();
      toast.success("点赞成功");
    } catch (err) {
      console.error("Like error:", err);
      toast.error("点赞失败");
    }
  };

  // 采用文档处理
  const handleAdopt = async (articleId) => {
    try {
      await serviceApi.knowledgeBase.adopt(articleId);
      loadDocuments();
      toast.success("已标记为采用");
    } catch (err) {
      console.error("Adopt error:", err);
      toast.error("标记采用失败");
    }
  };

  // 上传文档处理
  const handleUploadDocument = async (docData) => {
    try {
      // 有文件时使用文件上传 API
      if (docData.file) {
        const formData = new FormData();
        formData.append("file", docData.file);
        formData.append("title", docData.title);
        formData.append(
          "category",
          docData.category === "products"
            ? "PRODUCT"
            : docData.category === "process"
              ? "PROCESS"
              : docData.category.toUpperCase()
        );
        if (docData.tags && docData.tags.length > 0) {
          formData.append("tags", docData.tags.join(","));
        }
        if (docData.content) {
          formData.append("content", docData.content);
        }
        // 传递下载权限设置
        formData.append("allow_download", docData.allowDownload ? "true" : "false");

        await serviceApi.knowledgeBase.upload(formData);
      } else {
        // 无文件时使用普通创建 API
        if (
          docData.category === "products" ||
          docData.category === "process"
        ) {
          await serviceApi.knowledgeBase.create({
            title: docData.title,
            category: docData.category === "products" ? "PRODUCT" : "PROCESS",
            content: docData.content,
            tags: docData.tags,
            is_featured: false,
            status: "已发布",
          });
        } else if (docData.category === "templates") {
          await presaleApi.templates.create({
            name: docData.title,
            description: docData.content,
            template_type: "方案模板",
            tags: docData.tags,
          });
        } else if (docData.category === "solutions") {
          await presaleApi.solutions.create({
            name: docData.title,
            description: docData.content,
            solution_type: "历史方案",
            tags: docData.tags,
          });
        }
      }

      toast.success("文档上传成功");
      setShowUploadDialog(false);
      loadDocuments(); // 刷新列表
    } catch (err) {
      console.error("Failed to upload document:", err);
      toast.error(err.response?.data?.detail || "上传文档失败");
    }
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
            <Button
              className="flex items-center gap-2"
              onClick={() => setShowUploadDialog(true)}
            >
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
                    onDownload={handleDownload}
                    onLike={handleLike}
                    onAdopt={handleAdopt}
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

      {/* 上传文档对话框 */}
      <AnimatePresence>
        {showUploadDialog && (
          <UploadDocumentDialog
            onClose={() => setShowUploadDialog(false)}
            onSubmit={handleUploadDocument}
            categories={knowledgeCategoriesConfig.filter(
              (c) => c.id !== "competitors"
            )}
          />
        )}
      </AnimatePresence>
    </motion.div>
  );
}

// 上传文档对话框组件
function UploadDocumentDialog({ onClose, onSubmit, categories }) {
  const [formData, setFormData] = useState({
    title: "",
    category: "products",
    content: "",
    tags: [],
    file: null,
    allowDownload: true,
  });
  const [tagInput, setTagInput] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [quota, setQuota] = useState(null);
  const fileInputRef = React.useRef(null);

  // 最大文件大小：200MB
  const MAX_FILE_SIZE = 200 * 1024 * 1024;

  // 加载配额信息
  useEffect(() => {
    const loadQuota = async () => {
      try {
        const response = await serviceApi.knowledgeBase.getQuota();
        setQuota(response.data);
      } catch (err) {
        console.error("Failed to load quota:", err);
      }
    };
    loadQuota();
  }, []);

  // 允许的文件类型
  const ALLOWED_TYPES = [
    // 文档
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
    ".txt",
    ".md",
    ".csv",
    // 图片
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
    // 视频
    ".mp4",
    ".avi",
    ".mov",
    ".wmv",
    ".mkv",
    ".webm",
    // 压缩包
    ".zip",
    ".rar",
    ".7z",
  ];

  const formatFileSize = (bytes) => {
    if (bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  const handleFileSelect = (file) => {
    if (!file) return;

    // 检查文件大小
    if (file.size > MAX_FILE_SIZE) {
      toast.error(`文件大小超过限制（最大 200MB），当前文件: ${formatFileSize(file.size)}`);
      return;
    }

    // 检查文件类型
    const ext = "." + file.name.split(".").pop().toLowerCase();
    if (!ALLOWED_TYPES.includes(ext)) {
      toast.error(`不支持的文件类型: ${ext}`);
      return;
    }

    setFormData({ ...formData, file, title: formData.title || file.name.replace(/\.[^/.]+$/, "") });
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleSubmit = async () => {
    if (!formData.title.trim()) {
      toast.error("请填写文档标题");
      return;
    }
    if (!formData.file && !formData.content.trim()) {
      toast.error("请选择文件或填写文档内容");
      return;
    }

    setSubmitting(true);
    try {
      await onSubmit(formData);
    } finally {
      setSubmitting(false);
    }
  };

  const handleAddTag = () => {
    if (tagInput.trim() && !formData.tags.includes(tagInput.trim())) {
      setFormData({ ...formData, tags: [...formData.tags, tagInput.trim()] });
      setTagInput("");
    }
  };

  const handleRemoveTag = (tag) => {
    setFormData({ ...formData, tags: formData.tags.filter((t) => t !== tag) });
  };

  return (
    <Dialog open={true} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl bg-slate-900 border-slate-700 max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>上传知识文档</DialogTitle>
          <DialogDescription>
            上传文档到知识库（支持文档、图片、视频，最大 200MB）
          </DialogDescription>
        </DialogHeader>
        <DialogBody>
          <div className="space-y-4">
            {/* 配额显示 */}
            {quota && (
              <div className="p-3 rounded-lg bg-slate-800/50 border border-slate-700">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2 text-sm text-slate-300">
                    <HardDrive className="w-4 h-4" />
                    <span>存储空间</span>
                  </div>
                  <span className="text-xs text-slate-400">
                    {formatFileSize(quota.used_bytes)} / {formatFileSize(quota.total_bytes)}
                  </span>
                </div>
                <div className="w-full h-2 bg-slate-700 rounded-full overflow-hidden">
                  <div
                    className={cn(
                      "h-full rounded-full transition-all",
                      quota.used_percentage > 90
                        ? "bg-red-500"
                        : quota.used_percentage > 70
                          ? "bg-amber-500"
                          : "bg-emerald-500"
                    )}
                    style={{ width: `${Math.min(quota.used_percentage, 100)}%` }}
                  />
                </div>
                <div className="flex justify-between mt-1">
                  <span className="text-xs text-slate-500">
                    已用 {quota.used_percentage.toFixed(1)}%
                  </span>
                  <span className="text-xs text-slate-500">
                    剩余 {formatFileSize(quota.remaining_bytes)}
                  </span>
                </div>
              </div>
            )}

            {/* 文件上传区域 */}
            <div>
              <label className="text-sm text-slate-400 mb-1 block">
                选择文件
              </label>
              <div
                className={cn(
                  "border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors",
                  dragActive
                    ? "border-primary bg-primary/10"
                    : "border-slate-700 hover:border-slate-500",
                  formData.file && "border-emerald-500 bg-emerald-500/10"
                )}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  className="hidden"
                  accept={ALLOWED_TYPES.join(",")}
                  onChange={(e) => handleFileSelect(e.target.files?.[0])}
                />
                {formData.file ? (
                  <div className="space-y-2">
                    <File className="w-10 h-10 mx-auto text-emerald-400" />
                    <div className="text-white font-medium">
                      {formData.file.name}
                    </div>
                    <div className="text-sm text-slate-400">
                      {formatFileSize(formData.file.size)}
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        setFormData({ ...formData, file: null });
                      }}
                    >
                      移除文件
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <Download className="w-10 h-10 mx-auto text-slate-400 rotate-180" />
                    <div className="text-slate-300">
                      拖放文件到这里，或点击选择
                    </div>
                    <div className="text-xs text-slate-500">
                      支持 PDF、Word、Excel、PPT、图片、视频（最大 200MB）
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* 标题 */}
            <div>
              <label className="text-sm text-slate-400 mb-1 block">
                文档标题 *
              </label>
              <Input
                value={formData.title}
                onChange={(e) =>
                  setFormData({ ...formData, title: e.target.value })
                }
                placeholder="输入文档标题"
                className="bg-slate-800/50 border-slate-700"
              />
            </div>

            {/* 分类 */}
            <div>
              <label className="text-sm text-slate-400 mb-1 block">
                文档分类 *
              </label>
              <select
                value={formData.category}
                onChange={(e) =>
                  setFormData({ ...formData, category: e.target.value })
                }
                className="w-full px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-white"
              >
                {categories.map((cat) => (
                  <option key={cat.id} value={cat.id}>
                    {cat.name}
                  </option>
                ))}
              </select>
            </div>

            {/* 描述/内容 */}
            <div>
              <label className="text-sm text-slate-400 mb-1 block">
                文档描述 {!formData.file && "*"}
              </label>
              <Textarea
                value={formData.content}
                onChange={(e) =>
                  setFormData({ ...formData, content: e.target.value })
                }
                placeholder={formData.file ? "添加文档描述（可选）" : "输入文档内容..."}
                rows={4}
                className="bg-slate-800/50 border-slate-700 text-sm"
              />
            </div>

            {/* 标签 */}
            <div>
              <label className="text-sm text-slate-400 mb-1 block">标签</label>
              <div className="flex gap-2 mb-2">
                <Input
                  value={tagInput}
                  onChange={(e) => setTagInput(e.target.value)}
                  placeholder="添加标签"
                  className="bg-slate-800/50 border-slate-700 flex-1"
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      handleAddTag();
                    }
                  }}
                />
                <Button variant="outline" onClick={handleAddTag}>
                  添加
                </Button>
              </div>
              {formData.tags.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {formData.tags.map((tag) => (
                    <Badge
                      key={tag}
                      variant="secondary"
                      className="cursor-pointer hover:bg-red-500/20"
                      onClick={() => handleRemoveTag(tag)}
                    >
                      {tag} ×
                    </Badge>
                  ))}
                </div>
              )}
            </div>

            {/* 下载权限设置 */}
            <div className="pt-2 border-t border-slate-700">
              <label className="flex items-center gap-3 cursor-pointer group">
                <input
                  type="checkbox"
                  checked={formData.allowDownload}
                  onChange={(e) =>
                    setFormData({ ...formData, allowDownload: e.target.checked })
                  }
                  className="w-4 h-4 rounded border-slate-600 bg-slate-800 text-primary focus:ring-primary focus:ring-offset-0"
                />
                <div>
                  <span className="text-sm text-white group-hover:text-primary transition-colors">
                    允许他人下载
                  </span>
                  <p className="text-xs text-slate-500">
                    关闭后，只有您本人可以下载此文档
                  </p>
                </div>
              </label>
            </div>
          </div>
        </DialogBody>
        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={submitting}>
            取消
          </Button>
          <Button onClick={handleSubmit} disabled={submitting}>
            {submitting ? "上传中..." : "上传文档"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}