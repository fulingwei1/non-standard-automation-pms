// -*- coding: utf-8 -*-
/**
 * 员工档案列表页面
 */

import React, { useState, useEffect, useCallback, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Users,
  Search,
  Eye,
  RefreshCw,
  User,
  Clock,
  Upload,
  FileSpreadsheet,
  CheckCircle,
  AlertCircle,
  UserCheck,
  UserX,
  Briefcase,
} from "lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import { Progress } from "../components/ui/progress";
import { cn } from "../lib/utils";
import { staffMatchingApi, organizationApi } from "../services/api";

// 默认空数据
const defaultProfiles = [];

// 状态标签配置
const STATUS_TABS = [
  {
    key: "active",
    label: "在职",
    icon: UserCheck,
    color: "text-green-400",
    bgColor: "bg-green-500/10",
  },
  {
    key: "regular",
    label: "正式",
    icon: Briefcase,
    color: "text-blue-400",
    bgColor: "bg-blue-500/10",
  },
  {
    key: "probation",
    label: "试用期",
    icon: Clock,
    color: "text-yellow-400",
    bgColor: "bg-yellow-500/10",
  },
  {
    key: "intern",
    label: "实习期",
    icon: User,
    color: "text-purple-400",
    bgColor: "bg-purple-500/10",
  },
  {
    key: "resigned",
    label: "离职",
    icon: UserX,
    color: "text-slate-400",
    bgColor: "bg-slate-500/10",
  },
];

// 获取员工显示标签
const getEmployeeStatusBadge = (status, type) => {
  if (status === "resigned") {
    return {
      label: "离职",
      variant: "secondary",
      className: "bg-slate-500/20 text-slate-400",
    };
  }
  if (type === "probation") {
    return {
      label: "试用期",
      variant: "secondary",
      className: "bg-yellow-500/20 text-yellow-400",
    };
  }
  if (type === "intern") {
    return {
      label: "实习期",
      variant: "secondary",
      className: "bg-purple-500/20 text-purple-400",
    };
  }
  return {
    label: "正式",
    variant: "secondary",
    className: "bg-green-500/20 text-green-400",
  };
};

export default function EmployeeProfileList() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [profiles, setProfiles] = useState(defaultProfiles);
  const [searchKeyword, setSearchKeyword] = useState("");
  const [filterDepartment, setFilterDepartment] = useState("all");
  const [activeStatusTab, setActiveStatusTab] = useState("active");

  // 上传相关状态
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const fileInputRef = useRef(null);

  const loadProfiles = useCallback(async () => {
    setLoading(true);
    try {
      // 根据选中的标签构建查询参数
      const params = { limit: 200 };

      if (activeStatusTab === "active") {
        params.employment_status = "active";
      } else if (activeStatusTab === "resigned") {
        params.employment_status = "resigned";
      } else if (activeStatusTab === "regular") {
        params.employment_status = "active";
        params.employment_type = "regular";
      } else if (activeStatusTab === "probation") {
        params.employment_status = "active";
        params.employment_type = "probation";
      } else if (activeStatusTab === "intern") {
        params.employment_status = "active";
        params.employment_type = "intern";
      }

      console.log("[员工档案] 发起API请求, 参数:", params);
      const response = await staffMatchingApi.getProfiles(params);
      console.log("[员工档案] API响应:", response);
      // API 直接返回数组，不是 items 包装
      const data = response.data || response;
      console.log(
        "[员工档案] 解析后数据:",
        data,
        "是否数组:",
        Array.isArray(data),
      );
      if (Array.isArray(data)) {
        console.log("[员工档案] 设置数据, 数量:", data.length);
        setProfiles(data);
      } else if (data?.items) {
        console.log("[员工档案] 设置items数据, 数量:", data.items.length);
        setProfiles(data.items);
      } else {
        console.warn("[员工档案] 数据格式不正确:", data);
      }
    } catch (error) {
      console.error(
        "[员工档案] 加载失败:",
        error.response?.status,
        error.response?.data,
        error.message,
      );
    } finally {
      setLoading(false);
    }
  }, [activeStatusTab]);

  useEffect(() => {
    loadProfiles();
  }, [loadProfiles]);

  // 过滤
  const filteredProfiles = profiles.filter((p) => {
    const matchKeyword =
      !searchKeyword ||
      p.employee_name.includes(searchKeyword) ||
      p.employee_code.includes(searchKeyword);
    const matchDept =
      filterDepartment === "all" || p.department === filterDepartment;
    return matchKeyword && matchDept;
  });

  // 获取部门列表
  const departments = [
    ...new Set(profiles.map((p) => p.department).filter(Boolean)),
  ];

  // 统计
  const stats = {
    total: profiles.length,
    available: profiles.filter((p) => p.current_workload_pct < 80).length,
    busy: profiles.filter((p) => p.current_workload_pct >= 80).length,
  };

  const getWorkloadColor = (pct) => {
    if (pct >= 90) {return "text-red-400";}
    if (pct >= 70) {return "text-yellow-400";}
    return "text-green-400";
  };

  // 处理文件上传
  const handleFileUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) {return;}

    // 验证文件类型
    if (!file.name.endsWith(".xlsx") && !file.name.endsWith(".xls")) {
      setUploadResult({
        success: false,
        message: "请上传 Excel 文件（.xlsx 或 .xls 格式）",
      });
      return;
    }

    setUploading(true);
    setUploadResult(null);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await organizationApi.importEmployees(formData);
      setUploadResult(response.data || response);

      // 导入成功后刷新列表
      if (response.data?.success || response.success) {
        setTimeout(() => {
          loadProfiles();
        }, 1000);
      }
    } catch (error) {
      console.error("上传失败:", error);
      setUploadResult({
        success: false,
        message:
          error.response?.data?.detail || error.message || "上传失败，请重试",
      });
    } finally {
      setUploading(false);
      // 清空文件输入，允许重复选择同一文件
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="员工能力档案"
        description="查看员工技能评估、工作负载和项目绩效"
        actions={
          <Button onClick={() => setShowUploadModal(true)}>
            <Upload className="h-4 w-4 mr-2" />
            导入员工数据
          </Button>
        }
      />

      {/* 上传弹窗 */}
      {showUploadModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={() => {
              setShowUploadModal(false);
              setUploadResult(null);
            }}
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="relative z-10 w-full max-w-lg bg-slate-900 border border-white/10 rounded-xl p-6 shadow-xl"
          >
            <h3 className="text-lg font-semibold text-white mb-4">
              导入员工数据
            </h3>

            {/* 上传区域 */}
            <div
              className={cn(
                "border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors",
                uploading
                  ? "border-primary/50 bg-primary/5"
                  : "border-white/20 hover:border-primary/50 hover:bg-white/5",
              )}
              onClick={() => !uploading && fileInputRef.current?.click()}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".xlsx,.xls"
                onChange={handleFileUpload}
                className="hidden"
              />
              {uploading ? (
                <div className="flex flex-col items-center gap-3">
                  <RefreshCw className="h-10 w-10 text-primary animate-spin" />
                  <div className="text-slate-300">正在导入...</div>
                </div>
              ) : (
                <div className="flex flex-col items-center gap-3">
                  <FileSpreadsheet className="h-10 w-10 text-slate-400" />
                  <div className="text-slate-300">
                    点击或拖拽上传 Excel 文件
                  </div>
                  <div className="text-xs text-slate-500">
                    支持 .xlsx、.xls 格式
                  </div>
                </div>
              )}
            </div>

            {/* 上传结果 */}
            {uploadResult && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={cn(
                  "mt-4 p-4 rounded-lg",
                  uploadResult.success
                    ? "bg-green-500/10 border border-green-500/30"
                    : "bg-red-500/10 border border-red-500/30",
                )}
              >
                <div className="flex items-start gap-3">
                  {uploadResult.success ? (
                    <CheckCircle className="h-5 w-5 text-green-400 mt-0.5" />
                  ) : (
                    <AlertCircle className="h-5 w-5 text-red-400 mt-0.5" />
                  )}
                  <div>
                    <div
                      className={
                        uploadResult.success ? "text-green-300" : "text-red-300"
                      }
                    >
                      {uploadResult.message}
                    </div>
                    {uploadResult.success && (
                      <div className="text-sm text-slate-400 mt-2">
                        新增 {uploadResult.imported} 人 · 更新{" "}
                        {uploadResult.updated} 人 · 跳过 {uploadResult.skipped}{" "}
                        条
                      </div>
                    )}
                    {uploadResult.errors?.length > 0 && (
                      <div className="text-xs text-red-400/80 mt-2">
                        {uploadResult.errors.slice(0, 3).map((err, i) => (
                          <div key={i}>{err}</div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </motion.div>
            )}

            {/* 说明 */}
            <div className="mt-4 p-3 bg-white/5 rounded-lg text-xs text-slate-400 space-y-1">
              <div className="font-medium text-slate-300 mb-2">导入说明：</div>
              <div>• Excel 文件必须包含"姓名"列</div>
              <div>
                •
                支持的列：姓名、一级部门、二级部门、三级部门、职务、联系方式、在职离职状态
              </div>
              <div>• 系统会根据 姓名+部门 判断员工是否已存在</div>
              <div>• 已存在的员工会更新信息，不会重复创建</div>
              <div>• 支持直接导入企业微信导出的通讯录</div>
            </div>

            {/* 按钮 */}
            <div className="mt-6 flex justify-end gap-3">
              <Button
                variant="outline"
                onClick={() => {
                  setShowUploadModal(false);
                  setUploadResult(null);
                }}
              >
                关闭
              </Button>
            </div>
          </motion.div>
        </div>
      )}

      {/* 状态标签筛选 */}
      <div className="flex items-center gap-2 flex-wrap">
        {STATUS_TABS.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeStatusTab === tab.key;
          return (
            <button
              key={tab.key}
              onClick={() => setActiveStatusTab(tab.key)}
              className={cn(
                "flex items-center gap-2 px-4 py-2 rounded-lg border transition-all",
                isActive
                  ? `${tab.bgColor} border-current ${tab.color}`
                  : "border-white/10 text-slate-400 hover:bg-white/5 hover:text-white",
              )}
            >
              <Icon className="h-4 w-4" />
              <span className="font-medium">{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-3 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-lg bg-blue-500/10">
                <Users className="h-6 w-6 text-blue-400" />
              </div>
              <div>
                <div className="text-2xl font-bold text-white">
                  {stats.total}
                </div>
                <div className="text-sm text-slate-400">
                  {activeStatusTab === "active"
                    ? "在职员工"
                    : activeStatusTab === "regular"
                      ? "正式员工"
                      : activeStatusTab === "probation"
                        ? "试用期员工"
                        : activeStatusTab === "intern"
                          ? "实习期员工"
                          : activeStatusTab === "resigned"
                            ? "离职员工"
                            : "总员工数"}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-lg bg-green-500/10">
                <User className="h-6 w-6 text-green-400" />
              </div>
              <div>
                <div className="text-2xl font-bold text-green-400">
                  {stats.available}
                </div>
                <div className="text-sm text-slate-400">可用人员 (&lt;80%)</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-lg bg-orange-500/10">
                <Clock className="h-6 w-6 text-orange-400" />
              </div>
              <div>
                <div className="text-2xl font-bold text-orange-400">
                  {stats.busy}
                </div>
                <div className="text-sm text-slate-400">繁忙人员 (≥80%)</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 搜索和筛选 */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>员工列表</CardTitle>
          <div className="flex items-center gap-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <Input
                placeholder="搜索姓名/工号..."
                value={searchKeyword}
                onChange={(e) => setSearchKeyword(e.target.value)}
                className="pl-9 w-64"
              />
            </div>
            <select
              value={filterDepartment}
              onChange={(e) => setFilterDepartment(e.target.value)}
              className="h-10 px-3 rounded-md border border-white/10 bg-white/5 text-sm"
            >
              <option value="all">全部部门</option>
              {departments.map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              ))}
            </select>
            <Button variant="outline" size="icon" onClick={loadProfiles}>
              <RefreshCw className={cn("h-4 w-4", loading && "animate-spin")} />
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-12 text-slate-400">加载中...</div>
          ) : filteredProfiles.length === 0 ? (
            <div className="text-center py-12 text-slate-400">暂无数据</div>
          ) : (
            <div className="space-y-3">
              {filteredProfiles.map((profile) => (
                <motion.div
                  key={profile.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="p-4 rounded-lg border border-white/10 bg-white/5 hover:bg-white/10 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 rounded-full bg-gradient-to-br from-violet-500 to-indigo-500 flex items-center justify-center text-white font-semibold">
                        {profile.employee_name?.charAt(0) || "?"}
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-white">
                            {profile.employee_name}
                          </span>
                          <span className="text-xs text-slate-500">
                            {profile.employee_code}
                          </span>
                          {/* 员工状态标签 */}
                          {(() => {
                            const statusBadge = getEmployeeStatusBadge(
                              profile.employment_status,
                              profile.employment_type,
                            );
                            return (
                              <Badge
                                variant={statusBadge.variant}
                                className={cn("text-xs", statusBadge.className)}
                              >
                                {statusBadge.label}
                              </Badge>
                            );
                          })()}
                        </div>
                        <div className="text-sm text-slate-400 mt-1">
                          {profile.department || "未分配部门"}
                        </div>
                        <div className="flex gap-1 mt-2">
                          {(profile.top_skills || []).slice(0, 4).map((tag) => (
                            <Badge
                              key={tag}
                              variant="secondary"
                              className="text-xs"
                            >
                              {tag}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-8">
                      {/* 综合得分 */}
                      <div className="text-center">
                        <div className="text-xl font-bold text-primary">
                          {profile.avg_performance_score
                            ? Math.round(profile.avg_performance_score)
                            : "--"}
                        </div>
                        <div className="text-xs text-slate-500">绩效评分</div>
                      </div>

                      {/* 工作负载 */}
                      <div className="w-32">
                        <div className="flex justify-between text-xs mb-1">
                          <span className="text-slate-400">工作负载</span>
                          <span
                            className={getWorkloadColor(
                              profile.current_workload_pct || 0,
                            )}
                          >
                            {profile.current_workload_pct || 0}%
                          </span>
                        </div>
                        <Progress
                          value={profile.current_workload_pct || 0}
                          className="h-2"
                        />
                      </div>

                      {/* 项目数 */}
                      <div className="text-center">
                        <div className="text-lg font-semibold text-white">
                          {profile.total_projects || 0}
                        </div>
                        <div className="text-xs text-slate-500">参与项目</div>
                      </div>

                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() =>
                          navigate(
                            `/staff-matching/profiles/${profile.employee_id}`,
                          )
                        }
                      >
                        <Eye className="h-4 w-4 mr-1" />
                        详情
                      </Button>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
