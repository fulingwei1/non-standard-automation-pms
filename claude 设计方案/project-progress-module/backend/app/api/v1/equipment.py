# ===========================================
# 设备管理模块 API
# 非标自动化设备全生命周期管理
# ===========================================

from fastapi import APIRouter, Query, Path, Body, HTTPException, UploadFile, File
from typing import Optional, List
from datetime import date, datetime
from pydantic import BaseModel, Field
from enum import Enum

router = APIRouter(prefix="/api/v1/equipment", tags=["设备管理"])


# ===========================================
# 枚举定义
# ===========================================

class EquipmentStatus(str, Enum):
    DESIGNING = "designing"      # 设计中
    MANUFACTURING = "manufacturing"  # 制造中
    ASSEMBLING = "assembling"    # 装配中
    DEBUGGING = "debugging"      # 调试中
    TESTING = "testing"          # 测试中
    READY = "ready"              # 待发货
    SHIPPED = "shipped"          # 已发货
    INSTALLING = "installing"    # 安装中
    RUNNING = "running"          # 运行中
    MAINTENANCE = "maintenance"  # 维护中
    FAULT = "fault"              # 故障
    SCRAPPED = "scrapped"        # 报废


class MaintenanceType(str, Enum):
    PREVENTIVE = "preventive"    # 预防性维护
    CORRECTIVE = "corrective"    # 纠正性维护
    EMERGENCY = "emergency"      # 紧急维修
    UPGRADE = "upgrade"          # 升级改造


class FaultLevel(str, Enum):
    MINOR = "minor"              # 轻微
    MODERATE = "moderate"        # 中等
    MAJOR = "major"              # 严重
    CRITICAL = "critical"        # 紧急


# ===========================================
# 请求/响应模型
# ===========================================

class EquipmentCreate(BaseModel):
    """设备创建"""
    equipment_no: str = Field(..., description="设备编号")
    equipment_name: str = Field(..., description="设备名称")
    equipment_type: str = Field(..., description="设备类型")
    project_id: int = Field(..., description="所属项目ID")
    
    # 规格参数
    specifications: Optional[dict] = Field(None, description="规格参数")
    dimensions: Optional[str] = Field(None, description="外形尺寸 LxWxH")
    weight: Optional[float] = Field(None, description="重量(kg)")
    power: Optional[str] = Field(None, description="功率要求")
    
    # 客户信息
    customer_id: Optional[int] = None
    installation_address: Optional[str] = None
    
    # 设计信息
    designer_id: Optional[int] = None
    design_start_date: Optional[date] = None
    design_end_date: Optional[date] = None


class EquipmentUpdate(BaseModel):
    """设备更新"""
    equipment_name: Optional[str] = None
    status: Optional[EquipmentStatus] = None
    specifications: Optional[dict] = None
    current_location: Optional[str] = None
    remark: Optional[str] = None


class ComponentCreate(BaseModel):
    """部件创建"""
    component_no: str
    component_name: str
    component_type: str
    parent_id: Optional[int] = None  # 父部件ID
    
    # BOM信息
    material_code: Optional[str] = None
    quantity: int = 1
    unit: str = "件"
    
    # 制造信息
    make_or_buy: str = "buy"  # make/buy/outsource
    supplier_id: Optional[int] = None
    lead_time: Optional[int] = None


class MaintenanceRecordCreate(BaseModel):
    """维护记录创建"""
    maintenance_type: MaintenanceType
    maintenance_date: date
    description: str
    
    # 维护内容
    work_content: str
    replaced_parts: Optional[List[dict]] = None
    
    # 人员
    technician_id: int
    technician_name: str
    work_hours: float
    
    # 费用
    labor_cost: Optional[float] = None
    parts_cost: Optional[float] = None
    
    # 结果
    result: str  # completed/pending/failed
    next_maintenance_date: Optional[date] = None


class FaultReportCreate(BaseModel):
    """故障报告创建"""
    fault_time: datetime
    fault_level: FaultLevel
    fault_type: str
    fault_description: str
    
    # 现象
    symptoms: str
    error_codes: Optional[List[str]] = None
    
    # 报告人
    reporter_id: int
    reporter_name: str
    reporter_phone: Optional[str] = None
    
    # 影响
    production_impact: Optional[str] = None
    estimated_downtime: Optional[float] = None  # 小时


class FaultResolution(BaseModel):
    """故障解决"""
    root_cause: str
    solution: str
    resolution_time: datetime
    
    # 处理人
    resolver_id: int
    resolver_name: str
    
    # 更换部件
    replaced_parts: Optional[List[dict]] = None
    
    # 费用
    repair_cost: Optional[float] = None
    
    # 预防措施
    preventive_measures: Optional[str] = None


# ===========================================
# 设备管理接口
# ===========================================

@router.get("/list")
async def list_equipments(
    project_id: Optional[int] = Query(None, description="项目ID"),
    customer_id: Optional[int] = Query(None, description="客户ID"),
    status: Optional[EquipmentStatus] = Query(None, description="设备状态"),
    equipment_type: Optional[str] = Query(None, description="设备类型"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """
    获取设备列表
    
    返回字段：
    - 设备基本信息
    - 所属项目
    - 当前状态
    - 位置信息
    - 最近维护日期
    """
    # 模拟数据
    return {
        "total": 25,
        "items": [
            {
                "id": 1,
                "equipment_no": "EQ-2025-001",
                "equipment_name": "XX汽车传感器自动测试设备",
                "equipment_type": "自动化测试设备",
                "project_id": 1,
                "project_name": "XX汽车传感器测试设备项目",
                "customer_name": "XX汽车",
                "status": "debugging",
                "status_label": "调试中",
                "current_location": "调试车间-工位A3",
                "progress": 85,
                "design_completion": 100,
                "manufacture_completion": 95,
                "assembly_completion": 90,
                "debug_completion": 60,
                "last_maintenance_date": None,
                "created_at": "2024-11-15"
            },
            {
                "id": 2,
                "equipment_no": "EQ-2024-028",
                "equipment_name": "YY电池包EOL测试线",
                "equipment_type": "测试产线",
                "project_id": 2,
                "project_name": "YY新能源电池检测线项目",
                "customer_name": "YY新能源",
                "status": "running",
                "status_label": "运行中",
                "current_location": "YY新能源-生产车间",
                "progress": 100,
                "running_hours": 2580,
                "last_maintenance_date": "2024-12-15",
                "next_maintenance_date": "2025-01-15",
                "created_at": "2024-06-20"
            }
        ]
    }


@router.post("/create")
async def create_equipment(data: EquipmentCreate):
    """创建设备"""
    return {
        "id": 3,
        "equipment_no": data.equipment_no,
        "message": "设备创建成功"
    }


@router.get("/{equipment_id}")
async def get_equipment_detail(equipment_id: int = Path(..., description="设备ID")):
    """
    获取设备详情
    
    返回：
    - 基本信息
    - 规格参数
    - 部件清单(BOM)
    - 生产进度
    - 维护历史
    - 故障记录
    - 文档附件
    """
    return {
        "id": equipment_id,
        "equipment_no": "EQ-2025-001",
        "equipment_name": "XX汽车传感器自动测试设备",
        "equipment_type": "自动化测试设备",
        "status": "debugging",
        
        # 项目信息
        "project": {
            "id": 1,
            "project_no": "PRJ-2025-001",
            "project_name": "XX汽车传感器测试设备项目"
        },
        
        # 客户信息
        "customer": {
            "id": 1,
            "name": "XX汽车",
            "contact": "张经理",
            "phone": "13800138000",
            "installation_address": "XX汽车生产基地-测试车间"
        },
        
        # 规格参数
        "specifications": {
            "测试工位": "8工位",
            "节拍": "30秒/件",
            "精度": "±0.01mm",
            "电压": "AC380V",
            "气压": "0.5-0.7MPa"
        },
        "dimensions": "3200x2400x2100mm",
        "weight": 2500,
        "power": "15kW",
        
        # 进度信息
        "progress": {
            "overall": 85,
            "design": {"progress": 100, "status": "completed"},
            "manufacture": {"progress": 95, "status": "in_progress"},
            "assembly": {"progress": 90, "status": "in_progress"},
            "debug": {"progress": 60, "status": "in_progress"},
            "test": {"progress": 0, "status": "pending"}
        },
        
        # 时间节点
        "milestones": [
            {"name": "设计完成", "plan_date": "2024-12-15", "actual_date": "2024-12-18", "status": "completed"},
            {"name": "零件加工完成", "plan_date": "2025-01-10", "actual_date": None, "status": "in_progress"},
            {"name": "装配完成", "plan_date": "2025-01-25", "actual_date": None, "status": "pending"},
            {"name": "调试完成", "plan_date": "2025-02-10", "actual_date": None, "status": "pending"},
            {"name": "验收发货", "plan_date": "2025-02-20", "actual_date": None, "status": "pending"}
        ],
        
        # 关键部件
        "key_components": [
            {"id": 1, "name": "主控PLC", "model": "西门子S7-1500", "status": "installed"},
            {"id": 2, "name": "伺服驱动器", "model": "安川Σ-7", "status": "installed"},
            {"id": 3, "name": "视觉系统", "model": "康耐视In-Sight", "status": "调试中"},
            {"id": 4, "name": "机械手", "model": "发那科LR Mate", "status": "待安装"}
        ],
        
        # 统计
        "statistics": {
            "total_components": 256,
            "purchased_components": 180,
            "manufactured_components": 76,
            "total_work_hours": 1250,
            "total_cost": 450000
        }
    }


@router.put("/{equipment_id}")
async def update_equipment(
    equipment_id: int = Path(..., description="设备ID"),
    data: EquipmentUpdate = Body(...)
):
    """更新设备信息"""
    return {"message": "更新成功"}


@router.put("/{equipment_id}/status")
async def update_equipment_status(
    equipment_id: int = Path(..., description="设备ID"),
    status: EquipmentStatus = Body(..., embed=True),
    remark: Optional[str] = Body(None)
):
    """
    更新设备状态
    
    状态流转：
    designing → manufacturing → assembling → debugging → testing → ready → shipped → installing → running
    """
    return {"message": "状态更新成功", "new_status": status}


# ===========================================
# 部件管理接口
# ===========================================

@router.get("/{equipment_id}/components")
async def get_equipment_components(
    equipment_id: int = Path(..., description="设备ID"),
    component_type: Optional[str] = Query(None, description="部件类型"),
    status: Optional[str] = Query(None, description="状态")
):
    """获取设备部件清单(BOM树形结构)"""
    return {
        "equipment_id": equipment_id,
        "total_components": 256,
        "tree": [
            {
                "id": 1,
                "component_no": "COMP-001",
                "name": "机架总成",
                "type": "结构件",
                "quantity": 1,
                "status": "completed",
                "children": [
                    {"id": 11, "component_no": "COMP-001-01", "name": "底座", "type": "焊接件", "quantity": 1, "status": "completed"},
                    {"id": 12, "component_no": "COMP-001-02", "name": "立柱", "type": "机加件", "quantity": 4, "status": "completed"},
                    {"id": 13, "component_no": "COMP-001-03", "name": "横梁", "type": "机加件", "quantity": 2, "status": "in_progress"}
                ]
            },
            {
                "id": 2,
                "component_no": "COMP-002",
                "name": "传动系统",
                "type": "机械系统",
                "quantity": 1,
                "status": "in_progress",
                "children": [
                    {"id": 21, "component_no": "COMP-002-01", "name": "伺服电机", "type": "外购件", "quantity": 6, "status": "arrived"},
                    {"id": 22, "component_no": "COMP-002-02", "name": "减速机", "type": "外购件", "quantity": 6, "status": "arrived"},
                    {"id": 23, "component_no": "COMP-002-03", "name": "联轴器", "type": "外购件", "quantity": 6, "status": "in_transit"}
                ]
            },
            {
                "id": 3,
                "component_no": "COMP-003",
                "name": "电气系统",
                "type": "电气系统",
                "quantity": 1,
                "status": "in_progress",
                "children": [
                    {"id": 31, "component_no": "COMP-003-01", "name": "电气柜", "type": "自制件", "quantity": 1, "status": "assembling"},
                    {"id": 32, "component_no": "COMP-003-02", "name": "PLC控制器", "type": "外购件", "quantity": 1, "status": "installed"},
                    {"id": 33, "component_no": "COMP-003-03", "name": "触摸屏", "type": "外购件", "quantity": 1, "status": "arrived"}
                ]
            }
        ]
    }


@router.post("/{equipment_id}/components")
async def add_component(
    equipment_id: int = Path(..., description="设备ID"),
    data: ComponentCreate = Body(...)
):
    """添加部件"""
    return {"id": 100, "message": "部件添加成功"}


@router.put("/{equipment_id}/components/{component_id}/status")
async def update_component_status(
    equipment_id: int = Path(..., description="设备ID"),
    component_id: int = Path(..., description="部件ID"),
    status: str = Body(..., embed=True)
):
    """更新部件状态"""
    return {"message": "部件状态更新成功"}


# ===========================================
# 维护管理接口
# ===========================================

@router.get("/{equipment_id}/maintenance")
async def get_maintenance_records(
    equipment_id: int = Path(..., description="设备ID"),
    maintenance_type: Optional[MaintenanceType] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """获取维护记录"""
    return {
        "total": 5,
        "items": [
            {
                "id": 1,
                "maintenance_no": "MT-2024-001",
                "maintenance_type": "preventive",
                "maintenance_type_label": "预防性维护",
                "maintenance_date": "2024-12-15",
                "description": "季度保养",
                "work_content": "润滑、紧固、清洁、检测",
                "technician_name": "李工",
                "work_hours": 4,
                "parts_cost": 500,
                "labor_cost": 800,
                "result": "completed",
                "next_maintenance_date": "2025-03-15"
            }
        ],
        "statistics": {
            "total_count": 5,
            "total_cost": 12500,
            "avg_interval_days": 45,
            "next_due": "2025-01-15"
        }
    }


@router.post("/{equipment_id}/maintenance")
async def create_maintenance_record(
    equipment_id: int = Path(..., description="设备ID"),
    data: MaintenanceRecordCreate = Body(...)
):
    """创建维护记录"""
    return {"id": 10, "maintenance_no": "MT-2025-001", "message": "维护记录创建成功"}


@router.get("/{equipment_id}/maintenance/plan")
async def get_maintenance_plan(
    equipment_id: int = Path(..., description="设备ID")
):
    """获取维护计划"""
    return {
        "equipment_id": equipment_id,
        "maintenance_items": [
            {
                "item": "润滑保养",
                "interval_days": 30,
                "last_date": "2024-12-15",
                "next_date": "2025-01-14",
                "days_remaining": 11,
                "status": "upcoming"
            },
            {
                "item": "电气检测",
                "interval_days": 90,
                "last_date": "2024-10-15",
                "next_date": "2025-01-13",
                "days_remaining": 10,
                "status": "upcoming"
            },
            {
                "item": "精度校准",
                "interval_days": 180,
                "last_date": "2024-07-15",
                "next_date": "2025-01-11",
                "days_remaining": 8,
                "status": "warning"
            }
        ]
    }


# ===========================================
# 故障管理接口
# ===========================================

@router.get("/{equipment_id}/faults")
async def get_fault_records(
    equipment_id: int = Path(..., description="设备ID"),
    fault_level: Optional[FaultLevel] = Query(None),
    status: Optional[str] = Query(None),  # open/resolved/closed
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """获取故障记录"""
    return {
        "total": 3,
        "items": [
            {
                "id": 1,
                "fault_no": "FLT-2024-001",
                "fault_time": "2024-12-20 14:30:00",
                "fault_level": "moderate",
                "fault_level_label": "中等",
                "fault_type": "机械故障",
                "fault_description": "X轴伺服电机异响",
                "symptoms": "运行时有异常噪音，定位精度下降",
                "reporter_name": "张操作员",
                "status": "resolved",
                "resolution_time": "2024-12-20 18:30:00",
                "downtime_hours": 4,
                "root_cause": "轴承磨损",
                "solution": "更换伺服电机轴承",
                "repair_cost": 1500,
                "resolver_name": "李工"
            }
        ],
        "statistics": {
            "total_faults": 3,
            "open_faults": 0,
            "mtbf_hours": 850,  # 平均故障间隔
            "mttr_hours": 3.5,  # 平均修复时间
            "availability": 99.2  # 可用率%
        }
    }


@router.post("/{equipment_id}/faults")
async def report_fault(
    equipment_id: int = Path(..., description="设备ID"),
    data: FaultReportCreate = Body(...)
):
    """报告故障"""
    return {
        "id": 10,
        "fault_no": "FLT-2025-001",
        "message": "故障报告已提交，已通知维护人员"
    }


@router.post("/{equipment_id}/faults/{fault_id}/resolve")
async def resolve_fault(
    equipment_id: int = Path(..., description="设备ID"),
    fault_id: int = Path(..., description="故障ID"),
    data: FaultResolution = Body(...)
):
    """解决故障"""
    return {"message": "故障已解决"}


# ===========================================
# 文档附件接口
# ===========================================

@router.get("/{equipment_id}/documents")
async def get_equipment_documents(
    equipment_id: int = Path(..., description="设备ID"),
    doc_type: Optional[str] = Query(None, description="文档类型")
):
    """获取设备相关文档"""
    return {
        "categories": [
            {
                "type": "design",
                "type_label": "设计文档",
                "documents": [
                    {"id": 1, "name": "总体设计方案.pdf", "version": "V1.2", "size": "2.5MB", "updated_at": "2024-11-20"},
                    {"id": 2, "name": "电气原理图.dwg", "version": "V1.1", "size": "5.2MB", "updated_at": "2024-12-01"}
                ]
            },
            {
                "type": "drawing",
                "type_label": "图纸",
                "documents": [
                    {"id": 3, "name": "机架装配图.dwg", "version": "V1.0", "size": "8.5MB", "updated_at": "2024-11-25"},
                    {"id": 4, "name": "零件图册.pdf", "version": "V1.0", "size": "15.2MB", "updated_at": "2024-12-05"}
                ]
            },
            {
                "type": "manual",
                "type_label": "操作手册",
                "documents": [
                    {"id": 5, "name": "操作说明书.pdf", "version": "V1.0", "size": "3.2MB", "updated_at": "2024-12-10"},
                    {"id": 6, "name": "维护保养手册.pdf", "version": "V1.0", "size": "2.1MB", "updated_at": "2024-12-10"}
                ]
            }
        ]
    }


@router.post("/{equipment_id}/documents/upload")
async def upload_document(
    equipment_id: int = Path(..., description="设备ID"),
    doc_type: str = Query(..., description="文档类型"),
    file: UploadFile = File(...)
):
    """上传文档"""
    return {
        "id": 10,
        "filename": file.filename,
        "message": "文档上传成功"
    }


# ===========================================
# 统计分析接口
# ===========================================

@router.get("/statistics/overview")
async def get_equipment_statistics():
    """获取设备统计概览"""
    return {
        "total_equipments": 45,
        "by_status": {
            "designing": 3,
            "manufacturing": 5,
            "assembling": 4,
            "debugging": 6,
            "testing": 2,
            "ready": 1,
            "shipped": 2,
            "running": 20,
            "maintenance": 1,
            "fault": 1
        },
        "by_type": [
            {"type": "自动化测试设备", "count": 18},
            {"type": "装配线", "count": 12},
            {"type": "检测设备", "count": 10},
            {"type": "其他", "count": 5}
        ],
        "running_statistics": {
            "total_running": 20,
            "avg_availability": 98.5,
            "total_running_hours": 125000,
            "faults_this_month": 3
        },
        "maintenance_statistics": {
            "due_this_week": 5,
            "overdue": 2,
            "completed_this_month": 12
        }
    }


@router.get("/statistics/reliability")
async def get_reliability_statistics(
    start_date: date = Query(...),
    end_date: date = Query(...)
):
    """获取设备可靠性统计"""
    return {
        "period": f"{start_date} 至 {end_date}",
        "overall": {
            "mtbf": 850,  # 平均故障间隔(小时)
            "mttr": 3.2,  # 平均修复时间(小时)
            "availability": 99.2,  # 可用率(%)
            "oee": 85.5  # 设备综合效率(%)
        },
        "by_equipment": [
            {"equipment_name": "YY电池包EOL测试线", "mtbf": 1200, "mttr": 2.5, "availability": 99.5},
            {"equipment_name": "ZZ医疗器械测试系统", "mtbf": 950, "mttr": 3.0, "availability": 99.3},
            {"equipment_name": "AA自动装配线", "mtbf": 720, "mttr": 4.5, "availability": 98.8}
        ],
        "fault_analysis": {
            "by_type": [
                {"type": "机械故障", "count": 8, "percent": 40},
                {"type": "电气故障", "count": 6, "percent": 30},
                {"type": "软件故障", "count": 4, "percent": 20},
                {"type": "其他", "count": 2, "percent": 10}
            ],
            "by_level": [
                {"level": "轻微", "count": 10, "percent": 50},
                {"level": "中等", "count": 6, "percent": 30},
                {"level": "严重", "count": 3, "percent": 15},
                {"level": "紧急", "count": 1, "percent": 5}
            ]
        }
    }
