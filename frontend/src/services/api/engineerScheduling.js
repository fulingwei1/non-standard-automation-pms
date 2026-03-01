import api from "./client.js";

// 工程师调度 API
export const engineerSchedulingApi = {
  // 获取工程师负载看板
  getWorkloadBoard: () =>
    api.get('/engineer-scheduling/workload-board'),
  
  // 获取工程师可用时间
  getEngineerAvailability: (engineerId, startDate, endDate) =>
    api.get(`/engineer-scheduling/engineers/${engineerId}/availability`, {
      params: { start_date: startDate, end_date: endDate }
    }),
  
  // 分配工程师到项目
  assignEngineer: (projectId, engineerId, allocation) =>
    api.post('/engineer-scheduling/assignments', {
      project_id: projectId,
      engineer_id: engineerId,
      allocation_pct: allocation
    }),
  
  // 更新分配
  updateAssignment: (assignmentId, allocation) =>
    api.put(`/engineer-scheduling/assignments/${assignmentId}`, {
      allocation_pct: allocation
    }),
  
  // 删除分配
  deleteAssignment: (assignmentId) =>
    api.delete(`/engineer-scheduling/assignments/${assignmentId}`),
};
