# -*- coding: utf-8 -*-
"""
工程师绩效评价模块 ORM 模型
包含：工程师档案、五维评价配置、跨部门协作、知识贡献、岗位专属数据表
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Date, DateTime,
    Numeric, ForeignKey, Index, JSON
)
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin
from enum import Enum


# ==================== 枚举定义 ====================

class EngineerJobTypeEnum(str, Enum):
    """工程师岗位类型"""
    MECHANICAL = 'mechanical'    # 机械工程师
    TEST = 'test'                # 测试工程师
    ELECTRICAL = 'electrical'    # 电气工程师


class EngineerJobLevelEnum(str, Enum):
    """工程师职级"""
    JUNIOR = 'junior'            # 初级
    INTERMEDIATE = 'intermediate'  # 中级
    SENIOR = 'senior'            # 高级
    EXPERT = 'expert'            # 资深/专家


class ContributionTypeEnum(str, Enum):
    """知识贡献类型"""
    DOCUMENT = 'document'        # 技术文档
    TEMPLATE = 'template'        # 标准模板
    MODULE = 'module'            # 代码/功能模块
    TRAINING = 'training'        # 培训分享
    PATENT = 'patent'            # 专利
    STANDARD = 'standard'        # 标准规范


class ContributionStatusEnum(str, Enum):
    """知识贡献状态"""
    DRAFT = 'draft'              # 草稿
    PENDING = 'pending'          # 待审核
    APPROVED = 'approved'        # 已通过
    REJECTED = 'rejected'        # 已拒绝


class ReviewResultEnum(str, Enum):
    """评审结果"""
    PASSED = 'passed'            # 通过
    REJECTED = 'rejected'        # 驳回
    CONDITIONAL = 'conditional'  # 有条件通过


class IssueSeverityEnum(str, Enum):
    """问题严重程度"""
    CRITICAL = 'critical'        # 致命
    MAJOR = 'major'              # 严重
    NORMAL = 'normal'            # 一般
    MINOR = 'minor'              # 轻微


class IssueStatusEnum(str, Enum):
    """问题状态"""
    OPEN = 'open'                # 待处理
    IN_PROGRESS = 'in_progress'  # 处理中
    RESOLVED = 'resolved'        # 已解决
    CLOSED = 'closed'            # 已关闭


class BugFoundStageEnum(str, Enum):
    """Bug发现阶段"""
    INTERNAL_DEBUG = 'internal_debug'    # 内部调试
    SITE_DEBUG = 'site_debug'            # 现场调试
    ACCEPTANCE = 'acceptance'            # 客户验收
    PRODUCTION = 'production'            # 售后运行


class PlcBrandEnum(str, Enum):
    """PLC品牌"""
    SIEMENS = 'siemens'          # 西门子
    MITSUBISHI = 'mitsubishi'    # 三菱
    OMRON = 'omron'              # 欧姆龙
    BECKHOFF = 'beckhoff'        # 倍福
    INOVANCE = 'inovance'        # 汇川
    DELTA = 'delta'              # 台达


class DrawingTypeEnum(str, Enum):
    """电气图纸类型"""
    SCHEMATIC = 'schematic'      # 原理图
    LAYOUT = 'layout'            # 布局图
    WIRING = 'wiring'            # 接线图
    TERMINAL = 'terminal'        # 端子图
    PANEL = 'panel'              # 柜体图


class CodeModuleCategoryEnum(str, Enum):
    """代码模块分类"""
    COMMUNICATION = 'communication'  # 通讯模块
    DATA = 'data'                    # 数据处理
    UI = 'ui'                        # 界面组件
    DRIVER = 'driver'                # 硬件驱动
    UTILITY = 'utility'              # 工具类


class PlcModuleCategoryEnum(str, Enum):
    """PLC模块分类"""
    MOTION = 'motion'            # 运动控制
    IO = 'io'                    # IO处理
    COMMUNICATION = 'communication'  # 通讯
    DATA = 'data'                # 数据处理
    ALARM = 'alarm'              # 报警处理
    PROCESS = 'process'          # 工艺流程


# ==================== 工程师档案 ====================

class EngineerProfile(Base, TimestampMixin):
    """工程师档案 - 扩展用户信息"""
    __tablename__ = 'engineer_profile'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    user_id = Column(Integer, ForeignKey('users.id'), unique=True, nullable=False, comment='关联用户ID')

    # 岗位信息
    job_type = Column(String(20), nullable=False, comment='岗位类型')
    job_level = Column(String(20), default='junior', comment='职级')

    # 技能标签
    skills = Column(JSON, comment='技能标签')
    certifications = Column(JSON, comment='资质证书')

    # 时间信息
    job_start_date = Column(Date, comment='当前岗位开始日期')
    level_start_date = Column(Date, comment='当前级别开始日期')

    # 关系
    user = relationship('User', foreign_keys=[user_id], backref='engineer_profile')

    __table_args__ = (
        Index('idx_engineer_profile_job_type', 'job_type'),
        Index('idx_engineer_profile_job_level', 'job_level'),
        {'comment': '工程师档案表'}
    )


# ==================== 五维权重配置 ====================

class EngineerDimensionConfig(Base, TimestampMixin):
    """五维权重配置（只能按岗位+级别配置，不能针对个人）"""
    __tablename__ = 'engineer_dimension_config'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')

    # 配置维度
    job_type = Column(String(20), nullable=False, comment='岗位类型')
    job_level = Column(String(20), comment='职级（为空表示适用所有级别）')

    # 五维权重（百分比，总和100）
    technical_weight = Column(Integer, default=30, comment='技术能力权重')
    execution_weight = Column(Integer, default=25, comment='项目执行权重')
    cost_quality_weight = Column(Integer, default=20, comment='成本/质量权重')
    knowledge_weight = Column(Integer, default=15, comment='知识沉淀权重')
    collaboration_weight = Column(Integer, default=10, comment='团队协作权重')

    # 生效时间
    effective_date = Column(Date, nullable=False, comment='生效日期')
    expired_date = Column(Date, comment='失效日期')

    # 配置信息
    config_name = Column(String(100), comment='配置名称')
    description = Column(Text, comment='配置说明')
    operator_id = Column(Integer, ForeignKey('users.id'), comment='操作人ID')

    __table_args__ = (
        Index('idx_dimension_config_job_type', 'job_type'),
        Index('idx_dimension_config_effective', 'effective_date'),
        {'comment': '五维权重配置表'}
    )


# ==================== 跨部门协作评价 ====================

class CollaborationRating(Base, TimestampMixin):
    """跨部门协作评价"""
    __tablename__ = 'collaboration_rating'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    period_id = Column(Integer, ForeignKey('performance_period.id'), nullable=False, comment='考核周期ID')

    # 评价双方
    rater_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='评价人ID')
    ratee_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='被评价人ID')
    rater_job_type = Column(String(20), comment='评价人岗位类型')
    ratee_job_type = Column(String(20), comment='被评价人岗位类型')

    # 四维评分（1-5分）
    communication_score = Column(Integer, comment='沟通配合')
    response_score = Column(Integer, comment='响应速度')
    delivery_score = Column(Integer, comment='交付质量')
    interface_score = Column(Integer, comment='接口规范')

    # 总分
    total_score = Column(Numeric(4, 2), comment='总分')

    # 评价备注
    comment = Column(Text, comment='评价备注')

    # 项目关联
    project_id = Column(Integer, ForeignKey('projects.id'), comment='关联项目ID')

    # 关系
    rater = relationship('User', foreign_keys=[rater_id])
    ratee = relationship('User', foreign_keys=[ratee_id])
    period = relationship('PerformancePeriod', foreign_keys=[period_id])

    __table_args__ = (
        Index('idx_collab_rating_period', 'period_id'),
        Index('idx_collab_rating_rater', 'rater_id'),
        Index('idx_collab_rating_ratee', 'ratee_id'),
        {'comment': '跨部门协作评价表'}
    )


# ==================== 知识贡献 ====================

class KnowledgeContribution(Base, TimestampMixin):
    """知识贡献记录"""
    __tablename__ = 'knowledge_contribution'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    contributor_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='贡献者ID')

    # 贡献类型
    contribution_type = Column(String(30), nullable=False, comment='贡献类型')
    job_type = Column(String(20), comment='所属岗位领域')

    # 贡献内容
    title = Column(String(200), nullable=False, comment='标题')
    description = Column(Text, comment='描述')
    file_path = Column(String(500), comment='文件路径')
    tags = Column(JSON, comment='标签')

    # 复用统计
    reuse_count = Column(Integer, default=0, comment='复用次数')
    rating_score = Column(Numeric(3, 2), comment='平均评分')
    rating_count = Column(Integer, default=0, comment='评分次数')

    # 审核状态
    status = Column(String(20), default='draft', comment='状态')
    approved_by = Column(Integer, ForeignKey('users.id'), comment='审核人ID')
    approved_at = Column(DateTime, comment='审核时间')

    # 关系
    contributor = relationship('User', foreign_keys=[contributor_id])

    __table_args__ = (
        Index('idx_knowledge_contrib_user', 'contributor_id'),
        Index('idx_knowledge_contrib_type', 'contribution_type'),
        Index('idx_knowledge_contrib_status', 'status'),
        {'comment': '知识贡献记录表'}
    )


class KnowledgeReuseLog(Base):
    """知识复用记录"""
    __tablename__ = 'knowledge_reuse_log'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    contribution_id = Column(Integer, ForeignKey('knowledge_contribution.id'), nullable=False, comment='贡献ID')
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='使用者ID')
    project_id = Column(Integer, ForeignKey('projects.id'), comment='关联项目ID')

    # 复用信息
    reuse_type = Column(String(30), comment='复用类型')
    rating = Column(Integer, comment='评分')
    feedback = Column(Text, comment='反馈')

    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

    # 关系
    contribution = relationship('KnowledgeContribution', foreign_keys=[contribution_id])
    user = relationship('User', foreign_keys=[user_id])

    __table_args__ = (
        Index('idx_knowledge_reuse_contrib', 'contribution_id'),
        Index('idx_knowledge_reuse_user', 'user_id'),
        {'comment': '知识复用记录表'}
    )


# ==================== 机械工程师专属表 ====================

class DesignReview(Base, TimestampMixin):
    """设计评审记录（机械工程师）"""
    __tablename__ = 'design_review'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    project_id = Column(Integer, ForeignKey('projects.id'), comment='项目ID')
    designer_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='设计者ID')

    # 设计信息
    design_name = Column(String(200), nullable=False, comment='设计名称')
    design_type = Column(String(50), comment='设计类型')
    design_code = Column(String(50), comment='设计编号')
    version = Column(String(20), comment='版本号')

    # 评审信息
    review_date = Column(Date, comment='评审日期')
    reviewer_id = Column(Integer, ForeignKey('users.id'), comment='评审人ID')
    result = Column(String(20), comment='评审结果')
    is_first_pass = Column(Boolean, comment='是否一次通过')
    issues_found = Column(Integer, default=0, comment='发现问题数')
    review_comments = Column(Text, comment='评审意见')

    # 附件
    attachments = Column(JSON, comment='附件')

    # 关系
    designer = relationship('User', foreign_keys=[designer_id])
    reviewer = relationship('User', foreign_keys=[reviewer_id])
    project = relationship('Project', foreign_keys=[project_id])

    __table_args__ = (
        Index('idx_design_review_project', 'project_id'),
        Index('idx_design_review_designer', 'designer_id'),
        Index('idx_design_review_date', 'review_date'),
        {'comment': '设计评审记录表'}
    )


class MechanicalDebugIssue(Base, TimestampMixin):
    """机械调试问题记录"""
    __tablename__ = 'mechanical_debug_issue'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    project_id = Column(Integer, ForeignKey('projects.id'), comment='项目ID')
    responsible_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='责任人ID')
    reporter_id = Column(Integer, ForeignKey('users.id'), comment='报告人ID')

    # 问题信息
    issue_code = Column(String(50), comment='问题编号')
    issue_description = Column(Text, nullable=False, comment='问题描述')
    severity = Column(String(20), comment='严重程度')
    root_cause = Column(String(50), comment='根本原因')
    affected_part = Column(String(200), comment='受影响零件')

    # 处理状态
    status = Column(String(20), default='open', comment='状态')
    found_date = Column(Date, comment='发现日期')
    resolved_date = Column(Date, comment='解决日期')
    resolution = Column(Text, comment='解决方案')

    # 影响评估
    cost_impact = Column(Numeric(12, 2), comment='成本影响')
    time_impact_hours = Column(Numeric(6, 2), comment='时间影响(小时)')

    # 关系
    responsible = relationship('User', foreign_keys=[responsible_id])
    reporter = relationship('User', foreign_keys=[reporter_id])
    project = relationship('Project', foreign_keys=[project_id])

    __table_args__ = (
        Index('idx_mech_debug_project', 'project_id'),
        Index('idx_mech_debug_responsible', 'responsible_id'),
        Index('idx_mech_debug_severity', 'severity'),
        {'comment': '机械调试问题记录表'}
    )


class DesignReuseRecord(Base, TimestampMixin):
    """设计复用记录"""
    __tablename__ = 'design_reuse_record'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    project_id = Column(Integer, ForeignKey('projects.id'), comment='目标项目ID')
    designer_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='设计者ID')

    # 复用信息
    source_design_id = Column(Integer, comment='源设计ID')
    source_design_name = Column(String(200), comment='源设计名称')
    source_project_id = Column(Integer, ForeignKey('projects.id'), comment='源项目ID')

    # 复用程度
    reuse_type = Column(String(30), comment='复用类型')
    reuse_percentage = Column(Numeric(5, 2), comment='复用比例')

    # 节省评估
    saved_hours = Column(Numeric(6, 2), comment='节省工时')

    # 关系
    designer = relationship('User', foreign_keys=[designer_id])
    project = relationship('Project', foreign_keys=[project_id])

    __table_args__ = (
        Index('idx_design_reuse_project', 'project_id'),
        Index('idx_design_reuse_designer', 'designer_id'),
        {'comment': '设计复用记录表'}
    )


# ==================== 测试工程师专属表 ====================

class TestBugRecord(Base, TimestampMixin):
    """测试Bug记录"""
    __tablename__ = 'test_bug_record'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    project_id = Column(Integer, ForeignKey('projects.id'), comment='项目ID')
    reporter_id = Column(Integer, ForeignKey('users.id'), comment='报告人ID')
    assignee_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='处理人ID')

    # Bug信息
    bug_code = Column(String(50), comment='Bug编号')
    title = Column(String(200), nullable=False, comment='标题')
    description = Column(Text, comment='描述')
    severity = Column(String(20), comment='严重程度')
    bug_type = Column(String(30), comment='Bug类型')
    found_stage = Column(String(30), comment='发现阶段')

    # 处理信息
    status = Column(String(20), default='open', comment='状态')
    priority = Column(String(20), default='normal', comment='优先级')
    found_time = Column(DateTime, comment='发现时间')
    resolved_time = Column(DateTime, comment='解决时间')
    fix_duration_hours = Column(Numeric(6, 2), comment='修复时长(小时)')
    resolution = Column(Text, comment='解决方案')

    # 附件
    attachments = Column(JSON, comment='附件')

    # 关系
    reporter = relationship('User', foreign_keys=[reporter_id])
    assignee = relationship('User', foreign_keys=[assignee_id])
    project = relationship('Project', foreign_keys=[project_id])

    __table_args__ = (
        Index('idx_test_bug_project', 'project_id'),
        Index('idx_test_bug_assignee', 'assignee_id'),
        Index('idx_test_bug_severity', 'severity'),
        Index('idx_test_bug_status', 'status'),
        {'comment': '测试Bug记录表'}
    )


class CodeReviewRecord(Base, TimestampMixin):
    """代码评审记录"""
    __tablename__ = 'code_review_record'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    project_id = Column(Integer, ForeignKey('projects.id'), comment='项目ID')
    author_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='作者ID')
    reviewer_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='评审人ID')

    # 评审信息
    review_title = Column(String(200), comment='评审标题')
    code_module = Column(String(100), comment='代码模块')
    language = Column(String(30), comment='编程语言')
    lines_changed = Column(Integer, comment='修改行数')

    # 评审结果
    review_date = Column(Date, comment='评审日期')
    result = Column(String(20), comment='评审结果')
    is_first_pass = Column(Boolean, comment='是否一次通过')
    issues_found = Column(Integer, default=0, comment='发现问题数')
    comments = Column(Text, comment='评审意见')

    # 关系
    author = relationship('User', foreign_keys=[author_id])
    reviewer = relationship('User', foreign_keys=[reviewer_id])
    project = relationship('Project', foreign_keys=[project_id])

    __table_args__ = (
        Index('idx_code_review_project', 'project_id'),
        Index('idx_code_review_author', 'author_id'),
        Index('idx_code_review_reviewer', 'reviewer_id'),
        {'comment': '代码评审记录表'}
    )


class CodeModule(Base, TimestampMixin):
    """代码模块库"""
    __tablename__ = 'code_module'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    contributor_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='贡献者ID')

    # 模块信息
    module_name = Column(String(100), nullable=False, comment='模块名称')
    module_code = Column(String(50), comment='模块编号')
    category = Column(String(50), comment='分类')
    language = Column(String(30), comment='编程语言')
    description = Column(Text, comment='描述')

    # 版本信息
    version = Column(String(20), comment='版本')
    repository_url = Column(String(500), comment='仓库地址')

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
        Index('idx_code_module_contributor', 'contributor_id'),
        Index('idx_code_module_category', 'category'),
        Index('idx_code_module_language', 'language'),
        {'comment': '代码模块库表'}
    )


# ==================== 电气工程师专属表 ====================

class ElectricalDrawingVersion(Base, TimestampMixin):
    """电气图纸版本"""
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
    """元器件选型记录"""
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
    """电气故障记录"""
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
