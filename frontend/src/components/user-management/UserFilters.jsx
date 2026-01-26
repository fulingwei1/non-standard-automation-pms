/**
 * User Filters Component
 * 用户筛选组件
 */

import { useState, useEffect as _useEffect } from "react";
import { Badge } from "../../components/ui/badge";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue } from
"../../components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter } from
"../../components/ui/dialog";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
  PopoverHeader,
  PopoverBody,
  PopoverFooter } from
"../../components/ui/popover";
import {
  Label } from
"../../components/ui/label";
import {
  Search,
  Filter,
  X,
  Calendar,
  User,
  Building2,
  Tag,
  Shield,
  DollarSign,
  CheckCircle,
  Clock,
  Download,
  Upload,
  RotateCcw } from
"lucide-react";
import {
  userStatusConfigs,
  userTypeConfigs,
  departmentConfigs,
  userRoleConfigs,
  userSortConfigs,
  getUserStatusConfig,
  formatUserRole,
  formatUserStatus as _formatUserStatus } from
"./userManagementConstants";
import { cn } from "../../lib/utils";

export function UserFilters({
  onFiltersChange,
  initialFilters,
  availableDepartments: _availableDepartments = [],
  availableRoles: _availableRoles = [],
  showAdvancedFilters: _showAdvancedFilters = false,
  showExportOptions = true,
  className
}) {
  const [filters, setFilters] = useState(initialFilters || {
    search: "",
    status: "",
    userType: "",
    department: "",
    role: "",
    authType: "",
    minCredits: "",
    maxCredits: "",
    dateRange: null,
    sortBy: "created_at_desc",
    sortOrder: "desc"
  });

  const [showAdvanced, setShowAdvanced] = useState(false);
  const [_showDateRange, setShowDateRange] = useState(false);
  const [showBulkActions, setShowBulkActions] = useState(false);
  const [selectedUsers, _setSelectedUsers] = useState([]);

  // 处理搜索
  const handleSearch = (value) => {
    const newFilters = { ...filters, search: value };
    setFilters(newFilters);
    onFiltersChange?.(newFilters);
  };

  // 处理状态过滤
  const handleStatusChange = (value) => {
    const newFilters = { ...filters, status: value };
    setFilters(newFilters);
    onFiltersChange?.(newFilters);
  };

  // 处理用户类型过滤
  const handleUserTypeChange = (value) => {
    const newFilters = { ...filters, userType: value };
    setFilters(newFilters);
    onFiltersChange?.(newFilters);
  };

  // 处理部门过滤
  const handleDepartmentChange = (value) => {
    const newFilters = { ...filters, department: value };
    setFilters(newFilters);
    onFiltersChange?.(newFilters);
  };

  // 处理角色过滤
  const handleRoleChange = (value) => {
    const newFilters = { ...filters, role: value };
    setFilters(newFilters);
    onFiltersChange?.(newFilters);
  };

  // 处理认证类型过滤
  const handleAuthTypeChange = (value) => {
    const newFilters = { ...filters, authType: value };
    setFilters(newFilters);
    onFiltersChange?.(newFilters);
  };

  // 处理积分范围过滤
  const handleCreditsChange = (min, max) => {
    const newFilters = { ...filters, minCredits: min, maxCredits: max };
    setFilters(newFilters);
    onFiltersChange?.(newFilters);
  };

  // 处理日期范围过滤
  const handleDateRangeChange = (startDate, endDate) => {
    const newFilters = { ...filters, dateRange: { startDate, endDate } };
    setFilters(newFilters);
    onFiltersChange?.(newFilters);
    setShowDateRange(false);
  };

  // 处理排序
  const handleSortChange = (value) => {
    const [field, order] = value.split('_');
    const newFilters = {
      ...filters,
      sortBy: field,
      sortOrder: order
    };
    setFilters(newFilters);
    onFiltersChange?.(newFilters);
  };

  // 清除所有筛选
  const handleClearFilters = () => {
    const clearedFilters = {
      search: "",
      status: "",
      userType: "",
      department: "",
      role: "",
      authType: "",
      minCredits: "",
      maxCredits: "",
      dateRange: null,
      sortBy: "created_at_desc",
      sortOrder: "desc"
    };
    setFilters(clearedFilters);
    onFiltersChange?.(clearedFilters);
    setShowAdvanced(false);
  };

  // 重置筛选
  const handleResetFilters = () => {
    setFilters(initialFilters || {
      search: "",
      status: "",
      userType: "",
      department: "",
      role: "",
      authType: "",
      minCredits: "",
      maxCredits: "",
      dateRange: null,
      sortBy: "created_at_desc",
      sortOrder: "desc"
    });
    onFiltersChange?.(initialFilters || {
      search: "",
      status: "",
      userType: "",
      department: "",
      role: "",
      authType: "",
      minCredits: "",
      maxCredits: "",
      dateRange: null,
      sortBy: "created_at_desc",
      sortOrder: "desc"
    });
  };

  // 导出筛选结果
  const handleExport = (format = "excel") => {
    // 实现导出逻辑
    console.log("Export users with filters:", filters, "Format:", format);
  };

  // 导入用户
  const handleImport = () => {
    // 实现导入逻辑
    console.log("Import users");
  };

  // 渲染筛选标签
  const renderFilterTags = () => {
    const tags = [];

    if (filters.search) {
      tags.push({
        label: `搜索: ${filters.search}`,
        onRemove: () => handleSearch("")
      });
    }

    if (filters.status) {
      const config = getUserStatusConfig(filters.status);
      tags.push({
        label: `状态: ${config.label}`,
        onRemove: () => handleStatusChange("")
      });
    }

    if (filters.userType) {
      const config = userTypeConfigs[filters.userType];
      tags.push({
        label: `类型: ${config?.label || filters.userType}`,
        onRemove: () => handleUserTypeChange("")
      });
    }

    if (filters.department) {
      const deptConfig = departmentConfigs[filters.department];
      tags.push({
        label: `部门: ${deptConfig?.label || filters.department}`,
        onRemove: () => handleDepartmentChange("")
      });
    }

    if (filters.role) {
      tags.push({
        label: `角色: ${formatUserRole(filters.role)}`,
        onRemove: () => handleRoleChange("")
      });
    }

    if (filters.authType) {
      tags.push({
        label: `认证: ${filters.authType}`,
        onRemove: () => handleAuthTypeChange("")
      });
    }

    if (filters.minCredits || filters.maxCredits) {
      const min = filters.minCredits || "0";
      const max = filters.maxCredits || "∞";
      tags.push({
        label: `积分: ${min}-${max}`,
        onRemove: () => handleCreditsChange("", "")
      });
    }

    if (filters.dateRange) {
      const start = filters.dateRange.startDate ? new Date(filters.dateRange.startDate).toLocaleDateString() : "";
      const end = filters.dateRange.endDate ? new Date(filters.dateRange.endDate).toLocaleDateString() : "";
      tags.push({
        label: `日期: ${start} - ${end}`,
        onRemove: () => handleDateRangeChange(null, null)
      });
    }

    return tags;
  };

  // 渲染高级筛选对话框
  const renderAdvancedFilters = () =>
  <Dialog open={showAdvanced} onOpenChange={setShowAdvanced}>
      <DialogTrigger asChild>
        <Button
        variant="outline"
        size="sm"
        className={cn(showAdvanced && "bg-blue-50 border-blue-200")}>

          <Filter className="mr-2 h-4 w-4" />
          高级筛选
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>高级筛选</DialogTitle>
        </DialogHeader>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* 状态筛选 */}
          <div>
            <Label>用户状态</Label>
            <Select value={filters.status} onValueChange={handleStatusChange}>
              <SelectTrigger>
                <SelectValue placeholder="选择状态" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="__all__">全部状态</SelectItem>
                {Object.entries(userStatusConfigs).map(([key, config]) =>
              <SelectItem key={key} value={key}>
                    <div className="flex items-center gap-2">
                      <span className={cn("w-2 h-2 rounded-full", config.color)} />
                      {config.label}
                    </div>
              </SelectItem>
              )}
              </SelectContent>
            </Select>
          </div>

          {/* 用户类型筛选 */}
          <div>
            <Label>用户类型</Label>
            <Select value={filters.userType} onValueChange={handleUserTypeChange}>
              <SelectTrigger>
                <SelectValue placeholder="选择类型" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="__all__">全部类型</SelectItem>
                {Object.entries(userTypeConfigs).map(([key, config]) =>
              <SelectItem key={key} value={key}>
                    <div className="flex items-center gap-2">
                      <span>{config.icon}</span>
                      {config.label}
                    </div>
              </SelectItem>
              )}
              </SelectContent>
            </Select>
          </div>

          {/* 部门筛选 */}
          <div>
            <Label>所属部门</Label>
            <Select value={filters.department} onValueChange={handleDepartmentChange}>
              <SelectTrigger>
                <SelectValue placeholder="选择部门" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="__all__">全部部门</SelectItem>
                {Object.entries(departmentConfigs).map(([key, config]) =>
              <SelectItem key={key} value={key}>
                    <div className="flex items-center gap-2">
                      <span>{config.icon}</span>
                      {config.label}
                    </div>
              </SelectItem>
              )}
              </SelectContent>
            </Select>
          </div>

          {/* 角色筛选 */}
          <div>
            <Label>用户角色</Label>
            <Select value={filters.role} onValueChange={handleRoleChange}>
              <SelectTrigger>
                <SelectValue placeholder="选择角色" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="__all__">全部角色</SelectItem>
                {Object.entries(userRoleConfigs).map(([key, config]) =>
              <SelectItem key={key} value={key}>
                    <div className="flex items-center gap-2">
                      <span>{config.icon}</span>
                      {config.label}
                    </div>
              </SelectItem>
              )}
              </SelectContent>
            </Select>
          </div>

          {/* 积分范围筛选 */}
          <div className="md:col-span-2">
            <Label>积分范围</Label>
            <div className="flex gap-2">
              <Input
              placeholder="最小积分"
              type="number"
              value={filters.minCredits}
              onChange={(e) => {
                const newFilters = { ...filters };
                newFilters.minCredits = e.target.value;
                setFilters(newFilters);
                onFiltersChange?.(newFilters);
              }} />

              <span className="flex items-center text-muted-foreground">-</span>
              <Input
              placeholder="最大积分"
              type="number"
              value={filters.maxCredits}
              onChange={(e) => {
                const newFilters = { ...filters };
                newFilters.maxCredits = e.target.value;
                setFilters(newFilters);
                onFiltersChange?.(newFilters);
              }} />

            </div>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={handleResetFilters}>
            重置
          </Button>
          <Button onClick={() => setShowAdvanced(false)}>
            应用筛选
          </Button>
        </DialogFooter>
      </DialogContent>
  </Dialog>;


  // 渲染批量操作
  const _renderBulkActions = () =>
  <Dialog open={showBulkActions} onOpenChange={setShowBulkActions}>
      <DialogTrigger asChild>
        <Button
        variant="outline"
        size="sm"
        disabled={selectedUsers.length === 0}>

          批量操作 ({selectedUsers.length})
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>批量操作</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-2">
            <Button variant="outline" disabled>
              批量启用
            </Button>
            <Button variant="outline" disabled>
              批量禁用
            </Button>
            <Button variant="outline" disabled>
              批量重置密码
            </Button>
            <Button variant="outline" disabled>
              批量删除
            </Button>
          </div>
          <Button
          variant="destructive"
          disabled
          className="col-span-2">

            批量删除选中用户
          </Button>
        </div>
      </DialogContent>
  </Dialog>;


  // 检查是否有活跃筛选
  const hasActiveFilters = Object.values(filters).some((value) =>
  value !== null && value !== "" && value !== undefined
  );

  return (
    <div className={cn("space-y-4", className)}>
      {/* 搜索栏 */}
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
          <Input
            placeholder="搜索用户名、邮箱、工号..."
            value={filters.search}
            onChange={(e) => handleSearch(e.target.value)}
            className="pl-10" />

        </div>

        <div className="flex gap-2">
          {renderAdvancedFilters()}
          {showExportOptions &&
          <>
              <Button variant="outline" size="sm" onClick={handleImport}>
                <Upload className="mr-2 h-4 w-4" />
                导入
              </Button>
              <Button variant="outline" size="sm" onClick={() => handleExport("excel")}>
                <Download className="mr-2 h-4 w-4" />
                导出
              </Button>
          </>
          }
          {hasActiveFilters &&
          <Button variant="outline" size="sm" onClick={handleClearFilters}>
              <RotateCcw className="mr-2 h-4 w-4" />
              清除
          </Button>
          }
        </div>
      </div>

      {/* 筛选标签 */}
      {renderFilterTags().length > 0 &&
      <div className="flex flex-wrap gap-2">
          {renderFilterTags().map((tag, index) =>
        <Badge
          key={index}
          variant="secondary"
          className="cursor-pointer hover:bg-red-100"
          onClick={tag.onRemove}>

              {tag.label}
              <X className="ml-1 h-3 w-3" />
        </Badge>
        )}
      </div>
      }

      {/* 快速筛选 */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-2">
        <Button
          variant={filters.status === "ACTIVE" ? "default" : "outline"}
          size="sm"
          onClick={() => handleStatusChange(filters.status === "ACTIVE" ? "" : "ACTIVE")}>

          <CheckCircle className="mr-1 h-3 w-3" />
          启用 ({filters.status === "ACTIVE" ? "✓" : ""})
        </Button>
        <Button
          variant={filters.status === "INACTIVE" ? "default" : "outline"}
          size="sm"
          onClick={() => handleStatusChange(filters.status === "INACTIVE" ? "" : "INACTIVE")}>

          <UserX className="mr-1 h-3 w-3" />
          禁用 ({filters.status === "INACTIVE" ? "✓" : ""})
        </Button>
        <Button
          variant={filters.status === "PENDING" ? "default" : "outline"}
          size="sm"
          onClick={() => handleStatusChange(filters.status === "PENDING" ? "" : "PENDING")}>

          <Clock className="mr-1 h-3 w-3" />
          待审核 ({filters.status === "PENDING" ? "✓" : ""})
        </Button>
        <Button
          variant={filters.department ? "default" : "outline"}
          size="sm"
          onClick={() => handleDepartmentChange(filters.department ? "" : "ENGINEERING")}>

          <Building2 className="mr-1 h-3 w-3" />
          工程
        </Button>
        <Button
          variant={filters.role ? "default" : "outline"}
          size="sm"
          onClick={() => handleRoleChange(filters.role ? "" : "SUPER_ADMIN")}>

          <Shield className="mr-1 h-3 w-3" />
          管理员
        </Button>
        <Button
          variant={filters.userType ? "default" : "outline"}
          size="sm"
          onClick={() => handleUserTypeChange(filters.userType ? "" : "INTERNAL")}>

          <User className="mr-1 h-3 w-3" />
          内部用户
        </Button>
      </div>

      {/* 排序选项 */}
      <div className="flex items-center gap-2">
        <Label className="text-sm">排序:</Label>
        <Select value={filters.sortBy + '_' + filters.sortOrder} onValueChange={handleSortChange}>
          <SelectTrigger className="w-48">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {userSortConfigs.map((config) =>
            <SelectItem key={config.value} value={config.value}>
                {config.label}
            </SelectItem>
            )}
          </SelectContent>
        </Select>
      </div>
    </div>);

}