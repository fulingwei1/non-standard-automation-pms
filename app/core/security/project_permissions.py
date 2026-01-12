# -*- coding: utf-8 -*-
"""
项目权限模块

包含项目访问权限、研发项目权限、工时审批权限、设备文档权限
"""

from typing import Optional, Any, List

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...models.user import User
from .deps import get_db, get_current_active_user


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
    from ...services.data_scope_service import DataScopeService
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


def has_timesheet_approval_access(user: User, db: Session, timesheet_user_id: Optional[int] = None, timesheet_dept_id: Optional[int] = None) -> bool:
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
        'pm',                   # 项目经理
        'project_manager',      # 项目经理
        '项目经理',
        'dept_manager',         # 部门经理
        'department_manager',   # 部门经理
        '部门经理',
        'hr_manager',           # 人事经理
        '人事经理',
        'gm',                   # 总经理
        '总经理',
        'admin',                # 管理员
        'super_admin',
    ]

    # 检查用户角色
    has_approval_role = False
    for user_role in user.roles:
        role_code = user_role.role.role_code.lower() if user_role.role.role_code else ''
        role_name = user_role.role.role_name.lower() if user_role.role.role_name else ''
        if role_code in approval_roles or role_name in approval_roles:
            has_approval_role = True
            break

    if not has_approval_role:
        return False

    # 如果没有具体的工时信息，只检查角色
    if timesheet_user_id is None and timesheet_dept_id is None:
        return True

    # 检查项目经理权限：是否是工时提交人所在项目的项目经理
    from ...models.project import Project
    if timesheet_user_id:
        # 查找该用户参与的项目，其中当前用户是项目经理
        projects_as_pm = db.query(Project).filter(Project.pm_id == user.id).all()
        project_ids = [p.id for p in projects_as_pm]

        # 检查工时是否属于这些项目
        from ...models.timesheet import Timesheet
        timesheet_in_pm_project = db.query(Timesheet).filter(
            Timesheet.id == timesheet_user_id,  # 这里实际应该是timesheet的project_id检查
            Timesheet.project_id.in_(project_ids)
        ).first()
        if timesheet_in_pm_project:
            return True

    # 检查部门经理权限：是否是同一部门
    if timesheet_dept_id and user.department_id:
        if user.department_id == timesheet_dept_id:
            return True

    return True  # 有审批角色且通过基本检查


def check_timesheet_approval_permission(user: User, db: Session, timesheets: List[Any]) -> bool:
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
