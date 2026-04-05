/**
 * Sales Project Track Page — orchestrator
 * Tracks projects from the sales perspective: progress, milestones, acceptance.
 */

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { FolderKanban } from "lucide-react";
import { PageHeader } from "../../components/layout";
import { fadeIn, staggerContainer } from "../../lib/animations";
import { useSalesProjectTrack } from "./hooks/useSalesProjectTrack";
import { StatsRow } from "./StatsRow";
import { ProjectFilters } from "./ProjectFilters";
import { ProjectListItem } from "./ProjectListItem";
import { ProjectDetailPanel } from "./ProjectDetailPanel";

export default function SalesProjectTrack() {
  const {
    searchTerm,
    setSearchTerm,
    selectedStage,
    setSelectedStage,
    selectedHealth,
    setSelectedHealth,
    filteredProjects,
    stats,
  } = useSalesProjectTrack();

  const [selectedProject, setSelectedProject] = useState(null);

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      {/* Page Header */}
      <PageHeader
        title="项目跟踪"
        description="跟踪我负责的项目进度和关键节点"
      />

      {/* Stats Row */}
      <StatsRow stats={stats} />

      {/* Filters */}
      <ProjectFilters
        searchTerm={searchTerm}
        onSearchChange={setSearchTerm}
        selectedStage={selectedStage}
        onStageChange={setSelectedStage}
        selectedHealth={selectedHealth}
        onHealthChange={setSelectedHealth}
        resultCount={filteredProjects.length}
      />

      {/* Project List */}
      <motion.div variants={fadeIn} className="space-y-4">
        {filteredProjects.map((project) => (
          <ProjectListItem
            key={project.id}
            project={project}
            onClick={setSelectedProject}
          />
        ))}

        {filteredProjects.length === 0 && (
          <div className="text-center py-16">
            <FolderKanban className="w-12 h-12 mx-auto text-slate-600 mb-4" />
            <h3 className="text-lg font-medium text-white mb-2">暂无项目</h3>
            <p className="text-slate-400">没有找到符合条件的项目</p>
          </div>
        )}
      </motion.div>

      {/* Project Detail Side Panel */}
      <AnimatePresence>
        {selectedProject && (
          <ProjectDetailPanel
            project={selectedProject}
            onClose={() => setSelectedProject(null)}
          />
        )}
      </AnimatePresence>
    </motion.div>
  );
}
