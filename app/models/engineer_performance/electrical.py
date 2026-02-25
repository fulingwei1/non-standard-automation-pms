# -*- coding: utf-8 -*-
"""
工程师绩效评价模块 - 电气工程师专属模型
"""
from sqlalchemy import (
    JSON,
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


class ElectricalDrawingVersion(Base, TimestampMixin):
    """电气图纸版本
    
    【状态】未启用 - 电气图纸版本"""
    __tablename__ = 'electrical_drawing_version'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    project_id = Column(Integer, ForeignKey('projects.id'), comment='项目ID')
    designer_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='设计者ID')

    # 图纸信息
    drawing_name = Column(String(200), nullable=False, comment='图纸名称')
    drawing_code = Column(String(50), comment='图纸编号')
    drawing_type = Column(String(50), comment='图纸类型')
    version = Column(String(20), comment='版本号')

    # 评审结果
    review_date = Column(Date, comment='评审日期')
    reviewer_id = Column(Integer, ForeignKey('users.id'), comment='评审人ID')
    result = Column(String(20), comment='评审结果')
    is_first_pass = Column(Boolean, comment='是否一次通过')
    issues_found = Column(Integer, default=0, comment='发现问题数')
    review_comments = Column(Text, comment='评审意见')

    # 关系
    designer = relationship('User', foreign_keys=[designer_id])
    reviewer = relationship('User', foreign_keys=[reviewer_id])
    project = relationship('Project', foreign_keys=[project_id])

    __table_args__ = (
        Index('idx_elec_drawing_project', 'project_id'),
        Index('idx_elec_drawing_designer', 'designer_id'),
        Index('idx_elec_drawing_type', 'drawing_type'),
        {'comment': '电气图纸版本表'}
    )


class PlcProgramVersion(Base, TimestampMixin):
    """PLC程序版本"""
    __tablename__ = 'plc_program_version'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    project_id = Column(Integer, ForeignKey('projects.id'), comment='项目ID')
    programmer_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='程序员ID')

    # 程序信息
    program_name = Column(String(200), nullable=False, comment='程序名称')
    program_code = Column(String(50), comment='程序编号')
    plc_brand = Column(String(30), comment='PLC品牌')
    plc_model = Column(String(50), comment='PLC型号')
    version = Column(String(20), comment='版本号')

    # 调试结果
    first_debug_date = Column(Date, comment='首次调试日期')
    is_first_pass = Column(Boolean, comment='是否一次调通')
    debug_issues = Column(Integer, default=0, comment='调试问题数')
    debug_hours = Column(Numeric(6, 2), comment='调试工时')

    # 备注
    remarks = Column(Text, comment='备注')

    # 关系
    programmer = relationship('User', foreign_keys=[programmer_id])
    project = relationship('Project', foreign_keys=[project_id])

    __table_args__ = (
        Index('idx_plc_program_project', 'project_id'),
        Index('idx_plc_program_programmer', 'programmer_id'),
        Index('idx_plc_program_brand', 'plc_brand'),
        {'comment': 'PLC程序版本表'}
    )


class PlcModuleLibrary(Base, TimestampMixin):
    """PLC功能块库"""
    __tablename__ = 'plc_module_library'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    contributor_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='贡献者ID')

    # 模块信息
    module_name = Column(String(100), nullable=False, comment='模块名称')
    module_code = Column(String(50), comment='模块编号')
    category = Column(String(50), comment='分类')
    plc_brand = Column(String(30), comment='适用PLC品牌')
    description = Column(Text, comment='描述')

    # 版本信息
    version = Column(String(20), comment='版本')
    file_path = Column(String(500), comment='文件路径')

    # 复用统计
    reuse_count = Column(Integer, default=0, comment='复用次数')
    projects_used = Column(JSON, comment='使用项目列表')
    rating_score = Column(Numeric(3, 2), comment='平均评分')
    rating_count = Column(Integer, default=0, comment='评分次数')

    # 状态
    status = Column(String(20), default='active', comment='状态')

    # 关系
    contributor = relationship('User', foreign_keys=[contributor_id])

    __table_args__ = (
        Index('idx_plc_module_contributor', 'contributor_id'),
        Index('idx_plc_module_category', 'category'),
        Index('idx_plc_module_brand', 'plc_brand'),
        {'comment': 'PLC功能块库表'}
    )


class ComponentSelection(Base, TimestampMixin):
    """元器件选型记录
    
    【状态】未启用 - 元件选型"""
    __tablename__ = 'component_selection'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    project_id = Column(Integer, ForeignKey('projects.id'), comment='项目ID')
    engineer_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='工程师ID')

    # 选型信息
    component_name = Column(String(200), nullable=False, comment='元器件名称')
    component_type = Column(String(50), comment='元器件类型')
    specification = Column(String(200), comment='规格型号')
    manufacturer = Column(String(100), comment='制造商')

    # 选型结果
    is_standard = Column(Boolean, default=False, comment='是否标准件')
    is_from_stock = Column(Boolean, default=False, comment='是否库存件')
    selection_result = Column(String(20), comment='选型结果')
    replacement_reason = Column(Text, comment='替换原因')

    # 关系
    engineer = relationship('User', foreign_keys=[engineer_id])
    project = relationship('Project', foreign_keys=[project_id])

    __table_args__ = (
        Index('idx_comp_selection_project', 'project_id'),
        Index('idx_comp_selection_engineer', 'engineer_id'),
        Index('idx_comp_selection_type', 'component_type'),
        {'comment': '元器件选型记录表'}
    )


class ElectricalFaultRecord(Base, TimestampMixin):
    """电气故障记录
    
    【状态】未启用 - 电气故障记录"""
    __tablename__ = 'electrical_fault_record'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    project_id = Column(Integer, ForeignKey('projects.id'), comment='项目ID')
    responsible_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='责任人ID')
    reporter_id = Column(Integer, ForeignKey('users.id'), comment='报告人ID')

    # 故障信息
    fault_code = Column(String(50), comment='故障编号')
    fault_description = Column(Text, nullable=False, comment='故障描述')
    fault_type = Column(String(50), comment='故障类型')
    severity = Column(String(20), comment='严重程度')

    # 处理状态
    status = Column(String(20), default='open', comment='状态')
    found_date = Column(Date, comment='发现日期')
    resolved_date = Column(Date, comment='解决日期')
    resolution = Column(Text, comment='解决方案')
    root_cause = Column(Text, comment='根本原因')

    # 影响评估
    downtime_hours = Column(Numeric(6, 2), comment='停机时间(小时)')
    cost_impact = Column(Numeric(12, 2), comment='成本影响')

    # 关系
    responsible = relationship('User', foreign_keys=[responsible_id])
    reporter = relationship('User', foreign_keys=[reporter_id])
    project = relationship('Project', foreign_keys=[project_id])

    __table_args__ = (
        Index('idx_elec_fault_project', 'project_id'),
        Index('idx_elec_fault_responsible', 'responsible_id'),
        Index('idx_elec_fault_severity', 'severity'),
        {'comment': '电气故障记录表'}
    )
