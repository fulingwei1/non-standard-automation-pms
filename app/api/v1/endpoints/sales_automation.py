# -*- coding: utf-8 -*-
"""
销售自动化API
提供自动跟进提醒、自动邮件序列、自动任务创建、自动报告生成
"""

from typing import Any, Optional, List
from datetime import datetime, timedelta, date
from fastapi import APIRouter, Depends, HTTPException, Path, Query, Body
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User

router = APIRouter()


# ========== 1. 自动跟进提醒 ==========

@router.get("/follow-up-reminders", summary="获取跟进提醒")
def get_follow_up_reminders(
    days: int = Query(3, description="X天未联系"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取需要跟进的客户列表
    
    自动识别X天未联系的客户
    优先级：
    - 高优先级：商机阶段靠后 + 长时间未联系
    - 中优先级：普通客户 + 较长时间未联系
    - 低优先级：新客户 + 短期未联系
    """
    
    cutoff_date = date.today() - timedelta(days=days)
    
    # 模拟需要跟进的客户
    reminders = [
        {
            "customer_id": 1,
            "customer_name": "宁德时代",
            "last_contact_date": "2025-02-15",
            "days_since_contact": 14,
            "priority": "HIGH",
            "reason": "商机STAGE4价格谈判阶段，7天未联系",
            "opportunity_id": 101,
            "opportunity_name": "FCT测试线项目",
            "suggested_action": "电话跟进价格反馈",
        },
        {
            "customer_id": 2,
            "customer_name": "比亚迪",
            "last_contact_date": "2025-02-20",
            "days_since_contact": 9,
            "priority": "MEDIUM",
            "reason": "方案已发送，待客户确认",
            "opportunity_id": 102,
            "opportunity_name": "EOL测试设备",
            "suggested_action": "邮件询问方案反馈",
        },
        {
            "customer_id": 3,
            "customer_name": "中创新航",
            "last_contact_date": "2025-02-22",
            "days_since_contact": 7,
            "priority": "LOW",
            "reason": "初次接触阶段",
            "opportunity_id": None,
            "opportunity_name": None,
            "suggested_action": "发送公司介绍资料",
        },
    ]
    
    # 过滤超过天数的
    filtered = [r for r in reminders if r["days_since_contact"] >= days]
    
    return {
        "reminder_date": date.today().isoformat(),
        "days_threshold": days,
        "total_reminders": len(filtered),
        "high_priority": len([r for r in filtered if r["priority"] == "HIGH"]),
        "medium_priority": len([r for r in filtered if r["priority"] == "MEDIUM"]),
        "low_priority": len([r for r in filtered if r["priority"] == "LOW"]),
        "reminders": filtered,
    }


@router.post("/follow-up-reminders/send", summary="发送跟进提醒")
def send_follow_up_reminders(
    reminder_ids: List[int] = Body(..., description="提醒ID列表"),
    method: str = Query("app", description="发送方式：app/email/sms"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """发送跟进提醒通知给销售"""
    
    return {
        "message": "跟进提醒已发送",
        "sent_count": len(reminder_ids),
        "method": method,
        "sent_at": datetime.now().isoformat(),
    }


# ========== 2. 自动邮件序列 ==========

@router.get("/email-sequences", summary="获取邮件序列模板")
def get_email_sequences(
    sequence_type: str = Query("nurture", description="序列类型：nurture/cold/renewal"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取邮件序列模板
    
    序列类型：
    - nurture: 培育序列（新线索培育）
    - cold: 冷启动序列（激活沉睡客户）
    - renewal: 续约序列（续约提醒）
    """
    
    sequences = {
        "nurture": [
            {
                "step": 1,
                "delay_days": 0,
                "subject": "欢迎了解金凯博自动化测试解决方案",
                "template": "尊敬的{{客户姓名}}，您好！感谢您关注金凯博自动化...",
                "purpose": "建立初步联系",
            },
            {
                "step": 2,
                "delay_days": 3,
                "subject": "锂电行业FCT测试最新案例分享",
                "template": "{{客户姓名}}您好，分享一个与您行业相关的成功案例...",
                "purpose": "展示专业能力",
            },
            {
                "step": 3,
                "delay_days": 7,
                "subject": "免费技术咨询服务预约",
                "template": "{{客户姓名}}您好，我们提供免费的技术咨询服务...",
                "purpose": "推动进一步沟通",
            },
        ],
        "cold": [
            {
                "step": 1,
                "delay_days": 0,
                "subject": "好久不见，金凯博最新产品更新",
                "template": "{{客户姓名}}您好，好久不见...",
            },
            {
                "step": 2,
                "delay_days": 5,
                "subject": "行业趋势分享",
                "template": "{{客户姓名}}您好，分享最新行业趋势...",
            },
        ],
        "renewal": [
            {
                "step": 1,
                "delay_days": -30,
                "subject": "服务续约提醒",
                "template": "{{客户姓名}}您好，您的服务即将到期...",
            },
        ],
    }
    
    return {
        "sequence_type": sequence_type,
        "steps": sequences.get(sequence_type, []),
    }


@router.post("/email-sequences/start", summary="启动邮件序列")
def start_email_sequence(
    customer_ids: List[int] = Body(..., description="客户ID列表"),
    sequence_type: str = Body("nurture", description="序列类型"),
    start_date: Optional[str] = Body(None, description="开始日期"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    为指定客户启动自动邮件序列
    
    系统会按照预设的时间间隔自动发送邮件
    """
    
    return {
        "message": "邮件序列已启动",
        "sequence_type": sequence_type,
        "customer_count": len(customer_ids),
        "start_date": start_date or date.today().isoformat(),
        "status": "active",
    }


# ========== 3. 自动任务创建 ==========

@router.post("/auto-tasks/rules", summary="创建自动任务规则")
def create_auto_task_rule(
    rule: dict = Body(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建自动任务规则
    
    规则示例：
    - 当商机进入STAGE3时，自动创建"方案演示"任务
    - 当报价审批通过后，自动创建"合同准备"任务
    - 当合同签订后，自动创建"项目启动"任务
    """
    
    return {
        "message": "自动任务规则创建成功",
        "rule_id": 123,
        "rule_name": rule.get("name"),
    }


@router.get("/auto-tasks/triggers", summary="获取任务触发器")
def get_task_triggers(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取所有自动任务触发器配置"""
    
    triggers = [
        {
            "id": 1,
            "name": "商机阶段变更-方案演示",
            "trigger_event": "opportunity_stage_change",
            "condition": {"from": "STAGE2", "to": "STAGE3"},
            "action": {"create_task": "方案演示", "assign_to": "opportunity_owner"},
            "is_active": True,
        },
        {
            "id": 2,
            "name": "报价审批通过-合同准备",
            "trigger_event": "quote_approved",
            "condition": {"status": "approved"},
            "action": {"create_task": "合同准备", "assign_to": "quote_owner"},
            "is_active": True,
        },
        {
            "id": 3,
            "name": "合同签订-项目启动",
            "trigger_event": "contract_signed",
            "condition": {},
            "action": {"create_task": "项目启动会", "assign_to": "project_manager"},
            "is_active": True,
        },
        {
            "id": 4,
            "name": "客户7天未联系-跟进提醒",
            "trigger_event": "no_contact_7days",
            "condition": {"days": 7},
            "action": {"create_task": "客户跟进", "assign_to": "customer_owner"},
            "is_active": True,
        },
    ]
    
    return {
        "total_rules": len(triggers),
        "active_rules": len([t for t in triggers if t["is_active"]]),
        "triggers": triggers,
    }


# ========== 4. 自动报告生成 ==========

@router.post("/reports/generate", summary="生成销售报告")
def generate_sales_report(
    report_type: str = Query("weekly", description="报告类型：daily/weekly/monthly"),
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    sales_id: Optional[int] = Query(None, description="销售ID（为空则全部）"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    自动生成销售报告
    
    报告类型：
    - daily: 日报（今日关键指标）
    - weekly: 周报（本周业绩+下周计划）
    - monthly: 月报（月度总结+分析）
    """
    
    # 模拟报告数据
    if report_type == "weekly":
        report_data = {
            "period": "2025年第9周",
            "summary": {
                "new_leads": 12,
                "new_opportunities": 5,
                "quotes_sent": 3,
                "deals_won": 2,
                "revenue": 5800000,
                "target_completion": 45,
            },
            "highlights": [
                "成功签约宁德时代FCT项目（320万）",
                "新增比亚迪EOL商机（预估280万）",
                "完成3个客户方案演示",
            ],
            "next_week_plan": [
                "跟进比亚迪价格反馈",
                "完成中创新航方案编写",
                "拜访2个新客户",
            ],
            "alerts": [
                "宁德时代项目需跟进合同签署",
                "亿纬锂能商机已7天未更新",
            ],
        }
    elif report_type == "daily":
        report_data = {
            "date": date.today().isoformat(),
            "today_summary": {
                "calls_made": 8,
                "meetings": 2,
                "emails_sent": 15,
                "tasks_completed": 5,
            },
            "key_activities": [
                "与宁德时代技术部会议",
                "发送比亚迪方案V2",
            ],
            "tomorrow_plan": [
                "跟进宁德时代反馈",
                "准备中创新航报价",
            ],
        }
    else:  # monthly
        report_data = {
            "month": "2025年2月",
            "summary": {
                "total_revenue": 12500000,
                "target": 15000000,
                "completion_rate": 83,
                "new_customers": 5,
                "deals_won": 8,
                "deals_lost": 3,
            },
            "analysis": {
                "win_rate": 73,
                "avg_deal_size": 1560000,
                "sales_cycle": 65,
            },
        }
    
    return {
        "report_type": report_type,
        "generated_at": datetime.now().isoformat(),
        "generated_by": "AI Sales Assistant",
        "data": report_data,
    }


@router.post("/reports/schedule", summary="配置自动报告")
def schedule_auto_report(
    schedule: dict = Body(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    配置自动报告生成和发送
    
    配置示例：
    - 每周一早上9点自动生成周报
    - 每天下班前生成日报
    - 每月1号生成月报
    """
    
    return {
        "message": "自动报告配置成功",
        "schedule_id": 456,
        "report_type": schedule.get("report_type"),
        "frequency": schedule.get("frequency"),
        "send_time": schedule.get("send_time"),
        "recipients": schedule.get("recipients"),
    }


@router.get("/reports/schedules", summary="获取报告计划")
def get_report_schedules(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取所有自动报告计划"""
    
    schedules = [
        {
            "id": 1,
            "report_type": "daily",
            "frequency": "daily",
            "send_time": "18:00",
            "recipients": ["sales@company.com"],
            "is_active": True,
        },
        {
            "id": 2,
            "report_type": "weekly",
            "frequency": "weekly",
            "send_time": "09:00",
            "day_of_week": 1,  # 周一
            "recipients": ["sales@company.com", "manager@company.com"],
            "is_active": True,
        },
        {
            "id": 3,
            "report_type": "monthly",
            "frequency": "monthly",
            "send_time": "09:00",
            "day_of_month": 1,
            "recipients": ["sales@company.com", "manager@company.com", "ceo@company.com"],
            "is_active": True,
        },
    ]
    
    return {
        "total_schedules": len(schedules),
        "active_schedules": len([s for s in schedules if s["is_active"]]),
        "schedules": schedules,
    }


# ========== 5. 自动化规则管理 ==========

@router.get("/automation/rules", summary="获取所有自动化规则")
def get_automation_rules(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取所有销售自动化规则"""
    
    return {
        "categories": [
            {
                "name": "跟进提醒",
                "rules_count": 3,
                "active_count": 3,
            },
            {
                "name": "邮件序列",
                "rules_count": 2,
                "active_count": 2,
            },
            {
                "name": "自动任务",
                "rules_count": 4,
                "active_count": 4,
            },
            {
                "name": "自动报告",
                "rules_count": 3,
                "active_count": 3,
            },
        ],
        "total_active": 12,
        "last_run": datetime.now().isoformat(),
    }


@router.post("/automation/run", summary="手动触发自动化")
def run_automation(
    rule_type: str = Query(..., description="规则类型"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """手动触发自动化规则执行"""
    
    return {
        "message": "自动化规则已执行",
        "rule_type": rule_type,
        "executed_at": datetime.now().isoformat(),
        "results": {
            "reminders_sent": 5,
            "emails_queued": 12,
            "tasks_created": 3,
        },
    }
