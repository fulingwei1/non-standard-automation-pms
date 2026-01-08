# -*- coding: utf-8 -*-
"""
安全认证模块
"""

from datetime import datetime, timedelta
from threading import Lock
from typing import Optional
import secrets
import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from .config import settings
from ..models.base import get_session
from ..models.user import User
from ..utils.redis_client import get_redis_client

logger = logging.getLogger(__name__)

# 密码加密上下文
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# OAuth2配置
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login")

# Token 黑名单（优先使用Redis，不可用时降级到内存存储）
_token_blacklist = set()  # 内存黑名单（降级方案）
_token_blacklist_lock = Lock()

# 导出 oauth2_scheme 供其他模块使用
__all__ = [
    "verify_password",
    "get_password_hash",
    "create_access_token",
    "get_db",
    "get_current_user",
    "get_current_active_user",
    "check_permission",
    "require_permission",
    "has_procurement_access",
    "require_procurement_access",
    "has_finance_access",
    "require_finance_access",
    "has_production_access",
    "require_production_access",
    "require_project_access",
    "has_sales_assessment_access",
    "require_sales_assessment_access",
    "has_hr_access",
    "require_hr_access",
    "has_rd_project_access",
    "require_rd_project_access",
    "has_machine_document_permission",
    "has_machine_document_upload_permission",
    "oauth2_scheme",
    "revoke_token",
    "is_token_revoked",
]


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌"""
    to_encode = data.copy()
    now = datetime.utcnow()
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update(
        {
            "exp": expire,
            "iat": now,
            "jti": secrets.token_hex(16),
        }
    )
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def revoke_token(token: Optional[str]) -> None:
    """
    将 Token 加入黑名单
    
    优先使用Redis存储，如果Redis不可用则使用内存存储。
    使用JTI (JWT ID) 作为黑名单键，并设置与token相同的过期时间。
    """
    if not token:
        return
    
    try:
        # 尝试从token中提取JTI和过期时间
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM], options={"verify_exp": False}
        )
        jti = payload.get("jti")
        exp = payload.get("exp")
        
        if not jti:
            # 如果没有JTI，使用整个token的哈希值
            import hashlib
            jti = hashlib.sha256(token.encode()).hexdigest()
        
        # 尝试使用Redis
        redis_client = get_redis_client()
        if redis_client:
            try:
                # 计算剩余过期时间（秒）
                if exp:
                    now = datetime.utcnow().timestamp()
                    ttl = max(int(exp - now), 60)  # 至少保留60秒
                else:
                    # 如果没有过期时间，使用默认过期时间
                    ttl = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
                
                # 存储到Redis，key格式: jwt:blacklist:{jti}
                redis_key = f"jwt:blacklist:{jti}"
                redis_client.setex(redis_key, ttl, "1")
                logger.debug(f"Token已加入Redis黑名单: {jti[:16]}...")
                return
            except Exception as e:
                logger.warning(f"Redis操作失败，降级到内存存储: {e}")
        
        # 降级到内存存储
        with _token_blacklist_lock:
            _token_blacklist.add(token)
            logger.debug("Token已加入内存黑名单（降级模式）")
    except JWTError as e:
        logger.warning(f"无法解析token，直接加入内存黑名单: {e}")
        with _token_blacklist_lock:
            _token_blacklist.add(token)


def is_token_revoked(token: Optional[str]) -> bool:
    """
    判断 Token 是否已撤销
    
    优先检查Redis，如果Redis不可用则检查内存黑名单。
    """
    if not token:
        return False
    
    try:
        # 尝试从token中提取JTI
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM], options={"verify_exp": False}
        )
        jti = payload.get("jti")
        
        if not jti:
            # 如果没有JTI，使用整个token的哈希值
            import hashlib
            jti = hashlib.sha256(token.encode()).hexdigest()
        
        # 尝试使用Redis
        redis_client = get_redis_client()
        if redis_client:
            try:
                redis_key = f"jwt:blacklist:{jti}"
                exists = redis_client.exists(redis_key)
                if exists:
                    return True
            except Exception as e:
                logger.warning(f"Redis查询失败，降级到内存检查: {e}")
        
        # 降级到内存检查
        with _token_blacklist_lock:
            return token in _token_blacklist
    except JWTError:
        # 如果无法解析token，检查内存黑名单
        with _token_blacklist_lock:
            return token in _token_blacklist


def get_db():
    """获取数据库会话依赖"""
    db = get_session()
    try:
        yield db
    finally:
        db.close()


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    """获取当前用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if is_token_revoked(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token已失效，请重新登录",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """获取当前活跃用户"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="用户已被禁用")
    return current_user


def check_permission(user: User, permission_code: str) -> bool:
    """检查用户权限"""
    if user.is_superuser:
        return True

    for user_role in user.roles:
        for role_permission in user_role.role.permissions:
            if role_permission.permission.permission_code == permission_code:
                return True
    return False


def require_permission(permission_code: str):
    """权限装饰器依赖"""

    async def permission_checker(current_user: User = Depends(get_current_active_user)):
        if not check_permission(current_user, permission_code):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="没有执行此操作的权限"
            )
        return current_user

    return permission_checker


def has_procurement_access(user: User) -> bool:
    """检查用户是否有采购和物料管理模块的访问权限"""
    if user.is_superuser:
        return True
    
    # 定义有采购权限的角色代码
    procurement_roles = [
        'procurement_engineer',
        'procurement_manager',
        'procurement',
        'buyer',
        'pmc',
        'production_manager',
        'manufacturing_director',
        'gm',
        'chairman',
        'admin',
        'super_admin',
        'pm',
    ]
    
    # 检查用户角色
    for user_role in user.roles:
        role_code = user_role.role.role_code.lower() if user_role.role.role_code else ''
        if role_code in procurement_roles:
            return True
    
    return False


def require_procurement_access():
    """采购权限检查依赖"""
    async def procurement_checker(current_user: User = Depends(get_current_active_user)):
        if not has_procurement_access(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您没有权限访问采购和物料管理模块"
            )
        return current_user
    return procurement_checker


def has_shortage_report_access(user: User) -> bool:
    """检查用户是否有缺料上报权限"""
    if user.is_superuser:
        return True
    
    # 定义有缺料上报权限的角色代码
    shortage_report_roles = [
        # 生产一线人员
        'assembler',              # 装配技工
        'assembler_mechanic',     # 装配钳工
        'assembler_electrician',  # 装配电工
        # 仓库管理人员
        'warehouse',              # 仓库管理员
        # 计划管理人员
        'pmc',                    # PMC计划员
        # 车间管理人员（可根据实际情况调整）
        'production_manager',     # 生产部经理
        'manufacturing_director', # 制造总监
        # 管理层
        'gm',                     # 总经理
        'chairman',               # 董事长
        'admin',                  # 系统管理员
        'super_admin',            # 超级管理员
    ]
    
    # 检查用户角色
    for user_role in user.roles:
        role_code = user_role.role.role_code.lower() if user_role.role.role_code else ''
        if role_code in shortage_report_roles:
            return True
    
    return False


def require_shortage_report_access():
    """缺料上报权限检查依赖"""
    async def shortage_report_checker(current_user: User = Depends(get_current_active_user)):
        if not has_shortage_report_access(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您没有权限进行缺料上报，只有生产人员、仓管、PMC等角色可以上报缺料"
            )
        return current_user
    return shortage_report_checker


def has_finance_access(user: User) -> bool:
    """检查用户是否有财务管理模块的访问权限"""
    if user.is_superuser:
        return True
    
    # 定义有财务权限的角色代码
    finance_roles = [
        'finance_manager',
        'finance',
        '财务经理',
        '财务人员',
        'gm',
        '总经理',
        'chairman',
        '董事长',
        'admin',
        'super_admin',
        'business_support',
        '商务支持',
        '商务支持专员',
        # 销售相关角色也需要访问回款监控
        'sales_director',
        'sales_manager',
        'sales',
        '销售总监',
        '销售经理',
        '销售工程师',
    ]
    
    # 检查用户角色
    for user_role in user.roles:
        role_code = user_role.role.role_code.lower() if user_role.role.role_code else ''
        if role_code in finance_roles:
            return True
    
    return False


def require_finance_access():
    """财务权限检查依赖"""
    async def finance_checker(current_user: User = Depends(get_current_active_user)):
        if not has_finance_access(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您没有权限访问财务管理模块"
            )
        return current_user
    return finance_checker


def has_production_access(user: User) -> bool:
    """检查用户是否有生产管理模块的访问权限"""
    if user.is_superuser:
        return True
    
    # 定义有生产权限的角色代码
    production_roles = [
        'production_manager',
        'manufacturing_director',
        '生产部经理',
        '制造总监',
        'pmc',
        'assembler',
        'assembler_mechanic',
        'assembler_electrician',
        '装配技工',
        '装配钳工',
        '装配电工',
        'gm',
        '总经理',
        'chairman',
        '董事长',
        'admin',
        'super_admin',
    ]
    
    # 检查用户角色
    for user_role in user.roles:
        role_code = user_role.role.role_code.lower() if user_role.role.role_code else ''
        if role_code in production_roles:
            return True
    
    return False


def require_production_access():
    """生产权限检查依赖"""
    async def production_checker(current_user: User = Depends(get_current_active_user)):
        if not has_production_access(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您没有权限访问生产管理模块"
            )
        return current_user
    return production_checker


def check_project_access(project_id: int, current_user: User, db: Session) -> bool:
    """
    检查用户是否有权限访问指定项目
    
    Args:
        project_id: 项目ID
        current_user: 当前用户
        db: 数据库会话
    
    Returns:
        True: 有权限
        False: 无权限
    """
    from app.services.data_scope_service import DataScopeService
    return DataScopeService.check_project_access(db, current_user, project_id)


def require_project_access():
    """
    项目访问权限检查依赖（需要在路由中使用）
    
    使用方式：
        @router.get("/projects/{project_id}")
        def get_project(
            project_id: int,
            current_user: User = Depends(security.get_current_active_user),
            db: Session = Depends(deps.get_db),
            _: None = Depends(lambda p=project_id, u=current_user, d=db: 
                security.check_project_access(p, u, d) or None)
        ):
    """
    def project_access_checker(
        project_id: int,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        if not check_project_access(project_id, current_user, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您没有权限访问该项目"
            )
        return current_user
    return project_access_checker


def has_sales_assessment_access(user: User) -> bool:
    """检查用户是否有技术评估权限"""
    if user.is_superuser:
        return True
    
    # 定义有技术评估权限的角色代码
    assessment_roles = [
        'sales',
        'sales_engineer',
        'sales_manager',
        'sales_director',
        'presales_engineer',
        'presales_manager',
        'te',  # 技术工程师
        'technical_engineer',
        'admin',
        'super_admin',
    ]
    
    # 检查用户角色
    for user_role in user.roles:
        role_code = user_role.role.role_code.lower() if user_role.role.role_code else ''
        if role_code in assessment_roles:
            return True
    
    return False


def require_sales_assessment_access():
    """技术评估权限检查依赖"""
    async def assessment_checker(current_user: User = Depends(get_current_active_user)):
        if not has_sales_assessment_access(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您没有权限进行技术评估"
            )
        return current_user
    return assessment_checker


def has_hr_access(user: User) -> bool:
    """检查用户是否有人力资源管理模块的访问权限（奖金规则配置等）"""
    if user.is_superuser:
        return True
    
    # 定义有人力资源权限的角色代码
    hr_roles = [
        'hr_manager',           # 人力资源经理
        '人事经理',
        'hr',                   # 人力资源专员
        '人事',
        'gm',                   # 总经理
        '总经理',
        'chairman',             # 董事长
        '董事长',
        'admin',                # 系统管理员
        'super_admin',          # 超级管理员
    ]
    
    # 检查用户角色
    for user_role in user.roles:
        role_code = user_role.role.role_code.lower() if user_role.role.role_code else ''
        role_name = user_role.role.role_name.lower() if user_role.role.role_name else ''
        if role_code in hr_roles or role_name in hr_roles:
            return True
    
    return False


def require_hr_access():
    """人力资源权限检查依赖"""
    async def hr_checker(current_user: User = Depends(get_current_active_user)):
        if not has_hr_access(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您没有权限访问人力资源配置功能，仅人力资源经理可以配置"
            )
        return current_user
    return hr_checker


# 研发项目角色列表
RD_PROJECT_ROLES = [
    "admin", "super_admin", "管理员", "系统管理员",
    "tech_dev_manager", "技术开发部经理",
    "rd_engineer", "研发工程师",
    "me_engineer", "机械工程师",
    "ee_engineer", "电气工程师",
    "sw_engineer", "软件工程师",
    "te_engineer", "测试工程师",
    "me_dept_manager", "机械部经理",
    "ee_dept_manager", "电气部经理",
    "te_dept_manager", "测试部经理",
    "project_dept_manager", "项目部经理",
    "pm", "pmc", "项目经理",
    "gm", "总经理",
    "chairman", "董事长",
]

def has_rd_project_access(user: User) -> bool:
    """检查用户是否有研发项目访问权限"""
    if user.is_superuser:
        return True
    role = user.role
    if role in RD_PROJECT_ROLES:
        return True
    return False

def require_rd_project_access():
    """研发项目权限检查依赖"""
    async def rd_project_checker(current_user: User = Depends(get_current_active_user)):
        if not has_rd_project_access(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您没有权限访问研发项目管理功能"
            )
        return current_user
    return rd_project_checker


# ==================== 设备文档权限（上传和下载） ====================

def has_machine_document_permission(user: User, doc_type: str) -> bool:
    """
    检查用户是否有权限访问（上传/下载）指定类型的设备文档
    
    文档类型与角色权限映射：
    - CIRCUIT_DIAGRAM: 电气工程师、PLC工程师、研发工程师、项目经理
    - PLC_PROGRAM: PLC工程师、电气工程师、研发工程师、项目经理
    - LABELWORK_PROGRAM: 电气工程师、PLC工程师、研发工程师、项目经理
    - BOM_DOCUMENT: PMC、物料工程师、项目经理、工程师
    - FAT_DOCUMENT: 质量工程师、项目经理、总经理
    - SAT_DOCUMENT: 质量工程师、项目经理、总经理
    - OTHER: 项目成员（项目经理、工程师、PMC等）
    """
    if user.is_superuser:
        return True
    
    # 获取用户角色代码列表（转换为小写以便匹配）
    user_role_codes = []
    user_role_names = []
    for user_role in user.roles:
        role_code = user_role.role.role_code.upper() if user_role.role.role_code else ''
        role_name = user_role.role.role_name.lower() if user_role.role.role_name else ''
        if role_code:
            user_role_codes.append(role_code)
        if role_name:
            user_role_names.append(role_name)
    
    doc_type = doc_type.upper()
    
    # 根据文档类型检查权限
    if doc_type == "CIRCUIT_DIAGRAM":
        # 电路图：电气工程师、PLC工程师、研发工程师、项目经理
        allowed_codes = ["ENGINEER", "PM", "PMC", "RD_ENGINEER", "GM", "ADMIN"]
        allowed_names = ["电气", "plc", "研发", "工程师", "项目经理", "pm"]
        return any(code in user_role_codes for code in allowed_codes) or \
               any(name in user_role_names for name in allowed_names)
    
    elif doc_type == "PLC_PROGRAM":
        # PLC程序：PLC工程师、电气工程师、研发工程师、项目经理
        allowed_codes = ["ENGINEER", "PM", "PMC", "RD_ENGINEER", "GM", "ADMIN"]
        allowed_names = ["电气", "plc", "研发", "工程师", "项目经理", "pm"]
        return any(code in user_role_codes for code in allowed_codes) or \
               any(name in user_role_names for name in allowed_names)
    
    elif doc_type == "LABELWORK_PROGRAM":
        # Labelwork程序：电气工程师、PLC工程师、研发工程师、项目经理
        allowed_codes = ["ENGINEER", "PM", "PMC", "RD_ENGINEER", "GM", "ADMIN"]
        allowed_names = ["电气", "plc", "研发", "工程师", "项目经理", "pm"]
        return any(code in user_role_codes for code in allowed_codes) or \
               any(name in user_role_names for name in allowed_names)
    
    elif doc_type == "BOM_DOCUMENT":
        # BOM文档：PMC、物料工程师、项目经理、工程师
        allowed_codes = ["PMC", "PM", "ENGINEER", "GM", "ADMIN"]
        allowed_names = ["物料", "pmc", "项目经理", "pm", "工程师"]
        return any(code in user_role_codes for code in allowed_codes) or \
               any(name in user_role_names for name in allowed_names)
    
    elif doc_type == "FAT_DOCUMENT":
        # FAT文档：质量工程师、项目经理、总经理
        allowed_codes = ["QA", "QUALITY", "PM", "GM", "ADMIN"]
        allowed_names = ["质量", "qa", "项目经理", "pm", "总经理"]
        return any(code in user_role_codes for code in allowed_codes) or \
               any(name in user_role_names for name in allowed_names)
    
    elif doc_type == "SAT_DOCUMENT":
        # SAT文档：质量工程师、项目经理、总经理
        allowed_codes = ["QA", "QUALITY", "PM", "GM", "ADMIN"]
        allowed_names = ["质量", "qa", "项目经理", "pm", "总经理"]
        return any(code in user_role_codes for code in allowed_codes) or \
               any(name in user_role_names for name in allowed_names)
    
    elif doc_type == "OTHER":
        # 其他文档：项目成员都可以访问
        allowed_codes = ["PM", "ENGINEER", "PMC", "QA", "RD_ENGINEER", "GM", "ADMIN"]
        allowed_names = ["项目经理", "pm", "工程师", "pmc", "质量", "qa", "研发"]
        return any(code in user_role_codes for code in allowed_codes) or \
               any(name in user_role_names for name in allowed_names)
    
    # 默认：项目成员都可以访问
    allowed_codes = ["PM", "ENGINEER", "PMC", "QA", "GM", "ADMIN"]
    allowed_names = ["项目经理", "pm", "工程师", "pmc", "质量", "qa"]
    return any(code in user_role_codes for code in allowed_codes) or \
           any(name in user_role_names for name in allowed_names)


def has_machine_document_upload_permission(user: User, doc_type: str) -> bool:
    """
    检查用户是否有权限上传指定类型的设备文档（兼容性函数，内部调用通用权限检查）
    """
    # 调用通用权限检查函数
    return has_machine_document_permission(user, doc_type)
