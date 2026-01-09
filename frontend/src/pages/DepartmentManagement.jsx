import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  Plus,
  Search,
  Edit3,
  Eye,
  Building2,
  Users,
  ChevronRight,
  ChevronDown,
  FolderTree,
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
  DialogFooter,
} from '../components/ui/dialog';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { cn } from '../lib/utils';
import { fadeIn, staggerContainer } from '../lib/animations';
import { orgApi } from '../services/api';

// 部门树节点组件
function DepartmentTreeNode({ dept, level = 0, onEdit, onView, onSelect }) {
  const [expanded, setExpanded] = useState(level < 2); // 默认展开前两级

  return (
    <div>
      <div
        className={cn(
          'flex items-center gap-2 p-2 rounded hover:bg-muted/50 cursor-pointer',
          level > 0 && 'ml-4'
        )}
        style={{ paddingLeft: `${level * 20 + 8}px` }}
      >
        {dept.children && dept.children.length > 0 ? (
          <button
            onClick={() => setExpanded(!expanded)}
            className="p-1 hover:bg-muted rounded"
          >
            {expanded ? (
              <ChevronDown className="h-4 w-4" />
            ) : (
              <ChevronRight className="h-4 w-4" />
            )}
          </button>
        ) : (
          <div className="w-6" />
        )}
        <Building2 className="h-4 w-4 text-muted-foreground" />
        <span className="flex-1 font-medium">{dept.dept_name}</span>
        <Badge variant="outline" className="text-xs">
          {dept.dept_code}
        </Badge>
        {dept.manager_name && (
          <Badge variant="secondary" className="text-xs">
            {dept.manager_name}
          </Badge>
        )}
        <div className="flex items-center space-x-1">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onView(dept.id)}
          >
            <Eye className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onEdit(dept.id)}
          >
            <Edit3 className="h-4 w-4" />
          </Button>
        </div>
      </div>
      {expanded && dept.children && dept.children.length > 0 && (
        <div>
          {dept.children.map((child) => (
            <DepartmentTreeNode
              key={child.id}
              dept={child}
              level={level + 1}
              onEdit={onEdit}
              onView={onView}
              onSelect={onSelect}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export default function DepartmentManagement() {
  const [departments, setDepartments] = useState([]);
  const [departmentTree, setDepartmentTree] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [selectedDepartment, setSelectedDepartment] = useState(null);
  const [viewMode, setViewMode] = useState('tree'); // 'tree' or 'list'

  const [newDepartment, setNewDepartment] = useState({
    dept_code: '',
    dept_name: '',
    parent_id: null,
    manager_id: null,
    sort_order: 0,
    is_active: true,
  });

  const [editDepartment, setEditDepartment] = useState(null);

  // 加载部门列表
  const loadDepartments = async () => {
    setLoading(true);
    try {
      const response = await orgApi.departments({ skip: 0, limit: 1000 });
      setDepartments(response.data || []);
    } catch (error) {
      alert('加载部门列表失败: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  // 加载部门树
  const loadDepartmentTree = async () => {
    setLoading(true);
    try {
      const response = await orgApi.departmentTree({ is_active: true });
      setDepartmentTree(response.data || []);
    } catch (error) {
      alert('加载部门树失败: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (viewMode === 'tree') {
      loadDepartmentTree();
    } else {
      loadDepartments();
    }
  }, [viewMode]);

  const handleCreateChange = (e) => {
    const { name, value } = e.target;
    setNewDepartment((prev) => ({ ...prev, [name]: value }));
  };

  const handleEditChange = (e) => {
    const { name, value } = e.target;
    setEditDepartment((prev) => ({ ...prev, [name]: value }));
  };

  const handleCreateSubmit = async () => {
    try {
      const data = {
        ...newDepartment,
        parent_id: newDepartment.parent_id ? parseInt(newDepartment.parent_id) : null,
      };
      await orgApi.createDepartment(data);
      setShowCreateDialog(false);
      setNewDepartment({
        dept_code: '',
        dept_name: '',
        parent_id: null,
        manager_id: null,
        sort_order: 0,
        is_active: true,
      });
      if (viewMode === 'tree') {
        loadDepartmentTree();
      } else {
        loadDepartments();
      }
    } catch (error) {
      alert('创建部门失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleEditSubmit = async () => {
    try {
      const data = {
        ...editDepartment,
        parent_id: editDepartment.parent_id ? parseInt(editDepartment.parent_id) : null,
      };
      await orgApi.updateDepartment(editDepartment.id, data);
      setShowEditDialog(false);
      setEditDepartment(null);
      if (viewMode === 'tree') {
        loadDepartmentTree();
      } else {
        loadDepartments();
      }
    } catch (error) {
      alert('更新部门失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleViewDetail = async (id) => {
    try {
      const response = await orgApi.getDepartment(id);
      setSelectedDepartment(response.data);
      setShowDetailDialog(true);
    } catch (error) {
      alert('获取部门详情失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleEdit = async (id) => {
    try {
      const response = await orgApi.getDepartment(id);
      setEditDepartment(response.data);
      setShowEditDialog(true);
    } catch (error) {
      alert('获取部门信息失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  // 扁平化部门列表用于选择父部门
  const flattenDepartments = (depts, result = []) => {
    depts.forEach(dept => {
      result.push(dept);
      if (dept.children && dept.children.length > 0) {
        flattenDepartments(dept.children, result);
      }
    });
    return result;
  };

  const flatDepartments = viewMode === 'tree' ? flattenDepartments(departmentTree) : departments;

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      <PageHeader
        title="部门管理"
        description="管理系统部门信息，包括创建、编辑、查看部门树等操作。"
        actions={
          <div className="flex items-center space-x-2">
            <Button
              variant={viewMode === 'tree' ? 'default' : 'outline'}
              onClick={() => setViewMode('tree')}
            >
              <FolderTree className="mr-2 h-4 w-4" /> 树形视图
            </Button>
            <Button
              variant={viewMode === 'list' ? 'default' : 'outline'}
              onClick={() => setViewMode('list')}
            >
              <Building2 className="mr-2 h-4 w-4" /> 列表视图
            </Button>
            <Button onClick={() => setShowCreateDialog(true)}>
              <Plus className="mr-2 h-4 w-4" /> 新增部门
            </Button>
          </div>
        }
      />

      <motion.div variants={fadeIn}>
        <Card>
          <CardHeader>
            <CardTitle>{viewMode === 'tree' ? '部门树' : '部门列表'}</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="p-4 text-center text-muted-foreground">加载中...</div>
            ) : viewMode === 'tree' ? (
              <div className="space-y-1">
                {departmentTree.length === 0 ? (
                  <p className="p-4 text-center text-muted-foreground">暂无部门数据</p>
                ) : (
                  departmentTree.map((dept) => (
                    <DepartmentTreeNode
                      key={dept.id}
                      dept={dept}
                      level={0}
                      onEdit={handleEdit}
                      onView={handleViewDetail}
                      onSelect={() => {}}
                    />
                  ))
                )}
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-border">
                  <thead>
                    <tr className="bg-muted/50">
                      <th className="px-4 py-2 text-left text-sm font-semibold text-foreground">部门编码</th>
                      <th className="px-4 py-2 text-left text-sm font-semibold text-foreground">部门名称</th>
                      <th className="px-4 py-2 text-left text-sm font-semibold text-foreground">层级</th>
                      <th className="px-4 py-2 text-left text-sm font-semibold text-foreground">负责人</th>
                      <th className="px-4 py-2 text-left text-sm font-semibold text-foreground">状态</th>
                      <th className="px-4 py-2 text-left text-sm font-semibold text-foreground">操作</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {departments.map((dept) => (
                      <tr key={dept.id}>
                        <td className="px-4 py-2 text-sm text-foreground font-mono">{dept.dept_code}</td>
                        <td className="px-4 py-2 text-sm text-foreground">{dept.dept_name}</td>
                        <td className="px-4 py-2 text-sm text-muted-foreground">L{dept.level || 1}</td>
                        <td className="px-4 py-2 text-sm text-muted-foreground">{dept.manager?.name || '-'}</td>
                        <td className="px-4 py-2 text-sm">
                          <Badge variant={dept.is_active ? 'default' : 'secondary'}>
                            {dept.is_active ? '启用' : '禁用'}
                          </Badge>
                        </td>
                        <td className="px-4 py-2 text-sm">
                          <div className="flex items-center space-x-2">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleViewDetail(dept.id)}
                            >
                              <Eye className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleEdit(dept.id)}
                            >
                              <Edit3 className="h-4 w-4" />
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>

      {/* Create Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="sm:max-w-[600px]">
          <DialogHeader>
            <DialogTitle>新增部门</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="create-dept-code" className="text-right">部门编码 *</Label>
              <Input
                id="create-dept-code"
                name="dept_code"
                value={newDepartment.dept_code}
                onChange={handleCreateChange}
                className="col-span-3"
                required
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="create-dept-name" className="text-right">部门名称 *</Label>
              <Input
                id="create-dept-name"
                name="dept_name"
                value={newDepartment.dept_name}
                onChange={handleCreateChange}
                className="col-span-3"
                required
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="create-parent-id" className="text-right">父部门</Label>
              <Select
                value={newDepartment.parent_id ? String(newDepartment.parent_id) : ''}
                onValueChange={(value) =>
                  setNewDepartment((prev) => ({ ...prev, parent_id: value || null }))
                }
              >
                <SelectTrigger className="col-span-3">
                  <SelectValue placeholder="选择父部门（可选）" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">无（顶级部门）</SelectItem>
                  {flatDepartments
                    .filter(d => !editDepartment || d.id !== editDepartment.id)
                    .map((dept) => (
                      <SelectItem key={dept.id} value={String(dept.id)}>
                        {dept.dept_name} ({dept.dept_code})
                      </SelectItem>
                    ))}
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="create-sort-order" className="text-right">排序</Label>
              <Input
                id="create-sort-order"
                name="sort_order"
                type="number"
                value={newDepartment.sort_order}
                onChange={handleCreateChange}
                className="col-span-3"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
              取消
            </Button>
            <Button onClick={handleCreateSubmit}>保存</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Dialog */}
      <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
        <DialogContent className="sm:max-w-[600px]">
          <DialogHeader>
            <DialogTitle>编辑部门</DialogTitle>
          </DialogHeader>
          {editDepartment && (
            <div className="grid gap-4 py-4">
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="edit-dept-name" className="text-right">部门名称</Label>
                <Input
                  id="edit-dept-name"
                  name="dept_name"
                  value={editDepartment.dept_name || ''}
                  onChange={handleEditChange}
                  className="col-span-3"
                />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="edit-parent-id" className="text-right">父部门</Label>
                <Select
                  value={editDepartment.parent_id ? String(editDepartment.parent_id) : ''}
                  onValueChange={(value) =>
                    setEditDepartment((prev) => ({ ...prev, parent_id: value || null }))
                  }
                >
                  <SelectTrigger className="col-span-3">
                    <SelectValue placeholder="选择父部门（可选）" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">无（顶级部门）</SelectItem>
                    {flatDepartments
                      .filter(d => d.id !== editDepartment.id)
                      .map((dept) => (
                        <SelectItem key={dept.id} value={String(dept.id)}>
                          {dept.dept_name} ({dept.dept_code})
                        </SelectItem>
                      ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="edit-sort-order" className="text-right">排序</Label>
                <Input
                  id="edit-sort-order"
                  name="sort_order"
                  type="number"
                  value={editDepartment.sort_order || 0}
                  onChange={handleEditChange}
                  className="col-span-3"
                />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="edit-is-active" className="text-right">状态</Label>
                <Select
                  value={editDepartment.is_active ? 'active' : 'inactive'}
                  onValueChange={(value) =>
                    setEditDepartment((prev) => ({ ...prev, is_active: value === 'active' }))
                  }
                >
                  <SelectTrigger className="col-span-3">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="active">启用</SelectItem>
                    <SelectItem value="inactive">禁用</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowEditDialog(false)}>
              取消
            </Button>
            <Button onClick={handleEditSubmit}>保存</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Detail Dialog */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="sm:max-w-[600px]">
          <DialogHeader>
            <DialogTitle>部门详情</DialogTitle>
          </DialogHeader>
          {selectedDepartment && (
            <div className="grid gap-4 py-4 text-sm">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-muted-foreground">部门编码</Label>
                  <p className="font-medium font-mono">{selectedDepartment.dept_code}</p>
                </div>
                <div>
                  <Label className="text-muted-foreground">部门名称</Label>
                  <p className="font-medium">{selectedDepartment.dept_name}</p>
                </div>
                <div>
                  <Label className="text-muted-foreground">层级</Label>
                  <p className="font-medium">L{selectedDepartment.level || 1}</p>
                </div>
                <div>
                  <Label className="text-muted-foreground">负责人</Label>
                  <p className="font-medium">{selectedDepartment.manager?.name || '-'}</p>
                </div>
                <div>
                  <Label className="text-muted-foreground">状态</Label>
                  <p className="font-medium">
                    <Badge variant={selectedDepartment.is_active ? 'default' : 'secondary'}>
                      {selectedDepartment.is_active ? '启用' : '禁用'}
                    </Badge>
                  </p>
                </div>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button onClick={() => setShowDetailDialog(false)}>关闭</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </motion.div>
  );
}



