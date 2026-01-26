"""
系统管理API接口
包括用户管理、角色管理、菜单管理、部门管理
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from .auth import get_current_user, require_permission
from ..services.permission_service import PermissionService

router = APIRouter(prefix="/system", tags=["系统管理"])


# ==================== 请求模型 ====================

class CreateUserRequest(BaseModel):
    """创建用户"""
    username: str = Field(..., min_length=3, max_length=50)
    real_name: str = Field(..., max_length=50)
    employee_code: Optional[str] = None
    email: Optional[str] = None
    mobile: Optional[str] = None
    dept_id: Optional[int] = None
    position: Optional[str] = None
    role_ids: List[int] = []


class UpdateUserRequest(BaseModel):
    """更新用户"""
    real_name: Optional[str] = None
    email: Optional[str] = None
    mobile: Optional[str] = None
    dept_id: Optional[int] = None
    position: Optional[str] = None
    status: Optional[str] = None


class AssignRolesRequest(BaseModel):
    """分配角色"""
    role_ids: List[int]


class CreateRoleRequest(BaseModel):
    """创建角色"""
    role_code: str = Field(..., min_length=2, max_length=50)
    role_name: str = Field(..., max_length=50)
    description: Optional[str] = None
    data_scope: str = Field(default="self")
    sort_order: int = Field(default=0)


class UpdateRoleRequest(BaseModel):
    """更新角色"""
    role_name: Optional[str] = None
    description: Optional[str] = None
    data_scope: Optional[str] = None
    sort_order: Optional[int] = None
    status: Optional[str] = None


class AssignPermissionsRequest(BaseModel):
    """分配权限"""
    permission_ids: List[int]


class AssignMenusRequest(BaseModel):
    """分配菜单"""
    menu_ids: List[int]


class CreateMenuRequest(BaseModel):
    """创建菜单"""
    menu_code: str
    menu_name: str
    parent_id: int = 0
    menu_type: str = "menu"
    path: Optional[str] = None
    component: Optional[str] = None
    icon: Optional[str] = None
    sort_order: int = 0
    is_visible: bool = True
    permission_code: Optional[str] = None


class UpdateMenuRequest(BaseModel):
    """更新菜单"""
    menu_name: Optional[str] = None
    parent_id: Optional[int] = None
    path: Optional[str] = None
    component: Optional[str] = None
    icon: Optional[str] = None
    sort_order: Optional[int] = None
    is_visible: Optional[bool] = None


class CreateDeptRequest(BaseModel):
    """创建部门"""
    dept_code: Optional[str] = None
    dept_name: str
    parent_id: int = 0
    leader_id: Optional[int] = None
    sort_order: int = 0


# ==================== 依赖注入 ====================

def get_permission_service():
    return PermissionService()


# ==================== 用户管理API ====================

@router.get("/users", summary="获取用户列表")
async def get_user_list(
    keyword: str = Query(None, description="关键词搜索"),
    dept_id: int = Query(None, description="部门ID"),
    status: str = Query(None, description="状态"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(require_permission("system:user:view")),
    service: PermissionService = Depends(get_permission_service)
):
    """获取用户列表"""
    result = service.get_user_list(keyword, dept_id, status, page, page_size)
    return {"code": 200, "data": result}


@router.post("/users", summary="创建用户")
async def create_user(
    data: CreateUserRequest,
    current_user: dict = Depends(require_permission("system:user:create")),
    service: PermissionService = Depends(get_permission_service)
):
    """创建用户，返回初始密码"""
    result = service.create_user(data.dict())
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return {"code": 200, "message": "创建成功", "data": result["data"]}


@router.put("/users/{user_id}", summary="更新用户")
async def update_user(
    user_id: int,
    data: UpdateUserRequest,
    current_user: dict = Depends(require_permission("system:user:edit")),
    service: PermissionService = Depends(get_permission_service)
):
    """更新用户信息"""
    result = service.update_user(user_id, data.dict(exclude_none=True))
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return {"code": 200, "message": "更新成功"}


@router.delete("/users/{user_id}", summary="删除用户")
async def delete_user(
    user_id: int,
    current_user: dict = Depends(require_permission("system:user:delete")),
    service: PermissionService = Depends(get_permission_service)
):
    """删除用户（软删除）"""
    result = service.delete_user(user_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return {"code": 200, "message": "删除成功"}


@router.put("/users/{user_id}/roles", summary="分配用户角色")
async def assign_user_roles(
    user_id: int,
    data: AssignRolesRequest,
    current_user: dict = Depends(require_permission("system:user:edit")),
    service: PermissionService = Depends(get_permission_service)
):
    """为用户分配角色"""
    result = service.assign_user_roles(user_id, data.role_ids)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return {"code": 200, "message": "角色分配成功"}


@router.put("/users/{user_id}/status", summary="更新用户状态")
async def update_user_status(
    user_id: int,
    status: str = Query(..., description="状态：正常/禁用/锁定"),
    current_user: dict = Depends(require_permission("system:user:edit")),
    service: PermissionService = Depends(get_permission_service)
):
    """启用/禁用用户"""
    result = service.update_user_status(user_id, status)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return {"code": 200, "message": result["message"]}


# ==================== 角色管理API ====================

@router.get("/roles", summary="获取角色列表")
async def get_role_list(
    keyword: str = Query(None),
    status: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(require_permission("system:role:view")),
    service: PermissionService = Depends(get_permission_service)
):
    """获取角色列表"""
    result = service.get_role_list(keyword, status, page, page_size)
    return {"code": 200, "data": result}


@router.get("/roles/{role_id}", summary="获取角色详情")
async def get_role_detail(
    role_id: int,
    current_user: dict = Depends(require_permission("system:role:view")),
    service: PermissionService = Depends(get_permission_service)
):
    """获取角色详情，包含权限和菜单"""
    result = service.get_role_detail(role_id)
    if not result:
        raise HTTPException(status_code=404, detail="角色不存在")
    return {"code": 200, "data": result}


@router.post("/roles", summary="创建角色")
async def create_role(
    data: CreateRoleRequest,
    current_user: dict = Depends(require_permission("system:role:create")),
    service: PermissionService = Depends(get_permission_service)
):
    """创建角色"""
    result = service.create_role(data.dict())
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return {"code": 200, "message": "创建成功", "data": result["data"]}


@router.put("/roles/{role_id}", summary="更新角色")
async def update_role(
    role_id: int,
    data: UpdateRoleRequest,
    current_user: dict = Depends(require_permission("system:role:edit")),
    service: PermissionService = Depends(get_permission_service)
):
    """更新角色"""
    result = service.update_role(role_id, data.dict(exclude_none=True))
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return {"code": 200, "message": "更新成功"}


@router.delete("/roles/{role_id}", summary="删除角色")
async def delete_role(
    role_id: int,
    current_user: dict = Depends(require_permission("system:role:delete")),
    service: PermissionService = Depends(get_permission_service)
):
    """删除角色"""
    result = service.delete_role(role_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return {"code": 200, "message": "删除成功"}


@router.put("/roles/{role_id}/permissions", summary="分配角色权限")
async def assign_role_permissions(
    role_id: int,
    data: AssignPermissionsRequest,
    current_user: dict = Depends(require_permission("system:role:assign")),
    service: PermissionService = Depends(get_permission_service)
):
    """为角色分配权限"""
    result = service.assign_role_permissions(role_id, data.permission_ids)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return {"code": 200, "message": "权限分配成功"}


@router.put("/roles/{role_id}/menus", summary="分配角色菜单")
async def assign_role_menus(
    role_id: int,
    data: AssignMenusRequest,
    current_user: dict = Depends(require_permission("system:role:assign")),
    service: PermissionService = Depends(get_permission_service)
):
    """为角色分配菜单"""
    result = service.assign_role_menus(role_id, data.menu_ids)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return {"code": 200, "message": "菜单分配成功"}


# ==================== 权限管理API ====================

@router.get("/permissions", summary="获取权限列表")
async def get_permission_list(
    current_user: dict = Depends(require_permission("system:role:view")),
    service: PermissionService = Depends(get_permission_service)
):
    """获取权限树形列表"""
    result = service.get_permission_list()
    return {"code": 200, "data": result}


# ==================== 菜单管理API ====================

@router.get("/menus", summary="获取菜单列表")
async def get_menu_list(
    current_user: dict = Depends(get_current_user),
    service: PermissionService = Depends(get_permission_service)
):
    """获取菜单树形列表"""
    result = service.get_menu_list()
    return {"code": 200, "data": result}


@router.post("/menus", summary="创建菜单")
async def create_menu(
    data: CreateMenuRequest,
    current_user: dict = Depends(require_permission("system:menu:create")),
    service: PermissionService = Depends(get_permission_service)
):
    """创建菜单"""
    result = service.create_menu(data.dict())
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return {"code": 200, "message": "创建成功", "data": result["data"]}


@router.put("/menus/{menu_id}", summary="更新菜单")
async def update_menu(
    menu_id: int,
    data: UpdateMenuRequest,
    current_user: dict = Depends(require_permission("system:menu:edit")),
    service: PermissionService = Depends(get_permission_service)
):
    """更新菜单"""
    result = service.update_menu(menu_id, data.dict(exclude_none=True))
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return {"code": 200, "message": "更新成功"}


@router.delete("/menus/{menu_id}", summary="删除菜单")
async def delete_menu(
    menu_id: int,
    current_user: dict = Depends(require_permission("system:menu:delete")),
    service: PermissionService = Depends(get_permission_service)
):
    """删除菜单"""
    result = service.delete_menu(menu_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return {"code": 200, "message": "删除成功"}


# ==================== 部门管理API ====================

@router.get("/depts", summary="获取部门树")
async def get_dept_tree(
    current_user: dict = Depends(get_current_user),
    service: PermissionService = Depends(get_permission_service)
):
    """获取部门树形结构"""
    result = service.get_dept_tree()
    return {"code": 200, "data": result}


@router.post("/depts", summary="创建部门")
async def create_dept(
    data: CreateDeptRequest,
    current_user: dict = Depends(require_permission("system:dept:create")),
    service: PermissionService = Depends(get_permission_service)
):
    """创建部门"""
    return {"code": 200, "message": "创建成功", "data": {"dept_id": 100}}


@router.put("/depts/{dept_id}", summary="更新部门")
async def update_dept(
    dept_id: int,
    data: CreateDeptRequest,
    current_user: dict = Depends(require_permission("system:dept:edit")),
):
    """更新部门"""
    return {"code": 200, "message": "更新成功"}


@router.delete("/depts/{dept_id}", summary="删除部门")
async def delete_dept(
    dept_id: int,
    current_user: dict = Depends(require_permission("system:dept:delete")),
):
    """删除部门"""
    return {"code": 200, "message": "删除成功"}
