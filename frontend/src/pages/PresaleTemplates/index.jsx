import { motion } from "framer-motion";

import { PageHeader } from "../../components/layout";
import { fadeIn, staggerContainer } from "../../lib/animations";
import { FilterBar } from "./FilterBar";
import { PreviewDialog } from "./PreviewDialog";
import { StatsBar } from "./StatsBar";
import { TemplateGrid } from "./TemplateGrid";
import { usePresaleTemplates } from "./usePresaleTemplates";

export default function PresaleTemplates({ embedded = false } = {}) {
  const {
    loading,
    loadError,
    keyword,
    setKeyword,
    selectedCategory,
    setSelectedCategory,
    previewTemplate,
    previewLoading,
    applyingTemplateId,
    ratingTemplateId,
    myRatings,
    categories,
    filteredTemplates,
    stats,
    applyTemplate,
    rateTemplate,
    openPreview,
    closePreview,
  } = usePresaleTemplates();

  return (
    <motion.div
      className="space-y-6"
      initial="hidden"
      animate="visible"
      variants={staggerContainer}
    >
      {!embedded && (
        <PageHeader
          title="售前模板库"
          description="统一管理模板分类、快速预览、模板应用和团队评分反馈。"
        />
      )}

      {loadError && (
        <motion.div variants={fadeIn}>
          <div className="rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">
            模板数据加载失败：{loadError}，请刷新页面重试。
          </div>
        </motion.div>
      )}

      <motion.div variants={fadeIn}>
        <StatsBar stats={stats} />
      </motion.div>

      <motion.div variants={fadeIn}>
        <FilterBar
          categories={categories}
          selectedCategory={selectedCategory}
          onSelectCategory={setSelectedCategory}
          keyword={keyword}
          onKeywordChange={setKeyword}
        />
      </motion.div>

      <motion.div
        variants={fadeIn}
        className="grid grid-cols-1 gap-4 xl:grid-cols-2"
      >
        <TemplateGrid
          loading={loading}
          filteredTemplates={filteredTemplates}
          applyingTemplateId={applyingTemplateId}
          ratingTemplateId={ratingTemplateId}
          myRatings={myRatings}
          onPreview={openPreview}
          onApply={applyTemplate}
          onRate={rateTemplate}
        />
      </motion.div>

      <PreviewDialog
        previewTemplate={previewTemplate}
        previewLoading={previewLoading}
        applyingTemplateId={applyingTemplateId}
        onClose={closePreview}
        onApply={applyTemplate}
      />
    </motion.div>
  );
}
