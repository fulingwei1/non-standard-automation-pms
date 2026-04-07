/**
 * Service Record Management (重构版)
 * 现场服务记录管理 - 客服工程师高级功能
 *
 * 功能：
 * 1. 现场服务记录创建、编辑、查看
 * 2. 服务类型管理（安装调试、操作培训、定期维护、故障维修）
 * 3. 服务地点、时间、人员记录
 * 4. 服务内容详细记录
 * 5. 服务照片上传（可选）
 * 6. 服务报告生成
 * 7. 客户签字确认
 * 8. 服务记录搜索和筛选
 */

import { Plus, FileText } from "lucide-react";
import { staggerContainer } from "../../lib/animations";

import { useServiceRecordPage } from "./useServiceRecordPage";

export default function ServiceRecord() {
  const {
    records,
    loading,
    error,
    searchQuery,
    setSearchQuery,
    typeFilter,
    setTypeFilter,
    statusFilter,
    setStatusFilter,
    dateFilter,
    setDateFilter,
    showCreateDialog,
    setShowCreateDialog,
    showDetailDialog,
    setShowDetailDialog,
    selectedRecord,
    stats,
    formData,
    setFormData,
    filteredRecords,
    loadRecords,
    handleCreateRecord,
    handleViewDetail,
    handleQuickAction,
    handlePhotoUpload,
    removePhoto,
  } = useServiceRecordPage();

  if (loading && records?.length === 0) {
    return <LoadingCard message="加载服务记录中..." />;
  }

  if (error) {
    return <ErrorMessage message={error} onRetry={loadRecords} />;
  }

  return (
    <div className="min-h-screen bg-slate-900 text-white">
      <PageHeader
        title="服务记录管理"
        subtitle="现场服务记录管理 - 客服工程师高级功能"
        breadcrumbs={[
          { label: "服务管理", href: "/service" },
          { label: "服务记录" },
        ]}
        actions={[
          {
            label: "新建记录",
            icon: Plus,
            onClick: () => setShowCreateDialog(true),
            variant: "default",
          },
        ]}
      />

      <div className="container mx-auto px-4 py-6 space-y-6">
        {/* 服务概览 */}
        <ServiceRecordOverview
          records={records}
          stats={stats}
          onQuickAction={handleQuickAction}
        />

        {/* 筛选和搜索 */}
        <FilterBar
          searchQuery={searchQuery}
          setSearchQuery={setSearchQuery}
          typeFilter={typeFilter}
          setTypeFilter={setTypeFilter}
          statusFilter={statusFilter}
          setStatusFilter={setStatusFilter}
          dateFilter={dateFilter}
          setDateFilter={setDateFilter}
        />

        {/* 服务记录列表 */}
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className="space-y-4"
        >
          {filteredRecords.length === 0 ? (
            <Card>
              <CardContent className="p-8">
                <EmptyState
                  icon={FileText}
                  title="暂无服务记录"
                  description={
                    searchQuery ||
                    typeFilter !== "ALL" ||
                    statusFilter !== "ALL"
                      ? "没有找到匹配的记录"
                      : "还没有创建服务记录"
                  }
                  action={
                    <Button
                      onClick={() => setShowCreateDialog(true)}
                      className="mt-4"
                    >
                      <Plus className="h-4 w-4 mr-2" />
                      创建第一个服务记录
                    </Button>
                  }
                />
              </CardContent>
            </Card>
          ) : (
            (filteredRecords || []).map((record, index) => (
              <RecordListItem
                key={record.id}
                record={record}
                index={index}
                onViewDetail={handleViewDetail}
              />
            ))
          )}
        </motion.div>
      </div>

      {/* 创建服务记录对话框 */}
      <CreateRecordDialog
        open={showCreateDialog}
        onOpenChange={setShowCreateDialog}
        formData={formData}
        setFormData={setFormData}
        onSubmit={handleCreateRecord}
        onPhotoUpload={handlePhotoUpload}
        onRemovePhoto={removePhoto}
      />

      {/* 详情对话框 */}
      <DetailDialog
        open={showDetailDialog}
        onOpenChange={setShowDetailDialog}
        record={selectedRecord}
      />
    </div>
  );
}
