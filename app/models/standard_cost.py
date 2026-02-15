# -*- coding: utf-8 -*-
"""
标准成本库管理 ORM 模型
包含：标准成本项、标准成本历史记录
"""

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class StandardCost(Base, TimestampMixin):
    """标准成本表"""

    __tablename__ = "standard_costs"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    cost_code = Column(String(50), nullable=False, comment="成本项编码")
    cost_name = Column(String(200), nullable=False, comment="成本项名称")
    
    # 成本分类
    cost_category = Column(
        String(50), 
        nullable=False, 
        comment="成本类别：MATERIAL/LABOR/OVERHEAD"
    )
    
    # 成本详情
    specification = Column(String(500), comment="规格型号")
    unit = Column(String(20), nullable=False, comment="单位（如：件、kg、人天）")
    standard_cost = Column(Numeric(15, 4), nullable=False, comment="标准成本")
    currency = Column(String(10), default="CNY", comment="币种")
    
    # 成本来源
    cost_source = Column(
        String(50),
        nullable=False,
        comment="成本来源：HISTORICAL_AVG/INDUSTRY_STANDARD/EXPERT_ESTIMATE/VENDOR_QUOTE"
    )
    source_description = Column(Text, comment="来源说明")
    
    # 生效期
    effective_date = Column(Date, nullable=False, comment="生效日期")
    expiry_date = Column(Date, comment="失效日期（为空表示长期有效）")
    
    # 版本管理
    version = Column(Integer, default=1, comment="版本号")
    is_active = Column(Boolean, default=True, comment="是否当前有效版本")
    
    # 元数据
    parent_id = Column(Integer, ForeignKey("standard_costs.id"), comment="父成本项ID（用于版本追踪）")
    created_by = Column(Integer, ForeignKey("users.id"), comment="创建人ID")
    updated_by = Column(Integer, ForeignKey("users.id"), comment="更新人ID")
    
    # 备注
    description = Column(Text, comment="成本说明")
    notes = Column(Text, comment="备注")
    
    # 关系
    parent = relationship("StandardCost", remote_side=[id], backref="versions")
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    history_records = relationship(
        "StandardCostHistory", 
        back_populates="standard_cost",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_standard_cost_code", "cost_code"),
        Index("idx_standard_cost_category", "cost_category"),
        Index("idx_standard_cost_active", "is_active"),
        Index("idx_standard_cost_effective", "effective_date", "expiry_date"),
        Index("idx_standard_cost_code_version", "cost_code", "version"),
        {"comment": "标准成本表"}
    )

    def __repr__(self):
        return f"<StandardCost {self.cost_code} v{self.version}>"


class StandardCostHistory(Base, TimestampMixin):
    """标准成本历史记录表"""

    __tablename__ = "standard_cost_history"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    standard_cost_id = Column(
        Integer, 
        ForeignKey("standard_costs.id"), 
        nullable=False, 
        comment="标准成本ID"
    )
    
    # 变更信息
    change_type = Column(
        String(20), 
        nullable=False, 
        comment="变更类型：CREATE/UPDATE/ACTIVATE/DEACTIVATE"
    )
    change_date = Column(Date, nullable=False, comment="变更日期")
    
    # 变更前后值
    old_cost = Column(Numeric(15, 4), comment="变更前成本")
    new_cost = Column(Numeric(15, 4), comment="变更后成本")
    old_effective_date = Column(Date, comment="变更前生效日期")
    new_effective_date = Column(Date, comment="变更后生效日期")
    
    # 变更原因
    change_reason = Column(Text, comment="变更原因")
    change_description = Column(Text, comment="变更说明")
    
    # 操作人
    changed_by = Column(Integer, ForeignKey("users.id"), comment="变更人ID")
    changed_by_name = Column(String(50), comment="变更人姓名（冗余）")
    
    # 关系
    standard_cost = relationship("StandardCost", back_populates="history_records")
    changer = relationship("User", foreign_keys=[changed_by])

    __table_args__ = (
        Index("idx_cost_history_cost_id", "standard_cost_id"),
        Index("idx_cost_history_change_date", "change_date"),
        Index("idx_cost_history_change_type", "change_type"),
        {"comment": "标准成本历史记录表"}
    )

    def __repr__(self):
        return f"<StandardCostHistory {self.change_type} at {self.change_date}>"
