/**
 * AlertList - Alert list with batch actions, items, and pagination
 */

import { motion } from "framer-motion";
import { AlertTriangle, Download } from "lucide-react";
import {
  Card,
  CardContent } from
"../../components/ui/card";
import { Button } from "../../components/ui/button";
import { EmptyState } from "../../components/common";
import { staggerContainer } from "../../lib/animations";
import AlertListItem from "./AlertListItem";

export default function AlertList({
  filteredAlerts,
  selectedAlerts,
  setSelectedAlerts,
  searchQuery,
  selectedLevel,
  selectedStatus,
  page,
  setPage,
  total,
  pageSize,
  navigate,
  handleBatchAcknowledge,
  handleBatchResolve,
  handleExportExcel,
  handleExportPdf,
  handleAcknowledge,
  handleViewDetail,
  handleSelectOne,
  setSelectedAlert,
  setShowResolveDialog
}) {
  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible">

      {filteredAlerts.length === 0 ?
      <Card>
          <CardContent className="p-8">
            <EmptyState
            icon={AlertTriangle}
            title="暂无预警"
            description={searchQuery || selectedLevel !== "ALL" || selectedStatus !== "ALL" ? "没有找到匹配的预警" : "系统运行正常，暂无预警"}
            action={
            <Button
              onClick={() => navigate('/alerts/create')}
              className="mt-4">

                  <AlertTriangle className="h-4 w-4 mr-2" />
                  创建测试预警
            </Button>
            } />

          </CardContent>
      </Card> :

      <>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">预警列表</h3>
                <div className="flex items-center gap-2">
                  {selectedAlerts.size > 0 &&
                <>
                      <Button
                    size="sm"
                    onClick={handleBatchAcknowledge}
                    className="bg-blue-500 hover:bg-blue-600">

                        批量确认 ({selectedAlerts.size})
                      </Button>
                      <Button
                    size="sm"
                    onClick={handleBatchResolve}
                    className="bg-emerald-500 hover:bg-emerald-600">

                        批量解决 ({selectedAlerts.size})
                      </Button>
                </>
                }
                  <Button
                  size="sm"
                  onClick={() =>
                  setSelectedAlerts(
                    new Set((filteredAlerts || []).map((alert) => alert.id))
                  )
                  }
                  variant="outline">

                    {selectedAlerts.size === filteredAlerts.length ?
                  "取消全选" :
                  "全选"}
                  </Button>
                  <div className="flex gap-1">
                    <Button
                    size="sm"
                    onClick={handleExportExcel}
                    variant="outline">

                      <Download className="h-4 w-4 mr-2" />
                      Excel
                    </Button>
                    <Button
                    size="sm"
                    onClick={handleExportPdf}
                    variant="outline">

                      <Download className="h-4 w-4 mr-2" />
                      PDF
                    </Button>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 预警列表内容 */}
          <div className="space-y-4">
          {(filteredAlerts || []).map((alert, index) => (
            <AlertListItem
              key={alert.id}
              alert={alert}
              index={index}
              isSelected={selectedAlerts.has(alert.id)}
              onSelect={handleSelectOne}
              onAcknowledge={handleAcknowledge}
              onResolve={(alert) => {
                setSelectedAlert(alert);
                setShowResolveDialog(true);
              }}
              onViewDetail={handleViewDetail} />
          ))}
          </div>
      </>
      }

      {/* 分页 */}
      {total > pageSize &&
      <div className="flex justify-center items-center gap-2 mt-6">
          <Button
          variant="outline"
          onClick={() => setPage((prev) => Math.max(1, prev - 1))}
          disabled={page <= 1}>

            上一页
          </Button>
          <span className="text-sm text-slate-400">
            第 {page} 页，共 {Math.ceil(total / pageSize)} 页
          </span>
          <Button
          variant="outline"
          onClick={() => setPage((prev) => prev + 1)}
          disabled={page >= Math.ceil(total / pageSize)}>

            下一页
          </Button>
      </div>
      }
    </motion.div>
  );
}
