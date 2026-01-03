"""
项目管理部(PMO)模块 API
项目全生命周期管理、资源管理、风险管理、成本管理
"""
from fastapi import APIRouter, Query, HTTPException, Body
from typing import Optional, List, Dict
from datetime import datetime, date, timedelta
from pydantic import BaseModel
from enum import Enum

router = APIRouter(prefix="/pmo", tags=["项目管理部"])


# ==================== 管理驾驶舱 ====================

@router.get("/dashboard", summary="项目管理驾驶舱")
async def get_pmo_dashboard():
    """获取项目管理驾驶舱数据"""
    return {
        "code": 200,
        "data": {
            "overview": {
                "total_projects": 45,
                "level_a": 12,
                "level_b": 20,
                "level_c": 13,
                "this_month_delivery": 5,
                "warning_projects": 8,
                "avg_health_score": 82
            },
            "status_distribution": {
                "initiation": 3,
                "design": 15,
                "production": 18,
                "delivery": 6,
                "closure": 3
            },
            "health_distribution": {
                "green": 35,
                "yellow": 8,
                "red": 2
            },
            "department_workload": [
                {"dept": "机械部", "workload": 85, "status": "normal"},
                {"dept": "电气部", "workload": 95, "status": "overload"},
                {"dept": "软件部", "workload": 72, "status": "normal"},
                {"dept": "装配组", "workload": 78, "status": "normal"}
            ],
            "key_projects": [
                {"id": 1, "name": "XX汽车传感器测试设备", "level": "A", "progress": 78, "health": "green", "pm_name": "王经理"},
                {"id": 2, "name": "YY新能源电池检测线", "level": "A", "progress": 55, "health": "yellow", "pm_name": "李经理"},
                {"id": 3, "name": "ZZ医疗器械测试系统", "level": "B", "progress": 35, "health": "red", "pm_name": "张经理"}
            ],
            "warnings": [
                {"type": "red", "project": "ZZ项目", "content": "机械设计延期3天"},
                {"type": "red", "project": "YY项目", "content": "关键物料未到货"},
                {"type": "yellow", "project": "AA项目", "content": "客户需求变更"}
            ],
            "upcoming_milestones": [
                {"project": "XX项目", "milestone": "电气设计评审", "date": "2025-01-05"},
                {"project": "YY项目", "milestone": "软件联调", "date": "2025-01-08"}
            ]
        }
    }


# ==================== 项目管理 ====================

@router.get("/projects", summary="获取项目列表")
async def get_projects(
    status: Optional[str] = Query(None),
    phase: Optional[str] = Query(None),
    level: Optional[str] = Query(None),
    pm_id: Optional[int] = Query(None),
    keyword: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """获取项目列表"""
    projects = [
        {
            "id": 1, "project_no": "PRJ-2025-001", "project_name": "XX汽车传感器测试设备",
            "project_level": "A", "customer_name": "XX汽车科技", "contract_amount": 980000,
            "current_phase": "production", "phase_label": "生产阶段", "status": "active",
            "overall_progress": 78, "health_status": "green", "pm_name": "王经理",
            "plan_end_date": "2025-02-28", "budget_amount": 650000, "actual_cost": 480000
        },
        {
            "id": 2, "project_no": "PRJ-2025-002", "project_name": "YY新能源电池检测线",
            "project_level": "A", "customer_name": "YY新能源科技", "contract_amount": 1500000,
            "current_phase": "design", "phase_label": "设计阶段", "status": "active",
            "overall_progress": 55, "health_status": "yellow", "pm_name": "李经理",
            "plan_end_date": "2025-03-15", "budget_amount": 980000, "actual_cost": 420000
        },
        {
            "id": 3, "project_no": "PRJ-2024-045", "project_name": "ZZ医疗器械测试系统",
            "project_level": "B", "customer_name": "ZZ医疗器械", "contract_amount": 580000,
            "current_phase": "design", "phase_label": "设计阶段", "status": "active",
            "overall_progress": 35, "health_status": "red", "pm_name": "张经理",
            "plan_end_date": "2025-01-31", "budget_amount": 380000, "actual_cost": 150000
        }
    ]
    return {"code": 200, "data": {"projects": projects, "total": len(projects), "page": page, "page_size": page_size}}


@router.get("/projects/{project_id}", summary="获取项目详情")
async def get_project_detail(project_id: int):
    """获取项目详细信息"""
    return {
        "code": 200,
        "data": {
            "id": project_id,
            "project_no": "PRJ-2025-001",
            "project_name": "XX汽车传感器测试设备",
            "project_level": "A",
            "customer_name": "XX汽车科技有限公司",
            "contract_no": "HT-2024-0156",
            "contract_amount": 980000,
            "pm_name": "王经理",
            "plan_start_date": "2024-10-01",
            "plan_end_date": "2025-02-28",
            "current_phase": "production",
            "status": "active",
            "overall_progress": 78,
            "health_status": "green",
            "budget_amount": 650000,
            "actual_cost": 480000,
            "planned_hours": 1200,
            "actual_hours": 920,
            "phases": [
                {"phase": "initiation", "name": "立项", "status": "completed", "progress": 100},
                {"phase": "design", "name": "设计", "status": "completed", "progress": 100},
                {"phase": "production", "name": "生产", "status": "in_progress", "progress": 65},
                {"phase": "delivery", "name": "交付", "status": "pending", "progress": 0},
                {"phase": "closure", "name": "结项", "status": "pending", "progress": 0}
            ],
            "team_members": [
                {"id": 10, "name": "王经理", "role": "项目经理", "dept": "项目管理部"},
                {"id": 101, "name": "李工", "role": "机械工程师", "dept": "机械部"},
                {"id": 102, "name": "张工", "role": "电气工程师", "dept": "电气部"}
            ]
        }
    }


# ==================== 立项管理 ====================

@router.post("/initiations", summary="提交立项申请")
async def create_initiation(
    project_name: str = Body(...),
    customer_name: str = Body(...),
    contract_amount: float = Body(None),
    required_end_date: date = Body(None),
    requirement_summary: str = Body(""),
    current_user_id: int = Query(1)
):
    """销售/售前提交项目立项申请"""
    application_no = f"INI{datetime.now().strftime('%Y%m%d%H%M%S')}"
    return {
        "code": 200,
        "message": "立项申请已提交",
        "data": {"id": 1, "application_no": application_no, "status": "submitted"}
    }


@router.get("/initiations", summary="获取立项申请列表")
async def get_initiations(status: Optional[str] = Query(None), page: int = Query(1), page_size: int = Query(20)):
    """获取立项申请列表"""
    initiations = [
        {"id": 1, "application_no": "INI20250103001", "project_name": "AA电子测试设备", "customer_name": "AA电子科技", "contract_amount": 680000, "applicant_name": "张销售", "status": "submitted", "status_label": "待评审"},
        {"id": 2, "application_no": "INI20250102001", "project_name": "BB自动化检测线", "customer_name": "BB制造", "contract_amount": 1200000, "applicant_name": "李销售", "status": "reviewing", "status_label": "评审中"}
    ]
    return {"code": 200, "data": {"initiations": initiations, "total": len(initiations)}}


@router.post("/initiations/{initiation_id}/review", summary="立项评审")
async def review_initiation(
    initiation_id: int,
    approved: bool = Body(...),
    assigned_pm_id: int = Body(None),
    approved_level: str = Body(None),
    review_result: str = Body(""),
    current_user_id: int = Query(1)
):
    """PMO进行立项评审"""
    if approved:
        return {"code": 200, "message": "立项审批通过", "data": {"initiation_id": initiation_id, "status": "approved", "project_id": 100}}
    else:
        return {"code": 200, "message": "立项申请已驳回", "data": {"initiation_id": initiation_id, "status": "rejected"}}


# ==================== 里程碑管理 ====================

@router.get("/projects/{project_id}/milestones", summary="获取项目里程碑")
async def get_project_milestones(project_id: int):
    """获取项目里程碑列表"""
    milestones = [
        {"id": 1, "milestone_name": "立项评审", "plan_date": "2024-10-15", "actual_date": "2024-10-15", "status": "completed"},
        {"id": 2, "milestone_name": "设计评审", "plan_date": "2024-12-15", "actual_date": "2024-12-18", "status": "completed", "delay_days": 3},
        {"id": 3, "milestone_name": "出厂检验", "plan_date": "2025-02-10", "status": "pending", "days_remaining": 38},
        {"id": 4, "milestone_name": "客户验收", "plan_date": "2025-02-28", "status": "pending", "days_remaining": 56}
    ]
    return {"code": 200, "data": milestones}


@router.post("/projects/{project_id}/milestones", summary="创建里程碑")
async def create_milestone(
    project_id: int,
    milestone_name: str = Body(...),
    milestone_type: str = Body(...),
    plan_date: date = Body(...),
    owner_id: int = Body(None),
    current_user_id: int = Query(1)
):
    """为项目创建里程碑"""
    return {"code": 200, "message": "里程碑创建成功", "data": {"id": 10, "project_id": project_id, "status": "pending"}}


@router.put("/milestones/{milestone_id}/complete", summary="完成里程碑")
async def complete_milestone(milestone_id: int, actual_date: date = Body(...), current_user_id: int = Query(1)):
    """标记里程碑完成"""
    return {"code": 200, "message": "里程碑已完成", "data": {"id": milestone_id, "status": "completed"}}


# ==================== 风险管理 ====================

@router.get("/projects/{project_id}/risks", summary="获取项目风险")
async def get_project_risks(project_id: int):
    """获取项目风险列表"""
    risks = [
        {"id": 1, "risk_no": "RISK-001", "risk_category": "schedule", "risk_name": "关键物料交期风险", "probability": "medium", "impact": "high", "risk_level": "high", "response_strategy": "mitigate", "owner_name": "采购张工", "status": "monitoring"},
        {"id": 2, "risk_no": "RISK-002", "risk_category": "technical", "risk_name": "新技术方案验证风险", "probability": "medium", "impact": "medium", "risk_level": "medium", "owner_name": "软件李工", "status": "responding"}
    ]
    return {"code": 200, "data": risks}


@router.post("/projects/{project_id}/risks", summary="识别新风险")
async def create_risk(
    project_id: int,
    risk_category: str = Body(...),
    risk_name: str = Body(...),
    probability: str = Body(...),
    impact: str = Body(...),
    response_plan: str = Body(""),
    owner_id: int = Body(None),
    current_user_id: int = Query(1)
):
    """识别并记录项目风险"""
    risk_no = f"RISK-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    risk_matrix = {("low", "low"): "low", ("medium", "medium"): "medium", ("high", "high"): "critical", ("medium", "high"): "high", ("high", "medium"): "high"}
    risk_level = risk_matrix.get((probability, impact), "medium")
    return {"code": 200, "message": "风险已记录", "data": {"id": 10, "risk_no": risk_no, "risk_level": risk_level, "status": "identified"}}


# ==================== 变更管理 ====================

@router.get("/projects/{project_id}/changes", summary="获取变更记录")
async def get_project_changes(project_id: int):
    """获取项目变更记录"""
    changes = [
        {"id": 1, "change_no": "CHG-001", "change_type": "requirement", "title": "客户增加接口协议需求", "requestor_name": "销售张三", "status": "approved", "schedule_impact": "增加3天", "cost_impact": 15000},
        {"id": 2, "change_no": "CHG-002", "change_type": "scope", "title": "测试工位数量调整", "requestor_name": "王经理", "status": "reviewing", "schedule_impact": "增加7天", "cost_impact": 85000}
    ]
    return {"code": 200, "data": changes}


@router.post("/projects/{project_id}/changes", summary="提交变更申请")
async def create_change_request(
    project_id: int,
    change_type: str = Body(...),
    title: str = Body(...),
    description: str = Body(...),
    schedule_impact: str = Body(""),
    cost_impact: float = Body(None),
    current_user_id: int = Query(1)
):
    """提交项目变更申请"""
    change_no = f"CHG-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    return {"code": 200, "message": "变更申请已提交", "data": {"id": 10, "change_no": change_no, "status": "submitted"}}


@router.post("/changes/{change_id}/approve", summary="审批变更")
async def approve_change(change_id: int, approved: bool = Body(...), comment: str = Body(""), current_user_id: int = Query(1)):
    """审批变更申请"""
    return {"code": 200, "message": "审批完成", "data": {"id": change_id, "approved": approved}}


# ==================== 资源管理 ====================

@router.get("/resources/workload", summary="资源负荷分析")
async def get_resource_workload(start_date: date = Query(...), end_date: date = Query(...)):
    """获取资源负荷分析"""
    return {
        "code": 200,
        "data": {
            "departments": [
                {"dept_name": "机械部", "total_capacity": 1200, "allocated_hours": 1020, "utilization_rate": 85, "status": "normal"},
                {"dept_name": "电气部", "total_capacity": 960, "allocated_hours": 912, "utilization_rate": 95, "status": "overload"},
                {"dept_name": "软件部", "total_capacity": 800, "allocated_hours": 576, "utilization_rate": 72, "status": "normal"}
            ],
            "summary": {"total_capacity": 4800, "total_allocated": 4080, "overall_rate": 85}
        }
    }


@router.get("/projects/{project_id}/resources", summary="获取项目资源")
async def get_project_resources(project_id: int):
    """获取项目资源分配情况"""
    resources = [
        {"id": 1, "resource_name": "王经理", "resource_dept": "项目管理部", "resource_role": "项目经理", "allocation_percent": 50, "planned_hours": 400, "actual_hours": 280},
        {"id": 2, "resource_name": "李工", "resource_dept": "机械部", "resource_role": "机械工程师", "allocation_percent": 80, "planned_hours": 600, "actual_hours": 450}
    ]
    return {"code": 200, "data": resources}


@router.post("/projects/{project_id}/resources", summary="分配资源")
async def allocate_resource(
    project_id: int,
    resource_id: int = Body(...),
    resource_role: str = Body(...),
    allocation_percent: int = Body(100),
    start_date: date = Body(...),
    end_date: date = Body(...),
    current_user_id: int = Query(1)
):
    """为项目分配资源"""
    return {"code": 200, "message": "资源分配成功", "data": {"id": 10, "project_id": project_id, "status": "planned"}}


# ==================== 成本管理 ====================

@router.get("/projects/{project_id}/costs", summary="获取项目成本")
async def get_project_costs(project_id: int):
    """获取项目成本情况"""
    return {
        "code": 200,
        "data": {
            "summary": {"budget_amount": 650000, "actual_cost": 480000, "remaining": 170000, "cost_ratio": 73.8},
            "by_category": [
                {"category": "材料成本", "budget": 300000, "actual": 220000, "ratio": 73},
                {"category": "人工成本", "budget": 200000, "actual": 150000, "ratio": 75},
                {"category": "外协加工", "budget": 80000, "actual": 60000, "ratio": 75},
                {"category": "其他费用", "budget": 70000, "actual": 50000, "ratio": 71}
            ]
        }
    }


# ==================== 会议管理 ====================

@router.get("/meetings", summary="获取会议列表")
async def get_meetings(project_id: Optional[int] = Query(None), meeting_type: Optional[str] = Query(None)):
    """获取会议列表"""
    meetings = [
        {"id": 1, "project_name": "XX汽车项目", "meeting_type": "weekly", "meeting_name": "XX项目周例会", "meeting_date": "2025-01-03", "start_time": "14:00", "location": "会议室A", "status": "scheduled"},
        {"id": 2, "project_name": None, "meeting_type": "milestone_review", "meeting_name": "AA项目立项评审会", "meeting_date": "2025-01-05", "start_time": "09:30", "location": "大会议室", "status": "scheduled"}
    ]
    return {"code": 200, "data": {"meetings": meetings, "total": len(meetings)}}


@router.post("/meetings", summary="创建会议")
async def create_meeting(
    project_id: int = Body(None),
    meeting_type: str = Body(...),
    meeting_name: str = Body(...),
    meeting_date: date = Body(...),
    start_time: str = Body(...),
    location: str = Body(""),
    current_user_id: int = Query(1)
):
    """创建会议"""
    return {"code": 200, "message": "会议创建成功", "data": {"id": 10, "status": "scheduled"}}


@router.put("/meetings/{meeting_id}/minutes", summary="填写会议纪要")
async def update_meeting_minutes(meeting_id: int, minutes: str = Body(...), decisions: str = Body(""), current_user_id: int = Query(1)):
    """填写会议纪要"""
    return {"code": 200, "message": "会议纪要已保存", "data": {"id": meeting_id, "status": "completed"}}


# ==================== 项目结项 ====================

@router.get("/projects/{project_id}/closure", summary="获取结项信息")
async def get_project_closure(project_id: int):
    """获取项目结项信息"""
    return {
        "code": 200,
        "data": {
            "project_id": project_id,
            "final_budget": 650000, "final_cost": 620000, "cost_variance": -30000,
            "final_planned_hours": 1200, "final_actual_hours": 1150, "hours_variance": -50,
            "plan_duration": 150, "actual_duration": 148, "schedule_variance": -2,
            "quality_score": 92, "customer_satisfaction": 4.5,
            "archive_status": "completed", "closure_date": None
        }
    }


@router.post("/projects/{project_id}/closure", summary="提交结项申请")
async def submit_project_closure(project_id: int, project_summary: str = Body(...), lessons_learned: str = Body(""), current_user_id: int = Query(1)):
    """提交项目结项申请"""
    return {"code": 200, "message": "结项申请已提交", "data": {"project_id": project_id, "status": "pending_review"}}


@router.post("/projects/{project_id}/closure/review", summary="结项评审")
async def review_project_closure(project_id: int, approved: bool = Body(...), current_user_id: int = Query(1)):
    """PMO进行结项评审"""
    return {"code": 200, "message": "结项评审完成" if approved else "结项申请已驳回", "data": {"project_id": project_id, "review_result": "approved" if approved else "rejected"}}


# ==================== 报表统计 ====================

@router.get("/reports/project-status", summary="项目状态报告")
async def get_project_status_report(start_date: date = Query(...), end_date: date = Query(...)):
    """获取项目状态报告"""
    return {
        "code": 200,
        "data": {
            "summary": {"total_projects": 45, "on_track": 35, "at_risk": 8, "critical": 2},
            "kpis": {"on_time_delivery_rate": 85, "budget_compliance_rate": 92, "milestone_achievement_rate": 80, "customer_satisfaction": 4.3}
        }
    }


@router.get("/reports/weekly", summary="项目管理周报")
async def get_weekly_report(week_start: date = Query(...)):
    """获取项目管理周报"""
    return {
        "code": 200,
        "data": {
            "period": f"{week_start} ~ {week_start + timedelta(days=6)}",
            "overview": {"total_projects": 45, "health_green": 35, "health_yellow": 8, "health_red": 2},
            "warnings": [
                {"level": "red", "project": "ZZ项目", "issue": "机械设计延期3天"},
                {"level": "yellow", "project": "AA项目", "issue": "客户需求变更"}
            ]
        }
    }


# ==================== 项目模板 ====================

@router.get("/templates/wbs", summary="获取WBS模板")
async def get_wbs_templates():
    """获取WBS模板列表"""
    templates = [
        {"id": 1, "name": "标准测试设备WBS模板", "industry": "通用", "use_count": 45},
        {"id": 2, "name": "产线改造WBS模板", "industry": "制造", "use_count": 23},
        {"id": 3, "name": "软件开发WBS模板", "industry": "软件", "use_count": 18}
    ]
    return {"code": 200, "data": templates}
