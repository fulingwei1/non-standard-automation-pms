import { Upload } from "lucide-react";
import { PageHeader } from "../../components/layout";
import { Button } from "../../components/ui/button";
import { useEmployeeProfileList } from "./hooks";
import {
    EmployeeUploadModal,
    EmployeeStatsCards,
    EmployeeList,
    EmployeeStatusTabs
} from "./components";

export default function EmployeeProfileList() {
    const {
        loading,
        filteredProfiles,
        searchKeyword, setSearchKeyword,
        filterDepartment, setFilterDepartment,
        activeStatusTab, setActiveStatusTab,
        departments,
        stats,
        showUploadModal, setShowUploadModal,
        uploading,
        uploadResult, setUploadResult,
        fileInputRef,
        handleFileUpload,
        loadProfiles
    } = useEmployeeProfileList();

    return (
        <div className="space-y-6">
            <PageHeader
                title="员工能力档案"
                description="查看员工技能评估、工作负载和项目绩效"
                actions={
                    <Button onClick={() => setShowUploadModal(true)}>
                        <Upload className="h-4 w-4 mr-2" />
                        导入员工数据
                    </Button>
                }
            />

            <EmployeeUploadModal
                showUploadModal={showUploadModal}
                setShowUploadModal={setShowUploadModal}
                uploading={uploading}
                uploadResult={uploadResult}
                setUploadResult={setUploadResult}
                fileInputRef={fileInputRef}
                handleFileUpload={handleFileUpload}
            />

            <EmployeeStatusTabs
                activeStatusTab={activeStatusTab}
                setActiveStatusTab={setActiveStatusTab}
            />

            <EmployeeStatsCards
                stats={stats}
                activeStatusTab={activeStatusTab}
            />

            <EmployeeList
                loading={loading}
                filteredProfiles={filteredProfiles}
                searchKeyword={searchKeyword}
                setSearchKeyword={setSearchKeyword}
                filterDepartment={filterDepartment}
                setFilterDepartment={setFilterDepartment}
                departments={departments}
                onRefresh={loadProfiles}
            />
        </div>
    );
}
