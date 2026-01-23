# -*- coding: utf-8 -*-
"""
项目扩展模型 - 将 Project 的大表拆分为功能模块

此文件包含从 Project 表拆分出来的子模型，用于：
1. 降低单表字段数量（从 80+ 降至 40）
2. 提高代码可维护性
3. 便于权限控制（不同模块可分别授权）
4. 支持未来功能扩展

迁移策略：
- 保留 Project 表原字段（向后兼容）
- 新增扩展表存储相关数据
- 通过 @property 方法透明访问
- 逐步迁移代码使用新表
"""

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from ..base import Base, TimestampMixin


class ProjectFinancial(Base, TimestampMixin):
    """
    项目财务信息表

    存储项目的财务相关字段，从 Project 表拆分。

    字段来源：Project 表的财务字段
    - 合同金额、预算金额、实际成本
    - 开票状态、付款状态、付款日期
    """
    __tablename__ = "project_financials"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(
        Integer, ForeignKey("projects.id"), unique=True, nullable=False, comment="项目ID"
    )

    # 金额信息
    contract_amount = Column(Numeric(14, 2), default=0, comment="合同金额")
    budget_amount = Column(Numeric(14, 2), default=0, comment="预算金额")
    actual_cost = Column(Numeric(14, 2), default=0, comment="实际成本")

    # 开票与付款
    invoice_issued = Column(Boolean, default=False, comment="是否已开票")
    final_payment_completed = Column(Boolean, default=False, comment="是否已结尾款")
    final_payment_date = Column(Date, comment="结尾款日期")

    # 关系
    project = relationship("Project", back_populates="financial_info")

    __table_args__ = (
        Index("idx_project_financials_project", "project_id"),
    )

    @property
    def payment_progress_pct(self) -> float:
        """付款进度百分比"""
        if self.contract_amount == 0:
            return 0
        # 这里需要根据实际付款记录计算，暂时返回0
        return 0

    @property
    def cost_variance(self) -> float:
        """成本差异（预算 - 实际）"""
        return float(self.budget_amount - self.actual_cost)

    @property
    def is_over_budget(self) -> bool:
        """是否超预算"""
        return self.actual_cost > self.budget_amount

    def __repr__(self):
        return f"<ProjectFinancial {self.project_id}>"


class ProjectERP(Base, TimestampMixin):
    """
    项目ERP集成信息表

    存储项目与ERP系统集成的相关字段，从 Project 表拆分。
    """
    __tablename__ = "project_erp"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(
        Integer, ForeignKey("projects.id"), unique=True, nullable=False, comment="项目ID"
    )

    # ERP集成
    erp_synced = Column(Boolean, default=False, comment="是否已录入ERP系统")
    erp_sync_time = Column(DateTime, comment="ERP同步时间")
    erp_order_no = Column(String(50), comment="ERP订单号")
    erp_sync_status = Column(String(20), default="PENDING", comment="ERP同步状态：PENDING/SYNCED/FAILED")

    # 同步错误信息
    erp_sync_error = Column(Text, comment="同步错误信息")
    erp_last_sync_at = Column(DateTime, comment="最后同步时间")

    # 关系
    project = relationship("Project", back_populates="erp_info")

    __table_args__ = (
        Index("idx_project_erp_project", "project_id"),
        Index("idx_project_erp_status", "erp_sync_status"),
    )

    @property
    def is_synced(self) -> bool:
        """是否已同步成功"""
        return self.erp_sync_status == "SYNCED"

    @property
    def sync_status_display(self) -> str:
        """同步状态显示名称"""
        status_map = {
            "PENDING": "待同步",
            "SYNCED": "已同步",
            "FAILED": "同步失败",
        }
        return status_map.get(self.erp_sync_status, self.erp_sync_status)

    def __repr__(self):
        return f"<ProjectERP {self.project_id}>"


class ProjectWarranty(Base, TimestampMixin):
    """
    项目质保信息表

    存储项目的质保相关信息，从 Project 表拆分。
    """
    __tablename__ = "project_warranties"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(
        Integer, ForeignKey("projects.id"), unique=True, nullable=False, comment="项目ID"
    )

    # 质保信息
    warranty_period_months = Column(Integer, comment="质保期限（月）")
    warranty_start_date = Column(Date, comment="质保开始日期")
    warranty_end_date = Column(Date, comment="质保结束日期")

    # 质保状态
    warranty_status = Column(String(20), default="ACTIVE", comment="质保状态：ACTIVE/EXPIRED/EXTENDED")
    warranty_notes = Column(Text, comment="质保备注")

    # 关系
    project = relationship("Project", back_populates="warranty_info")

    __table_args__ = (
        Index("idx_project_warranties_project", "project_id"),
        Index("idx_project_warranties_end_date", "warranty_end_date"),
    )

    @property
    def remaining_days(self) -> int:
        """剩余质保天数"""
        if not self.warranty_end_date:
            return 0
        delta = self.warranty_end_date - date.today()
        return max(0, delta.days)

    @property
    def is_expired(self) -> bool:
        """质保是否已过期"""
        if not self.warranty_end_date:
            return False
        return date.today() > self.warranty_end_date

    @property
    def is_expiring_soon(self, days: int = 30) -> bool:
        """质保是否即将过期（默认30天内）"""
        if not self.warranty_end_date:
            return False
        delta = self.warranty_end_date - date.today()
        return 0 <= delta.days <= days

    def __repr__(self):
        return f"<ProjectWarranty {self.project_id}>"


class ProjectImplementation(Base, TimestampMixin):
    """
    项目实施信息表

    存储项目的实施相关信息，从 Project 表拆分。
    """
    __tablename__ = "project_implementations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(
        Integer, ForeignKey("projects.id"), unique=True, nullable=False, comment="项目ID"
    )

    # 实施信息
    implementation_address = Column(String(500), comment="实施地址")
    test_encryption = Column(String(100), comment="测试加密")

    # 实施联系人
    site_contact_name = Column(String(50), comment="现场联系人姓名")
    site_contact_phone = Column(String(30), comment="现场联系人电话")
    site_contact_email = Column(String(100), comment="现场联系人邮箱")

    # 实施环境
    site_conditions = Column(Text, comment="现场条件说明")
    installation_requirements = Column(Text, comment="安装要求")

    # 关系
    project = relationship("Project", back_populates="implementation_info")

    __table_args__ = (
        Index("idx_project_implementations_project", "project_id"),
    )

    @property
    def has_site_contact(self) -> bool:
        """是否有现场联系人信息"""
        return bool(self.site_contact_name or self.site_contact_phone)

    @property
    def contact_info(self) -> dict:
        """获取现场联系人信息"""
        return {
            'name': self.site_contact_name,
            'phone': self.site_contact_phone,
            'email': self.site_contact_email,
        }

    def __repr__(self):
        return f"<ProjectImplementation {self.project_id}>"


class ProjectPresale(Base, TimestampMixin):
    """
    项目售前评估信息表

    存储项目的售前评估相关信息，从 Project 表拆分。
    """
    __tablename__ = "project_presales"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(
        Integer, ForeignKey("projects.id"), unique=True, nullable=False, comment="项目ID"
    )

    # 售前评估
    source_lead_id = Column(String(50), comment="来源线索号（如XS2501001）")
    evaluation_score = Column(Numeric(5, 2), comment="评估总分")
    predicted_win_rate = Column(Numeric(5, 4), comment="预测中标率（0-1）")
    outcome = Column(String(20), comment="最终结果：PENDING/WON/LOST/ABANDONED")

    # 丢标原因
    loss_reason = Column(String(50), comment="丢标原因代码")
    loss_reason_detail = Column(Text, comment="丢标原因详情")

    # 竞争对手信息
    competitor_info = Column(Text, comment="竞争对手信息JSON")

    # 关系
    project = relationship("Project", back_populates="presale_info")

    __table_args__ = (
        Index("idx_project_presales_project", "project_id"),
        Index("idx_project_presales_outcome", "outcome"),
    )

    @property
    def predicted_win_rate_pct(self) -> float:
        """预测中标率百分比"""
        return float(self.predicted_win_rate * 100) if self.predicted_win_rate else 0

    @property
    def is_won(self) -> bool:
        """是否中标"""
        return self.outcome == "WON"

    @property
    def is_lost(self) -> bool:
        """是否丢标"""
        return self.outcome == "LOST"

    @property
    def outcome_display(self) -> str:
        """结果显示名称"""
        outcome_map = {
            "PENDING": "进行中",
            "WON": "中标",
            "LOST": "丢标",
            "ABANDONED": "已放弃",
        }
        return outcome_map.get(self.outcome, self.outcome)

    def __repr__(self):
        return f"<ProjectPresale {self.project_id}>"
