import { cn } from "../../lib/utils";
import { staggerContainer } from "./constants";

function LoadingGrid() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {[1, 2, 3, 4, 5, 6].map((i) => (
        <SkeletonCard key={i} />
      ))}
    </div>
  );
}

function EmptyState({ onCreateClick }) {
  return (
    <Card>
      <CardContent className="p-12 text-center">
        <FileText className="h-12 w-12 text-slate-500 mx-auto mb-4" />
        <p className="text-slate-400">暂无研发项目</p>
        <Button
          variant="outline"
          className="mt-4"
          onClick={onCreateClick}
        >
          <Plus className="h-4 w-4 mr-2" />
          创建第一个研发项目
        </Button>
      </CardContent>
    </Card>
  );
}

function Pagination({ pagination, onPageChange }) {
  if (pagination.pages <= 1) return null;

  return (
    <div className="flex items-center justify-center gap-2 mt-6">
      <Button
        variant="secondary"
        size="sm"
        onClick={() => onPageChange(pagination.page - 1)}
        disabled={pagination.page <= 1}
      >
        上一页
      </Button>
      <span className="text-sm text-slate-400">
        第 {pagination.page} / {pagination.pages} 页，共{" "}
        {pagination.total} 条
      </span>
      <Button
        variant="secondary"
        size="sm"
        onClick={() => onPageChange(pagination.page + 1)}
        disabled={pagination.page >= pagination.pages}
      >
        下一页
      </Button>
    </div>
  );
}

export function ProjectListView({
  loading,
  projects,
  viewMode,
  pagination,
  onProjectClick,
  onPageChange,
  onCreateClick,
}) {
  if (loading) {
    return <LoadingGrid />;
  }

  if (!projects?.length) {
    return <EmptyState onCreateClick={onCreateClick} />;
  }

  return (
    <>
      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
        className={cn(
          "grid gap-6",
          viewMode === "grid"
            ? "grid-cols-1 md:grid-cols-2 lg:grid-cols-3"
            : "grid-cols-1"
        )}
      >
        {(projects || []).map((project) => (
          <RdProjectCard
            key={project.id}
            project={project}
            onClick={() => onProjectClick(project)}
          />
        ))}
      </motion.div>

      <Pagination pagination={pagination} onPageChange={onPageChange} />
    </>
  );
}
