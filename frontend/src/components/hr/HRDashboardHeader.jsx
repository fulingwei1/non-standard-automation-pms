/**
 * HRDashboardHeader Component
 * HR Dashboard 页面头部组件
 */
import { useState } from "react";
import { motion } from "framer-motion";
import { PageHeader } from "../layout";
import {
  Button,
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger } from
"../ui";
import {
  UserPlus,
  Award,
  RefreshCw,
  MoreVertical,
  FileSpreadsheet,
  Printer,
  Share2,
  Settings } from
"lucide-react";
import { cn } from "../../lib/utils";
import { toast } from "../ui/toast";
import { fadeIn } from "../../lib/animations";

export default function HRDashboardHeader({
  mockHRStats,
  refreshing,
  onRefresh,
  onExportReport
}) {
  const [_selectedTab, setSelectedTab] = useState(null);
  const handlePrint = () => {
    window.print();
  };

  const handleShare = async () => {
    try {
      const url = window.location.href;
      await navigator.clipboard.writeText(url);
      toast.success("链接已复制到剪贴板");
    } catch (error) {
      console.error("分享失败:", error);
      toast.error("分享失败: " + error.message);
    }
  };

  return (
    <PageHeader
      title="人事管理"
      description={`在职员工: ${mockHRStats.activeEmployees}人 | 本月新增: ${mockHRStats.newEmployeesThisMonth}人 | 绩效完成率: ${mockHRStats.performanceCompletionRate}%`}
      actions={
      <motion.div variants={fadeIn} className="flex gap-2">
          <Button
          variant="outline"
          size="sm"
          className="flex items-center gap-2"
          onClick={() => {
            setSelectedTab("recruitment");
            // TODO: 打开新建招聘对话框
          }}>

            <UserPlus className="w-4 h-4" />
            新建招聘
          </Button>
          <Button
          variant="outline"
          size="sm"
          className="flex items-center gap-2"
          onClick={() => {
            setSelectedTab("performance");
            // TODO: 跳转到绩效管理页面
          }}>

            <Award className="w-4 h-4" />
            绩效管理
          </Button>
          <Button
          variant="outline"
          size="sm"
          className="flex items-center gap-2"
          disabled={refreshing}
          onClick={onRefresh}>

            <RefreshCw
            className={cn("w-4 h-4", refreshing && "animate-spin")} />

            刷新
          </Button>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
              variant="outline"
              size="sm"
              className="flex items-center gap-2">

                <MoreVertical className="w-4 h-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-48">
              <DropdownMenuItem onClick={onExportReport}>
                <FileSpreadsheet className="w-4 h-4 mr-2" />
                导出报表
              </DropdownMenuItem>
              <DropdownMenuItem onClick={handlePrint}>
                <Printer className="w-4 h-4 mr-2" />
                打印
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={handleShare}>
                <Share2 className="w-4 h-4 mr-2" />
                分享
              </DropdownMenuItem>
              <DropdownMenuItem
              onClick={() => {

                // TODO: Implement settings
              }}>
                <Settings className="w-4 h-4 mr-2" />
                设置
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </motion.div>
      } />);


}
