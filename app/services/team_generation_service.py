# -*- coding: utf-8 -*-
"""
AI 自动组队服务

根据项目需求自动生成项目组成员方案
"""

import json
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.engineer_capacity import EngineerCapacity, EngineerTaskAssignment
from app.models.pmo import PmoProjectInitiation
from app.models.project import Project
from app.models.project_team import ProjectTeamMember, ProjectTeamPlan
from app.models.user import User


class TeamGenerationService:
    """AI 自动组队服务"""

    def __init__(self, db: Session):
        self.db = db

    def generate_team_plan(self, project_id: int) -> Dict[str, Any]:
        """
        为项目自动生成团队方案

        流程：
        1. 分析项目需求
        2. 确定所需角色
        3. 匹配工程师
        4. 优化组合
        5. 生成方案
        """
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return {"error": "项目不存在"}

        # 1. 分析项目需求
        requirements = self._analyze_project_requirements(project)

        # 2. 确定所需角色和人数
        roles_needed = self._determine_roles(requirements, project)

        # 3. 为每个角色匹配工程师
        role_assignments = {}
        for role, role_info in roles_needed.items():
            candidates = self._match_engineers_for_role(role, role_info, project)
            if candidates:
                role_assignments[role] = candidates[0]  # 选择最佳匹配

        # 4. 检查负载均衡
        self._check_workload_balance(role_assignments)

        # 5. 生成团队方案
        team_plan = self._create_team_plan(project, role_assignments, requirements)

        return team_plan

    def _analyze_project_requirements(self, project: Project) -> Dict[str, Any]:
        """分析项目需求"""
        initiation = self._get_initiation_context(project)
        product_category = project.product_category or ""
        industry = project.industry or ""
        contract_amount = float(project.contract_amount or 0)
        technical_difficulty = getattr(initiation, "technical_difficulty", None) if initiation else None

        # 确定项目规模
        if contract_amount > 5000000:
            scale = "LARGE"
        elif contract_amount > 3000000:
            scale = "MEDIUM"
        else:
            scale = "SMALL"

        # 确定技术复杂度
        complexity_map = {
            "ICT": "MEDIUM",
            "FCT": "HIGH",
            "EOL": "HIGH",
            "aging": "MEDIUM",
            "vision": "EXPERT",
        }
        tech_complexity = complexity_map.get(product_category, "MEDIUM")
        if technical_difficulty == "HIGH":
            tech_complexity = "HIGH"
        elif technical_difficulty == "LOW":
            tech_complexity = "MEDIUM"

        # 确定行业特殊要求
        industry_requirements = {
            "锂电": ["安全规范", "高压系统"],
            "光伏": ["并网标准", "户外环境"],
            "3C 电子": ["快速交付", "高精度"],
            "汽车": ["IATF16949", "追溯系统"],
            "医疗": ["洁净规范", "验证文档"],
        }

        return {
            "scale": scale,
            "tech_complexity": tech_complexity,
            "industry_requirements": industry_requirements.get(industry, []),
            "product_category": product_category,
            "contract_amount": contract_amount,
            "source": "pmo_initiation" if initiation else "project",
            "initiation_id": getattr(initiation, "id", None) if initiation else None,
            "estimated_hours": float(getattr(initiation, "estimated_hours", 0) or 0),
            "resource_requirements": (
                getattr(initiation, "resource_requirements", None) if initiation else None
            )
            or "",
            "technical_difficulty": technical_difficulty,
            "project_level": getattr(initiation, "project_level", None) if initiation else None,
        }

    def _get_initiation_context(self, project: Project) -> Optional[PmoProjectInitiation]:
        """回查由立项审批创建/绑定的项目上下文。"""
        project_id = getattr(project, "id", None)
        if not project_id:
            return None

        try:
            return (
                self.db.query(PmoProjectInitiation)
                .filter(PmoProjectInitiation.project_id == project_id)
                .filter(PmoProjectInitiation.status == "APPROVED")
                .order_by(PmoProjectInitiation.id.desc())
                .first()
            )
        except Exception:  # noqa: BLE001 - 兼容缺表/旧库，组队仍可按项目字段运行
            return None

    def _determine_roles(self, requirements: Dict, project: Project) -> Dict[str, Any]:
        """确定所需角色和人数"""
        scale = requirements["scale"]
        product_category = requirements["product_category"]
        resource_requirements = str(requirements.get("resource_requirements") or "")
        resource_text = resource_requirements.lower()

        # 基础角色配置
        base_roles = {
            "PM": {  # 项目经理
                "count": 1,
                "required_skills": ["项目管理", "客户沟通"],
                "min_experience": 5,
                "ai_level": "INTERMEDIATE",
                "multi_project_min": 3,
            },
            "TECH_LEAD": {  # 技术负责人
                "count": 1,
                "required_skills": ["系统设计", "技术评审"],
                "min_experience": 5,
                "ai_level": "ADVANCED",
                "standardization_min": 7.0,
            },
        }

        def mentions(*keywords: str) -> bool:
            return any(keyword.lower() in resource_text for keyword in keywords)

        # 根据产品类型添加专业角色
        if product_category in ["ICT", "FCT", "EOL"] or mentions("电气", "plc", "控制"):
            base_roles["ELEC_ENG"] = {  # 电气工程师
                "count": 2 if scale == "LARGE" else 1,
                "required_skills": ["电气设计", "PLC 调试"],
                "min_experience": 3,
            }
        if product_category in ["ICT", "FCT", "EOL"] or mentions("机械", "夹具", "结构"):
            base_roles["MECH_ENG"] = {  # 机械工程师
                "count": 1,
                "required_skills": ["机械设计", "CAD"],
                "min_experience": 3,
            }

        if product_category == "vision" or mentions("视觉", "图像", "光学"):
            base_roles["VISION_ENG"] = {  # 视觉工程师
                "count": 1,
                "required_skills": ["视觉算法", "光学调试"],
                "min_experience": 4,
                "ai_level": "ADVANCED",
            }

        if mentions("软件", "上位机", "mes", "scada", "数据采集"):
            base_roles["SOFTWARE_ENG"] = {
                "count": 1,
                "required_skills": ["软件开发", "上位机"],
                "min_experience": 3,
                "ai_level": "INTERMEDIATE",
            }

        if mentions("测试", "验证", "fat", "sat"):
            base_roles["TEST_ENG"] = {
                "count": 1,
                "required_skills": ["测试验证", "问题闭环"],
                "min_experience": 2,
            }

        # 售后服务工程师
        base_roles["SERVICE_ENG"] = {  # 售后工程师
            "count": 1,
            "required_skills": ["客户沟通", "快速诊断"],
            "min_experience": 2,
            "customer_facing": True,
        }

        self._apply_initiation_hour_allocation(base_roles, requirements)

        return base_roles

    def _apply_initiation_hour_allocation(
        self, roles: Dict[str, Dict[str, Any]], requirements: Dict[str, Any]
    ) -> None:
        """把立项预计总工时分摊到本次团队角色。"""
        estimated_hours = float(requirements.get("estimated_hours") or 0)
        if estimated_hours <= 0 or not roles:
            return

        role_weights = {
            "PM": 0.15,
            "TECH_LEAD": 0.20,
            "MECH_ENG": 0.20,
            "ELEC_ENG": 0.25,
            "VISION_ENG": 0.15,
            "SOFTWARE_ENG": 0.15,
            "TEST_ENG": 0.10,
            "SERVICE_ENG": 0.05,
        }
        total_weight = sum(role_weights.get(role, 0.10) for role in roles)
        if total_weight <= 0:
            return

        for role, role_info in roles.items():
            role_info["estimated_hours"] = round(
                estimated_hours * role_weights.get(role, 0.10) / total_weight,
                2,
            )

    def _match_engineers_for_role(
        self,
        role: str,
        role_info: Dict,
        project: Project,
    ) -> List[Dict[str, Any]]:
        """为角色匹配工程师"""
        role_info.get("required_skills", [])
        role_info.get("min_experience", 0)
        role_info.get("ai_level", "NONE")

        # 查询工程师
        engineers = (
            self.db.query(User, EngineerCapacity)
            .outerjoin(EngineerCapacity, User.id == EngineerCapacity.engineer_id)
            .filter(User.is_active == True)
            .all()
        )

        candidates = []

        for user, capacity in engineers:
            if not capacity:
                continue

            # 计算匹配度
            match_result = self._calculate_role_match(user, capacity, role, role_info, project)

            if match_result["score"] >= 60:
                candidates.append(
                    {
                        "engineer_id": user.id,
                        "engineer_name": user.real_name or user.username,
                        "department": user.department,
                        "role": role,
                        "role_name": self._get_role_name(role),
                        "match_score": match_result["score"],
                        "match_reason": match_result["reason"],
                        "estimated_hours": self._estimate_hours(role, project, role_info),
                        "capacity": capacity,
                    }
                )

        # 按匹配度排序
        candidates.sort(key=lambda x: x["match_score"], reverse=True)

        return candidates

    def _calculate_role_match(
        self,
        engineer: User,
        capacity: EngineerCapacity,
        role: str,
        role_info: Dict,
        project: Project,
    ) -> Dict[str, Any]:
        """计算工程师与角色的匹配度"""
        score = 100
        reasons = []

        # 1. 技能匹配（40 分）
        engineer_skills = []
        if capacity.skill_tags:
            try:
                engineer_skills = json.loads(capacity.skill_tags)
            except (json.JSONDecodeError, TypeError):
                # JSON 格式无效，保持空列表
                pass

        required_skills = role_info.get("required_skills", [])
        matched = [s for s in required_skills if any(s in e or e in s for e in engineer_skills)]
        skill_score = len(matched) / len(required_skills) * 40 if required_skills else 40
        score = score - 40 + skill_score

        if skill_score >= 35:
            reasons.append(f"技能匹配 ({len(matched)}/{len(required_skills)})")

        # 2. 经验匹配（20 分）
        experience_score = self._calculate_experience_score(
            engineer,
            capacity,
            role,
            role_info,
            project,
        )
        score = score - 20 + experience_score
        if experience_score >= 12:
            reasons.append(f"经验匹配 ({experience_score:.1f}/20)")

        # 3. AI 能力（15 分）
        ai_levels = {"NONE": 0, "BASIC": 1, "INTERMEDIATE": 2, "ADVANCED": 3, "EXPERT": 4}
        required_ai = role_info.get("ai_level", "NONE")
        if ai_levels.get(capacity.ai_skill_level, 0) >= ai_levels.get(required_ai, 0):
            ai_score = 15
            reasons.append(f"AI 能力达标 ({capacity.ai_skill_level})")
        else:
            ai_score = 5
        score = score - 15 + ai_score

        # 4. 多项目能力（15 分）
        multi_project_min = role_info.get("multi_project_min", 0)
        if multi_project_min > 0:
            if capacity.multi_project_capacity >= multi_project_min:
                mp_score = 15
                reasons.append(f"多项目能力 ({capacity.multi_project_capacity})")
            else:
                mp_score = 5
        else:
            mp_score = 15
        score = score - 15 + mp_score

        # 5. 标准化能力（10 分）
        std_min = role_info.get("standardization_min", 0)
        if std_min > 0:
            if capacity.standardization_score >= std_min:
                std_score = 10
                reasons.append(f"标准化能力 ({capacity.standardization_score:.1f})")
            else:
                std_score = 3
        else:
            std_score = 10
        score = score - 10 + std_score

        # 6. 当前负载（额外扣分）
        if hasattr(capacity, "workload_status"):
            if capacity.workload_status == "OVERLOAD":
                score -= 20
            elif capacity.workload_status == "BUSY":
                score -= 10

        score = max(0, min(100, score))

        return {
            "score": round(score, 1),
            "reason": "。".join(reasons[:3]),
        }

    def _calculate_experience_score(
        self,
        engineer: User,
        capacity: EngineerCapacity,
        role: str,
        role_info: Dict,
        project: Project,
    ) -> float:
        """按历史任务、交付质量和返工情况计算经验分（0-20）。"""

        def safe_float(value: Any, default: float = 0.0) -> float:
            try:
                return float(value)
            except (TypeError, ValueError):
                return default

        assignments = []
        try:
            assignments = (
                self.db.query(EngineerTaskAssignment)
                .filter(EngineerTaskAssignment.engineer_id == engineer.id)
                .all()
            )
        except Exception:  # noqa: BLE001 - 缺表/旧库时回退能力画像
            assignments = []

        completed_statuses = {"COMPLETED", "DONE", "CLOSED", "FINISHED"}
        completed = [
            item
            for item in assignments
            if str(getattr(item, "status", "") or "").upper() in completed_statuses
        ]

        required_skills = role_info.get("required_skills", [])
        role_name = self._get_role_name(role)
        keywords = [role, role_name, *required_skills]

        def is_relevant(item: Any) -> bool:
            text = " ".join(
                str(part or "")
                for part in (
                    getattr(item, "task_type", ""),
                    getattr(item, "task_description", ""),
                    getattr(project, "product_category", ""),
                    getattr(project, "industry", ""),
                )
            ).lower()
            return any(str(keyword).lower() in text for keyword in keywords if keyword)

        relevant = [item for item in completed if is_relevant(item)] or completed

        target_count = max(1, int(role_info.get("min_experience", 0) or 1))
        count_score = min(len(relevant) / target_count, 1.0) * 8

        quality_values = [
            safe_float(getattr(item, "quality_score", None))
            for item in relevant
            if getattr(item, "quality_score", None) is not None
        ]
        avg_quality = (
            sum(quality_values) / len(quality_values)
            if quality_values
            else safe_float(getattr(capacity, "avg_quality_score", 0))
        )
        quality_score = max(0.0, min(avg_quality / 10, 1.0)) * 5

        if relevant:
            on_time_rate = (
                sum(1 for item in relevant if bool(getattr(item, "is_on_time", False)))
                / len(relevant)
                * 100
            )
            rework_rate = (
                sum(1 for item in relevant if bool(getattr(item, "has_rework", False)))
                / len(relevant)
                * 100
            )
        else:
            on_time_rate = safe_float(getattr(capacity, "on_time_delivery_rate", 0))
            rework_rate = safe_float(getattr(capacity, "rework_rate", 100), 100.0)

        delivery_score = max(0.0, min(on_time_rate / 100, 1.0)) * 5
        rework_score = max(0.0, min(1 - rework_rate / 100, 1.0)) * 2

        return round(min(20.0, count_score + quality_score + delivery_score + rework_score), 1)

    def _get_role_name(self, role: str) -> str:
        """获取角色中文名称"""
        role_names = {
            "PM": "项目经理",
            "TECH_LEAD": "技术负责人",
            "MECH_ENG": "机械工程师",
            "ELEC_ENG": "电气工程师",
            "VISION_ENG": "视觉工程师",
            "SOFTWARE_ENG": "软件工程师",
            "TEST_ENG": "测试工程师",
            "SERVICE_ENG": "售后工程师",
        }
        return role_names.get(role, role)

    def _estimate_hours(
        self,
        role: str,
        project: Project,
        role_info: Optional[Dict[str, Any]] = None,
    ) -> float:
        """估算工时"""
        if role_info and role_info.get("estimated_hours") is not None:
            return float(role_info.get("estimated_hours") or 0)

        contract_amount = float(project.contract_amount or 0)

        # 简化估算
        base_hours = {
            "PM": 0.15,  # 15% 总工时
            "TECH_LEAD": 0.20,
            "MECH_ENG": 0.20,
            "ELEC_ENG": 0.25,
            "VISION_ENG": 0.15,
            "SOFTWARE_ENG": 0.15,
            "TEST_ENG": 0.10,
            "SERVICE_ENG": 0.05,
        }

        total_hours = contract_amount / 10000  # 每万元 1 小时
        return total_hours * base_hours.get(role, 0.1)

    def _check_workload_balance(self, role_assignments: Dict) -> Dict[str, Any]:
        """检查负载均衡"""
        overloaded = []
        balanced = []

        for role, assignment in role_assignments.items():
            capacity = assignment.get("capacity")
            if capacity and hasattr(capacity, "workload_status"):
                if capacity.workload_status == "OVERLOAD":
                    overloaded.append(assignment["engineer_name"])
                else:
                    balanced.append(assignment["engineer_name"])

        return {
            "overloaded_count": len(overloaded),
            "balanced_count": len(balanced),
            "overloaded_engineers": overloaded,
            "balance_score": 100 - (len(overloaded) * 20),
        }

    def _create_team_plan(
        self,
        project: Project,
        role_assignments: Dict,
        requirements: Dict,
    ) -> Dict[str, Any]:
        """创建团队方案"""
        total_hours = sum(a.get("estimated_hours", 0) for a in role_assignments.values())

        # 计算方案评分
        skill_coverage = 85  # 简化
        capacity_balance = (
            100
            - len(
                [
                    a
                    for a in role_assignments.values()
                    if a.get("capacity")
                    and getattr(a["capacity"], "workload_status", "") == "OVERLOAD"
                ]
            )
            * 20
        )
        cost_efficiency = 80

        overall_score = skill_coverage * 0.4 + capacity_balance * 0.3 + cost_efficiency * 0.3

        # 生成优势
        advantages = []
        if overall_score >= 85:
            advantages.append("团队整体匹配度高")
        if any(
            a.get("capacity")
            and getattr(a["capacity"], "ai_skill_level", "") in ["ADVANCED", "EXPERT"]
            for a in role_assignments.values()
        ):
            advantages.append("包含 AI 高级用户，效率有保障")
        if any(
            a.get("capacity") and getattr(a["capacity"], "multi_project_capacity", 0) >= 5
            for a in role_assignments.values()
        ):
            advantages.append("有多项目专家，可并行推进")

        # 生成风险
        risks = []
        overloaded = [
            a["engineer_name"]
            for a in role_assignments.values()
            if a.get("capacity") and getattr(a["capacity"], "workload_status", "") == "OVERLOAD"
        ]
        if overloaded:
            risks.append(f"{len(overloaded)}名工程师过载：{', '.join(overloaded[:3])}")

        role_count = max(len(role_assignments), 1)

        return {
            "project_id": project.id,
            "project_name": project.project_name,
            "total_members": len(role_assignments),
            "total_estimated_hours": total_hours,
            "estimated_duration_days": max(1, int(total_hours / 8 / role_count)),
            "overall_score": round(overall_score, 1),
            "skill_coverage": skill_coverage,
            "capacity_balance": capacity_balance,
            "cost_efficiency": cost_efficiency,
            "role_assignments": role_assignments,
            "requirements": {
                "source": requirements.get("source", "project"),
                "initiation_id": requirements.get("initiation_id"),
                "scale": requirements.get("scale"),
                "tech_complexity": requirements.get("tech_complexity"),
                "estimated_hours": requirements.get("estimated_hours", 0),
                "resource_requirements": requirements.get("resource_requirements", ""),
            },
            "advantages": advantages,
            "risks": risks,
            "recommendations": ["建议确认过载工程师的时间安排"] if overloaded else [],
        }

    def save_team_plan(self, team_data: Dict[str, Any], submitted_by: int) -> ProjectTeamPlan:
        """保存团队方案"""
        from datetime import datetime

        plan = ProjectTeamPlan(
            plan_no=f"PTP{datetime.now().strftime('%Y%m%d%H%M%S')}",
            project_id=team_data["project_id"],
            project_name=team_data["project_name"],
            total_members=team_data["total_members"],
            total_estimated_hours=team_data["total_estimated_hours"],
            estimated_duration_days=team_data["estimated_duration_days"],
            overall_score=team_data["overall_score"],
            skill_coverage=team_data["skill_coverage"],
            capacity_balance=team_data["capacity_balance"],
            cost_efficiency=team_data["cost_efficiency"],
            team_structure=json.dumps({"roles": list(team_data["role_assignments"].keys())}),
            role_assignments=json.dumps(team_data["role_assignments"]),
            advantages=json.dumps(team_data["advantages"]),
            risks=json.dumps(team_data["risks"]),
            recommendations=json.dumps(team_data["recommendations"]),
            status="DRAFT",
            submitted_by=submitted_by,
            submitted_at=datetime.now(),
        )

        self.db.add(plan)
        self.db.flush()

        # 添加成员
        for role, assignment in team_data["role_assignments"].items():
            member = ProjectTeamMember(
                team_plan_id=plan.id,
                engineer_id=assignment["engineer_id"],
                engineer_name=assignment["engineer_name"],
                role=role,
                role_name=assignment["role_name"],
                estimated_hours=assignment["estimated_hours"],
                match_score=assignment["match_score"],
                match_reason=assignment["match_reason"],
            )
            self.db.add(member)

        self.db.commit()
        self.db.refresh(plan)

        return plan
