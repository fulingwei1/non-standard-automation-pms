# -*- coding: utf-8 -*-
"""
用户同步服务
负责从员工档案同步创建用户账号
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.organization import Employee
from app.models.user import Role, User, UserRole
from app.utils.pinyin_utils import (
    generate_initial_password,
    generate_unique_username,
    name_to_pinyin,
)

logger = logging.getLogger(__name__)


class UserSyncService:
    """用户同步服务"""

    # 默认岗位-角色映射（作为兜底）
    DEFAULT_POSITION_ROLE_MAPPING = {
        # 销售序列
        "销售总监": "sales_director",
        "销售经理": "sales_manager",
        "销售工程师": "sales",
        "销售助理": "sales_assistant",

        # 工程序列
        "PLC工程师": "plc_engineer",
        "测试工程师": "test_engineer",
        "机械工程师": "mechanical_engineer",
        "结构工程师": "mechanical_engineer",
        "电气工程师": "electrical_engineer",
        "软件工程师": "software_engineer",

        # 生产序列
        "装配技工": "assembler",
        "装配钳工": "assembler",
        "装配电工": "assembler",
        "品质工程师": "qa_engineer",

        # 项目管理序列
        "项目经理": "pm",
        "PMC": "pmc",

        # 客服序列
        "客服工程师": "customer_service",

        # 采购序列
        "采购工程师": "procurement_engineer",
        "采购": "procurement",

        # 仓库序列
        "仓库管理员": "warehouse",

        # 财务序列
        "财务经理": "finance_manager",
        "财务": "finance",
        "会计": "accountant",

        # 人事序列
        "人事经理": "hr_manager",
        "人事": "hr",

        # 管理层
        "总经理": "gm",
        "副总经理": "vp",
        "董事长": "chairman",
        "部门经理": "dept_manager",
    }

    @staticmethod
    def get_role_by_position(position: str, db: Session) -> Optional[Role]:
        """
        根据岗位名称获取对应的角色

        优先从数据库的 position_role_mapping 表查询，
        如果没有找到，则使用默认映射
        """
        if not position:
            return None

        # 1. 从数据库映射表查询（按优先级排序）
        try:
            result = db.execute(
                text("""
                    SELECT role_code FROM position_role_mapping
                    WHERE :position LIKE '%' || position_keyword || '%'
                    AND is_active = 1
                    ORDER BY priority DESC
                    LIMIT 1
                """),
                {"position": position}
            )
            row = result.fetchone()
            if row:
                role_code = row[0]
                role = db.query(Role).filter(Role.role_code == role_code).first()
                if role:
                    return role
        except Exception:
            logger.debug("岗位-角色映射查询失败，使用默认映射", exc_info=True)

        # 2. 使用默认映射
        for keyword, role_code in UserSyncService.DEFAULT_POSITION_ROLE_MAPPING.items():
            if keyword in position:
                role = db.query(Role).filter(Role.role_code == role_code).first()
                if role:
                    return role

        # 3. 返回默认员工角色
        return db.query(Role).filter(Role.role_code == "employee").first()

    @staticmethod
    def create_user_from_employee(
        db: Session,
        employee: Employee,
        existing_usernames: set,
        auto_activate: bool = False
    ) -> Tuple[Optional[User], str]:
        """
        从员工记录创建用户账号

        Args:
            db: 数据库会话
            employee: 员工对象
            existing_usernames: 已存在的用户名集合
            auto_activate: 是否自动激活账号

        Returns:
            (创建的用户对象, 初始密码) 或 (None, 错误信息)
        """
        # 检查是否已有账号
        existing_user = db.query(User).filter(User.employee_id == employee.id).first()
        if existing_user:
            return None, f"员工 {employee.name} 已有账号: {existing_user.username}"

        # 生成用户名
        username = generate_unique_username(employee.name, db, existing_usernames)
        existing_usernames.add(username)

        # 生成密码（优先使用身份证后4位，回退使用工号后4位）
        password = generate_initial_password(
            username,
            id_card=employee.id_card,
            employee_code=employee.employee_code
        )

        # 创建用户
        user = User(
            employee_id=employee.id,
            username=username,
            password_hash=get_password_hash(password),
            real_name=employee.name,
            employee_no=employee.employee_code,
            department=employee.department,
            position=employee.role,
            is_active=auto_activate,
            is_superuser=False,
        )
        db.add(user)
        db.flush()  # 获取 user.id

        # 分配初始角色
        role = UserSyncService.get_role_by_position(employee.role, db)
        if role:
            user_role = UserRole(user_id=user.id, role_id=role.id)
            db.add(user_role)

        return user, password

    @staticmethod
    def sync_all_employees(
        db: Session,
        only_active: bool = True,
        auto_activate: bool = False,
        department_filter: Optional[str] = None
    ) -> Dict:
        """
        批量同步所有员工到用户表

        Args:
            db: 数据库会话
            only_active: 是否只同步在职员工
            auto_activate: 是否自动激活新账号
            department_filter: 部门筛选（可选）

        Returns:
            同步结果统计
        """
        # 构建员工查询
        query = db.query(Employee)

        if only_active:
            query = query.filter(Employee.employment_status == 'active')

        if department_filter:
            query = query.filter(Employee.department.contains(department_filter))

        employees = query.all()

        # 获取现有用户名集合
        existing_usernames = set(
            u.username for u in db.query(User.username).all()
        )

        # 统计
        result = {
            "total_employees": len(employees),
            "created": 0,
            "skipped": 0,
            "errors": [],
            "created_users": [],  # 创建的用户信息（用户名+初始密码）
        }

        for emp in employees:
            try:
                user, password = UserSyncService.create_user_from_employee(
                    db, emp, existing_usernames, auto_activate
                )
                if user:
                    result["created"] += 1
                    result["created_users"].append({
                        "employee_id": emp.id,
                        "employee_name": emp.name,
                        "employee_code": emp.employee_code,
                        "username": user.username,
                        "initial_password": password,
                        "department": emp.department,
                        "position": emp.role,
                        "is_active": user.is_active,
                    })
                else:
                    result["skipped"] += 1
            except Exception as e:
                result["errors"].append({
                    "employee_id": emp.id,
                    "employee_name": emp.name,
                    "error": str(e)
                })

        # 提交事务
        if result["created"] > 0:
            db.commit()

        return result

    @staticmethod
    def reset_user_password(db: Session, user_id: int) -> Tuple[bool, str]:
        """
        重置用户密码为初始密码

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            (是否成功, 新密码或错误信息)
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, "用户不存在"

        # 获取关联的员工信息
        employee = db.query(Employee).filter(Employee.id == user.employee_id).first()
        if not employee:
            return False, "未找到关联的员工信息"

        # 生成新密码（优先使用身份证后4位，回退使用工号后4位）
        new_password = generate_initial_password(
            user.username,
            id_card=employee.id_card,
            employee_code=employee.employee_code
        )

        # 更新密码
        user.password_hash = get_password_hash(new_password)
        user.updated_at = datetime.now()
        db.commit()

        return True, new_password

    @staticmethod
    def toggle_user_active(db: Session, user_id: int, is_active: bool) -> Tuple[bool, str]:
        """
        切换用户激活状态

        Args:
            db: 数据库会话
            user_id: 用户ID
            is_active: 目标状态

        Returns:
            (是否成功, 消息)
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, "用户不存在"

        if user.is_superuser:
            return False, "不能修改超级管理员的状态"

        user.is_active = is_active
        user.updated_at = datetime.now()
        db.commit()

        status_text = "已激活" if is_active else "已禁用"
        return True, f"用户 {user.username} {status_text}"

    @staticmethod
    def batch_toggle_active(
        db: Session,
        user_ids: List[int],
        is_active: bool
    ) -> Dict:
        """
        批量切换用户激活状态

        Args:
            db: 数据库会话
            user_ids: 用户ID列表
            is_active: 目标状态

        Returns:
            操作结果统计
        """
        result = {
            "total": len(user_ids),
            "success": 0,
            "failed": 0,
            "errors": []
        }

        for user_id in user_ids:
            success, message = UserSyncService.toggle_user_active(db, user_id, is_active)
            if success:
                result["success"] += 1
            else:
                result["failed"] += 1
                result["errors"].append({"user_id": user_id, "error": message})

        return result
