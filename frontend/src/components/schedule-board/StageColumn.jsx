import { Badge } from "../../components/ui/badge";
import { cn } from "../../lib/utils";
import { stageColors } from "./scheduleConfig";
import ProjectCard from "./ProjectCard";

export default function StageColumn({ stage, stageName, projects }) {
  const stageProjects = (projects || []).filter((p) => p.stage === stage);
  const stageColor = stageColors[stage];

  return (
    <div className="min-w-[320px] max-w-[320px]">
      {/* Column Header */}
      <div className="flex items-center gap-2 mb-4 px-2">
        <div className={cn("w-3 h-3 rounded-full", stageColor)} />
        <h3 className="font-semibold text-white">{stageName}</h3>
        <Badge variant="secondary" className="ml-auto">
          {stageProjects.length}
        </Badge>
      </div>

      {/* Projects */}
      <div className="space-y-4">
        {stageProjects.length > 0 ? (
          (stageProjects || []).map((project) => (
            <ProjectCard key={project.id} project={project} />
          ))
        ) : (
          <div className="p-8 text-center text-slate-500 border border-dashed border-border rounded-xl">
            暂无项目
          </div>
        )}
      </div>
    </div>
  );
}
