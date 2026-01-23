# -*- coding: utf-8 -*-
"""
统一工作台统计 API

根据用户角色返回相应的统计数据：
- sales: 销售相关（线索、商机、合同、收入）
- engineer: 工程相关（任务、工时、ECN、评审）
- procurement: 采购相关（订单、待确认、逾期、节省）
- production: 生产相关（工单、进行中、完成、良品率）
- pmo: PMO相关（活跃项目、进度、延期、完成）
- admin: 管理员相关（用户、角色、登录、错误）
"""

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User, Role
from app.models.project import Project
from app.schemas.common import ResponseModel

router = APIRouter()


def get_sales_stats(db: Session, current_user: User) -> dict:
    """获取销售统计数据"""
    # 由于没有销售相关表，返回模拟数据
    # TODO: 集成实际的销售数据（线索、商机、合同等）
    return {
        'stats': [
            {'key': 'leads', 'label': '活跃线索', 'value': 0, 'trend': 0},
            {'key': 'opportunities', 'label': '商机数', 'value': 0, 'trend': 0},
            {'key': 'contracts', 'label': '合同数', 'value': 0, 'trend': 0},
            {'key': 'revenue', 'label': '本月签约', 'value': '¥0', 'trend': 0},
        ]
    }


def get_engineer_stats(db: Session, current_user: User) -> dict:
    """获取工程师统计数据"""
    # TODO: 集成实际的任务、工时、ECN数据
    return {
        'stats': [
            {'key': 'tasks', 'label': '待办任务', 'value': 0, 'trend': 0},
            {'key': 'hours-logged', 'label': '本周工时', 'value': '0h', 'trend': 0},
            {'key': 'ecn-pending', 'label': '待处理ECN', 'value': 0, 'trend': 0},
            {'key': 'reviews', 'label': '待评审', 'value': 0, 'trend': 0},
        ]
    }


def get_procurement_stats(db: Session, current_user: User) -> dict:
    """获取采购统计数据"""
    # TODO: 集成实际的采购订单数据
    return {
        'stats': [
            {'key': 'orders', 'label': '采购订单', 'value': 0, 'trend': 0},
            {'key': 'pending', 'label': '待确认', 'value': 0, 'trend': 0},
            {'key': 'overdue', 'label': '逾期', 'value': 0, 'trend': 0},
            {'key': 'savings', 'label': '节省金额', 'value': '¥0', 'trend': 0},
        ]
    }


def get_production_stats(db: Session, current_user: User) -> dict:
    """获取生产统计数据"""
    # TODO: 集成实际的生产工单数据
    return {
        'stats': [
            {'key': 'work-orders', 'label': '工单数', 'value': 0, 'trend': 0},
            {'key': 'in-progress', 'label': '进行中', 'value': 0, 'trend': 0},
            {'key': 'completed', 'label': '已完成', 'value': 0, 'trend': 0},
            {'key': 'yield', 'label': '良品率', 'value': '0%', 'trend': 0},
        ]
    }


def get_pmo_stats(db: Session, current_user: User) -> dict:
    """获取PMO统计数据"""
    # 应用数据权限过滤
    from app.services.data_scope_service import DataScopeService
    query = db.query(Project).filter(Project.is_active == True)
    query = DataScopeService.filter_projects_by_scope(db, query, current_user)

    projects = query.all()

    # 统计项目数据
    total = len(projects)

    # 按健康度统计
    on_track = sum(1 for p in projects if p.health == 'H1')
    delayed = sum(1 for p in projects if p.health in ['H2', 'H3'])
    completed = sum(1 for p in projects if p.health == 'H4')

    return {
        'stats': [
            {'key': 'active-projects', 'label': '活跃项目', 'value': total, 'trend': 0},
            {'key': 'on-track', 'label': '正常进度', 'value': on_track, 'trend': 0},
            {'key': 'delayed', 'label': '延期项目', 'value': delayed, 'trend': 0},
            {'key': 'completed', 'label': '已完成', 'value': completed, 'trend': 0},
        ]
    }


def get_admin_stats(db: Session, current_user: User) -> dict:
    """获取管理员统计数据"""
    total_users = db.query(func.count(User.id)).scalar() or 0
    active_users = db.query(func.count(User.id)).filter(User.is_active == True).scalar() or 0
    total_roles = db.query(func.count(Role.id)).scalar() or 0

    # 今日登录次数（简化实现）
    login_count_today = 0
    error_count = 0

    return {
        'stats': [
            {'key': 'users', 'label': '用户数', 'value': total_users, 'trend': 0},
            {'key': 'roles', 'label': '角色数', 'value': total_roles, 'trend': 0},
            {'key': 'logins', 'label': '今日登录', 'value': login_count_today, 'trend': 0},
            {'key': 'errors', 'label': '系统错误', 'value': error_count, 'trend': 0},
        ]
    }


# 类型映射到统计函数
STATS_FUNCTIONS = {
    'sales': get_sales_stats,
    'engineer': get_engineer_stats,
    'procurement': get_procurement_stats,
    'production': get_production_stats,
    'pmo': get_pmo_stats,
    'admin': get_admin_stats,
}


@router.get("/dashboard/stats/{stats_type}", response_model=ResponseModel)
def get_dashboard_stats(
    stats_type: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取统一工作台统计数据

    根据stats_type返回不同类型的统计数据：
    - sales: 销售统计（线索、商机、合同、收入）
    - engineer: 工程统计（任务、工时、ECN、评审）
    - procurement: 采购统计（订单、待确认、逾期、节省）
    - production: 生产统计（工单、进行中、完成、良品率）
    - pmo: PMO统计（项目、进度、延期、完成）
    - admin: 管理员统计（用户、角色、登录、错误）
    """
    # 验证stats_type是否有效
    if stats_type not in STATS_FUNCTIONS:
        return ResponseModel(
            code=400,
            message=f"不支持的统计类型: {stats_type}",
            data=None
        )

    # 获取对应的统计函数
    stats_func = STATS_FUNCTIONS[stats_type]

    # 调用统计函数获取数据
    try:
        stats_data = stats_func(db, current_user)
        return ResponseModel(
            code=200,
            message="success",
            data=stats_data
        )
    except Exception as e:
        return ResponseModel(
            code=500,
            message=f"获取统计数据失败: {str(e)}",
            data=None
        )
