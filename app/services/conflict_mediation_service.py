# -*- coding: utf-8 -*-
"""
冲突自动调解建议服务

提供三种调解策略：
1. 替代人选推荐 — 技能匹配 + 负荷排序
2. 时间调整建议 — 基于阶段依赖推荐延期/提前
3. 负荷均衡建议 — 项目间重新分配工作量
"""
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.project import Project, ProjectStageResourcePlan
from app.models.project.resource_plan import ResourceConflict as ResourceConflictModel
from app.models.user import User


class ConflictMediationService:
    """冲突调解建议服务"""

    def __init__(self, db: Session):
        self.db = db

    def get_recommendations(self, conflict_id: int) -> Dict[str, Any]:
        """
        为指定冲突生成全部调解建议

        Returns:
            {
                "conflict_id": int,
                "alternative_candidates": [...],
                "schedule_adjustments": [...],
                "workload_balancing": [...]
            }
        """
        conflict = (
            self.db.query(ResourceConflictModel)
            .filter(ResourceConflictModel.id == conflict_id)
            .first()
        )
        if not conflict:
            return {"error": "冲突记录不存在"}

        plan_a = conflict.plan_a
        plan_b = conflict.plan_b

        return {
            "conflict_id": conflict_id,
            "alternative_candidates": self._recommend_alternatives(conflict, plan_a, plan_b),
            "schedule_adjustments": self._recommend_schedule_adjustments(conflict, plan_a, plan_b),
            "workload_balancing": self._recommend_workload_balancing(conflict, plan_a, plan_b),
        }

    # ==================== 1. 替代人选推荐 ====================

    def _recommend_alternatives(
        self,
        conflict: ResourceConflictModel,
        plan_a: ProjectStageResourcePlan,
        plan_b: ProjectStageResourcePlan,
    ) -> List[Dict[str, Any]]:
        """
        推荐可替代的人选：同角色 + 时间段内负荷更低的员工

        对 plan_a 和 plan_b 分别推荐替代人选。
        """
        results = []

        for plan, label in [(plan_a, "plan_a"), (plan_b, "plan_b")]:
            if not plan:
                continue

            project = self.db.query(Project).filter(Project.id == plan.project_id).first()

            candidates = self._find_candidates_for_plan(plan, conflict.employee_id)

            results.append({
                "target_plan": label,
                "project_id": plan.project_id,
                "project_name": project.project_name if project else None,
                "stage_code": plan.stage_code,
                "role_code": plan.role_code,
                "role_name": plan.role_name,
                "candidates": candidates,
                "reason": f"为 {project.project_name if project else '项目'} 的 {plan.role_name or plan.role_code} 角色寻找替代人选",
            })

        return results

    def _find_candidates_for_plan(
        self, plan: ProjectStageResourcePlan, exclude_employee_id: int
    ) -> List[Dict[str, Any]]:
        """查找某个计划的替代候选人"""
        if not plan.planned_start or not plan.planned_end:
            return []

        # 找同角色的其他员工（已在其他资源计划中担任相同角色的人）
        same_role_employee_ids = (
            self.db.query(ProjectStageResourcePlan.assigned_employee_id)
            .filter(
                ProjectStageResourcePlan.role_code == plan.role_code,
                ProjectStageResourcePlan.assigned_employee_id.isnot(None),
                ProjectStageResourcePlan.assigned_employee_id != exclude_employee_id,
                ProjectStageResourcePlan.assignment_status == "ASSIGNED",
            )
            .distinct()
            .all()
        )
        same_role_ids = {r[0] for r in same_role_employee_ids}

        # 如果同角色的人太少，扩大搜索到同部门的所有人
        current_employee = self.db.query(User).filter(User.id == exclude_employee_id).first()
        if len(same_role_ids) < 3 and current_employee and current_employee.department_id:
            dept_employees = (
                self.db.query(User.id)
                .filter(
                    User.department_id == current_employee.department_id,
                    User.id != exclude_employee_id,
                    User.is_active == 1,
                )
                .all()
            )
            dept_ids = {r[0] for r in dept_employees}
            candidate_ids = same_role_ids | dept_ids
        else:
            candidate_ids = same_role_ids

        if not candidate_ids:
            return []

        # 计算每个候选人在冲突时间段的负荷
        candidates = []
        for cid in candidate_ids:
            user = self.db.query(User).filter(User.id == cid).first()
            if not user:
                continue

            allocation = self._calculate_period_allocation(
                cid, plan.planned_start, plan.planned_end
            )
            available_pct = max(Decimal("0"), Decimal("100") - allocation)

            # 需要的分配比例
            needed = plan.allocation_pct or Decimal("100")

            # 技能匹配分：同角色经验给高分
            skill_score = 80 if cid in same_role_ids else 50

            # 可用性分：可用比例越大越好
            availability_score = min(100, float(available_pct))

            # 综合分 = 技能 40% + 可用性 60%
            total_score = skill_score * 0.4 + availability_score * 0.6

            # 是否能胜任（可用比例 >= 需要的比例）
            can_fit = available_pct >= needed

            candidates.append({
                "employee_id": cid,
                "employee_name": user.username,
                "department": getattr(user, "position", None),
                "is_same_role": cid in same_role_ids,
                "current_allocation": float(allocation),
                "available_pct": float(available_pct),
                "needed_pct": float(needed),
                "can_fit": can_fit,
                "skill_score": skill_score,
                "availability_score": round(availability_score, 1),
                "total_score": round(total_score, 1),
                "reason": self._build_candidate_reason(
                    user.username, cid in same_role_ids, float(available_pct), can_fit
                ),
            })

        # 按总分降序排序，取前5名
        candidates.sort(key=lambda c: c["total_score"], reverse=True)
        return candidates[:5]

    def _calculate_period_allocation(
        self, employee_id: int, start: date, end: date
    ) -> Decimal:
        """计算员工在指定时间段的总分配比例"""
        assignments = (
            self.db.query(ProjectStageResourcePlan)
            .filter(
                ProjectStageResourcePlan.assigned_employee_id == employee_id,
                ProjectStageResourcePlan.assignment_status == "ASSIGNED",
                ProjectStageResourcePlan.planned_end >= start,
                ProjectStageResourcePlan.planned_start <= end,
            )
            .all()
        )

        total = Decimal("0")
        for a in assignments:
            total += a.allocation_pct or Decimal("100")
        return total

    @staticmethod
    def _build_candidate_reason(
        name: str, is_same_role: bool, available_pct: float, can_fit: bool
    ) -> str:
        parts = []
        if is_same_role:
            parts.append("具有相同角色经验")
        else:
            parts.append("同部门人员")

        if can_fit:
            parts.append(f"当前可用 {available_pct:.0f}%，可直接承接")
        else:
            parts.append(f"当前可用 {available_pct:.0f}%，需协调其他分配后可承接")

        return "；".join(parts)

    # ==================== 2. 时间调整建议 ====================

    def _recommend_schedule_adjustments(
        self,
        conflict: ResourceConflictModel,
        plan_a: ProjectStageResourcePlan,
        plan_b: ProjectStageResourcePlan,
    ) -> List[Dict[str, Any]]:
        """
        推荐时间调整方案：
        - 方案A: plan_b 延后（等 plan_a 结束后开始）
        - 方案B: plan_a 提前完成
        - 方案C: 缩短重叠时间（各自调整一半）
        """
        if not plan_a or not plan_b:
            return []
        if not all([plan_a.planned_start, plan_a.planned_end, plan_b.planned_start, plan_b.planned_end]):
            return []

        project_a = self.db.query(Project).filter(Project.id == plan_a.project_id).first()
        project_b = self.db.query(Project).filter(Project.id == plan_b.project_id).first()
        name_a = project_a.project_name if project_a else "项目A"
        name_b = project_b.project_name if project_b else "项目B"

        overlap_days = (conflict.overlap_end - conflict.overlap_start).days

        suggestions = []

        # 方案1: plan_b 延后到 plan_a 结束后
        new_b_start = plan_a.planned_end + timedelta(days=1)
        duration_b = (plan_b.planned_end - plan_b.planned_start).days
        new_b_end = new_b_start + timedelta(days=duration_b)
        delay_days = (new_b_start - plan_b.planned_start).days

        if delay_days > 0:
            suggestions.append({
                "type": "DELAY",
                "target_plan": "plan_b",
                "project_name": name_b,
                "stage_code": plan_b.stage_code,
                "description": f"将 {name_b} {plan_b.stage_code} 阶段延后 {delay_days} 天",
                "original_period": f"{plan_b.planned_start} ~ {plan_b.planned_end}",
                "suggested_period": f"{new_b_start} ~ {new_b_end}",
                "delay_days": delay_days,
                "impact": self._assess_delay_impact(plan_b, delay_days),
                "reason": f"等待 {name_a} {plan_a.stage_code} 阶段完成后再启动，完全消除重叠",
            })

        # 方案2: plan_a 提前完成（压缩工期）
        new_a_end = plan_b.planned_start - timedelta(days=1)
        compress_days = (plan_a.planned_end - new_a_end).days

        if compress_days > 0 and new_a_end > plan_a.planned_start:
            original_duration = (plan_a.planned_end - plan_a.planned_start).days
            suggestions.append({
                "type": "ADVANCE",
                "target_plan": "plan_a",
                "project_name": name_a,
                "stage_code": plan_a.stage_code,
                "description": f"将 {name_a} {plan_a.stage_code} 阶段提前 {compress_days} 天完成",
                "original_period": f"{plan_a.planned_start} ~ {plan_a.planned_end}",
                "suggested_period": f"{plan_a.planned_start} ~ {new_a_end}",
                "compress_days": compress_days,
                "impact": f"工期从 {original_duration} 天压缩到 {original_duration - compress_days} 天",
                "reason": f"在 {name_b} {plan_b.stage_code} 阶段开始前完成，避免人员冲突",
            })

        # 方案3: 双方各调整一半，降低重叠
        half_overlap = overlap_days // 2
        if half_overlap > 0:
            suggestions.append({
                "type": "SPLIT",
                "target_plan": "both",
                "description": f"双向调整：{name_a} 提前 {half_overlap} 天完成 + {name_b} 延后 {overlap_days - half_overlap} 天开始",
                "adjustments": [
                    {
                        "plan": "plan_a",
                        "project_name": name_a,
                        "original_end": str(plan_a.planned_end),
                        "suggested_end": str(plan_a.planned_end - timedelta(days=half_overlap)),
                    },
                    {
                        "plan": "plan_b",
                        "project_name": name_b,
                        "original_start": str(plan_b.planned_start),
                        "suggested_start": str(plan_b.planned_start + timedelta(days=overlap_days - half_overlap)),
                    },
                ],
                "reason": "双方各承担部分调整，对两个项目的影响最小化",
            })

        # 方案4: 降低分配比例
        needed_reduction = float(conflict.over_allocation)
        if needed_reduction > 0:
            alloc_a = float(plan_a.allocation_pct or 100)
            alloc_b = float(plan_b.allocation_pct or 100)
            # 按比例分摊削减
            ratio_a = alloc_a / (alloc_a + alloc_b)
            reduce_a = round(needed_reduction * ratio_a, 0)
            reduce_b = round(needed_reduction - reduce_a, 0)

            suggestions.append({
                "type": "REDUCE_ALLOCATION",
                "target_plan": "both",
                "description": f"降低分配比例：{name_a} 从 {alloc_a:.0f}% 降到 {alloc_a - reduce_a:.0f}%，{name_b} 从 {alloc_b:.0f}% 降到 {alloc_b - reduce_b:.0f}%",
                "adjustments": [
                    {
                        "plan": "plan_a",
                        "project_name": name_a,
                        "original_pct": alloc_a,
                        "suggested_pct": alloc_a - reduce_a,
                    },
                    {
                        "plan": "plan_b",
                        "project_name": name_b,
                        "original_pct": alloc_b,
                        "suggested_pct": alloc_b - reduce_b,
                    },
                ],
                "reason": f"将总分配从 {alloc_a + alloc_b:.0f}% 降到 100%，消除超额分配",
            })

        return suggestions

    def _assess_delay_impact(self, plan: ProjectStageResourcePlan, delay_days: int) -> str:
        """评估延期对项目的影响"""
        # 查看该项目是否有后续阶段
        stage_num = int(plan.stage_code[1]) if plan.stage_code and len(plan.stage_code) == 2 else 0
        next_stage = f"S{stage_num + 1}"

        next_plan = (
            self.db.query(ProjectStageResourcePlan)
            .filter(
                ProjectStageResourcePlan.project_id == plan.project_id,
                ProjectStageResourcePlan.stage_code == next_stage,
            )
            .first()
        )

        if next_plan and next_plan.planned_start:
            gap = (next_plan.planned_start - plan.planned_end).days
            if delay_days > gap:
                return f"延期 {delay_days} 天将影响后续 {next_stage} 阶段（当前间隔仅 {gap} 天），需同步调整"
            else:
                return f"延期 {delay_days} 天在可接受范围内（与 {next_stage} 间隔 {gap} 天）"

        return f"延期 {delay_days} 天，该阶段后无直接后续依赖"

    # ==================== 3. 负荷均衡建议 ====================

    def _recommend_workload_balancing(
        self,
        conflict: ResourceConflictModel,
        plan_a: ProjectStageResourcePlan,
        plan_b: ProjectStageResourcePlan,
    ) -> List[Dict[str, Any]]:
        """
        推荐负荷均衡方案：
        - 分析冲突员工的全部分配
        - 找出可转移的工作量
        - 推荐具体的重分配方案
        """
        if not plan_a or not plan_b:
            return []

        employee_id = conflict.employee_id
        employee = self.db.query(User).filter(User.id == employee_id).first()
        employee_name = employee.username if employee else "该员工"

        # 获取员工在冲突期间的所有分配
        all_assignments = (
            self.db.query(ProjectStageResourcePlan)
            .filter(
                ProjectStageResourcePlan.assigned_employee_id == employee_id,
                ProjectStageResourcePlan.assignment_status == "ASSIGNED",
                ProjectStageResourcePlan.planned_end >= conflict.overlap_start,
                ProjectStageResourcePlan.planned_start <= conflict.overlap_end,
            )
            .all()
        )

        total_alloc = sum(float(a.allocation_pct or 100) for a in all_assignments)
        over = total_alloc - 100

        if over <= 0:
            return []

        suggestions = []

        # 按分配比例从小到大排序，优先转移小的分配
        sorted_assignments = sorted(all_assignments, key=lambda a: float(a.allocation_pct or 100))

        for assignment in sorted_assignments:
            project = self.db.query(Project).filter(Project.id == assignment.project_id).first()
            alloc_pct = float(assignment.allocation_pct or 100)

            # 找这个角色的同组候选人
            replacements = self._find_candidates_for_plan(assignment, employee_id)
            fit_candidates = [c for c in replacements if c["can_fit"]]

            if fit_candidates:
                best = fit_candidates[0]
                suggestions.append({
                    "type": "TRANSFER",
                    "description": (
                        f"将 {employee_name} 在 {project.project_name if project else '项目'} "
                        f"{assignment.stage_code} 的 {alloc_pct:.0f}% 工作转交给 {best['employee_name']}"
                    ),
                    "from_employee": {
                        "id": employee_id,
                        "name": employee_name,
                    },
                    "to_employee": {
                        "id": best["employee_id"],
                        "name": best["employee_name"],
                    },
                    "plan_id": assignment.id,
                    "project_id": assignment.project_id,
                    "project_name": project.project_name if project else None,
                    "stage_code": assignment.stage_code,
                    "transfer_pct": alloc_pct,
                    "relief_effect": f"释放 {employee_name} {alloc_pct:.0f}% 负荷，超额从 {over:.0f}% 降到 {max(0, over - alloc_pct):.0f}%",
                    "reason": f"{best['employee_name']} {best['reason']}",
                })

                over -= alloc_pct
                if over <= 0:
                    break

        # 如果还有剩余超额，建议拆分工作
        if over > 0:
            suggestions.append({
                "type": "SPLIT_WORK",
                "description": (
                    f"建议将 {employee_name} 的部分工作拆分给多人，"
                    f"仍有 {over:.0f}% 超额需要通过调整计划或增加人手解决"
                ),
                "remaining_over_allocation": over,
                "reason": "当前可用替代人选不足以完全消化超额，需要项目经理介入协调",
            })

        return suggestions
