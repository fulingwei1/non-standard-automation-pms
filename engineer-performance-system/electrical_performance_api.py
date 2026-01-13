"""
电气工程师绩效评价系统 - API接口实现
基于 FastAPI 框架
"""

from fastapi import FastAPI, Query, Path, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
import json

app = FastAPI(
    title="电气工程师绩效评价系统 API",
    description="非标自动化设备公司电气工程师绩效评价系统后端接口",
    version="1.0.0"
)

# ==================== 枚举定义 ====================

class PeriodType(str, Enum):
    monthly = "monthly"
    quarterly = "quarterly"
    yearly = "yearly"

class PLCBrand(str, Enum):
    siemens = "西门子"
    mitsubishi = "三菱"
    omron = "欧姆龙"
    beckhoff = "倍福"
    inovance = "汇川"
    delta = "台达"
    other = "其他"

class DrawingType(str, Enum):
    schematic = "电气原理图"
    layout = "电气布局图"
    wiring = "接线图"
    terminal = "端子图"
    cable_list = "线缆清单"
    plc_program = "PLC程序"
    hmi = "HMI画面"

class ReviewStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"

class FaultType(str, Enum):
    wiring_error = "接线错误"
    selection_error = "选型错误"
    program_bug = "程序Bug"
    design_defect = "设计缺陷"
    component_damage = "元器件损坏"
    communication = "通讯故障"
    other = "其他"

class Severity(str, Enum):
    fatal = "致命"
    serious = "严重"
    normal = "一般"
    minor = "轻微"

class ModuleType(str, Enum):
    motion_control = "运动控制"
    io_processing = "IO处理"
    communication = "通讯"
    data_processing = "数据处理"
    alarm = "报警处理"
    recipe = "配方管理"
    process = "工艺流程"
    utility = "通用工具"


# ==================== 请求/响应模型 ====================

# --- 通用响应 ---
class APIResponse(BaseModel):
    code: int = 200
    message: str = "success"
    data: Optional[dict] = None

# --- 绩效概览 ---
class MetricStatus(BaseModel):
    value: float
    target: float
    status: str  # good, warning, bad

class DimensionScore(BaseModel):
    technical: float
    execution: float
    cost: float
    knowledge: float
    collaboration: float

class PerformanceSummaryResponse(BaseModel):
    period: dict
    overview: dict
    key_metrics: dict
    dimension_avg: DimensionScore
    plc_brand_distribution: List[dict]
    fault_type_distribution: List[dict]

# --- 绩效排名 ---
class EngineerRanking(BaseModel):
    rank: int
    engineer_id: int
    engineer_name: str
    level: str
    primary_plc: str
    scores: DimensionScore
    total_score: float
    grade: str
    trend: str
    key_metrics: dict

class RankingListResponse(BaseModel):
    total: int
    list: List[EngineerRanking]

# --- 个人绩效详情 ---
class EngineerInfo(BaseModel):
    id: int
    name: str
    level: str
    department: str
    primary_plc: List[str]
    join_date: date

class PerformanceSummary(BaseModel):
    total_score: float
    grade: str
    rank: int
    rank_total: int
    score_change: float

class DetailMetric(BaseModel):
    value: float
    target: Optional[float] = None
    status: Optional[str] = None
    description: Optional[str] = None

class ProjectRecord(BaseModel):
    project_id: str
    project_name: str
    role: str
    status: str
    plc_brand: str
    drawing_count: int
    program_score: Optional[float]
    fault_count: int

class PLCProgram(BaseModel):
    project: str
    program_name: str
    plc_brand: str
    model: str
    version: str
    first_debug_pass: bool
    stability: float
    deploy_date: date

class ModuleContribution(BaseModel):
    module_name: str
    module_type: str
    plc_brand: str
    reuse_count: int
    rating: float

class IndividualPerformanceResponse(BaseModel):
    engineer: EngineerInfo
    period: dict
    summary: PerformanceSummary
    dimension_scores: dict
    detail_metrics: dict
    projects: List[ProjectRecord]
    drawings_summary: dict
    plc_programs: List[PLCProgram]
    module_contributions: List[ModuleContribution]

# --- 图纸提交 ---
class DrawingSubmitRequest(BaseModel):
    project_id: int
    drawing_no: str
    drawing_name: str
    drawing_type: DrawingType
    version: str = "V1.0"
    page_count: Optional[int] = None
    component_count: Optional[int] = None
    planned_date: date
    designer_id: int
    attachments: Optional[List[str]] = None

class DrawingSubmitResponse(BaseModel):
    id: int
    drawing_no: str
    status: str
    message: str

# --- 图纸审核 ---
class ReviewItem(BaseModel):
    item: str
    passed: bool = Field(..., alias="pass")

    class Config:
        populate_by_name = True

class DrawingReviewRequest(BaseModel):
    reviewer_id: int
    status: ReviewStatus
    comments: Optional[str] = None
    review_items: Optional[List[ReviewItem]] = None

class DrawingReviewResponse(BaseModel):
    id: int
    review_status: str
    review_pass_first: bool
    review_count: int
    message: str

# --- PLC程序提交 ---
class PLCProgramSubmitRequest(BaseModel):
    project_id: int
    program_name: str
    plc_brand: PLCBrand
    plc_model: Optional[str] = None
    program_type: Optional[str] = None
    version: str = "V1.0"
    program_steps: Optional[int] = None
    function_blocks: Optional[int] = None
    io_points: Optional[int] = None
    axis_count: Optional[int] = None
    developer_id: int
    planned_debug_hours: Optional[float] = None

class PLCProgramSubmitResponse(BaseModel):
    id: int
    program_name: str
    status: str
    message: str

# --- 调试结果更新 ---
class DebugResultRequest(BaseModel):
    first_debug_pass: bool
    debug_hours: float
    deploy_date: date
    deploy_status: str
    notes: Optional[str] = None

class DebugResultResponse(BaseModel):
    id: int
    first_debug_pass: bool
    debug_efficiency: float
    message: str

# --- 故障登记 ---
class FaultSubmitRequest(BaseModel):
    project_id: int
    fault_type: FaultType
    fault_title: str
    fault_description: Optional[str] = None
    severity: Severity
    found_stage: str
    responsible_id: Optional[int] = None
    is_design_fault: bool = False

class FaultSubmitResponse(BaseModel):
    id: int
    fault_no: str
    status: str
    message: str

# --- PLC模块贡献 ---
class ModuleSubmitRequest(BaseModel):
    module_name: str
    module_type: ModuleType
    plc_brand: PLCBrand
    description: Optional[str] = None
    usage_guide: Optional[str] = None
    author_id: int
    version: str = "V1.0"
    attachments: Optional[List[str]] = None

class ModuleSubmitResponse(BaseModel):
    id: int
    module_name: str
    status: str
    message: str

# --- 绩效计算 ---
class CalculateRequest(BaseModel):
    period_type: PeriodType
    period_value: str
    engineer_ids: Optional[List[int]] = None

class CalculateResponse(BaseModel):
    task_id: str
    status: str
    message: str
    estimated_time: int

# --- 权重配置 ---
class SubItemConfig(BaseModel):
    weight: int
    target: Optional[float] = None
    inverse: Optional[bool] = None

class DimensionConfig(BaseModel):
    weight: int
    sub_items: dict

class GradeRule(BaseModel):
    grade: str
    min_score: int

class ConfigResponse(BaseModel):
    weights: dict
    grade_rules: List[GradeRule]


# ==================== API 接口实现 ====================

# -------------------- 绩效查询接口 --------------------

@app.get("/api/electrical/performance/summary", 
         response_model=APIResponse,
         summary="部门绩效概览",
         tags=["绩效查询"])
async def get_performance_summary(
    period_type: PeriodType = Query(..., description="周期类型"),
    period_value: str = Query(..., description="周期值，如 2024-11 或 2024Q4")
):
    """
    获取电气部门绩效概览，包括：
    - 部门整体统计（人数、平均分、优秀率等）
    - 关键指标达成情况
    - 各维度平均分
    - PLC品牌分布
    - 故障类型分布
    """
    # 模拟返回数据
    data = {
        "period": {
            "type": period_type.value,
            "value": period_value,
            "start_date": "2024-11-01",
            "end_date": "2024-11-30"
        },
        "overview": {
            "engineer_count": 10,
            "avg_score": 82.5,
            "score_change": 1.5,
            "excellent_count": 3,
            "excellent_rate": 30,
            "need_improve_count": 1
        },
        "key_metrics": {
            "drawing_pass_rate": {"value": 86.5, "target": 85, "status": "good"},
            "plc_debug_pass_rate": {"value": 82.0, "target": 80, "status": "good"},
            "on_time_rate": {"value": 88.5, "target": 90, "status": "warning"},
            "standard_component_rate": {"value": 72.0, "target": 70, "status": "good"},
            "fault_density": {"value": 0.15, "target": 0.2, "status": "good"}
        },
        "dimension_avg": {
            "technical": 85.2,
            "execution": 82.5,
            "cost": 80.8,
            "knowledge": 76.5,
            "collaboration": 86.0
        },
        "plc_brand_distribution": [
            {"brand": "西门子", "count": 45, "percentage": 50},
            {"brand": "三菱", "count": 27, "percentage": 30},
            {"brand": "欧姆龙", "count": 18, "percentage": 20}
        ],
        "fault_type_distribution": [
            {"type": "程序Bug", "count": 5, "percentage": 35},
            {"type": "接线错误", "count": 4, "percentage": 28},
            {"type": "选型错误", "count": 3, "percentage": 21},
            {"type": "其他", "count": 2, "percentage": 16}
        ]
    }
    return APIResponse(data=data)


@app.get("/api/electrical/performance/ranking",
         response_model=APIResponse,
         summary="绩效排名列表",
         tags=["绩效查询"])
async def get_performance_ranking(
    period_type: PeriodType = Query(...),
    period_value: str = Query(...),
    plc_brand: Optional[PLCBrand] = Query(None, description="按PLC品牌筛选"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """
    获取电气工程师绩效排名列表，支持：
    - 按PLC品牌筛选
    - 分页查询
    """
    # 模拟返回数据
    data = {
        "total": 10,
        "list": [
            {
                "rank": 1,
                "engineer_id": 1001,
                "engineer_name": "王电气",
                "level": "高级",
                "primary_plc": "西门子",
                "scores": {
                    "technical": 92,
                    "execution": 88,
                    "cost": 85,
                    "knowledge": 82,
                    "collaboration": 90
                },
                "total_score": 88.5,
                "grade": "优秀",
                "trend": "up",
                "key_metrics": {
                    "drawing_pass_rate": 95,
                    "plc_debug_pass_rate": 90,
                    "on_time_rate": 92,
                    "fault_count": 1
                }
            },
            {
                "rank": 2,
                "engineer_id": 1002,
                "engineer_name": "李工控",
                "level": "高级",
                "primary_plc": "西门子",
                "scores": {
                    "technical": 88,
                    "execution": 84,
                    "cost": 82,
                    "knowledge": 80,
                    "collaboration": 88
                },
                "total_score": 85.2,
                "grade": "优秀",
                "trend": "up",
                "key_metrics": {
                    "drawing_pass_rate": 90,
                    "plc_debug_pass_rate": 85,
                    "on_time_rate": 88,
                    "fault_count": 2
                }
            }
        ]
    }
    return APIResponse(data=data)


@app.get("/api/electrical/performance/{engineer_id}",
         response_model=APIResponse,
         summary="个人绩效详情",
         tags=["绩效查询"])
async def get_individual_performance(
    engineer_id: int = Path(..., description="工程师ID"),
    period_type: PeriodType = Query(...),
    period_value: str = Query(...)
):
    """
    获取指定工程师的绩效详情，包括：
    - 基本信息
    - 综合得分和排名
    - 五维评分详情
    - 各项指标明细
    - 项目参与记录
    - PLC程序列表
    - 模块贡献
    """
    # 模拟返回数据
    data = {
        "engineer": {
            "id": engineer_id,
            "name": "王电气",
            "level": "高级工程师",
            "department": "电气设计部",
            "primary_plc": ["西门子", "三菱"],
            "join_date": "2019-03-15"
        },
        "period": {
            "type": period_type.value,
            "value": period_value
        },
        "summary": {
            "total_score": 88.5,
            "grade": "优秀",
            "rank": 1,
            "rank_total": 10,
            "score_change": 3.2
        },
        "dimension_scores": {
            "technical": {"score": 92, "weight": 30, "weighted": 27.6},
            "execution": {"score": 88, "weight": 25, "weighted": 22.0},
            "cost": {"score": 85, "weight": 20, "weighted": 17.0},
            "knowledge": {"score": 82, "weight": 15, "weighted": 12.3},
            "collaboration": {"score": 90, "weight": 10, "weighted": 9.0}
        },
        "detail_metrics": {
            "technical": {
                "drawing_pass_rate": {"value": 95, "target": 85, "status": "good"},
                "plc_debug_pass_rate": {"value": 90, "target": 80, "status": "good"},
                "fault_density": {"value": 0.1, "target": 0.2, "status": "good"},
                "debug_efficiency": {"value": 115, "target": 90, "status": "good"}
            },
            "execution": {
                "task_count": {"value": 15, "description": "完成任务数"},
                "on_time_rate": {"value": 92, "target": 90, "status": "good"},
                "drawing_delivery_rate": {"value": 96, "target": 95, "status": "good"},
                "field_response_rate": {"value": 88, "target": 90, "status": "warning"}
            },
            "cost": {
                "standard_component_rate": {"value": 78, "target": 70, "status": "good"},
                "selection_accuracy": {"value": 98, "target": 95, "status": "good"},
                "stock_usage_rate": {"value": 62, "target": 60, "status": "good"}
            },
            "knowledge": {
                "plc_module_count": {"value": 5, "target": 2, "status": "good"},
                "template_count": {"value": 1, "target": 1, "status": "good"},
                "doc_count": {"value": 2, "target": 2, "status": "good"},
                "module_reuse_count": {"value": 18, "description": "被复用次数"}
            },
            "collaboration": {
                "mechanical_collab_score": {"value": 4.5, "target": 4.0, "status": "good"},
                "test_collab_score": {"value": 4.3, "target": 4.0, "status": "good"},
                "interface_doc_score": {"value": 92, "target": 90, "status": "good"}
            }
        },
        "projects": [
            {
                "project_id": "P2024-156",
                "project_name": "XX检测设备",
                "role": "主设计",
                "status": "已验收",
                "plc_brand": "西门子",
                "drawing_count": 25,
                "program_score": 92,
                "fault_count": 0
            }
        ],
        "drawings_summary": {
            "total": 45,
            "passed_first": 43,
            "by_type": [
                {"type": "电气原理图", "count": 15},
                {"type": "PLC程序", "count": 12},
                {"type": "HMI画面", "count": 8},
                {"type": "其他", "count": 10}
            ]
        },
        "plc_programs": [
            {
                "project": "P2024-156",
                "program_name": "主控程序",
                "plc_brand": "西门子",
                "model": "S7-1500",
                "version": "V2.1",
                "first_debug_pass": True,
                "stability": 100,
                "deploy_date": "2024-11-15"
            }
        ],
        "module_contributions": [
            {
                "module_name": "伺服定位FB",
                "module_type": "运动控制",
                "plc_brand": "西门子",
                "reuse_count": 8,
                "rating": 4.8
            }
        ]
    }
    return APIResponse(data=data)


@app.get("/api/electrical/performance/{engineer_id}/trend",
         response_model=APIResponse,
         summary="绩效趋势",
         tags=["绩效查询"])
async def get_performance_trend(
    engineer_id: int = Path(...),
    period_type: PeriodType = Query(PeriodType.monthly),
    count: int = Query(6, ge=1, le=12, description="返回周期数")
):
    """
    获取指定工程师的绩效趋势数据
    """
    data = {
        "engineer_id": engineer_id,
        "engineer_name": "王电气",
        "period_type": period_type.value,
        "trends": [
            {
                "period": "2024-06",
                "total_score": 82.1,
                "department_avg": 80.5,
                "dimensions": {
                    "technical": 85,
                    "execution": 80,
                    "cost": 82,
                    "knowledge": 75,
                    "collaboration": 88
                }
            },
            {
                "period": "2024-11",
                "total_score": 88.5,
                "department_avg": 82.5,
                "dimensions": {
                    "technical": 92,
                    "execution": 88,
                    "cost": 85,
                    "knowledge": 82,
                    "collaboration": 90
                }
            }
        ],
        "metric_trends": {
            "drawing_pass_rate": [85, 87, 88, 90, 92, 95],
            "plc_debug_pass_rate": [78, 80, 82, 85, 88, 90],
            "on_time_rate": [88, 89, 90, 90, 91, 92]
        }
    }
    return APIResponse(data=data)


# -------------------- 数据录入接口 --------------------

@app.post("/api/electrical/drawings",
          response_model=APIResponse,
          summary="提交图纸",
          tags=["数据录入"])
async def submit_drawing(request: DrawingSubmitRequest):
    """
    提交电气图纸，创建新的图纸版本记录
    """
    # 模拟保存逻辑
    data = {
        "id": 10001,
        "drawing_no": request.drawing_no,
        "status": "pending",
        "message": "图纸已提交，等待审核"
    }
    return APIResponse(data=data)


@app.post("/api/electrical/drawings/{drawing_id}/review",
          response_model=APIResponse,
          summary="图纸审核",
          tags=["数据录入"])
async def review_drawing(
    drawing_id: int = Path(...),
    request: DrawingReviewRequest = ...
):
    """
    审核电气图纸，记录审核结果
    """
    # 模拟审核逻辑
    is_first_pass = True  # 需要查询历史审核次数
    data = {
        "id": drawing_id,
        "review_status": request.status.value,
        "review_pass_first": is_first_pass,
        "review_count": 1,
        "message": "审核通过" if request.status == ReviewStatus.approved else "需要修改"
    }
    return APIResponse(data=data)


@app.post("/api/electrical/plc-programs",
          response_model=APIResponse,
          summary="提交PLC程序",
          tags=["数据录入"])
async def submit_plc_program(request: PLCProgramSubmitRequest):
    """
    提交PLC程序版本记录
    """
    data = {
        "id": 20001,
        "program_name": request.program_name,
        "status": "created",
        "message": "程序版本已创建"
    }
    return APIResponse(data=data)


@app.put("/api/electrical/plc-programs/{program_id}/debug-result",
         response_model=APIResponse,
         summary="更新调试结果",
         tags=["数据录入"])
async def update_debug_result(
    program_id: int = Path(...),
    request: DebugResultRequest = ...
):
    """
    更新PLC程序调试结果
    """
    # 计算调试效率 = 计划时间 / 实际时间 * 100
    planned_hours = 24  # 从数据库获取
    debug_efficiency = round(planned_hours / request.debug_hours * 100, 1)
    
    data = {
        "id": program_id,
        "first_debug_pass": request.first_debug_pass,
        "debug_efficiency": debug_efficiency,
        "message": "调试结果已更新"
    }
    return APIResponse(data=data)


@app.post("/api/electrical/faults",
          response_model=APIResponse,
          summary="登记故障",
          tags=["数据录入"])
async def submit_fault(request: FaultSubmitRequest):
    """
    登记电气故障记录
    """
    # 生成故障编号
    fault_no = f"EF-{datetime.now().strftime('%Y')}-{1001:04d}"
    
    data = {
        "id": 30001,
        "fault_no": fault_no,
        "status": "新建",
        "message": "故障已登记"
    }
    return APIResponse(data=data)


@app.post("/api/electrical/modules",
          response_model=APIResponse,
          summary="贡献PLC模块",
          tags=["数据录入"])
async def submit_module(request: ModuleSubmitRequest):
    """
    提交PLC模块到公共模块库
    """
    data = {
        "id": 40001,
        "module_name": request.module_name,
        "status": "draft",
        "message": "模块已提交，待审核发布"
    }
    return APIResponse(data=data)


# -------------------- 计算和配置接口 --------------------

@app.post("/api/electrical/performance/calculate",
          response_model=APIResponse,
          summary="触发绩效计算",
          tags=["计算配置"])
async def trigger_calculation(request: CalculateRequest):
    """
    触发指定周期的绩效计算任务
    """
    task_id = f"calc-{datetime.now().strftime('%Y%m%d%H%M%S')}-001"
    
    data = {
        "task_id": task_id,
        "status": "processing",
        "message": "绩效计算任务已提交",
        "estimated_time": 30
    }
    return APIResponse(data=data)


@app.get("/api/electrical/performance/config",
         response_model=APIResponse,
         summary="获取权重配置",
         tags=["计算配置"])
async def get_config():
    """
    获取电气工程师绩效评价权重配置
    """
    data = {
        "weights": {
            "technical": {
                "weight": 30,
                "sub_items": {
                    "drawing_pass_rate": {"weight": 30, "target": 85},
                    "plc_debug_pass_rate": {"weight": 30, "target": 80},
                    "fault_density": {"weight": 25, "target": 0.2, "inverse": True},
                    "debug_efficiency": {"weight": 15, "target": 90}
                }
            },
            "execution": {
                "weight": 25,
                "sub_items": {
                    "on_time_rate": {"weight": 40, "target": 90},
                    "drawing_delivery_rate": {"weight": 30, "target": 95},
                    "field_response_rate": {"weight": 30, "target": 90}
                }
            },
            "cost": {
                "weight": 20,
                "sub_items": {
                    "standard_component_rate": {"weight": 40, "target": 70},
                    "selection_accuracy": {"weight": 40, "target": 95},
                    "stock_usage_rate": {"weight": 20, "target": 60}
                }
            },
            "knowledge": {
                "weight": 15,
                "sub_items": {
                    "plc_module_count": {"weight": 40, "target": 2},
                    "template_count": {"weight": 20, "target": 1},
                    "doc_count": {"weight": 25, "target": 2},
                    "module_reuse_count": {"weight": 15, "target": 5}
                }
            },
            "collaboration": {
                "weight": 10,
                "sub_items": {
                    "mechanical_collab_score": {"weight": 35, "target": 4.0},
                    "test_collab_score": {"weight": 35, "target": 4.0},
                    "interface_doc_score": {"weight": 30, "target": 90}
                }
            }
        },
        "grade_rules": [
            {"grade": "优秀", "min_score": 85},
            {"grade": "良好", "min_score": 70},
            {"grade": "合格", "min_score": 60},
            {"grade": "待改进", "min_score": 0}
        ]
    }
    return APIResponse(data=data)


@app.put("/api/electrical/performance/config",
         response_model=APIResponse,
         summary="更新权重配置",
         tags=["计算配置"])
async def update_config(config: dict):
    """
    更新电气工程师绩效评价权重配置
    """
    # 验证权重总和为100
    total_weight = sum(dim["weight"] for dim in config.get("weights", {}).values())
    if total_weight != 100:
        raise HTTPException(status_code=400, detail=f"权重总和必须为100，当前为{total_weight}")
    
    data = {
        "message": "配置已更新",
        "updated_at": datetime.now().isoformat()
    }
    return APIResponse(data=data)


# -------------------- 数据查询接口 --------------------

@app.get("/api/electrical/drawings",
         response_model=APIResponse,
         summary="图纸列表",
         tags=["数据查询"])
async def list_drawings(
    project_id: Optional[int] = Query(None),
    designer_id: Optional[int] = Query(None),
    drawing_type: Optional[DrawingType] = Query(None),
    review_status: Optional[ReviewStatus] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """
    查询电气图纸列表
    """
    data = {
        "total": 156,
        "page": page,
        "page_size": page_size,
        "list": [
            {
                "id": 10001,
                "drawing_no": "ELE-156-001",
                "drawing_name": "主电源柜原理图",
                "drawing_type": "电气原理图",
                "project_id": 156,
                "project_name": "XX检测设备",
                "designer_id": 1001,
                "designer_name": "王电气",
                "version": "V1.0",
                "review_status": "approved",
                "review_pass_first": True,
                "review_count": 1,
                "submit_date": "2024-11-15"
            }
        ]
    }
    return APIResponse(data=data)


@app.get("/api/electrical/plc-programs",
         response_model=APIResponse,
         summary="PLC程序列表",
         tags=["数据查询"])
async def list_plc_programs(
    project_id: Optional[int] = Query(None),
    developer_id: Optional[int] = Query(None),
    plc_brand: Optional[PLCBrand] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """
    查询PLC程序列表
    """
    data = {
        "total": 45,
        "list": [
            {
                "id": 20001,
                "program_name": "XX检测主控",
                "project_id": 156,
                "project_name": "XX检测设备",
                "plc_brand": "西门子",
                "plc_model": "S7-1500",
                "version": "V2.1",
                "developer_id": 1001,
                "developer_name": "王电气",
                "first_debug_pass": True,
                "debug_efficiency": 120,
                "stability_30days": 100,
                "deploy_date": "2024-11-15"
            }
        ]
    }
    return APIResponse(data=data)


@app.get("/api/electrical/faults",
         response_model=APIResponse,
         summary="故障记录",
         tags=["数据查询"])
async def list_faults(
    project_id: Optional[int] = Query(None),
    responsible_id: Optional[int] = Query(None),
    fault_type: Optional[FaultType] = Query(None),
    severity: Optional[Severity] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """
    查询电气故障记录
    """
    data = {
        "total": 23,
        "list": [
            {
                "id": 30001,
                "fault_no": "EF-2024-0125",
                "fault_title": "自动模式下伺服报警",
                "fault_type": "程序Bug",
                "severity": "一般",
                "project_id": 156,
                "project_name": "XX检测设备",
                "responsible_id": 1001,
                "responsible_name": "王电气",
                "status": "已解决",
                "resolve_hours": 2.5,
                "reported_at": "2024-11-10T09:30:00",
                "resolved_at": "2024-11-10T12:00:00"
            }
        ]
    }
    return APIResponse(data=data)


@app.get("/api/electrical/modules",
         response_model=APIResponse,
         summary="PLC模块库",
         tags=["数据查询"])
async def list_modules(
    module_type: Optional[ModuleType] = Query(None),
    plc_brand: Optional[PLCBrand] = Query(None),
    author_id: Optional[int] = Query(None),
    sort_by: str = Query("reuse_count", description="排序字段"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """
    查询PLC公共模块库
    """
    data = {
        "total": 68,
        "statistics": {
            "total_modules": 68,
            "total_reuse": 245,
            "contributors": 8
        },
        "list": [
            {
                "id": 40001,
                "module_name": "伺服定位FB",
                "module_type": "运动控制",
                "plc_brand": "西门子",
                "description": "支持绝对定位、相对定位、回原点",
                "author_id": 1001,
                "author_name": "王电气",
                "version": "V2.0",
                "reuse_count": 32,
                "rating": 4.9,
                "status": "published",
                "created_at": "2024-06-15"
            }
        ]
    }
    return APIResponse(data=data)


# ==================== 启动入口 ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
