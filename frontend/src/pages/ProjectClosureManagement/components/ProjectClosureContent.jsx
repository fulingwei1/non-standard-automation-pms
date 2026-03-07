import { FileText } from "lucide-react";
import { Card, CardContent, Button, SkeletonCard } from "../../../components/ui";
import { ProjectClosureStatusCard } from "./ProjectClosureStatusCard";
import { ProjectClosureStats } from "./ProjectClosureStats";
import { ProjectClosureInfo } from "./ProjectClosureInfo";
import { ProjectClosureLessons } from "./ProjectClosureLessons";
import { ProjectClosureQuality } from "./ProjectClosureQuality";
import { ProjectClosureReview } from "./ProjectClosureReview";
import { ProjectClosureActions } from "./ProjectClosureActions";

export function ProjectClosureContent({
    loading,
    closure,
    onCreate,
    onReview,
    onEditLessons,
    onViewDetail
}) {
    if (loading) {
        return (
            <div className="grid grid-cols-1 gap-4">
                <SkeletonCard />
            </div>
        );
    }

    if (!closure) {
        return (
            <Card>
                <CardContent className="p-12 text-center">
                    <div className="space-y-4">
                        <div className="p-4 rounded-xl bg-white/[0.03] border border-white/5 inline-block mx-auto">
                            <FileText className="h-12 w-12 text-slate-500" />
                        </div>
                        <div>
                            <h3 className="text-lg font-semibold text-white mb-2">
                                该项目尚未创建结项申请
                            </h3>
                            <p className="text-slate-400 mb-4">
                                创建结项申请以记录项目完成情况和经验教训
                            </p>
                            <Button onClick={onCreate}>
                                <FileText className="h-4 w-4 mr-2" />
                                创建结项申请
                            </Button>
                        </div>
                    </div>
                </CardContent>
            </Card>
        );
    }

    return (
        <div className="space-y-6">
            <ProjectClosureStatusCard status={closure.status} />
            <ProjectClosureStats closure={closure} />
            <ProjectClosureInfo closure={closure} />
            <ProjectClosureLessons closure={closure} onEdit={onEditLessons} />
            <ProjectClosureQuality closure={closure} />
            <ProjectClosureReview closure={closure} />
            <ProjectClosureActions
                closure={closure}
                onReview={onReview}
                onViewDetail={onViewDetail}
            />
        </div>
    );
}
