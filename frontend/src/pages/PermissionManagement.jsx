import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  Search,
  Shield,
  Filter,
  Eye,
  Users,
  Package,
  ChevronDown,
  ChevronRight,
  Key,
  FileText,
  Settings,
} from 'lucide-react';
import { PageHeader } from '../components/layout';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { cn } from '../lib/utils';
import { fadeIn } from '../lib/animations';
import { roleApi } from '../services/api';

export default function PermissionManagement() {
  const [permissions, setPermissions] = useState([]);
  const [roles, setRoles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchKeyword, setSearchKeyword] = useState('');
  const [filterModule, setFilterModule] = useState('all');
  const [expandedModules, setExpandedModules] = useState({});
  const [selectedPermission, setSelectedPermission] = useState(null);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [permissionRoles, setPermissionRoles] = useState([]);

  // 加载权限列表
  const loadPermissions = async () => {
    setLoading(true);
    try {
      let response;
      if (filterModule !== 'all') {
        // 如果指定了模块，需要传递module参数
        response = await roleApi.permissions({ module: filterModule });
      } else {
        response = await roleApi.permissions();
      }
      setPermissions(response.data || []);
    } catch (error) {
      console.error('加载权限列表失败:', error);
      alert('加载权限列表失败: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  // 加载角色列表
  const loadRoles = async () => {
    try {
      const response = await roleApi.list({ page_size: 1000 });
      setRoles(response.data.items || []);
    } catch (error) {
      console.error('加载角色列表失败:', error);
    }
  };

  useEffect(() => {
    loadPermissions();
    loadRoles();
  }, [filterModule]);

  // 获取所有模块列表
  const modules = Array.from(new Set(permissions.map(p => p.module).filter(Boolean))).sort();

  // 按模块分组权限
  const groupedPermissions = permissions.reduce((acc, permission) => {
    const module = permission.module || '其他';
    if (!acc[module]) {
      acc[module] = [];
    }
    acc[module].push(permission);
    return acc;
  }, {});

  // 过滤权限
  const filteredPermissions = Object.entries(groupedPermissions).reduce((acc, [module, perms]) => {
    const filtered = perms.filter(p => {
      if (!searchKeyword) return true;
      const keyword = searchKeyword.toLowerCase();
      return (
        p.permission_code?.toLowerCase().includes(keyword) ||
        p.permission_name?.toLowerCase().includes(keyword) ||
        p.description?.toLowerCase().includes(keyword)
      );
    });
    if (filtered.length > 0) {
      acc[module] = filtered;
    }
    return acc;
  }, {});

  // 切换模块展开/收起
  const toggleModule = (module) => {
    setExpandedModules(prev => ({
      ...prev,
      [module]: !prev[module],
    }));
  };

  // 查看权限详情
  const handleViewDetail = async (permission) => {
    setSelectedPermission(permission);
    setShowDetailDialog(true);
    
    // 查找拥有该权限的角色
    try {
      // 获取所有角色的详细信息（包含权限）
      const rolesWithPermission = [];
      for (const role of roles) {
        try {
          const roleDetail = await roleApi.get(role.id);
          // 后端返回的permissions是权限名称列表（List[str]）
          const rolePermissionNames = roleDetail.data?.permissions || [];
          // 通过权限名称匹配
          if (rolePermissionNames.includes(permission.permission_name) || 
              rolePermissionNames.includes(permission.permission_code)) {
            rolesWithPermission.push(role);
          }
        } catch (error) {
          console.warn(`获取角色 ${role.id} 详情失败:`, error);
        }
      }
      setPermissionRoles(rolesWithPermission);
    } catch (error) {
      console.error('加载权限关联角色失败:', error);
      setPermissionRoles([]);
    }
  };

  // 获取权限操作类型颜色
  const getActionColor = (action) => {
    const colors = {
      'read': 'bg-blue-500/10 text-blue-400',
      'create': 'bg-green-500/10 text-green-400',
      'update': 'bg-yellow-500/10 text-yellow-400',
      'delete': 'bg-red-500/10 text-red-400',
      'approve': 'bg-purple-500/10 text-purple-400',
      'submit': 'bg-cyan-500/10 text-cyan-400',
    };
    return colors[action?.toLowerCase()] || 'bg-gray-500/10 text-gray-400';
  };

  // 统计信息
  const stats = {
    total: permissions.length,
    modules: modules.length,
    active: permissions.filter(p => p.is_active).length,
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="权限管理"
        description="查看和管理系统中的所有权限配置"
        icon={Shield}
      />

      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400">权限总数</p>
                  <p className="text-2xl font-bold text-white mt-1">{stats.total}</p>
                </div>
                <Key className="h-8 w-8 text-blue-400" />
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400">模块数量</p>
                  <p className="text-2xl font-bold text-white mt-1">{stats.modules}</p>
                </div>
                <Package className="h-8 w-8 text-green-400" />
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400">启用权限</p>
                  <p className="text-2xl font-bold text-white mt-1">{stats.active}</p>
                </div>
                <Shield className="h-8 w-8 text-purple-400" />
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* 搜索和筛选 */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
              <Input
                placeholder="搜索权限编码、名称或描述..."
                value={searchKeyword}
                onChange={(e) => setSearchKeyword(e.target.value)}
                className="pl-10"
              />
            </div>
            <Select value={filterModule} onValueChange={setFilterModule}>
              <SelectTrigger className="w-full sm:w-[200px]">
                <Filter className="h-4 w-4 mr-2" />
                <SelectValue placeholder="选择模块" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">所有模块</SelectItem>
                {modules.map(module => (
                  <SelectItem key={module} value={module}>
                    {module}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* 权限列表 */}
      {loading ? (
        <Card>
          <CardContent className="pt-6">
            <div className="text-center py-8 text-slate-400">加载中...</div>
          </CardContent>
        </Card>
      ) : Object.keys(filteredPermissions).length === 0 ? (
        <Card>
          <CardContent className="pt-6">
            <div className="text-center py-8 text-slate-400">
              {searchKeyword ? '未找到匹配的权限' : '暂无权限数据'}
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {Object.entries(filteredPermissions).map(([module, perms]) => (
            <motion.div
              key={module}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
            >
              <Card>
                <CardHeader>
                  <div
                    className="flex items-center justify-between cursor-pointer"
                    onClick={() => toggleModule(module)}
                  >
                    <CardTitle className="flex items-center gap-2">
                      <Package className="h-5 w-5 text-blue-400" />
                      <span>{module}</span>
                      <Badge variant="secondary" className="ml-2">
                        {perms.length}
                      </Badge>
                    </CardTitle>
                    {expandedModules[module] !== false ? (
                      <ChevronDown className="h-5 w-5 text-slate-400" />
                    ) : (
                      <ChevronRight className="h-5 w-5 text-slate-400" />
                    )}
                  </div>
                </CardHeader>
                {expandedModules[module] !== false && (
                  <CardContent>
                    <div className="space-y-2">
                      {perms.map((permission) => (
                        <div
                          key={permission.id}
                          className="flex items-center justify-between p-3 rounded-lg bg-slate-800/50 hover:bg-slate-800 transition-colors"
                        >
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <Key className="h-4 w-4 text-slate-400" />
                              <span className="font-medium text-white">
                                {permission.permission_code}
                              </span>
                              {permission.action && (
                                <Badge
                                  className={cn('text-xs', getActionColor(permission.action))}
                                >
                                  {permission.action}
                                </Badge>
                              )}
                              {!permission.is_active && (
                                <Badge variant="destructive" className="text-xs">
                                  已禁用
                                </Badge>
                              )}
                            </div>
                            <p className="text-sm text-slate-400 ml-6">
                              {permission.permission_name}
                            </p>
                            {permission.description && (
                              <p className="text-xs text-slate-500 ml-6 mt-1">
                                {permission.description}
                              </p>
                            )}
                            {permission.resource && (
                              <div className="flex items-center gap-2 mt-2 ml-6">
                                <FileText className="h-3 w-3 text-slate-500" />
                                <span className="text-xs text-slate-500">
                                  资源: {permission.resource}
                                </span>
                              </div>
                            )}
                          </div>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleViewDetail(permission)}
                            className="ml-4"
                          >
                            <Eye className="h-4 w-4 mr-1" />
                            详情
                          </Button>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                )}
              </Card>
            </motion.div>
          ))}
        </div>
      )}

      {/* 权限详情对话框 */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Shield className="h-5 w-5" />
              权限详情
            </DialogTitle>
          </DialogHeader>
          {selectedPermission && (
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium text-slate-400">权限编码</label>
                <p className="text-white mt-1 font-mono">{selectedPermission.permission_code}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-slate-400">权限名称</label>
                <p className="text-white mt-1">{selectedPermission.permission_name}</p>
              </div>
              {selectedPermission.description && (
                <div>
                  <label className="text-sm font-medium text-slate-400">描述</label>
                  <p className="text-white mt-1">{selectedPermission.description}</p>
                </div>
              )}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-slate-400">所属模块</label>
                  <p className="text-white mt-1">{selectedPermission.module || '未分类'}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-slate-400">资源类型</label>
                  <p className="text-white mt-1">{selectedPermission.resource || '未指定'}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-slate-400">操作类型</label>
                  <p className="text-white mt-1">
                    {selectedPermission.action ? (
                      <Badge className={getActionColor(selectedPermission.action)}>
                        {selectedPermission.action}
                      </Badge>
                    ) : (
                      '未指定'
                    )}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-slate-400">状态</label>
                  <p className="text-white mt-1">
                    {selectedPermission.is_active ? (
                      <Badge className="bg-green-500/10 text-green-400">启用</Badge>
                    ) : (
                      <Badge variant="destructive">禁用</Badge>
                    )}
                  </p>
                </div>
              </div>
              {selectedPermission.created_at && (
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium text-slate-400">创建时间</label>
                    <p className="text-white mt-1">
                      {new Date(selectedPermission.created_at).toLocaleString('zh-CN')}
                    </p>
                  </div>
                  {selectedPermission.updated_at && (
                    <div>
                      <label className="text-sm font-medium text-slate-400">更新时间</label>
                      <p className="text-white mt-1">
                        {new Date(selectedPermission.updated_at).toLocaleString('zh-CN')}
                      </p>
                    </div>
                  )}
                </div>
              )}
              <div className="pt-4 border-t border-slate-700">
                <label className="text-sm font-medium text-slate-400 mb-2 block">
                  拥有此权限的角色
                </label>
                <div className="space-y-2 max-h-40 overflow-y-auto">
                  {permissionRoles.length > 0 ? (
                    permissionRoles.map((role) => (
                      <div
                        key={role.id}
                        className="flex items-center gap-2 p-2 rounded bg-slate-800/50"
                      >
                        <Users className="h-4 w-4 text-slate-400" />
                        <span className="text-sm text-white">{role.role_name}</span>
                        <Badge variant="secondary" className="ml-auto text-xs">
                          {role.role_code}
                        </Badge>
                      </div>
                    ))
                  ) : (
                    <p className="text-sm text-slate-500 text-center py-4">
                      暂无角色拥有此权限
                    </p>
                  )}
                </div>
                <p className="text-xs text-slate-500 mt-2">
                  提示：权限通常通过角色管理页面进行分配
                </p>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
