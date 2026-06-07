/**
 * 技术评审详情/创建页面
 * 支持创建、编辑、查看技术评审详情
 */
import { useLocation, useNavigate, useParams } from "react-router-dom";
import { PageHeader } from "../../components/layout/PageHeader";
import {
    Button,
    Tabs,
    TabsList,
    TabsTrigger,
    TabsContent,
    SkeletonCard,
} from "../../components/ui";
import { ArrowLeft, Save } from "lucide-react";

import { useTechnicalReviewForm } from "./hooks";
import { BasicInfoTab } from "./BasicInfoTab";
import { ParticipantsTab } from "./ParticipantsTab";
import { MaterialsTab } from "./MaterialsTab";
import { ChecklistTab } from "./ChecklistTab";
import { IssuesTab } from "./IssuesTab";
import { ReviewChecklistDialog } from "./ReviewChecklistDialog";
import { ReviewIssueDialog } from "./ReviewIssueDialog";
import { ReviewMaterialDialog } from "./ReviewMaterialDialog";
import { ReviewParticipantDialog } from "./ReviewParticipantDialog";
import { buildTechnicalReviewListPath } from "./navigation";

export default function TechnicalReviewDetail() {
    const { reviewId } = useParams();
    const navigate = useNavigate();
    const location = useLocation();

    const {
        isNew,
        loading,
        saving,
        review,
        activeTab,
        setActiveTab,
        formData,
        updateField,
        projects,
        users,
        participants,
        materials,
        checklistRecords,
        issues,
        participantDialog,
        materialDialog,
        checklistDialog,
        issueDialog,
        setParticipantDialog,
        setMaterialDialog,
        setChecklistDialog,
        setIssueDialog,
        handleSave,
        handleAddParticipant,
        handleAddMaterial,
        handleCreateChecklistRecord,
        handleCreateIssue,
        fetchReview,
    } = useTechnicalReviewForm(reviewId);

    if (loading) {
        return (
            <div className="min-h-screen bg-slate-950 text-slate-100 p-6 space-y-6">
                <SkeletonCard />
                <SkeletonCard />
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-slate-950 text-slate-100">
            <PageHeader
                title={
                    isNew ? "创建技术评审" : `技术评审 - ${review?.review_name || ""}`
                }
                description={
                    isNew ? "创建新的技术评审" : `评审编号: ${review?.review_no || ""}`
                }
                action={
                    <div className="flex items-center gap-2">
                        <Button
                            variant="outline"
                            onClick={() => navigate(buildTechnicalReviewListPath(location.search))}
                            className="border-slate-700"
                        >
                            <ArrowLeft className="w-4 h-4 mr-2" />
                            返回列表
                        </Button>
                        <Button
                            onClick={handleSave}
                            disabled={saving}
                            className="bg-blue-600 hover:bg-blue-700"
                        >
                            <Save className="w-4 h-4 mr-2" />
                            {saving ? "保存中..." : "保存"}
                        </Button>
                    </div>
                }
            />

            <div className="container mx-auto px-4 py-6">
                <Tabs
                    value={activeTab || "unknown"}
                    onValueChange={setActiveTab}
                    className="space-y-6"
                >
                    <TabsList className="bg-slate-900/50 border-slate-800">
                        <TabsTrigger value="basic">基本信息</TabsTrigger>
                        <TabsTrigger value="participants">
                            参与人 ({participants.length})
                        </TabsTrigger>
                        <TabsTrigger value="materials">
                            材料 ({materials?.length})
                        </TabsTrigger>
                        <TabsTrigger value="checklist">
                            检查项 ({checklistRecords.length})
                        </TabsTrigger>
                        <TabsTrigger value="issues">
                            问题 ({issues?.length})
                        </TabsTrigger>
                    </TabsList>

                    <TabsContent value="basic" className="space-y-4">
                        <BasicInfoTab
                            isNew={isNew}
                            review={review}
                            formData={formData}
                            updateField={updateField}
                            projects={projects}
                            users={users}
                        />
                    </TabsContent>

                    <TabsContent value="participants" className="space-y-4">
                        <ParticipantsTab
                            isNew={isNew}
                            participants={participants}
                            users={users}
                            onAddParticipant={() => setParticipantDialog({ open: true })}
                        />
                    </TabsContent>

                    <TabsContent value="materials" className="space-y-4">
                        <MaterialsTab
                            isNew={isNew}
                            materials={materials}
                            onUpload={() => setMaterialDialog({ open: true })}
                            onRefresh={fetchReview}
                        />
                    </TabsContent>

                    <TabsContent value="checklist" className="space-y-4">
                        <ChecklistTab
                            isNew={isNew}
                            checklistRecords={checklistRecords}
                            onAddChecklist={() => setChecklistDialog({ open: true })}
                        />
                    </TabsContent>

                    <TabsContent value="issues" className="space-y-4">
                        <IssuesTab
                            isNew={isNew}
                            issues={issues}
                            users={users}
                            onCreateIssue={() => setIssueDialog({ open: true })}
                        />
                    </TabsContent>
                </Tabs>
            </div>

            {!isNew && (
                <>
                    <ReviewParticipantDialog
                        open={Boolean(participantDialog?.open)}
                        onOpenChange={(open) => setParticipantDialog({ open })}
                        reviewId={reviewId}
                        users={users}
                        onSubmit={handleAddParticipant}
                    />
                    <ReviewMaterialDialog
                        open={Boolean(materialDialog?.open)}
                        onOpenChange={(open) => setMaterialDialog({ open })}
                        reviewId={reviewId}
                        onSubmit={handleAddMaterial}
                    />
                    <ReviewChecklistDialog
                        open={Boolean(checklistDialog?.open)}
                        onOpenChange={(open) => setChecklistDialog({ open })}
                        reviewId={reviewId}
                        users={users}
                        onSubmit={handleCreateChecklistRecord}
                    />
                    <ReviewIssueDialog
                        open={Boolean(issueDialog?.open)}
                        onOpenChange={(open) => setIssueDialog({ open })}
                        reviewId={reviewId}
                        users={users}
                        onSubmit={handleCreateIssue}
                    />
                </>
            )}
        </div>
    );
}
