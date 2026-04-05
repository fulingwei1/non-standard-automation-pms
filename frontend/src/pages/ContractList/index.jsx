/**
 * Contract List Page - Contract management for sales
 * Features: Contract list, status tracking, payment milestones
 */

import { motion, AnimatePresence } from "framer-motion";
import {
  Download,
  Plus,
  Loader2,
  AlertTriangle,
} from "lucide-react";
import { PageHeader } from "../../components/layout";
import { Button, Card, CardContent } from "../../components/ui";
import { fadeIn, staggerContainer } from "../../lib/animations";

import { useContractList } from "./hooks";
import ContractStatsRow from "./ContractStatsRow";
import ContractFilters from "./ContractFilters";
import ContractTable from "./ContractTable";
import ContractDetailPanel from "./ContractDetailPanel";
import CreateContractDialog from "./CreateContractDialog";

export default function ContractList() {
  const {
    loading,
    error,
    filteredContracts,
    stats,
    searchTerm,
    setSearchTerm,
    selectedStatus,
    setSelectedStatus,
    selectedContract,
    setSelectedContract,
    showCreateDialog,
    setShowCreateDialog,
    handleContractClick,
  } = useContractList();

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      {/* Page Header */}
      <PageHeader
        title="合同管理"
        description="管理销售合同和付款条款"
        actions={
          <motion.div variants={fadeIn} className="flex gap-2">
            <Button variant="outline" className="flex items-center gap-2">
              <Download className="w-4 h-4" />
              导出
            </Button>
            <Button
              className="flex items-center gap-2"
              onClick={() => setShowCreateDialog(true)}
            >
              <Plus className="w-4 h-4" />
              新建合同
            </Button>
          </motion.div>
        }
      />

      {/* Stats Row */}
      <ContractStatsRow stats={stats} />

      {/* Filters */}
      <ContractFilters
        searchTerm={searchTerm}
        onSearchChange={setSearchTerm}
        selectedStatus={selectedStatus}
        onStatusChange={setSelectedStatus}
        resultCount={filteredContracts.length}
      />

      {/* Loading State */}
      {loading && (
        <motion.div variants={fadeIn} className="flex justify-center py-20">
          <div className="flex items-center gap-3 text-slate-400">
            <Loader2 className="w-6 h-6 animate-spin" />
            <span>加载中...</span>
          </div>
        </motion.div>
      )}

      {/* Error State */}
      {error && !loading && (
        <motion.div variants={fadeIn}>
          <Card className="bg-red-500/10 border-red-500/20">
            <CardContent className="p-6 text-center">
              <AlertTriangle className="w-12 h-12 mx-auto text-red-400 mb-4" />
              <h3 className="text-lg font-medium text-white mb-2">加载失败</h3>
              <p className="text-slate-400 mb-4">{error}</p>
              <Button onClick={() => window.location.reload()}>重新加载</Button>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Contract Table */}
      {!loading && !error && (
        <ContractTable
          contracts={filteredContracts}
          onContractClick={handleContractClick}
          onCreateClick={() => setShowCreateDialog(true)}
        />
      )}

      {/* Contract Detail Panel */}
      <AnimatePresence>
        {selectedContract && (
          <ContractDetailPanel
            contract={selectedContract}
            onClose={() => setSelectedContract(null)}
          />
        )}
      </AnimatePresence>

      {/* Create Dialog */}
      <CreateContractDialog
        open={showCreateDialog}
        onOpenChange={setShowCreateDialog}
      />
    </motion.div>
  );
}
