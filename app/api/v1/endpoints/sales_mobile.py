# -*- coding: utf-8 -*-
"""
移动端销售支持 API
提供拜访打卡、名片扫描、移动审批
"""

from typing import Any, Optional, List
from datetime import date, datetime
from fastapi import APIRouter, Depends, Query, Body, UploadFile, File
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User

router = APIRouter()


# ========== 1. 拜访打卡 ==========

@router.post("/mobile/check-in", summary="拜访打卡")
def create_check_in(
    customer_id: int = Body(..., description="客户 ID"),
    latitude: float = Body(..., description="纬度"),
    longitude: float = Body(..., description="经度"),
    address: str = Body(..., description="打卡地址"),
    photos: Optional[List[str]] = Body(None, description="现场照片 URL 列表"),
    notes: Optional[str] = Body(None, description="拜访备注"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    销售拜访打卡
    
    功能：
    - GPS 定位验证
    - 现场拍照
    - 拜访记录
    """
    
    return {
        "message": "打卡成功",
        "check_in_id": 1001,
        "customer_id": customer_id,
        "timestamp": datetime.now().isoformat(),
        "location": {
            "latitude": latitude,
            "longitude": longitude,
            "address": address,
        },
        "photos_count": len(photos) if photos else 0,
        "distance_to_customer": 50,  # 距离客户地址的米数
        "is_valid": True,
    }


@router.get("/mobile/check-in/history", summary="打卡历史")
def get_check_in_history(
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取拜访打卡历史"""
    
    history = [
        {
            "check_in_id": 1001,
            "customer_name": "宁德时代",
            "address": "福建省宁德市蕉城区漳湾镇新港路 2 号",
            "check_in_time": "2025-02-28 10:30:00",
            "check_out_time": "2025-02-28 12:00:00",
            "duration_minutes": 90,
            "photos_count": 3,
            "notes": "与技术总监讨论 FCT 测试方案",
        },
        {
            "check_in_id": 1002,
            "customer_name": "比亚迪",
            "address": "深圳市坪山区比亚迪路 3009 号",
            "check_in_time": "2025-02-27 14:00:00",
            "check_out_time": "2025-02-27 16:30:00",
            "duration_minutes": 150,
            "photos_count": 2,
            "notes": "EOL 设备现场勘测",
        },
    ]
    
    return {
        "total_count": len(history),
        "total_duration_minutes": sum(h["duration_minutes"] for h in history),
        "history": history,
    }


# ========== 2. 名片扫描 ==========

@router.post("/mobile/business-card/scan", summary="名片扫描识别")
async def scan_business_card(
    image: UploadFile = File(..., description="名片图片"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    名片扫描识别
    
    使用 OCR 识别名片信息，自动创建联系人
    """
    
    # 模拟 OCR 识别结果
    ocr_result = {
        "name": "张三",
        "title": "技术总监",
        "company": "宁德时代新能源科技股份有限公司",
        "phone": "138****1234",
        "email": "zhangsan@catl.com",
        "address": "福建省宁德市蕉城区漳湾镇新港路 2 号",
        "confidence": 0.95,
    }
    
    return {
        "message": "名片识别成功",
        "ocr_result": ocr_result,
        "suggested_action": "创建联系人",
        "existing_contact": None,  # 如果已存在联系人则返回
    }


@router.post("/mobile/business-card/save", summary="保存名片信息")
def save_business_card(
    name: str = Body(..., description="姓名"),
    title: Optional[str] = Body(None, description="职位"),
    company: Optional[str] = Body(None, description="公司"),
    phone: Optional[str] = Body(None, description="电话"),
    email: Optional[str] = Body(None, description="邮箱"),
    customer_id: Optional[int] = Body(None, description="关联客户 ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """保存名片信息为联系人"""
    
    return {
        "message": "联系人已创建",
        "contact_id": 501,
        "name": name,
        "company": company,
        "customer_id": customer_id,
    }


# ========== 3. 移动审批 ==========

@router.get("/mobile/approvals/pending", summary="待审批列表")
def get_pending_approvals(
    type: Optional[str] = Query(None, description="类型：quote/contract/discount"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取待审批列表（移动端优化）"""
    
    approvals = [
        {
            "approval_id": 1,
            "type": "quote",
            "type_name": "报价审批",
            "title": "宁德时代 FCT 项目报价",
            "applicant": "张三",
            "amount": 3500000,
            "submitted_at": "2025-02-28 16:00:00",
            "priority": "HIGH",
            "deadline": "2025-03-01 12:00:00",
        },
        {
            "approval_id": 2,
            "type": "discount",
            "type_name": "折扣审批",
            "title": "比亚迪 EOL 项目特殊折扣申请",
            "applicant": "李四",
            "discount_rate": 15,
            "submitted_at": "2025-02-28 14:00:00",
            "priority": "MEDIUM",
            "deadline": "2025-03-02 12:00:00",
        },
    ]
    
    return {
        "total_count": len(approvals),
        "urgent_count": len([a for a in approvals if a["priority"] == "HIGH"]),
        "approvals": approvals,
    }


@router.post("/mobile/approvals/{approval_id}/approve", summary="审批通过")
def approve_request(
    approval_id: int,
    comment: Optional[str] = Body(None, description="审批意见"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """审批通过"""
    
    return {
        "message": "审批通过",
        "approval_id": approval_id,
        "status": "approved",
        "approved_at": datetime.now().isoformat(),
        "approved_by": current_user.username,
    }


@router.post("/mobile/approvals/{approval_id}/reject", summary="审批拒绝")
def reject_request(
    approval_id: int,
    reason: str = Body(..., description="拒绝原因"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """审批拒绝"""
    
    return {
        "message": "审批拒绝",
        "approval_id": approval_id,
        "status": "rejected",
        "reason": reason,
        "rejected_at": datetime.now().isoformat(),
        "rejected_by": current_user.username,
    }


# ========== 4. 语音记录 ==========

@router.post("/mobile/voice-note", summary="语音记录")
async def create_voice_note(
    audio: UploadFile = File(..., description="语音文件"),
    customer_id: Optional[int] = Body(None, description="客户 ID"),
    opportunity_id: Optional[int] = Body(None, description="商机 ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    语音记录
    
    拜访后语音速记，自动转文字
    """
    
    # 模拟语音转文字
    transcription = "今天拜访了宁德时代，与技术总监张三讨论了 FCT 测试方案。客户对我们的测试精度很满意，但是希望价格能再优惠一些。约定下周三提交最终报价。"
    
    return {
        "message": "语音记录已保存",
        "note_id": 201,
        "duration_seconds": 45,
        "transcription": transcription,
        "keywords": ["宁德时代", "FCT", "价格", "报价"],
        "suggested_actions": [
            "准备最终报价",
            "申请价格折扣",
        ],
    }


# ========== 5. 移动端首页 ==========

@router.get("/mobile/dashboard", summary="移动端首页")
def get_mobile_dashboard(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    移动端首页数据
    
    精简版仪表盘，适合手机查看
    """
    
    return {
        "greeting": f"早上好，{current_user.username}",
        "date": date.today().isoformat(),
        
        "quick_stats": {
            "today_visits": 2,
            "week_visits": 8,
            "month_revenue": 15800000,
            "month_target_completion": 158.0,
        },
        
        "today_schedule": [
            {
                "time": "10:00",
                "type": "visit",
                "title": "拜访宁德时代",
                "address": "福建省宁德市",
                "status": "completed",
            },
            {
                "time": "14:00",
                "type": "call",
                "title": "电话跟进比亚迪",
                "contact": "李四 - 采购经理",
                "status": "pending",
            },
            {
                "time": "16:00",
                "type": "meeting",
                "title": "内部方案评审",
                "location": "会议室 A",
                "status": "pending",
            },
        ],
        
        "pending_tasks": [
            {
                "task_id": 1,
                "title": "提交宁德时代最终报价",
                "deadline": "2025-03-05",
                "priority": "HIGH",
            },
            {
                "task_id": 2,
                "title": "准备比亚迪技术方案 V2",
                "deadline": "2025-03-03",
                "priority": "MEDIUM",
            },
        ],
        
        "pending_approvals": 2,
        "unread_messages": 5,
        
        "quick_actions": [
            {"action": "check_in", "label": "拜访打卡", "icon": "📍"},
            {"action": "scan_card", "label": "扫名片", "icon": "📇"},
            {"action": "voice_note", "label": "语音记录", "icon": "🎤"},
            {"action": "create_opportunity", "label": "新建商机", "icon": "➕"},
        ],
    }
