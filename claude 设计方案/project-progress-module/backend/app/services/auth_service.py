"""
认证服务
处理用户登录、Token管理、密码加密等
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import hashlib
import secrets
import jwt
from passlib.context import CryptContext

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT配置
JWT_SECRET_KEY = "your-secret-key-change-in-production"
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8小时
REFRESH_TOKEN_EXPIRE_DAYS = 7


class AuthService:
    """认证服务"""
    
    def __init__(self, db_session=None):
        self.db = db_session
    
    # ==================== 密码处理 ====================
    
    @staticmethod
    def hash_password(password: str) -> str:
        """密码哈希"""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def generate_random_password(length: int = 12) -> str:
        """生成随机密码"""
        import string
        chars = string.ascii_letters + string.digits + "!@#$%"
        return ''.join(secrets.choice(chars) for _ in range(length))
    
    # ==================== Token处理 ====================
    
    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: timedelta = None) -> str:
        """创建访问令牌"""
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })
        return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    
    @staticmethod
    def create_refresh_token(data: Dict[str, Any]) -> str:
        """创建刷新令牌"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh",
            "jti": secrets.token_hex(16)  # 唯一标识
        })
        return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    
    @staticmethod
    def decode_token(token: str) -> Optional[Dict]:
        """解码Token"""
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            return None  # Token已过期
        except jwt.InvalidTokenError:
            return None  # Token无效
    
    @staticmethod
    def verify_token(token: str) -> Optional[Dict]:
        """验证Token并返回用户信息"""
        payload = AuthService.decode_token(token)
        if payload is None:
            return None
        if payload.get("type") != "access":
            return None
        return payload
    
    # ==================== 用户认证 ====================
    
    def authenticate_user(self, username: str, password: str) -> Dict[str, Any]:
        """
        用户认证
        返回: {"success": bool, "user": user_data, "message": str}
        """
        # 模拟数据库查询
        user = self._get_user_by_username(username)
        
        if not user:
            return {"success": False, "user": None, "message": "用户不存在"}
        
        if user.get("status") == "禁用":
            return {"success": False, "user": None, "message": "账户已被禁用"}
        
        if user.get("status") == "锁定":
            return {"success": False, "user": None, "message": "账户已被锁定，请联系管理员"}
        
        # 检查登录失败次数
        if user.get("login_fail_count", 0) >= 5:
            return {"success": False, "user": None, "message": "登录失败次数过多，账户已锁定"}
        
        # 验证密码
        if not self.verify_password(password, user.get("password_hash", "")):
            self._increment_login_fail_count(user["user_id"])
            remaining = 5 - user.get("login_fail_count", 0) - 1
            return {"success": False, "user": None, "message": f"密码错误，剩余尝试次数: {remaining}"}
        
        # 重置失败计数
        self._reset_login_fail_count(user["user_id"])
        
        return {"success": True, "user": user, "message": "登录成功"}
    
    def login(self, username: str, password: str, device_type: str = "web", 
              ip_address: str = None, user_agent: str = None) -> Dict[str, Any]:
        """
        用户登录
        返回Token和用户信息
        """
        # 认证
        auth_result = self.authenticate_user(username, password)
        if not auth_result["success"]:
            self._log_login(username, None, "失败", auth_result["message"], ip_address, user_agent)
            return {
                "success": False,
                "message": auth_result["message"]
            }
        
        user = auth_result["user"]
        
        # 生成Token
        token_data = {
            "sub": str(user["user_id"]),
            "username": user["username"],
            "real_name": user.get("real_name"),
            "roles": [r["role_code"] for r in user.get("roles", [])],
            "dept_id": user.get("dept_id")
        }
        
        access_token = self.create_access_token(token_data)
        refresh_token = self.create_refresh_token({"sub": str(user["user_id"])})
        
        # 保存Token
        self._save_token(user["user_id"], access_token, refresh_token, device_type, ip_address)
        
        # 更新最后登录时间
        self._update_last_login(user["user_id"], ip_address)
        
        # 记录登录日志
        self._log_login(username, user["user_id"], "成功", "登录成功", ip_address, user_agent)
        
        # 获取用户权限
        permissions = self._get_user_permissions(user["user_id"])
        menus = self._get_user_menus(user["user_id"])
        
        return {
            "success": True,
            "message": "登录成功",
            "data": {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "Bearer",
                "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                "user": {
                    "user_id": user["user_id"],
                    "username": user["username"],
                    "real_name": user.get("real_name"),
                    "avatar": user.get("avatar"),
                    "email": user.get("email"),
                    "dept_name": user.get("dept_name"),
                    "roles": user.get("roles", []),
                    "permissions": permissions,
                    "menus": menus
                }
            }
        }
    
    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """刷新访问令牌"""
        payload = self.decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            return {"success": False, "message": "无效的刷新令牌"}
        
        user_id = payload.get("sub")
        user = self._get_user_by_id(int(user_id))
        if not user:
            return {"success": False, "message": "用户不存在"}
        
        # 生成新的访问令牌
        token_data = {
            "sub": str(user["user_id"]),
            "username": user["username"],
            "real_name": user.get("real_name"),
            "roles": [r["role_code"] for r in user.get("roles", [])],
            "dept_id": user.get("dept_id")
        }
        new_access_token = self.create_access_token(token_data)
        
        return {
            "success": True,
            "data": {
                "access_token": new_access_token,
                "token_type": "Bearer",
                "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
            }
        }
    
    def logout(self, token: str) -> Dict[str, Any]:
        """登出"""
        # 将Token加入黑名单或标记为已撤销
        self._revoke_token(token)
        return {"success": True, "message": "登出成功"}
    
    def change_password(self, user_id: int, old_password: str, new_password: str) -> Dict[str, Any]:
        """修改密码"""
        user = self._get_user_by_id(user_id)
        if not user:
            return {"success": False, "message": "用户不存在"}
        
        if not self.verify_password(old_password, user["password_hash"]):
            return {"success": False, "message": "原密码错误"}
        
        # 验证新密码强度
        if len(new_password) < 8:
            return {"success": False, "message": "新密码长度至少8位"}
        
        # 更新密码
        new_hash = self.hash_password(new_password)
        self._update_password(user_id, new_hash)
        
        # 撤销所有Token，强制重新登录
        self._revoke_all_user_tokens(user_id)
        
        return {"success": True, "message": "密码修改成功，请重新登录"}
    
    def reset_password(self, user_id: int, admin_user_id: int) -> Dict[str, Any]:
        """重置密码（管理员操作）"""
        new_password = self.generate_random_password()
        new_hash = self.hash_password(new_password)
        
        self._update_password(user_id, new_hash)
        self._reset_login_fail_count(user_id)
        self._revoke_all_user_tokens(user_id)
        
        return {
            "success": True,
            "message": "密码重置成功",
            "data": {"new_password": new_password}
        }
    
    # ==================== 私有方法（模拟数据库操作）====================
    
    def _get_user_by_username(self, username: str) -> Optional[Dict]:
        """根据用户名获取用户"""
        # 模拟数据
        users = {
            "admin": {
                "user_id": 1,
                "username": "admin",
                "password_hash": self.hash_password("admin123"),
                "real_name": "系统管理员",
                "email": "admin@example.com",
                "dept_id": 1,
                "dept_name": "管理部",
                "status": "正常",
                "login_fail_count": 0,
                "roles": [{"role_id": 1, "role_code": "admin", "role_name": "管理员"}]
            },
            "pm001": {
                "user_id": 2,
                "username": "pm001",
                "password_hash": self.hash_password("123456"),
                "real_name": "张经理",
                "email": "zhangpm@example.com",
                "dept_id": 2,
                "dept_name": "项目部",
                "status": "正常",
                "login_fail_count": 0,
                "roles": [{"role_id": 2, "role_code": "pm", "role_name": "项目经理"}]
            },
            "engineer001": {
                "user_id": 3,
                "username": "engineer001",
                "password_hash": self.hash_password("123456"),
                "real_name": "李工",
                "email": "lieng@example.com",
                "dept_id": 3,
                "dept_name": "机械组",
                "status": "正常",
                "login_fail_count": 0,
                "roles": [{"role_id": 3, "role_code": "engineer", "role_name": "工程师"}]
            }
        }
        return users.get(username)
    
    def _get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """根据ID获取用户"""
        for username in ["admin", "pm001", "engineer001"]:
            user = self._get_user_by_username(username)
            if user and user["user_id"] == user_id:
                return user
        return None
    
    def _get_user_permissions(self, user_id: int) -> List[str]:
        """获取用户权限列表"""
        # 模拟数据
        permissions_map = {
            1: ["*"],  # admin拥有所有权限
            2: ["project:view", "project:edit", "task:view", "task:edit", "task:assign",
                "timesheet:view", "timesheet:approve", "report:view", "workload:view"],
            3: ["project:view", "task:view", "task:edit:own", "timesheet:view", "timesheet:create"]
        }
        return permissions_map.get(user_id, [])
    
    def _get_user_menus(self, user_id: int) -> List[Dict]:
        """获取用户菜单"""
        all_menus = [
            {"menu_id": 1, "menu_name": "工作台", "path": "/dashboard", "icon": "Dashboard", "parent_id": 0},
            {"menu_id": 2, "menu_name": "项目管理", "path": "/projects", "icon": "Folder", "parent_id": 0},
            {"menu_id": 3, "menu_name": "我的任务", "path": "/my-tasks", "icon": "List", "parent_id": 0},
            {"menu_id": 4, "menu_name": "工时管理", "path": "/timesheet", "icon": "Clock", "parent_id": 0},
            {"menu_id": 5, "menu_name": "负荷管理", "path": "/workload", "icon": "User", "parent_id": 0},
            {"menu_id": 6, "menu_name": "预警中心", "path": "/alerts", "icon": "Warning", "parent_id": 0},
            {"menu_id": 7, "menu_name": "报表中心", "path": "/reports", "icon": "DataAnalysis", "parent_id": 0},
            {"menu_id": 8, "menu_name": "系统管理", "path": "/system", "icon": "Setting", "parent_id": 0},
            {"menu_id": 81, "menu_name": "用户管理", "path": "/system/users", "icon": "", "parent_id": 8},
            {"menu_id": 82, "menu_name": "角色管理", "path": "/system/roles", "icon": "", "parent_id": 8},
            {"menu_id": 83, "menu_name": "菜单管理", "path": "/system/menus", "icon": "", "parent_id": 8},
        ]
        
        # 根据角色过滤菜单
        user = self._get_user_by_id(user_id)
        if not user:
            return []
        
        roles = [r["role_code"] for r in user.get("roles", [])]
        
        if "admin" in roles:
            return all_menus
        elif "pm" in roles:
            return [m for m in all_menus if m["menu_id"] not in [8, 81, 82, 83]]
        else:
            return [m for m in all_menus if m["menu_id"] in [1, 2, 3, 4]]
    
    def _increment_login_fail_count(self, user_id: int):
        """增加登录失败次数"""
        pass  # 实际实现需要更新数据库
    
    def _reset_login_fail_count(self, user_id: int):
        """重置登录失败次数"""
        pass
    
    def _update_last_login(self, user_id: int, ip_address: str):
        """更新最后登录时间"""
        pass
    
    def _save_token(self, user_id: int, access_token: str, refresh_token: str, 
                    device_type: str, ip_address: str):
        """保存Token"""
        pass
    
    def _revoke_token(self, token: str):
        """撤销Token"""
        pass
    
    def _revoke_all_user_tokens(self, user_id: int):
        """撤销用户所有Token"""
        pass
    
    def _update_password(self, user_id: int, password_hash: str):
        """更新密码"""
        pass
    
    def _log_login(self, username: str, user_id: int, status: str, message: str,
                   ip_address: str, user_agent: str):
        """记录登录日志"""
        pass
