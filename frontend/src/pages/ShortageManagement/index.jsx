/**
 * Shortage Management - 缺料管理
 * Features: 缺料上报、到货跟踪、物料替代、物料调拨、统计分析
 *
 * This file is the orchestrator. It composes sub-components and wires them
 * to the shared state managed by useShortageManagement.
 */

import { PageHeader } from "../../components/layout";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../../components/ui/tabs";
import { useShortageManagement } from "./hooks/useShortageManagement";
import { DashboardTab } from "./DashboardTab";
import { ReportsTab } from "./ReportsTab";
import { ArrivalsTab } from "./ArrivalsTab";
import { SubstitutionsTab } from "./SubstitutionsTab";
import { TransfersTab } from "./TransfersTab";

export default function ShortageManagement() {
  const {
    // Tab
    activeTab,
    setActiveTab,

    // Data
    dashboardData,
    reports,
    arrivals,
    substitutions,
    transfers,

    // UI
    loading,

    // Reports filters / pagination
    searchKeyword,
    setSearchKeyword,
    statusFilter,
    setStatusFilter,
    page,
    setPage,
    pageSize,
    total,

    // Arrivals filters
    arrivalFilters,
    setArrivalFilters,
  } = useShortageManagement();

  return (
    <div className="space-y-6 p-6">
      <PageHeader
        title="缺料管理"
        description="缺料上报、到货跟踪、物料替代、物料调拨"
      />

      <Tabs
        value={activeTab || "dashboard"}
        onValueChange={setActiveTab}
        className="space-y-6"
      >
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="dashboard">看板</TabsTrigger>
          <TabsTrigger value="reports">缺料上报</TabsTrigger>
          <TabsTrigger value="arrivals">到货跟踪</TabsTrigger>
          <TabsTrigger value="substitutions">物料替代</TabsTrigger>
          <TabsTrigger value="transfers">物料调拨</TabsTrigger>
        </TabsList>

        {/* 看板 */}
        <TabsContent value="dashboard" className="space-y-6">
          <DashboardTab dashboardData={dashboardData} />
        </TabsContent>

        {/* 缺料上报 */}
        <TabsContent value="reports" className="space-y-6">
          <ReportsTab
            reports={reports}
            loading={loading}
            searchKeyword={searchKeyword}
            setSearchKeyword={setSearchKeyword}
            statusFilter={statusFilter}
            setStatusFilter={setStatusFilter}
            page={page}
            setPage={setPage}
            pageSize={pageSize}
            total={total}
          />
        </TabsContent>

        {/* 到货跟踪 */}
        <TabsContent value="arrivals" className="space-y-6">
          <ArrivalsTab
            arrivals={arrivals}
            loading={loading}
            arrivalFilters={arrivalFilters}
            setArrivalFilters={setArrivalFilters}
          />
        </TabsContent>

        {/* 物料替代 */}
        <TabsContent value="substitutions" className="space-y-6">
          <SubstitutionsTab substitutions={substitutions} loading={loading} />
        </TabsContent>

        {/* 物料调拨 */}
        <TabsContent value="transfers" className="space-y-6">
          <TransfersTab transfers={transfers} loading={loading} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
