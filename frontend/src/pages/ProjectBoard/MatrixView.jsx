import { useMemo } from "react";
import { cn } from "../../lib/utils";
import { HEALTH_CONFIG } from "../../lib/constants";

export default function MatrixView({ projects, stages, onProjectClick }) {
  // 按阶段和健康度分组
  const matrix = useMemo(() => {
    const result = {};
    (stages || []).forEach((stage) => {
      result[stage.key] = { H1: [], H2: [], H3: [], H4: [] };
    });

    (projects || []).forEach((project) => {
      // API返回的是 stage 字段，不是 current_stage
      const stageKey = project.stage || project.current_stage || "S1";
      const healthKey = project.health || "H1";
      if (result[stageKey]) {
        result[stageKey][healthKey].push(project);
      }
    });

    return result;
  }, [projects, stages]);

  const healthKeys = ["H3", "H2", "H1", "H4"]; // 预警优先

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse">
        <thead>
          <tr>
            <th className="p-2 text-left text-xs text-slate-500 font-normal">
              健康度 / 阶段
            </th>
            {(stages || []).map((stage) =>
            <th key={stage.key} className="p-2 text-center">
                <div className="text-xs text-slate-400">{stage.key}</div>
                <div className="text-sm text-white">{stage.shortName}</div>
            </th>
            )}
          </tr>
        </thead>
        <tbody>
          {(healthKeys || []).map((healthKey) =>
          <tr key={healthKey} className="border-t border-white/5">
              <td className="p-2">
                <div
                className={cn(
                  "flex items-center gap-2 px-2 py-1 rounded",
                  HEALTH_CONFIG[healthKey].bgClass
                )}>

                  <span
                  className={cn(
                    "w-2 h-2 rounded-full",
                    HEALTH_CONFIG[healthKey].dotClass
                  )} />

                  <span
                  className={cn(
                    "text-sm",
                    HEALTH_CONFIG[healthKey].textClass
                  )}>

                    {HEALTH_CONFIG[healthKey].label}
                  </span>
                </div>
              </td>
              {(stages || []).map((stage) => {
              const cellProjects = matrix[stage.key]?.[healthKey] || [];
              return (
                <td key={stage.key} className="p-2 text-center align-top">
                    {cellProjects.length > 0 ?
                  <div className="space-y-1">
                        {cellProjects.slice(0, 3).map((project) =>
                    <motion.div
                      key={project.id}
                      whileHover={{ scale: 1.05 }}
                      onClick={() => onProjectClick(project)}
                      className={cn(
                        "cursor-pointer px-2 py-1 rounded text-xs truncate",
                        "bg-surface-1 hover:bg-surface-2 border border-white/5",
                        HEALTH_CONFIG[healthKey].borderClass,
                        "border-l-2"
                      )}>

                            {project.project_code}
                    </motion.div>
                    )}
                        {cellProjects.length > 3 &&
                    <div className="text-xs text-slate-500">
                            +{cellProjects.length - 3} 更多
                    </div>
                    }
                  </div> :

                  <span className="text-slate-600">-</span>
                  }
                </td>);

            })}
          </tr>
          )}
        </tbody>
      </table>
    </div>);

}
