# -*- coding: utf-8 -*-
"""
售前费用模块 ORM 模型
包含：售前费用记录
"""


from sqlalchemy import (
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


class PresaleExpense(Base, TimestampMixin):
    """售前费用表"""
    __tablename__ = 'presale_expenses'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')

    # 项目关联
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, comment='项目ID（未中标项目）')
    project_code = Column(String(50), comment='项目编号（冗余字段）')
    project_name = Column(String(200), comment='项目名称（冗余字段）')

    # 线索/商机关联
    lead_id = Column(Integer, ForeignKey('leads.id'), comment='关联线索ID')
    opportunity_id = Column(Integer, ForeignKey('opportunities.id'), comment='关联商机ID')

    # 费用信息
    expense_type = Column(String(20), nullable=False, comment='费用类型：LABOR_COST/TRAVEL_COST/OTHER')
    expense_category = Column(String(50), nullable=False, comment='费用分类：LOST_BID/ABANDONED')
    amount = Column(Numeric(14, 2), nullable=False, comment='费用金额')

    # 工时信息（如果是工时费用）
    labor_hours = Column(Numeric(10, 2), comment='工时数（如果是工时费用）')
    hourly_rate = Column(Numeric(10, 2), comment='工时单价')

    # 人员信息
    user_id = Column(Integer, ForeignKey('users.id'), comment='人员ID（工时费用）')
    user_name = Column(String(50), comment='人员姓名（冗余）')
    department_id = Column(Integer, comment='部门ID')
    department_name = Column(String(100), comment='部门名称（冗余）')

    # 销售人员信息
    salesperson_id = Column(Integer, ForeignKey('users.id'), comment='销售人员ID')
    salesperson_name = Column(String(50), comment='销售人员姓名（冗余）')

    # 时间信息
    expense_date = Column(Date, nullable=False, comment='费用发生日期')

    # 详细信息
    description = Column(Text, comment='费用说明')
    loss_reason = Column(String(50), comment='未中标原因')
    loss_reason_detail = Column(Text, comment='未中标原因详情')

    # 创建信息
    created_by = Column(Integer, ForeignKey('users.id'), comment='创建人ID')

    # 关系
    project = relationship('Project', foreign_keys=[project_id])
    lead = relationship('Lead', foreign_keys=[lead_id])
    opportunity = relationship('Opportunity', foreign_keys=[opportunity_id])
    user = relationship('User', foreign_keys=[user_id])
    salesperson = relationship('User', foreign_keys=[salesperson_id])
    creator = relationship('User', foreign_keys=[created_by])

    __table_args__ = (
        Index('idx_presale_expense_project', 'project_id'),
        Index('idx_presale_expense_lead', 'lead_id'),
        Index('idx_presale_expense_opportunity', 'opportunity_id'),
        Index('idx_presale_expense_type', 'expense_type'),
        Index('idx_presale_expense_category', 'expense_category'),
        Index('idx_presale_expense_date', 'expense_date'),
        Index('idx_presale_expense_user', 'user_id'),
        Index('idx_presale_expense_salesperson', 'salesperson_id'),
        Index('idx_presale_expense_department', 'department_id'),
        {'comment': '售前费用表'}
    )

    def __repr__(self):
        return f'<PresaleExpense {self.project_code}-{self.expense_type}>'
