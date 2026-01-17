# -*- coding: utf-8 -*-
"""
权限检查模块 - 采购、财务、生产、项目、人事等权限
"""

import logging
from typing import Any, List, Optional

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..models.user import User
from .auth import get_current_active_user, get_db

logger = logging.getLogger(__name__)

__all__ = [
    "has_procurement_access",
    "require_procurement_access",
    "has_shortage_report_access",
    "require_shortage_report_access",
    "has_finance_access",
    "require_finance_access",
    "has_production_access",
    "require_production_access",
    "check_project_access",
    "require_project_access",
    "has_hr_access",
    "require_hr_access",
    "has_timesheet_approval_access",
    "require_timesheet_approval_access",
    "check_timesheet_approval_permission",
    "has_scheduler_admin_access",
    "require_scheduler_admin_access",
    "RD_PROJECT_ROLES",
    "has_rd_project_access",
    "require_rd_project_access",
    "has_machine_document_permission",
    "has_machine_document_upload_permission",
]


def has_procurement_access(user: User) -> bool:
    """检查用户是否有采购和物料管理模块的访问权限"""
    if user.is_superuser:
        return True

    # 定义有采购权限的角色代码
    procurement_roles = [
        "procurement_engineer",
        "procurement_manager",
        "procurement",
        "buyer",
        "pmc",
        "production_manager",
        "manufacturing_director",
        "gm",
        "chairman",
        "admin",
        "super_admin",
        "pm",
    ]

    # 检查用户角色
    for user_role in user.roles:
        role_code = user_role.role.role_code.lower() if user_role.role.role_code else ""
        if role_code in procurement_roles:
            return True

    return False


def require_procurement_access():
    """采购权限检查依赖"""

    async def procurement_checker(
        current_user: User = Depends(get_current_active_user),
    ):
        if not has_procurement_access(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您没有权限访问采购和物料管理模块",
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
        "assembler",  # 装配技工
        "assembler_mechanic",  # 装配钳工
        "assembler_electrician",  # 装配电工
        # 仓库管理人员
        "warehouse",  # 仓库管理员
        # 计划管理人员
        "pmc",  # PMC计划员
        # 车间管理人员（可根据实际情况调整）
        "production_manager",  # 生产部经理
        "manufacturing_director",  # 制造总监
        # 管理层
        "gm",  # 总经理
        "chairman",  # 董事长
        "admin",  # 系统管理员
        "super_admin",  # 超级管理员
    ]

    # 检查用户角色
    for user_role in user.roles:
        role_code = user_role.role.role_code.lower() if user_role.role.role_code else ""
        if role_code in shortage_report_roles:
            return True

    return False


def require_shortage_report_access():
    """缺料上报权限检查依赖"""

    async def shortage_report_checker(
        current_user: User = Depends(get_current_active_user),
    ):
        if not has_shortage_report_access(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您没有权限进行缺料上报，只有生产人员、仓管、PMC等角色可以上报缺料",
            )
        return current_user

    return shortage_report_checker


def has_finance_access(user: User) -> bool:
    """
    检查用户是否有财务管理模块的访问权限

    注意：此配置需要与前端 frontend/src/lib/roleConfig.js 中的 hasFinanceAccess() 保持同步
    当修改前端权限时，请同步更新此函数
    """
    if user.is_superuser:
        return True

    # 定义有财务权限的角色代码
    # 与前端 frontend/src/lib/roleConfig.js 中的 hasFinanceAccess() 保持一致
    finance_roles = [
        # 管理层
        "admin",
        "super_admin",
        "chairman",
        "gm",
        "管理员",
        "系统管理员",
        "董事长",
        "总经理",
        # 财务部门
        "finance_manager",
        "finance",
        "accountant",
        "财务经理",
        "财务人员",
        "会计",
        # 销售部门（需要访问回款监控）
        "sales_director",
        "sales_manager",
        "sales",
        "销售总监",
        "销售经理",
        "销售工程师",
        "business_support",
        "presales_manager",
        "presales",
        "商务支持",
        "商务支持专员",
        "售前经理",
        "售前技术工程师",
        # 项目管理部门（需要查看项目回款情况）
        "project_dept_manager",
        "pmc",
        "pm",
        "项目部经理",
        "项目经理",
    ]

    # 检查用户角色
    for user_role in user.roles:
        role_code = user_role.role.role_code.lower() if user_role.role.role_code else ""
        # 同时检查英文和中文角色名
        role_name = user_role.role.role_name if user_role.role.role_name else ""
        if role_code in finance_roles or role_name in finance_roles:
            return True

    return False


def require_finance_access():
    """财务权限检查依赖"""

    async def finance_checker(current_user: User = Depends(get_current_active_user)):
        if not has_finance_access(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您没有权限访问财务管理模块",
            )
        return current_user

    return finance_checker


def has_production_access(user: User) -> bool:
    """检查用户是否有生产管理模块的访问权限"""
    if user.is_superuser:
        return True

    # 定义有生产权限的角色代码
    production_roles = [
        "production_manager",
        "manufacturing_director",
        "生产部经理",
        "制造总监",
        "pmc",
        "assembler",
        "assembler_mechanic",
        "assembler_electrician",
        "装配技工",
        "装配钳工",
        "装配电工",
        "gm",
        "总经理",
        "chairman",
        "董事长",
        "admin",
        "super_admin",
    ]

    # 检查用户角色
    for user_role in user.roles:
        role_code = user_role.role.role_code.lower() if user_role.role.role_code else ""
        if role_code in production_roles:
            return True

    return False


def require_production_access():
    """生产权限检查依赖"""

    async def production_checker(current_user: User = Depends(get_current_active_user)):
        if not has_production_access(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您没有权限访问生产管理模块",
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
        db: Session = Depends(get_db),
    ):
        if not check_project_access(project_id, current_user, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="您没有权限访问该项目"
            )
        return current_user

    return project_access_checker


def has_hr_access(user: User) -> bool:
    """检查用户是否有人力资源管理模块的访问权限（奖金规则配置等）"""
    if user.is_superuser:
        return True

    # 定义有人力资源权限的角色代码
    hr_roles = [
        "hr_manager",  # 人力资源经理
        "人事经理",
        "hr",  # 人力资源专员
        "人事",
        "gm",  # 总经理
        "总经理",
        "chairman",  # 董事长
        "董事长",
        "admin",  # 系统管理员
        "super_admin",  # 超级管理员
    ]

    # 检查用户角色
    for user_role in user.roles:
        role_code = user_role.role.role_code.lower() if user_role.role.role_code else ""
        role_name = user_role.role.role_name.lower() if user_role.role.role_name else ""
        if role_code in hr_roles or role_name in hr_roles:
            return True

    return False


def require_hr_access():
    """人力资源权限检查依赖"""

    async def hr_checker(current_user: User = Depends(get_current_active_user)):
        if not has_hr_access(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您没有权限访问人力资源配置功能，仅人力资源经理可以配置",
            )
        return current_user

    return hr_checker


def has_timesheet_approval_access(
    user: User,
    db: Session,
    timesheet_user_id: Optional[int] = None,
    timesheet_dept_id: Optional[int] = None,
) -> bool:
    """
    检查用户是否有工时审批权限

    工时审批权限包括：
    1. 项目经理可以审批本项目的工时
    2. 部门经理可以审批本部门的工时
    3. 管理员可以审批所有工时

    Args:
        user: 当前用户
        db: 数据库会话
        timesheet_user_id: 工时提交人的用户ID
        timesheet_dept_id: 工时提交人的部门ID

    Returns:
        bool: 是否有审批权限
    """
    if user.is_superuser:
        return True

    # 检查是否有工时审批权限角色
    approval_roles = [
        "pm",  # 项目经理
        "project_manager",  # 项目经理
        "项目经理",
        "dept_manager",  # 部门经理
        "department_manager",  # 部门经理
        "部门经理",
        "hr_manager",  # 人事经理
        "人事经理",
        "gm",  # 总经理
        "总经理",
        "admin",  # 管理员
        "super_admin",
    ]

    # 检查用户角色
    has_approval_role = False
    for user_role in user.roles:
        role_code = user_role.role.role_code.lower() if user_role.role.role_code else ""
        role_name = user_role.role.role_name.lower() if user_role.role.role_name else ""
        if role_code in approval_roles or role_name in approval_roles:
            has_approval_role = True
            break

    if not has_approval_role:
        return False

    # 如果没有具体的工时信息，只检查角色
    if timesheet_user_id is None and timesheet_dept_id is None:
        return True

    # 检查项目经理权限：是否是工时提交人所在项目的项目经理
    from app.models.project import Project

    if timesheet_user_id:
        # 查找该用户参与的项目，其中当前用户是项目经理
        projects_as_pm = db.query(Project).filter(Project.pm_id == user.id).all()
        project_ids = [p.id for p in projects_as_pm]

        # 检查工时是否属于这些项目
        from app.models.timesheet import Timesheet

        timesheet_in_pm_project = (
            db.query(Timesheet)
            .filter(
                Timesheet.id
                == timesheet_user_id,  # 这里实际应该是timesheet的project_id检查
                Timesheet.project_id.in_(project_ids),
            )
            .first()
        )
        if timesheet_in_pm_project:
            return True

    # 检查部门经理权限：是否是同一部门
    if timesheet_dept_id and user.department_id:
        if user.department_id == timesheet_dept_id:
            return True

    return True  # 有审批角色且通过基本检查


def require_timesheet_approval_access():
    """工时审批权限检查依赖"""

    async def checker(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        if not has_timesheet_approval_access(current_user, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您没有权限审批工时记录",
            )
        return current_user

    return checker


def check_timesheet_approval_permission(
    user: User, db: Session, timesheets: List[Any]
) -> bool:
    """
    检查工时审批权限（批量）

    Args:
        user: 当前用户
        db: 数据库会话
        timesheets: 工时记录列表

    Returns:
        bool: 是否有审批权限
    """
    if user.is_superuser:
        return True

    # 收集所有需要检查的用户和部门
    user_ids = list(set(ts.user_id for ts in timesheets))
    dept_ids = list(set(ts.department_id for ts in timesheets if ts.department_id))

    # 检查是否有任何审批权限
    for user_id in user_ids:
        for dept_id in dept_ids:
            if has_timesheet_approval_access(user, db, user_id, dept_id):
                return True

    return has_timesheet_approval_access(user, db)


def has_scheduler_admin_access(user: User) -> bool:
    """
    检查用户是否有调度器管理权限

    调度器管理权限包括：手动触发任务、更新任务配置、同步任务配置
    只有管理员和系统管理员可以操作

    Args:
        user: 当前用户

    Returns:
        bool: 是否有调度器管理权限
    """
    if user.is_superuser:
        return True

    # 定义有调度器管理权限的角色代码
    admin_roles = [
        "admin",  # 管理员
        "super_admin",  # 超级管理员
        "系统管理员",
        "管理员",
        "gm",  # 总经理
        "总经理",
        "chairman",  # 董事长
        "董事长",
    ]

    # 检查用户角色
    for user_role in user.roles:
        role_code = user_role.role.role_code.lower() if user_role.role.role_code else ""
        role_name = user_role.role.role_name.lower() if user_role.role.role_name else ""
        if role_code in admin_roles or role_name in admin_roles:
            return True

    return False


def require_scheduler_admin_access():
    """调度器管理权限检查依赖"""

    async def admin_checker(current_user: User = Depends(get_current_active_user)):
        if not has_scheduler_admin_access(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您没有权限管理调度器，仅管理员可以操作",
            )
        return current_user

    return admin_checker


# 研发项目角色列表
RD_PROJECT_ROLES = [
    "admin",
    "super_admin",
    "管理员",
    "系统管理员",
    "tech_dev_manager",
    "技术开发部经理",
    "rd_engineer",
    "研发工程师",
    "me_engineer",
    "机械工程师",
    "ee_engineer",
    "电气工程师",
    "sw_engineer",
    "软件工程师",
    "te_engineer",
    "测试工程师",
    "me_dept_manager",
    "机械部经理",
    "ee_dept_manager",
    "电气部经理",
    "te_dept_manager",
    "测试部经理",
    "project_dept_manager",
    "项目部经理",
    "pm",
    "pmc",
    "项目经理",
    "gm",
    "总经理",
    "chairman",
    "董事长",
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
                detail="您没有权限访问研发项目管理功能",
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
        role_code = user_role.role.role_code.upper() if user_role.role.role_code else ""
        role_name = user_role.role.role_name.lower() if user_role.role.role_name else ""
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
        return any(code in user_role_codes for code in allowed_codes) or any(
            name in user_role_names for name in allowed_names
        )

    elif doc_type == "PLC_PROGRAM":
        # PLC程序：PLC工程师、电气工程师、研发工程师、项目经理
        allowed_codes = ["ENGINEER", "PM", "PMC", "RD_ENGINEER", "GM", "ADMIN"]
        allowed_names = ["电气", "plc", "研发", "工程师", "项目经理", "pm"]
        return any(code in user_role_codes for code in allowed_codes) or any(
            name in user_role_names for name in allowed_names
        )

    elif doc_type == "LABELWORK_PROGRAM":
        # Labelwork程序：电气工程师、PLC工程师、研发工程师、项目经理
        allowed_codes = ["ENGINEER", "PM", "PMC", "RD_ENGINEER", "GM", "ADMIN"]
        allowed_names = ["电气", "plc", "研发", "工程师", "项目经理", "pm"]
        return any(code in user_role_codes for code in allowed_codes) or any(
            name in user_role_names for name in allowed_names
        )

    elif doc_type == "BOM_DOCUMENT":
        # BOM文档：PMC、物料工程师、项目经理、工程师
        allowed_codes = ["PMC", "PM", "ENGINEER", "GM", "ADMIN"]
        allowed_names = ["物料", "pmc", "项目经理", "pm", "工程师"]
        return any(code in user_role_codes for code in allowed_codes) or any(
            name in user_role_names for name in allowed_names
        )

    elif doc_type == "FAT_DOCUMENT":
        # FAT文档：质量工程师、项目经理、总经理
        allowed_codes = ["QA", "QUALITY", "PM", "GM", "ADMIN"]
        allowed_names = ["质量", "qa", "项目经理", "pm", "总经理"]
        return any(code in user_role_codes for code in allowed_codes) or any(
            name in user_role_names for name in allowed_names
        )

    elif doc_type == "SAT_DOCUMENT":
        # SAT文档：质量工程师、项目经理、总经理
        allowed_codes = ["QA", "QUALITY", "PM", "GM", "ADMIN"]
        allowed_names = ["质量", "qa", "项目经理", "pm", "总经理"]
        return any(code in user_role_codes for code in allowed_codes) or any(
            name in user_role_names for name in allowed_names
        )

    elif doc_type == "OTHER":
        # 其他文档：项目成员都可以访问
        allowed_codes = ["PM", "ENGINEER", "PMC", "QA", "RD_ENGINEER", "GM", "ADMIN"]
        allowed_names = ["项目经理", "pm", "工程师", "pmc", "质量", "qa", "研发"]
        return any(code in user_role_codes for code in allowed_codes) or any(
            name in user_role_names for name in allowed_names
        )

    # 默认：项目成员都可以访问
    allowed_codes = ["PM", "ENGINEER", "PMC", "QA", "GM", "ADMIN"]
    allowed_names = ["项目经理", "pm", "工程师", "pmc", "质量", "qa"]
    return any(code in user_role_codes for code in allowed_codes) or any(
        name in user_role_names for name in allowed_names
    )


def has_machine_document_upload_permission(user: User, doc_type: str) -> bool:
    """
    检查用户是否有权限上传指定类型的设备文档（兼容性函数，内部调用通用权限检查）
    """
    # 调用通用权限检查函数
    return has_machine_document_permission(user, doc_type)
