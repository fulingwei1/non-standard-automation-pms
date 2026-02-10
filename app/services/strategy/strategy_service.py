# -*- coding: utf-8 -*-
"""
战略管理服务 - Strategy CRUD
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.strategy import Strategy
from app.schemas.strategy import (
    StrategyCreate,
    StrategyDetailResponse,
    StrategyMapDimension,
    StrategyMapResponse,
    StrategyUpdate,
)


def create_strategy(
    db: Session,
    data: StrategyCreate,
    created_by: int
) -> Strategy:
    """
    创建战略

    Args:
        db: 数据库会话
        data: 创建数据
        created_by: 创建人ID

    Returns:
        Strategy: 创建的战略对象
    """
    strategy = Strategy(
        code=data.code,
        name=data.name,
        vision=data.vision,
        mission=data.mission,
        slogan=data.slogan,
        year=data.year,
        start_date=data.start_date,
        end_date=data.end_date,
        status="DRAFT",
        created_by=created_by,
    )
    db.add(strategy)
    db.commit()
    db.refresh(strategy)
    return strategy


def get_strategy(db: Session, strategy_id: int) -> Optional[Strategy]:
    """
    获取战略详情

    Args:
        db: 数据库会话
        strategy_id: 战略ID

    Returns:
        Optional[Strategy]: 战略对象
    """
    return db.query(Strategy).filter(
        Strategy.id == strategy_id,
        Strategy.is_active == True
    ).first()


def get_strategy_by_code(db: Session, code: str) -> Optional[Strategy]:
    """
    根据编码获取战略

    Args:
        db: 数据库会话
        code: 战略编码

    Returns:
        Optional[Strategy]: 战略对象
    """
    return db.query(Strategy).filter(
        Strategy.code == code,
        Strategy.is_active == True
    ).first()


def get_strategy_by_year(db: Session, year: int) -> Optional[Strategy]:
    """
    根据年度获取战略

    Args:
        db: 数据库会话
        year: 年度

    Returns:
        Optional[Strategy]: 战略对象
    """
    return db.query(Strategy).filter(
        Strategy.year == year,
        Strategy.is_active == True
    ).first()


def get_active_strategy(db: Session) -> Optional[Strategy]:
    """
    获取当前生效的战略

    Args:
        db: 数据库会话

    Returns:
        Optional[Strategy]: 生效的战略对象
    """
    return db.query(Strategy).filter(
        Strategy.status == "ACTIVE",
        Strategy.is_active == True
    ).first()


def list_strategies(
    db: Session,
    year: Optional[int] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 20
) -> tuple[List[Strategy], int]:
    """
    获取战略列表

    Args:
        db: 数据库会话
        year: 年度筛选
        status: 状态筛选
        skip: 跳过数量
        limit: 限制数量

    Returns:
        tuple: (战略列表, 总数)
    """
    query = db.query(Strategy).filter(Strategy.is_active == True)

    if year:
        query = query.filter(Strategy.year == year)
    if status:
        query = query.filter(Strategy.status == status)

    total = query.count()
    items = query.order_by(desc(Strategy.year), desc(Strategy.created_at)).offset(skip).limit(limit).all()

    return items, total


def update_strategy(
    db: Session,
    strategy_id: int,
    data: StrategyUpdate
) -> Optional[Strategy]:
    """
    更新战略

    Args:
        db: 数据库会话
        strategy_id: 战略ID
        data: 更新数据

    Returns:
        Optional[Strategy]: 更新后的战略对象
    """
    strategy = get_strategy(db, strategy_id)
    if not strategy:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(strategy, key, value)

    db.commit()
    db.refresh(strategy)
    return strategy


def publish_strategy(
    db: Session,
    strategy_id: int,
    approved_by: int
) -> Optional[Strategy]:
    """
    发布战略

    Args:
        db: 数据库会话
        strategy_id: 战略ID
        approved_by: 审批人ID

    Returns:
        Optional[Strategy]: 发布后的战略对象
    """
    strategy = get_strategy(db, strategy_id)
    if not strategy:
        return None

    # 将同年度其他战略设为归档
    db.query(Strategy).filter(
        Strategy.year == strategy.year,
        Strategy.id != strategy_id,
        Strategy.status == "ACTIVE"
    ).update({"status": "ARCHIVED"})

    # 发布当前战略
    strategy.status = "ACTIVE"
    strategy.approved_by = approved_by
    strategy.approved_at = datetime.now()
    strategy.published_at = datetime.now()

    db.commit()
    db.refresh(strategy)
    return strategy


def archive_strategy(db: Session, strategy_id: int) -> Optional[Strategy]:
    """
    归档战略

    Args:
        db: 数据库会话
        strategy_id: 战略ID

    Returns:
        Optional[Strategy]: 归档后的战略对象
    """
    strategy = get_strategy(db, strategy_id)
    if not strategy:
        return None

    strategy.status = "ARCHIVED"
    db.commit()
    db.refresh(strategy)
    return strategy


def delete_strategy(db: Session, strategy_id: int) -> bool:
    """
    删除战略（软删除）

    Args:
        db: 数据库会话
        strategy_id: 战略ID

    Returns:
        bool: 是否删除成功
    """
    strategy = get_strategy(db, strategy_id)
    if not strategy:
        return False

    strategy.is_active = False
    db.commit()
    return True


def get_strategy_detail(db: Session, strategy_id: int) -> Optional[StrategyDetailResponse]:
    """
    获取战略详情（包含统计信息）

    Args:
        db: 数据库会话
        strategy_id: 战略ID

    Returns:
        Optional[StrategyDetailResponse]: 战略详情
    """
    strategy = get_strategy(db, strategy_id)
    if not strategy:
        return None

    # 统计 CSF、KPI、重点工作数量
    from app.models.strategy import CSF, KPI, AnnualKeyWork

    csf_count = db.query(CSF).filter(
        CSF.strategy_id == strategy_id,
        CSF.is_active == True
    ).count()

    kpi_count = db.query(KPI).join(CSF).filter(
        CSF.strategy_id == strategy_id,
        CSF.is_active == True,
        KPI.is_active == True
    ).count()

    annual_work_count = db.query(AnnualKeyWork).join(CSF).filter(
        CSF.strategy_id == strategy_id,
        CSF.is_active == True,
        AnnualKeyWork.is_active == True
    ).count()

    # 获取健康度评分
    from .health_calculator import calculate_strategy_health
    health_score = calculate_strategy_health(db, strategy_id)

    return StrategyDetailResponse(
        id=strategy.id,
        code=strategy.code,
        name=strategy.name,
        vision=strategy.vision,
        mission=strategy.mission,
        slogan=strategy.slogan,
        year=strategy.year,
        start_date=strategy.start_date,
        end_date=strategy.end_date,
        status=strategy.status,
        created_by=strategy.created_by,
        approved_by=strategy.approved_by,
        approved_at=strategy.approved_at,
        published_at=strategy.published_at,
        is_active=strategy.is_active,
        created_at=strategy.created_at,
        updated_at=strategy.updated_at,
        csf_count=csf_count,
        kpi_count=kpi_count,
        annual_work_count=annual_work_count,
        health_score=health_score,
    )


def get_strategy_map_data(db: Session, strategy_id: int) -> Optional[StrategyMapResponse]:
    """
    获取战略地图数据

    Args:
        db: 数据库会话
        strategy_id: 战略ID

    Returns:
        Optional[StrategyMapResponse]: 战略地图数据
    """
    strategy = get_strategy(db, strategy_id)
    if not strategy:
        return None

    from app.models.strategy import CSF, KPI
    from .health_calculator import calculate_csf_health, calculate_strategy_health

    # BSC 四维度名称映射
    dimension_names = {
        "FINANCIAL": "财务维度",
        "CUSTOMER": "客户维度",
        "INTERNAL": "内部运营维度",
        "LEARNING": "学习成长维度",
    }

    dimensions = []
    for dim_code in ["FINANCIAL", "CUSTOMER", "INTERNAL", "LEARNING"]:
        csfs = db.query(CSF).filter(
            CSF.strategy_id == strategy_id,
            CSF.dimension == dim_code,
            CSF.is_active == True
        ).order_by(CSF.sort_order).all()

        csf_items = []
        total_weight = 0
        for csf in csfs:
            kpi_count = db.query(KPI).filter(
                KPI.csf_id == csf.id,
                KPI.is_active == True
            ).count()

            health_data = calculate_csf_health(db, csf.id)

            csf_items.append({
                "id": csf.id,
                "code": csf.code,
                "name": csf.name,
                "weight": float(csf.weight or 0),
                "health_score": health_data.get("score"),
                "health_level": health_data.get("level"),
                "kpi_count": kpi_count,
                "kpi_completion_rate": health_data.get("kpi_completion_rate"),
            })
            total_weight += float(csf.weight or 0)

        # 计算维度健康度（CSF 加权平均）
        dim_health = None
        if csf_items:
            weighted_sum = sum(
                (c["health_score"] or 0) * c["weight"]
                for c in csf_items
            )
            if total_weight > 0:
                dim_health = int(weighted_sum / total_weight)

        dimensions.append(StrategyMapDimension(
            dimension=dim_code,
            dimension_name=dimension_names[dim_code],
            csfs=csf_items,
            health_score=dim_health,
            total_weight=total_weight,
        ))

    overall_health = calculate_strategy_health(db, strategy_id)

    return StrategyMapResponse(
        strategy_id=strategy.id,
        strategy_code=strategy.code,
        strategy_name=strategy.name,
        vision=strategy.vision,
        slogan=strategy.slogan,
        year=strategy.year,
        overall_health_score=overall_health,
        dimensions=dimensions,
    )


class StrategyService:
    """兼容包装类：测试中使用 StrategyService(db) 形式调用"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, data: StrategyCreate, created_by: int) -> Strategy:
        return create_strategy(self.db, data, created_by)

    def get(self, strategy_id: int) -> Optional[Strategy]:
        return get_strategy(self.db, strategy_id)

    def list(
        self,
        year: Optional[int] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[List[Strategy], int]:
        return list_strategies(self.db, year=year, status=status, skip=skip, limit=limit)

    def update(self, strategy_id: int, data: StrategyUpdate) -> Optional[Strategy]:
        return update_strategy(self.db, strategy_id, data)

    def delete(self, strategy_id: int) -> bool:
        return delete_strategy(self.db, strategy_id)

    def get_detail(self, strategy_id: int) -> Optional[StrategyDetailResponse]:
        return get_strategy_detail(self.db, strategy_id)

    def get_metrics(self, strategy_id: int) -> dict:
        """获取战略指标统计"""
        detail = get_strategy_detail(self.db, strategy_id)
        if not detail:
            return {}
        return {
            "csf_count": detail.csf_count,
            "kpi_count": detail.kpi_count,
            "annual_work_count": detail.annual_work_count,
            "health_score": detail.health_score,
        }

    # 兼容别名方法
    def get_strategies(self, **kwargs):
        # 将 page/page_size 转换为 skip/limit
        if 'page' in kwargs or 'page_size' in kwargs:
            page = kwargs.pop('page', 1)
            page_size = kwargs.pop('page_size', 20)
            kwargs['skip'] = (page - 1) * page_size
            kwargs['limit'] = page_size
        return self.list(**kwargs)

    def get_strategy(self, strategy_id: int):
        return self.get(strategy_id)

    def create_strategy(self, data, created_by: int = 0):
        return self.create(data, created_by)

    def update_strategy(self, strategy_id: int, data):
        return self.update(strategy_id, data)

    def delete_strategy(self, strategy_id: int) -> bool:
        return self.delete(strategy_id)

    def get_strategy_metrics(self, strategy_id: int) -> dict:
        return self.get_metrics(strategy_id)
