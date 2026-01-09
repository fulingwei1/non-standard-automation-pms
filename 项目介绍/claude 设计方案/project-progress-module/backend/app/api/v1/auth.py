"""
认证相关API接口
"""
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from pydantic import BaseModel, Field
from typing import Optional, List
from ..services.auth_service import AuthService
from ..services.permission_service import PermissionService

router = APIRouter(prefix="/auth", tags=["认证管理"])


# ==================== 请求/响应模型 ====================

class LoginRequest(BaseModel):
    """登录请求"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")
    captcha: Optional[str] = Field(None, description="验证码")
    remember: bool = Field(False, description="记住登录")


class LoginResponse(BaseModel):
    """登录响应"""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    """刷新Token请求"""
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    """修改密码请求"""
    old_password: str = Field(..., min_length=6)
    new_password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)


class ResetPasswordRequest(BaseModel):
    """重置密码请求"""
    user_id: int


# ==================== 依赖注入 ====================

def get_auth_service():
    return AuthService()


def get_current_user(authorization: str = Header(None)):
    """获取当前登录用户"""
    if not authorization:
        raise HTTPException(status_code=401, detail="未提供认证信息")
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="认证方式错误")
    except ValueError:
        raise HTTPException(status_code=401, detail="认证格式错误")
    
    auth = AuthService()
    payload = auth.verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token已过期或无效")
    
    return {
        "user_id": int(payload.get("sub")),
        "username": payload.get("username"),
        "real_name": payload.get("real_name"),
        "roles": payload.get("roles", []),
        "dept_id": payload.get("dept_id")
    }


def require_permission(permission_code: str):
    """权限验证装饰器"""
    def dependency(current_user: dict = Depends(get_current_user)):
        perm_service = PermissionService()
        if not perm_service.check_permission(current_user["user_id"], permission_code):
            raise HTTPException(status_code=403, detail="没有操作权限")
        return current_user
    return dependency


# ==================== API接口 ====================

@router.post("/login", summary="用户登录")
async def login(request: Request, data: LoginRequest, 
                auth: AuthService = Depends(get_auth_service)):
    """
    用户登录接口
    - 支持用户名密码登录
    - 返回access_token和refresh_token
    - 失败5次后锁定账户
    """
    # 获取客户端信息
    ip_address = request.client.host
    user_agent = request.headers.get("user-agent", "")
    
    result = auth.login(
        username=data.username,
        password=data.password,
        device_type="web",
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    if not result["success"]:
        raise HTTPException(status_code=401, detail=result["message"])
    
    return {"code": 200, "message": "登录成功", "data": result["data"]}


@router.post("/logout", summary="用户登出")
async def logout(authorization: str = Header(None),
                 auth: AuthService = Depends(get_auth_service)):
    """用户登出，使Token失效"""
    if authorization:
        try:
            _, token = authorization.split()
            auth.logout(token)
        except:
            pass
    return {"code": 200, "message": "登出成功"}


@router.post("/refresh", summary="刷新Token")
async def refresh_token(data: RefreshTokenRequest,
                        auth: AuthService = Depends(get_auth_service)):
    """使用refresh_token获取新的access_token"""
    result = auth.refresh_access_token(data.refresh_token)
    if not result["success"]:
        raise HTTPException(status_code=401, detail=result["message"])
    return {"code": 200, "message": "刷新成功", "data": result["data"]}


@router.get("/userinfo", summary="获取当前用户信息")
async def get_userinfo(current_user: dict = Depends(get_current_user),
                       auth: AuthService = Depends(get_auth_service)):
    """获取当前登录用户的详细信息"""
    user = auth._get_user_by_id(current_user["user_id"])
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    permissions = auth._get_user_permissions(current_user["user_id"])
    menus = auth._get_user_menus(current_user["user_id"])
    
    return {
        "code": 200,
        "data": {
            "user_id": user["user_id"],
            "username": user["username"],
            "real_name": user.get("real_name"),
            "avatar": user.get("avatar"),
            "email": user.get("email"),
            "mobile": user.get("mobile"),
            "dept_id": user.get("dept_id"),
            "dept_name": user.get("dept_name"),
            "position": user.get("position"),
            "roles": user.get("roles", []),
            "permissions": permissions,
            "menus": menus
        }
    }


@router.put("/password", summary="修改密码")
async def change_password(data: ChangePasswordRequest,
                          current_user: dict = Depends(get_current_user),
                          auth: AuthService = Depends(get_auth_service)):
    """修改当前用户密码"""
    if data.new_password != data.confirm_password:
        raise HTTPException(status_code=400, detail="两次输入的密码不一致")
    
    result = auth.change_password(
        current_user["user_id"],
        data.old_password,
        data.new_password
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return {"code": 200, "message": result["message"]}


@router.post("/reset-password", summary="重置密码(管理员)")
async def reset_password(data: ResetPasswordRequest,
                         current_user: dict = Depends(require_permission("system:user:reset_pwd")),
                         auth: AuthService = Depends(get_auth_service)):
    """管理员重置用户密码"""
    result = auth.reset_password(data.user_id, current_user["user_id"])
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return {
        "code": 200,
        "message": "密码重置成功",
        "data": {"new_password": result["data"]["new_password"]}
    }


@router.get("/captcha", summary="获取验证码")
async def get_captcha():
    """获取图形验证码"""
    # 简化实现，实际应生成图形验证码
    import uuid
    captcha_id = str(uuid.uuid4())
    return {
        "code": 200,
        "data": {
            "captcha_id": captcha_id,
            "captcha_image": "data:image/png;base64,..."  # 实际应返回base64图片
        }
    }
