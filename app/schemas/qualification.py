# -*- coding: utf-8 -*-
"""
任职资格体系 Schema
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .common import PageParams, PaginatedResponse, ResponseModel

# ==================== 任职资格等级 ====================

class QualificationLevelBase(BaseModel):
    """任职资格等级基础模型"""
    level_code: str = Field(..., description="等级编码 (ASSISTANT/JUNIOR/MIDDLE/SENIOR/EXPERT)")
    level_name: str = Field(..., description="等级名称")
    level_order: int = Field(..., description="排序顺序")
    role_type: Optional[str] = Field(None, description="适用角色类型")
    description: Optional[str] = Field(None, description="等级描述")
    is_active: bool = Field(True, description="是否启用")


class QualificationLevelCreate(QualificationLevelBase):
    """创建任职资格等级"""
    pass


class QualificationLevelUpdate(BaseModel):
    """更新任职资格等级"""
    level_name: Optional[str] = None
    level_order: Optional[int] = None
    role_type: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class QualificationLevelResponse(QualificationLevelBase):
    """任职资格等级响应"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class QualificationLevelListResponse(PaginatedResponse[QualificationLevelResponse]):
    """任职资格等级列表响应"""
    pass


# ==================== 岗位能力模型 ====================

class CompetencyDimensionItem(BaseModel):
    """能力维度项"""
    name: str = Field(..., description="能力项名称")
    description: Optional[str] = Field(None, description="能力项描述")
    score_range: List[int] = Field(..., description="得分范围 [min, max]")
    weight: Optional[float] = Field(None, description="权重")


class CompetencyDimension(BaseModel):
    """能力维度"""
    name: str = Field(..., description="维度名称")
    weight: float = Field(..., description="维度权重")
    items: List[CompetencyDimensionItem] = Field(..., description="能力项列表")


class PositionCompetencyModelBase(BaseModel):
    """岗位能力模型基础模型"""
    position_type: str = Field(..., description="岗位类型")
    position_subtype: Optional[str] = Field(None, description="岗位子类型")
    level_id: int = Field(..., description="等级ID")
    competency_dimensions: Dict[str, Any] = Field(..., description="能力维度要求 (JSON)")


class PositionCompetencyModelCreate(PositionCompetencyModelBase):
    """创建岗位能力模型"""
    pass


class PositionCompetencyModelUpdate(BaseModel):
    """更新岗位能力模型"""
    position_subtype: Optional[str] = None
    level_id: Optional[int] = None
    competency_dimensions: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class PositionCompetencyModelResponse(PositionCompetencyModelBase):
    """岗位能力模型响应"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    level: Optional[QualificationLevelResponse] = None

    class Config:
        from_attributes = True


class PositionCompetencyModelListResponse(PaginatedResponse[PositionCompetencyModelResponse]):
    """岗位能力模型列表响应"""
    pass


# ==================== 员工任职资格 ====================

class EmployeeQualificationBase(BaseModel):
    """员工任职资格基础模型"""
    employee_id: int = Field(..., description="员工ID")
    position_type: str = Field(..., description="岗位类型")
    current_level_id: int = Field(..., description="当前等级ID")
    certified_date: Optional[date] = Field(None, description="认证日期")
    certifier_id: Optional[int] = Field(None, description="认证人ID")
    status: str = Field("PENDING", description="认证状态")
    assessment_details: Optional[Dict[str, Any]] = Field(None, description="能力评估详情")
    valid_until: Optional[date] = Field(None, description="有效期至")


class EmployeeQualificationCreate(BaseModel):
    """创建员工任职资格"""
    employee_id: int
    position_type: str
    current_level_id: int
    assessment_details: Optional[Dict[str, Any]] = None
    certified_date: Optional[date] = None
    valid_until: Optional[date] = None


class EmployeeQualificationUpdate(BaseModel):
    """更新员工任职资格"""
    current_level_id: Optional[int] = None
    status: Optional[str] = None
    assessment_details: Optional[Dict[str, Any]] = None
    valid_until: Optional[date] = None


class EmployeeQualificationResponse(EmployeeQualificationBase):
    """员工任职资格响应"""
    id: int
    created_at: datetime
    updated_at: datetime
    level: Optional[QualificationLevelResponse] = None

    class Config:
        from_attributes = True


class EmployeeQualificationListResponse(PaginatedResponse[EmployeeQualificationResponse]):
    """员工任职资格列表响应"""
    pass


class EmployeeQualificationCertifyRequest(BaseModel):
    """员工任职资格认证请求"""
    position_type: str = Field(..., description="岗位类型")
    level_id: int = Field(..., description="等级ID")
    assessment_details: Dict[str, Any] = Field(..., description="评估详情")
    certified_date: Optional[date] = Field(None, description="认证日期")
    valid_until: Optional[date] = Field(None, description="有效期至")


class EmployeeQualificationPromoteRequest(BaseModel):
    """员工晋升评估请求"""
    target_level_id: int = Field(..., description="目标等级ID")
    assessment_details: Dict[str, Any] = Field(..., description="评估详情")
    assessment_period: Optional[str] = Field(None, description="评估周期")


# ==================== 任职资格评估 ====================

class QualificationAssessmentBase(BaseModel):
    """任职资格评估基础模型"""
    employee_id: int = Field(..., description="员工ID")
    qualification_id: Optional[int] = Field(None, description="任职资格ID")
    assessment_period: Optional[str] = Field(None, description="评估周期")
    assessment_type: str = Field(..., description="评估类型")
    scores: Dict[str, Any] = Field(..., description="各维度得分")
    total_score: Optional[Decimal] = Field(None, description="综合得分")
    result: Optional[str] = Field(None, description="评估结果")
    assessor_id: Optional[int] = Field(None, description="评估人ID")
    comments: Optional[str] = Field(None, description="评估意见")


class QualificationAssessmentCreate(BaseModel):
    """创建任职资格评估"""
    employee_id: int
    qualification_id: Optional[int] = None
    assessment_period: Optional[str] = None
    assessment_type: str
    scores: Dict[str, Any]
    assessor_id: Optional[int] = None
    comments: Optional[str] = None


class QualificationAssessmentUpdate(BaseModel):
    """更新任职资格评估"""
    scores: Optional[Dict[str, Any]] = None
    total_score: Optional[Decimal] = None
    result: Optional[str] = None
    comments: Optional[str] = None


class QualificationAssessmentResponse(QualificationAssessmentBase):
    """任职资格评估响应"""
    id: int
    assessed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class QualificationAssessmentListResponse(PaginatedResponse[QualificationAssessmentResponse]):
    """任职资格评估列表响应"""
    pass


class QualificationAssessmentSubmitRequest(BaseModel):
    """提交评估结果请求"""
    total_score: Decimal = Field(..., description="综合得分")
    result: str = Field(..., description="评估结果")
    comments: Optional[str] = Field(None, description="评估意见")


# ==================== 查询参数 ====================

class QualificationLevelQuery(PageParams):
    """任职资格等级查询参数"""
    role_type: Optional[str] = Field(None, description="角色类型")
    is_active: Optional[bool] = Field(None, description="是否启用")


class PositionCompetencyModelQuery(PageParams):
    """岗位能力模型查询参数"""
    position_type: Optional[str] = Field(None, description="岗位类型")
    position_subtype: Optional[str] = Field(None, description="岗位子类型")
    level_id: Optional[int] = Field(None, description="等级ID")
    is_active: Optional[bool] = Field(None, description="是否启用")


class EmployeeQualificationQuery(PageParams):
    """员工任职资格查询参数"""
    employee_id: Optional[int] = Field(None, description="员工ID")
    position_type: Optional[str] = Field(None, description="岗位类型")
    level_id: Optional[int] = Field(None, description="等级ID")
    status: Optional[str] = Field(None, description="认证状态")


class QualificationAssessmentQuery(PageParams):
    """任职资格评估查询参数"""
    employee_id: Optional[int] = Field(None, description="员工ID")
    qualification_id: Optional[int] = Field(None, description="任职资格ID")
    assessment_type: Optional[str] = Field(None, description="评估类型")
    assessment_period: Optional[str] = Field(None, description="评估周期")
    result: Optional[str] = Field(None, description="评估结果")

