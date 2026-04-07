/**
 * Quote Cost Analysis Page - 报价成本分析页面
 * Features: Version comparison, cost trend, cost structure analysis
 */

import { useParams, useNavigate } from "react-router-dom";


import { staggerContainer } from "../../lib/animations";
import { ANALYSIS_TABS } from "./constants";
import { useQuoteCostAnalysis } from "./hooks/useQuoteCostAnalysis";

export default function QuoteCostAnalysis() {
  const { id } = useParams();
  const navigate = useNavigate();

  const {
    loading,
    quote,
    versions,
    selectedVersions,
    setSelectedVersions,
    comparison,
    costStructure,
    structureByCategory,
  } = useQuoteCostAnalysis(id);

  if (loading && !quote) {
    return (
      <div className="flex items-center justify-center h-64">加载中...</div>
    );
  }

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={staggerContainer}
      className="space-y-6"
    >
      <PageHeader
        title="报价成本分析"
        description={quote ? `报价编号: ${quote.quote_no || id}` : ""}
        actions={
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={() => navigate(`/sales/quotes/${id}/cost`)}
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              返回成本管理
            </Button>
            <Button variant="outline">
              <Download className="h-4 w-4 mr-2" />
              导出报告
            </Button>
          </div>
        }
      />

      <Tabs defaultValue="comparison" className="space-y-4">
        <TabsList>
          {ANALYSIS_TABS.map((tab) => (
            <TabsTrigger key={tab.value} value={tab.value}>
              {tab.label}
            </TabsTrigger>
          ))}
        </TabsList>

        <TabsContent value="comparison" className="space-y-4">
          <VersionComparison
            versions={versions}
            selectedVersions={selectedVersions}
            setSelectedVersions={setSelectedVersions}
            comparison={comparison}
          />
        </TabsContent>

        <TabsContent value="trend" className="space-y-4">
          <CostTrendTab versions={versions} />
        </TabsContent>

        <TabsContent value="structure" className="space-y-4">
          <CostStructureTab
            costStructure={costStructure}
            structureByCategory={structureByCategory}
          />
        </TabsContent>
      </Tabs>
    </motion.div>
  );
}
