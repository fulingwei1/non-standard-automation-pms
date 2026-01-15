import { api } from "./client.js";



export const taskCenterApi = {
  getOverview: () => api.get("/task-center/overview"),
  myTasks: (params) => api.get("/task-center/my-tasks", { params }),
  getMyTasks: (params) => api.get("/task-center/my-tasks", { params }),
  getTask: (id) => api.get(`/task-center/tasks/${id}`),
  createTask: (data) => api.post("/task-center/tasks", data),
  updateTask: (id, data) => api.put(`/task-center/tasks/${id}`, data),
  updateProgress: (id, data) =>
    api.put(`/task-center/tasks/${id}/progress`, data),
  completeTask: (id) => api.put(`/task-center/tasks/${id}/complete`),
  transferTask: (id, data) =>
    api.post(`/task-center/tasks/${id}/transfer`, data),
  acceptTransfer: (id) => api.put(`/task-center/tasks/${id}/accept`),
  rejectTransfer: (id) => api.put(`/task-center/tasks/${id}/reject`),
  addComment: (id, data) => api.post(`/task-center/tasks/${id}/comments`, data),
  getComments: (id) => api.get(`/task-center/tasks/${id}/comments`),
};
