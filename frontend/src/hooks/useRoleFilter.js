import { useMemo } from 'react'
import { PROJECT_STAGES } from '../lib/constants'

/**
 * 角色智能推荐 Hook
 * 根据用户角色筛选相关阶段和项目
 */
export function useRoleFilter(user, projects = []) {
  // 获取与当前用户角色相关的阶段
  const relevantStages = useMemo(() => {
    if (!user?.role) return PROJECT_STAGES
    
    // 管理员和PMC可以看所有阶段
    if (['admin', 'gm', 'pmc', 'pm', 'dept_manager'].includes(user.role)) {
      return PROJECT_STAGES
    }
    
    // 如果阶段配置中有 roles 字段，则按角色筛选
    return PROJECT_STAGES.filter(stage => {
      if (!stage.roles) return true  // 没有 roles 字段则显示所有阶段
      return stage.roles.includes(user.role)
    })
  }, [user.role])

  // 获取与当前用户相关的项目
  const myProjects = useMemo(() => {
    if (!user?.id) return projects
    
    return projects.filter(project => {
      // 项目经理
      if (project.pm_id === user.id) return true
      // 技术负责人
      if (project.te_id === user.id) return true
      // 项目成员
      if (project.members?.some(m => m.user_id === user.id)) return true
      // 客户负责人 (销售)
      if (project.sales_id === user.id) return true
      return false
    })
  }, [projects, user.id])

  // 获取所有相关阶段的key
  const relevantStageKeys = useMemo(() => {
    return relevantStages.map(s => s.key || s.code)
  }, [relevantStages])

  // 判断项目是否与当前用户相关
  const isProjectRelevant = useMemo(() => {
    const myProjectIds = new Set(myProjects.map(p => p.id))
    return (projectId) => myProjectIds.has(projectId)
  }, [myProjects])

  // 判断阶段是否与当前用户角色相关
  const isStageRelevant = useMemo(() => {
    const stageSet = new Set(relevantStageKeys)
    return (stageKey) => stageSet.has(stageKey)
  }, [relevantStageKeys])

  // 根据筛选模式过滤项目
  const filterProjects = (allProjects, mode = 'my') => {
    if (mode === 'all') return allProjects
    
    // "我相关的" 模式
    return allProjects.filter(project => {
      // 项目经理
      if (project.pm_id === user?.id) return true
      // 技术负责人
      if (project.te_id === user?.id) return true
      // 项目成员
      if (project.members?.some(m => m.user_id === user?.id)) return true
      // 销售负责人
      if (project.sales_id === user?.id) return true
      // 按角色相关阶段筛选
      const projectStage = project.stage || project.current_stage
      if (projectStage && isStageRelevant(projectStage)) return true
      return false
    })
  }

  // 按阶段分组项目
  const groupByStage = (projectList) => {
    const grouped = {}
    // PROJECT_STAGES 使用 code 字段作为 key
    PROJECT_STAGES.forEach(stage => {
      const stageKey = stage.key || stage.code
      grouped[stageKey] = []
    })
    
    projectList.forEach(project => {
      // 支持多种字段名：stage, current_stage
      // API返回的是 stage 字段（如 'S1', 'S2'）
      const stageKey = project.stage || project.current_stage || 'S1'
      if (grouped[stageKey]) {
        grouped[stageKey].push(project)
      } else {
        // 如果阶段不在预定义列表中，记录警告（但不阻塞）
        console.warn(`项目 ${project.project_code || project.id} 的阶段 "${stageKey}" 不在预定义列表中，将忽略`)
      }
    })
    
    return grouped
  }

  // 按健康度分组项目
  const groupByHealth = (projectList) => {
    const grouped = { H1: [], H2: [], H3: [], H4: [] }
    
    projectList.forEach(project => {
      const healthKey = project.health || 'H1'
      if (grouped[healthKey]) {
        grouped[healthKey].push(project)
      }
    })
    
    return grouped
  }

  // 统计各阶段项目数量
  const stageStats = useMemo(() => {
    const stats = {}
    PROJECT_STAGES.forEach(stage => {
      const stageKey = stage.key || stage.code
      stats[stageKey] = {
        total: 0,
        H1: 0,
        H2: 0,
        H3: 0,
        H4: 0,
      }
    })
    
    projects.forEach(project => {
      // 支持多种字段名：stage, current_stage
      // API返回的是 stage 字段（如 'S1', 'S2'）
      const stageKey = project.stage || project.current_stage || 'S1'
      const healthKey = project.health || 'H1'
      if (stats[stageKey]) {
        stats[stageKey].total++
        stats[stageKey][healthKey]++
      }
    })
    
    return stats
  }, [projects])

  return {
    relevantStages,
    relevantStageKeys,
    myProjects,
    isProjectRelevant,
    isStageRelevant,
    filterProjects,
    groupByStage,
    groupByHealth,
    stageStats,
  }
}

export default useRoleFilter

