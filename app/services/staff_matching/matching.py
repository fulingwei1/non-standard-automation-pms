# -*- coding: utf-8 -*-
"""
人员智能匹配服务 - 主匹配逻辑
"""

import json
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.organization import Employee
from app.models.project import Project
from app.models.staff_matching import (
    HrAIMatchingLog,
    HrEmployeeProfile,
    MesProjectStaffingNeed,
)
from app.services.ai_client_service import AIClientService
from app.services.ai_structured_output import extract_json_payload

from .base import StaffMatchingBase
from .score_calculators import (
    AttitudeScoreCalculator,
    DomainScoreCalculator,
    QualityScoreCalculator,
    SkillScoreCalculator,
    SpecialScoreCalculator,
    WorkloadScoreCalculator,
)


class MatchingEngine(StaffMatchingBase):
    """匹配引擎 - 执行主匹配算法"""

    _ai_client: Optional[AIClientService] = None

    @classmethod
    def match_candidates(
        cls, db: Session, staffing_need_id: int, top_n: int = 10, include_overloaded: bool = False
    ) -> Dict:
        """
        执行AI匹配算法

        Args:
            db: 数据库会话
            staffing_need_id: 人员需求ID
            top_n: 返回候选人数量
            include_overloaded: 是否包含超负荷员工

        Returns:
            匹配结果字典
        """
        # 获取人员需求
        staffing_need = (
            db.query(MesProjectStaffingNeed)
            .filter(MesProjectStaffingNeed.id == staffing_need_id)
            .first()
        )

        if not staffing_need:
            raise ValueError(f"人员需求不存在: {staffing_need_id}")

        # 获取项目信息
        project = db.query(Project).filter(Project.id == staffing_need.project_id).first()

        # 生成请求ID
        request_id = (
            f"MATCH-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8].upper()}"
        )

        # 获取所有活跃员工及其档案
        candidates = cls._get_candidate_employees(db, staffing_need, include_overloaded)

        # 计算每个候选人的得分
        scored_candidates = []
        for employee, profile in candidates:
            scores = cls._calculate_candidate_scores(db, employee, profile, staffing_need)
            scored_candidates.append(
                {
                    "employee": employee,
                    "profile": profile,
                    "scores": scores,
                    "total_score": scores["total"],
                }
            )

        # 按总分排序
        scored_candidates.sort(key=lambda x: x["total_score"], reverse=True)

        # 获取优先级阈值
        threshold = cls.get_priority_threshold(staffing_need.priority)

        # 构建结果
        result_candidates = []
        for rank, candidate in enumerate(scored_candidates[:top_n], 1):
            employee = candidate["employee"]
            profile = candidate["profile"]
            scores = candidate["scores"]

            # 分类推荐类型
            recommendation_type = cls.classify_recommendation(scores["total"], threshold)

            # 保存匹配日志
            log = HrAIMatchingLog(
                request_id=request_id,
                project_id=staffing_need.project_id,
                staffing_need_id=staffing_need_id,
                candidate_employee_id=employee.id,
                total_score=Decimal(str(round(scores["total"], 2))),
                dimension_scores={
                    "skill": round(scores["skill"], 2),
                    "domain": round(scores["domain"], 2),
                    "attitude": round(scores["attitude"], 2),
                    "quality": round(scores["quality"], 2),
                    "workload": round(scores["workload"], 2),
                    "special": round(scores["special"], 2),
                },
                rank=rank,
                recommendation_type=recommendation_type,
                matching_time=datetime.now(),
            )
            db.add(log)

            # 构建候选人信息
            result_candidates.append(
                {
                    "employee_id": employee.id,
                    "employee_name": employee.name,
                    "employee_code": employee.employee_code,
                    "department": employee.department,
                    "total_score": round(scores["total"], 2),
                    "dimension_scores": {
                        "skill": round(scores["skill"], 2),
                        "domain": round(scores["domain"], 2),
                        "attitude": round(scores["attitude"], 2),
                        "quality": round(scores["quality"], 2),
                        "workload": round(scores["workload"], 2),
                        "special": round(scores["special"], 2),
                    },
                    "rank": rank,
                    "recommendation_type": recommendation_type,
                    "matched_skills": scores.get("matched_skills", []),
                    "missing_skills": scores.get("missing_skills", []),
                    "current_workload_pct": float(profile.current_workload_pct) if profile else 0,
                    "available_hours": float(profile.available_hours) if profile else 0,
                }
            )

        explanation_result = cls._generate_candidate_explanations(
            project=project,
            staffing_need=staffing_need,
            candidates=result_candidates,
        )
        explanation_map = explanation_result.get("candidate_map", {})
        for candidate in result_candidates:
            explanation = explanation_map.get(candidate["employee_id"], {})
            candidate["recommendation_reason"] = explanation.get(
                "recommendation_reason",
                cls._build_fallback_reason(candidate),
            )
            candidate["risk_notes"] = explanation.get(
                "risk_notes",
                cls._build_risk_notes(candidate),
            )

        # 更新需求状态为匹配中
        staffing_need.status = "MATCHING"
        db.commit()

        # 统计达到阈值的候选人数
        qualified_count = sum(1 for c in result_candidates if c["total_score"] >= threshold)

        return {
            "request_id": request_id,
            "staffing_need_id": staffing_need_id,
            "project_id": staffing_need.project_id,
            "project_name": project.name if project else None,
            "role_code": staffing_need.role_code,
            "role_name": staffing_need.role_name,
            "priority": staffing_need.priority,
            "priority_threshold": threshold,
            "candidates": result_candidates,
            "total_candidates": len(scored_candidates),
            "qualified_count": qualified_count,
            "matching_time": datetime.now().isoformat(),
            "analysis_summary": explanation_result.get(
                "analysis_summary",
                cls._build_default_summary(result_candidates, qualified_count, threshold),
            ),
        }

    @classmethod
    def _get_candidate_employees(
        cls, db: Session, staffing_need: MesProjectStaffingNeed, include_overloaded: bool
    ) -> List[Tuple[Employee, Optional[HrEmployeeProfile]]]:
        """获取候选员工列表"""
        # 基础查询：活跃员工
        query = (
            db.query(Employee, HrEmployeeProfile)
            .outerjoin(HrEmployeeProfile, Employee.id == HrEmployeeProfile.employee_id)
            .filter(Employee.is_active)
        )

        # 如果不包含超负荷员工，过滤工作负载
        if not include_overloaded:
            required_allocation = float(staffing_need.allocation_pct or 100)
            # 员工当前负载 + 需求分配比例 <= 100%，或者没有档案记录的员工
            query = query.filter(
                or_(
                    HrEmployeeProfile.id is None,  # 没有档案的员工（假设可用）
                    HrEmployeeProfile.current_workload_pct <= (100 - required_allocation * 0.5),
                )
            )

        return query.all()

    @classmethod
    def _calculate_candidate_scores(
        cls,
        db: Session,
        employee: Employee,
        profile: Optional[HrEmployeeProfile],
        staffing_need: MesProjectStaffingNeed,
    ) -> Dict:
        """计算候选人各维度得分"""
        scores = {
            "skill": 0.0,
            "domain": 0.0,
            "attitude": 0.0,
            "quality": 0.0,
            "workload": 0.0,
            "special": 0.0,
            "matched_skills": [],
            "missing_skills": [],
        }

        # 1. 计算技能匹配分
        skill_result = SkillScoreCalculator.calculate_skill_score(
            db,
            employee.id,
            profile,
            staffing_need.required_skills or [],
            staffing_need.preferred_skills or [],
        )
        scores["skill"] = skill_result["score"]
        scores["matched_skills"] = skill_result.get("matched", [])
        scores["missing_skills"] = skill_result.get("missing", [])

        # 2. 计算领域匹配分
        scores["domain"] = DomainScoreCalculator.calculate_domain_score(
            db, employee.id, profile, staffing_need.required_domains or []
        )

        # 3. 计算态度评分
        scores["attitude"] = AttitudeScoreCalculator.calculate_attitude_score(
            db, employee.id, profile, staffing_need.required_attitudes or []
        )

        # 4. 计算质量评分（从历史绩效）
        scores["quality"] = QualityScoreCalculator.calculate_quality_score(db, employee.id)

        # 5. 计算工作负载分
        scores["workload"] = WorkloadScoreCalculator.calculate_workload_score(
            profile, float(staffing_need.allocation_pct or 100)
        )

        # 6. 计算特殊能力分
        scores["special"] = SpecialScoreCalculator.calculate_special_score(db, employee.id, profile)

        # 计算加权总分
        scores["total"] = (
            scores["skill"] * cls.DIMENSION_WEIGHTS["skill"]
            + scores["domain"] * cls.DIMENSION_WEIGHTS["domain"]
            + scores["attitude"] * cls.DIMENSION_WEIGHTS["attitude"]
            + scores["quality"] * cls.DIMENSION_WEIGHTS["quality"]
            + scores["workload"] * cls.DIMENSION_WEIGHTS["workload"]
            + scores["special"] * cls.DIMENSION_WEIGHTS["special"]
        )

        return scores

    @classmethod
    def _get_ai_client(cls) -> AIClientService:
        """懒加载AI客户端，避免在导入阶段初始化。"""
        if cls._ai_client is None:
            cls._ai_client = AIClientService()
        return cls._ai_client

    @classmethod
    def _has_live_ai(cls) -> bool:
        """检查是否可进行真实AI调用。"""
        client = cls._get_ai_client()
        openai_ready = bool(
            client.openai_client and str(client.openai_api_key).startswith(("sk-", "sk-proj-"))
        )
        return bool(openai_ready or client.zhipu_client or client.kimi_api_key)

    @classmethod
    def _generate_ai_content(
        cls, prompt: str, temperature: float = 0.2, max_tokens: int = 1600
    ) -> Optional[str]:
        """统一AI调用封装。"""
        if not cls._has_live_ai():
            return None

        client = cls._get_ai_client()
        models = [client.default_model]
        for model in models:
            try:
                response = client.generate_solution(
                    prompt=prompt,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            except Exception:
                continue

            content = (response or {}).get("content")
            model_name = str((response or {}).get("model", ""))
            if content and not model_name.endswith("-mock"):
                return str(content).strip()

        return None

    @classmethod
    def _generate_candidate_explanations(
        cls,
        project: Optional[Project],
        staffing_need: MesProjectStaffingNeed,
        candidates: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """为候选人补充AI解释信息。"""
        if not candidates:
            return {"candidate_map": {}, "analysis_summary": "暂无候选人满足当前筛选条件。"}

        ai_result = cls._generate_candidate_explanations_with_ai(project, staffing_need, candidates)
        if ai_result:
            return ai_result

        candidate_map = {
            candidate["employee_id"]: {
                "recommendation_reason": cls._build_fallback_reason(candidate),
                "risk_notes": cls._build_risk_notes(candidate),
            }
            for candidate in candidates
        }
        return {
            "candidate_map": candidate_map,
            "analysis_summary": cls._build_default_summary(
                candidates,
                sum(1 for candidate in candidates if candidate["recommendation_type"] != "WEAK"),
                cls.get_priority_threshold(staffing_need.priority),
            ),
        }

    @classmethod
    def _generate_candidate_explanations_with_ai(
        cls,
        project: Optional[Project],
        staffing_need: MesProjectStaffingNeed,
        candidates: List[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        """使用AI总结候选人推荐原因和风险。"""
        payload = {
            "project_name": project.name if project else None,
            "role_code": staffing_need.role_code,
            "role_name": staffing_need.role_name,
            "priority": staffing_need.priority,
            "required_skills": staffing_need.required_skills or [],
            "preferred_skills": staffing_need.preferred_skills or [],
            "required_domains": staffing_need.required_domains or [],
            "required_attitudes": staffing_need.required_attitudes or [],
            "candidates": candidates[:5],
        }
        prompt = f"""你是一名项目资源配置顾问，请根据以下人员匹配结果，给出每位候选人的推荐理由和风险提示。

输入数据：
{json.dumps(payload, ensure_ascii=False, indent=2, default=str)}

请仅输出 JSON：
{{
  "analysis_summary": "整体推荐结论",
  "candidates": [
    {{
      "employee_id": 1,
      "recommendation_reason": "推荐原因",
      "risk_notes": ["风险1", "风险2"]
    }}
  ]
}}

要求：
1. 解释必须基于输入分数、技能和负载信息。
2. risk_notes 最多 3 条。
3. 只输出合法 JSON。"""

        content = cls._generate_ai_content(prompt, temperature=0.2, max_tokens=1400)
        parsed = extract_json_payload(content or "")
        if not isinstance(parsed, dict):
            return None

        candidate_map = {}
        for item in parsed.get("candidates", []):
            if not isinstance(item, dict) or item.get("employee_id") is None:
                continue
            risk_notes = item.get("risk_notes")
            if not isinstance(risk_notes, list):
                risk_notes = []
            candidate_map[int(item["employee_id"])] = {
                "recommendation_reason": str(item.get("recommendation_reason") or "").strip(),
                "risk_notes": [
                    str(note).strip() for note in risk_notes if str(note).strip()
                ][:3],
            }

        if not candidate_map:
            return None

        return {
            "candidate_map": candidate_map,
            "analysis_summary": str(parsed.get("analysis_summary") or "").strip() or None,
        }

    @classmethod
    def _build_fallback_reason(cls, candidate: Dict[str, Any]) -> str:
        """在无AI时生成稳定的推荐说明。"""
        parts = []
        matched_skills = candidate.get("matched_skills") or []
        missing_skills = candidate.get("missing_skills") or []
        workload = float(candidate.get("current_workload_pct") or 0)
        total_score = float(candidate.get("total_score") or 0)

        if matched_skills:
            parts.append(f"核心匹配技能包括：{', '.join(matched_skills[:3])}")
        if total_score >= 85:
            parts.append("综合得分高，适合作为优先候选")
        elif total_score >= 70:
            parts.append("综合能力较均衡，可作为推荐人选")
        else:
            parts.append("具备一定匹配度，但需要结合项目优先级进一步评估")
        if workload <= 60:
            parts.append("当前负载相对可控，具备较好的投入空间")
        elif workload <= 85:
            parts.append("当前负载中等，安排时需协调资源窗口")
        if missing_skills:
            parts.append(f"仍需补位技能：{', '.join(missing_skills[:2])}")

        return "；".join(parts)

    @classmethod
    def _build_risk_notes(cls, candidate: Dict[str, Any]) -> List[str]:
        """生成风险提示。"""
        risk_notes = []
        workload = float(candidate.get("current_workload_pct") or 0)
        missing_skills = candidate.get("missing_skills") or []
        recommendation_type = candidate.get("recommendation_type")

        if workload >= 85:
            risk_notes.append("当前工作负载偏高，需确认是否具备及时投入能力。")
        elif workload >= 70:
            risk_notes.append("当前工作负载较高，建议预留缓冲时间。")

        if missing_skills:
            risk_notes.append(f"存在待补齐技能：{', '.join(missing_skills[:3])}。")

        if recommendation_type == "WEAK":
            risk_notes.append("综合得分低于推荐阈值，建议仅作为备选方案。")

        return risk_notes[:3]

    @classmethod
    def _build_default_summary(
        cls, candidates: List[Dict[str, Any]], qualified_count: int, threshold: int
    ) -> str:
        """生成整体分析摘要。"""
        if not candidates:
            return "暂无候选人满足当前筛选条件。"
        top_candidate = candidates[0]
        return (
            f"本次共评估 {len(candidates)} 名候选人，其中 {qualified_count} 人达到阈值 "
            f"{threshold} 分。当前首选为 {top_candidate['employee_name']}，综合得分 "
            f"{top_candidate['total_score']} 分。"
        )
