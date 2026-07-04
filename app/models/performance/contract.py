# -*- coding: utf-8 -*-
"""ORM models for performance contracts."""

from sqlalchemy import CheckConstraint, Column, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class PerformanceContract(Base, TimestampMixin):
    """绩效合约"""

    __tablename__ = "performance_contracts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True, comment="租户ID")
    contract_no = Column(String(100), unique=True, nullable=False)
    contract_type = Column(String(10), nullable=False)
    year = Column(Integer, nullable=False)
    quarter = Column(Integer)
    signer_id = Column(Integer)
    signer_name = Column(String(100), nullable=False)
    signer_title = Column(String(100))
    counterpart_id = Column(Integer)
    counterpart_name = Column(String(100), nullable=False)
    counterpart_title = Column(String(100))
    department_id = Column(Integer)
    department_name = Column(String(100))
    strategy_id = Column(Integer)
    status = Column(String(30), nullable=False, default="draft")
    total_weight = Column(Float, default=0)
    sign_date = Column(String(20))
    effective_date = Column(String(20))
    expiry_date = Column(String(20))
    signer_signature = Column(String(30))
    counterpart_signature = Column(String(30))
    remarks = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"))

    items = relationship(
        "PerformanceContractItem",
        back_populates="contract",
        cascade="all, delete-orphan",
        order_by="PerformanceContractItem.sort_order, PerformanceContractItem.id",
    )

    __table_args__ = (
        CheckConstraint("contract_type IN ('L1', 'L2', 'L3')", name="ck_perf_contract_type"),
        CheckConstraint(
            "status IN ('draft', 'pending_review', 'pending_sign', 'active', 'completed', 'terminated')",
            name="ck_perf_contract_status",
        ),
        Index("idx_perf_contract_type", "contract_type"),
        Index("idx_perf_contract_status", "status"),
        Index("idx_perf_contract_year", "year"),
        Index("idx_perf_contract_signer", "signer_id"),
    )


class PerformanceContractItem(Base, TimestampMixin):
    """绩效合约指标条目"""

    __tablename__ = "performance_contract_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True, comment="租户ID")
    contract_id = Column(
        Integer,
        ForeignKey("performance_contracts.id", ondelete="CASCADE"),
        nullable=False,
    )
    sort_order = Column(Integer, default=0)
    category = Column(String(30), nullable=False)
    indicator_name = Column(String(200), nullable=False)
    indicator_description = Column(Text)
    weight = Column(Float, nullable=False)
    unit = Column(String(50))
    target_value = Column(String(100))
    challenge_value = Column(String(100))
    baseline_value = Column(String(100))
    scoring_rule = Column(Text)
    data_source = Column(String(200))
    evaluation_method = Column(String(100))
    actual_value = Column(String(100))
    score = Column(Float)
    evaluator_comment = Column(Text)
    source_type = Column(String(20))
    source_id = Column(Integer)

    contract = relationship("PerformanceContract", back_populates="items")

    __table_args__ = (
        CheckConstraint(
            "category IN ('业绩指标', '管理指标', '能力指标', '态度指标')",
            name="ck_perf_contract_item_category",
        ),
        CheckConstraint(
            "source_type IS NULL OR source_type IN ('kpi', 'work', 'custom')",
            name="ck_perf_contract_item_source_type",
        ),
        Index("idx_perf_contract_item_contract", "contract_id"),
        Index("idx_perf_contract_item_source", "source_type", "source_id"),
    )
