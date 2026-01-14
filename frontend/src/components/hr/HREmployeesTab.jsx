import React from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { 
  Users, UserPlus, FileText, Search, 
  Mail, Phone, Calendar, Building 
} from 'lucide-react';
import { cn } from '@/lib/utils';

const fadeIn = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5 } }
};

/**
 * 员工表格行
 */
const EmployeeRow = ({ employee, onView, onEdit }) => (
  <tr className="border-b border-slate-700/50 hover:bg-slate-800/30 transition-colors">
    <td className="px-4 py-3">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center text-white font-semibold">
          {employee.name?.charAt(0) || 'U'}
        </div>
        <div>
          <p className="font-medium text-white">{employee.name}</p>
          <p className="text-xs text-slate-400">{employee.employee_code}</p>
        </div>
      </div>
    </td>
    <td className="px-4 py-3 text-slate-300">{employee.department || '-'}</td>
    <td className="px-4 py-3 text-slate-300">{employee.position || '-'}</td>
    <td className="px-4 py-3">
      <Badge className={cn(
        employee.is_active 
          ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/30" 
          : "bg-slate-500/20 text-slate-400 border-slate-500/30"
      )}>
        {employee.is_active ? '在职' : '离职'}
      </Badge>
    </td>
    <td className="px-4 py-3">
      <div className="flex items-center gap-2 text-sm text-slate-400">
        <Calendar className="w-4 h-4" />
        {employee.hire_date || '-'}
      </div>
    </td>
    <td className="px-4 py-3">
      <div className="flex items-center gap-2">
        <Button 
          variant="ghost" 
          size="sm"
          onClick={() => onView?.(employee)}
          className="text-primary hover:text-primary/80"
        >
          查看
        </Button>
        <Button 
          variant="ghost" 
          size="sm"
          onClick={() => onEdit?.(employee)}
          className="text-slate-400 hover:text-white"
        >
          编辑
        </Button>
      </div>
    </td>
  </tr>
);

/**
 * 员工管理标签页组件
 * 
 * @param {Object} props
 * @param {Array} props.employees - 员工列表
 * @param {Array} props.departments - 部门列表
 * @param {boolean} props.loading - 加载状态
 * @param {string} props.error - 错误信息
 * @param {string} props.searchKeyword - 搜索关键词
 * @param {string} props.filterDepartment - 筛选部门
 * @param {string} props.filterStatus - 筛选状态
 * @param {Function} props.onSearchChange - 搜索变化回调
 * @param {Function} props.onDepartmentChange - 部门筛选变化回调
 * @param {Function} props.onStatusChange - 状态筛选变化回调
 * @param {Function} props.onAddEmployee - 添加员工回调
 * @param {Function} props.onExport - 导出回调
 * @param {Function} props.onViewEmployee - 查看员工回调
 * @param {Function} props.onEditEmployee - 编辑员工回调
 */
export const HREmployeesTab = ({
  employees = [],
  departments = [],
  loading = false,
  error = null,
  searchKeyword = '',
  filterDepartment = 'all',
  filterStatus = 'all',
  onSearchChange,
  onDepartmentChange,
  onStatusChange,
  onAddEmployee,
  onExport,
  onViewEmployee,
  onEditEmployee
}) => {
  return (
    <motion.div
      variants={fadeIn}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-base">
              <Users className="h-5 w-5 text-blue-400" />
              员工管理
            </CardTitle>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                className="flex items-center gap-2"
                onClick={onExport}
              >
                <FileText className="w-4 h-4" />
                导出
              </Button>
              <Button
                className="flex items-center gap-2"
                onClick={onAddEmployee}
              >
                <UserPlus className="w-4 h-4" />
                新增员工
              </Button>
            </div>
          </div>
        </CardHeader>
        
        <CardContent className="space-y-4">
          {/* 搜索和筛选 */}
          <div className="flex items-center gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <Input
                placeholder="搜索员工姓名、工号、电话..."
                value={searchKeyword}
                onChange={(e) => onSearchChange?.(e.target.value)}
                className="bg-slate-800/40 border-slate-700/50 pl-10"
              />
            </div>
            <select
              value={filterDepartment}
              onChange={(e) => onDepartmentChange?.(e.target.value)}
              className="px-4 py-2 rounded-lg bg-slate-800/40 border border-slate-700/50 text-white text-sm"
            >
              <option value="all">全部部门</option>
              {departments.map((dept) => (
                <option key={dept.id} value={dept.dept_name}>
                  {dept.dept_name}
                </option>
              ))}
            </select>
            <select
              value={filterStatus}
              onChange={(e) => onStatusChange?.(e.target.value)}
              className="px-4 py-2 rounded-lg bg-slate-800/40 border border-slate-700/50 text-white text-sm"
            >
              <option value="all">全部状态</option>
              <option value="active">在职</option>
              <option value="inactive">离职</option>
            </select>
          </div>

          {/* 员工列表 */}
          {loading ? (
            <div className="text-center py-12 text-slate-400">
              加载中...
            </div>
          ) : error ? (
            <div className="text-center py-12">
              <p className="text-red-400 mb-4">{error}</p>
              <Button variant="outline" onClick={() => window.location.reload()}>
                重试
              </Button>
            </div>
          ) : employees.length === 0 ? (
            <div className="text-center py-12">
              <Users className="w-12 h-12 text-slate-600 mx-auto mb-4" />
              <p className="text-slate-400 mb-2">暂无员工数据</p>
              <p className="text-sm text-slate-500">
                {searchKeyword || filterDepartment !== 'all' || filterStatus !== 'all'
                  ? '没有找到符合条件的员工，请尝试调整筛选条件'
                  : '点击上方按钮添加新员工'}
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto rounded-lg border border-slate-700/50">
              <table className="w-full">
                <thead className="bg-slate-800/50">
                  <tr className="border-b border-slate-700/50">
                    <th className="px-4 py-3 text-left text-sm font-medium text-slate-400">员工</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-slate-400">部门</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-slate-400">职位</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-slate-400">状态</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-slate-400">入职日期</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-slate-400">操作</th>
                  </tr>
                </thead>
                <tbody>
                  {employees.map((employee) => (
                    <EmployeeRow
                      key={employee.id}
                      employee={employee}
                      onView={onViewEmployee}
                      onEdit={onEditEmployee}
                    />
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* 统计信息 */}
          {employees.length > 0 && (
            <div className="flex items-center justify-between pt-4 border-t border-slate-700/50">
              <p className="text-sm text-slate-400">
                共 <span className="font-semibold text-white">{employees.length}</span> 名员工
              </p>
              <p className="text-sm text-slate-400">
                在职 <span className="font-semibold text-emerald-400">
                  {employees.filter(e => e.is_active).length}
                </span> 人
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
};

export default HREmployeesTab;
