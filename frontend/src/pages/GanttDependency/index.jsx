import { motion } from "framer-motion";
import { PageHeader } from "../../components/layout";
import { staggerContainer, fadeIn } from "../../lib/animations";
import useGanttData from "./useGanttData";
import useBlockingHighlight from "./useBlockingHighlight";
import Toolbar from "./Toolbar";
import GanttTimeline from "./GanttTimeline";
import DependencyForm from "./DependencyForm";
import CriticalPathPanel from "./CriticalPathPanel";
import DependencyList from "./DependencyList";

export default function GanttDependency() {
  const {
    projects,
    selectedProjectId,
    setSelectedProjectId,
    selectedProject,
    sortedTasks,
    dependencies,
    criticalPathTaskIds,
    criticalPathDuration,
    criticalTaskSet,
    loading,
    submitting,
    error,
    notice,
    form,
    setForm,
    timelineMarkers,
    taskPlacementMap,
    dependencyLines,
    handleRefresh,
    handleCreateDependency,
    handleDeleteDependency,
  } = useGanttData();

  const {
    blockingMode,
    highlightedTaskId,
    isTaskHighlighted,
    getTaskBlockingRole,
    handleTaskClick,
    toggleBlockingMode,
  } = useBlockingHighlight(dependencies);

  return (
    <div className="space-y-6">
      <PageHeader
        title="甘特图依赖关系"
        description="任务时间线、依赖关系与关键路径分析"
      />

      {error && (
        <div className="rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">
          {error}
        </div>
      )}
      {notice && (
        <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-200">
          {notice}
        </div>
      )}

      {loading ? (
        <div className="rounded-2xl border border-slate-800 bg-slate-950/60 py-16 text-center text-slate-400">
          正在加载甘特图依赖数据...
        </div>
      ) : (
        <motion.div
          initial="hidden"
          animate="visible"
          variants={staggerContainer}
          className="space-y-6"
        >
          <Toolbar
            projects={projects}
            selectedProjectId={selectedProjectId}
            setSelectedProjectId={setSelectedProjectId}
            selectedProject={selectedProject}
            criticalPathDuration={criticalPathDuration}
            blockingMode={blockingMode}
            toggleBlockingMode={toggleBlockingMode}
            handleRefresh={handleRefresh}
          />

          <div className="grid grid-cols-1 gap-6 xl:grid-cols-[2fr,1fr]">
            <GanttTimeline
              sortedTasks={sortedTasks}
              timelineMarkers={timelineMarkers}
              taskPlacementMap={taskPlacementMap}
              dependencyLines={dependencyLines}
              criticalTaskSet={criticalTaskSet}
              blockingMode={blockingMode}
              highlightedTaskId={highlightedTaskId}
              isTaskHighlighted={isTaskHighlighted}
              getTaskBlockingRole={getTaskBlockingRole}
              handleTaskClick={handleTaskClick}
            />

            <motion.section variants={fadeIn} className="space-y-6">
              <DependencyForm
                form={form}
                setForm={setForm}
                sortedTasks={sortedTasks}
                submitting={submitting}
                selectedProjectId={selectedProjectId}
                handleCreateDependency={handleCreateDependency}
              />

              <CriticalPathPanel
                criticalPathTaskIds={criticalPathTaskIds}
                sortedTasks={sortedTasks}
              />

              <DependencyList
                dependencies={dependencies}
                sortedTasks={sortedTasks}
                criticalTaskSet={criticalTaskSet}
                handleDeleteDependency={handleDeleteDependency}
              />
            </motion.section>
          </div>
        </motion.div>
      )}
    </div>
  );
}
