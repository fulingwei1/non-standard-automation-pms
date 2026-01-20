import { useNavigate } from "react-router-dom";
import { PageHeader } from "../../components/layout/PageHeader";
import { useTechnicalReviewList } from "./hooks";
import { TechnicalReviewFilter, TechnicalReviewCards, TechnicalReviewDeleteDialog } from "./components";

export default function TechnicalReviewList() {
    const navigate = useNavigate();
    const {
        loading,
        reviews,
        total,
        page,
        setPage,
        pageSize,
        searchKeyword, setSearchKeyword,
        projectId, setProjectId,
        status, setStatus,
        reviewType, setReviewType,
        projectList,
        deleteDialog, setDeleteDialog,
        handleDelete,
        handleSearch,
        handleReset
    } = useTechnicalReviewList();

    return (
        <div className="min-h-screen bg-slate-950 text-slate-100">
            <PageHeader
                title="技术评审管理"
                description="管理项目各阶段的技术评审（PDR/DDR/PRR/FRR/ARR）"
            />

            <div className="container mx-auto px-4 py-6 space-y-6">
                <TechnicalReviewFilter
                    searchKeyword={searchKeyword}
                    setSearchKeyword={setSearchKeyword}
                    projectId={projectId}
                    setProjectId={setProjectId}
                    reviewType={reviewType}
                    setReviewType={setReviewType}
                    status={status}
                    setStatus={setStatus}
                    projectList={projectList}
                    onSearch={handleSearch}
                    onReset={handleReset}
                    onCreate={() => navigate("/technical-reviews/new")}
                />

                <TechnicalReviewCards
                    loading={loading}
                    reviews={reviews}
                    total={total}
                    page={page}
                    pageSize={pageSize}
                    setPage={setPage}
                    onCreate={() => navigate("/technical-reviews/new")}
                    onView={(review) => navigate(`/technical-reviews/${review.id}`)}
                    onEdit={(review) => navigate(`/technical-reviews/${review.id}/edit`)}
                    onDeleteRequest={(review) => setDeleteDialog({ open: true, review })}
                />
            </div>

            <TechnicalReviewDeleteDialog
                open={deleteDialog.open}
                review={deleteDialog.review}
                onClose={() => setDeleteDialog({ open: false, review: null })}
                onConfirm={handleDelete}
            />
        </div>
    );
}
