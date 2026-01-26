"""
物料保障模块 API
齐套分析、缺料预警、缺料上报、到货跟踪、物料替代
"""
from fastapi import APIRouter, Query, Body, UploadFile, File
from typing import Optional, List, Dict
from datetime import datetime, date, timedelta

router = APIRouter(prefix="/material", tags=["物料保障"])


# ==================== 物料保障看板 ====================

@router.get("/dashboard", summary="物料保障看板")
async def get_material_dashboard():
    """获取物料保障看板数据"""
    return {
        "code": 200,
        "data": {
            "overview": {
                "today_work_orders": 45,
                "kit_complete": 38,
                "kit_partial": 4,
                "kit_shortage": 3,
                "kit_rate": 84.4,
                "urgent_shortage": 3,
                "pending_arrival": 12
            },
            "kit_trend": [
                {"date": "01-01", "rate": 82},
                {"date": "01-02", "rate": 85},
                {"date": "01-03", "rate": 84}
            ],
            "urgent_shortages": [
                {
                    "id": 1,
                    "work_order_no": "WO-0103-001",
                    "project_name": "XX汽车传感器测试设备",
                    "material_name": "传动轴",
                    "material_code": "M-0123",
                    "shortage_qty": 1,
                    "impact": "装配停工",
                    "status": "handling",
                    "expected_arrival": "今天14:00",
                    "alert_level": "level3"
                },
                {
                    "id": 2,
                    "work_order_no": "WO-0103-005",
                    "project_name": "YY新能源电池检测线",
                    "material_name": "伺服控制器",
                    "material_code": "M-0456",
                    "shortage_qty": 2,
                    "impact": "电气装配延后",
                    "status": "handling",
                    "expected_arrival": "明天上午",
                    "alert_level": "level2"
                },
                {
                    "id": 3,
                    "work_order_no": "WO-0103-008",
                    "project_name": "ZZ医疗器械测试系统",
                    "material_name": "M8内六角螺丝",
                    "material_code": "M-0789",
                    "shortage_qty": 50,
                    "impact": "可用替代料",
                    "status": "substituting",
                    "alert_level": "level1"
                }
            ],
            "today_arrivals": [
                {"id": 1, "material_name": "伺服电机", "qty": 2, "supplier": "XX电机", "expected_time": "10:00", "status": "shipped"},
                {"id": 2, "material_name": "传动轴", "qty": 1, "supplier": "YY机械", "expected_time": "14:00", "status": "shipped"},
                {"id": 3, "material_name": "PLC模块", "qty": 3, "supplier": "ZZ自动化", "expected_time": "16:00", "status": "confirmed"}
            ],
            "shortage_by_reason": [
                {"reason": "采购延迟", "count": 5, "percent": 42},
                {"reason": "供应商交期", "count": 4, "percent": 33},
                {"reason": "库存不准", "count": 2, "percent": 17},
                {"reason": "设计变更", "count": 1, "percent": 8}
            ],
            "alerts_summary": {
                "level1": 5,
                "level2": 3,
                "level3": 2,
                "level4": 0
            }
        }
    }


# ==================== 齐套分析 ====================

@router.get("/kit-check/work-orders", summary="工单齐套列表")
async def get_work_order_kit_list(
    kit_status: Optional[str] = Query(None, description="齐套状态:complete/partial/shortage"),
    workshop_id: Optional[int] = Query(None),
    project_id: Optional[int] = Query(None),
    plan_date: Optional[date] = Query(None, description="计划开工日期"),
    page: int = Query(1),
    page_size: int = Query(20)
):
    """获取工单齐套列表"""
    work_orders = [
        {
            "id": 1,
            "work_order_no": "WO-0103-001",
            "task_name": "XX项目-支架装配",
            "project_name": "XX汽车传感器测试设备",
            "workshop_name": "装配车间",
            "plan_start_date": "2025-01-03",
            "total_items": 12,
            "fulfilled_items": 10,
            "shortage_items": 2,
            "kit_rate": 83.3,
            "kit_status": "partial",
            "kit_status_label": "部分齐套",
            "shortage_materials": [
                {"material_code": "M-0123", "material_name": "传动轴", "required": 1, "available": 0, "shortage": 1},
                {"material_code": "M-0456", "material_name": "联轴器", "required": 2, "available": 1, "shortage": 1}
            ],
            "last_check_time": "2025-01-03 08:00:00"
        },
        {
            "id": 2,
            "work_order_no": "WO-0103-002",
            "task_name": "XX项目-底座装配",
            "project_name": "XX汽车传感器测试设备",
            "workshop_name": "装配车间",
            "plan_start_date": "2025-01-03",
            "total_items": 8,
            "fulfilled_items": 8,
            "shortage_items": 0,
            "kit_rate": 100,
            "kit_status": "complete",
            "kit_status_label": "齐套",
            "shortage_materials": [],
            "last_check_time": "2025-01-03 08:00:00"
        },
        {
            "id": 3,
            "work_order_no": "WO-0103-003",
            "task_name": "YY项目-电气柜装配",
            "project_name": "YY新能源电池检测线",
            "workshop_name": "装配车间",
            "plan_start_date": "2025-01-04",
            "total_items": 25,
            "fulfilled_items": 20,
            "shortage_items": 5,
            "kit_rate": 80,
            "kit_status": "shortage",
            "kit_status_label": "缺料",
            "shortage_materials": [
                {"material_code": "M-0789", "material_name": "伺服控制器", "required": 2, "available": 0, "shortage": 2}
            ],
            "last_check_time": "2025-01-03 08:00:00"
        }
    ]
    
    # 过滤
    if kit_status:
        work_orders = [w for w in work_orders if w["kit_status"] == kit_status]
    
    return {
        "code": 200,
        "data": {
            "work_orders": work_orders,
            "total": len(work_orders),
            "summary": {
                "total": 45,
                "complete": 38,
                "partial": 4,
                "shortage": 3
            }
        }
    }


@router.get("/kit-check/work-orders/{work_order_id}", summary="工单齐套详情")
async def get_work_order_kit_detail(work_order_id: int):
    """获取工单齐套详情"""
    return {
        "code": 200,
        "data": {
            "work_order_id": work_order_id,
            "work_order_no": "WO-0103-001",
            "task_name": "XX项目-支架装配",
            "project_name": "XX汽车传感器测试设备",
            "plan_start_date": "2025-01-03",
            "assigned_name": "李师傅",
            
            "kit_summary": {
                "total_items": 12,
                "fulfilled_items": 10,
                "shortage_items": 2,
                "in_transit_items": 1,
                "kit_rate": 83.3,
                "kit_status": "partial"
            },
            
            "material_list": [
                {"material_code": "M-001", "material_name": "底板", "spec": "500x400x20", "required": 1, "available": 1, "allocated": 1, "shortage": 0, "status": "fulfilled"},
                {"material_code": "M-002", "material_name": "支架", "spec": "L型", "required": 4, "available": 4, "allocated": 4, "shortage": 0, "status": "fulfilled"},
                {"material_code": "M-003", "material_name": "螺栓M10", "spec": "M10x30", "required": 20, "available": 50, "allocated": 20, "shortage": 0, "status": "fulfilled"},
                {"material_code": "M-0123", "material_name": "传动轴", "spec": "D30x200", "required": 1, "available": 0, "allocated": 0, "shortage": 1, "status": "shortage", "expected_arrival": "2025-01-03 14:00", "po_no": "PO-2025-0089"},
                {"material_code": "M-0456", "material_name": "联轴器", "spec": "D30", "required": 2, "available": 1, "allocated": 1, "shortage": 1, "status": "partial", "substitute_available": True, "substitute_code": "M-0457"}
            ],
            
            "check_history": [
                {"check_time": "2025-01-03 08:00:00", "kit_rate": 83.3, "checker": "系统自动"},
                {"check_time": "2025-01-02 17:00:00", "kit_rate": 75.0, "checker": "系统自动"}
            ]
        }
    }


@router.post("/kit-check/work-orders/{work_order_id}/check", summary="执行齐套检查")
async def check_work_order_kit(work_order_id: int, current_user_id: int = Query(1)):
    """手动执行工单齐套检查"""
    return {
        "code": 200,
        "message": "齐套检查完成",
        "data": {
            "work_order_id": work_order_id,
            "check_time": datetime.now().isoformat(),
            "kit_rate": 83.3,
            "kit_status": "partial",
            "shortage_items": 2,
            "shortage_list": [
                {"material_code": "M-0123", "material_name": "传动轴", "shortage": 1},
                {"material_code": "M-0456", "material_name": "联轴器", "shortage": 1}
            ]
        }
    }


@router.post("/kit-check/work-orders/{work_order_id}/confirm", summary="开工前齐套确认")
async def confirm_work_order_kit(
    work_order_id: int,
    confirm_type: str = Body(..., description="确认类型: start_now/wait/partial_start"),
    remarks: str = Body(""),
    current_user_id: int = Query(101),
    current_user_name: str = Query("工人")
):
    """工人开工前确认齐套状态"""
    return {
        "code": 200,
        "message": "确认成功",
        "data": {
            "work_order_id": work_order_id,
            "confirm_type": confirm_type,
            "confirm_time": datetime.now().isoformat(),
            "confirmed_by": current_user_name
        }
    }


# ==================== 缺料预警 ====================

@router.get("/alerts", summary="缺料预警列表")
async def get_shortage_alerts(
    alert_level: Optional[str] = Query(None, description="预警级别:level1/level2/level3/level4"),
    status: Optional[str] = Query(None, description="状态:pending/handling/resolved/escalated"),
    project_id: Optional[int] = Query(None),
    page: int = Query(1),
    page_size: int = Query(20)
):
    """获取缺料预警列表"""
    alerts = [
        {
            "id": 1,
            "alert_no": "ALT-20250103-001",
            "alert_level": "level3",
            "alert_level_label": "三级(紧急)",
            "project_name": "XX汽车传感器测试设备",
            "work_order_no": "WO-0103-001",
            "material_code": "M-0123",
            "material_name": "传动轴",
            "shortage_qty": 1,
            "required_date": "2025-01-03",
            "impact": "装配工序停工等待",
            "status": "handling",
            "status_label": "处理中",
            "handler_name": "采购张工",
            "handle_plan": "已联系供应商加急，预计14:00到货",
            "created_at": "2025-01-03 07:00:00",
            "response_deadline": "2025-01-03 08:00:00"
        },
        {
            "id": 2,
            "alert_no": "ALT-20250103-002",
            "alert_level": "level2",
            "alert_level_label": "二级(警告)",
            "project_name": "YY新能源电池检测线",
            "work_order_no": "WO-0104-003",
            "material_code": "M-0456",
            "material_name": "伺服控制器",
            "shortage_qty": 2,
            "required_date": "2025-01-04",
            "impact": "电气装配将延后",
            "status": "handling",
            "status_label": "处理中",
            "handler_name": "采购李工",
            "handle_plan": "供应商已发货，预计明天上午到达",
            "created_at": "2025-01-02 16:00:00"
        },
        {
            "id": 3,
            "alert_no": "ALT-20250103-003",
            "alert_level": "level1",
            "alert_level_label": "一级(提醒)",
            "project_name": "ZZ医疗器械测试系统",
            "work_order_no": "WO-0106-001",
            "material_code": "M-0789",
            "material_name": "M8内六角螺丝",
            "shortage_qty": 50,
            "required_date": "2025-01-06",
            "impact": "有替代料可用",
            "status": "pending",
            "status_label": "待处理",
            "created_at": "2025-01-03 08:00:00"
        }
    ]
    
    return {"code": 200, "data": {"alerts": alerts, "total": len(alerts)}}


@router.get("/alerts/{alert_id}", summary="预警详情")
async def get_alert_detail(alert_id: int):
    """获取预警详情"""
    return {
        "code": 200,
        "data": {
            "id": alert_id,
            "alert_no": "ALT-20250103-001",
            "alert_level": "level3",
            
            "project_id": 1,
            "project_name": "XX汽车传感器测试设备",
            "work_order_id": 1,
            "work_order_no": "WO-0103-001",
            "task_name": "支架装配",
            
            "material_code": "M-0123",
            "material_name": "传动轴",
            "specification": "D30x200",
            "shortage_qty": 1,
            "required_date": "2025-01-03",
            
            "impact_description": "该物料为装配关键件，缺料将导致装配工序无法开工，影响项目整体进度",
            "affected_process": "机械装配",
            "affected_worker": "李师傅",
            
            "inventory_info": {
                "current_stock": 0,
                "allocated": 0,
                "available": 0
            },
            
            "purchase_info": {
                "po_no": "PO-2025-0089",
                "supplier": "YY机械",
                "order_qty": 2,
                "order_date": "2024-12-28",
                "promised_date": "2025-01-02",
                "expected_date": "2025-01-03",
                "delay_days": 1,
                "status": "shipped"
            },
            
            "substitute_info": {
                "has_substitute": False,
                "substitute_materials": []
            },
            
            "handle_history": [
                {"time": "2025-01-03 07:00:00", "action": "系统自动生成预警", "operator": "系统"},
                {"time": "2025-01-03 07:05:00", "action": "预警升级至三级", "operator": "系统"},
                {"time": "2025-01-03 07:10:00", "action": "采购张工开始处理", "operator": "采购张工"},
                {"time": "2025-01-03 07:30:00", "action": "已联系供应商确认，预计14:00送达", "operator": "采购张工"}
            ],
            
            "status": "handling",
            "handler_id": 201,
            "handler_name": "采购张工",
            "handle_plan": "已联系供应商加急配送",
            "expected_resolve_time": "2025-01-03 14:00:00",
            
            "created_at": "2025-01-03 07:00:00"
        }
    }


@router.post("/alerts/{alert_id}/handle", summary="处理预警")
async def handle_alert(
    alert_id: int,
    handle_plan: str = Body(...),
    expected_resolve_time: datetime = Body(None),
    current_user_id: int = Query(1),
    current_user_name: str = Query("处理人")
):
    """开始处理预警"""
    return {
        "code": 200,
        "message": "已开始处理",
        "data": {
            "alert_id": alert_id,
            "status": "handling",
            "handler_name": current_user_name,
            "handle_time": datetime.now().isoformat()
        }
    }


@router.post("/alerts/{alert_id}/escalate", summary="升级预警")
async def escalate_alert(
    alert_id: int,
    escalate_reason: str = Body(...),
    current_user_id: int = Query(1)
):
    """升级预警级别"""
    return {
        "code": 200,
        "message": "预警已升级",
        "data": {
            "alert_id": alert_id,
            "new_level": "level3",
            "escalate_time": datetime.now().isoformat()
        }
    }


@router.post("/alerts/{alert_id}/resolve", summary="解决预警")
async def resolve_alert(
    alert_id: int,
    resolve_method: str = Body(..., description="解决方式:arrived/substitute/other"),
    resolve_description: str = Body(...),
    current_user_id: int = Query(1)
):
    """解决预警"""
    return {
        "code": 200,
        "message": "预警已解决",
        "data": {
            "alert_id": alert_id,
            "status": "resolved",
            "resolve_time": datetime.now().isoformat()
        }
    }


# ==================== 缺料上报(工人端) ====================

@router.get("/shortage-reports", summary="缺料上报列表")
async def get_shortage_reports(
    status: Optional[str] = Query(None),
    reporter_id: Optional[int] = Query(None),
    work_order_id: Optional[int] = Query(None),
    page: int = Query(1),
    page_size: int = Query(20)
):
    """获取缺料上报列表"""
    reports = [
        {
            "id": 1,
            "report_no": "SR-20250103-001",
            "work_order_no": "WO-0103-001",
            "project_name": "XX汽车传感器测试设备",
            "material_name": "传动轴",
            "shortage_qty": 1,
            "urgency": "critical",
            "urgency_label": "非常紧急",
            "reporter_name": "李师傅",
            "report_time": "2025-01-03 08:35:00",
            "status": "handling",
            "status_label": "处理中",
            "handler_name": "仓管王工",
            "handle_progress": "已确认库存为0，采购正在跟催供应商"
        },
        {
            "id": 2,
            "report_no": "SR-20250103-002",
            "work_order_no": "WO-0103-005",
            "project_name": "YY新能源电池检测线",
            "material_name": "航空插头",
            "shortage_qty": 5,
            "urgency": "urgent",
            "urgency_label": "紧急",
            "reporter_name": "张师傅",
            "report_time": "2025-01-03 09:20:00",
            "status": "resolved",
            "status_label": "已解决",
            "handler_name": "仓管王工",
            "resolve_result": "从其他项目调拨5件"
        }
    ]
    return {"code": 200, "data": {"reports": reports, "total": len(reports)}}


@router.post("/shortage-reports", summary="提交缺料上报")
async def create_shortage_report(
    work_order_id: int = Body(...),
    material_code: str = Body(None),
    material_name: str = Body(...),
    shortage_qty: float = Body(...),
    urgency: str = Body("normal", description="紧急程度:normal/urgent/critical"),
    description: str = Body(""),
    current_user_id: int = Query(101),
    current_user_name: str = Query("工人")
):
    """工人提交缺料上报"""
    report_no = f"SR-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    return {
        "code": 200,
        "message": "缺料上报成功，相关人员已收到通知",
        "data": {
            "id": 1,
            "report_no": report_no,
            "status": "reported",
            "notified_users": ["仓管王工", "车间李主管", "采购张工"]
        }
    }


@router.post("/shortage-reports/{report_id}/upload-image", summary="上传缺料图片")
async def upload_shortage_image(report_id: int, file: UploadFile = File(...)):
    """上传缺料相关图片"""
    return {
        "code": 200,
        "message": "图片上传成功",
        "data": {
            "report_id": report_id,
            "image_url": f"/uploads/shortage/{report_id}_{file.filename}"
        }
    }


@router.get("/shortage-reports/{report_id}", summary="上报详情")
async def get_shortage_report_detail(report_id: int):
    """获取缺料上报详情"""
    return {
        "code": 200,
        "data": {
            "id": report_id,
            "report_no": "SR-20250103-001",
            "work_order_id": 1,
            "work_order_no": "WO-0103-001",
            "task_name": "支架装配",
            "project_name": "XX汽车传感器测试设备",
            
            "material_code": "M-0123",
            "material_name": "传动轴",
            "specification": "D30x200",
            "shortage_qty": 1,
            "urgency": "critical",
            
            "reporter_id": 101,
            "reporter_name": "李师傅",
            "report_time": "2025-01-03 08:35:00",
            "description": "仓库说没有库存了，我这边装配工序需要用",
            "images": [],
            
            "status": "handling",
            "handler_id": 301,
            "handler_name": "仓管王工",
            "handle_time": "2025-01-03 08:40:00",
            "handle_method": "确认库存为0，已通知采购跟催",
            
            "progress_updates": [
                {"time": "2025-01-03 08:35:00", "content": "李师傅提交缺料上报", "operator": "李师傅"},
                {"time": "2025-01-03 08:36:00", "content": "系统通知仓管员、车间主管、采购员", "operator": "系统"},
                {"time": "2025-01-03 08:40:00", "content": "仓管王工确认库存为0", "operator": "仓管王工"},
                {"time": "2025-01-03 08:45:00", "content": "采购张工确认供应商预计14:00送达", "operator": "采购张工"}
            ],
            
            "inventory_check": {
                "current_stock": 0,
                "other_locations": [],
                "in_transit": {"po_no": "PO-2025-0089", "qty": 2, "expected": "2025-01-03 14:00"}
            }
        }
    }


@router.post("/shortage-reports/{report_id}/handle", summary="处理上报")
async def handle_shortage_report(
    report_id: int,
    handle_method: str = Body(...),
    current_user_id: int = Query(1),
    current_user_name: str = Query("处理人")
):
    """开始处理缺料上报"""
    return {
        "code": 200,
        "message": "已开始处理",
        "data": {"report_id": report_id, "status": "handling"}
    }


@router.post("/shortage-reports/{report_id}/resolve", summary="解决上报")
async def resolve_shortage_report(
    report_id: int,
    resolve_method: str = Body(..., description="解决方式:arrived/substitute/transfer/other"),
    resolve_description: str = Body(...),
    notify_reporter: bool = Body(True),
    current_user_id: int = Query(1)
):
    """解决缺料上报"""
    return {
        "code": 200,
        "message": "已解决，工人已收到通知",
        "data": {
            "report_id": report_id,
            "status": "resolved",
            "resolve_time": datetime.now().isoformat()
        }
    }


@router.get("/my-shortage-reports", summary="[工人]我的上报记录")
async def get_my_shortage_reports(current_user_id: int = Query(101)):
    """工人查看自己的缺料上报记录"""
    reports = [
        {
            "id": 1,
            "report_no": "SR-20250103-001",
            "work_order_no": "WO-0103-001",
            "material_name": "传动轴",
            "shortage_qty": 1,
            "report_time": "2025-01-03 08:35:00",
            "status": "handling",
            "status_label": "处理中",
            "latest_progress": "采购确认预计14:00到货"
        }
    ]
    return {"code": 200, "data": reports}


# ==================== 到货跟踪 ====================

@router.get("/arrivals", summary="到货跟踪列表")
async def get_arrival_tracking(
    status: Optional[str] = Query(None, description="状态:ordered/confirmed/shipped/arrived/delayed"),
    expected_date: Optional[date] = Query(None),
    is_delayed: Optional[bool] = Query(None),
    supplier_id: Optional[int] = Query(None),
    page: int = Query(1),
    page_size: int = Query(20)
):
    """获取到货跟踪列表"""
    arrivals = [
        {
            "id": 1,
            "po_no": "PO-2025-0089",
            "material_code": "M-0123",
            "material_name": "传动轴",
            "specification": "D30x200",
            "order_qty": 2,
            "supplier_name": "YY机械",
            "promised_date": "2025-01-02",
            "expected_date": "2025-01-03",
            "status": "shipped",
            "status_label": "已发货",
            "is_delayed": True,
            "delay_days": 1,
            "related_projects": ["XX汽车传感器测试设备"],
            "urgency": "high"
        },
        {
            "id": 2,
            "po_no": "PO-2025-0092",
            "material_code": "M-0456",
            "material_name": "伺服控制器",
            "specification": "2kW",
            "order_qty": 3,
            "supplier_name": "ZZ自动化",
            "promised_date": "2025-01-04",
            "expected_date": "2025-01-04",
            "status": "confirmed",
            "status_label": "已确认",
            "is_delayed": False,
            "related_projects": ["YY新能源电池检测线"],
            "urgency": "normal"
        }
    ]
    return {"code": 200, "data": {"arrivals": arrivals, "total": len(arrivals)}}


@router.get("/arrivals/{arrival_id}", summary="到货详情")
async def get_arrival_detail(arrival_id: int):
    """获取到货详情"""
    return {
        "code": 200,
        "data": {
            "id": arrival_id,
            "po_no": "PO-2025-0089",
            "po_line_no": 1,
            
            "material_code": "M-0123",
            "material_name": "传动轴",
            "specification": "D30x200",
            "unit": "件",
            "order_qty": 2,
            
            "supplier_id": 1,
            "supplier_name": "YY机械",
            "supplier_contact": "王经理 138xxxx8888",
            
            "order_date": "2024-12-28",
            "promised_date": "2025-01-02",
            "expected_date": "2025-01-03",
            "actual_date": None,
            
            "status": "shipped",
            "is_delayed": True,
            "delay_days": 1,
            "delay_reason": "供应商生产排期延迟",
            
            "shipping_info": {
                "carrier": "顺丰快递",
                "tracking_no": "SF1234567890",
                "shipped_time": "2025-01-02 16:00:00"
            },
            
            "related_work_orders": [
                {"work_order_no": "WO-0103-001", "task_name": "支架装配", "required_qty": 1, "project_name": "XX汽车传感器测试设备"}
            ],
            
            "follow_up_history": [
                {"time": "2024-12-30", "action": "首次跟催", "result": "供应商确认1月2日发货", "operator": "采购张工"},
                {"time": "2025-01-02", "action": "确认发货", "result": "已发货，预计明天到达", "operator": "采购张工"}
            ]
        }
    }


@router.put("/arrivals/{arrival_id}/status", summary="更新到货状态")
async def update_arrival_status(
    arrival_id: int,
    status: str = Body(...),
    expected_date: date = Body(None),
    remarks: str = Body(""),
    current_user_id: int = Query(1)
):
    """更新到货状态"""
    return {
        "code": 200,
        "message": "状态已更新",
        "data": {"arrival_id": arrival_id, "status": status}
    }


@router.post("/arrivals/{arrival_id}/confirm", summary="确认到货")
async def confirm_arrival(
    arrival_id: int,
    received_qty: float = Body(...),
    quality_status: str = Body("qualified", description="质量状态:qualified/unqualified/partial"),
    remarks: str = Body(""),
    current_user_id: int = Query(1)
):
    """仓管确认到货"""
    return {
        "code": 200,
        "message": "到货确认成功，相关人员已收到通知",
        "data": {
            "arrival_id": arrival_id,
            "status": "arrived",
            "received_qty": received_qty,
            "receive_time": datetime.now().isoformat()
        }
    }


# ==================== 物料替代 ====================

@router.get("/substitutions", summary="物料替代列表")
async def get_substitutions(
    status: Optional[str] = Query(None),
    page: int = Query(1),
    page_size: int = Query(20)
):
    """获取物料替代列表"""
    substitutions = [
        {
            "id": 1,
            "substitution_no": "SUB-20250103-001",
            "work_order_no": "WO-0103-008",
            "project_name": "ZZ医疗器械测试系统",
            "original_material": "M8内六角螺丝(M-0789)",
            "substitute_material": "M8内六角螺丝-不锈钢(M-0790)",
            "qty": 50,
            "applicant_name": "装配主管",
            "apply_time": "2025-01-03 09:00:00",
            "status": "pending",
            "status_label": "待审批"
        }
    ]
    return {"code": 200, "data": {"substitutions": substitutions, "total": len(substitutions)}}


@router.post("/substitutions", summary="申请物料替代")
async def create_substitution(
    work_order_id: int = Body(...),
    original_material_code: str = Body(...),
    substitute_material_code: str = Body(...),
    qty: float = Body(...),
    apply_reason: str = Body(...),
    current_user_id: int = Query(1),
    current_user_name: str = Query("申请人")
):
    """申请物料替代"""
    substitution_no = f"SUB-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    return {
        "code": 200,
        "message": "替代申请已提交",
        "data": {"id": 1, "substitution_no": substitution_no, "status": "pending"}
    }


@router.post("/substitutions/{substitution_id}/approve", summary="审批物料替代")
async def approve_substitution(
    substitution_id: int,
    approved: bool = Body(...),
    comment: str = Body(""),
    current_user_id: int = Query(1)
):
    """审批物料替代"""
    return {
        "code": 200,
        "message": "审批完成",
        "data": {
            "substitution_id": substitution_id,
            "status": "approved" if approved else "rejected"
        }
    }


@router.get("/substitute-materials/{material_code}", summary="查询可替代物料")
async def get_substitute_materials(material_code: str):
    """查询物料的可替代料"""
    return {
        "code": 200,
        "data": {
            "original_material": {
                "code": material_code,
                "name": "M8内六角螺丝",
                "specification": "M8x20 碳钢"
            },
            "substitutes": [
                {
                    "code": "M-0790",
                    "name": "M8内六角螺丝-不锈钢",
                    "specification": "M8x20 304不锈钢",
                    "available_qty": 200,
                    "price_diff": 0.5,
                    "compatibility": "完全兼容"
                },
                {
                    "code": "M-0791",
                    "name": "M8内六角螺丝-镀锌",
                    "specification": "M8x20 镀锌",
                    "available_qty": 150,
                    "price_diff": 0.2,
                    "compatibility": "完全兼容"
                }
            ]
        }
    }


# ==================== 统计分析 ====================

@router.get("/reports/kit-rate", summary="齐套率报表")
async def get_kit_rate_report(
    start_date: date = Query(...),
    end_date: date = Query(...),
    group_by: str = Query("day", description="分组:day/week/month")
):
    """获取齐套率报表"""
    return {
        "code": 200,
        "data": {
            "period": f"{start_date} ~ {end_date}",
            "summary": {
                "avg_kit_rate": 84.5,
                "total_work_orders": 450,
                "kit_complete": 380,
                "shortage_count": 70
            },
            "trend": [
                {"date": "2025-01-01", "kit_rate": 82, "work_orders": 42, "shortage": 8},
                {"date": "2025-01-02", "kit_rate": 85, "work_orders": 45, "shortage": 7},
                {"date": "2025-01-03", "kit_rate": 84, "work_orders": 45, "shortage": 7}
            ],
            "by_workshop": [
                {"workshop": "机加车间", "kit_rate": 92, "work_orders": 150},
                {"workshop": "装配车间", "kit_rate": 78, "work_orders": 220},
                {"workshop": "调试车间", "kit_rate": 88, "work_orders": 80}
            ]
        }
    }


@router.get("/reports/shortage-analysis", summary="缺料分析报表")
async def get_shortage_analysis(
    start_date: date = Query(...),
    end_date: date = Query(...)
):
    """获取缺料分析报表"""
    return {
        "code": 200,
        "data": {
            "period": f"{start_date} ~ {end_date}",
            "summary": {
                "total_shortage_count": 45,
                "affected_work_orders": 32,
                "stop_work_hours": 86,
                "avg_resolve_time": 3.5
            },
            "by_reason": [
                {"reason": "采购延迟", "count": 18, "percent": 40, "avg_resolve_hours": 4.2},
                {"reason": "供应商交期延误", "count": 15, "percent": 33, "avg_resolve_hours": 6.5},
                {"reason": "库存数据不准", "count": 7, "percent": 16, "avg_resolve_hours": 1.5},
                {"reason": "设计变更", "count": 3, "percent": 7, "avg_resolve_hours": 2.0},
                {"reason": "其他", "count": 2, "percent": 4, "avg_resolve_hours": 1.0}
            ],
            "by_material_category": [
                {"category": "电气件", "count": 20, "percent": 44},
                {"category": "机械件", "count": 12, "percent": 27},
                {"category": "标准件", "count": 8, "percent": 18},
                {"category": "其他", "count": 5, "percent": 11}
            ],
            "top_shortage_materials": [
                {"material": "伺服电机", "count": 5, "total_shortage_qty": 12},
                {"material": "PLC模块", "count": 4, "total_shortage_qty": 8},
                {"material": "传动轴", "count": 3, "total_shortage_qty": 5}
            ]
        }
    }


@router.get("/reports/supplier-delivery", summary="供应商交期报表")
async def get_supplier_delivery_report(
    start_date: date = Query(...),
    end_date: date = Query(...)
):
    """获取供应商交期报表"""
    return {
        "code": 200,
        "data": {
            "period": f"{start_date} ~ {end_date}",
            "summary": {
                "total_orders": 120,
                "on_time_orders": 102,
                "delayed_orders": 18,
                "on_time_rate": 85
            },
            "by_supplier": [
                {"supplier": "XX电机", "orders": 25, "on_time": 24, "rate": 96, "avg_delay_days": 0.5},
                {"supplier": "YY机械", "orders": 30, "on_time": 25, "rate": 83, "avg_delay_days": 1.2},
                {"supplier": "ZZ自动化", "orders": 20, "on_time": 18, "rate": 90, "avg_delay_days": 0.8},
                {"supplier": "AA五金", "orders": 45, "on_time": 35, "rate": 78, "avg_delay_days": 2.1}
            ],
            "delay_trend": [
                {"month": "2024-11", "on_time_rate": 82},
                {"month": "2024-12", "on_time_rate": 84},
                {"month": "2025-01", "on_time_rate": 85}
            ]
        }
    }


# ==================== 移动端接口 ====================

@router.get("/mobile/kit-status", summary="[移动端]我的工单齐套状态")
async def get_mobile_kit_status(current_user_id: int = Query(101)):
    """工人查看自己工单的齐套状态"""
    return {
        "code": 200,
        "data": [
            {
                "work_order_id": 1,
                "work_order_no": "WO-0103-001",
                "task_name": "XX项目-支架装配",
                "kit_status": "partial",
                "kit_rate": 83,
                "shortage_items": 2,
                "can_start": False,
                "shortage_summary": "传动轴x1(预计14:00到), 联轴器x1(可替代)"
            },
            {
                "work_order_id": 2,
                "work_order_no": "WO-0103-002",
                "task_name": "YY项目-底座装配",
                "kit_status": "complete",
                "kit_rate": 100,
                "shortage_items": 0,
                "can_start": True
            }
        ]
    }


@router.get("/mobile/arrival-notify", summary="[移动端]到货通知")
async def get_mobile_arrival_notify(current_user_id: int = Query(101)):
    """工人获取与自己相关的到货通知"""
    return {
        "code": 200,
        "data": [
            {
                "id": 1,
                "material_name": "传动轴",
                "arrived_qty": 2,
                "arrival_time": "2025-01-03 14:05:00",
                "work_order_no": "WO-0103-001",
                "message": "您等待的传动轴已到货，可前往仓库领料",
                "is_read": False
            }
        ]
    }
