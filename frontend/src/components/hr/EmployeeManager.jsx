/**
 * Employee Manager Component
 * 员工管理组件
 */

import { useState } from "react";
import { Badge } from "../../components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { 
  Dialog, 
  DialogContent, 
  DialogHeader, 
  DialogTitle, 
  DialogBody, 
  DialogFooter 
} from "../../components/ui/dialog";
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from "../../components/ui/select";
import { 
  Eye, 
  Edit, 
  Plus, 
  Search, 
  Filter,
  Users,
  UserPlus,
  Calendar,
  Mail,
  Phone,
  Building2,
  MapPin
} from "lucide-react";
import { 
  employeeStatusConfigs,
  employeeTypeConfigs,
  departmentConfigs,
  positionLevelConfigs,
  getEmployeeStatusConfig,
  getDepartmentConfig,
  formatEmployeeStatus,
  formatDepartment
} from "./hrConstants";
import { cn, formatDate } from "../../lib/utils";

export function EmployeeManager({ 
  employees, 
  loading, 
  onViewEmployee, 
  onEditEmployee,
  onCreateEmployee
}) {
  const [searchTerm, setSearchTerm] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  const [filterDepartment, setFilterDepartment] = useState("");
  const [selectedEmployee, setSelectedEmployee] = useState(null);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [showCreateDialog, setShowCreateDialog] = useState(false);

  // 过滤员工
  const filteredEmployees = employees?.filter(employee => {
    if (searchTerm && !employee.name?.toLowerCase().includes(searchTerm.toLowerCase()) && 
        !employee.employee_id?.toLowerCase().includes(searchTerm.toLowerCase())) {
      return false;
    }
    if (filterStatus && employee.status !== filterStatus) {
      return false;
    }
    if (filterDepartment && employee.department !== filterDepartment) {
      return false;
    }
    return true;
  }) || [];

  const handleViewDetail = (employee) => {
    setSelectedEmployee(employee);
    setShowDetailDialog(true);
    if (onViewEmployee) {
      onViewEmployee(employee);
    }
  };

  const handleEdit = (employee) => {
    setSelectedEmployee(employee);
    if (onEditEmployee) {
      onEditEmployee(employee);
    }
  };

  const handleCreate = () => {
    setShowCreateDialog(true);
    if (onCreateEmployee) {
      onCreateEmployee();
    }
  };

  return (
    <>
      {/* 工具栏 */}
      <Card className="bg-surface-50 border-white/10">
        <CardHeader>
          <div className="flex justify-between items-center">
            <CardTitle className="flex items-center gap-2">
              <Users className="w-5 h-5" />
              员工管理
            </CardTitle>
            <Button onClick={handleCreate}>
              <Plus className="w-4 h-4 mr-2" />
              新增员工
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
              <Input
                placeholder="搜索员工姓名或工号..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            <Select value={filterStatus} onValueChange={setFilterStatus}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="员工状态" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">全部状态</SelectItem>
                {Object.entries(employeeStatusConfigs).map(([key, config]) => (
                  <SelectItem key={key} value={key}>
                    {config.icon} {config.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={filterDepartment} onValueChange={setFilterDepartment}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="部门" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">全部部门</SelectItem>
                {Object.entries(departmentConfigs).map(([key, config]) => (
                  <SelectItem key={key} value={key}>
                    {config.icon} {config.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* 员工列表 */}
      <Card className="bg-surface-50 border-white/10">
        <CardContent className="p-0">
          {loading ? (
            <div className="p-6 space-y-3">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="animate-pulse flex items-center gap-4 p-3 bg-slate-800 rounded">
                  <div className="w-10 h-10 bg-slate-700 rounded-full"></div>
                  <div className="flex-1 space-y-2">
                    <div className="h-4 bg-slate-700 rounded w-1/4"></div>
                    <div className="h-3 bg-slate-700 rounded w-1/6"></div>
                  </div>
                </div>
              ))}
            </div>
          ) : filteredEmployees.length === 0 ? (
            <div className="p-12 text-center text-slate-400">
              <Users className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>暂无员工数据</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-slate-700">
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                      员工信息
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                      部门
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                      职位
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                      状态
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                      入职日期
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                      操作
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-700">
                  {filteredEmployees.map((employee) => {
                    const statusConfig = getEmployeeStatusConfig(employee.status);
                    const deptConfig = getDepartmentConfig(employee.department);
                    
                    return (
                      <tr key={employee.id} className="hover:bg-slate-800/50 transition-colors">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-500 rounded-full flex items-center justify-center text-white font-medium">
                              {employee.name?.charAt(0) || "E"}
                            </div>
                            <div>
                              <div className="text-sm font-medium text-white">
                                {employee.name}
                              </div>
                              <div className="text-xs text-slate-400">
                                {employee.employee_id}
                              </div>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center gap-2">
                            <span>{deptConfig.icon}</span>
                            <span className="text-sm text-slate-300">
                              {formatDepartment(employee.department)}
                            </span>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-slate-300">
                            {employee.position}
                          </div>
                          <div className="text-xs text-slate-500">
                            {formatDepartment(employee.department)}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <Badge className={cn(statusConfig.color, statusConfig.textColor, "text-xs")}>
                            {statusConfig.icon} {formatEmployeeStatus(employee.status)}
                          </Badge>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-300">
                          {formatDate(employee.hire_date)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center gap-2">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleViewDetail(employee)}
                              className="hover:bg-blue-500/20 hover:text-blue-400"
                            >
                              <Eye className="w-4 h-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleEdit(employee)}
                              className="hover:bg-amber-500/20 hover:text-amber-400"
                            >
                              <Edit className="w-4 h-4" />
                            </Button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* 员工详情对话框 */}
      {selectedEmployee && (
        <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-3">
                <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-500 rounded-full flex items-center justify-center text-white font-medium">
                  {selectedEmployee.name?.charAt(0)}
                </div>
                <div>
                  <div className="text-xl font-semibold">{selectedEmployee.name}</div>
                  <div className="text-sm text-slate-400">{selectedEmployee.employee_id}</div>
                </div>
              </DialogTitle>
            </DialogHeader>
            <DialogBody>
              <div className="grid grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div>
                    <label className="text-sm font-medium text-slate-400">邮箱</label>
                    <div className="flex items-center gap-2 text-white">
                      <Mail className="w-4 h-4" />
                      {selectedEmployee.email}
                    </div>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-slate-400">电话</label>
                    <div className="flex items-center gap-2 text-white">
                      <Phone className="w-4 h-4" />
                      {selectedEmployee.phone}
                    </div>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-slate-400">地址</label>
                    <div className="flex items-center gap-2 text-white">
                      <MapPin className="w-4 h-4" />
                      {selectedEmployee.address}
                    </div>
                  </div>
                </div>
                <div className="space-y-4">
                  <div>
                    <label className="text-sm font-medium text-slate-400">部门</label>
                    <div className="flex items-center gap-2 text-white">
                      <Building2 className="w-4 h-4" />
                      {formatDepartment(selectedEmployee.department)}
                    </div>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-slate-400">职位</label>
                    <div className="text-white">{selectedEmployee.position}</div>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-slate-400">入职日期</label>
                    <div className="flex items-center gap-2 text-white">
                      <Calendar className="w-4 h-4" />
                      {formatDate(selectedEmployee.hire_date)}
                    </div>
                  </div>
                </div>
              </div>
            </DialogBody>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowDetailDialog(false)}>
                关闭
              </Button>
              <Button>
                编辑员工
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}
    </>
  );
}