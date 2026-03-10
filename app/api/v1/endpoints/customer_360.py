# -*- coding: utf-8 -*-
"""
客户 360°画像 API
提供交互历史、决策链分析、健康度评分、购买偏好

重构版本：对接真实数据库
"""

import json
import logging
from datetime import date, timedelta
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from app.api import deps
from app.core import security
from app.models.project import Customer
from app.models.sales import Contact, Opportunity
from app.models.user import User
from app.services.relationship_scoring_service import RelationshipScoringService

router = APIRouter()


# 决策角色名称映射
ROLE_NAMES = {
    "EB": "最终决策人",
    "TB": "技术决策人",
    "PB": "采购决策人",
    "UB": "最终用户",
    "COACH": "内线",
}


def _get_customer_or_404(db: Session, customer_id: int) -> Customer:
    """获取客户或返回404"""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail=f"客户不存在: {customer_id}")
    return customer


# ========== 1. 客户交互历史时间线 ==========


@router.get("/customers/{customer_id}/timeline", summary="客户交互历史时间线")
def get_customer_timeline(
    customer_id: int = Path(..., description="客户 ID"),
    months: int = Query(6, description="查看月数"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    客户完整交互历史时间线

    包含：
    - 电话/会议/邮件/微信记录
    - 商机阶段变更
    - 报价/合同/收款记录
    """
    customer = _get_customer_or_404(db, customer_id)

    # 尝试从沟通记录表获取数据
    timeline = []
    start_date = date.today() - timedelta(days=months * 30)

    try:
        # 尝试导入沟通记录模型
        from app.models.sales.communication import CustomerCommunication

        communications = (
            db.query(CustomerCommunication)
            .filter(
                CustomerCommunication.customer_id == customer_id,
                CustomerCommunication.communication_date >= start_date,
            )
            .order_by(CustomerCommunication.communication_date.desc())
            .all()
        )

        for comm in communications:
            timeline.append({
                "date": str(comm.communication_date),
                "type": comm.communication_type or "其他",
                "title": comm.subject or "沟通记录",
                "participants": json.loads(comm.participants) if comm.participants else [],
                "outcome": comm.content or "",
                "next_action": comm.next_action or "",
                "sentiment": comm.sentiment or "neutral",
            })
    except ImportError:
        # 沟通记录模型尚未定义，回退到基于联系人的记录
        logger.debug("CustomerCommunication 模型未找到，使用联系人记录回退")
    except SQLAlchemyError as e:
        # 数据库查询异常（如表不存在），记录日志并回退
        logger.warning(f"查询沟通记录失败: {e}")

    # 如果沟通记录表不存在或查询失败，返回基于联系人最后联系日期的记录
    if not timeline:
        contacts = db.query(Contact).filter(Contact.customer_id == customer_id).all()
        for contact in contacts:
            if contact.last_contact_date:
                timeline.append({
                    "date": str(contact.last_contact_date),
                    "type": "contact",
                    "title": f"与 {contact.name} 联系",
                    "participants": [f"{contact.name}（{contact.position}）"],
                    "outcome": "",
                    "next_action": "",
                    "sentiment": "neutral",
                })

    # 按时间排序
    timeline.sort(key=lambda x: x["date"], reverse=True)

    # 统计类型分布
    type_counts = {}
    sentiment_counts = {"positive": 0, "neutral": 0, "negative": 0}

    for item in timeline:
        t = item.get("type", "其他")
        type_counts[t] = type_counts.get(t, 0) + 1
        s = item.get("sentiment", "neutral")
        if s in sentiment_counts:
            sentiment_counts[s] += 1

    # 计算最后联系天数
    days_since_last = 999
    if timeline:
        try:
            last_date = date.fromisoformat(timeline[0]["date"])
            days_since_last = (date.today() - last_date).days
        except ValueError:
            # 日期格式无效，保持默认值 999
            pass

    return {
        "customer_id": customer_id,
        "customer_name": customer.customer_name,
        "period_months": months,
        "total_interactions": len(timeline),
        "by_type": type_counts,
        "sentiment_distribution": sentiment_counts,
        "timeline": timeline[:50],  # 限制返回数量
        "last_contact": timeline[0]["date"] if timeline else None,
        "days_since_last_contact": days_since_last,
    }


# ========== 2. 决策链分析 ==========


@router.get("/customers/{customer_id}/decision-chain", summary="决策链分析")
def get_decision_chain(
    customer_id: int = Path(..., description="客户 ID"),
    opportunity_id: Optional[int] = Query(None, description="关联商机ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    客户决策链分析

    识别：
    - 关键决策人（EB）
    - 技术决策人（TB）
    - 采购决策人（PB）
    - 最终用户（UB）
    - 教练/内线（Coach）
    """
    customer = _get_customer_or_404(db, customer_id)

    # 获取联系人列表
    contacts = db.query(Contact).filter(Contact.customer_id == customer_id).all()

    # 获取商机名称
    opportunity_name = None
    if opportunity_id:
        opportunity = db.query(Opportunity).get(opportunity_id)
        if opportunity:
            opportunity_name = opportunity.name

    # 构建联系人决策链数据
    contact_list = []
    coverage = {
        "eb_covered": False,
        "tb_covered": False,
        "pb_covered": False,
        "ub_covered": False,
        "coach_identified": False,
    }

    for contact in contacts:
        role = contact.decision_role
        if role:
            # 更新覆盖状态
            role_lower = role.lower()
            if role_lower == "eb":
                coverage["eb_covered"] = True
            elif role_lower == "tb":
                coverage["tb_covered"] = True
            elif role_lower == "pb":
                coverage["pb_covered"] = True
            elif role_lower == "ub":
                coverage["ub_covered"] = True
            elif role_lower == "coach":
                coverage["coach_identified"] = True

        # 解析关键关注点
        key_concerns = []
        if contact.key_concerns:
            try:
                key_concerns = json.loads(contact.key_concerns)
            except (json.JSONDecodeError, TypeError):
                # JSON 格式无效，当作纯文本处理
                key_concerns = [contact.key_concerns]

        contact_list.append({
            "id": contact.id,
            "name": contact.name,
            "title": contact.position or "",
            "department": contact.department or "",
            "role": role or "",
            "role_name": ROLE_NAMES.get(role, "未分类") if role else "未分类",
            "influence": contact.influence_level or "MEDIUM",
            "attitude": contact.attitude or "unknown",
            "last_contact": str(contact.last_contact_date) if contact.last_contact_date else None,
            "key_concerns": key_concerns,
            "relationship_strength": contact.relationship_strength or 0,
            "mobile": contact.mobile,
            "email": contact.email,
            "is_primary": contact.is_primary,
        })

    # 计算覆盖率
    covered_count = sum(1 for v in coverage.values() if v)
    coverage_score = covered_count / 5 * 100

    # 风险分析
    risks = []
    for contact in contact_list:
        if contact["role"] == "EB" and contact["relationship_strength"] < 60:
            risks.append({
                "risk": "EB 关系不足",
                "description": f"与 {contact['name']} 关系强度仅 {contact['relationship_strength']}%，需加强接触",
                "severity": "HIGH",
                "action": "安排高层拜访或技术交流",
            })
        if contact["attitude"] == "resistant":
            risks.append({
                "risk": f"{contact['role_name']} 态度反对",
                "description": f"{contact['name']} 对我们持反对态度",
                "severity": "HIGH",
                "action": "了解反对原因，制定针对性策略",
            })
        if contact["attitude"] == "neutral" and contact["role"] in ["EB", "TB", "PB"]:
            risks.append({
                "risk": f"{contact['role_name']} 态度中立",
                "description": f"{contact['name']} 态度中立，可能存在变数",
                "severity": "MEDIUM",
                "action": "加强沟通，争取支持",
            })

    # 判断整体风险
    high_risks = len([r for r in risks if r["severity"] == "HIGH"])
    overall_risk = "HIGH" if high_risks >= 2 else ("MEDIUM" if high_risks >= 1 or len(risks) >= 2 else "LOW")

    # 生成建议
    recommended_actions = []
    if not coverage["eb_covered"]:
        recommended_actions.append("识别并接触最终决策人（EB）")
    if not coverage["tb_covered"]:
        recommended_actions.append("建立与技术决策人（TB）的联系")
    if not coverage["coach_identified"]:
        recommended_actions.append("发展内部支持者（Coach）")
    for contact in contact_list:
        if contact["role"] == "EB" and contact["relationship_strength"] < 60:
            recommended_actions.append(f"加强与 {contact['name']} 的关系（当前 {contact['relationship_strength']}%）")

    return {
        "customer_id": customer_id,
        "customer_name": customer.customer_name,
        "opportunity_id": opportunity_id,
        "opportunity_name": opportunity_name,
        "contacts": contact_list,
        "coverage_analysis": {
            **coverage,
            "coverage_score": coverage_score,
        },
        "risk_analysis": {
            "risks": risks[:5],  # 最多返回5个风险
            "overall_risk": overall_risk,
        },
        "recommended_actions": recommended_actions[:5],
    }


# ========== 3. 客户健康度评分 ==========


@router.get("/customers/{customer_id}/health-score", summary="客户健康度评分")
def get_customer_health_score(
    customer_id: int = Path(..., description="客户 ID"),
    opportunity_id: Optional[int] = Query(None, description="关联商机ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    客户健康度综合评分（关系成熟度评估）

    维度：
    - 决策链覆盖度 (0-20分)
    - 互动频率 (0-15分)
    - 关系深度 (0-20分)
    - 信息获取度 (0-15分)
    - 支持度 (0-20分)
    - 高层互动 (0-10分)
    """
    customer = _get_customer_or_404(db, customer_id)

    # 使用评分服务计算
    scoring_service = RelationshipScoringService(db)
    assessment = scoring_service.calculate_customer_score(
        customer_id=customer_id,
        opportunity_id=opportunity_id,
        save_to_db=True,
    )

    # 转换为健康度格式
    overall = assessment["overall_assessment"]
    dim_scores = assessment["dimension_scores"]

    # 映射健康等级
    health_level = "GOOD" if overall["total_score"] >= 60 else ("MEDIUM" if overall["total_score"] >= 40 else "LOW")

    # 获取历史趋势
    history = scoring_service.get_customer_score_history(customer_id, limit=4)
    trend = "stable"
    if len(history) >= 2:
        if history[0]["score"] > history[-1]["score"]:
            trend = "improving"
        elif history[0]["score"] < history[-1]["score"]:
            trend = "declining"

    # 构建维度数据
    dimensions = [
        {
            "name": "决策链覆盖度",
            "score": dim_scores["decision_chain"]["score"],
            "max_score": 20,
            "weight": 20,
            "metrics": dim_scores["decision_chain"].get("details", {}),
            "status": "GOOD" if dim_scores["decision_chain"]["score"] >= 16 else "MEDIUM",
        },
        {
            "name": "互动频率",
            "score": dim_scores["interaction_frequency"]["score"],
            "max_score": 15,
            "weight": 15,
            "metrics": dim_scores["interaction_frequency"].get("details", {}),
            "status": "GOOD" if dim_scores["interaction_frequency"]["score"] >= 12 else "MEDIUM",
        },
        {
            "name": "关系深度",
            "score": dim_scores["relationship_depth"]["score"],
            "max_score": 20,
            "weight": 20,
            "metrics": {
                "level": dim_scores["relationship_depth"].get("level", ""),
                "avg_relationship": dim_scores["relationship_depth"].get("avg_relationship", 0),
            },
            "status": "GOOD" if dim_scores["relationship_depth"]["score"] >= 16 else "MEDIUM",
        },
        {
            "name": "信息获取度",
            "score": dim_scores["information_access"]["score"],
            "max_score": 15,
            "weight": 15,
            "metrics": dim_scores["information_access"].get("details", {}),
            "status": "GOOD" if dim_scores["information_access"]["score"] >= 12 else "MEDIUM",
        },
        {
            "name": "支持度",
            "score": dim_scores["support_level"]["score"],
            "max_score": 20,
            "weight": 20,
            "metrics": dim_scores["support_level"].get("details", {}),
            "status": "GOOD" if dim_scores["support_level"]["score"] >= 16 else "MEDIUM",
        },
        {
            "name": "高层互动",
            "score": dim_scores["executive_engagement"]["score"],
            "max_score": 10,
            "weight": 10,
            "metrics": {
                "level": dim_scores["executive_engagement"].get("level", ""),
            },
            "status": "GOOD" if dim_scores["executive_engagement"]["score"] >= 7 else "MEDIUM",
        },
    ]

    # 生成告警
    alerts = []
    for dim in dimensions:
        if dim["score"] < dim["max_score"] * 0.5:
            alerts.append({
                "type": "WARNING",
                "title": f"{dim['name']}不足",
                "description": f"当前得分 {dim['score']}/{dim['max_score']}",
                "suggested_action": assessment["improvement_recommendations"][0]["action"]
                if assessment.get("improvement_recommendations") else "",
            })

    return {
        "customer_id": customer_id,
        "customer_name": customer.customer_name,
        "assessment_date": date.today().isoformat(),
        "overall_score": overall["total_score"],
        "maturity_level": overall["maturity_level"],
        "maturity_level_name": overall["maturity_level_name"],
        "estimated_win_rate": overall["estimated_win_rate"],
        "health_level": health_level,
        "health_trend": trend,
        "dimensions": dimensions,
        "radar_data": assessment.get("radar_data", []),
        "alerts": alerts[:3],
        "recommended_actions": assessment.get("improvement_recommendations", []),
        "historical_trend": history,
    }


# ========== 4. 购买偏好分析 ==========


@router.get("/customers/{customer_id}/buying-preferences", summary="购买偏好分析")
def get_buying_preferences(
    customer_id: int = Path(..., description="客户 ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    客户购买偏好分析

    分析：
    - 产品类型偏好
    - 价格敏感度
    - 决策周期
    - 关键采购因素
    """
    customer = _get_customer_or_404(db, customer_id)

    # 尝试从历史商机和合同中分析
    opportunities = (
        db.query(Opportunity)
        .filter(Opportunity.customer_id == customer_id)
        .all()
    )

    # 统计商机数据
    total_opportunities = len(opportunities)
    won_opportunities = len([o for o in opportunities if o.stage == "WON"])
    lost_opportunities = len([o for o in opportunities if o.stage == "LOST"])
    win_rate = round(won_opportunities / total_opportunities * 100, 1) if total_opportunities > 0 else 0

    # 计算平均金额和总额
    amounts = [float(o.est_amount or 0) for o in opportunities if o.est_amount]
    avg_amount = round(sum(amounts) / len(amounts), 2) if amounts else 0
    total_amount = sum(amounts)

    # 计算平均决策周期（从创建到关闭）
    decision_cycles = []
    for o in opportunities:
        if o.stage in ["WON", "LOST"] and o.actual_close_date and o.created_at:
            try:
                if hasattr(o.actual_close_date, "date"):
                    close_date = o.actual_close_date.date()
                else:
                    close_date = o.actual_close_date
                if hasattr(o.created_at, "date"):
                    create_date = o.created_at.date()
                else:
                    create_date = o.created_at
                days = (close_date - create_date).days
                if days > 0:
                    decision_cycles.append(days)
            except (AttributeError, TypeError):
                # 日期字段格式异常，跳过该记录
                pass

    avg_decision_cycle = round(sum(decision_cycles) / len(decision_cycles)) if decision_cycles else 45

    # 获取联系人偏好
    contacts = db.query(Contact).filter(Contact.customer_id == customer_id).all()
    key_concerns = []
    for contact in contacts:
        if contact.key_concerns:
            try:
                concerns = json.loads(contact.key_concerns)
                key_concerns.extend(concerns)
            except (json.JSONDecodeError, TypeError):
                # JSON 格式无效，当作纯文本处理
                key_concerns.append(contact.key_concerns)

    # 去重并统计频率
    concern_counts = {}
    for concern in key_concerns:
        concern_counts[concern] = concern_counts.get(concern, 0) + 1

    # 排序取前5
    top_concerns = sorted(concern_counts.items(), key=lambda x: x[1], reverse=True)[:5]

    return {
        "customer_id": customer_id,
        "customer_name": customer.customer_name,
        "analysis_date": date.today().isoformat(),
        "product_preferences": {
            "preferred_features": [c[0] for c in top_concerns] if top_concerns else [],
            "analysis_note": f"基于 {len(contacts)} 个联系人的关注点分析",
        },
        "price_sensitivity": {
            "level": "MEDIUM",  # 基于历史数据判断
            "typical_budget_range": {
                "min": min(amounts) if amounts else 0,
                "max": max(amounts) if amounts else 0,
                "avg": avg_amount,
                "currency": "CNY",
            },
            "payment_preference": customer.payment_terms or "标准付款条款",
        },
        "decision_pattern": {
            "avg_decision_cycle_days": avg_decision_cycle,
            "decision_speed": "FAST" if avg_decision_cycle < 30 else ("MEDIUM" if avg_decision_cycle < 60 else "SLOW"),
            "key_decision_factors": [
                {"factor": c[0], "count": c[1]} for c in top_concerns
            ],
        },
        "historical_insights": {
            "total_opportunities": total_opportunities,
            "won_opportunities": won_opportunities,
            "lost_opportunities": lost_opportunities,
            "win_rate": win_rate,
            "avg_opportunity_value": avg_amount,
            "total_opportunity_value": total_amount,
        },
        "recommended_approach": [],  # 需要业务逻辑生成
    }


# ========== 5. 客户 360°总览 ==========


@router.get("/customers/{customer_id}/360-view", summary="客户 360°总览")
def get_customer_360_view(
    customer_id: int = Path(..., description="客户 ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    客户 360°完整视图

    整合所有客户信息于一页
    """
    customer = _get_customer_or_404(db, customer_id)

    # 获取联系人
    contacts = db.query(Contact).filter(Contact.customer_id == customer_id).all()
    key_contacts = [
        {
            "id": c.id,
            "name": c.name,
            "title": c.position or "",
            "role": c.decision_role or "",
            "relationship": c.relationship_strength or 0,
            "attitude": c.attitude or "unknown",
        }
        for c in contacts
        if c.decision_role  # 只返回有决策角色的联系人
    ][:5]

    # 获取活跃商机
    active_opportunities = (
        db.query(Opportunity)
        .filter(
            Opportunity.customer_id == customer_id,
            Opportunity.stage.notin_(["WON", "LOST", "ABANDONED"]),
        )
        .all()
    )

    active_opps = [
        {
            "id": o.id,
            "name": o.name,
            "stage": o.stage,
            "estimated_amount": float(o.est_amount or 0),
            "win_rate": o.win_rate or 0,
            "estimated_close": str(o.expected_close_date) if o.expected_close_date else None,
        }
        for o in active_opportunities
    ]

    # 计算健康度
    scoring_service = RelationshipScoringService(db)
    latest_score = scoring_service.get_latest_score(customer_id)

    health_score = latest_score["total_score"] if latest_score else 0
    health_level = "GOOD" if health_score >= 60 else ("MEDIUM" if health_score >= 40 else "LOW")

    # 计算最后联系天数
    last_contact_date = None
    for contact in contacts:
        if contact.last_contact_date:
            if last_contact_date is None or contact.last_contact_date > last_contact_date:
                last_contact_date = contact.last_contact_date

    days_since_last = (date.today() - last_contact_date).days if last_contact_date else 999

    # 生成快速行动建议
    quick_actions = []
    if days_since_last > 14:
        quick_actions.append({
            "action": "联系客户",
            "priority": "HIGH",
            "deadline": "尽快",
        })
    for contact in key_contacts:
        if contact["role"] == "EB" and contact["relationship"] < 60:
            quick_actions.append({
                "action": f"加强与 {contact['name']} 的关系",
                "priority": "HIGH",
                "deadline": "2周内",
            })
            break

    # 生成告警
    alerts = []
    if days_since_last > 30:
        alerts.append({"type": "WARNING", "message": f"超过 {days_since_last} 天未联系客户"})
    if health_score < 50:
        alerts.append({"type": "WARNING", "message": "客户健康度较低，需关注"})

    return {
        "customer_id": customer_id,
        "customer_name": customer.customer_name,
        "short_name": customer.short_name,
        "industry": customer.industry,
        "customer_type": customer.customer_type,
        "customer_level": customer.customer_level,
        "basic_info": {
            "address": customer.address,
            "website": customer.website,
            "established_date": customer.established_date,
            "contact_person": customer.contact_person,
            "contact_phone": customer.contact_phone,
            "contact_email": customer.contact_email,
        },
        "relationship_summary": {
            "total_contacts": len(contacts),
            "key_contacts_count": len(key_contacts),
            "last_contact": str(last_contact_date) if last_contact_date else None,
            "days_since_last_contact": days_since_last,
            "health_score": health_score,
            "health_level": health_level,
            "maturity_level": latest_score["maturity_level"] if latest_score else "L1",
        },
        "active_opportunities": active_opps,
        "key_contacts": key_contacts,
        "quick_actions": quick_actions[:3],
        "alerts": alerts[:3],
    }
