# -*- coding: utf-8 -*-
"""
销售协同 API
提供内部协作、知识共享、技术支持请求
"""

from typing import Any, Optional, List
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, Path, Query, Body
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User

router = APIRouter()


# ========== 1. 内部协作留言 ==========

@router.get("/collaboration/messages", summary="协作留言列表")
def get_collaboration_messages(
    customer_id: Optional[int] = Query(None, description="客户 ID"),
    opportunity_id: Optional[int] = Query(None, description="商机 ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    客户/商机相关的内部协作留言
    
    用于销售团队内部沟通，不展示给客户
    """
    
    # 模拟协作留言数据
    messages = [
        {
            "message_id": 1,
            "customer_id": 1,
            "opportunity_id": 101,
            "author": {
                "id": 101,
                "name": "张三",
                "avatar": "https://avatar.example.com/101.jpg",
            },
            "content": "这个客户的技术总监很关注测试精度，建议准备详细的技术参数对比表",
            "mentions": ["@李四"],
            "created_at": "2025-02-28 14:30:00",
            "is_internal": True,
        },
        {
            "message_id": 2,
            "customer_id": 1,
            "opportunity_id": 101,
            "author": {
                "id": 102,
                "name": "李四",
                "avatar": "https://avatar.example.com/102.jpg",
            },
            "content": "收到，我明天准备一份竞品对比报告",
            "mentions": [],
            "created_at": "2025-02-28 15:00:00",
            "is_internal": True,
        },
        {
            "message_id": 3,
            "customer_id": 1,
            "opportunity_id": 101,
            "author": {
                "id": 103,
                "name": "王五",
                "avatar": "https://avatar.example.com/103.jpg",
            },
            "content": "需要技术支持吗？我可以安排售前工程师协助",
            "mentions": ["@张三"],
            "created_at": "2025-02-27 10:00:00",
            "is_internal": True,
        },
    ]
    
    return {
        "total_count": len(messages),
        "messages": messages,
        "participants": [
            {"id": 101, "name": "张三", "role": "销售"},
            {"id": 102, "name": "李四", "role": "销售"},
            {"id": 103, "name": "王五", "role": "销售经理"},
        ],
    }


@router.post("/collaboration/messages", summary="发送协作留言")
def create_collaboration_message(
    content: str = Body(..., description="留言内容"),
    customer_id: Optional[int] = Body(None, description="客户 ID"),
    opportunity_id: Optional[int] = Body(None, description="商机 ID"),
    mentions: List[str] = Body([], description="提及的用户"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """发送内部协作留言"""
    
    return {
        "message": "留言已发送",
        "message_id": 123,
        "content": content,
        "mentions": mentions,
        "notified_users": mentions,
    }


# ========== 2. 技术支持请求 ==========

@router.get("/collaboration/support-requests", summary="技术支持请求列表")
def get_support_requests(
    status: Optional[str] = Query("pending", description="状态：pending/processing/completed"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    销售向技术团队发起的技术支持请求
    """
    
    requests = [
        {
            "request_id": 1,
            "title": "FCT 测试方案技术咨询",
            "opportunity_id": 101,
            "customer_name": "宁德时代",
            "requester": {
                "id": 101,
                "name": "张三",
            },
            "assignee": {
                "id": 201,
                "name": "陈工",
                "department": "技术部",
            },
            "priority": "HIGH",
            "status": "processing",
            "description": "客户需要了解我们的 FCT 设备与竞品的技术差异，需要准备详细对比报告",
            "required_skills": ["FCT", "测试方案"],
            "deadline": "2025-03-05",
            "created_at": "2025-02-28 10:00:00",
            "updated_at": "2025-02-28 14:00:00",
        },
        {
            "request_id": 2,
            "title": "EOL 设备选型建议",
            "opportunity_id": 102,
            "customer_name": "比亚迪",
            "requester": {
                "id": 102,
                "name": "李四",
            },
            "assignee": None,
            "priority": "MEDIUM",
            "status": "pending",
            "description": "客户需要在标准型和增强型之间做选择，需要技术建议",
            "required_skills": ["EOL", "产品选型"],
            "deadline": "2025-03-03",
            "created_at": "2025-02-27 15:00:00",
            "updated_at": "2025-02-27 15:00:00",
        },
    ]
    
    return {
        "total_count": len(requests),
        "pending_count": len([r for r in requests if r["status"] == "pending"]),
        "processing_count": len([r for r in requests if r["status"] == "processing"]),
        "requests": requests,
    }


@router.post("/collaboration/support-requests", summary="创建技术支持请求")
def create_support_request(
    title: str = Body(..., description="请求标题"),
    description: str = Body(..., description="详细描述"),
    opportunity_id: int = Body(..., description="商机 ID"),
    priority: str = Body("MEDIUM", description="优先级：LOW/MEDIUM/HIGH"),
    required_skills: List[str] = Body([], description="需要的技能"),
    deadline: str = Body(..., description="截止日期 YYYY-MM-DD"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """创建技术支持请求"""
    
    return {
        "message": "技术支持请求已创建",
        "request_id": 124,
        "title": title,
        "status": "pending",
        "estimated_response": "24 小时内",
    }


# ========== 3. 知识共享库 ==========

@router.get("/collaboration/knowledge-base", summary="知识库列表")
def get_knowledge_base(
    category: Optional[str] = Query(None, description="分类：case/competitor/product/skill"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    销售知识库
    
    分类：
    - case: 成功案例
    - competitor: 竞品分析
    - product: 产品资料
    - skill: 销售技巧
    """
    
    articles = [
        {
            "article_id": 1,
            "title": "宁德时代 FCT 项目成功案例",
            "category": "case",
            "category_name": "成功案例",
            "author": {
                "id": 101,
                "name": "张三",
            },
            "summary": "350 万 FCT 测试线项目，从接触 to 签约 45 天，关键成功因素分析",
            "tags": ["FCT", "锂电", "大客户"],
            "views": 256,
            "likes": 42,
            "created_at": "2025-01-15",
            "updated_at": "2025-01-20",
        },
        {
            "article_id": 2,
            "title": "竞品对比：我们 vs 竞品 A vs 竞品 B",
            "category": "competitor",
            "category_name": "竞品分析",
            "author": {
                "id": 103,
                "name": "王五",
            },
            "summary": "详细对比技术参数、价格、服务，附应对策略",
            "tags": ["竞品分析", "FCT", "EOL"],
            "views": 512,
            "likes": 89,
            "created_at": "2025-02-01",
            "updated_at": "2025-02-10",
        },
        {
            "article_id": 3,
            "title": "价格谈判 10 大技巧",
            "category": "skill",
            "category_name": "销售技巧",
            "author": {
                "id": 104,
                "name": "赵六",
            },
            "summary": "总结多年价格谈判经验，10 个实用技巧和话术",
            "tags": ["谈判技巧", "价格"],
            "views": 890,
            "likes": 156,
            "created_at": "2024-12-01",
            "updated_at": "2025-01-05",
        },
        {
            "article_id": 4,
            "title": "锂电行业客户特点分析",
            "category": "product",
            "category_name": "产品资料",
            "author": {
                "id": 105,
                "name": "钱七",
            },
            "summary": "锂电行业客户采购流程、决策链、关注点分析",
            "tags": ["锂电", "行业分析"],
            "views": 345,
            "likes": 67,
            "created_at": "2025-01-20",
            "updated_at": "2025-02-01",
        },
    ]
    
    # 过滤
    if category:
        articles = [a for a in articles if a["category"] == category]
    if keyword:
        articles = [a for a in articles if keyword.lower() in a["title"].lower() or keyword.lower() in a["summary"].lower()]
    
    return {
        "total_count": len(articles),
        "categories": [
            {"code": "case", "name": "成功案例", "count": 1},
            {"code": "competitor", "name": "竞品分析", "count": 1},
            {"code": "product", "name": "产品资料", "count": 1},
            {"code": "skill", "name": "销售技巧", "count": 1},
        ],
        "articles": articles,
    }


@router.post("/collaboration/knowledge-base", summary="贡献知识文章")
def create_knowledge_article(
    title: str = Body(..., description="标题"),
    content: str = Body(..., description="内容"),
    category: str = Body(..., description="分类"),
    tags: List[str] = Body([], description="标签"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """贡献知识文章到共享库"""
    
    return {
        "message": "文章已提交",
        "article_id": 125,
        "status": "pending_review",
        "points_earned": 10,
    }


# ========== 4. 销售经验分享 ==========

@router.get("/collaboration/share-sessions", summary="经验分享会列表")
def get_share_sessions(
    status: Optional[str] = Query("upcoming", description="状态：upcoming/completed"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """销售经验分享会"""
    
    sessions = [
        {
            "session_id": 1,
            "title": "Q1 大单签约经验分享",
            "speaker": {
                "id": 101,
                "name": "张三",
                "title": "高级销售",
            },
            "scheduled_time": "2025-03-05 15:00:00",
            "duration_minutes": 60,
            "format": "online",
            "max_participants": 50,
            "registered_count": 32,
            "status": "upcoming",
            "description": "分享宁德时代 350 万 FCT 项目签约经验，包括需求挖掘、技术方案、价格谈判等关键环节",
        },
        {
            "session_id": 2,
            "title": "竞品应对策略培训",
            "speaker": {
                "id": 103,
                "name": "王五",
                "title": "销售经理",
            },
            "scheduled_time": "2025-02-20 14:00:00",
            "duration_minutes": 90,
            "format": "offline",
            "location": "深圳会议室 A",
            "max_participants": 30,
            "registered_count": 30,
            "status": "completed",
            "description": "针对主要竞品的应对策略培训，包含实战演练",
            "recording_url": "https://example.com/recording/2",
            "materials": ["竞品对比表.pdf", "应对话术.docx"],
        },
    ]
    
    return {
        "total_count": len(sessions),
        "upcoming_count": len([s for s in sessions if s["status"] == "upcoming"]),
        "sessions": sessions,
    }


@router.post("/collaboration/share-sessions/register", summary="报名经验分享会")
def register_share_session(
    session_id: int = Body(..., description="分享会 ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """报名参与经验分享会"""
    
    return {
        "message": "报名成功",
        "session_id": session_id,
        "calendar_invite_sent": True,
    }


# ========== 5. 协同数据统计 ==========

@router.get("/collaboration/stats", summary="协同数据统计")
def get_collaboration_stats(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """个人/团队协同数据统计"""
    
    return {
        "personal_stats": {
            "user_id": current_user.id,
            "user_name": current_user.username,
            "messages_sent": 156,
            "support_requests": {
                "created": 12,
                "completed": 10,
                "pending": 2,
            },
            "knowledge_contributions": 5,
            "share_sessions": {
                "attended": 8,
                "presented": 2,
            },
            "collaboration_score": 85,
        },
        "team_stats": {
            "team_name": "华南大区",
            "active_members": 8,
            "total_messages": 1256,
            "total_support_requests": 45,
            "avg_response_time_hours": 4.5,
            "knowledge_base_articles": 32,
            "share_sessions_ytd": 12,
        },
        "top_contributors": [
            {"rank": 1, "name": "张三", "score": 95, "contributions": 25},
            {"rank": 2, "name": "李四", "score": 88, "contributions": 20},
            {"rank": 3, "name": "王五", "score": 82, "contributions": 18},
        ],
    }
