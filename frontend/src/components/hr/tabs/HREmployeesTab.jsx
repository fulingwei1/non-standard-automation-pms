/**
 * HREmployeesTab Component
 * 员工管理 Tab 组件
 */
import { motion } from "framer-motion";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Input,
  LoadingCard,
  ErrorMessage,
  EmptyState,
} from "../../ui";
import { Users, UserPlus, FileText, Eye, Edit } from "lucide-react";
import { cn } from "../../../lib/utils";
import { employeeApi } from "../../../services/api";

export default function HREmployeesTab({
  employees,
  departments,
  loading,
  error,
  searchKeyword,
  setSearchKeyword,
  filterDepartment,
  setFilterDepartment,
  filterStatus,
  setFilterStatus,
  loadEmployees,
  handleExportEmployeeList,
  setSelectedEmployee,
  setShowEmployeeDialog,
}) {
  return (
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
              title="导出员工列表"
              onClick={handleExportEmployeeList}
            >
              <FileText className="w-4 h-4" />
              导出
            </Button>
            <Button
              className="flex items-center gap-2"
              onClick={() => {
                setSelectedEmployee(null);
                setShowEmployeeDialog(true);
              }}
            >
              <UserPlus className="w-4 h-4" />
              新增员工
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Search and Filters */}
        <div className="flex items-center gap-4">
          <div className="flex-1">
            <Input
              placeholder="搜索员工姓名、工号、电话..."
              value={searchKeyword}
              onChange={(e) => setSearchKeyword(e.target.value)}
              className="bg-slate-800/40 border-slate-700/50"
            />
          </div>
          <select
            value={filterDepartment}
            onChange={(e) => setFilterDepartment(e.target.value)}
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
            onChange={(e) => setFilterStatus(e.target.value)}
            className="px-4 py-2 rounded-lg bg-slate-800/40 border border-slate-700/50 text-white text-sm"
          >
            <option value="all">全部状态</option>
            <option value="active">在职</option>
            <option value="inactive">离职</option>
          </select>
        </div>

        {/* Employee List */}
        {loading ? (
          <LoadingCard message="加载员工列表..." />
        ) : error ? (
          <ErrorMessage
            title="加载失败"
            message={error}
            onRetry={loadEmployees}
          />
        ) : employees.length === 0 ? (
          <EmptyState
            icon={Users}
            title="暂无员工数据"
            message={
              searchKeyword ||
              filterDepartment !== "all" ||
              filterStatus !== "all"
                ? "没有找到符合条件的员工，请尝试调整筛选条件"
                : "当前没有员工数据，点击上方按钮添加新员工"
            }
            action={() => {
              setSearchKeyword("");
              setFilterDepartment("all");
              setFilterStatus("all");
            }}
            actionLabel={
              searchKeyword ||
              filterDepartment !== "all" ||
              filterStatus !== "all"
                ? "清除筛选"
                : undefined
            }
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-800/40 border-b border-slate-700/50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">
                    工号
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">
                    姓名
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">
                    部门
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">
                    角色
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">
                    电话
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">
                    状态
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">
                    操作
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700/50">
                {employees.map((employee, index) => (
                  <motion.tr
                    key={employee.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.05 }}
                    className="hover:bg-slate-800/40"
                  >
                    <td className="px-6 py-4 text-sm font-semibold text-white">
                      {employee.employee_code || "-"}
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-300">
                      {employee.name}
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-300">
                      {employee.department || "-"}
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-300">
                      {employee.role || "-"}
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-300">
                      {employee.phone || "-"}
                    </td>
                    <td className="px-6 py-4">
                      <Badge
                        className={cn(
                          "text-xs",
                          employee.is_active
                            ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/30"
                            : "bg-slate-500/20 text-slate-400 border-slate-500/30",
                        )}
                      >
                        {employee.is_active ? "在职" : "离职"}
                      </Badge>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          title="查看详情"
                          className="hover:bg-blue-500/20 hover:text-blue-400"
                          onClick={async () => {
                            try {
                              const response = await employeeApi.get(
                                employee.id,
                              );
                              setSelectedEmployee(response.data);
                              setShowEmployeeDialog(true);
                            } catch (error) {
                              console.error("加载员工详情失败:", error);
                              // 如果API失败，使用列表中的数据
                              setSelectedEmployee(employee);
                              setShowEmployeeDialog(true);
                            }
                          }}
                        >
                          <Eye className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          title="编辑员工"
                          className="hover:bg-amber-500/20 hover:text-amber-400"
                          onClick={() => {
                            setSelectedEmployee(employee);
                            setShowEmployeeDialog(true);
                          }}
                        >
                          <Edit className="w-4 h-4" />
                        </Button>
                      </div>
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
