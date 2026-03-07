"""
权限管理服务
处理角色、权限、菜单的CRUD及权限验证
"""
from typing import List, Dict, Any, Optional


class PermissionService:
    """权限管理服务"""
    
    def __init__(self, db_session=None):
        self.db = db_session
    
    # ==================== 角色管理 ====================
    
    def get_role_list(self, keyword: str = None, status: str = None,
                      page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """获取角色列表"""
        # 模拟数据
        roles = [
            {
                "role_id": 1, "role_code": "admin", "role_name": "系统管理员",
                "description": "拥有系统所有权限", "data_scope": "all",
                "status": "正常", "is_system": True, "user_count": 2,
                "created_time": "2025-01-01 00:00:00"
            },
            {
                "role_id": 2, "role_code": "pm", "role_name": "项目经理",
                "description": "负责项目整体管理", "data_scope": "dept_and_child",
                "status": "正常", "is_system": True, "user_count": 5,
                "created_time": "2025-01-01 00:00:00"
            },
            {
                "role_id": 3, "role_code": "engineer", "role_name": "工程师",
                "description": "执行具体任务", "data_scope": "self",
                "status": "正常", "is_system": True, "user_count": 50,
                "created_time": "2025-01-01 00:00:00"
            },
            {
                "role_id": 4, "role_code": "te", "role_name": "技术负责人",
                "description": "技术方案把关", "data_scope": "dept",
                "status": "正常", "is_system": False, "user_count": 8,
                "created_time": "2025-01-01 00:00:00"
            },
            {
                "role_id": 5, "role_code": "dept_manager", "role_name": "部门经理",
                "description": "部门管理", "data_scope": "dept_and_child",
                "status": "正常", "is_system": False, "user_count": 4,
                "created_time": "2025-01-01 00:00:00"
            },
            {
                "role_id": 6, "role_code": "viewer", "role_name": "只读用户",
                "description": "只能查看，不能修改", "data_scope": "all",
                "status": "正常", "is_system": False, "user_count": 10,
                "created_time": "2025-01-01 00:00:00"
            }
        ]
        
        # 过滤
        if keyword:
            roles = [r for r in roles if keyword in r["role_name"] or keyword in r["role_code"]]
        if status:
            roles = [r for r in roles if r["status"] == status]
        
        total = len(roles)
        start = (page - 1) * page_size
        end = start + page_size
        
        return {
            "total": total,
            "list": roles[start:end]
        }
    
    def get_role_detail(self, role_id: int) -> Optional[Dict]:
        """获取角色详情"""
        roles = self.get_role_list()["list"]
        for role in roles:
            if role["role_id"] == role_id:
                # 添加权限和菜单信息
                role["permissions"] = self._get_role_permissions(role_id)
                role["menus"] = self._get_role_menus(role_id)
                return role
        return None
    
    def create_role(self, data: Dict) -> Dict[str, Any]:
        """创建角色"""
        # 检查编码是否重复
        if self._check_role_code_exists(data.get("role_code")):
            return {"success": False, "message": "角色编码已存在"}
        
        # 创建角色（模拟）
        new_role_id = 100
        
        return {
            "success": True,
            "message": "创建成功",
            "data": {"role_id": new_role_id}
        }
    
    def update_role(self, role_id: int, data: Dict) -> Dict[str, Any]:
        """更新角色"""
        role = self.get_role_detail(role_id)
        if not role:
            return {"success": False, "message": "角色不存在"}
        
        if role.get("is_system"):
            return {"success": False, "message": "系统内置角色不能修改"}
        
        return {"success": True, "message": "更新成功"}
    
    def delete_role(self, role_id: int) -> Dict[str, Any]:
        """删除角色"""
        role = self.get_role_detail(role_id)
        if not role:
            return {"success": False, "message": "角色不存在"}
        
        if role.get("is_system"):
            return {"success": False, "message": "系统内置角色不能删除"}
        
        if role.get("user_count", 0) > 0:
            return {"success": False, "message": "该角色下还有用户，不能删除"}
        
        return {"success": True, "message": "删除成功"}
    
    def assign_role_permissions(self, role_id: int, permission_ids: List[int]) -> Dict[str, Any]:
        """分配角色权限"""
        role = self.get_role_detail(role_id)
        if not role:
            return {"success": False, "message": "角色不存在"}
        
        # 更新权限关联（模拟）
        return {"success": True, "message": "权限分配成功"}
    
    def assign_role_menus(self, role_id: int, menu_ids: List[int]) -> Dict[str, Any]:
        """分配角色菜单"""
        role = self.get_role_detail(role_id)
        if not role:
            return {"success": False, "message": "角色不存在"}
        
        return {"success": True, "message": "菜单分配成功"}
    
    # ==================== 权限管理 ====================
    
    def get_permission_list(self) -> List[Dict]:
        """获取权限列表（树形结构）"""
        permissions = [
            # 项目管理权限
            {"permission_id": 1, "permission_code": "project", "permission_name": "项目管理", "parent_id": 0, "resource_type": "menu"},
            {"permission_id": 11, "permission_code": "project:view", "permission_name": "查看项目", "parent_id": 1, "resource_type": "button"},
            {"permission_id": 12, "permission_code": "project:create", "permission_name": "创建项目", "parent_id": 1, "resource_type": "button"},
            {"permission_id": 13, "permission_code": "project:edit", "permission_name": "编辑项目", "parent_id": 1, "resource_type": "button"},
            {"permission_id": 14, "permission_code": "project:delete", "permission_name": "删除项目", "parent_id": 1, "resource_type": "button"},
            {"permission_id": 15, "permission_code": "project:export", "permission_name": "导出项目", "parent_id": 1, "resource_type": "button"},
            
            # 任务管理权限
            {"permission_id": 2, "permission_code": "task", "permission_name": "任务管理", "parent_id": 0, "resource_type": "menu"},
            {"permission_id": 21, "permission_code": "task:view", "permission_name": "查看任务", "parent_id": 2, "resource_type": "button"},
            {"permission_id": 22, "permission_code": "task:create", "permission_name": "创建任务", "parent_id": 2, "resource_type": "button"},
            {"permission_id": 23, "permission_code": "task:edit", "permission_name": "编辑任务", "parent_id": 2, "resource_type": "button"},
            {"permission_id": 24, "permission_code": "task:delete", "permission_name": "删除任务", "parent_id": 2, "resource_type": "button"},
            {"permission_id": 25, "permission_code": "task:assign", "permission_name": "分配任务", "parent_id": 2, "resource_type": "button"},
            {"permission_id": 26, "permission_code": "task:progress", "permission_name": "更新进度", "parent_id": 2, "resource_type": "button"},
            
            # 工时管理权限
            {"permission_id": 3, "permission_code": "timesheet", "permission_name": "工时管理", "parent_id": 0, "resource_type": "menu"},
            {"permission_id": 31, "permission_code": "timesheet:view", "permission_name": "查看工时", "parent_id": 3, "resource_type": "button"},
            {"permission_id": 32, "permission_code": "timesheet:create", "permission_name": "填报工时", "parent_id": 3, "resource_type": "button"},
            {"permission_id": 33, "permission_code": "timesheet:edit", "permission_name": "编辑工时", "parent_id": 3, "resource_type": "button"},
            {"permission_id": 34, "permission_code": "timesheet:approve", "permission_name": "审批工时", "parent_id": 3, "resource_type": "button"},
            {"permission_id": 35, "permission_code": "timesheet:export", "permission_name": "导出工时", "parent_id": 3, "resource_type": "button"},
            
            # 负荷管理权限
            {"permission_id": 4, "permission_code": "workload", "permission_name": "负荷管理", "parent_id": 0, "resource_type": "menu"},
            {"permission_id": 41, "permission_code": "workload:view", "permission_name": "查看负荷", "parent_id": 4, "resource_type": "button"},
            {"permission_id": 42, "permission_code": "workload:adjust", "permission_name": "调整分配", "parent_id": 4, "resource_type": "button"},
            
            # 预警管理权限
            {"permission_id": 5, "permission_code": "alert", "permission_name": "预警管理", "parent_id": 0, "resource_type": "menu"},
            {"permission_id": 51, "permission_code": "alert:view", "permission_name": "查看预警", "parent_id": 5, "resource_type": "button"},
            {"permission_id": 52, "permission_code": "alert:handle", "permission_name": "处理预警", "parent_id": 5, "resource_type": "button"},
            {"permission_id": 53, "permission_code": "alert:config", "permission_name": "预警配置", "parent_id": 5, "resource_type": "button"},
            
            # 报表权限
            {"permission_id": 6, "permission_code": "report", "permission_name": "报表管理", "parent_id": 0, "resource_type": "menu"},
            {"permission_id": 61, "permission_code": "report:view", "permission_name": "查看报表", "parent_id": 6, "resource_type": "button"},
            {"permission_id": 62, "permission_code": "report:export", "permission_name": "导出报表", "parent_id": 6, "resource_type": "button"},
            
            # 系统管理权限
            {"permission_id": 9, "permission_code": "system", "permission_name": "系统管理", "parent_id": 0, "resource_type": "menu"},
            {"permission_id": 91, "permission_code": "system:user", "permission_name": "用户管理", "parent_id": 9, "resource_type": "menu"},
            {"permission_id": 911, "permission_code": "system:user:view", "permission_name": "查看用户", "parent_id": 91, "resource_type": "button"},
            {"permission_id": 912, "permission_code": "system:user:create", "permission_name": "创建用户", "parent_id": 91, "resource_type": "button"},
            {"permission_id": 913, "permission_code": "system:user:edit", "permission_name": "编辑用户", "parent_id": 91, "resource_type": "button"},
            {"permission_id": 914, "permission_code": "system:user:delete", "permission_name": "删除用户", "parent_id": 91, "resource_type": "button"},
            {"permission_id": 915, "permission_code": "system:user:reset_pwd", "permission_name": "重置密码", "parent_id": 91, "resource_type": "button"},
            {"permission_id": 92, "permission_code": "system:role", "permission_name": "角色管理", "parent_id": 9, "resource_type": "menu"},
            {"permission_id": 921, "permission_code": "system:role:view", "permission_name": "查看角色", "parent_id": 92, "resource_type": "button"},
            {"permission_id": 922, "permission_code": "system:role:create", "permission_name": "创建角色", "parent_id": 92, "resource_type": "button"},
            {"permission_id": 923, "permission_code": "system:role:edit", "permission_name": "编辑角色", "parent_id": 92, "resource_type": "button"},
            {"permission_id": 924, "permission_code": "system:role:delete", "permission_name": "删除角色", "parent_id": 92, "resource_type": "button"},
            {"permission_id": 925, "permission_code": "system:role:assign", "permission_name": "分配权限", "parent_id": 92, "resource_type": "button"},
            {"permission_id": 93, "permission_code": "system:menu", "permission_name": "菜单管理", "parent_id": 9, "resource_type": "menu"},
            {"permission_id": 94, "permission_code": "system:log", "permission_name": "日志管理", "parent_id": 9, "resource_type": "menu"},
        ]
        return self._build_tree(permissions, "permission_id", "parent_id")
    
    def get_permission_flat_list(self) -> List[Dict]:
        """获取权限平铺列表"""
        return self._flatten_tree(self.get_permission_list())
    
    # ==================== 菜单管理 ====================
    
    def get_menu_list(self) -> List[Dict]:
        """获取菜单列表（树形结构）"""
        menus = [
            {"menu_id": 1, "menu_code": "dashboard", "menu_name": "工作台", "parent_id": 0, "menu_type": "menu", "path": "/dashboard", "component": "Dashboard", "icon": "Odometer", "sort_order": 1, "is_visible": True},
            {"menu_id": 2, "menu_code": "project", "menu_name": "项目管理", "parent_id": 0, "menu_type": "menu", "path": "/projects", "component": "ProjectList", "icon": "Folder", "sort_order": 2, "is_visible": True},
            {"menu_id": 3, "menu_code": "my_tasks", "menu_name": "我的任务", "parent_id": 0, "menu_type": "menu", "path": "/my-tasks", "component": "MyTasks", "icon": "List", "sort_order": 3, "is_visible": True},
            {"menu_id": 4, "menu_code": "timesheet", "menu_name": "工时管理", "parent_id": 0, "menu_type": "menu", "path": "/timesheet", "component": "TimesheetPage", "icon": "Clock", "sort_order": 4, "is_visible": True},
            {"menu_id": 5, "menu_code": "workload", "menu_name": "负荷管理", "parent_id": 0, "menu_type": "menu", "path": "/workload", "component": "WorkloadPage", "icon": "User", "sort_order": 5, "is_visible": True},
            {"menu_id": 6, "menu_code": "alerts", "menu_name": "预警中心", "parent_id": 0, "menu_type": "menu", "path": "/alerts", "component": "AlertsPage", "icon": "Warning", "sort_order": 6, "is_visible": True},
            {"menu_id": 7, "menu_code": "reports", "menu_name": "报表中心", "parent_id": 0, "menu_type": "menu", "path": "/reports", "component": "ReportsPage", "icon": "DataAnalysis", "sort_order": 7, "is_visible": True},
            {"menu_id": 8, "menu_code": "system", "menu_name": "系统管理", "parent_id": 0, "menu_type": "directory", "path": "/system", "component": "", "icon": "Setting", "sort_order": 99, "is_visible": True},
            {"menu_id": 81, "menu_code": "system_user", "menu_name": "用户管理", "parent_id": 8, "menu_type": "menu", "path": "/system/users", "component": "UserManage", "icon": "", "sort_order": 1, "is_visible": True},
            {"menu_id": 82, "menu_code": "system_role", "menu_name": "角色管理", "parent_id": 8, "menu_type": "menu", "path": "/system/roles", "component": "RoleManage", "icon": "", "sort_order": 2, "is_visible": True},
            {"menu_id": 83, "menu_code": "system_menu", "menu_name": "菜单管理", "parent_id": 8, "menu_type": "menu", "path": "/system/menus", "component": "MenuManage", "icon": "", "sort_order": 3, "is_visible": True},
            {"menu_id": 84, "menu_code": "system_dept", "menu_name": "部门管理", "parent_id": 8, "menu_type": "menu", "path": "/system/depts", "component": "DeptManage", "icon": "", "sort_order": 4, "is_visible": True},
            {"menu_id": 85, "menu_code": "system_log", "menu_name": "操作日志", "parent_id": 8, "menu_type": "menu", "path": "/system/logs", "component": "OperationLog", "icon": "", "sort_order": 5, "is_visible": True},
        ]
        return self._build_tree(menus, "menu_id", "parent_id")
    
    def create_menu(self, data: Dict) -> Dict[str, Any]:
        """创建菜单"""
        return {"success": True, "message": "创建成功", "data": {"menu_id": 100}}
    
    def update_menu(self, menu_id: int, data: Dict) -> Dict[str, Any]:
        """更新菜单"""
        return {"success": True, "message": "更新成功"}
    
    def delete_menu(self, menu_id: int) -> Dict[str, Any]:
        """删除菜单"""
        return {"success": True, "message": "删除成功"}
    
    # ==================== 用户管理 ====================
    
    def get_user_list(self, keyword: str = None, dept_id: int = None, 
                      status: str = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """获取用户列表"""
        users = [
            {"user_id": 1, "username": "admin", "real_name": "系统管理员", "employee_code": "A001", "dept_name": "管理部", "position": "管理员", "email": "admin@example.com", "mobile": "13800000001", "status": "正常", "roles": [{"role_code": "admin", "role_name": "管理员"}], "created_time": "2025-01-01"},
            {"user_id": 2, "username": "pm001", "real_name": "张经理", "employee_code": "P001", "dept_name": "项目部", "position": "项目经理", "email": "zhangpm@example.com", "mobile": "13800000002", "status": "正常", "roles": [{"role_code": "pm", "role_name": "项目经理"}], "created_time": "2025-01-01"},
            {"user_id": 3, "username": "engineer001", "real_name": "李工", "employee_code": "E001", "dept_name": "机械组", "position": "机械工程师", "email": "lieng@example.com", "mobile": "13800000003", "status": "正常", "roles": [{"role_code": "engineer", "role_name": "工程师"}], "created_time": "2025-01-01"},
            {"user_id": 4, "username": "engineer002", "real_name": "王工", "employee_code": "E002", "dept_name": "电气组", "position": "电气工程师", "email": "wangeng@example.com", "mobile": "13800000004", "status": "正常", "roles": [{"role_code": "engineer", "role_name": "工程师"}], "created_time": "2025-01-01"},
            {"user_id": 5, "username": "te001", "real_name": "赵工", "employee_code": "T001", "dept_name": "技术部", "position": "技术负责人", "email": "zhaote@example.com", "mobile": "13800000005", "status": "正常", "roles": [{"role_code": "te", "role_name": "技术负责人"}], "created_time": "2025-01-01"},
        ]
        
        if keyword:
            users = [u for u in users if keyword in u["real_name"] or keyword in u["username"] or keyword in u.get("employee_code", "")]
        if status:
            users = [u for u in users if u["status"] == status]
        
        return {"total": len(users), "list": users}
    
    def create_user(self, data: Dict) -> Dict[str, Any]:
        """创建用户"""
        from .auth_service import AuthService
        auth = AuthService()
        
        # 生成随机密码
        password = auth.generate_random_password()
        auth.hash_password(password)
        
        return {
            "success": True,
            "message": "创建成功",
            "data": {"user_id": 100, "password": password}
        }
    
    def update_user(self, user_id: int, data: Dict) -> Dict[str, Any]:
        """更新用户"""
        return {"success": True, "message": "更新成功"}
    
    def delete_user(self, user_id: int) -> Dict[str, Any]:
        """删除用户"""
        if user_id == 1:
            return {"success": False, "message": "不能删除超级管理员"}
        return {"success": True, "message": "删除成功"}
    
    def assign_user_roles(self, user_id: int, role_ids: List[int]) -> Dict[str, Any]:
        """分配用户角色"""
        return {"success": True, "message": "角色分配成功"}
    
    def update_user_status(self, user_id: int, status: str) -> Dict[str, Any]:
        """更新用户状态"""
        if user_id == 1:
            return {"success": False, "message": "不能禁用超级管理员"}
        return {"success": True, "message": f"用户状态已更新为{status}"}
    
    # ==================== 部门管理 ====================
    
    def get_dept_tree(self) -> List[Dict]:
        """获取部门树"""
        depts = [
            {"dept_id": 1, "dept_name": "金凯博自动化", "parent_id": 0, "leader_name": "总经理", "status": "正常"},
            {"dept_id": 2, "dept_name": "项目部", "parent_id": 1, "leader_name": "张总", "status": "正常"},
            {"dept_id": 3, "dept_name": "机械组", "parent_id": 2, "leader_name": "机械主管", "status": "正常"},
            {"dept_id": 4, "dept_name": "电气组", "parent_id": 2, "leader_name": "电气主管", "status": "正常"},
            {"dept_id": 5, "dept_name": "测试组", "parent_id": 2, "leader_name": "测试主管", "status": "正常"},
            {"dept_id": 6, "dept_name": "技术部", "parent_id": 1, "leader_name": "技术总监", "status": "正常"},
            {"dept_id": 7, "dept_name": "采购部", "parent_id": 1, "leader_name": "采购主管", "status": "正常"},
            {"dept_id": 8, "dept_name": "行政人事部", "parent_id": 1, "leader_name": "HR主管", "status": "正常"},
        ]
        return self._build_tree(depts, "dept_id", "parent_id")
    
    # ==================== 权限验证 ====================
    
    def check_permission(self, user_id: int, permission_code: str) -> bool:
        """检查用户是否有指定权限"""
        from .auth_service import AuthService
        auth = AuthService()
        permissions = auth._get_user_permissions(user_id)
        
        if "*" in permissions:  # 超级管理员
            return True
        
        return permission_code in permissions
    
    def check_data_scope(self, user_id: int, target_dept_id: int) -> bool:
        """检查数据权限范围"""
        # 获取用户数据权限范围
        # all: 所有数据
        # dept_and_child: 本部门及子部门
        # dept: 仅本部门
        # self: 仅自己
        return True  # 简化实现
    
    # ==================== 辅助方法 ====================
    
    def _build_tree(self, items: List[Dict], id_key: str, parent_key: str) -> List[Dict]:
        """构建树形结构"""
        item_map = {item[id_key]: {**item, "children": []} for item in items}
        tree = []
        
        for item in items:
            node = item_map[item[id_key]]
            parent_id = item[parent_key]
            if parent_id == 0:
                tree.append(node)
            elif parent_id in item_map:
                item_map[parent_id]["children"].append(node)
        
        return tree
    
    def _flatten_tree(self, tree: List[Dict], result: List[Dict] = None) -> List[Dict]:
        """展平树形结构"""
        if result is None:
            result = []
        for node in tree:
            result.append({k: v for k, v in node.items() if k != "children"})
            if node.get("children"):
                self._flatten_tree(node["children"], result)
        return result
    
    def _get_role_permissions(self, role_id: int) -> List[int]:
        """获取角色权限ID列表"""
        role_permissions = {
            1: list(range(1, 100)),  # admin全部
            2: [1, 11, 12, 13, 2, 21, 22, 23, 25, 26, 3, 31, 34, 4, 41, 5, 51, 52, 6, 61],  # pm
            3: [1, 11, 2, 21, 26, 3, 31, 32],  # engineer
        }
        return role_permissions.get(role_id, [])
    
    def _get_role_menus(self, role_id: int) -> List[int]:
        """获取角色菜单ID列表"""
        role_menus = {
            1: list(range(1, 100)),  # admin全部
            2: [1, 2, 3, 4, 5, 6, 7],  # pm
            3: [1, 2, 3, 4],  # engineer
        }
        return role_menus.get(role_id, [])
    
    def _check_role_code_exists(self, role_code: str) -> bool:
        """检查角色编码是否存在"""
        roles = self.get_role_list()["list"]
        return any(r["role_code"] == role_code for r in roles)
