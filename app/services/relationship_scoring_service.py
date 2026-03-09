# -*- coding: utf-8 -*-
"""
客户关系成熟度评分服务

提供六维度评分算法：
1. 决策链覆盖度 (0-20分)
2. 互动频率 (0-15分)
3. 关系深度 (0-20分)
4. 信息获取度 (0-15分)
5. 支持度 (0-20分)
6. 高层互动 (0-10分)
"""

import json
from datetime import date, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.models.sales import Contact, CustomerRelationshipScore, Opportunity


# 成熟度等级映射
MATURITY_LEVELS = {
    "L1": {"range": (0, 30), "name": "初始级", "win_rate": (10, 25)},
    "L2": {"range": (31, 50), "name": "发展级", "win_rate": (25, 45)},
    "L3": {"range": (51, 70), "name": "成熟级", "win_rate": (45, 65)},
    "L4": {"range": (71, 85), "name": "战略级", "win_rate": (65, 85)},
    "L5": {"range": (86, 100), "name": "伙伴级", "win_rate": (85, 95)},
}

# 决策角色权重
DECISION_ROLE_WEIGHTS = {
    "EB": {"max_score": 5, "min_relationship": 60},  # 经济决策人
    "TB": {"max_score": 5, "min_relationship": 60},  # 技术决策人
    "PB": {"max_score": 4, "min_relationship": 60},  # 采购决策人
    "UB": {"max_score": 3, "min_relationship": 60},  # 最终用户
    "COACH": {"max_score": 3, "min_relationship": 0},  # 内线/教练
}

# 态度分数
ATTITUDE_SCORES = {
    "supportive": {"EB": 8, "TB": 6, "PB": 4, "UB": 2},
    "neutral": -5,  # 惩罚分
    "resistant": -10,  # 惩罚分
}


class RelationshipScoringService:
    """客户关系成熟度评分服务"""

    def __init__(self, db: Session):
        self.db = db

    def calculate_decision_chain_score(self, contacts: list[Contact]) -> dict:
        """
        计算决策链覆盖度 (0-20分)

        规则：
        - EB 覆盖且关系>=60: +5分
        - TB 覆盖且关系>=60: +5分
        - PB 覆盖且关系>=60: +4分
        - UB 覆盖且关系>=60: +3分
        - Coach 覆盖: +3分
        """
        score = 0
        details = {}
        covered_roles = set()

        for contact in contacts:
            role = contact.decision_role
            if not role or role not in DECISION_ROLE_WEIGHTS:
                continue

            # 避免重复计算同一角色
            if role in covered_roles:
                # 保留关系强度更高的
                if contact.relationship_strength > details.get(role, {}).get("relationship", 0):
                    details[role]["relationship"] = contact.relationship_strength
                    details[role]["name"] = f"{contact.name} - {contact.position}"
                continue

            weight = DECISION_ROLE_WEIGHTS[role]
            relationship = contact.relationship_strength or 0
            attitude = contact.attitude or "unknown"

            # 计算该角色的得分
            role_score = 0
            if role == "COACH":
                # Coach 不需要关系强度门槛
                role_score = weight["max_score"]
            elif relationship >= weight["min_relationship"]:
                role_score = weight["max_score"]
            else:
                # 关系强度不足，按比例得分
                role_score = int(weight["max_score"] * relationship / 100)

            score += role_score
            covered_roles.add(role)

            details[role] = {
                "covered": True,
                "name": f"{contact.name} - {contact.position}",
                "relationship": relationship,
                "attitude": attitude,
                "score": role_score,
            }

        # 确保不超过20分
        score = min(score, 20)

        return {
            "score": score,
            "max_score": 20,
            "details": details,
            "coverage_rate": len(covered_roles) / 5 * 100,  # 5个角色
        }

    def calculate_interaction_frequency_score(
        self, customer_id: int, days: int = 30
    ) -> dict:
        """
        计算互动频率 (0-15分)

        规则：
        - 每天联系: 15分
        - 每周2+次: 12分
        - 每周1次: 8分
        - 每2周1次: 5分
        - 每月1次: 2分
        - 不规律: 0分
        """
        # 查询沟通记录
        # 注意：这里假设有 CustomerCommunication 表，实际需要对接真实表
        try:
            from app.models.sales.communication import CustomerCommunication

            start_date = date.today() - timedelta(days=days)
            communications = (
                self.db.query(CustomerCommunication)
                .filter(
                    CustomerCommunication.customer_id == customer_id,
                    CustomerCommunication.communication_date >= start_date,
                )
                .all()
            )
            total_count = len(communications)
        except Exception:
            # 如果表不存在，返回默认值
            total_count = 0
            communications = []

        # 计算每周联系次数
        weeks = max(days / 7, 1)
        avg_per_week = total_count / weeks

        # 根据频率计算分数
        if avg_per_week >= 7:  # 每天
            score = 15
            level = "每天联系"
        elif avg_per_week >= 2:  # 每周2+次
            score = 12
            level = "每周2次以上"
        elif avg_per_week >= 1:  # 每周1次
            score = 8
            level = "每周1次"
        elif avg_per_week >= 0.5:  # 每2周1次
            score = 5
            level = "每2周1次"
        elif avg_per_week >= 0.25:  # 每月1次
            score = 2
            level = "每月1次"
        else:
            score = 0
            level = "不规律"

        # 统计沟通方式分布
        method_counts = {}
        for comm in communications:
            method = getattr(comm, "communication_type", "其他")
            method_counts[method] = method_counts.get(method, 0) + 1

        return {
            "score": score,
            "max_score": 15,
            "level": level,
            "details": {
                "total_count": total_count,
                "period_days": days,
                "avg_per_week": round(avg_per_week, 1),
                "by_method": method_counts,
            },
        }

    def calculate_relationship_depth_score(self, contacts: list[Contact]) -> dict:
        """
        计算关系深度 (0-20分)

        基于联系人平均关系强度：
        - 平均>=80 (伙伴级): 20分
        - 平均>=60 (信任级): 16分
        - 平均>=40 (认可级): 12分
        - 平均>=20 (接触级): 8分
        - 平均<20 (陌生级): 4分
        """
        if not contacts:
            return {
                "score": 0,
                "max_score": 20,
                "level": "无联系人",
                "avg_relationship": 0,
            }

        # 计算有决策角色的联系人的平均关系强度
        key_contacts = [c for c in contacts if c.decision_role]
        if not key_contacts:
            key_contacts = contacts

        total_strength = sum(c.relationship_strength or 0 for c in key_contacts)
        avg_relationship = total_strength / len(key_contacts)

        # 映射到分数
        if avg_relationship >= 80:
            score = 20
            level = "伙伴级"
        elif avg_relationship >= 60:
            score = 16
            level = "信任级"
        elif avg_relationship >= 40:
            score = 12
            level = "认可级"
        elif avg_relationship >= 20:
            score = 8
            level = "接触级"
        else:
            score = 4
            level = "陌生级"

        return {
            "score": score,
            "max_score": 20,
            "level": level,
            "avg_relationship": round(avg_relationship, 1),
            "key_contacts_count": len(key_contacts),
        }

    def calculate_information_access_score(
        self, opportunity: Optional[Opportunity]
    ) -> dict:
        """
        计算信息获取度 (0-15分)

        基于商机信息完整度：
        - 预算明确 (est_amount有值): +4分
        - 决策流程清楚 (有notes): +4分
        - 时间表明确 (expected_close_date): +3分
        - 竞品信息 (competitor字段): +2分
        - 痛点需求 (requirement字段): +2分
        """
        if not opportunity:
            return {
                "score": 0,
                "max_score": 15,
                "details": {},
                "completeness": 0,
            }

        score = 0
        details = {}

        # 预算明确
        if opportunity.est_amount and opportunity.est_amount > 0:
            score += 4
            details["budget"] = {
                "known": True,
                "value": float(opportunity.est_amount),
                "score": 4,
            }
        else:
            details["budget"] = {"known": False, "score": 0}

        # 决策流程（通过notes判断）
        if opportunity.notes and len(opportunity.notes) > 20:
            score += 4
            details["decision_process"] = {"known": True, "score": 4}
        else:
            details["decision_process"] = {"known": False, "score": 0}

        # 时间表
        if opportunity.expected_close_date:
            score += 3
            details["timeline"] = {
                "known": True,
                "deadline": str(opportunity.expected_close_date),
                "score": 3,
            }
        else:
            details["timeline"] = {"known": False, "score": 0}

        # 竞品信息（假设有competitor字段，如果没有则跳过）
        competitor = getattr(opportunity, "competitor", None)
        if competitor:
            score += 2
            details["competitors"] = {"known": True, "score": 2}
        else:
            details["competitors"] = {"known": False, "score": 0}

        # 痛点需求（通过requirements关系判断）
        has_requirements = (
            hasattr(opportunity, "requirements") and len(opportunity.requirements) > 0
        )
        if has_requirements:
            score += 2
            details["pain_points"] = {"known": True, "score": 2}
        else:
            details["pain_points"] = {"known": False, "score": 0}

        return {
            "score": min(score, 15),
            "max_score": 15,
            "details": details,
            "completeness": round(score / 15 * 100, 1),
        }

    def calculate_support_level_score(self, contacts: list[Contact]) -> dict:
        """
        计算支持度 (0-20分)

        基于联系人态度：
        - EB supportive: +8分
        - TB supportive: +6分
        - PB supportive: +4分
        - UB supportive: +2分
        - 有neutral: -5分
        - 有resistant: -10分
        """
        score = 0
        details = {}
        has_neutral = False
        has_resistant = False

        for contact in contacts:
            role = contact.decision_role
            attitude = contact.attitude or "unknown"

            if not role or role not in DECISION_ROLE_WEIGHTS:
                continue

            # 记录详情
            if role not in details:
                details[role] = {"attitude": attitude, "score": 0}

            # 支持态度加分
            if attitude == "supportive":
                role_score = ATTITUDE_SCORES["supportive"].get(role, 0)
                score += role_score
                details[role]["score"] = role_score
            elif attitude == "neutral":
                has_neutral = True
                details[role]["score"] = 0
            elif attitude == "resistant":
                has_resistant = True
                details[role]["score"] = 0

        # 应用惩罚
        if has_resistant:
            score += ATTITUDE_SCORES["resistant"]
        elif has_neutral:
            score += ATTITUDE_SCORES["neutral"]

        # 确保分数在合理范围
        score = max(0, min(score, 20))

        # 识别风险
        risks = []
        if has_resistant:
            risks.append("存在关键人反对我们")
        if has_neutral:
            risks.append("关键人态度中立，需争取支持")

        return {
            "score": score,
            "max_score": 20,
            "details": details,
            "risks": risks,
            "has_champion": any(
                d.get("attitude") == "supportive" for d in details.values()
            ),
        }

    def calculate_executive_engagement_score(self, customer_id: int) -> dict:
        """
        计算高层互动 (0-10分)

        基于沟通记录的参与层级：
        - 有CEO级别沟通记录: 10分
        - 有VP级别沟通: 7分
        - 有总监级别沟通: 4分
        - 仅工作层面: 2分
        """
        # 查询联系人的最高职级
        contacts = (
            self.db.query(Contact)
            .filter(Contact.customer_id == customer_id)
            .all()
        )

        # 根据职位判断层级
        has_ceo = False
        has_vp = False
        has_director = False

        ceo_keywords = ["总经理", "总裁", "CEO", "董事长", "Owner"]
        vp_keywords = ["副总", "VP", "副总裁", "副总经理"]
        director_keywords = ["总监", "经理", "Director", "Manager"]

        for contact in contacts:
            position = (contact.position or "").upper()
            # 检查是否有高层互动记录（通过last_contact_date判断）
            if contact.last_contact_date:
                for kw in ceo_keywords:
                    if kw.upper() in position:
                        has_ceo = True
                        break
                for kw in vp_keywords:
                    if kw.upper() in position:
                        has_vp = True
                        break
                for kw in director_keywords:
                    if kw.upper() in position:
                        has_director = True
                        break

        # 计算分数
        if has_ceo:
            score = 10
            level = "CEO级交流"
        elif has_vp:
            score = 7
            level = "VP级交流"
        elif has_director:
            score = 4
            level = "总监级交流"
        else:
            score = 2
            level = "工作层交流"

        return {
            "score": score,
            "max_score": 10,
            "level": level,
            "has_ceo_contact": has_ceo,
            "has_vp_contact": has_vp,
            "has_director_contact": has_director,
        }

    def get_maturity_level(self, total_score: int) -> dict:
        """根据总分获取成熟度等级"""
        for level, config in MATURITY_LEVELS.items():
            min_score, max_score = config["range"]
            if min_score <= total_score <= max_score:
                min_rate, max_rate = config["win_rate"]
                # 在范围内线性插值计算赢单率
                range_size = max_score - min_score
                if range_size > 0:
                    position = (total_score - min_score) / range_size
                    estimated_win_rate = int(min_rate + (max_rate - min_rate) * position)
                else:
                    estimated_win_rate = min_rate

                return {
                    "level": level,
                    "name": config["name"],
                    "estimated_win_rate": estimated_win_rate,
                }

        # 默认返回L1
        return {"level": "L1", "name": "初始级", "estimated_win_rate": 15}

    def calculate_customer_score(
        self,
        customer_id: int,
        opportunity_id: Optional[int] = None,
        save_to_db: bool = True,
    ) -> dict:
        """
        计算客户的完整关系成熟度评分

        参数：
            customer_id: 客户ID
            opportunity_id: 关联商机ID（可选）
            save_to_db: 是否保存到数据库

        返回：
            包含所有维度评分和总体评估的字典
        """
        # 获取客户联系人
        contacts = (
            self.db.query(Contact)
            .filter(Contact.customer_id == customer_id)
            .all()
        )

        # 获取商机（如果指定）
        opportunity = None
        if opportunity_id:
            opportunity = self.db.query(Opportunity).get(opportunity_id)

        # 计算六维度得分
        decision_chain = self.calculate_decision_chain_score(contacts)
        interaction_freq = self.calculate_interaction_frequency_score(customer_id)
        relationship_depth = self.calculate_relationship_depth_score(contacts)
        information_access = self.calculate_information_access_score(opportunity)
        support_level = self.calculate_support_level_score(contacts)
        executive_engagement = self.calculate_executive_engagement_score(customer_id)

        # 计算总分
        total_score = (
            decision_chain["score"]
            + interaction_freq["score"]
            + relationship_depth["score"]
            + information_access["score"]
            + support_level["score"]
            + executive_engagement["score"]
        )

        # 获取成熟度等级
        maturity = self.get_maturity_level(total_score)

        # 构建结果
        result = {
            "customer_id": customer_id,
            "opportunity_id": opportunity_id,
            "assessment_date": date.today().isoformat(),
            "dimension_scores": {
                "decision_chain": decision_chain,
                "interaction_frequency": interaction_freq,
                "relationship_depth": relationship_depth,
                "information_access": information_access,
                "support_level": support_level,
                "executive_engagement": executive_engagement,
            },
            "overall_assessment": {
                "total_score": total_score,
                "max_score": 100,
                "maturity_level": maturity["level"],
                "maturity_level_name": maturity["name"],
                "estimated_win_rate": maturity["estimated_win_rate"],
            },
            "radar_data": [
                {
                    "dimension": "决策链",
                    "score": decision_chain["score"],
                    "max": 20,
                    "percentage": round(decision_chain["score"] / 20 * 100),
                },
                {
                    "dimension": "互动频率",
                    "score": interaction_freq["score"],
                    "max": 15,
                    "percentage": round(interaction_freq["score"] / 15 * 100),
                },
                {
                    "dimension": "关系深度",
                    "score": relationship_depth["score"],
                    "max": 20,
                    "percentage": round(relationship_depth["score"] / 20 * 100),
                },
                {
                    "dimension": "信息获取",
                    "score": information_access["score"],
                    "max": 15,
                    "percentage": round(information_access["score"] / 15 * 100),
                },
                {
                    "dimension": "支持度",
                    "score": support_level["score"],
                    "max": 20,
                    "percentage": round(support_level["score"] / 20 * 100),
                },
                {
                    "dimension": "高层互动",
                    "score": executive_engagement["score"],
                    "max": 10,
                    "percentage": round(executive_engagement["score"] / 10 * 100),
                },
            ],
        }

        # 生成改进建议
        result["improvement_recommendations"] = self._generate_recommendations(result)

        # 保存到数据库
        if save_to_db:
            self._save_score_to_db(result)

        return result

    def _generate_recommendations(self, assessment: dict) -> list:
        """根据评估结果生成改进建议"""
        recommendations = []
        dimension_scores = assessment["dimension_scores"]

        # 按得分率排序，找出需要改进的维度
        dimensions = [
            ("决策链覆盖度", "decision_chain", 20),
            ("互动频率", "interaction_frequency", 15),
            ("关系深度", "relationship_depth", 20),
            ("信息获取度", "information_access", 15),
            ("支持度", "support_level", 20),
            ("高层互动", "executive_engagement", 10),
        ]

        improvement_actions = {
            "decision_chain": {
                "action": "完善决策链覆盖",
                "specific_actions": [
                    "识别缺失的决策角色（EB/TB/PB/UB/Coach）",
                    "建立与关键决策人的联系",
                    "提升与已覆盖角色的关系强度",
                ],
            },
            "interaction_frequency": {
                "action": "增加互动频率",
                "specific_actions": [
                    "制定定期沟通计划",
                    "增加拜访和会议频率",
                    "保持微信/电话日常联系",
                ],
            },
            "relationship_depth": {
                "action": "深化客户关系",
                "specific_actions": [
                    "从认可级提升至信任级",
                    "邀请客户参观公司或已交付项目",
                    "提供定制化服务和支持",
                ],
            },
            "information_access": {
                "action": "获取更多客户信息",
                "specific_actions": [
                    "明确客户预算范围",
                    "了解决策流程和时间表",
                    "收集竞品信息和客户痛点",
                ],
            },
            "support_level": {
                "action": "争取关键人支持",
                "specific_actions": [
                    "转化中立者为支持者",
                    "化解反对者的顾虑",
                    "发展内部支持者(Coach)",
                ],
            },
            "executive_engagement": {
                "action": "提升高层互动",
                "specific_actions": [
                    "安排双方高层会面",
                    "组织战略合作交流",
                    "签署合作备忘录",
                ],
            },
        }

        priority = 1
        for name, key, max_score in dimensions:
            dim = dimension_scores[key]
            score = dim["score"]
            percentage = score / max_score * 100

            # 低于80%的维度需要改进
            if percentage < 80:
                gap = max_score - score
                action_config = improvement_actions.get(key, {})

                recommendations.append({
                    "priority": priority,
                    "dimension": name,
                    "current_score": score,
                    "target_score": max_score,
                    "gap": gap,
                    "action": action_config.get("action", "提升该维度"),
                    "specific_actions": action_config.get("specific_actions", []),
                    "expected_impact": f"+{gap}分，提升赢单概率",
                })
                priority += 1

        # 只返回前3个最重要的建议
        return recommendations[:3]

    def _save_score_to_db(self, assessment: dict) -> None:
        """保存评分到数据库"""
        try:
            score_record = CustomerRelationshipScore(
                customer_id=assessment["customer_id"],
                opportunity_id=assessment.get("opportunity_id"),
                score_date=date.today(),
                decision_chain_score=assessment["dimension_scores"]["decision_chain"]["score"],
                interaction_frequency_score=assessment["dimension_scores"]["interaction_frequency"]["score"],
                relationship_depth_score=assessment["dimension_scores"]["relationship_depth"]["score"],
                information_access_score=assessment["dimension_scores"]["information_access"]["score"],
                support_level_score=assessment["dimension_scores"]["support_level"]["score"],
                executive_engagement_score=assessment["dimension_scores"]["executive_engagement"]["score"],
                total_score=assessment["overall_assessment"]["total_score"],
                maturity_level=assessment["overall_assessment"]["maturity_level"],
                estimated_win_rate=assessment["overall_assessment"]["estimated_win_rate"],
                score_details=json.dumps(assessment, ensure_ascii=False),
                is_auto_calculated=True,
            )

            self.db.add(score_record)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            # 记录错误但不中断流程
            print(f"Failed to save relationship score: {e}")

    def get_customer_score_history(
        self, customer_id: int, limit: int = 10
    ) -> list[dict]:
        """获取客户评分历史"""
        records = (
            self.db.query(CustomerRelationshipScore)
            .filter(CustomerRelationshipScore.customer_id == customer_id)
            .order_by(CustomerRelationshipScore.score_date.desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "date": str(r.score_date),
                "score": r.total_score,
                "level": r.maturity_level,
                "estimated_win_rate": r.estimated_win_rate,
            }
            for r in records
        ]

    def get_latest_score(self, customer_id: int) -> Optional[dict]:
        """获取客户最新评分"""
        record = (
            self.db.query(CustomerRelationshipScore)
            .filter(CustomerRelationshipScore.customer_id == customer_id)
            .order_by(CustomerRelationshipScore.score_date.desc())
            .first()
        )

        if not record:
            return None

        return {
            "date": str(record.score_date),
            "total_score": record.total_score,
            "maturity_level": record.maturity_level,
            "estimated_win_rate": record.estimated_win_rate,
            "dimension_scores": {
                "decision_chain": record.decision_chain_score,
                "interaction_frequency": record.interaction_frequency_score,
                "relationship_depth": record.relationship_depth_score,
                "information_access": record.information_access_score,
                "support_level": record.support_level_score,
                "executive_engagement": record.executive_engagement_score,
            },
        }
