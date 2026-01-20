# -*- coding: utf-8 -*-
"""
战略管理服务 - KPI 数据采集器

支持从各业务模块自动采集 KPI 数据，包括：
- 项目模块：项目数量、完成率、健康度等
- 财务模块：收入、成本、利润等
- 采购模块：采购金额、供应商数量等
- 人力模块：人员数量、离职率等
"""

import json
from datetime import datetime
from decimal import Decimal
from typing import Any, Callable, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.strategy import KPI, KPIDataSource

# 尝试导入 simpleeval，如果不存在则禁用公式计算
try:
    from simpleeval import simple_eval
    HAS_SIMPLEEVAL = True
except ImportError:
    HAS_SIMPLEEVAL = False


# ============================================
# 数据采集器注册表
# ============================================

_collectors: Dict[str, Callable] = {}


def register_collector(module: str):
    """装饰器：注册数据采集器"""
    def decorator(func: Callable):
        _collectors[module] = func
        return func
    return decorator


def get_collector(module: str) -> Optional[Callable]:
    """获取数据采集器"""
    return _collectors.get(module)


# ============================================
# 项目模块采集器
# ============================================

@register_collector("PROJECT")
def collect_project_metrics(
    db: Session,
    metric: str,
    filters: Optional[Dict] = None,
    aggregation: str = "COUNT"
) -> Optional[Decimal]:
    """
    采集项目模块指标

    Args:
        db: 数据库会话
        metric: 指标名称
        filters: 筛选条件
        aggregation: 聚合方式

    Returns:
        Optional[Decimal]: 采集到的值
    """
    from app.models.project import Project

    filters = filters or {}

    query = db.query(Project).filter(Project.is_active == True)

    # 应用筛选条件
    if "status" in filters:
        query = query.filter(Project.status == filters["status"])
    if "year" in filters:
        query = query.filter(func.year(Project.created_at) == filters["year"])
    if "health_status" in filters:
        query = query.filter(Project.health_status == filters["health_status"])

    if metric == "PROJECT_COUNT":
        # 项目数量
        return Decimal(query.count())

    elif metric == "PROJECT_COMPLETION_RATE":
        # 项目完成率
        total = query.count()
        if total == 0:
            return Decimal(0)
        completed = query.filter(Project.status == "COMPLETED").count()
        return Decimal(str(completed / total * 100))

    elif metric == "PROJECT_ON_TIME_RATE":
        # 项目按时完成率
        completed = query.filter(Project.status == "COMPLETED").all()
        if not completed:
            return Decimal(0)
        on_time = sum(1 for p in completed if p.actual_end_date and p.planned_end_date
                      and p.actual_end_date <= p.planned_end_date)
        return Decimal(str(on_time / len(completed) * 100))

    elif metric == "PROJECT_HEALTH_RATE":
        # 项目健康率（H1 占比）
        total = query.count()
        if total == 0:
            return Decimal(0)
        healthy = query.filter(Project.health_status == "H1").count()
        return Decimal(str(healthy / total * 100))

    elif metric == "PROJECT_TOTAL_VALUE":
        # 项目总金额
        result = query.with_entities(func.sum(Project.contract_amount)).scalar()
        return Decimal(str(result or 0))

    return None


# ============================================
# 财务模块采集器
# ============================================

@register_collector("FINANCE")
def collect_finance_metrics(
    db: Session,
    metric: str,
    filters: Optional[Dict] = None,
    aggregation: str = "SUM"
) -> Optional[Decimal]:
    """
    采集财务模块指标

    Args:
        db: 数据库会话
        metric: 指标名称
        filters: 筛选条件
        aggregation: 聚合方式

    Returns:
        Optional[Decimal]: 采集到的值
    """
    # 财务模块待实现，返回模拟数据
    # TODO: 集成真实财务模块
    return None


# ============================================
# 采购模块采集器
# ============================================

@register_collector("PURCHASE")
def collect_purchase_metrics(
    db: Session,
    metric: str,
    filters: Optional[Dict] = None,
    aggregation: str = "SUM"
) -> Optional[Decimal]:
    """
    采集采购模块指标

    Args:
        db: 数据库会话
        metric: 指标名称
        filters: 筛选条件
        aggregation: 聚合方式

    Returns:
        Optional[Decimal]: 采集到的值
    """
    from app.models.purchase import PurchaseOrder

    filters = filters or {}

    query = db.query(PurchaseOrder).filter(PurchaseOrder.is_active == True)

    # 应用筛选条件
    if "year" in filters:
        query = query.filter(func.year(PurchaseOrder.created_at) == filters["year"])
    if "status" in filters:
        query = query.filter(PurchaseOrder.status == filters["status"])

    if metric == "PO_COUNT":
        # 采购订单数量
        return Decimal(query.count())

    elif metric == "PO_TOTAL_AMOUNT":
        # 采购总金额
        result = query.with_entities(func.sum(PurchaseOrder.total_amount)).scalar()
        return Decimal(str(result or 0))

    elif metric == "PO_ON_TIME_RATE":
        # 采购按时到货率
        delivered = query.filter(PurchaseOrder.status == "DELIVERED").all()
        if not delivered:
            return Decimal(0)
        on_time = sum(1 for po in delivered if po.actual_delivery_date and po.expected_delivery_date
                      and po.actual_delivery_date <= po.expected_delivery_date)
        return Decimal(str(on_time / len(delivered) * 100))

    return None


# ============================================
# 人力模块采集器
# ============================================

@register_collector("HR")
def collect_hr_metrics(
    db: Session,
    metric: str,
    filters: Optional[Dict] = None,
    aggregation: str = "COUNT"
) -> Optional[Decimal]:
    """
    采集人力资源模块指标

    Args:
        db: 数据库会话
        metric: 指标名称
        filters: 筛选条件
        aggregation: 聚合方式

    Returns:
        Optional[Decimal]: 采集到的值
    """
    from app.models.user import User

    filters = filters or {}

    query = db.query(User).filter(User.is_active == True)

    # 应用筛选条件
    if "department_id" in filters:
        query = query.filter(User.department_id == filters["department_id"])

    if metric == "EMPLOYEE_COUNT":
        # 员工数量
        return Decimal(query.count())

    elif metric == "EMPLOYEE_TURNOVER_RATE":
        # 离职率（需要离职记录表，暂时返回模拟数据）
        # TODO: 集成离职记录
        return None

    return None


# ============================================
# 公式计算（仅使用 simpleeval）
# ============================================

def calculate_formula(
    formula: str,
    params: Dict[str, Any]
) -> Optional[Decimal]:
    """
    计算公式（使用 simpleeval 安全执行）

    Args:
        formula: 公式字符串（如 "a / b * 100"）
        params: 参数字典（如 {"a": 10, "b": 20}）

    Returns:
        Optional[Decimal]: 计算结果

    Raises:
        RuntimeError: 如果 simpleeval 未安装
    """
    if not formula:
        return None

    if not HAS_SIMPLEEVAL:
        raise RuntimeError(
            "公式计算需要安装 simpleeval 库。请运行: pip install simpleeval"
        )

    try:
        # 将 Decimal 转换为 float 以便计算
        float_params = {
            k: float(v) if isinstance(v, Decimal) else v
            for k, v in params.items()
            if v is not None
        }

        # 使用 simpleeval 安全执行公式
        result = simple_eval(formula, names=float_params)

        return Decimal(str(result))
    except Exception:
        return None


# ============================================
# 核心采集函数
# ============================================

def collect_kpi_value(
    db: Session,
    kpi_id: int,
    data_source_id: Optional[int] = None
) -> Optional[Decimal]:
    """
    采集单个 KPI 的值

    Args:
        db: 数据库会话
        kpi_id: KPI ID
        data_source_id: 指定数据源 ID（可选）

    Returns:
        Optional[Decimal]: 采集到的值
    """
    kpi = db.query(KPI).filter(KPI.id == kpi_id, KPI.is_active == True).first()
    if not kpi:
        return None

    # 获取数据源配置
    if data_source_id:
        data_source = db.query(KPIDataSource).filter(
            KPIDataSource.id == data_source_id,
            KPIDataSource.kpi_id == kpi_id,
            KPIDataSource.is_active == True
        ).first()
    else:
        # 使用主数据源
        data_source = db.query(KPIDataSource).filter(
            KPIDataSource.kpi_id == kpi_id,
            KPIDataSource.is_primary == True,
            KPIDataSource.is_active == True
        ).first()

    if not data_source:
        return None

    try:
        # 根据数据源类型采集
        if data_source.source_type == "AUTO":
            # 自动采集
            collector = get_collector(data_source.source_module)
            if not collector:
                return None

            filters = json.loads(data_source.filters) if data_source.filters else None
            value = collector(
                db,
                metric=data_source.metric,
                filters=filters,
                aggregation=data_source.aggregation or "COUNT"
            )

            # 如果有公式，进行计算
            if value is not None and data_source.formula:
                formula_params = json.loads(data_source.formula_params) if data_source.formula_params else {}
                formula_params["value"] = value
                value = calculate_formula(data_source.formula, formula_params)

        elif data_source.source_type == "FORMULA":
            # 纯公式计算
            formula_params = json.loads(data_source.formula_params) if data_source.formula_params else {}
            value = calculate_formula(data_source.formula, formula_params)

        else:
            # 手动采集，返回当前值
            value = kpi.current_value

        # 更新数据源执行信息
        data_source.last_executed_at = datetime.now()
        data_source.last_result = str(value) if value is not None else None
        data_source.last_error = None
        db.commit()

        return value

    except Exception as e:
        # 记录错误
        data_source.last_executed_at = datetime.now()
        data_source.last_error = str(e)
        db.commit()
        return None


def auto_collect_kpi(
    db: Session,
    kpi_id: int,
    recorded_by: Optional[int] = None
) -> Optional[KPI]:
    """
    自动采集并更新 KPI 值

    Args:
        db: 数据库会话
        kpi_id: KPI ID
        recorded_by: 记录人（系统采集时为空）

    Returns:
        Optional[KPI]: 更新后的 KPI
    """
    value = collect_kpi_value(db, kpi_id)
    if value is None:
        return None

    kpi = db.query(KPI).filter(KPI.id == kpi_id, KPI.is_active == True).first()
    if not kpi:
        return None

    # 更新当前值
    kpi.current_value = value
    kpi.last_collected_at = datetime.now()

    # 创建历史记录
    from .kpi_service import create_kpi_snapshot
    create_kpi_snapshot(db, kpi_id, "AUTO", recorded_by)

    db.commit()
    db.refresh(kpi)
    return kpi


def batch_collect_kpis(
    db: Session,
    strategy_id: Optional[int] = None,
    frequency: Optional[str] = None
) -> Dict[str, Any]:
    """
    批量采集 KPI

    Args:
        db: 数据库会话
        strategy_id: 战略 ID（可选）
        frequency: 采集频率筛选（可选）

    Returns:
        Dict: 采集结果统计
    """
    from app.models.strategy import CSF

    query = db.query(KPI).filter(
        KPI.is_active == True,
        KPI.data_source_type == "AUTO"
    )

    if strategy_id:
        query = query.join(CSF).filter(
            CSF.strategy_id == strategy_id,
            CSF.is_active == True
        )

    if frequency:
        query = query.filter(KPI.frequency == frequency)

    kpis = query.all()

    success_count = 0
    failed_count = 0
    failed_kpis: List[Dict[str, Any]] = []

    for kpi in kpis:
        result = auto_collect_kpi(db, kpi.id)
        if result:
            success_count += 1
        else:
            failed_count += 1
            failed_kpis.append({"id": kpi.id, "code": kpi.code, "name": kpi.name})

    return {
        "total": len(kpis),
        "success": success_count,
        "failed": failed_count,
        "failed_kpis": failed_kpis,
        "collected_at": datetime.now(),
    }


def get_collection_status(db: Session, strategy_id: int) -> Dict[str, Any]:
    """
    获取采集状态概览

    Args:
        db: 数据库会话
        strategy_id: 战略 ID

    Returns:
        Dict: 采集状态统计
    """
    from app.models.strategy import CSF

    kpis = db.query(KPI).join(CSF).filter(
        CSF.strategy_id == strategy_id,
        CSF.is_active == True,
        KPI.is_active == True
    ).all()

    auto_kpis = [k for k in kpis if k.data_source_type == "AUTO"]
    manual_kpis = [k for k in kpis if k.data_source_type == "MANUAL"]

    # 统计各频率的 KPI
    frequency_stats: Dict[str, Dict[str, int]] = {}
    for kpi in kpis:
        freq = kpi.frequency or "UNKNOWN"
        if freq not in frequency_stats:
            frequency_stats[freq] = {"total": 0, "collected": 0}
        frequency_stats[freq]["total"] += 1
        if kpi.current_value is not None:
            frequency_stats[freq]["collected"] += 1

    # 最近采集时间
    collected_times = [k.last_collected_at for k in kpis if k.last_collected_at]
    last_collected = max(collected_times) if collected_times else None

    return {
        "total_kpis": len(kpis),
        "auto_kpis": len(auto_kpis),
        "manual_kpis": len(manual_kpis),
        "collected_kpis": sum(1 for k in kpis if k.current_value is not None),
        "pending_kpis": sum(1 for k in kpis if k.current_value is None),
        "frequency_stats": frequency_stats,
        "last_collected_at": last_collected,
    }
