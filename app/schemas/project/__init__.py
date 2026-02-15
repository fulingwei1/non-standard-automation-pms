# -*- coding: utf-8 -*-
"""
项目管理 Schema 模块

此模块将原始的 project.py 拆分为多个子模块以提高可维护性：
- customer.py: 客户管理相关 Schema
- project_core.py: 项目核心管理 Schema
- machine.py: 设备管理 Schema
- milestone.py: 里程碑管理 Schema
- project_config.py: 项目配置 Schema（阶段、状态、模板）
- project_cost.py: 项目成本和收款 Schema
- project_analysis.py: 项目分析和管理 Schema

为了保持向后兼容性，所有 Schema 类都在此处重新导出。
"""

# 从各子模块导入所有 Schema 类
from .customer import (
    Customer360CommunicationItem,
    Customer360ContractItem,
    Customer360InvoiceItem,
    Customer360OpportunityItem,
    Customer360PaymentPlanItem,
    Customer360ProjectItem,
    Customer360QuoteItem,
    Customer360Response,
    Customer360Summary,
    CustomerCreate,
    CustomerResponse,
    CustomerUpdate,
)
from .machine import (
    MachineCreate,
    MachineResponse,
    MachineUpdate,
)
from .milestone import (
    MilestoneCreate,
    MilestoneResponse,
    MilestoneUpdate,
)
from .project_analysis import (
    BatchArchiveRequest,
    BatchAssignPMRequest,
    BatchOperationResponse,
    BatchUpdateStageRequest,
    BatchUpdateStatusRequest,
    ChangeImpactRequest,
    ChangeImpactResponse,
    GateCheckCondition,
    GateCheckResult,
    InProductionProjectSummary,
    ProjectArchiveRequest,
    ProjectCloneRequest,
    ProjectDashboardResponse,
    ProjectHealthDetailsResponse,
    ProjectRelationResponse,
    ProjectStatusLogResponse,
    ProjectStatusResponse,
    ProjectSummaryResponse,
    ProjectTimelineResponse,
    ResourceConflictResponse,
    ResourceOptimizationResponse,
    RiskMatrixResponse,
    StageAdvanceRequest,
    StageAdvanceResponse,
    TimelineEvent,
)
from .project_config import (
    ProjectStageCreate,
    ProjectStageResponse,
    ProjectStageUpdate,
    ProjectStatusCreate,
    ProjectTemplateCreate,
    ProjectTemplateResponse,
    ProjectTemplateUpdate,
    ProjectTemplateVersionCreate,
    ProjectTemplateVersionResponse,
    ProjectTemplateVersionUpdate,
)
from .project_core import (
    ProjectCreate,
    ProjectDetailResponse,
    ProjectDocumentCreate,
    ProjectDocumentResponse,
    ProjectDocumentUpdate,
    ProjectListResponse,
    ProjectMemberCreate,
    ProjectMemberResponse,
    ProjectMemberUpdate,
    ProjectResponse,
    ProjectUpdate,
)
from .project_cost import (
    FinancialProjectCostCreate,
    FinancialProjectCostResponse,
    FinancialProjectCostUploadRequest,
    ProjectCostBreakdown,
    ProjectCostCreate,
    ProjectCostResponse,
    ProjectCostSummary,
    ProjectCostUpdate,
    ProjectPaymentPlanCreate,
    ProjectPaymentPlanResponse,
    ProjectPaymentPlanUpdate,
)

# 导出所有公共类，使其可以通过 `from app.schemas.project import *` 导入
__all__ = [
    # Customer
    "CustomerCreate",
    "CustomerUpdate",
    "CustomerResponse",
    "Customer360Summary",
    "Customer360ProjectItem",
    "Customer360OpportunityItem",
    "Customer360QuoteItem",
    "Customer360ContractItem",
    "Customer360InvoiceItem",
    "Customer360PaymentPlanItem",
    "Customer360CommunicationItem",
    "Customer360Response",
    # Project Core
    "ProjectCreate",
    "ProjectUpdate",
    "ProjectResponse",
    "ProjectListResponse",
    "ProjectDetailResponse",
    "ProjectMemberCreate",
    "ProjectMemberUpdate",
    "ProjectMemberResponse",
    "ProjectDocumentCreate",
    "ProjectDocumentUpdate",
    "ProjectDocumentResponse",
    # Machine
    "MachineCreate",
    "MachineUpdate",
    "MachineResponse",
    # Milestone
    "MilestoneCreate",
    "MilestoneUpdate",
    "MilestoneResponse",
    # Project Config
    "ProjectStageCreate",
    "ProjectStageUpdate",
    "ProjectStageResponse",
    "ProjectStatusCreate",
    "ProjectStatusResponse",
    "ProjectTemplateCreate",
    "ProjectTemplateUpdate",
    "ProjectTemplateResponse",
    "ProjectTemplateVersionCreate",
    "ProjectTemplateVersionUpdate",
    "ProjectTemplateVersionResponse",
    # Project Cost
    "ProjectCostCreate",
    "ProjectCostUpdate",
    "ProjectCostResponse",
    "ProjectCostSummary",
    "ProjectCostBreakdown",
    "FinancialProjectCostCreate",
    "FinancialProjectCostResponse",
    "FinancialProjectCostUploadRequest",
    "ProjectPaymentPlanCreate",
    "ProjectPaymentPlanUpdate",
    "ProjectPaymentPlanResponse",
    # Project Analysis
    "ProjectHealthDetailsResponse",
    "ProjectStatusLogResponse",
    "ProjectCloneRequest",
    "ProjectArchiveRequest",
    "ResourceConflictResponse",
    "ResourceOptimizationResponse",
    "ProjectRelationResponse",
    "RiskMatrixResponse",
    "ChangeImpactRequest",
    "ChangeImpactResponse",
    "ProjectSummaryResponse",
    "TimelineEvent",
    "ProjectTimelineResponse",
    "StageAdvanceRequest",
    "GateCheckCondition",
    "GateCheckResult",
    "StageAdvanceResponse",
    "ProjectStatusResponse",
    "BatchUpdateStatusRequest",
    "BatchArchiveRequest",
    "BatchAssignPMRequest",
    "BatchUpdateStageRequest",
    "BatchOperationResponse",
    "ProjectDashboardResponse",
    "InProductionProjectSummary",
]

# 添加模块级别的文档字符串
__doc__ = """
项目管理 Schema 模块

此模块提供项目管理相关的所有 Pydantic Schema 类，包括：

客户管理：
- CustomerCreate, CustomerUpdate, CustomerResponse
- Customer360Response 及相关组件

项目核心：
- ProjectCreate, ProjectUpdate, ProjectResponse
- ProjectListResponse, ProjectDetailResponse
- ProjectMemberCreate, ProjectMemberUpdate, ProjectMemberResponse
- ProjectDocumentCreate, ProjectDocumentUpdate, ProjectDocumentResponse

设备管理：
- MachineCreate, MachineUpdate, MachineResponse

里程碑管理：
- MilestoneCreate, MilestoneUpdate, MilestoneResponse

项目配置：
- ProjectStageCreate, ProjectStageUpdate, ProjectStageResponse
- ProjectStatusCreate, ProjectStatusResponse
- ProjectTemplateCreate, ProjectTemplateUpdate, ProjectTemplateResponse
- ProjectTemplateVersionCreate, ProjectTemplateVersionUpdate, ProjectTemplateVersionResponse

项目成本：
- ProjectCostCreate, ProjectCostUpdate, ProjectCostResponse
- FinancialProjectCostCreate, FinancialProjectCostResponse, FinancialProjectCostUploadRequest
- ProjectPaymentPlanCreate, ProjectPaymentPlanUpdate, ProjectPaymentPlanResponse

项目分析：
- ProjectHealthDetailsResponse, ProjectStatusLogResponse
- ProjectCloneRequest, ProjectArchiveRequest
- ResourceConflictResponse, ResourceOptimizationResponse
- ProjectRelationResponse, RiskMatrixResponse
- ChangeImpactRequest, ChangeImpactResponse
- ProjectSummaryResponse, ProjectTimelineResponse
- StageAdvanceRequest, StageAdvanceResponse
- GateCheckCondition, GateCheckResult
- ProjectStatusResponse
- BatchUpdateStatusRequest, BatchArchiveRequest, BatchAssignPMRequest, BatchUpdateStageRequest
- BatchOperationResponse, ProjectDashboardResponse
- InProductionProjectSummary

使用示例：
```python
# 从项目模块导入特定 Schema
from app.schemas.project import ProjectCreate, ProjectResponse

# 从子模块导入（推荐用于大型项目）
from app.schemas.project.customer import CustomerCreate
from app.schemas.project.project_core import ProjectCreate
```
"""
