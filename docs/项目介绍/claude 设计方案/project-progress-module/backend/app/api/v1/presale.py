"""
售前技术支持管理 API
工单管理、方案管理、知识库、统计分析
"""
from fastapi import APIRouter, Query, HTTPException, Body, BackgroundTasks
from typing import Optional, List, Dict
from datetime import datetime, date, timedelta
from pydantic import BaseModel
from enum import Enum

router = APIRouter(prefix="/presale", tags=["售前技术支持"])


# ==================== 枚举定义 ====================

class TicketType(str, Enum):
    CONSULT = "consult"           # 技术咨询
    SURVEY = "survey"             # 需求调研
    SOLUTION = "solution"         # 方案设计
    QUOTATION = "quotation"       # 报价支持
    TENDER = "tender"             # 投标支持
    MEETING = "meeting"           # 技术交流
    SITE_VISIT = "site_visit"     # 现场勘查


class Urgency(str, Enum):
    NORMAL = "normal"
    URGENT = "urgent"
    VERY_URGENT = "very_urgent"


class TicketStatus(str, Enum):
    PENDING = "pending"           # 待接单
    ACCEPTED = "accepted"         # 已接单
    PROCESSING = "processing"     # 处理中
    REVIEW = "review"             # 待审核
    COMPLETED = "completed"       # 已完成
    CLOSED = "closed"             # 已关闭
    CANCELLED = "cancelled"       # 已取消


# ==================== 请求模型 ====================

class CreateTicketRequest(BaseModel):
    """创建工单请求"""
    title: str
    ticket_type: TicketType
    urgency: Urgency = Urgency.NORMAL
    description: Optional[str] = None
    customer_id: Optional[int] = None
    customer_name: Optional[str] = None
    opportunity_id: Optional[int] = None
    expected_date: Optional[date] = None
    attachments: Optional[List[str]] = None


class UpdateTicketRequest(BaseModel):
    """更新工单请求"""
    status: Optional[TicketStatus] = None
    progress_percent: Optional[int] = None
    comment: Optional[str] = None


class TransferTicketRequest(BaseModel):
    """转派工单请求"""
    to_user_id: int
    reason: str


class CreateSolutionRequest(BaseModel):
    """创建方案请求"""
    name: str
    ticket_id: Optional[int] = None
    customer_id: Optional[int] = None
    opportunity_id: Optional[int] = None
    industry: Optional[str] = None
    test_type: Optional[str] = None
    requirement_summary: Optional[str] = None
    template_id: Optional[int] = None


class CostItem(BaseModel):
    """成本项"""
    category: str
    item_name: str
    specification: Optional[str] = None
    unit: Optional[str] = None
    quantity: float = 1
    unit_price: float = 0
    remark: Optional[str] = None


class SubmitSolutionRequest(BaseModel):
    """提交方案审核请求"""
    solution_overview: str
    technical_spec: Optional[str] = None
    cost_items: List[CostItem]
    estimated_hours: Optional[int] = None
    estimated_duration: Optional[int] = None
    suggested_price: Optional[float] = None


# ==================== 支持工单接口 ====================

@router.post("/tickets", summary="创建支持工单")
async def create_ticket(
    data: CreateTicketRequest,
    current_user_id: int = Query(1),
    current_user_name: str = Query("销售员")
):
    """
    销售创建支持工单
    
    工单类型：
    - consult: 技术咨询
    - survey: 需求调研  
    - solution: 方案设计
    - quotation: 报价支持
    - tender: 投标支持
    - meeting: 技术交流
    - site_visit: 现场勘查
    """
    # 生成工单编号
    ticket_no = f"PS{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # 根据类型和紧急程度计算截止时间
    deadline_hours = {
        (TicketType.CONSULT, Urgency.NORMAL): 4,
        (TicketType.CONSULT, Urgency.URGENT): 2,
        (TicketType.CONSULT, Urgency.VERY_URGENT): 1,
        (TicketType.SOLUTION, Urgency.NORMAL): 120,  # 5天
        (TicketType.SOLUTION, Urgency.URGENT): 72,   # 3天
        (TicketType.SITE_VISIT, Urgency.NORMAL): 48,
    }
    hours = deadline_hours.get((data.ticket_type, data.urgency), 24)
    deadline = datetime.now() + timedelta(hours=hours)
    
    ticket = {
        "id": 1001,
        "ticket_no": ticket_no,
        "title": data.title,
        "ticket_type": data.ticket_type,
        "ticket_type_label": {
            "consult": "技术咨询", "survey": "需求调研", "solution": "方案设计",
            "quotation": "报价支持", "tender": "投标支持", "meeting": "技术交流",
            "site_visit": "现场勘查"
        }.get(data.ticket_type, "其他"),
        "urgency": data.urgency,
        "urgency_label": {"normal": "普通", "urgent": "紧急", "very_urgent": "非常紧急"}.get(data.urgency),
        "description": data.description,
        "customer_id": data.customer_id,
        "customer_name": data.customer_name,
        "opportunity_id": data.opportunity_id,
        "applicant_id": current_user_id,
        "applicant_name": current_user_name,
        "apply_time": datetime.now().isoformat(),
        "expected_date": data.expected_date.isoformat() if data.expected_date else None,
        "deadline": deadline.isoformat(),
        "status": "pending",
        "status_label": "待接单"
    }
    
    return {
        "code": 200,
        "message": "工单创建成功",
        "data": ticket
    }


@router.get("/tickets", summary="获取工单列表")
async def get_tickets(
    status: Optional[str] = Query(None, description="状态筛选"),
    ticket_type: Optional[str] = Query(None, description="类型筛选"),
    urgency: Optional[str] = Query(None, description="紧急程度"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    role: str = Query("presale", description="角色:sales/presale/manager"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user_id: int = Query(1)
):
    """
    获取工单列表
    
    - 销售视角：只看自己提交的工单
    - 售前视角：看分配给自己的工单
    - 主管视角：看团队所有工单
    """
    # 模拟数据
    tickets = [
        {
            "id": 1001,
            "ticket_no": "PS20250103001",
            "title": "XX汽车传感器测试设备技术咨询",
            "ticket_type": "consult",
            "ticket_type_label": "技术咨询",
            "urgency": "urgent",
            "urgency_label": "紧急",
            "customer_name": "XX汽车科技有限公司",
            "applicant_name": "张销售",
            "assignee_name": "王工",
            "apply_time": "2025-01-03 09:30:00",
            "deadline": "2025-01-03 11:30:00",
            "status": "processing",
            "status_label": "处理中",
            "progress_percent": 60
        },
        {
            "id": 1002,
            "ticket_no": "PS20250103002",
            "title": "YY电子连接器测试设备方案设计",
            "ticket_type": "solution",
            "ticket_type_label": "方案设计",
            "urgency": "normal",
            "urgency_label": "普通",
            "customer_name": "YY电子科技",
            "applicant_name": "李销售",
            "assignee_name": "王工",
            "apply_time": "2025-01-02 14:00:00",
            "deadline": "2025-01-07 14:00:00",
            "expected_date": "2025-01-06",
            "status": "processing",
            "status_label": "处理中",
            "progress_percent": 30
        },
        {
            "id": 1003,
            "ticket_no": "PS20250103003",
            "title": "ZZ医疗设备测试线技术交流",
            "ticket_type": "meeting",
            "ticket_type_label": "技术交流",
            "urgency": "normal",
            "urgency_label": "普通",
            "customer_name": "ZZ医疗器械",
            "applicant_name": "张销售",
            "assignee_name": None,
            "apply_time": "2025-01-03 10:00:00",
            "deadline": "2025-01-04 10:00:00",
            "status": "pending",
            "status_label": "待接单"
        }
    ]
    
    return {
        "code": 200,
        "data": {
            "tickets": tickets,
            "total": len(tickets),
            "page": page,
            "page_size": page_size,
            "total_pages": 1
        }
    }


@router.get("/tickets/{ticket_id}", summary="获取工单详情")
async def get_ticket_detail(ticket_id: int):
    """获取工单详情"""
    ticket = {
        "id": ticket_id,
        "ticket_no": "PS20250103001",
        "title": "XX汽车传感器测试设备技术咨询",
        "ticket_type": "consult",
        "ticket_type_label": "技术咨询",
        "urgency": "urgent",
        "urgency_label": "紧急",
        "description": "客户询问传感器综合测试设备的测试能力和交期，需要详细解答。\n\n主要问题：\n1. 设备能否同时测试温度、压力、位移传感器？\n2. 测试精度能达到什么水平？\n3. 设备交期多长？",
        "customer_id": 100,
        "customer_name": "XX汽车科技有限公司",
        "opportunity_id": 200,
        "applicant_id": 1,
        "applicant_name": "张销售",
        "applicant_dept": "华南销售部",
        "apply_time": "2025-01-03 09:30:00",
        "assignee_id": 10,
        "assignee_name": "王工",
        "accept_time": "2025-01-03 09:45:00",
        "deadline": "2025-01-03 11:30:00",
        "expected_date": None,
        "status": "processing",
        "status_label": "处理中",
        "progress_percent": 60,
        "actual_hours": 1.5,
        "progress_records": [
            {"time": "2025-01-03 09:45:00", "operator": "王工", "content": "已接单，预计1小时内完成"},
            {"time": "2025-01-03 10:30:00", "operator": "王工", "content": "正在整理技术参数，进度60%"}
        ],
        "deliverables": [],
        "satisfaction_score": None,
        "feedback": None
    }
    
    return {
        "code": 200,
        "data": ticket
    }


@router.post("/tickets/{ticket_id}/accept", summary="接单")
async def accept_ticket(
    ticket_id: int,
    estimated_hours: float = Body(4, description="预计工时"),
    current_user_id: int = Query(1),
    current_user_name: str = Query("售前工程师")
):
    """售前工程师接单"""
    return {
        "code": 200,
        "message": "接单成功",
        "data": {
            "ticket_id": ticket_id,
            "assignee_id": current_user_id,
            "assignee_name": current_user_name,
            "accept_time": datetime.now().isoformat(),
            "estimated_hours": estimated_hours,
            "status": "accepted"
        }
    }


@router.post("/tickets/{ticket_id}/progress", summary="更新进度")
async def update_ticket_progress(
    ticket_id: int,
    progress_percent: int = Body(..., ge=0, le=100),
    comment: str = Body(""),
    current_user_id: int = Query(1),
    current_user_name: str = Query("售前工程师")
):
    """更新工单进度"""
    return {
        "code": 200,
        "message": "进度更新成功",
        "data": {
            "ticket_id": ticket_id,
            "progress_percent": progress_percent,
            "comment": comment,
            "update_time": datetime.now().isoformat()
        }
    }


@router.post("/tickets/{ticket_id}/complete", summary="完成工单")
async def complete_ticket(
    ticket_id: int,
    actual_hours: float = Body(..., description="实际工时"),
    summary: str = Body("", description="完成总结"),
    current_user_id: int = Query(1)
):
    """完成工单"""
    return {
        "code": 200,
        "message": "工单已完成",
        "data": {
            "ticket_id": ticket_id,
            "status": "completed",
            "complete_time": datetime.now().isoformat(),
            "actual_hours": actual_hours
        }
    }


@router.post("/tickets/{ticket_id}/transfer", summary="转派工单")
async def transfer_ticket(
    ticket_id: int,
    data: TransferTicketRequest,
    current_user_id: int = Query(1)
):
    """转派工单给其他售前工程师"""
    return {
        "code": 200,
        "message": "工单已转派",
        "data": {
            "ticket_id": ticket_id,
            "to_user_id": data.to_user_id,
            "reason": data.reason,
            "transfer_time": datetime.now().isoformat()
        }
    }


@router.post("/tickets/{ticket_id}/feedback", summary="销售反馈评价")
async def feedback_ticket(
    ticket_id: int,
    satisfaction_score: int = Body(..., ge=1, le=5, description="满意度1-5分"),
    feedback: str = Body("", description="反馈意见"),
    current_user_id: int = Query(1)
):
    """销售对工单进行评价"""
    return {
        "code": 200,
        "message": "评价成功",
        "data": {
            "ticket_id": ticket_id,
            "satisfaction_score": satisfaction_score,
            "feedback": feedback,
            "status": "closed"
        }
    }


@router.post("/tickets/{ticket_id}/deliverables", summary="上传交付物")
async def upload_deliverable(
    ticket_id: int,
    name: str = Body(...),
    file_path: str = Body(...),
    file_type: str = Body(""),
    current_user_id: int = Query(1)
):
    """上传工单交付物"""
    return {
        "code": 200,
        "message": "上传成功",
        "data": {
            "id": 1,
            "ticket_id": ticket_id,
            "name": name,
            "file_path": file_path,
            "file_type": file_type,
            "status": "draft",
            "created_at": datetime.now().isoformat()
        }
    }


# ==================== 方案管理接口 ====================

@router.post("/solutions", summary="创建方案")
async def create_solution(
    data: CreateSolutionRequest,
    current_user_id: int = Query(1),
    current_user_name: str = Query("售前工程师")
):
    """创建技术方案"""
    solution_no = f"FA{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    return {
        "code": 200,
        "message": "方案创建成功",
        "data": {
            "id": 1,
            "solution_no": solution_no,
            "name": data.name,
            "status": "draft",
            "status_label": "草稿",
            "author_id": current_user_id,
            "author_name": current_user_name,
            "created_at": datetime.now().isoformat()
        }
    }


@router.get("/solutions", summary="获取方案列表")
async def get_solutions(
    status: Optional[str] = Query(None),
    industry: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    page: int = Query(1),
    page_size: int = Query(20),
    current_user_id: int = Query(1)
):
    """获取方案列表"""
    solutions = [
        {
            "id": 1,
            "solution_no": "FA20250102001",
            "name": "XX汽车传感器综合测试设备技术方案",
            "industry": "汽车",
            "test_type": "综合测试",
            "customer_name": "XX汽车科技",
            "status": "review",
            "status_label": "待审核",
            "estimated_cost": 800000,
            "suggested_price": 980000,
            "author_name": "王工",
            "created_at": "2025-01-02 14:30:00",
            "version": "V1.0"
        },
        {
            "id": 2,
            "solution_no": "FA20250101001",
            "name": "YY电子连接器寿命测试设备技术方案",
            "industry": "3C电子",
            "test_type": "寿命测试",
            "customer_name": "YY电子科技",
            "status": "delivered",
            "status_label": "已交付",
            "estimated_cost": 350000,
            "suggested_price": 450000,
            "author_name": "李工",
            "created_at": "2025-01-01 10:00:00",
            "version": "V2.0"
        }
    ]
    
    return {
        "code": 200,
        "data": {
            "solutions": solutions,
            "total": len(solutions),
            "page": page,
            "page_size": page_size
        }
    }


@router.get("/solutions/{solution_id}", summary="获取方案详情")
async def get_solution_detail(solution_id: int):
    """获取方案详情"""
    solution = {
        "id": solution_id,
        "solution_no": "FA20250102001",
        "name": "XX汽车传感器综合测试设备技术方案",
        "solution_type": "custom",
        "industry": "汽车",
        "test_type": "综合测试",
        "ticket_id": 1002,
        "customer_id": 100,
        "customer_name": "XX汽车科技有限公司",
        "opportunity_id": 200,
        "requirement_summary": "客户需要一台能够同时测试温度传感器、压力传感器、位移传感器的综合测试设备。\n\n测试要求：\n1. 温度测试范围：-40℃~150℃\n2. 压力测试范围：0~10MPa\n3. 位移测试精度：±0.01mm\n4. 节拍要求：30秒/件\n5. 需要对接客户MES系统",
        "solution_overview": "基于客户需求，我们设计了一套集成式传感器综合测试系统...",
        "technical_spec": "设备技术规格...",
        "status": "review",
        "status_label": "待审核",
        "version": "V1.0",
        "cost_items": [
            {"category": "机械部分", "item_name": "测试工位框架", "quantity": 1, "unit_price": 50000, "amount": 50000},
            {"category": "机械部分", "item_name": "传感器夹具", "quantity": 3, "unit_price": 15000, "amount": 45000},
            {"category": "电气部分", "item_name": "PLC控制系统", "quantity": 1, "unit_price": 35000, "amount": 35000},
            {"category": "电气部分", "item_name": "伺服电机", "quantity": 4, "unit_price": 8000, "amount": 32000},
            {"category": "软件部分", "item_name": "上位机软件", "quantity": 1, "unit_price": 80000, "amount": 80000},
            {"category": "软件部分", "item_name": "MES对接", "quantity": 1, "unit_price": 30000, "amount": 30000}
        ],
        "cost_summary": {
            "机械部分": 250000,
            "电气部分": 180000,
            "软件部分": 120000,
            "标准件": 150000,
            "人工成本": 80000,
            "其他": 20000,
            "total": 800000
        },
        "estimated_cost": 800000,
        "suggested_price": 980000,
        "estimated_hours": 800,
        "estimated_duration": 60,
        "author_id": 10,
        "author_name": "王工",
        "created_at": "2025-01-02 14:30:00",
        "updated_at": "2025-01-03 09:00:00",
        "review_status": "pending",
        "attachments": [
            {"name": "技术方案V1.0.docx", "path": "/files/solution/1/方案.docx"},
            {"name": "设备布局图.dwg", "path": "/files/solution/1/布局图.dwg"}
        ]
    }
    
    return {
        "code": 200,
        "data": solution
    }


@router.put("/solutions/{solution_id}", summary="更新方案")
async def update_solution(
    solution_id: int,
    data: SubmitSolutionRequest,
    current_user_id: int = Query(1)
):
    """更新方案内容"""
    total_cost = sum(item.quantity * item.unit_price for item in data.cost_items)
    
    return {
        "code": 200,
        "message": "方案更新成功",
        "data": {
            "id": solution_id,
            "estimated_cost": total_cost,
            "suggested_price": data.suggested_price or total_cost * 1.2,
            "updated_at": datetime.now().isoformat()
        }
    }


@router.post("/solutions/{solution_id}/submit-review", summary="提交审核")
async def submit_solution_review(
    solution_id: int,
    current_user_id: int = Query(1)
):
    """提交方案审核"""
    return {
        "code": 200,
        "message": "已提交审核",
        "data": {
            "id": solution_id,
            "status": "review",
            "submit_time": datetime.now().isoformat()
        }
    }


@router.post("/solutions/{solution_id}/review", summary="审核方案")
async def review_solution(
    solution_id: int,
    approved: bool = Body(...),
    comment: str = Body(""),
    current_user_id: int = Query(1),
    current_user_name: str = Query("主管")
):
    """审核方案（主管）"""
    return {
        "code": 200,
        "message": "审核通过" if approved else "审核驳回",
        "data": {
            "id": solution_id,
            "review_status": "approved" if approved else "rejected",
            "status": "approved" if approved else "draft",
            "reviewer_id": current_user_id,
            "reviewer_name": current_user_name,
            "review_comment": comment,
            "review_time": datetime.now().isoformat()
        }
    }


# ==================== 方案模板库接口 ====================

@router.get("/templates", summary="获取方案模板列表")
async def get_solution_templates(
    industry: Optional[str] = Query(None),
    test_type: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None)
):
    """获取方案模板列表"""
    templates = [
        {
            "id": 1,
            "template_no": "TPL-001",
            "name": "汽车传感器综合测试设备通用方案",
            "industry": "汽车",
            "test_type": "综合测试",
            "description": "适用于各类汽车传感器的综合测试需求",
            "use_count": 23,
            "is_active": True
        },
        {
            "id": 2,
            "template_no": "TPL-002",
            "name": "新能源电池包气密性检测设备方案",
            "industry": "新能源",
            "test_type": "气密性测试",
            "description": "适用于动力电池包的气密性检测",
            "use_count": 18,
            "is_active": True
        },
        {
            "id": 3,
            "template_no": "TPL-003",
            "name": "连接器插拔寿命测试机方案",
            "industry": "通用",
            "test_type": "寿命测试",
            "description": "适用于各类连接器的插拔寿命测试",
            "use_count": 12,
            "is_active": True
        }
    ]
    
    if industry:
        templates = [t for t in templates if t["industry"] == industry]
    
    return {
        "code": 200,
        "data": templates
    }


@router.get("/templates/{template_id}", summary="获取模板详情")
async def get_template_detail(template_id: int):
    """获取模板详情"""
    return {
        "code": 200,
        "data": {
            "id": template_id,
            "template_no": "TPL-001",
            "name": "汽车传感器综合测试设备通用方案",
            "industry": "汽车",
            "test_type": "综合测试",
            "description": "适用于各类汽车传感器的综合测试需求",
            "content_template": "# 技术方案\n\n## 1. 项目概述\n...",
            "cost_template": [
                {"category": "机械部分", "items": ["测试工位", "夹具", "治具"]},
                {"category": "电气部分", "items": ["PLC", "伺服", "传感器"]},
                {"category": "软件部分", "items": ["上位机", "数据库", "报表"]}
            ],
            "use_count": 23
        }
    }


@router.post("/solutions/{solution_id}/use-template", summary="使用模板创建方案")
async def use_template(
    solution_id: int,
    template_id: int = Body(...),
    current_user_id: int = Query(1)
):
    """基于模板创建方案"""
    return {
        "code": 200,
        "message": "模板已应用",
        "data": {
            "solution_id": solution_id,
            "template_id": template_id
        }
    }


# ==================== 统计分析接口 ====================

@router.get("/statistics/dashboard", summary="工作台统计")
async def get_dashboard_statistics(
    current_user_id: int = Query(1),
    role: str = Query("presale")
):
    """获取工作台统计数据"""
    return {
        "code": 200,
        "data": {
            "tickets": {
                "pending": 3,
                "processing": 5,
                "completed_today": 2,
                "completed_month": 32
            },
            "solutions": {
                "draft": 2,
                "review": 1,
                "approved_month": 8
            },
            "response": {
                "avg_response_hours": 1.8,
                "response_rate": 0.95,
                "completion_rate": 0.88
            },
            "satisfaction": {
                "avg_score": 4.6,
                "five_star_rate": 0.72
            },
            "workload": {
                "planned_hours": 40,
                "actual_hours": 32,
                "utilization_rate": 0.8
            }
        }
    }


@router.get("/statistics/tickets", summary="工单统计")
async def get_ticket_statistics(
    start_date: date = Query(...),
    end_date: date = Query(...),
    group_by: str = Query("day", description="分组:day/week/month")
):
    """获取工单统计数据"""
    return {
        "code": 200,
        "data": {
            "summary": {
                "total": 45,
                "completed": 32,
                "completion_rate": 0.71,
                "avg_response_hours": 1.8,
                "avg_completion_hours": 12.5
            },
            "by_type": {
                "consult": 15,
                "solution": 12,
                "meeting": 8,
                "site_visit": 5,
                "tender": 3,
                "other": 2
            },
            "by_urgency": {
                "normal": 30,
                "urgent": 12,
                "very_urgent": 3
            },
            "trend": [
                {"date": "2025-01-01", "count": 8},
                {"date": "2025-01-02", "count": 12},
                {"date": "2025-01-03", "count": 10}
            ]
        }
    }


@router.get("/statistics/solutions", summary="方案统计")
async def get_solution_statistics(
    start_date: date = Query(...),
    end_date: date = Query(...)
):
    """获取方案统计数据"""
    return {
        "code": 200,
        "data": {
            "summary": {
                "total": 12,
                "won": 4,
                "lost": 1,
                "pending": 7,
                "conversion_rate": 0.4
            },
            "by_industry": {
                "汽车": 5,
                "3C电子": 3,
                "新能源": 2,
                "医疗": 1,
                "其他": 1
            },
            "amount": {
                "total_estimated": 8500000,
                "total_won": 3200000
            }
        }
    }


@router.get("/statistics/personnel", summary="人员工作量统计")
async def get_personnel_statistics(
    start_date: date = Query(...),
    end_date: date = Query(...)
):
    """获取人员工作量统计"""
    return {
        "code": 200,
        "data": [
            {
                "user_id": 10,
                "user_name": "王工",
                "tickets_count": 15,
                "solutions_count": 5,
                "actual_hours": 120,
                "response_rate": 0.98,
                "satisfaction_score": 4.8
            },
            {
                "user_id": 11,
                "user_name": "李工",
                "tickets_count": 12,
                "solutions_count": 4,
                "actual_hours": 96,
                "response_rate": 0.95,
                "satisfaction_score": 4.6
            },
            {
                "user_id": 12,
                "user_name": "张工",
                "tickets_count": 10,
                "solutions_count": 3,
                "actual_hours": 80,
                "response_rate": 0.92,
                "satisfaction_score": 4.5
            }
        ]
    }


# ==================== 售前人员列表 ====================

@router.get("/engineers", summary="获取售前工程师列表")
async def get_presale_engineers():
    """获取售前工程师列表（用于分配工单）"""
    return {
        "code": 200,
        "data": [
            {"id": 10, "name": "王工", "title": "高级售前工程师", "specialties": ["汽车", "新能源"], "current_tickets": 3},
            {"id": 11, "name": "李工", "title": "售前工程师", "specialties": ["3C电子", "医疗"], "current_tickets": 2},
            {"id": 12, "name": "张工", "title": "售前工程师", "specialties": ["通用"], "current_tickets": 4}
        ]
    }


# ==================== 客户技术档案 ====================

@router.get("/customers/{customer_id}/tech-profile", summary="获取客户技术档案")
async def get_customer_tech_profile(customer_id: int):
    """获取客户技术档案"""
    return {
        "code": 200,
        "data": {
            "customer_id": customer_id,
            "customer_name": "XX汽车科技有限公司",
            "industry": "汽车",
            "business_scope": "汽车传感器研发与生产",
            "common_test_types": ["功能测试", "环境测试", "寿命测试"],
            "technical_requirements": "对测试精度要求高，需要满足IATF16949质量标准",
            "quality_standards": "IATF16949, ISO9001",
            "existing_equipment": "已有3台我司生产的测试设备",
            "mes_system": "西门子MES",
            "cooperation_history": "2020年开始合作，累计采购5台设备",
            "success_cases": [
                {"name": "温度传感器测试设备", "year": 2020, "amount": 850000},
                {"name": "压力传感器测试线", "year": 2022, "amount": 1200000}
            ],
            "technical_contacts": [
                {"name": "李经理", "title": "技术总监", "phone": "138****1234"},
                {"name": "王工", "title": "测试工程师", "phone": "139****5678"}
            ]
        }
    }


@router.put("/customers/{customer_id}/tech-profile", summary="更新客户技术档案")
async def update_customer_tech_profile(
    customer_id: int,
    data: Dict = Body(...),
    current_user_id: int = Query(1)
):
    """更新客户技术档案"""
    return {
        "code": 200,
        "message": "档案更新成功",
        "data": {
            "customer_id": customer_id,
            "updated_at": datetime.now().isoformat()
        }
    }
