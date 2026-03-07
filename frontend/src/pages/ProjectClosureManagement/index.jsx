import { motion } from "framer-motion";
import { ArrowLeft, FileText } from "lucide-react";
import { PageHeader } from "../../components/layout/PageHeader";
import { Button } from "../../components/ui";
import { staggerContainer } from "../../lib/animations";
import { useProjectClosureManagement } from "./hooks";
import {
    ProjectSelectionView,
    ProjectClosureContent
} from "./components";
import {
    CreateClosureDialog,
    ReviewClosureDialog,
    LessonsClosureDialog,
    ClosureDetailDialog
} from "../../components/project-closure";

export default function ProjectClosureManagement() {
    const {
        loading,
        project,
        closure,
        projectSearch,
        setProjectSearch,
        projectList,
        showProjectSelect,
        setShowProjectSelect,
        createDialogOpen,
        setCreateDialogOpen,
        reviewDialog,
        setReviewDialog,
        lessonsDialog,
        setLessonsDialog,
        detailDialog,
        setDetailDialog,
        navigate,
        handleSelectProject,
        handleCreate,
        handleReview,
        handleLessons
    } = useProjectClosureManagement();

    if (showProjectSelect) {
        return (
            <ProjectSelectionView
                projectSearch={projectSearch}
                setProjectSearch={setProjectSearch}
                projectList={projectList}
                onSelectProject={handleSelectProject}
            />
        );
    }

    return (
        <motion.div initial="hidden" animate="visible" variants={staggerContainer}>
            <PageHeader
                title="项目结项管理"
                description={
                    project ? `${project.project_name} - 项目结项` : "项目结项"
                }
                action={
                    <div className="flex items-center gap-2">
                        <Button
                            variant="outline"
                            onClick={() => {
                                setShowProjectSelect(true);
                                navigate("/pmo/closure");
                            }}
                        >
                            <ArrowLeft className="h-4 w-4 mr-2" />
                            选择项目
                        </Button>
                        {!closure && (
                            <Button
                                onClick={() => setCreateDialogOpen(true)}
                                className="gap-2"
                            >
                                <FileText className="h-4 w-4" />
                                创建结项申请
                            </Button>
                        )}
                    </div>
                }
            />

            <ProjectClosureContent
                loading={loading}
                closure={closure}
                onCreate={() => setCreateDialogOpen(true)}
                onReview={(id) => setReviewDialog({ open: true, closureId: id })}
                onEditLessons={(id) => setLessonsDialog({ open: true, closureId: id })}
                onViewDetail={(item) => setDetailDialog({ open: true, closure: item })}
            />

            {/* Dialogs */}
            <CreateClosureDialog
                open={createDialogOpen}
                onOpenChange={setCreateDialogOpen}
                onSubmit={handleCreate}
            />

            <ReviewClosureDialog
                open={reviewDialog.open}
                onOpenChange={(open) => setReviewDialog({ open, closureId: null })}
                onSubmit={(data) => handleReview(reviewDialog.closureId, data)}
            />

            <LessonsClosureDialog
                open={lessonsDialog.open}
                onOpenChange={(open) => setLessonsDialog({ open, closureId: null })}
                onSubmit={(data) => handleLessons(lessonsDialog.closureId, data)}
                closure={closure}
            />

            <ClosureDetailDialog
                open={detailDialog.open}
                onOpenChange={(open) => setDetailDialog({ open, closure: null })}
                closure={detailDialog.closure}
            />
        </motion.div>
    );
}
