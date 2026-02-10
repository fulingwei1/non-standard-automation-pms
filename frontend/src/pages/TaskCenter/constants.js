// 任务中心常量配置
import { statusConfigs, priorityConfigs } from "../../components/task-center/taskConfig";

export { statusConfigs, priorityConfigs };

export const statusMapToBackend = {
    pending: "PENDING",
    in_progress: "IN_PROGRESS",
    blocked: "BLOCKED",
    completed: "COMPLETED"
};

export const statusMapToFrontend = {
    PENDING: "pending",
    ACCEPTED: "pending",
    IN_PROGRESS: "in_progress",
    BLOCKED: "blocked",
    COMPLETED: "completed",
    CLOSED: "completed"
};
