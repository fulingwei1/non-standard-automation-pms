/**
 * BOM Management Page - BOM管理页面
 * Features: BOM列表、详情、版本管理、导入导出、发布审批
 */
import { PageHeader } from '../../components/layout';
import { useBOMManagement } from './hooks';
import BOMFilterBar from './BOMFilterBar';
import BOMTable from './BOMTable';
import BOMDetailDialog from './BOMDetailDialog';
import CreateBOMDialog from './CreateBOMDialog';
import ImportBOMDialog from './ImportBOMDialog';
import ReleaseBOMDialog from './ReleaseBOMDialog';

export default function BOMManagement() {
    const {
        // list
        loading,
        filteredBoms,
        projects,
        machines,
        // detail
        selectedBom,
        setSelectedBom,
        bomItems,
        versions,
        // filters
        searchKeyword,
        setSearchKeyword,
        filterProject,
        filterMachine,
        setFilterMachine,
        filterStatus,
        setFilterStatus,
        handleFilterProjectChange,
        // dialogs
        showBomDetail,
        setShowBomDetail,
        showCreateDialog,
        setShowCreateDialog,
        showImportDialog,
        setShowImportDialog,
        showReleaseDialog,
        setShowReleaseDialog,
        // form
        newBom,
        setNewBom,
        importFile,
        setImportFile,
        releaseNote,
        setReleaseNote,
        // actions
        fetchBOMDetail,
        handleCreateBOM,
        handleReleaseBOM,
        handleImport,
        handleExport,
        handleCreateDialogProjectChange,
    } = useBOMManagement();

    return (
        <div className="space-y-6 p-6">
            <PageHeader
                title="BOM管理"
                description="物料清单管理，支持版本控制、导入导出、发布审批"
            />

            <BOMFilterBar
                searchKeyword={searchKeyword}
                setSearchKeyword={setSearchKeyword}
                filterProject={filterProject}
                filterMachine={filterMachine}
                setFilterMachine={setFilterMachine}
                filterStatus={filterStatus}
                setFilterStatus={setFilterStatus}
                projects={projects}
                machines={machines}
                onProjectChange={handleFilterProjectChange}
            />

            <BOMTable
                loading={loading}
                filteredBoms={filteredBoms}
                onViewDetail={fetchBOMDetail}
                onExport={handleExport}
                onCreateNew={() => setShowCreateDialog(true)}
            />

            <BOMDetailDialog
                open={showBomDetail}
                onOpenChange={setShowBomDetail}
                selectedBom={selectedBom}
                bomItems={bomItems}
                versions={versions}
                onImport={() => setShowImportDialog(true)}
                onExport={handleExport}
                onRelease={() => setShowReleaseDialog(true)}
                onViewVersion={(version) => {
                    setSelectedBom(version);
                    fetchBOMDetail(version.id);
                }}
            />

            <CreateBOMDialog
                open={showCreateDialog}
                onOpenChange={setShowCreateDialog}
                newBom={newBom}
                setNewBom={setNewBom}
                projects={projects}
                machines={machines}
                onProjectChange={handleCreateDialogProjectChange}
                onSubmit={handleCreateBOM}
            />

            <ImportBOMDialog
                open={showImportDialog}
                onOpenChange={setShowImportDialog}
                importFile={importFile}
                setImportFile={setImportFile}
                onSubmit={handleImport}
            />

            <ReleaseBOMDialog
                open={showReleaseDialog}
                onOpenChange={setShowReleaseDialog}
                releaseNote={releaseNote}
                setReleaseNote={setReleaseNote}
                onSubmit={handleReleaseBOM}
            />
        </div>
    );
}
