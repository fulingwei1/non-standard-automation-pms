"""
生产管理模块 API
生产计划、工单管理、报工、异常管理、车间管理
"""
from fastapi import APIRouter, Query, Body
from typing import Optional, List, Dict
from datetime import datetime, date

router = APIRouter(prefix="/production", tags=["生产管理"])


# ==================== 生产驾驶舱 ====================

@router.get("/dashboard", summary="生产管理驾驶舱")
async def get_production_dashboard():
    """获取生产管理驾驶舱数据"""
    return {
        "code": 200,
        "data": {
            "overview": {
                "active_projects": 12, "today_tasks": 45, "completed_today": 32,
                "exception_count": 3, "today_efficiency": 87
            },
            "workshop_workload": [
                {"workshop": "机加车间", "workload": 85, "status": "normal", "tasks": 15, "workers": 14},
                {"workshop": "装配车间", "workload": 95, "status": "overload", "tasks": 22, "workers": 18},
                {"workshop": "调试车间", "workload": 68, "status": "normal", "tasks": 8, "workers": 10}
            ],
            "today_exceptions": [
                {"id": 1, "level": "critical", "project": "XX项目", "content": "缺料，影响装配"},
                {"id": 2, "level": "major", "project": "设备", "content": "CNC机床故障"},
                {"id": 3, "level": "minor", "project": "YY项目", "content": "图纸有误"}
            ],
            "key_projects": [
                {"id": 1, "name": "XX汽车传感器测试设备", "machining_progress": 100, "assembly_progress": 75, "debugging_progress": 0, "deadline": "2025-02-10", "status": "normal"},
                {"id": 2, "name": "YY新能源电池检测线", "machining_progress": 80, "assembly_progress": 30, "debugging_progress": 0, "deadline": "2025-03-15", "status": "at_risk"}
            ],
            "attendance": {"present": 42, "leave": 2, "overtime": 8}
        }
    }


# ==================== 生产计划 ====================

@router.get("/plans", summary="获取生产计划列表")
async def get_production_plans(plan_type: Optional[str] = Query(None), page: int = Query(1)):
    plans = [
        {"id": 1, "plan_no": "MPS-2025-001", "plan_type": "master", "plan_name": "XX项目主生产计划", "project_name": "XX汽车传感器测试设备", "status": "executing", "progress": 68},
        {"id": 2, "plan_no": "WPS-2025-001", "plan_type": "workshop", "plan_name": "装配车间1月计划", "status": "executing", "progress": 45}
    ]
    return {"code": 200, "data": {"plans": plans, "total": len(plans)}}


@router.post("/plans", summary="创建生产计划")
async def create_production_plan(plan_type: str = Body(...), plan_name: str = Body(...), plan_start_date: date = Body(...), plan_end_date: date = Body(...)):
    plan_no = f"{'MPS' if plan_type == 'master' else 'WPS'}-{datetime.now().strftime('%Y-%m%d%H%M')}"
    return {"code": 200, "message": "计划创建成功", "data": {"id": 1, "plan_no": plan_no, "status": "draft"}}


# ==================== 工单管理 ====================

@router.get("/work-orders", summary="获取工单列表")
async def get_work_orders(workshop_id: Optional[int] = Query(None), status: Optional[str] = Query(None), assigned_to: Optional[int] = Query(None), page: int = Query(1)):
    work_orders = [
        {"id": 1, "work_order_no": "WO-20250103-001", "task_name": "XX项目-底板加工", "task_type": "machining", "task_type_label": "机加", "project_name": "XX汽车传感器测试设备", "material_name": "底板", "plan_qty": 1, "standard_hours": 4, "workshop_name": "机加车间", "assigned_name": "张师傅", "status": "started", "priority": "high", "progress": 60},
        {"id": 2, "work_order_no": "WO-20250103-002", "task_name": "XX项目-支架装配", "task_type": "assembly", "task_type_label": "装配", "project_name": "XX汽车传感器测试设备", "material_name": "支架组件", "plan_qty": 1, "standard_hours": 6, "workshop_name": "装配车间", "assigned_name": "李师傅", "status": "assigned", "priority": "normal", "progress": 0},
        {"id": 3, "work_order_no": "WO-20250103-003", "task_name": "YY项目-底座装配", "task_type": "assembly", "task_type_label": "装配", "project_name": "YY新能源电池检测线", "plan_qty": 1, "standard_hours": 8, "workshop_name": "装配车间", "assigned_name": "王师傅", "status": "started", "priority": "urgent", "progress": 30}
    ]
    return {"code": 200, "data": {"work_orders": work_orders, "total": len(work_orders)}}


@router.get("/work-orders/{work_order_id}", summary="获取工单详情")
async def get_work_order_detail(work_order_id: int):
    return {
        "code": 200,
        "data": {
            "id": work_order_id, "work_order_no": "WO-20250103-001", "task_name": "XX项目-底板加工",
            "task_type": "machining", "work_content": "按图纸要求加工底板",
            "project_name": "XX汽车传感器测试设备", "material_name": "底板", "specification": "500x400x20",
            "plan_qty": 1, "completed_qty": 0, "process_name": "CNC铣削",
            "standard_hours": 4, "actual_hours": 2.5,
            "workshop_name": "机加车间", "assigned_name": "张师傅",
            "status": "started", "priority": "high", "progress": 60,
            "drawing_no": "DWG-XX-001-01",
            "work_reports": [
                {"report_type": "start", "report_time": "2025-01-03 08:30:00", "worker_name": "张师傅"},
                {"report_type": "progress", "report_time": "2025-01-03 10:30:00", "progress_percent": 60, "work_hours": 2}
            ]
        }
    }


@router.post("/work-orders", summary="创建工单")
async def create_work_order(project_id: int = Body(...), task_name: str = Body(...), task_type: str = Body(...), plan_start_date: date = Body(...), plan_end_date: date = Body(...)):
    work_order_no = f"WO-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    return {"code": 200, "message": "工单创建成功", "data": {"id": 1, "work_order_no": work_order_no, "status": "pending"}}


@router.post("/work-orders/{work_order_id}/assign", summary="派工")
async def assign_work_order(work_order_id: int, assigned_to: int = Body(...), workstation_id: int = Body(None)):
    return {"code": 200, "message": "派工成功", "data": {"id": work_order_id, "status": "assigned"}}


@router.post("/work-orders/batch-assign", summary="批量派工")
async def batch_assign_work_orders(work_order_ids: List[int] = Body(...), assigned_to: int = Body(...)):
    return {"code": 200, "message": f"成功派工{len(work_order_ids)}个工单"}


# ==================== 报工管理 ====================

@router.get("/my-tasks", summary="获取我的任务(工人)")
async def get_my_tasks(current_user_id: int = Query(101)):
    tasks = [
        {"id": 1, "work_order_no": "WO-20250103-001", "task_name": "XX项目-底板加工", "process_name": "铣削", "plan_hours": 4, "actual_hours": 2.5, "status": "started", "priority": "high", "progress": 60},
        {"id": 2, "work_order_no": "WO-20250103-005", "task_name": "YY项目-侧板加工", "process_name": "铣削", "plan_hours": 3, "status": "assigned", "priority": "normal", "progress": 0},
        {"id": 3, "work_order_no": "WO-20250102-008", "task_name": "BB项目-框架加工", "plan_hours": 5, "actual_hours": 5.5, "status": "completed", "progress": 100, "completed_qty": 1, "qualified_qty": 1}
    ]
    return {"code": 200, "data": tasks}


@router.post("/work-orders/{work_order_id}/start", summary="开工报告")
async def start_work_order(work_order_id: int, current_user_id: int = Query(101)):
    report_no = f"RPT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    return {"code": 200, "message": "开工成功", "data": {"report_no": report_no, "work_order_id": work_order_id, "report_type": "start", "start_time": datetime.now().isoformat()}}


@router.post("/work-orders/{work_order_id}/progress", summary="进度报告")
async def report_progress(work_order_id: int, progress_percent: int = Body(...), work_hours: float = Body(None), description: str = Body(""), current_user_id: int = Query(101)):
    return {"code": 200, "message": "进度已更新", "data": {"work_order_id": work_order_id, "progress_percent": progress_percent}}


@router.post("/work-orders/{work_order_id}/complete", summary="完工报告")
async def complete_work_order(work_order_id: int, completed_qty: int = Body(1), qualified_qty: int = Body(1), defect_qty: int = Body(0), work_hours: float = Body(None), current_user_id: int = Query(101)):
    return {"code": 200, "message": "完工报告已提交", "data": {"work_order_id": work_order_id, "status": "completed", "completed_qty": completed_qty}}


@router.post("/work-orders/{work_order_id}/pause", summary="暂停工单")
async def pause_work_order(work_order_id: int, reason: str = Body(...)):
    return {"code": 200, "message": "工单已暂停", "data": {"id": work_order_id, "status": "paused"}}


@router.post("/work-orders/{work_order_id}/resume", summary="恢复工单")
async def resume_work_order(work_order_id: int):
    return {"code": 200, "message": "工单已恢复", "data": {"id": work_order_id, "status": "started"}}


@router.get("/work-reports", summary="获取报工记录")
async def get_work_reports(work_order_id: Optional[int] = Query(None), worker_id: Optional[int] = Query(None), page: int = Query(1)):
    reports = [
        {"id": 1, "report_no": "RPT-20250103083000", "work_order_no": "WO-20250103-001", "task_name": "XX项目-底板加工", "report_type": "start", "worker_name": "张师傅", "report_time": "2025-01-03 08:30:00", "status": "approved"},
        {"id": 2, "report_no": "RPT-20250103103000", "work_order_no": "WO-20250103-001", "task_name": "XX项目-底板加工", "report_type": "progress", "worker_name": "张师傅", "report_time": "2025-01-03 10:30:00", "progress_percent": 60, "work_hours": 2, "status": "pending"}
    ]
    return {"code": 200, "data": {"reports": reports, "total": len(reports)}}


@router.post("/work-reports/{report_id}/approve", summary="审核报工")
async def approve_work_report(report_id: int, approved: bool = Body(...), comment: str = Body("")):
    return {"code": 200, "message": "审核完成", "data": {"id": report_id, "status": "approved" if approved else "rejected"}}


# ==================== 异常管理 ====================

@router.get("/exceptions", summary="获取异常列表")
async def get_exceptions(exception_type: Optional[str] = Query(None), status: Optional[str] = Query(None), page: int = Query(1)):
    exceptions = [
        {"id": 1, "exception_no": "EXC-20250103-001", "exception_type": "material", "exception_level": "critical", "title": "XX项目缺料", "description": "传动轴未到货", "project_name": "XX汽车传感器测试设备", "reporter_name": "装配主管", "status": "handling"},
        {"id": 2, "exception_no": "EXC-20250103-002", "exception_type": "equipment", "exception_level": "major", "title": "CNC机床故障", "reporter_name": "机加主管", "status": "handling"},
        {"id": 3, "exception_no": "EXC-20250103-003", "exception_type": "process", "exception_level": "minor", "title": "图纸尺寸有误", "project_name": "YY新能源电池检测线", "reporter_name": "张师傅", "status": "reported"}
    ]
    return {"code": 200, "data": {"exceptions": exceptions, "total": len(exceptions)}}


@router.post("/exceptions", summary="上报异常")
async def create_exception(exception_type: str = Body(...), exception_level: str = Body("minor"), title: str = Body(...), description: str = Body(...), work_order_id: int = Body(None), current_user_id: int = Query(101)):
    exception_no = f"EXC-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    return {"code": 200, "message": "异常已上报", "data": {"id": 1, "exception_no": exception_no, "status": "reported"}}


@router.post("/exceptions/{exception_id}/handle", summary="处理异常")
async def handle_exception(exception_id: int, handle_plan: str = Body(...), current_user_name: str = Query("处理人")):
    return {"code": 200, "message": "已开始处理", "data": {"id": exception_id, "status": "handling"}}


@router.post("/exceptions/{exception_id}/resolve", summary="解决异常")
async def resolve_exception(exception_id: int, handle_result: str = Body(...)):
    return {"code": 200, "message": "异常已解决", "data": {"id": exception_id, "status": "resolved"}}


# ==================== 车间管理 ====================

@router.get("/workshops", summary="获取车间列表")
async def get_workshops():
    workshops = [
        {"id": 1, "workshop_code": "WS-01", "workshop_name": "机加车间", "workshop_type": "machining", "manager_name": "李主管", "worker_count": 15, "capacity_hours": 120},
        {"id": 2, "workshop_code": "WS-02", "workshop_name": "装配车间", "workshop_type": "assembly", "manager_name": "王主管", "worker_count": 20, "capacity_hours": 160},
        {"id": 3, "workshop_code": "WS-03", "workshop_name": "调试车间", "workshop_type": "debugging", "manager_name": "张主管", "worker_count": 10, "capacity_hours": 80}
    ]
    return {"code": 200, "data": workshops}


@router.get("/workshops/{workshop_id}/board", summary="车间看板数据")
async def get_workshop_board(workshop_id: int):
    return {
        "code": 200,
        "data": {
            "workshop_id": workshop_id, "workshop_name": "装配车间",
            "today_summary": {"total_tasks": 22, "pending": 5, "in_progress": 12, "completed": 5, "completion_rate": 23},
            "workers": [
                {"id": 101, "name": "李师傅", "status": "working", "current_task": "XX项目-支架装配", "progress": 65},
                {"id": 102, "name": "王师傅", "status": "working", "current_task": "YY项目-底座装配", "progress": 30},
                {"id": 103, "name": "张师傅", "status": "idle"},
                {"id": 104, "name": "赵师傅", "status": "break"}
            ],
            "pending_tasks": [
                {"id": 10, "task_name": "ZZ项目-电气柜装配", "priority": "urgent", "plan_hours": 8},
                {"id": 11, "task_name": "AA项目-管路装配", "priority": "normal", "plan_hours": 4}
            ]
        }
    }


@router.get("/workstations", summary="获取工位列表")
async def get_workstations(workshop_id: Optional[int] = Query(None)):
    workstations = [
        {"id": 1, "workstation_code": "CNC-01", "workstation_name": "CNC加工中心-01", "workshop_name": "机加车间", "status": "working", "current_worker": "张师傅"},
        {"id": 2, "workstation_code": "CNC-02", "workstation_name": "CNC加工中心-02", "workshop_name": "机加车间", "status": "maintenance"},
        {"id": 3, "workstation_code": "ASM-01", "workstation_name": "装配工位-01", "workshop_name": "装配车间", "status": "working", "current_worker": "李师傅"}
    ]
    return {"code": 200, "data": workstations}


# ==================== 人员管理 ====================

@router.get("/workers", summary="获取生产人员列表")
async def get_workers(workshop_id: Optional[int] = Query(None), page: int = Query(1)):
    workers = [
        {"id": 101, "worker_no": "W001", "worker_name": "张师傅", "workshop_name": "机加车间", "position": "CNC操作工", "skill_level": "senior", "status": "active"},
        {"id": 102, "worker_no": "W002", "worker_name": "李师傅", "workshop_name": "装配车间", "position": "装配工", "skill_level": "intermediate", "status": "active"},
        {"id": 103, "worker_no": "W003", "worker_name": "王师傅", "workshop_name": "装配车间", "position": "装配工", "skill_level": "senior", "status": "active"},
        {"id": 104, "worker_no": "W004", "worker_name": "赵师傅", "workshop_name": "调试车间", "position": "调试工程师", "skill_level": "expert", "status": "active"}
    ]
    return {"code": 200, "data": {"workers": workers, "total": len(workers)}}


@router.get("/workers/{worker_id}/statistics", summary="获取工人统计数据")
async def get_worker_statistics(worker_id: int, month: str = Query(None)):
    return {
        "code": 200,
        "data": {
            "worker_id": worker_id, "worker_name": "张师傅",
            "summary": {"total_tasks": 45, "completed_tasks": 42, "completion_rate": 93.3, "total_hours": 168, "efficiency": 105, "qualified_rate": 99.2}
        }
    }


# ==================== 领料管理 ====================

@router.get("/material-requisitions", summary="获取领料单列表")
async def get_material_requisitions(status: Optional[str] = Query(None), page: int = Query(1)):
    requisitions = [
        {"id": 1, "requisition_no": "MR-20250103-001", "work_order_no": "WO-20250103-001", "project_name": "XX汽车传感器测试设备", "applicant_name": "张师傅", "apply_time": "2025-01-03 08:00:00", "status": "completed"},
        {"id": 2, "requisition_no": "MR-20250103-002", "work_order_no": "WO-20250103-002", "project_name": "XX汽车传感器测试设备", "applicant_name": "李师傅", "apply_time": "2025-01-03 09:00:00", "status": "approved"}
    ]
    return {"code": 200, "data": {"requisitions": requisitions, "total": len(requisitions)}}


@router.post("/material-requisitions", summary="创建领料单")
async def create_material_requisition(work_order_id: int = Body(None), items: List[Dict] = Body(...), current_user_id: int = Query(101)):
    requisition_no = f"MR-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    return {"code": 200, "message": "领料单已提交", "data": {"id": 1, "requisition_no": requisition_no, "status": "submitted"}}


@router.post("/material-requisitions/{requisition_id}/approve", summary="审批领料单")
async def approve_material_requisition(requisition_id: int, approved: bool = Body(...)):
    return {"code": 200, "message": "审批完成", "data": {"id": requisition_id, "status": "approved" if approved else "rejected"}}


# ==================== 报表统计 ====================

@router.get("/reports/daily", summary="生产日报")
async def get_daily_report(report_date: date = Query(...), workshop_id: Optional[int] = Query(None)):
    return {
        "code": 200,
        "data": {
            "report_date": report_date.isoformat(),
            "production": {"plan_qty": 45, "completed_qty": 38, "completion_rate": 84.4},
            "hours": {"plan_hours": 360, "actual_hours": 342, "efficiency": 95},
            "attendance": {"should_attend": 45, "actual_attend": 42, "overtime_hours": 24},
            "quality": {"total_qty": 38, "qualified_qty": 37, "pass_rate": 97.4},
            "exceptions": {"new_count": 3, "resolved_count": 2}
        }
    }


@router.get("/reports/efficiency", summary="效率分析报告")
async def get_efficiency_report(start_date: date = Query(...), end_date: date = Query(...)):
    return {
        "code": 200,
        "data": {
            "period": f"{start_date} ~ {end_date}",
            "summary": {"total_standard_hours": 1600, "total_actual_hours": 1520, "overall_efficiency": 105.3},
            "by_workshop": [
                {"workshop": "机加车间", "efficiency": 103.4},
                {"workshop": "装配车间", "efficiency": 107.7},
                {"workshop": "调试车间", "efficiency": 103.4}
            ]
        }
    }


@router.get("/reports/quality", summary="质量分析报告")
async def get_quality_report(start_date: date = Query(...), end_date: date = Query(...)):
    return {
        "code": 200,
        "data": {
            "summary": {"total_qty": 380, "qualified_qty": 372, "pass_rate": 97.9},
            "by_defect_type": [
                {"type": "尺寸超差", "count": 3},
                {"type": "表面划伤", "count": 2},
                {"type": "装配不良", "count": 2}
            ]
        }
    }


# ==================== 设备管理 ====================

@router.get("/equipment", summary="获取设备列表")
async def get_equipment(workshop_id: Optional[int] = Query(None)):
    equipment = [
        {"id": 1, "equipment_code": "EQ-CNC-01", "equipment_name": "CNC加工中心", "model": "VMC850", "workshop_name": "机加车间", "status": "running"},
        {"id": 2, "equipment_code": "EQ-CNC-02", "equipment_name": "CNC加工中心", "model": "VMC850", "workshop_name": "机加车间", "status": "maintenance"},
        {"id": 3, "equipment_code": "EQ-LATHE-01", "equipment_name": "数控车床", "model": "CK6140", "workshop_name": "机加车间", "status": "idle"}
    ]
    return {"code": 200, "data": {"equipment": equipment}}


@router.post("/equipment/{equipment_id}/fault", summary="设备故障上报")
async def report_equipment_fault(equipment_id: int, fault_description: str = Body(...)):
    return {"code": 200, "message": "故障已上报", "data": {"equipment_id": equipment_id, "status": "repair"}}


# ==================== 工序管理 ====================

@router.get("/processes", summary="获取工序列表")
async def get_processes(process_type: Optional[str] = Query(None)):
    processes = [
        {"id": 1, "process_code": "CNC-MILL", "process_name": "CNC铣削", "process_type": "machining", "standard_hours": 4},
        {"id": 2, "process_code": "CNC-TURN", "process_name": "CNC车削", "process_type": "machining", "standard_hours": 3},
        {"id": 5, "process_code": "MECH-ASM", "process_name": "机械装配", "process_type": "assembly", "standard_hours": 6},
        {"id": 6, "process_code": "ELEC-ASM", "process_name": "电气装配", "process_type": "assembly", "standard_hours": 8},
        {"id": 8, "process_code": "ELEC-DBG", "process_name": "电气调试", "process_type": "debugging", "standard_hours": 8},
        {"id": 9, "process_code": "SOFT-DBG", "process_name": "软件调试", "process_type": "debugging", "standard_hours": 16}
    ]
    return {"code": 200, "data": processes}


# ==================== 移动端专用接口 ====================

@router.get("/mobile/today-tasks", summary="[移动端]今日任务")
async def get_mobile_today_tasks(current_user_id: int = Query(101)):
    return {
        "code": 200,
        "data": {
            "summary": {"total": 3, "pending": 1, "in_progress": 1, "completed": 1},
            "tasks": [
                {"id": 1, "work_order_no": "WO-20250103-001", "task_name": "XX项目-底板加工", "process_name": "铣削", "plan_hours": 4, "progress": 60, "status": "started", "priority": "high"},
                {"id": 2, "work_order_no": "WO-20250103-005", "task_name": "YY项目-侧板加工", "process_name": "铣削", "plan_hours": 3, "progress": 0, "status": "assigned", "priority": "normal"}
            ]
        }
    }


@router.post("/mobile/scan-start", summary="[移动端]扫码开工")
async def mobile_scan_start(qr_code: str = Body(...), current_user_id: int = Query(101)):
    return {"code": 200, "message": "开工成功", "data": {"work_order_no": "WO-20250103-001", "task_name": "XX项目-底板加工", "start_time": datetime.now().isoformat()}}


@router.get("/mobile/my-statistics", summary="[移动端]我的统计")
async def get_mobile_my_statistics(current_user_id: int = Query(101)):
    return {
        "code": 200,
        "data": {
            "this_month": {"work_days": 20, "total_hours": 168, "overtime_hours": 12, "completed_tasks": 42, "qualified_rate": 99.2, "efficiency": 105},
            "today": {"tasks": 3, "completed": 1, "hours": 6.5},
            "ranking": {"efficiency_rank": 3, "total_workers": 45}
        }
    }
