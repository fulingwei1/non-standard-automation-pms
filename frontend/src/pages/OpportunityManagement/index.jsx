/**
 * 商机管理页面 - 薄壳组件
 * 1,735 行单体拆分为: constants + hook + 4 个对话框组件
 */

import { motion } from "framer-motion";
import {
  Search, Filter, Plus, Target, DollarSign,
  User, Building2, CheckCircle2, Clock, Edit,
  Eye, FileText, LayoutGrid, List,
} from "lucide-react";
import { PageHeader } from "../../components/layout";
import {
  Card, CardContent, CardHeader, CardTitle,
  Button, Badge, Input,
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger,
} from "../../components/ui";
import { cn } from "../../lib/utils";
import { formatDateTime } from "@/lib/formatters";
import { stageConfig, isGatePassed, PAGE_SIZE } from "./constants";
import { useOpportunityManagement } from "./hooks/useOpportunityManagement";
import { CreateDialog } from "./components/CreateDialog";
import { GateDialog } from "./components/GateDialog";
import { DetailDialog } from "./components/DetailDialog";
import { ReviewDialog } from "./components/ReviewDialog";

export default function OpportunityManagement({ embedded = false }) {
  const ctx = useOpportunityManagement();

  return (
    <div className="space-y-6 p-6">
      {!embedded && (
        <PageHeader
          title="商机管理"
          description="管理销售商机，跟踪项目进展"
          action={
            <Button onClick={() => ctx.setShowCreateDialog(true)}>
              <Plus className="mr-2 h-4 w-4" />
              新建商机
            </Button>
          }
        />
      )}

      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">总商机数</p>
                <p className="text-2xl font-bold text-white">{ctx.stats.total}</p>
              </div>
              <Target className="h-8 w-8 text-blue-400" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">需求澄清</p>
                <p className="text-2xl font-bold text-white">{ctx.stats.discovery}</p>
              </div>
              <Clock className="h-8 w-8 text-blue-400" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">报价中</p>
                <p className="text-2xl font-bold text-white">{ctx.stats.proposal}</p>
              </div>
              <DollarSign className="h-8 w-8 text-amber-400" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">预估金额</p>
                <p className="text-2xl font-bold text-white">
                  {(ctx.stats.totalAmount / 10000).toFixed(1)}万
                </p>
              </div>
              <DollarSign className="h-8 w-8 text-emerald-400" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 筛选栏 */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col md:flex-row gap-4 items-center">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
              <Input
                placeholder="搜索商机编码、名称..."
                value={ctx.searchTerm || "unknown"}
                onChange={(e) => ctx.setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline">
                  <Filter className="mr-2 h-4 w-4" />
                  阶段: {ctx.stageFilter === "all" ? "全部" : stageConfig[ctx.stageFilter]?.label}
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent>
                <DropdownMenuItem onClick={() => ctx.setStageFilter("all")}>全部</DropdownMenuItem>
                {Object.entries(stageConfig).map(([key, config]) => (
                  <DropdownMenuItem key={key} onClick={() => ctx.setStageFilter(key)}>
                    {config.label}
                  </DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
            <div className="flex gap-2">
              <select
                value={ctx.customerFilter || "unknown"}
                onChange={(e) => ctx.setCustomerFilter(e.target.value)}
                className="px-3 py-1 border rounded text-sm bg-slate-900 text-slate-300"
              >
                <option value="all">客户: 全部</option>
                {(ctx.customers || []).map((customer) => (
                  <option key={customer.id} value={customer.id}>
                    {customer.customer_name}
                  </option>
                ))}
              </select>
              <select
                value={ctx.ownerFilter || "unknown"}
                onChange={(e) => ctx.setOwnerFilter(e.target.value)}
                className="px-3 py-1 border rounded text-sm bg-slate-900 text-slate-300"
              >
                <option value="all">负责人: 全部</option>
                {(ctx.owners || []).map((owner) => (
                  <option key={owner.id} value={owner.id}>
                    {owner.real_name || owner.username}
                  </option>
                ))}
              </select>
              <Button
                variant={ctx.viewMode === "grid" ? "default" : "outline"}
                size="icon"
                onClick={() => ctx.setViewMode("grid")}
              >
                <LayoutGrid className="h-4 w-4" />
              </Button>
              <Button
                variant={ctx.viewMode === "list" ? "default" : "outline"}
                size="icon"
                onClick={() => ctx.setViewMode("list")}
              >
                <List className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 商机列表 */}
      {ctx.loading ? (
        <div className="text-center py-12 text-slate-400">加载中...</div>
      ) : ctx.opportunities.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center">
            <p className="text-slate-400">暂无商机数据</p>
          </CardContent>
        </Card>
      ) : ctx.viewMode === "grid" ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {(ctx.opportunities || []).map((opp) => (
            <motion.div key={opp.id} whileHover={{ y: -4 }}>
              <Card className="h-full hover:border-blue-500 transition-colors">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <CardTitle className="text-lg">{opp.opp_code}</CardTitle>
                      <p className="text-sm text-slate-400 mt-1">{opp.opp_name}</p>
                    </div>
                    <Badge className={cn(stageConfig[opp.stage]?.color)}>
                      {stageConfig[opp.stage]?.label}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2 text-sm">
                    <div className="flex items-center gap-2 text-slate-300">
                      <span className="text-xs text-slate-400">阶段</span>
                      <select
                        value={opp.stage}
                        onChange={(e) => ctx.handleStageChange(opp, e.target.value)}
                        disabled={!!ctx.stageUpdating[opp.id]}
                        className="bg-slate-900 border border-slate-700 rounded-md px-2 py-1 text-xs text-white"
                      >
                        {Object.entries(stageConfig).map(([key, config]) => (
                          <option key={key} value={key || "unknown"}>
                            {config.label}
                          </option>
                        ))}
                      </select>
                      {ctx.stageUpdating[opp.id] && (
                        <span className="text-xs text-slate-500">更新中...</span>
                      )}
                    </div>
                    <div className="flex items-center gap-2 text-slate-300">
                      <Building2 className="h-4 w-4 text-slate-400" />
                      {opp.customer_name}
                    </div>
                    {opp.est_amount && (
                      <div className="flex items-center gap-2 text-slate-300">
                        <DollarSign className="h-4 w-4 text-slate-400" />
                        {parseFloat(opp.est_amount).toLocaleString()} 元
                      </div>
                    )}
                    {opp.owner_name && (
                      <div className="flex items-center gap-2 text-slate-300">
                        <User className="h-4 w-4 text-slate-400" />
                        负责人: {opp.owner_name}
                      </div>
                    )}
                  </div>
                  <div className="grid grid-cols-4 gap-2 mt-4">
                    <Button variant="outline" size="sm" onClick={() => ctx.handleViewDetail(opp)} className="w-full">
                      <Eye className="mr-2 h-4 w-4" />详情
                    </Button>
                    <Button variant="outline" size="sm" onClick={() => ctx.handleEdit(opp)} className="w-full">
                      <Edit className="mr-2 h-4 w-4" />编辑
                    </Button>
                    <Button variant="outline" size="sm" onClick={() => { ctx.setSelectedOpp(opp); ctx.setShowGateDialog(true); }} className="w-full">
                      <CheckCircle2 className="mr-2 h-4 w-4" />阶段门
                    </Button>
                    <Button
                      variant="outline" size="sm"
                      onClick={() => ctx.openReviewDialog(opp)}
                      className="w-full"
                      disabled={!isGatePassed(opp.gate_status)}
                      title={isGatePassed(opp.gate_status) ? "" : "阶段门未通过，无法申请评审"}
                    >
                      <FileText className="mr-2 h-4 w-4" />申请评审
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      ) : (
        <Card>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-slate-800">
                    <th className="text-left p-4 text-slate-400 text-sm">商机</th>
                    <th className="text-left p-4 text-slate-400 text-sm">客户</th>
                    <th className="text-left p-4 text-slate-400 text-sm">阶段</th>
                    <th className="text-left p-4 text-slate-400 text-sm">负责人</th>
                    <th className="text-left p-4 text-slate-400 text-sm">预估金额</th>
                    <th className="text-left p-4 text-slate-400 text-sm">创建时间</th>
                    <th className="text-left p-4 text-slate-400 text-sm">操作</th>
                  </tr>
                </thead>
                <tbody>
                  {(ctx.opportunities || []).map((opp) => (
                    <tr key={opp.id} className="border-b border-slate-800 hover:bg-slate-800/50">
                      <td className="p-4">
                        <div>
                          <div className="text-white font-medium">{opp.opp_name}</div>
                          <div className="text-xs text-slate-500">{opp.opp_code}</div>
                        </div>
                      </td>
                      <td className="p-4 text-slate-300">{opp.customer_name || "-"}</td>
                      <td className="p-4">
                        <div className="flex items-center gap-2">
                          <select
                            value={opp.stage}
                            onChange={(e) => ctx.handleStageChange(opp, e.target.value)}
                            disabled={!!ctx.stageUpdating[opp.id]}
                            className="bg-slate-900 border border-slate-700 rounded-md px-2 py-1 text-xs text-white"
                          >
                            {Object.entries(stageConfig).map(([key, config]) => (
                              <option key={key} value={key || "unknown"}>{config.label}</option>
                            ))}
                          </select>
                          {ctx.stageUpdating[opp.id] && (
                            <span className="text-xs text-slate-500">更新中...</span>
                          )}
                        </div>
                      </td>
                      <td className="p-4 text-blue-400">{opp.owner_name || "-"}</td>
                      <td className="p-4 text-slate-300">
                        {opp.est_amount ? `${parseFloat(opp.est_amount).toLocaleString()} 元` : "-"}
                      </td>
                      <td className="p-4 text-slate-400 text-sm">{formatDateTime(opp.created_at)}</td>
                      <td className="p-4">
                        <div className="flex gap-1">
                          <Button variant="ghost" size="sm" onClick={() => ctx.handleViewDetail(opp)} className="h-8 w-8 p-0">
                            <Eye className="h-4 w-4" />
                          </Button>
                          <Button variant="ghost" size="sm" onClick={() => ctx.handleEdit(opp)} className="h-8 w-8 p-0">
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button variant="ghost" size="sm" onClick={() => { ctx.setSelectedOpp(opp); ctx.setShowGateDialog(true); }} className="h-8 w-8 p-0 text-emerald-400">
                            <CheckCircle2 className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost" size="sm"
                            onClick={() => ctx.openReviewDialog(opp)}
                            className="h-8 w-8 p-0 text-violet-400"
                            disabled={!isGatePassed(opp.gate_status)}
                            title={isGatePassed(opp.gate_status) ? "" : "阶段门未通过，无法申请评审"}
                          >
                            <FileText className="h-4 w-4" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* 分页 */}
      {ctx.total > PAGE_SIZE && (
        <div className="flex justify-center gap-2">
          <Button variant="outline" disabled={ctx.page === 1} onClick={() => ctx.setPage(ctx.page - 1)}>
            上一页
          </Button>
          <span className="flex items-center px-4 text-slate-400">
            第 {ctx.page} 页，共 {Math.ceil(ctx.total / PAGE_SIZE)} 页
          </span>
          <Button variant="outline" disabled={ctx.page >= Math.ceil(ctx.total / PAGE_SIZE)} onClick={() => ctx.setPage(ctx.page + 1)}>
            下一页
          </Button>
        </div>
      )}

      {/* 对话框 */}
      <CreateDialog
        open={ctx.showCreateDialog}
        onOpenChange={ctx.setShowCreateDialog}
        formData={ctx.formData}
        setFormData={ctx.setFormData}
        customers={ctx.customers}
        onCreate={ctx.handleCreate}
      />
      <GateDialog
        open={ctx.showGateDialog}
        onOpenChange={ctx.setShowGateDialog}
        gateData={ctx.gateData}
        setGateData={ctx.setGateData}
        onSubmit={ctx.handleSubmitGate}
      />
      <DetailDialog
        open={ctx.showDetailDialog}
        onOpenChange={ctx.setShowDetailDialog}
        selectedOpp={ctx.selectedOpp}
        detailEditing={ctx.detailEditing}
        setDetailEditing={ctx.setDetailEditing}
        detailSaving={ctx.detailSaving}
        detailForm={ctx.detailForm}
        setDetailForm={ctx.setDetailForm}
        detailData={ctx.detailData}
        onSave={ctx.handleDetailSave}
      />
      <ReviewDialog
        open={ctx.showReviewDialog}
        onOpenChange={ctx.setShowReviewDialog}
        reviewForm={ctx.reviewForm}
        setReviewForm={ctx.setReviewForm}
        reviewSubmitting={ctx.reviewSubmitting}
        onSubmit={ctx.handleCreateReviewTicket}
      />
    </div>
  );
}
