# -*- coding: utf-8 -*-
"""
技术规格管理模块模型
"""

from sqlalchemy import (
    JSON,
    BigInteger,
    Column,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class TechnicalSpecRequirement(Base, TimestampMixin):
    """技术规格要求表"""
    __tablename__ = 'technical_spec_requirements'

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, comment='项目ID')
    document_id = Column(Integer, ForeignKey('project_documents.id'), comment='关联技术规格书文档')

    # 物料信息
    material_code = Column(String(50), comment='物料编码（可选）')
    material_name = Column(String(200), nullable=False, comment='物料名称')
    specification = Column(String(500), nullable=False, comment='规格型号要求')
    brand = Column(String(100), comment='品牌要求')
    model = Column(String(100), comment='型号要求')

    # 关键参数（JSON格式，用于智能匹配）
    key_parameters = Column(JSON, comment='关键参数：电压、电流、精度、温度范围等')

    # 要求级别
    requirement_level = Column(String(20), default='REQUIRED', comment='要求级别：REQUIRED/OPTIONAL/STRICT')

    # 备注
    remark = Column(Text, comment='备注说明')
    extracted_by = Column(Integer, ForeignKey('users.id'), comment='提取人')

    # 关系
    project = relationship('Project', backref='technical_spec_requirements')
    document = relationship('ProjectDocument', backref='technical_spec_requirements')
    extractor = relationship('User', foreign_keys=[extracted_by])
    match_records = relationship('SpecMatchRecord', back_populates='spec_requirement', lazy='dynamic')

    __table_args__ = (
        Index('idx_spec_req_project', 'project_id'),
        Index('idx_spec_req_document', 'document_id'),
        Index('idx_spec_req_material', 'material_code'),
    )

    def __repr__(self):
        return f'<TechnicalSpecRequirement {self.id}: {self.material_name}>'


class SpecMatchRecord(Base, TimestampMixin):
    """规格匹配记录表"""
    __tablename__ = 'spec_match_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, comment='项目ID')
    spec_requirement_id = Column(Integer, ForeignKey('technical_spec_requirements.id'), comment='规格要求ID')

    # 匹配对象
    match_type = Column(String(20), nullable=False, comment='匹配类型：BOM/PURCHASE_ORDER')
    match_target_id = Column(Integer, nullable=False, comment='匹配对象ID（BOM行ID或采购订单行ID）')

    # 匹配结果
    match_status = Column(String(20), nullable=False, comment='匹配状态：MATCHED/MISMATCHED/UNKNOWN')
    match_score = Column(Numeric(5, 2), comment='匹配度（0-100）')

    # 差异详情（JSON）
    differences = Column(JSON, comment='差异详情')

    # 预警
    alert_id = Column(BigInteger, ForeignKey('alert_records.id'), comment='关联预警ID')

    # 关系
    project = relationship('Project', backref='spec_match_records')
    spec_requirement = relationship('TechnicalSpecRequirement', back_populates='match_records')
    alert = relationship('AlertRecord', foreign_keys=[alert_id])

    __table_args__ = (
        Index('idx_match_record_project', 'project_id'),
        Index('idx_match_record_spec', 'spec_requirement_id'),
        Index('idx_match_record_type', 'match_type', 'match_target_id'),
        Index('idx_match_record_status', 'match_status'),
        Index('idx_match_record_alert', 'alert_id'),
    )

    def __repr__(self):
        return f'<SpecMatchRecord {self.id}: {self.match_type}-{self.match_target_id} ({self.match_status})>'




