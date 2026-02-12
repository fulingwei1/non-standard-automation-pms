# -*- coding: utf-8 -*-
"""
销售模块公共工具函数 - 通用函数
"""
import calendar
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from app.models.user import Role, User, UserRole


def get_entity_creator_id(entity) -> Optional[int]:
    """Safely fetch created_by if the ORM model defines it."""
    return getattr(entity, "created_by", None)


def normalize_date_range(
    start_date_value: Optional[date],
    end_date_value: Optional[date],
) -> Tuple[date, date]:
    """Normalize and validate date range."""
    today = date.today()
    normalized_start = start_date_value or date(today.year, today.month, 1)

    if end_date_value:
        normalized_end = end_date_value
    else:
        if normalized_start.month == 12:
            normalized_end = date(normalized_start.year, 12, 31)
        else:
            normalized_end = date(normalized_start.year, normalized_start.month + 1, 1) - timedelta(days=1)

    if normalized_start > normalized_end:
        raise HTTPException(status_code=400, detail="开始日期不能晚于结束日期")

    return normalized_start, normalized_end


def get_user_role_code(db: Session, user: User) -> str:
    """获取用户的角色代码（返回第一个角色的代码）"""
    user_roles = db.query(UserRole).filter(UserRole.user_id == user.id).all()
    if user_roles and user_roles[0].role:
        return user_roles[0].role.role_code
    return "USER"


def get_user_role_name(db: Session, user: User) -> str:
    """获取用户的角色名称（返回第一个角色的名称）"""
    user_roles = db.query(UserRole).filter(UserRole.user_id == user.id).all()
    if user_roles and user_roles[0].role:
        return user_roles[0].role.role_name
    return "普通用户"


def get_visible_sales_users(
    db: Session,
    current_user: User,
    department_id: Optional[int],
    region_keyword: Optional[str],
) -> List[User]:
    """根据角色、部门和区域过滤可见的销售用户"""
    # 使用 joinedload 预加载 role 关系，避免 N+1 查询
    user_roles = (
        db.query(UserRole)
        .options(joinedload(UserRole.role))
        .filter(UserRole.user_id == current_user.id)
        .all()
    )
    user_role_codes = []
    for ur in user_roles:
        if ur.role is not None and hasattr(ur.role, 'role_code') and ur.role.role_code:
            user_role_codes.append(ur.role.role_code)

    is_sales_director = 'SALES_DIR' in user_role_codes
    is_sales_manager = 'SALES_MANAGER' in user_role_codes

    query = db.query(User).filter(User.is_active)

    # 应用部门过滤
    if department_id is not None:
        query = query.filter(User.department_id == department_id)

    # 应用区域过滤（如果用户模型有 region 字段）
    if region_keyword:
        # 假设用户有 region 或负责区域字段，根据实际模型调整
        # 这里先不实现，因为需要确认 User 模型是否有相关字段
        pass

    if is_sales_director:
        sales_role_codes = ['SALES', 'SALES_DIR', 'SALES_MANAGER', 'SA']
        # 优化查询：直接使用子查询，避免先查询再过滤
        sales_user_ids = (
            db.query(UserRole.user_id)
            .join(Role, Role.id == UserRole.role_id)
            .filter(Role.role_code.in_(sales_role_codes))
            .filter(Role.is_active)  # 只查询激活的角色
            .distinct()
            .all()
        )
        sales_user_ids = [uid for (uid,) in sales_user_ids]
        if sales_user_ids:
            return query.filter(User.id.in_(sales_user_ids)).all()
        else:
            return []
    elif is_sales_manager:
        dept_id = getattr(current_user, 'department_id', None)
        if dept_id:
            return query.filter(User.department_id == dept_id).all()
        else:
            return [current_user]
    else:
        return [current_user]


def build_department_name_map(db: Session, users: List[User]) -> Dict[str, str]:
    """批量获取部门名称，减少数据库查询"""
    dept_names = {user.department for user in users if user.department}
    return {name: name for name in dept_names}


def shift_month(year: int, month: int, delta: int) -> Tuple[int, int]:
    """根据delta偏移月数"""
    total_months = year * 12 + (month - 1) + delta
    new_year = total_months // 12
    new_month = total_months % 12 + 1
    return new_year, new_month


def generate_trend_buckets(period: str, count: int) -> List[dict]:
    """根据周期生成统计区间"""
    today = date.today()
    buckets: List[dict] = []
    period = period.upper()

    if period == "QUARTER":
        period = "QUARTER"
    elif period == "YEAR":
        period = "YEAR"
    else:
        period = "MONTH"

    if period == "MONTH":
        for offset in range(count - 1, -1, -1):
            target_year, target_month = shift_month(today.year, today.month, -offset)
            start = date(target_year, target_month, 1)
            _, last_day = calendar.monthrange(target_year, target_month)
            end = date(target_year, target_month, last_day)
            label = f"{target_year}-{target_month:02d}"
            buckets.append({
                "label": label,
                "target_label": label,
                "start": start,
                "end": end,
            })
    elif period == "QUARTER":
        current_quarter = (today.month - 1) // 3 + 1
        for offset in range(count - 1, -1, -1):
            quarter_delta = -offset
            total_quarters = (today.year * 4 + (current_quarter - 1)) + quarter_delta
            target_year = total_quarters // 4
            target_quarter = total_quarters % 4 + 1
            start_month = (target_quarter - 1) * 3 + 1
            start = date(target_year, start_month, 1)
            end_month = start_month + 2
            _, last_day = calendar.monthrange(target_year, end_month)
            end = date(target_year, end_month, last_day)
            label = f"{target_year}-Q{target_quarter}"
            buckets.append({
                "label": label,
                "target_label": label,
                "start": start,
                "end": end,
            })
    else:  # YEAR
        for offset in range(count - 1, -1, -1):
            target_year = today.year - offset
            start = date(target_year, 1, 1)
            end = date(target_year, 12, 31)
            label = str(target_year)
            buckets.append({
                "label": label,
                "target_label": label,
                "start": start,
                "end": end,
            })

    return buckets


def calculate_growth(current: float, previous: Optional[float]) -> float:
    """计算增长率"""
    if previous is None or previous == 0:
        return 100.0 if current > 0 else 0.0
    return round(((current - previous) / previous) * 100, 2)


def get_previous_range(start_date_value: date, end_date_value: date) -> Tuple[date, date]:
    """根据当前区间计算上一对等区间"""
    delta_days = (end_date_value - start_date_value).days + 1
    prev_end = start_date_value - timedelta(days=1)
    prev_start = prev_end - timedelta(days=delta_days - 1)
    return prev_start, prev_end
