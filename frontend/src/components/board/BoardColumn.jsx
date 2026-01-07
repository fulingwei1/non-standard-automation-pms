import { memo, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { cn } from '../../lib/utils'
import { HEALTH_CONFIG } from '../../lib/constants'
import ProjectCard from './ProjectCard'
import {
  ChevronDown,
  ChevronUp,
  MoreHorizontal,
} from 'lucide-react'

/**
 * 看板列组件
 * 显示单个阶段的所有项目
 */
const BoardColumn = memo(function BoardColumn({
  stage,
  projects = [],
  isRelevant = false,
  onProjectClick,
  isProjectRelevant,
  collapsed = false,
  onToggleCollapse,
}) {
  const [isCollapsed, setIsCollapsed] = useState(collapsed)
  
  // 按健康度统计
  const healthStats = {
    H1: projects.filter(p => p.health === 'H1').length,
    H2: projects.filter(p => p.health === 'H2').length,
    H3: projects.filter(p => p.health === 'H3').length,
    H4: projects.filter(p => p.health === 'H4').length,
  }

  const toggleCollapse = () => {
    setIsCollapsed(!isCollapsed)
    onToggleCollapse?.(stage.key, !isCollapsed)
  }

  return (
    <div
      className={cn(
        'flex flex-col min-w-[280px] max-w-[320px] h-full',
        'bg-surface-0/50 rounded-xl border border-white/5',
        'transition-all duration-300',
        isRelevant && 'ring-1 ring-primary/20 bg-primary/5'
      )}
    >
      {/* 列头部 */}
      <div 
        className={cn(
          'flex items-center justify-between p-3 border-b border-white/5',
          'cursor-pointer hover:bg-white/5 transition-colors rounded-t-xl'
        )}
        onClick={toggleCollapse}
      >
        <div className="flex items-center gap-2">
          {/* 阶段编号 */}
          <span className={cn(
            'w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold',
            isRelevant ? 'bg-primary/20 text-primary' : 'bg-white/10 text-white'
          )}>
            {stage.key}
          </span>
          
          {/* 阶段名称 */}
          <div>
            <h3 className="font-medium text-white text-sm">{stage.name}</h3>
            <p className="text-xs text-slate-500">{projects.length} 个项目</p>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          {/* 健康度统计点 */}
          <div className="flex items-center gap-1">
            {healthStats.H3 > 0 && (
              <span className="flex items-center gap-0.5">
                <span className="w-2 h-2 rounded-full bg-red-500" />
                <span className="text-xs text-red-400">{healthStats.H3}</span>
              </span>
            )}
            {healthStats.H2 > 0 && (
              <span className="flex items-center gap-0.5">
                <span className="w-2 h-2 rounded-full bg-amber-500" />
                <span className="text-xs text-amber-400">{healthStats.H2}</span>
              </span>
            )}
            {healthStats.H1 > 0 && (
              <span className="flex items-center gap-0.5">
                <span className="w-2 h-2 rounded-full bg-emerald-500" />
                <span className="text-xs text-emerald-400">{healthStats.H1}</span>
              </span>
            )}
          </div>
          
          {/* 展开/收起按钮 */}
          {isCollapsed ? (
            <ChevronDown className="w-4 h-4 text-slate-400" />
          ) : (
            <ChevronUp className="w-4 h-4 text-slate-400" />
          )}
        </div>
      </div>

      {/* 项目列表 */}
      <AnimatePresence>
        {!isCollapsed && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="flex-1 overflow-hidden"
          >
            <div className="p-2 space-y-2 overflow-y-auto max-h-[calc(100vh-280px)] custom-scrollbar">
              {projects.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-8 text-slate-500">
                  <MoreHorizontal className="w-8 h-8 mb-2 opacity-30" />
                  <p className="text-sm">暂无项目</p>
                </div>
              ) : (
                projects.map((project) => (
                  <ProjectCard
                    key={project.id}
                    project={project}
                    isRelevant={isProjectRelevant?.(project.id)}
                    onClick={() => onProjectClick?.(project)}
                  />
                ))
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* 收起时的简略信息 */}
      {isCollapsed && projects.length > 0 && (
        <div className="p-2">
          <div className="flex items-center justify-center gap-2 py-2 text-slate-500 text-sm">
            <span>{projects.length} 个项目</span>
            <div className="flex gap-1">
              {Object.entries(healthStats).map(([key, count]) => (
                count > 0 && (
                  <span
                    key={key}
                    className={cn(
                      'w-4 h-4 rounded text-xs flex items-center justify-center',
                      HEALTH_CONFIG[key].bgClass,
                      HEALTH_CONFIG[key].textClass
                    )}
                  >
                    {count}
                  </span>
                )
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
})

export default BoardColumn

