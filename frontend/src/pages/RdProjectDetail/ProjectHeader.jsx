import { useNavigate } from "react-router-dom";




import { formatDate } from "../../lib/utils";

export default function ProjectHeader({ project, status, categoryType }) {
  const navigate = useNavigate();

  return (
    <div className="flex items-center justify-between mb-6">
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => navigate("/rd-projects")}
        >
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div>
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 rounded-lg bg-primary/20">
              <FlaskConical className="h-5 w-5 text-primary" />
            </div>
            <h1 className="text-2xl font-bold text-white">
              {project.project_name}
            </h1>
            <Badge variant={status.color}>{status.label}</Badge>
            <Badge variant="outline">{categoryType.label}</Badge>
          </div>
          <div className="flex items-center gap-4 text-sm text-slate-400">
            <span>{project.project_no}</span>
            <span>•</span>
            <span>负责人: {project.project_manager_name || "未指定"}</span>
            {project.planned_start_date && (
              <>
                <span>•</span>
                <span>
                  {formatDate(project.planned_start_date)} ~{" "}
                  {formatDate(project.planned_end_date)}
                </span>
              </>
            )}
          </div>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <Button variant="secondary" size="icon">
          <Edit2 className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
