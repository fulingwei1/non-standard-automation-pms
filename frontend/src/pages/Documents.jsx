/**
 * Documents Management Page - 文档管理页面
 * Features: Document list, upload, download, delete, filter by project
 */
import { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import {
  Archive,
  FileText,
  Upload,
  Search,
  Folder,
  Download,
  Trash2,
  Eye,
  Filter,
  X,
  File,
  FileImage,
  FileVideo,
  FileCode,
  FileSpreadsheet,
  Calendar,
  User } from
"lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle } from
"../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue } from
"../components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogBody,
  DialogFooter } from
"../components/ui/dialog";
import { cn, formatDate } from "../lib/utils";
import { fadeIn, staggerContainer } from "../lib/animations";
import { documentApi, projectApi } from "../services/api";
import { toast } from "../components/ui/toast";
import { LoadingCard, ErrorMessage, EmptyState } from "../components/common";

// File type icons mapping
const getFileIcon = (fileName) => {
  const ext = fileName?.split(".").pop()?.toLowerCase() || "";
  if (["jpg", "jpeg", "png", "gif", "webp", "svg"].includes(ext)) {
    return FileImage;
  }
  if (["mp4", "avi", "mov", "wmv", "flv"].includes(ext)) {
    return FileVideo;
  }
  if (["js", "ts", "jsx", "tsx", "py", "java", "cpp", "c"].includes(ext)) {
    return FileCode;
  }
  if (["xls", "xlsx", "csv"].includes(ext)) {
    return FileSpreadsheet;
  }
  return FileText;
};

// Format file size
const formatFileSize = (bytes) => {
  if (!bytes) {return "0 B";}
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + " " + sizes[i];
};

export default function Documents() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [projects, setProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [showUploadDialog, setShowUploadDialog] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadFile, setUploadFile] = useState(null);
  const [uploadProjectId, setUploadProjectId] = useState("");
  const [uploadDescription, setUploadDescription] = useState("");

  // Load projects
  const loadProjects = useCallback(async () => {
    try {
      const response = await projectApi.list({ page_size: 1000 });
      const data = response.data || response;
      const projectList = data.items || data || [];
      setProjects(projectList);
    } catch (err) {
      console.error("Failed to load projects:", err);
    }
  }, []);

  // Load documents
  const loadDocuments = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // If a specific project is selected, load documents for that project
      if (selectedProject && selectedProject !== "all") {
        const response = await documentApi.list(selectedProject);
        const data = response.data || response;
        const docList = Array.isArray(data) ? data : data.items || [];
        setDocuments(docList);
      } else {
        // Load documents for all projects
        // Since API requires project_id, we'll load from all projects
        const allDocs = [];
        if (projects?.length > 0) {
          const promises = projects.
          slice(0, 20).
          map((project) =>
          documentApi.list(project.id).catch(() => ({ data: [] }))
          );
          const results = await Promise.allSettled(promises);
          (results || []).forEach((result) => {
            if (result.status === "fulfilled") {
              const data = result.value.data || result.value;
              const docs = Array.isArray(data) ? data : data.items || [];
              allDocs.push(...docs);
            }
          });
        }
        setDocuments(allDocs);
      }
    } catch (err) {
      console.error("Failed to load documents:", err);
      const errorMessage =
      err.response?.data?.detail || err.message || "加载文档失败";
      setError(errorMessage);
      setDocuments([]);
    } finally {
      setLoading(false);
    }
  }, [selectedProject, projects]);

  useEffect(() => {
    loadProjects();
  }, [loadProjects]);

  useEffect(() => {
    if (projects?.length > 0 || selectedProject === "all") {
      loadDocuments();
    }
  }, [loadDocuments, selectedProject]);

  // Handle file upload
  const handleFileSelect = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      // Check file size (max 50MB)
      if (file.size > 50 * 1024 * 1024) {
        toast.error("文件大小不能超过 50MB");
        return;
      }
      setUploadFile(file);
    }
  };

  const handleUpload = async () => {
    if (!uploadFile) {
      toast.error("请选择要上传的文件");
      return;
    }
    if (!uploadProjectId) {
      toast.error("请选择关联项目");
      return;
    }

    try {
      setUploading(true);
      const formData = new FormData();
      formData.append("file", uploadFile);
      formData.append("project_id", uploadProjectId);
      if (uploadDescription) {
        formData.append("description", uploadDescription);
      }

      await documentApi.create(formData);
      toast.success("文件上传成功");
      setShowUploadDialog(false);
      setUploadFile(null);
      setUploadProjectId("");
      setUploadDescription("");
      await loadDocuments();
    } catch (err) {
      console.error("Failed to upload file:", err);
      const errorMessage =
      err.response?.data?.detail || err.message || "上传失败，请稍后重试";
      toast.error(errorMessage);
    } finally {
      setUploading(false);
    }
  };

  // Handle download
  const handleDownload = async (document) => {
    try {
      // If document has a download_url, use it
      if (document.download_url || document.file_url) {
        window.open(document.download_url || document.file_url, "_blank");
      } else if (document.id) {
        // Try to construct download URL
        const baseURL =
        import.meta.env?.VITE_API_BASE_URL || "http://127.0.0.1:8000";
        window.open(
          `${baseURL}/api/v1/documents/${document.id}/download`,
          "_blank"
        );
      } else {
        toast.error("无法获取下载链接");
      }
    } catch (err) {
      console.error("Failed to download file:", err);
      toast.error("下载失败，请稍后重试");
    }
  };

  // Filter documents
  const filteredDocuments = (documents || []).filter((doc) => {
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      return (
        doc.file_name?.toLowerCase().includes(query) ||
        doc.name?.toLowerCase().includes(query) ||
        doc.description?.toLowerCase().includes(query) ||
        doc.project_name?.toLowerCase().includes(query));

    }
    return true;
  });

  // Get project name
  const getProjectName = (projectId) => {
    const project = (projects || []).find(
      (p) => p.id === projectId || p.project_code === projectId
    );
    return project?.project_name || "未知项目";
  };

  if (loading && documents?.length === 0) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        <PageHeader title="文件管理" />
        <div className="container mx-auto px-4 py-6">
          <LoadingCard rows={5} />
        </div>
      </div>);

  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <PageHeader
        title="文件管理"
        actions={
        <Button className="gap-2" onClick={() => setShowUploadDialog(true)}>
            <Upload className="w-4 h-4" />
            上传文件
        </Button>
        } />

      <div className="container mx-auto px-4 py-6 space-y-6">
        {/* Filters */}
        <motion.div variants={fadeIn} initial="hidden" animate="visible">
          <Card className="bg-surface-1/50">
            <CardContent className="p-4">
              <div className="flex flex-col md:flex-row gap-4">
                <div className="flex-1">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <Input
                      placeholder="搜索文档名称、描述..."
                      value={searchQuery || "unknown"}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="pl-10 bg-slate-800/50 border-slate-700" />

                  </div>
                </div>
                <div className="w-full md:w-64">
                  <Select
                    value={selectedProject || "unknown"}
                    onValueChange={setSelectedProject}>

                    <SelectTrigger className="bg-slate-800/50 border-slate-700">
                      <SelectValue placeholder="选择项目" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">全部项目</SelectItem>
                      {(projects || []).map((project) =>
                      <SelectItem
                        key={project.id || project.project_code}
                        value={project.id || project.project_code}>

                          {project.project_name}
                      </SelectItem>
                      )}
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Documents List */}
        {error && !documents?.length ?
        <ErrorMessage error={error} onRetry={loadDocuments} /> :
        filteredDocuments.length === 0 ?
        <EmptyState
          icon={Archive}
          title="暂无文档"
          description={
          searchQuery || selectedProject !== "all" ?
          "没有找到匹配的文档" :
          "还没有上传任何文档"
          } /> :


        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">

            {(filteredDocuments || []).map((doc) => {
            const FileIcon = getFileIcon(doc.file_name || doc.name);
            return (
              <motion.div key={doc.id} variants={fadeIn}>
                  <Card className="bg-surface-1/50 hover:bg-surface-1/70 transition-colors">
                    <CardContent className="p-4">
                      <div className="flex items-start gap-3">
                        <div
                        className={cn(
                          "p-2 rounded-lg",
                          "bg-blue-500/10 text-blue-400"
                        )}>

                          <FileIcon className="w-5 h-5" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <h4 className="font-medium text-white truncate mb-1">
                            {doc.file_name || doc.name || "未命名文件"}
                          </h4>
                          <div className="space-y-1 text-xs text-slate-400">
                            {doc.file_size &&
                          <div className="flex items-center gap-1">
                                <Archive className="w-3 h-3" />
                                {formatFileSize(doc.file_size)}
                          </div>
                          }
                            {doc.created_at &&
                          <div className="flex items-center gap-1">
                                <Calendar className="w-3 h-3" />
                                {formatDate(doc.created_at)}
                          </div>
                          }
                            {doc.project_id &&
                          <div className="flex items-center gap-1">
                                <Folder className="w-3 h-3" />
                                {getProjectName(doc.project_id)}
                          </div>
                          }
                            {doc.uploaded_by &&
                          <div className="flex items-center gap-1">
                                <User className="w-3 h-3" />
                                {doc.uploaded_by}
                          </div>
                          }
                          </div>
                          {doc.description &&
                        <p className="text-xs text-slate-500 mt-2 line-clamp-2">
                              {doc.description}
                        </p>
                        }
                        </div>
                      </div>
                      <div className="flex items-center gap-2 mt-4 pt-4 border-t border-slate-700">
                        <Button
                        size="sm"
                        variant="ghost"
                        className="flex-1 gap-2"
                        onClick={() => handleDownload(doc)}>

                          <Download className="w-4 h-4" />
                          下载
                        </Button>
                        {doc.file_type &&
                      <Badge variant="outline" className="text-xs">
                            {doc.file_type}
                      </Badge>
                      }
                      </div>
                    </CardContent>
                  </Card>
              </motion.div>);

          })}
        </motion.div>
        }

        {/* Upload Dialog */}
        <Dialog open={showUploadDialog} onOpenChange={setShowUploadDialog}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>上传文件</DialogTitle>
            </DialogHeader>
            <DialogBody className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">
                  选择项目
                </label>
                <Select
                  value={uploadProjectId || "unknown"}
                  onValueChange={setUploadProjectId}>

                  <SelectTrigger>
                    <SelectValue placeholder="选择关联项目" />
                  </SelectTrigger>
                  <SelectContent>
                    {(projects || []).map((project) =>
                    <SelectItem
                      key={project.id || project.project_code}
                      value={project.id || project.project_code}>

                        {project.project_name}
                    </SelectItem>
                    )}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">
                  选择文件
                </label>
                <div className="border-2 border-dashed border-slate-700 rounded-lg p-6 text-center">
                  <input
                    type="file"
                    onChange={handleFileSelect}
                    className="hidden"
                    id="file-upload" />

                  <label
                    htmlFor="file-upload"
                    className="cursor-pointer flex flex-col items-center gap-2">

                    <Upload className="w-8 h-8 text-slate-400" />
                    <span className="text-sm text-slate-400">
                      {uploadFile ? uploadFile.name : "点击选择文件"}
                    </span>
                    {uploadFile &&
                    <span className="text-xs text-slate-500">
                        {formatFileSize(uploadFile.size)}
                    </span>
                    }
                  </label>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">
                  描述（可选）
                </label>
                <Input
                  placeholder="输入文件描述..."
                  value={uploadDescription || "unknown"}
                  onChange={(e) => setUploadDescription(e.target.value)} />

              </div>
            </DialogBody>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => {
                  setShowUploadDialog(false);
                  setUploadFile(null);
                  setUploadProjectId("");
                  setUploadDescription("");
                }}>

                取消
              </Button>
              <Button
                onClick={handleUpload}
                disabled={uploading || !uploadFile || !uploadProjectId}>

                {uploading ? "上传中..." : "上传"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>);}