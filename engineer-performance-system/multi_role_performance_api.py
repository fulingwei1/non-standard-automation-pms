"""
多岗位工程师绩效管理平台 - 统一API接口实现
支持机械、测试、电气三类工程师的绩效评价

基于 FastAPI 框架
"""

from fastapi import FastAPI, Query, Path, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
import json

app = FastAPI(
    title="多岗位工程师绩效管理平台 API",
    description="支持机械、测试、电气三类工程师的统一绩效评价系统",
    version="1.0.0"
)


# ==================== 枚举定义 ====================

class JobType(str, Enum):
    mechanical = "mechanical"
    test = "test"
    electrical = "electrical"

class PeriodType(str, Enum):
    monthly = "monthly"
    quarterly = "quarterly"
    yearly = "yearly"

class Grade(str, Enum):
    S = "S"
    A = "A"
    B = "B"
    C = "C"
    D = "D"

class ContributionType(str, Enum):
    document = "document"
    template = "template"
    module = "module"
    training = "training"
    patent = "patent"
    standard = "standard"


# ==================== 通用响应模型 ====================

class APIResponse(BaseModel):
    code: int = 200
    message: str = "success"
    data: Optional[Any] = None


# ==================== 请求/响应模型 ====================

# --- 维度得分 ---
class DimensionScores(BaseModel):
    technical: float = Field(..., description="技术能力")
    execution: float = Field(..., description="项目执行")
    cost_quality: float = Field(..., description="成本/质量")
    knowledge: float = Field(..., description="知识沉淀")
    collaboration: float = Field(..., description="团队协作")


# --- 工程师基础信息 ---
class EngineerInfo(BaseModel):
    id: int
    name: str
    job_type: JobType
    job_type_name: str
    level: str
    department: str
    skills: List[str]
    join_date: Optional[date]


# --- 排名条目 ---
class RankingItem(BaseModel):
    rank: int
    engineer_id: int
    engineer_name: str
    job_type: JobType
    job_type_name: str
    department: str
    level: str
    scores: DimensionScores
    total_score: float
    grade: Grade
    grade_name: str
    trend: str
    score_change: Optional[float]


# --- 跨部门评价请求 ---
class CollaborationRatingRequest(BaseModel):
    rating_period: str = Field(..., description="评价周期，如 2024Q4")
    rated_engineer_id: int = Field(..., description="被评价人ID")
    communication_score: float = Field(..., ge=1, le=5, description="沟通配合(1-5)")
    response_score: float = Field(..., ge=1, le=5, description="响应速度(1-5)")
    quality_score: float = Field(..., ge=1, le=5, description="交付质量(1-5)")
    interface_score: float = Field(..., ge=1, le=5, description="接口规范(1-5)")
    comments: Optional[str] = None
    project_id: Optional[int] = None


# --- 知识贡献请求 ---
class KnowledgeContributionRequest(BaseModel):
    contribution_type: ContributionType
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    attachments: Optional[List[str]] = None


# --- 绩效计算请求 ---
class CalculateRequest(BaseModel):
    period_type: PeriodType
    period_value: str
    job_types: Optional[List[JobType]] = None
    engineer_ids: Optional[List[int]] = None


# --- 权重配置 ---
class DimensionWeight(BaseModel):
    code: str
    name: str
    weight: int


class MetricConfig(BaseModel):
    code: str
    name: str
    weight: int
    target: Optional[float] = None
    inverse: bool = False


class WeightConfig(BaseModel):
    job_type: JobType
    dimensions: List[DimensionWeight]
    metrics: Dict[str, List[MetricConfig]]


# ==================== 辅助函数 ====================

def get_job_type_name(job_type: JobType) -> str:
    names = {
        JobType.mechanical: "机械工程师",
        JobType.test: "测试工程师",
        JobType.electrical: "电气工程师"
    }
    return names.get(job_type, str(job_type))


def get_grade_name(grade: Grade) -> str:
    names = {
        Grade.S: "优秀",
        Grade.A: "良好",
        Grade.B: "合格",
        Grade.C: "待改进",
        Grade.D: "不合格"
    }
    return names.get(grade, str(grade))


def calculate_grade(score: float) -> Grade:
    if score >= 85:
        return Grade.S
    elif score >= 70:
        return Grade.A
    elif score >= 60:
        return Grade.B
    elif score >= 40:
        return Grade.C
    else:
        return Grade.D


# ==================== API 接口实现 ====================

# -------------------- 综合概览 --------------------

@app.get("/api/v1/performance/summary/company",
         response_model=APIResponse,
         summary="公司整体绩效概览",
         tags=["综合概览"])
async def get_company_summary(
    period_type: PeriodType = Query(...),
    period_value: str = Query(...)
):
    """
    获取公司整体绩效概览，包括：
    - 各岗位人数和平均分
    - 等级分布
    - 各维度对比
    - 月度趋势
    """
    data = {
        "period": {
            "type": period_type.value,
            "value": period_value,
            "start_date": "2024-11-01",
            "end_date": "2024-11-30"
        },
        "overview": {
            "total_engineers": 80,
            "avg_score": 81.5,
            "score_change": 1.2,
            "by_job_type": [
                {"job_type": "mechanical", "job_type_name": "机械工程师", "count": 35, "avg_score": 82.1},
                {"job_type": "test", "job_type_name": "测试工程师", "count": 15, "avg_score": 83.2},
                {"job_type": "electrical", "job_type_name": "电气工程师", "count": 30, "avg_score": 80.5}
            ],
            "grade_distribution": [
                {"grade": "S", "grade_name": "优秀", "count": 15, "percentage": 18.75},
                {"grade": "A", "grade_name": "良好", "count": 35, "percentage": 43.75},
                {"grade": "B", "grade_name": "合格", "count": 25, "percentage": 31.25},
                {"grade": "C", "grade_name": "待改进", "count": 5, "percentage": 6.25}
            ]
        },
        "dimension_comparison": {
            "mechanical": {"technical": 84, "execution": 82, "cost_quality": 80, "knowledge": 75, "collaboration": 85},
            "test": {"technical": 86, "execution": 84, "cost_quality": 82, "knowledge": 78, "collaboration": 88},
            "electrical": {"technical": 83, "execution": 80, "cost_quality": 78, "knowledge": 72, "collaboration": 84}
        },
        "key_metrics_by_job_type": {
            "mechanical": {
                "first_pass_rate": {"value": 87, "target": 85, "status": "good"},
                "ecn_responsibility_rate": {"value": 8, "target": 10, "status": "good"},
                "standard_parts_rate": {"value": 65, "target": 60, "status": "good"}
            },
            "test": {
                "program_first_pass_rate": {"value": 82, "target": 80, "status": "good"},
                "bug_resolve_hours": {"value": 3.5, "target": 4, "status": "good"},
                "program_stability": {"value": 96.5, "target": 95, "status": "good"}
            },
            "electrical": {
                "drawing_pass_rate": {"value": 86, "target": 85, "status": "good"},
                "plc_debug_pass_rate": {"value": 82, "target": 80, "status": "good"},
                "standard_component_rate": {"value": 72, "target": 70, "status": "good"}
            }
        },
        "trend": [
            {"period": "2024-07", "mechanical": 80, "test": 81, "electrical": 78, "company": 79.5},
            {"period": "2024-08", "mechanical": 80.5, "test": 81.5, "electrical": 78.5, "company": 80},
            {"period": "2024-09", "mechanical": 81, "test": 82, "electrical": 79, "company": 80.5},
            {"period": "2024-10", "mechanical": 81.5, "test": 82.5, "electrical": 80, "company": 81},
            {"period": "2024-11", "mechanical": 82.1, "test": 83.2, "electrical": 80.5, "company": 81.5}
        ]
    }
    return APIResponse(data=data)


@app.get("/api/v1/performance/summary/job-type/{job_type}",
         response_model=APIResponse,
         summary="按岗位类型绩效概览",
         tags=["综合概览"])
async def get_job_type_summary(
    job_type: JobType = Path(...),
    period_type: PeriodType = Query(...),
    period_value: str = Query(...)
):
    """获取指定岗位类型的绩效概览"""
    
    # 根据岗位类型返回不同的专属指标
    job_metrics = {
        JobType.mechanical: {
            "first_pass_rate": {"name": "设计一次通过率", "value": 87, "target": 85},
            "ecn_responsibility_rate": {"name": "ECN责任率", "value": 8, "target": 10, "inverse": True},
            "debug_issue_density": {"name": "调试问题密度", "value": 0.3, "target": 0.5, "inverse": True},
            "standard_parts_rate": {"name": "标准件使用率", "value": 65, "target": 60},
            "design_reuse_rate": {"name": "设计复用率", "value": 32, "target": 30}
        },
        JobType.test: {
            "program_first_pass_rate": {"name": "程序一次调通率", "value": 82, "target": 80},
            "bug_resolve_hours": {"name": "Bug修复时长(h)", "value": 3.5, "target": 4, "inverse": True},
            "code_review_pass_rate": {"name": "代码审查通过率", "value": 91, "target": 90},
            "program_stability": {"name": "程序稳定性", "value": 96.5, "target": 95},
            "test_coverage": {"name": "测试覆盖率", "value": 88, "target": 90}
        },
        JobType.electrical: {
            "drawing_pass_rate": {"name": "图纸一次通过率", "value": 86, "target": 85},
            "plc_debug_pass_rate": {"name": "PLC一次调通率", "value": 82, "target": 80},
            "debug_efficiency": {"name": "调试效率", "value": 95, "target": 90},
            "standard_component_rate": {"name": "标准件使用率", "value": 72, "target": 70},
            "selection_accuracy": {"name": "选型准确率", "value": 96, "target": 95}
        }
    }
    
    data = {
        "job_type": job_type.value,
        "job_type_name": get_job_type_name(job_type),
        "period": {"type": period_type.value, "value": period_value},
        "overview": {
            "engineer_count": 35 if job_type == JobType.mechanical else 15 if job_type == JobType.test else 30,
            "avg_score": 82.1 if job_type == JobType.mechanical else 83.2 if job_type == JobType.test else 80.5,
            "score_change": 1.5,
            "excellent_count": 5,
            "excellent_rate": 14.3
        },
        "dimension_avg": {
            "technical": 84,
            "execution": 82,
            "cost_quality": 80,
            "knowledge": 75,
            "collaboration": 85
        },
        "key_metrics": job_metrics.get(job_type, {}),
        "grade_distribution": [
            {"grade": "S", "count": 5, "percentage": 14.3},
            {"grade": "A", "count": 18, "percentage": 51.4},
            {"grade": "B", "count": 10, "percentage": 28.6},
            {"grade": "C", "count": 2, "percentage": 5.7}
        ]
    }
    return APIResponse(data=data)


# -------------------- 绩效排名 --------------------

@app.get("/api/v1/performance/ranking",
         response_model=APIResponse,
         summary="综合绩效排名",
         tags=["绩效排名"])
async def get_ranking(
    period_type: PeriodType = Query(...),
    period_value: str = Query(...),
    job_type: Optional[JobType] = Query(None, description="按岗位筛选"),
    department_id: Optional[int] = Query(None, description="按部门筛选"),
    grade: Optional[Grade] = Query(None, description="按等级筛选"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """
    获取绩效排名列表，支持多维度筛选
    """
    # 模拟数据
    engineers = [
        {"id": 1, "name": "张机械", "job_type": "mechanical", "dept": "机械设计部", "level": "高级",
         "scores": {"technical": 90, "execution": 88, "cost_quality": 85, "knowledge": 82, "collaboration": 90},
         "total_score": 88.5, "grade": "S", "trend": "up", "score_change": 2.5},
        {"id": 2, "name": "李测试", "job_type": "test", "dept": "测试部", "level": "高级",
         "scores": {"technical": 92, "execution": 86, "cost_quality": 84, "knowledge": 80, "collaboration": 88},
         "total_score": 87.2, "grade": "S", "trend": "up", "score_change": 1.8},
        {"id": 3, "name": "王电气", "job_type": "electrical", "dept": "电气部", "level": "高级",
         "scores": {"technical": 88, "execution": 85, "cost_quality": 86, "knowledge": 82, "collaboration": 88},
         "total_score": 86.8, "grade": "S", "trend": "stable", "score_change": 0.5},
    ]
    
    # 添加排名和岗位名称
    ranking_list = []
    for idx, eng in enumerate(engineers):
        ranking_list.append({
            "rank": idx + 1,
            "engineer_id": eng["id"],
            "engineer_name": eng["name"],
            "job_type": eng["job_type"],
            "job_type_name": get_job_type_name(JobType(eng["job_type"])),
            "department": eng["dept"],
            "level": eng["level"],
            "scores": eng["scores"],
            "total_score": eng["total_score"],
            "grade": eng["grade"],
            "grade_name": get_grade_name(Grade(eng["grade"])),
            "trend": eng["trend"],
            "score_change": eng["score_change"]
        })
    
    data = {
        "period": {"type": period_type.value, "value": period_value},
        "filters": {
            "job_type": job_type.value if job_type else None,
            "department_id": department_id,
            "grade": grade.value if grade else None
        },
        "total": len(ranking_list),
        "page": page,
        "page_size": page_size,
        "list": ranking_list
    }
    return APIResponse(data=data)


@app.get("/api/v1/performance/ranking/top",
         response_model=APIResponse,
         summary="TOP N 工程师",
         tags=["绩效排名"])
async def get_top_engineers(
    period_type: PeriodType = Query(...),
    period_value: str = Query(...),
    top_n: int = Query(10, ge=1, le=50)
):
    """获取TOP N工程师排名"""
    # 复用排名接口逻辑
    result = await get_ranking(period_type, period_value, page_size=top_n)
    return result


# -------------------- 个人绩效 --------------------

@app.get("/api/v1/performance/engineer/{engineer_id}",
         response_model=APIResponse,
         summary="个人绩效详情",
         tags=["个人绩效"])
async def get_engineer_performance(
    engineer_id: int = Path(...),
    period_type: PeriodType = Query(...),
    period_value: str = Query(...)
):
    """
    获取指定工程师的绩效详情
    """
    # 模拟数据 - 机械工程师示例
    data = {
        "engineer": {
            "id": engineer_id,
            "name": "张机械",
            "job_type": "mechanical",
            "job_type_name": "机械工程师",
            "level": "高级工程师",
            "department": "机械设计部",
            "department_id": 101,
            "skills": ["SolidWorks", "AutoCAD", "ANSYS"],
            "join_date": "2019-03-15"
        },
        "period": {
            "type": period_type.value,
            "value": period_value
        },
        "summary": {
            "total_score": 85.5,
            "grade": "S",
            "grade_name": "优秀",
            "department_rank": 2,
            "department_total": 35,
            "job_type_rank": 3,
            "job_type_total": 35,
            "company_rank": 5,
            "company_total": 80,
            "prev_score": 83.0,
            "score_change": 2.5
        },
        "dimension_scores": {
            "technical": {"score": 88, "weight": 30, "weighted": 26.4},
            "execution": {"score": 85, "weight": 25, "weighted": 21.25},
            "cost_quality": {"score": 82, "weight": 20, "weighted": 16.4},
            "knowledge": {"score": 80, "weight": 15, "weighted": 12.0},
            "collaboration": {"score": 88, "weight": 10, "weighted": 8.8}
        },
        "metrics": {
            "technical": [
                {"code": "first_pass_rate", "name": "设计一次通过率", "value": 90, "target": 85, "unit": "%", "status": "good"},
                {"code": "ecn_responsibility_rate", "name": "ECN责任率", "value": 8, "target": 10, "unit": "%", "status": "good", "inverse": True},
                {"code": "debug_issue_density", "name": "调试问题密度", "value": 0.3, "target": 0.5, "status": "good", "inverse": True}
            ],
            "execution": [
                {"code": "on_time_rate", "name": "按时完成率", "value": 92, "target": 90, "unit": "%", "status": "good"},
                {"code": "bom_delivery_rate", "name": "BOM交付及时率", "value": 96, "target": 95, "unit": "%", "status": "good"},
                {"code": "weighted_output", "name": "难度加权产出", "value": 28, "description": "本月完成"}
            ],
            "cost_quality": [
                {"code": "standard_parts_rate", "name": "标准件使用率", "value": 68, "target": 60, "unit": "%", "status": "good"},
                {"code": "design_reuse_rate", "name": "设计复用率", "value": 35, "target": 30, "unit": "%", "status": "good"}
            ],
            "knowledge": [
                {"code": "doc_count", "name": "技术文档贡献", "value": 3, "target": 2, "status": "good"},
                {"code": "template_count", "name": "标准模板贡献", "value": 1, "target": 1, "status": "good"},
                {"code": "reuse_count", "name": "被引用次数", "value": 15, "description": "本季度"}
            ],
            "collaboration": [
                {"code": "electrical_score", "name": "电气部评价", "value": 4.5, "target": 4.0, "status": "good"},
                {"code": "test_score", "name": "测试部评价", "value": 4.3, "target": 4.0, "status": "good"},
                {"code": "mentee_count", "name": "带教新人", "value": 2, "description": "本季度"}
            ]
        },
        "collaboration_ratings": {
            "received": [
                {"from_job_type": "electrical", "from_job_type_name": "电气部", "avg_score": 4.5, "count": 5},
                {"from_job_type": "test", "from_job_type_name": "测试部", "avg_score": 4.3, "count": 3}
            ],
            "given_count": 6
        },
        "projects": [
            {
                "project_id": "P2024-156",
                "project_name": "XX检测设备",
                "role": "主设计",
                "status": "已验收",
                "task_count": 12,
                "on_time_rate": 92,
                "first_pass_rate": 90
            },
            {
                "project_id": "P2024-162",
                "project_name": "YY组装线",
                "role": "参与设计",
                "status": "进行中",
                "task_count": 5,
                "on_time_rate": 100,
                "first_pass_rate": 100
            }
        ],
        "knowledge_contributions": [
            {"title": "标准检测机台设计规范", "type": "document", "reuse_count": 8, "rating": 4.8},
            {"title": "快速定位机构模板", "type": "template", "reuse_count": 12, "rating": 4.9}
        ]
    }
    return APIResponse(data=data)


@app.get("/api/v1/performance/engineer/{engineer_id}/trend",
         response_model=APIResponse,
         summary="个人绩效趋势",
         tags=["个人绩效"])
async def get_engineer_trend(
    engineer_id: int = Path(...),
    period_type: PeriodType = Query(PeriodType.monthly),
    count: int = Query(6, ge=1, le=12)
):
    """获取个人绩效趋势数据"""
    data = {
        "engineer_id": engineer_id,
        "period_type": period_type.value,
        "trends": [
            {
                "period": "2024-06",
                "total_score": 80.5,
                "department_avg": 79.0,
                "dimensions": {"technical": 82, "execution": 80, "cost_quality": 78, "knowledge": 75, "collaboration": 85}
            },
            {
                "period": "2024-07",
                "total_score": 81.5,
                "department_avg": 80.0,
                "dimensions": {"technical": 84, "execution": 81, "cost_quality": 79, "knowledge": 76, "collaboration": 86}
            },
            {
                "period": "2024-11",
                "total_score": 85.5,
                "department_avg": 82.1,
                "dimensions": {"technical": 88, "execution": 85, "cost_quality": 82, "knowledge": 80, "collaboration": 88}
            }
        ],
        "metric_trends": {
            "first_pass_rate": [85, 86, 87, 88, 89, 90],
            "on_time_rate": [88, 89, 90, 90, 91, 92],
            "standard_parts_rate": [60, 62, 63, 65, 66, 68]
        }
    }
    return APIResponse(data=data)


@app.get("/api/v1/performance/engineer/{engineer_id}/comparison",
         response_model=APIResponse,
         summary="个人绩效对比",
         tags=["个人绩效"])
async def get_engineer_comparison(
    engineer_id: int = Path(...),
    compare_with: int = Query(..., description="对比工程师ID"),
    period_type: PeriodType = Query(...),
    period_value: str = Query(...)
):
    """将两位工程师进行绩效对比"""
    data = {
        "period": {"type": period_type.value, "value": period_value},
        "engineer_a": {
            "id": engineer_id,
            "name": "张机械",
            "job_type": "mechanical",
            "total_score": 85.5,
            "dimensions": {"technical": 88, "execution": 85, "cost_quality": 82, "knowledge": 80, "collaboration": 88}
        },
        "engineer_b": {
            "id": compare_with,
            "name": "赵机械",
            "job_type": "mechanical",
            "total_score": 82.0,
            "dimensions": {"technical": 84, "execution": 82, "cost_quality": 80, "knowledge": 76, "collaboration": 85}
        },
        "comparison": {
            "total_score_diff": 3.5,
            "dimension_diffs": {
                "technical": 4,
                "execution": 3,
                "cost_quality": 2,
                "knowledge": 4,
                "collaboration": 3
            },
            "winner": engineer_id
        }
    }
    return APIResponse(data=data)


# -------------------- 跨部门协作 --------------------

@app.get("/api/v1/performance/collaboration/matrix",
         response_model=APIResponse,
         summary="跨部门协作矩阵",
         tags=["跨部门协作"])
async def get_collaboration_matrix(
    rating_period: str = Query(..., description="评价周期")
):
    """获取跨部门协作评价矩阵"""
    data = {
        "rating_period": rating_period,
        "matrix": {
            "mechanical_from_test": {"avg_score": 4.3, "count": 25},
            "mechanical_from_electrical": {"avg_score": 4.5, "count": 30},
            "test_from_mechanical": {"avg_score": 4.2, "count": 28},
            "test_from_electrical": {"avg_score": 4.4, "count": 18},
            "electrical_from_mechanical": {"avg_score": 4.1, "count": 32},
            "electrical_from_test": {"avg_score": 3.9, "count": 15}
        },
        "summary": {
            "total_ratings": 156,
            "avg_score": 4.2,
            "pending_count": 12
        }
    }
    return APIResponse(data=data)


@app.get("/api/v1/performance/collaboration/received/{engineer_id}",
         response_model=APIResponse,
         summary="收到的协作评价",
         tags=["跨部门协作"])
async def get_received_ratings(
    engineer_id: int = Path(...),
    rating_period: Optional[str] = Query(None)
):
    """获取工程师收到的跨部门协作评价"""
    data = {
        "engineer_id": engineer_id,
        "summary": {
            "avg_score": 4.4,
            "total_count": 8,
            "by_dimension": {
                "communication": 4.5,
                "response": 4.3,
                "quality": 4.5,
                "interface": 4.2
            }
        },
        "ratings": [
            {
                "rater_id": 2001,
                "rater_name": "李电气",
                "rater_job_type": "electrical",
                "scores": {"communication": 5, "response": 4, "quality": 5, "interface": 4},
                "avg_score": 4.5,
                "comments": "配合非常好",
                "project_id": "P2024-156",
                "created_at": "2024-11-15"
            }
        ]
    }
    return APIResponse(data=data)


@app.post("/api/v1/performance/collaboration",
          response_model=APIResponse,
          summary="提交协作评价",
          tags=["跨部门协作"])
async def submit_collaboration_rating(request: CollaborationRatingRequest):
    """提交跨部门协作评价"""
    avg_score = (request.communication_score + request.response_score + 
                 request.quality_score + request.interface_score) / 4
    
    data = {
        "id": 10001,
        "rating_period": request.rating_period,
        "rated_engineer_id": request.rated_engineer_id,
        "avg_score": round(avg_score, 2),
        "message": "评价已提交"
    }
    return APIResponse(data=data)


# -------------------- 知识贡献 --------------------

@app.get("/api/v1/performance/knowledge",
         response_model=APIResponse,
         summary="知识贡献列表",
         tags=["知识贡献"])
async def list_knowledge_contributions(
    job_type: Optional[JobType] = Query(None),
    contribution_type: Optional[ContributionType] = Query(None),
    author_id: Optional[int] = Query(None),
    sort_by: str = Query("reuse_count", description="排序字段"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """查询知识贡献列表"""
    data = {
        "statistics": {
            "total_contributions": 256,
            "this_month": 18,
            "total_reuse": 892,
            "contributors": 45
        },
        "total": 256,
        "list": [
            {
                "id": 1,
                "title": "伺服定位功能块(FB)",
                "type": "module",
                "type_name": "模块",
                "author_id": 3001,
                "author_name": "王电气",
                "job_type": "electrical",
                "job_type_name": "电气工程师",
                "reuse_count": 56,
                "rating": 4.9,
                "status": "published",
                "created_at": "2024-06-15"
            },
            {
                "id": 2,
                "title": "标准检测机台设计模板",
                "type": "template",
                "type_name": "模板",
                "author_id": 1001,
                "author_name": "张机械",
                "job_type": "mechanical",
                "job_type_name": "机械工程师",
                "reuse_count": 48,
                "rating": 4.8,
                "status": "published",
                "created_at": "2024-05-20"
            }
        ]
    }
    return APIResponse(data=data)


@app.get("/api/v1/performance/knowledge/ranking",
         response_model=APIResponse,
         summary="知识贡献排行",
         tags=["知识贡献"])
async def get_knowledge_ranking(
    top_n: int = Query(10, ge=1, le=50)
):
    """获取知识贡献者排行榜"""
    data = {
        "ranking": [
            {
                "rank": 1,
                "engineer_id": 3001,
                "engineer_name": "王电气",
                "job_type": "electrical",
                "job_type_name": "电气工程师",
                "contribution_count": 18,
                "total_reuse": 128,
                "avg_rating": 4.8
            },
            {
                "rank": 2,
                "engineer_id": 1001,
                "engineer_name": "张机械",
                "job_type": "mechanical",
                "job_type_name": "机械工程师",
                "contribution_count": 15,
                "total_reuse": 96,
                "avg_rating": 4.7
            },
            {
                "rank": 3,
                "engineer_id": 2001,
                "engineer_name": "李测试",
                "job_type": "test",
                "job_type_name": "测试工程师",
                "contribution_count": 12,
                "total_reuse": 85,
                "avg_rating": 4.6
            }
        ]
    }
    return APIResponse(data=data)


@app.post("/api/v1/performance/knowledge",
          response_model=APIResponse,
          summary="提交知识贡献",
          tags=["知识贡献"])
async def submit_knowledge_contribution(request: KnowledgeContributionRequest):
    """提交新的知识贡献"""
    data = {
        "id": 10001,
        "title": request.title,
        "type": request.contribution_type.value,
        "status": "reviewing",
        "message": "贡献已提交，等待审核"
    }
    return APIResponse(data=data)


# -------------------- 配置管理 --------------------

@app.get("/api/v1/performance/config/weights",
         response_model=APIResponse,
         summary="获取权重配置列表",
         tags=["配置管理"])
async def list_weight_configs():
    """
    获取所有岗位级别的权重配置列表
    【重要】权重只能按岗位+级别配置，不能针对个人！
    """
    data = {
        "principle": "权重配置按「岗位类型+职级」统一设定，确保评价公平性，不支持针对个人调整",
        "configs": [
            {
                "job_type": "mechanical",
                "job_type_name": "机械工程师",
                "job_level": "all",
                "job_level_name": "全部级别",
                "affected_count": 35,
                "dimensions": [
                    {"code": "technical", "name": "技术能力", "weight": 30},
                    {"code": "execution", "name": "项目执行", "weight": 25},
                    {"code": "cost_quality", "name": "成本/质量", "weight": 20},
                    {"code": "knowledge", "name": "知识沉淀", "weight": 15},
                    {"code": "collaboration", "name": "团队协作", "weight": 10}
                ],
                "effective_date": "2024-01-01",
                "version": 1
            },
            {
                "job_type": "test",
                "job_type_name": "测试工程师",
                "job_level": "all",
                "job_level_name": "全部级别",
                "affected_count": 15,
                "dimensions": [
                    {"code": "technical", "name": "技术能力", "weight": 30},
                    {"code": "execution", "name": "项目执行", "weight": 25},
                    {"code": "cost_quality", "name": "成本/质量", "weight": 20},
                    {"code": "knowledge", "name": "知识沉淀", "weight": 15},
                    {"code": "collaboration", "name": "团队协作", "weight": 10}
                ],
                "effective_date": "2024-01-01",
                "version": 1
            },
            {
                "job_type": "electrical",
                "job_type_name": "电气工程师",
                "job_level": "all",
                "job_level_name": "全部级别",
                "affected_count": 30,
                "dimensions": [
                    {"code": "technical", "name": "技术能力", "weight": 30},
                    {"code": "execution", "name": "项目执行", "weight": 25},
                    {"code": "cost_quality", "name": "成本/质量", "weight": 20},
                    {"code": "knowledge", "name": "知识沉淀", "weight": 15},
                    {"code": "collaboration", "name": "团队协作", "weight": 10}
                ],
                "effective_date": "2024-01-01",
                "version": 1
            }
        ]
    }
    return APIResponse(data=data)


class JobLevel(str, Enum):
    all = "all"
    junior = "初级"
    intermediate = "中级"
    senior = "高级"
    expert = "资深"
    master = "专家"


@app.get("/api/v1/performance/config/weights/{job_type}/{job_level}",
         response_model=APIResponse,
         summary="获取指定岗位级别的权重配置",
         tags=["配置管理"])
async def get_weight_config(
    job_type: JobType = Path(..., description="岗位类型"),
    job_level: str = Path("all", description="职级，all表示通用配置")
):
    """
    获取指定岗位和级别的权重配置
    【重要原则】配置按岗位+级别设定，不能针对个人！
    """
    
    # 计算该配置影响的人数
    affected_counts = {
        ("mechanical", "all"): 35,
        ("test", "all"): 15,
        ("electrical", "all"): 30,
    }
    affected_count = affected_counts.get((job_type.value, job_level), 0)
    
    # 通用维度配置
    dimensions = [
        {"code": "technical", "name": "技术能力", "weight": 30},
        {"code": "execution", "name": "项目执行", "weight": 25},
        {"code": "cost_quality", "name": "成本/质量", "weight": 20},
        {"code": "knowledge", "name": "知识沉淀", "weight": 15},
        {"code": "collaboration", "name": "团队协作", "weight": 10}
    ]
    
    # 岗位专属指标配置（省略，同之前）
    metrics_config = {
        JobType.mechanical: {
            "technical": [
                {"code": "first_pass_rate", "name": "设计一次通过率", "weight": 35, "target": 85},
                {"code": "ecn_responsibility_rate", "name": "ECN责任率", "weight": 25, "target": 10, "inverse": True},
            ]
        },
        # ... 其他岗位配置
    }
    
    data = {
        "principle": "此配置统一适用于该岗位+级别的所有工程师，不支持个人差异化",
        "job_type": job_type.value,
        "job_type_name": get_job_type_name(job_type),
        "job_level": job_level,
        "job_level_name": "全部级别" if job_level == "all" else job_level,
        "affected_count": affected_count,
        "dimensions": dimensions,
        "metrics": metrics_config.get(job_type, {}),
        "effective_date": "2024-01-01",
        "version": 1
    }
    return APIResponse(data=data)


class WeightUpdateRequest(BaseModel):
    """权重更新请求 - 只能按岗位+级别更新，不能针对个人"""
    job_type: JobType = Field(..., description="岗位类型")
    job_level: str = Field("all", description="职级")
    dimensions: List[DimensionWeight] = Field(..., description="维度权重列表")
    effective_date: date = Field(..., description="生效日期")


@app.put("/api/v1/performance/config/weights",
         response_model=APIResponse,
         summary="更新权重配置（按岗位+级别）",
         tags=["配置管理"])
async def update_weight_config(request: WeightUpdateRequest):
    """
    更新指定岗位+级别的权重配置
    【重要原则】只能按岗位+级别配置，不能针对个人！
    此更新将影响该分类下的所有工程师
    """
    # 验证权重总和
    total = sum(d.weight for d in request.dimensions)
    if total != 100:
        raise HTTPException(
            status_code=400, 
            detail=f"维度权重总和必须为100%，当前为{total}%"
        )
    
    # 计算影响人数
    affected_counts = {
        ("mechanical", "all"): 35,
        ("test", "all"): 15,
        ("electrical", "all"): 30,
    }
    affected_count = affected_counts.get((request.job_type.value, request.job_level), 0)
    
    data = {
        "job_type": request.job_type.value,
        "job_type_name": get_job_type_name(request.job_type),
        "job_level": request.job_level,
        "affected_count": affected_count,
        "effective_date": request.effective_date.isoformat(),
        "message": f"配置已更新，将影响 {affected_count} 名工程师，于 {request.effective_date} 生效",
        "updated_at": datetime.now().isoformat()
    }
    return APIResponse(data=data)


@app.get("/api/v1/performance/config/grades",
         response_model=APIResponse,
         summary="获取等级规则",
         tags=["配置管理"])
async def get_grade_rules():
    """获取等级划分规则"""
    data = {
        "rules": [
            {"grade": "S", "grade_name": "优秀", "min_score": 85, "max_score": 100, "color": "#22c55e"},
            {"grade": "A", "grade_name": "良好", "min_score": 70, "max_score": 84.99, "color": "#3b82f6"},
            {"grade": "B", "grade_name": "合格", "min_score": 60, "max_score": 69.99, "color": "#f59e0b"},
            {"grade": "C", "grade_name": "待改进", "min_score": 40, "max_score": 59.99, "color": "#f97316"},
            {"grade": "D", "grade_name": "不合格", "min_score": 0, "max_score": 39.99, "color": "#ef4444"}
        ]
    }
    return APIResponse(data=data)


# -------------------- 计算任务 --------------------

@app.post("/api/v1/performance/calculate/trigger",
          response_model=APIResponse,
          summary="触发绩效计算",
          tags=["计算任务"])
async def trigger_calculation(request: CalculateRequest):
    """触发绩效计算任务"""
    task_id = f"calc-{datetime.now().strftime('%Y%m%d%H%M%S')}-001"
    
    # 计算预估时间
    engineer_count = 80  # 实际应从数据库查询
    if request.engineer_ids:
        engineer_count = len(request.engineer_ids)
    elif request.job_types:
        engineer_count = len(request.job_types) * 25  # 估算
    
    estimated_seconds = max(30, engineer_count * 2)
    
    data = {
        "task_id": task_id,
        "status": "processing",
        "period": {
            "type": request.period_type.value,
            "value": request.period_value
        },
        "scope": {
            "job_types": [jt.value for jt in request.job_types] if request.job_types else ["all"],
            "engineer_count": engineer_count
        },
        "estimated_time": estimated_seconds,
        "message": "绩效计算任务已提交"
    }
    return APIResponse(data=data)


@app.get("/api/v1/performance/calculate/status/{task_id}",
         response_model=APIResponse,
         summary="计算任务状态",
         tags=["计算任务"])
async def get_calculation_status(task_id: str = Path(...)):
    """获取计算任务状态"""
    data = {
        "task_id": task_id,
        "status": "completed",
        "progress": 100,
        "result": {
            "processed_count": 80,
            "success_count": 80,
            "failed_count": 0,
            "duration_seconds": 45
        },
        "completed_at": datetime.now().isoformat()
    }
    return APIResponse(data=data)


# ==================== 启动入口 ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
