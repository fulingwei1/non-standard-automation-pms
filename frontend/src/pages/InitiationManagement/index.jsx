import { useNavigate } from "react-router-dom";
import { useInitiationManagement } from "./hooks";

export default function InitiationManagement() {
    const navigate = useNavigate();
    const {
        loading,
        error,
        initiations,
        total,
        page, setPage,
        pageSize,
        keyword, setKeyword,
        statusFilter, setStatusFilter,
        createDialogOpen, setCreateDialogOpen,
        handleCreate,
        handleSubmit,
        fetchData
    } = useInitiationManagement();

    return (
        <div>
            <PageHeader
                title="立项管理"
                description="项目立项申请与评审管理"
                action={
                    <Button onClick={() => setCreateDialogOpen(true)} className="gap-2">
                        <Plus className="h-4 w-4" />
                        新建申请
                    </Button>
                }
            />

            <InitiationFilter
                keyword={keyword}
                setKeyword={setKeyword}
                statusFilter={statusFilter}
                setStatusFilter={setStatusFilter}
            />

            <InitiationList
                loading={loading}
                error={error}
                initiations={initiations}
                total={total}
                page={page}
                pageSize={pageSize}
                setPage={setPage}
                onRetry={fetchData}
                onViewDetail={(id) => navigate(`/pmo/initiations/${id}`)}
                onViewProject={(id) => navigate(`/projects/${id}`)}
                onSubmitReview={handleSubmit}
            />

            <CreateInitiationDialog
                open={createDialogOpen}
                onOpenChange={setCreateDialogOpen}
                onSubmit={handleCreate}
            />
        </div>
    );
}
