/**
 * Delivery Management (Refactored)
 * PMC 发货管理页面 (重构版本) - shadcn/Tailwind Dark Theme
 *
 * This file is the orchestrator. Sub-components and the data hook live in
 * the same directory; shared constants are imported from @/lib/constants/service.
 */

import { motion } from "framer-motion";
import {
  PackageCheck,
  Calendar,
  Truck,
} from "lucide-react";

import {
  Card,
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
} from "../../components/ui";

// Shared delivery-management sub-components (from components directory)
import {
  DeliveryOverview,
  DeliveryPlan,
  DeliveryTracking,
} from "../../components/delivery-management";

// Page-local sub-components
import DeliveryDetail from "./DeliveryDetail";
import DeliveryForm from "./DeliveryForm";
import PageHeader from "./PageHeader";
import SearchBar from "./SearchBar";

// Primary data / state hook
import useDeliveryManagement from "./useDeliveryManagement";

// ─────────────────────────────────────────────────────────────────────────────

const DeliveryManagement = () => {
  const {
    viewMode,
    params,
    loading,
    deliveries,
    deliveryStatistics,
    filteredDeliveries,
    activeTab,
    setActiveTab,
    searchText,
    setSearchText,
    loadData,
    handleBack,
    handleView,
    handleEdit,
    handleExport,
    buildDeliveryPath,
    canCreateDeliveryPlan,
    navigate,
  } = useDeliveryManagement();

  // ── sub-views ──────────────────────────────────────────────────────────────

  if (viewMode === "detail") {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="p-6 bg-slate-900 min-h-screen"
      >
        <DeliveryDetail
          id={params.id}
          onBack={handleBack}
          onEdit={() => handleEdit(params.id)}
        />
      </motion.div>
    );
  }

  if (viewMode === "edit") {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="p-6 bg-slate-900 min-h-screen"
      >
        <DeliveryForm id={params.id} onBack={handleBack} />
      </motion.div>
    );
  }

  if (viewMode === "create") {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="p-6 bg-slate-900 min-h-screen"
      >
        <DeliveryForm onBack={handleBack} />
      </motion.div>
    );
  }

  // ── list view ──────────────────────────────────────────────────────────────

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="delivery-management-container p-6 bg-slate-900 min-h-screen"
    >
      <PageHeader
        canCreateFromProject={canCreateDeliveryPlan}
        onNew={() => navigate(buildDeliveryPath("/pmc/delivery-orders/new"))}
        onRefresh={loadData}
        onExport={handleExport}
      />

      <SearchBar value={searchText} onChange={setSearchText} />

      <Card className="bg-surface-100/50">
        <Tabs
          value={activeTab || "overview"}
          onValueChange={setActiveTab}
          className="w-full"
        >
          <TabsList className="grid w-full grid-cols-3 bg-surface-100">
            <TabsTrigger
              value="overview"
              className="data-[state=active]:bg-primary data-[state=active]:text-white"
            >
              <PackageCheck size={16} className="mr-2" />
              交付概览
            </TabsTrigger>
            <TabsTrigger
              value="plan"
              className="data-[state=active]:bg-primary data-[state=active]:text-white"
            >
              <Calendar size={16} className="mr-2" />
              交付计划
            </TabsTrigger>
            <TabsTrigger
              value="tracking"
              className="data-[state=active]:bg-primary data-[state=active]:text-white"
            >
              <Truck size={16} className="mr-2" />
              物流跟踪
            </TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="mt-4">
            <DeliveryOverview
              data={filteredDeliveries}
              loading={loading}
              statistics={deliveryStatistics}
            />
          </TabsContent>

          <TabsContent value="plan" className="mt-4">
            <DeliveryPlan
              deliveries={filteredDeliveries}
              loading={loading}
              onView={handleView}
              onEdit={handleEdit}
            />
          </TabsContent>

          <TabsContent value="tracking" className="mt-4">
            <DeliveryTracking
              deliveries={filteredDeliveries}
              loading={loading}
            />
          </TabsContent>
        </Tabs>
      </Card>
    </motion.div>
  );
};

export default DeliveryManagement;
