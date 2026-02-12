# -*- coding: utf-8 -*-
"""
技术评审管理模块 Schema
"""

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from .common import BaseSchema, TimestampSchema

# ==================== 评审主表 ====================

class TechnicalReviewCreate(BaseModel):
    """创建技术评审"""

    review_type: str = Field(..., description="评审类型：PDR/DDR/PRR/FRR/ARR")
    review_name: str = Field(..., max_length=200, description="评审名称")
    project_id: int = Field(..., description="关联项目ID")
    equipment_id: Optional[int] = Field(default=None, description="关联设备ID（多设备项目）")

    scheduled_date: datetime = Field(..., description="计划评审时间")
    location: Optional[str] = Field(default=None, max_length=200, description="评审地点")
    meeting_type: str = Field(default="ONSITE", description="会议形式：onsite/online/hybrid")

    host_id: int = Field(..., description="主持人ID")
    presenter_id: int = Field(..., description="汇报人ID")
    recorder_id: int = Field(..., description="记录人ID")

    class Config:
        from_attributes = True


class TechnicalReviewUpdate(BaseModel):
    """更新技术评审"""

    review_name: Optional[str] = Field(default=None, max_length=200, description="评审名称")
    scheduled_date: Optional[datetime] = Field(default=None, description="计划评审时间")
    actual_date: Optional[datetime] = Field(default=None, description="实际评审时间")
    location: Optional[str] = Field(default=None, max_length=200, description="评审地点")
    meeting_type: Optional[str] = Field(default=None, description="会议形式")
    status: Optional[str] = Field(default=None, description="状态")

    host_id: Optional[int] = Field(default=None, description="主持人ID")
    presenter_id: Optional[int] = Field(default=None, description="汇报人ID")
    recorder_id: Optional[int] = Field(default=None, description="记录人ID")

    conclusion: Optional[str] = Field(default=None, description="评审结论")
    conclusion_summary: Optional[str] = Field(default=None, description="结论说明")
    condition_deadline: Optional[date] = Field(default=None, description="有条件通过的整改期限")
    next_review_date: Optional[date] = Field(default=None, description="下次复审日期")

    class Config:
        from_attributes = True


class TechnicalReviewResponse(TimestampSchema):
    """技术评审响应"""

    id: int
    review_no: str
    review_type: str
    review_name: str
    project_id: int
    project_no: str
    equipment_id: Optional[int] = None

    status: str
    scheduled_date: datetime
    actual_date: Optional[datetime] = None
    location: Optional[str] = None
    meeting_type: str

    host_id: int
    presenter_id: int
    recorder_id: int

    conclusion: Optional[str] = None
    conclusion_summary: Optional[str] = None
    condition_deadline: Optional[date] = None
    next_review_date: Optional[date] = None

    issue_count_a: int = 0
    issue_count_b: int = 0
    issue_count_c: int = 0
    issue_count_d: int = 0

    created_by: int

    class Config:
        from_attributes = True


# ==================== 评审参与人 ====================

class ReviewParticipantCreate(BaseModel):
    """创建评审参与人"""

    review_id: int = Field(..., description="评审ID")
    user_id: int = Field(..., description="用户ID")
    role: str = Field(..., description="角色：host/expert/presenter/recorder/observer")
    is_required: bool = Field(default=True, description="是否必须参与")

    class Config:
        from_attributes = True


class ReviewParticipantUpdate(BaseModel):
    """更新评审参与人"""

    attendance: Optional[str] = Field(default=None, description="出席状态")
    delegate_id: Optional[int] = Field(default=None, description="代理人ID")
    sign_time: Optional[datetime] = Field(default=None, description="签到时间")
    signature: Optional[str] = Field(default=None, max_length=500, description="电子签名")

    class Config:
        from_attributes = True


class ReviewParticipantResponse(BaseSchema):
    """评审参与人响应"""

    id: int
    review_id: int
    user_id: int
    role: str
    is_required: bool
    attendance: Optional[str] = None
    delegate_id: Optional[int] = None
    sign_time: Optional[datetime] = None
    signature: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== 评审材料 ====================

class ReviewMaterialCreate(BaseModel):
    """创建评审材料"""

    review_id: int = Field(..., description="评审ID")
    material_type: str = Field(..., description="材料类型：drawing/bom/report/document/other")
    material_name: str = Field(..., max_length=200, description="材料名称")
    file_path: str = Field(..., max_length=500, description="文件路径")
    file_size: int = Field(..., description="文件大小（字节）")
    version: Optional[str] = Field(default=None, max_length=20, description="版本号")
    is_required: bool = Field(default=True, description="是否必须材料")

    class Config:
        from_attributes = True


class ReviewMaterialResponse(TimestampSchema):
    """评审材料响应"""

    id: int
    review_id: int
    material_type: str
    material_name: str
    file_path: str
    file_size: int
    version: Optional[str] = None
    is_required: bool
    upload_by: int
    upload_at: datetime

    class Config:
        from_attributes = True


# ==================== 评审检查项记录 ====================

class ReviewChecklistRecordCreate(BaseModel):
    """创建评审检查项记录"""

    review_id: int = Field(..., description="评审ID")
    checklist_item_id: Optional[int] = Field(default=None, description="检查项ID（关联模板）")
    category: str = Field(..., max_length=50, description="检查类别")
    check_item: str = Field(..., max_length=500, description="检查项内容")
    result: str = Field(..., description="检查结果：pass/fail/na")

    issue_level: Optional[str] = Field(default=None, description="问题等级：A/B/C/D（不通过时）")
    issue_desc: Optional[str] = Field(default=None, description="问题描述")

    checker_id: int = Field(..., description="检查人ID")
    remark: Optional[str] = Field(default=None, max_length=500, description="备注")

    class Config:
        from_attributes = True


class ReviewChecklistRecordUpdate(BaseModel):
    """更新评审检查项记录"""

    result: Optional[str] = Field(default=None, description="检查结果")
    issue_level: Optional[str] = Field(default=None, description="问题等级")
    issue_desc: Optional[str] = Field(default=None, description="问题描述")
    issue_id: Optional[int] = Field(default=None, description="关联问题ID")
    remark: Optional[str] = Field(default=None, max_length=500, description="备注")

    class Config:
        from_attributes = True


class ReviewChecklistRecordResponse(BaseSchema):
    """评审检查项记录响应"""

    id: int
    review_id: int
    checklist_item_id: Optional[int] = None
    category: str
    check_item: str
    result: str
    issue_level: Optional[str] = None
    issue_desc: Optional[str] = None
    issue_id: Optional[int] = None
    checker_id: int
    remark: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== 评审问题 ====================

class ReviewIssueCreate(BaseModel):
    """创建评审问题"""

    review_id: int = Field(..., description="评审ID")
    issue_level: str = Field(..., description="问题等级：A/B/C/D")
    category: str = Field(..., max_length=50, description="问题类别")
    description: str = Field(..., description="问题描述")
    suggestion: Optional[str] = Field(default=None, description="改进建议")

    assignee_id: int = Field(..., description="责任人ID")
    deadline: date = Field(..., description="整改期限")

    class Config:
        from_attributes = True


class ReviewIssueUpdate(BaseModel):
    """更新评审问题"""

    status: Optional[str] = Field(default=None, description="状态")
    solution: Optional[str] = Field(default=None, description="解决方案")
    verify_result: Optional[str] = Field(default=None, description="验证结果")
    verifier_id: Optional[int] = Field(default=None, description="验证人")
    verify_time: Optional[datetime] = Field(default=None, description="验证时间")
    linked_issue_id: Optional[int] = Field(default=None, description="关联问题管理系统ID")

    class Config:
        from_attributes = True


class ReviewIssueResponse(TimestampSchema):
    """评审问题响应"""

    id: int
    review_id: int
    issue_no: str
    issue_level: str
    category: str
    description: str
    suggestion: Optional[str] = None

    assignee_id: int
    deadline: date

    status: str
    solution: Optional[str] = None

    verify_result: Optional[str] = None
    verifier_id: Optional[int] = None
    verify_time: Optional[datetime] = None

    linked_issue_id: Optional[int] = None

    class Config:
        from_attributes = True


# ==================== 评审详情（包含关联数据） ====================

class TechnicalReviewDetailResponse(TechnicalReviewResponse):
    """技术评审详情响应（包含关联数据）"""

    participants: List[ReviewParticipantResponse] = []
    materials: List[ReviewMaterialResponse] = []
    checklist_records: List[ReviewChecklistRecordResponse] = []
    issues: List[ReviewIssueResponse] = []

    class Config:
        from_attributes = True






