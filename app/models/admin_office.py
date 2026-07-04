# -*- coding: utf-8 -*-
"""行政管理模型（ADMIN-07 做实：用品/车辆/资产/费用）。

此前 /admin/* 四件套为整段硬编码演示数据且写端点缺失（前端 POST 必 404）。
"""
from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text

from app.models.base import Base, TimestampMixin


class AdminSupply(Base, TimestampMixin):
    """办公用品台账"""

    __tablename__ = "admin_supplies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment="用品名称")
    category = Column(String(50), comment="分类")
    specification = Column(String(200), comment="规格")
    unit = Column(String(20), default="件", comment="单位")
    current_stock = Column(Integer, default=0, comment="当前库存")
    min_stock = Column(Integer, default=0, comment="安全库存")
    unit_price = Column(Numeric(10, 2), default=0, comment="单价")
    supplier = Column(String(100), comment="供应商")
    last_purchase_date = Column(Date, comment="最近采购日期")
    created_by = Column(Integer, ForeignKey("users.id"), comment="创建人")


class AdminSupplyRequest(Base, TimestampMixin):
    """办公用品申领单"""

    __tablename__ = "admin_supply_requests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    supply_id = Column(Integer, ForeignKey("admin_supplies.id"), nullable=False, comment="用品ID")
    quantity = Column(Integer, nullable=False, comment="申领数量")
    reason = Column(Text, comment="申领事由")
    status = Column(String(20), default="PENDING", comment="状态: PENDING/APPROVED/REJECTED")
    requested_by = Column(Integer, ForeignKey("users.id"), comment="申领人")
    approved_by = Column(Integer, ForeignKey("users.id"), comment="审批人")
    approved_at = Column(DateTime, comment="审批时间")
    approval_comment = Column(Text, comment="审批意见")


class AdminVehicle(Base, TimestampMixin):
    """公务车辆台账"""

    __tablename__ = "admin_vehicles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plate_no = Column(String(20), unique=True, nullable=False, comment="车牌号")
    model = Column(String(100), comment="车型")
    seats = Column(Integer, comment="座位数")
    status = Column(String(20), default="AVAILABLE", comment="状态: AVAILABLE/IN_USE/MAINTENANCE")
    current_driver = Column(String(50), comment="当前使用人")
    remark = Column(Text, comment="备注")


class AdminVehicleRequest(Base, TimestampMixin):
    """用车申请单"""

    __tablename__ = "admin_vehicle_requests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    vehicle_id = Column(Integer, ForeignKey("admin_vehicles.id"), comment="车辆ID（可待分配）")
    use_date = Column(Date, nullable=False, comment="用车日期")
    destination = Column(String(200), comment="目的地")
    purpose = Column(Text, comment="用车事由")
    status = Column(String(20), default="PENDING", comment="状态: PENDING/APPROVED/REJECTED/RETURNED")
    requested_by = Column(Integer, ForeignKey("users.id"), comment="申请人")
    approved_by = Column(Integer, ForeignKey("users.id"), comment="审批人")
    approved_at = Column(DateTime, comment="审批时间")
    approval_comment = Column(Text, comment="审批意见")


class AdminAsset(Base, TimestampMixin):
    """固定资产台账"""

    __tablename__ = "admin_assets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    asset_no = Column(String(50), unique=True, nullable=False, comment="资产编号")
    name = Column(String(100), nullable=False, comment="资产名称")
    category = Column(String(50), comment="分类")
    specification = Column(String(200), comment="规格型号")
    value = Column(Numeric(12, 2), default=0, comment="资产原值")
    purchase_date = Column(Date, comment="购置日期")
    custodian = Column(String(50), comment="保管人")
    location = Column(String(100), comment="存放地点")
    status = Column(String(20), default="IN_USE", comment="状态: IN_USE/IDLE/REPAIRING/SCRAPPED")
    remark = Column(Text, comment="备注")
    created_by = Column(Integer, ForeignKey("users.id"), comment="创建人")


class AdminExpense(Base, TimestampMixin):
    """行政费用记录"""

    __tablename__ = "admin_expenses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    expense_no = Column(String(50), unique=True, comment="费用编号")
    category = Column(String(50), nullable=False, comment="费用类别")
    amount = Column(Numeric(12, 2), nullable=False, comment="金额")
    expense_date = Column(Date, nullable=False, comment="发生日期")
    description = Column(Text, comment="说明")
    status = Column(String(20), default="RECORDED", comment="状态: RECORDED/REIMBURSED")
    created_by = Column(Integer, ForeignKey("users.id"), comment="登记人")
