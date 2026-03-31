import { Shield } from "lucide-react";
import { PageHeader } from "../../components/layout";
import { usePermissionData } from "./usePermissionData";
import { StatsCards } from "./StatsCards";
import { UsageStats } from "./UsageStats";
import { SearchFilter } from "./SearchFilter";
import { DemoAccountBanner } from "./DemoAccountBanner";
import { PermissionList } from "./PermissionList";
import { PermissionDetailDialog } from "./PermissionDetailDialog";

export default function PermissionManagement() {
  const {
    loading,
    searchKeyword,
    setSearchKeyword,
    filterModule,
    setFilterModule,
    expandedModules,
    selectedPermission,
    showDetailDialog,
    setShowDetailDialog,
    permissionRoles,
    permissionUsageStats,
    isDemoAccount,
    modules,
    filteredPermissions,
    stats,
    toggleModule,
    handleViewDetail,
  } = usePermissionData();

  return (
    <div className="space-y-6">
      <PageHeader
        title="权限管理"
        description="查看和管理系统中的所有权限配置"
        icon={Shield}
      />

      <StatsCards stats={stats} />

      <UsageStats
        permissionUsageStats={permissionUsageStats}
        unusedCount={stats.unused}
      />

      <SearchFilter
        searchKeyword={searchKeyword}
        setSearchKeyword={setSearchKeyword}
        filterModule={filterModule}
        setFilterModule={setFilterModule}
        modules={modules}
      />

      {isDemoAccount && <DemoAccountBanner />}

      <PermissionList
        loading={loading}
        isDemoAccount={isDemoAccount}
        searchKeyword={searchKeyword}
        filteredPermissions={filteredPermissions}
        expandedModules={expandedModules}
        permissionUsageStats={permissionUsageStats}
        toggleModule={toggleModule}
        handleViewDetail={handleViewDetail}
      />

      <PermissionDetailDialog
        open={showDetailDialog}
        onOpenChange={setShowDetailDialog}
        selectedPermission={selectedPermission}
        permissionRoles={permissionRoles}
      />
    </div>
  );
}
