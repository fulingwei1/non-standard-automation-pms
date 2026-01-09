/**
 * useECNTasks Hook
 * 管理 ECN 执行任务相关的状态和逻辑
 */
import { useState, useCallback } from 'react'
import { ecnApi } from '../../../services/api'

const initialTaskForm = {
  task_name: '',
  task_type: '',
  task_dept: '',
  task_description: '',
  assignee_id: null,
  planned_start: '',
  planned_end: '',
}

export function useECNTasks(ecnId, refetchECN) {
  const [showTaskDialog, setShowTaskDialog] = useState(false)
  const [taskForm, setTaskForm] = useState(initialTaskForm)

  // 创建任务
  const handleCreateTask = useCallback(async () => {
    if (!taskForm.task_name) {
      return {
        success: false,
        message: '请填写任务名称',
      }
    }

    try {
      await ecnApi.createTask(ecnId, taskForm)
      setShowTaskDialog(false)
      setTaskForm(initialTaskForm)
      await refetchECN()
      return {
        success: true,
        message: '任务已创建',
      }
    } catch (error) {
      return {
        success: false,
        message: '创建任务失败: ' + (error.response?.data?.detail || error.message),
      }
    }
  }, [ecnId, taskForm, refetchECN])

  // 更新任务进度
  const handleUpdateTaskProgress = useCallback(
    async (taskId, progress) => {
      try {
        await ecnApi.updateTaskProgress(taskId, progress)
        await refetchECN()
        return {
          success: true,
          message: '进度已更新',
        }
      } catch (error) {
        return {
          success: false,
          message: '更新进度失败: ' + (error.response?.data?.detail || error.message),
        }
      }
    },
    [refetchECN]
  )

  // 完成任务
  const handleCompleteTask = useCallback(
    async (taskId) => {
      try {
        await ecnApi.completeTask(taskId)
        await refetchECN()
        return {
          success: true,
          message: '任务已完成',
        }
      } catch (error) {
        return {
          success: false,
          message: '完成任务失败: ' + (error.response?.data?.detail || error.message),
        }
      }
    },
    [refetchECN]
  )

  // 重置表单
  const resetForm = useCallback(() => {
    setTaskForm(initialTaskForm)
  }, [])

  return {
    // 对话框状态
    showTaskDialog,
    setShowTaskDialog,
    // 表单状态
    taskForm,
    setTaskForm,
    // 操作方法
    handleCreateTask,
    handleUpdateTaskProgress,
    handleCompleteTask,
    resetForm,
  }
}
