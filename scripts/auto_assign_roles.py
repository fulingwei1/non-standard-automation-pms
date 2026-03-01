#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能角色分配脚本

根据用户的部门、职位、职级等信息，自动为所有用户分配合适的角色

分配规则（按优先级）：
1. 部门特殊规则匹配：
   - 制造中心生产部相关 -> ASSEMBLER（装配技师）
   - 生产部 -> ASSEMBLER（装配技师）
2. 部门默认角色（department_default_roles）- 如果配置了部门默认角色
3. 职位+职级智能匹配：
   a. 优先从职级中提取岗位类型（如"助理电气工程师" -> EE，"中级机械工程师" -> ME）
   b. 职位精确匹配（如"销售工程师" -> SALES，"电气工程师" -> EE）
   c. 职位模糊匹配（职位包含关键词）
4. 默认角色（USER）- 如果以上都无法匹配

特殊规则说明：
- 销售工程师 -> SALES（销售人员）
- 制造中心生产部 -> ASSEMBLER（装配技师）
- 生产部 -> ASSEMBLER（装配技师）

职级匹配说明：
- 从职级中提取岗位类型：如"助理电气工程师"、"初级测试工程师"、"中级机械工程师"
- 支持的关键词：机械(ME)、电气(EE)、软件(SW)、测试(ENGINEER)、销售(SALES)、采购(PU_ENGINEER)、质量(QA)、财务(FINANCE)、客服(ENGINEER)
- "待定"职级不进行匹配，使用职位匹配或默认角色

使用方法：
    python scripts/auto_assign_roles.py [--dry-run] [--replace] [--verbose]

参数说明：
    --dry-run: 预览模式，不实际分配（默认）
    --execute: 执行模式，实际分配角色
    --replace: 替换用户现有角色（默认保留现有角色）
    --verbose: 显示详细信息
"""

import os
import sys
from typing import List, Optional

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text

from app.models.base import get_db_session
from app.models.organization import Department, Employee, EmployeeHrProfile
from app.models.user import Role, User, UserRole

# 职位到角色编码的映射（基础映射）
POSITION_ROLE_MAPPING = {
    # 管理层
    "总经理": "GM",
    "副总经理": "GM",
    "财务总监": "CFO",
    "技术总监": "CTO",
    "销售总监": "SALES_DIR",
    # 项目经理
    "项目经理": "PROJECT_MANAGER",
    "PM": "PROJECT_MANAGER",
    "计划管理": "PMC",
    "PMC": "PMC",
    # 主管级
    "质量主管": "QA_MGR",
    "采购经理": "PU_MGR",  # 采购经理
    "采购主管": "PU_MGR",  # 采购主管也映射到采购经理
    "人事经理": "HR_MGR",
    # 工程师（基础岗位）
    "机械工程师": "ME",
    "电气工程师": "EE",
    "软件工程师": "SW",
    "测试工程师": "ENGINEER",  # 测试工程师使用ENGINEER角色
    "工程师": "ENGINEER",
    "PLC工程师": "ENGINEER",
    # 采购
    "采购助理": "PU_ASSISTANT",  # 采购助理（原采购员）
    "采购专员": "PU",
    "采购工程师": "PU_ENGINEER",
    "采购员": "PU_ASSISTANT",  # 采购员也映射到采购助理（兼容旧数据）
    "采购": "PU_ENGINEER",  # 默认采购职位映射到采购工程师
    # 质量
    "质量工程师": "QA",
    "品质工程师": "QA",
    "QA": "QA",
    # 财务
    "财务人员": "FINANCE",
    "财务专员": "FI",
    "财务": "FINANCE",
    # 销售
    "销售人员": "SALES",
    "销售专员": "SA",
    "销售经理": "SALES",
    "销售工程师": "SALES",  # 销售工程师分配销售角色
    "销售": "SALES",
    "售前工程师": "PRESALES",
    # 生产
    "装配技师": "ASSEMBLER",
    "装配钳工": "ASSEMBLER",
    "装配电工": "ASSEMBLER",
    "装配工": "ASSEMBLER",
    "调试工程师": "DEBUG",
    "生产": "PRODUCTION",
    # 客服
    "客服工程师": "ENGINEER",
    "售后工程师": "ENGINEER",
    # 其他
    "普通用户": "USER",
    "客户": "CUSTOMER",
    "供应商": "SUPPLIER",
}

# 职级关键词到岗位类型的映射（从职级中提取岗位信息）
JOB_LEVEL_POSITION_MAPPING = {
    "机械": "ME",
    "电气": "EE",
    "软件": "SW",
    "测试": "ENGINEER",  # 测试工程师使用ENGINEER角色
    "PLC": "ENGINEER",
    "销售": "SALES",
    "采购": "PU_ENGINEER",  # 采购映射到采购工程师
    "质量": "QA",
    "财务": "FINANCE",
    "客服": "ENGINEER",
    "售后": "ENGINEER",
}

# 职级等级关键词（用于识别职级等级）
LEVEL_KEYWORDS = {
    "助理": "ASSISTANT",
    "初级": "JUNIOR",
    "中级": "MIDDLE",
    "高级": "SENIOR",
    "专家": "EXPERT",
    "待定": None,  # 待定职级，使用默认角色
}


def get_role_by_code(db_session, role_code: str) -> Optional[Role]:
    """根据角色编码获取角色"""
    return (
        db_session.query(Role)
        .filter(Role.role_code == role_code, Role.is_active == True)
        .first()
    )


def get_department_default_roles(
    db_session, department_id: Optional[int]
) -> List[Role]:
    """获取部门的默认角色"""
    if not department_id:
        return []

    result = db_session.execute(
        text("""
        SELECT r.id, r.role_code, r.role_name
        FROM department_default_roles ddr
        JOIN roles r ON ddr.role_id = r.id
        WHERE ddr.department_id = :dept_id
        AND r.is_active = 1
        ORDER BY ddr.is_primary DESC, ddr.created_at ASC
    """),
        {"dept_id": department_id},
    )

    roles = []
    for row in result:
        role = db_session.query(Role).filter(Role.id == row.id).first()
        if role:
            roles.append(role)

    return roles


def extract_position_from_job_level(job_level: str) -> Optional[str]:
    """
    从职级中提取岗位类型

    例如：
    - "助理电气工程师" -> "EE"
    - "初级测试工程师" -> "ENGINEER"
    - "中级机械工程师" -> "ME"
    """
    if not job_level:
        return None

    for keyword, role_code in JOB_LEVEL_POSITION_MAPPING.items():
        if keyword in job_level:
            return role_code

    return None


def get_role_by_position_and_level(
    db_session, position: str, job_level: Optional[str] = None
) -> Optional[Role]:
    """
    根据职位和职级获取角色（更智能的匹配）

    优先级：
    1. 从职级中提取岗位类型（最精确，如"助理电气工程师" -> EE）
    2. 职位精确匹配
    3. 职位模糊匹配
    4. 职位关键词匹配
    """
    # 方法1: 优先从职级中提取岗位类型（最精确）
    if job_level and "待定" not in job_level:
        extracted_role_code = extract_position_from_job_level(job_level)
        if extracted_role_code:
            role = get_role_by_code(db_session, extracted_role_code)
            if role:
                return role

    # 方法2: 职位精确匹配
    if position:
        role_code = POSITION_ROLE_MAPPING.get(position)
        if role_code:
            role = get_role_by_code(db_session, role_code)
            if role:
                return role

        # 方法3: 职位模糊匹配（职位包含关键词）
        for pos_key, role_code in POSITION_ROLE_MAPPING.items():
            if pos_key in position or position in pos_key:
                role = get_role_by_code(db_session, role_code)
                if role:
                    return role

    return None


def get_default_role(db_session) -> Optional[Role]:
    """获取默认角色（USER）"""
    return get_role_by_code(db_session, "USER")


def get_department_id_by_name(db_session, department_name: str) -> Optional[int]:
    """根据部门名称获取部门ID"""
    if not department_name:
        return None

    # 尝试精确匹配
    dept = (
        db_session.query(Department)
        .filter(Department.dept_name == department_name, Department.is_active == True)
        .first()
    )

    if dept:
        return dept.id

    # 尝试模糊匹配（部门名称包含关键词）
    dept = (
        db_session.query(Department)
        .filter(
            Department.dept_name.like(f"%{department_name}%"),
            Department.is_active == True,
        )
        .first()
    )

    return dept.id if dept else None


def get_role_by_department(db_session, department_name: str) -> Optional[Role]:
    """
    根据部门名称获取角色（部门特殊规则）

    规则：
    - 制造中心生产部 -> ASSEMBLER（装配技师）
    - 制造中心-生产部 -> ASSEMBLER
    - 生产部 -> ASSEMBLER
    - 工程技术中心 -> ENGINEER（工程师，如果没有更细化的匹配）
    """
    if not department_name:
        return None

    # 制造中心生产部相关 -> 装配技师
    if "制造中心" in department_name and "生产" in department_name:
        return get_role_by_code(db_session, "ASSEMBLER")

    if "生产部" in department_name:
        return get_role_by_code(db_session, "ASSEMBLER")

    # 工程技术中心 -> 工程师（作为默认，如果职位匹配不到更具体的角色）
    # 注意：这个会在职位匹配之后作为fallback使用
    if "工程技术中心" in department_name:
        return get_role_by_code(db_session, "ENGINEER")

    return None


def is_manager_level(job_level: Optional[str], position: Optional[str]) -> bool:
    """
    判断是否为经理级别

    判断依据：
    - 职级包含"经理"、"主管"、"总监"
    - 职位包含"经理"、"主管"、"总监"、"组长"（组长也算管理岗）
    """
    if job_level:
        manager_keywords = ["经理", "主管", "总监", "组长", "负责人"]
        if any(keyword in job_level for keyword in manager_keywords):
            return True

    if position:
        manager_keywords = ["经理", "主管", "总监", "组长", "负责人", "副经理"]
        if any(keyword in position for keyword in manager_keywords):
            return True

    return False


def get_manager_role(
    db_session, department_name: Optional[str] = None
) -> Optional[Role]:
    """
    获取部门经理角色

    优先级：
    1. 根据部门类型匹配特定经理角色（如质量主管 -> QA_MGR）
    2. 如果有通用的部门经理角色，使用它
    3. 如果没有，返回None，保持原有的职位匹配结果（如工程师+经理 -> ENGINEER）
    """
    # 如果部门是质量相关，使用质量主管
    if department_name and "质量" in department_name:
        role = get_role_by_code(db_session, "QA_MGR")
        if role:
            return role

    # 如果部门是采购相关，使用采购主管
    if department_name and "采购" in department_name:
        role = get_role_by_code(db_session, "PU_MGR")
        if role:
            return role

    # 如果部门是人事相关，使用人事经理
    if department_name and ("人事" in department_name or "HR" in department_name):
        role = get_role_by_code(db_session, "HR_MGR")
        if role:
            return role

    # 尝试查找通用的部门经理角色（如果存在）
    manager_roles = [
        "DEPT_MGR",  # 部门经理（如果存在）
    ]

    for role_code in manager_roles:
        role = get_role_by_code(db_session, role_code)
        if role:
            return role

    # 如果没有专门的经理角色，返回None
    # 这样会保持原有的职位匹配结果（如"工程师"+"经理" -> ENGINEER）
    # 或者可以根据需要创建通用的部门经理角色
    return None


def assign_role_to_user(
    db_session,
    user: User,
    role: Role,
    replace: bool = False,
    additional_roles: List[Role] = None,
) -> bool:
    """
    为用户分配角色

    Args:
        db_session: 数据库会话
        user: 用户对象
        role: 主要角色对象
        replace: 是否替换现有角色
        additional_roles: 额外分配的角色列表（如部门经理角色）

    Returns:
        是否成功分配
    """
    roles_to_assign = [role]
    if additional_roles:
        roles_to_assign.extend(additional_roles)

    # 如果replace为True，先删除所有现有角色
    if replace:
        db_session.query(UserRole).filter(UserRole.user_id == user.id).delete()

    assigned_count = 0
    for role_to_assign in roles_to_assign:
        # 检查是否已有该角色
        existing = (
            db_session.query(UserRole)
            .filter(UserRole.user_id == user.id, UserRole.role_id == role_to_assign.id)
            .first()
        )

        if existing:
            continue  # 已有该角色，跳过

        # 创建新的角色分配
        user_role = UserRole(user_id=user.id, role_id=role_to_assign.id)
        db_session.add(user_role)
        assigned_count += 1

    return assigned_count > 0


def auto_assign_roles(
    dry_run: bool = True, replace: bool = False, verbose: bool = False
):
    """
    智能角色分配

    Args:
        dry_run: 是否只是预览，不实际执行
        replace: 是否替换现有角色
        verbose: 是否显示详细信息
    """
    with get_db_session() as session:
        print("=" * 80)
        print("智能角色分配工具")
        print("=" * 80)
        print(
            f"模式: {'预览模式（不会实际分配）' if dry_run else '执行模式（将分配角色）'}"
        )
        print(f"替换现有角色: {'是' if replace else '否（保留现有角色）'}")
        print()

        # 获取所有活跃用户
        users = session.query(User).filter(User.is_active == True).all()

        if not users:
            print("未找到活跃用户")
            return

        print(f"找到 {len(users)} 个活跃用户")
        print()

        stats = {
            "total": len(users),
            "assigned": 0,
            "skipped": 0,
            "failed": 0,
            "by_department_rule": 0,  # 部门规则匹配
            "by_department_default": 0,  # 部门默认角色
            "by_position": 0,
            "by_default": 0,
        }

        for user in users:
            if verbose:
                print(f"\n处理用户: {user.real_name or user.username} (ID: {user.id})")
                print(f"  部门: {user.department or '无'}")
                print(f"  职位: {user.position or '无'}")

            # 获取用户当前角色
            current_roles = (
                session.query(UserRole).filter(UserRole.user_id == user.id).all()
            )
            current_role_ids = [ur.role_id for ur in current_roles]

            if current_roles and not replace:
                if verbose:
                    role_names = [
                        session.query(Role).filter(Role.id == rid).first().role_name
                        for rid in current_role_ids
                    ]
                    print(f"  已有角色: {', '.join(role_names)}，跳过")
                stats["skipped"] += 1
                continue

            # 确定要分配的角色
            role_to_assign = None
            assignment_method = None
            additional_roles = []  # 额外分配的角色（如部门经理角色）

            # 方法1: 使用部门特殊规则（仅限制造中心生产部 -> 装配技师）
            # 注意：工程技术中心的规则作为fallback，不在优先级1
            if user.department:
                # 制造中心生产部优先匹配
                if "制造中心" in user.department and "生产" in user.department:
                    role_to_assign = get_role_by_department(session, user.department)
                    if role_to_assign:
                        assignment_method = f"部门规则 ({user.department})"
                        stats["by_department_rule"] += 1

            # 方法2: 使用部门默认角色（如果部门特殊规则未匹配）
            if not role_to_assign and user.department:
                dept_id = get_department_id_by_name(session, user.department)
                if dept_id:
                    dept_roles = get_department_default_roles(session, dept_id)
                    if dept_roles:
                        role_to_assign = dept_roles[0]  # 使用第一个（通常是主要角色）
                        assignment_method = "部门默认角色"
                        stats["by_department_default"] += 1

            # 方法3: 根据职位和职级匹配（智能匹配，优先匹配细化角色）
            if not role_to_assign:
                # 获取用户的职级信息（从HR档案中）
                job_level = None
                hr_position = None
                try:
                    employee = (
                        session.query(Employee)
                        .filter(Employee.id == user.employee_id)
                        .first()
                    )
                    if employee:
                        hr_profile = (
                            session.query(EmployeeHrProfile)
                            .filter(EmployeeHrProfile.employee_id == employee.id)
                            .first()
                        )
                        if hr_profile:
                            job_level = hr_profile.job_level
                            hr_position = hr_profile.position
                except Exception:
                    pass

                # 优先使用HR档案中的职位，如果没有则使用用户表的职位
                position = hr_position or user.position

                # 先进行职位+职级匹配（获取基础角色）
                base_role = get_role_by_position_and_level(session, position, job_level)

                # 如果没有基础角色且是工程技术中心，使用默认工程师角色
                if (
                    not base_role
                    and user.department
                    and "工程技术中心" in user.department
                ):
                    base_role = get_role_by_code(session, "ENGINEER")

                # 检查是否为经理级别
                is_manager = is_manager_level(job_level, position)

                # 如果是经理级别，尝试分配部门经理角色
                if is_manager:
                    # 尝试获取专门的部门经理角色（如QA_MGR、PU_MGR等）
                    specific_manager_role = get_manager_role(session, user.department)
                    if specific_manager_role:
                        # 有专门的经理角色，使用专门的经理角色
                        # 但如果也有基础角色，同时分配基础角色
                        role_to_assign = specific_manager_role
                        if base_role and base_role.id != specific_manager_role.id:
                            additional_roles.append(base_role)
                        assignment_method = f"经理角色匹配"
                        if job_level:
                            assignment_method += f" (职级: {job_level})"
                        if additional_roles:
                            assignment_method += f" + {base_role.role_name}"
                        stats["by_position"] += 1
                    else:
                        # 没有专门的经理角色，使用基础角色，并额外分配部门经理角色
                        if base_role:
                            role_to_assign = base_role
                            # 尝试分配通用的部门经理角色
                            dept_mgr_role = get_role_by_code(session, "DEPT_MGR")
                            if dept_mgr_role:
                                additional_roles.append(dept_mgr_role)
                            assignment_method = f"职位+职级匹配（经理级别）"
                            if job_level:
                                assignment_method += f" (职级: {job_level})"
                            if additional_roles:
                                assignment_method += f" + 部门经理"
                            stats["by_position"] += 1
                        else:
                            # 如果还是没有基础角色，使用工程技术中心默认角色
                            if user.department and "工程技术中心" in user.department:
                                role_to_assign = get_role_by_code(session, "ENGINEER")
                                if role_to_assign:
                                    dept_mgr_role = get_role_by_code(
                                        session, "DEPT_MGR"
                                    )
                                    if dept_mgr_role:
                                        additional_roles.append(dept_mgr_role)
                                    assignment_method = f"工程技术中心默认（经理级别）"
                                    if job_level:
                                        assignment_method += f" (职级: {job_level})"
                                    if additional_roles:
                                        assignment_method += f" + 部门经理"
                                    stats["by_position"] += 1
                else:
                    # 不是经理级别，使用基础角色
                    if base_role:
                        role_to_assign = base_role
                        assignment_method = f"职位+职级匹配"
                        if job_level:
                            assignment_method += f" (职级: {job_level})"
                        stats["by_position"] += 1

                # 如果还没有匹配到角色
                if not role_to_assign:
                    role_to_assign = get_role_by_position_and_level(
                        session, position, job_level
                    )
                    if role_to_assign:
                        assignment_method = f"职位+职级匹配"
                        if job_level:
                            assignment_method += f" (职级: {job_level})"
                        stats["by_position"] += 1

                # 方法4: 如果工程技术中心且没有匹配到具体角色，使用默认工程师角色（fallback）
                if (
                    not role_to_assign
                    and user.department
                    and "工程技术中心" in user.department
                ):
                    role_to_assign = get_role_by_code(session, "ENGINEER")
                    if role_to_assign:
                        assignment_method = (
                            f"工程技术中心默认 (部门: {user.department})"
                        )
                        stats["by_department_rule"] += 1

            # 方法3: 使用默认角色
            if not role_to_assign:
                role_to_assign = get_default_role(session)
                if role_to_assign:
                    assignment_method = "默认角色（USER）"
                    stats["by_default"] += 1

            if not role_to_assign:
                if verbose:
                    print(f"  ❌ 无法找到合适的角色")
                stats["failed"] += 1
                continue

            if verbose:
                print(
                    f"  ✓ 分配角色: {role_to_assign.role_name} ({role_to_assign.role_code}) - {assignment_method}"
                )

            # 执行分配
            if not dry_run:
                try:
                    assigned = assign_role_to_user(
                        session,
                        user,
                        role_to_assign,
                        replace=replace,
                        additional_roles=additional_roles if additional_roles else None,
                    )
                    if assigned:
                        stats["assigned"] += 1
                    else:
                        stats["skipped"] += 1
                except Exception as e:
                    if verbose:
                        print(f"  ❌ 分配失败: {e}")
                    stats["failed"] += 1
            else:
                stats["assigned"] += 1

        print()
        print("=" * 80)
        print("统计信息:")
        print(f"  总用户数: {stats['total']}")
        print(f"  成功分配: {stats['assigned']}")
        print(f"  跳过（已有角色）: {stats['skipped']}")
        print(f"  分配失败: {stats['failed']}")
        print()
        print("分配方式统计:")
        print(f"  部门规则匹配: {stats['by_department_rule']}")
        print(f"  部门默认角色: {stats['by_department_default']}")
        print(f"  职位+职级匹配: {stats['by_position']}")
        print(f"  默认角色: {stats['by_default']}")
        print("=" * 80)

        if dry_run:
            print()
            print("这是预览模式，未实际分配任何角色。")
            print("要执行分配，请运行: python scripts/auto_assign_roles.py --execute")
        else:
            session.commit()
            print()
            print("✓ 角色分配完成！")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="智能角色分配工具")
    parser.add_argument(
        "--execute", action="store_true", help="实际执行分配（默认是预览模式）"
    )
    parser.add_argument(
        "--replace", action="store_true", help="替换用户现有角色（默认保留现有角色）"
    )
    parser.add_argument("--verbose", action="store_true", help="显示详细信息")

    args = parser.parse_args()

    auto_assign_roles(
        dry_run=not args.execute, replace=args.replace, verbose=args.verbose
    )
