// 从 localStorage 获取用户信息
export const getStoredUser = () => {
  try {
    const storedUser = localStorage.getItem("user");
    if (storedUser) {
      return JSON.parse(storedUser);
    }
  } catch (_e) {
    console.error("Failed to parse user from localStorage:", _e);
  }
  // 默认用户数据
  return {
    id: 1,
    name: "当前用户",
    role: "project_manager",
    department: "项目管理部"
  };
};
