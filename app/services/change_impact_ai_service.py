# -*- coding: utf-8 -*-
"""
变更影响AI分析服务 - 使用GLM-5模型
"""

import json
import logging
import os
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models import (
    ChangeImpactAnalysis,
    ChangeRequest,
    ChangeResponseSuggestion,
    Project,
    ProjectMilestone,
    Task,
    TaskDependency,
)
from app.services.glm_service import call_glm_api

logger = logging.getLogger(__name__)


class ChangeImpactAIService:
    """变更影响AI分析服务"""

    def __init__(self, db: Session):
        self.db = db

    async def analyze_change_impact(
        self, change_request_id: int, user_id: int
    ) -> ChangeImpactAnalysis:
        """
        执行完整的变更影响分析
        
        Args:
            change_request_id: 变更请求ID
            user_id: 分析发起人ID
            
        Returns:
            ChangeImpactAnalysis: 分析结果
        """
        start_time = datetime.now()
        
        # 获取变更请求
        change = self.db.query(ChangeRequest).filter(
            ChangeRequest.id == change_request_id
        ).first()
        
        if not change:
            raise ValueError(f"变更请求 {change_request_id} 不存在")
        
        # 获取项目信息
        project = self.db.query(Project).filter(
            Project.id == change.project_id
        ).first()
        
        if not project:
            raise ValueError(f"项目 {change.project_id} 不存在")
        
        # 创建分析记录
        analysis = ChangeImpactAnalysis(
            change_request_id=change_request_id,
            analysis_status="ANALYZING",
            analysis_started_at=start_time,
            ai_model="GLM-5",
            created_by=user_id
        )
        self.db.add(analysis)
        self.db.flush()
        
        try:
            # 收集分析数据
            context_data = self._gather_analysis_context(change, project)
            
            # 1. 分析进度影响
            schedule_impact = await self._analyze_schedule_impact(
                change, project, context_data
            )
            
            # 2. 分析成本影响
            cost_impact = await self._analyze_cost_impact(
                change, project, context_data
            )
            
            # 3. 分析质量影响
            quality_impact = await self._analyze_quality_impact(
                change, project, context_data
            )
            
            # 4. 分析资源影响
            resource_impact = await self._analyze_resource_impact(
                change, project, context_data
            )
            
            # 5. 识别连锁反应
            chain_reaction = self._identify_chain_reactions(
                change, project, context_data
            )
            
            # 6. 综合风险评估
            overall_risk = self._calculate_overall_risk(
                schedule_impact, cost_impact, quality_impact, 
                resource_impact, chain_reaction
            )
            
            # 更新分析记录
            analysis.analysis_status = "COMPLETED"
            analysis.analysis_completed_at = datetime.now()
            analysis.analysis_duration_ms = int(
                (analysis.analysis_completed_at - start_time).total_seconds() * 1000
            )
            
            # 进度影响
            analysis.schedule_impact_level = schedule_impact.get("level")
            analysis.schedule_delay_days = schedule_impact.get("delay_days", 0)
            analysis.schedule_affected_tasks_count = schedule_impact.get("affected_tasks_count", 0)
            analysis.schedule_critical_path_affected = schedule_impact.get("critical_path_affected", False)
            analysis.schedule_milestone_affected = schedule_impact.get("milestone_affected", False)
            analysis.schedule_impact_description = schedule_impact.get("description")
            analysis.schedule_affected_tasks = schedule_impact.get("affected_tasks", [])
            analysis.schedule_affected_milestones = schedule_impact.get("affected_milestones", [])
            
            # 成本影响
            analysis.cost_impact_level = cost_impact.get("level")
            analysis.cost_impact_amount = Decimal(str(cost_impact.get("amount", 0)))
            analysis.cost_impact_percentage = Decimal(str(cost_impact.get("percentage", 0)))
            analysis.cost_breakdown = cost_impact.get("breakdown", {})
            analysis.cost_impact_description = cost_impact.get("description")
            analysis.cost_budget_exceeded = cost_impact.get("budget_exceeded", False)
            analysis.cost_contingency_required = Decimal(str(cost_impact.get("contingency_required", 0)))
            
            # 质量影响
            analysis.quality_impact_level = quality_impact.get("level")
            analysis.quality_risk_areas = quality_impact.get("risk_areas", [])
            analysis.quality_testing_impact = quality_impact.get("testing_impact")
            analysis.quality_acceptance_impact = quality_impact.get("acceptance_impact")
            analysis.quality_mitigation_required = quality_impact.get("mitigation_required", False)
            analysis.quality_impact_description = quality_impact.get("description")
            
            # 资源影响
            analysis.resource_impact_level = resource_impact.get("level")
            analysis.resource_additional_required = resource_impact.get("additional_required", [])
            analysis.resource_reallocation_needed = resource_impact.get("reallocation_needed", False)
            analysis.resource_conflict_detected = resource_impact.get("conflict_detected", False)
            analysis.resource_impact_description = resource_impact.get("description")
            analysis.resource_affected_allocations = resource_impact.get("affected_allocations", [])
            
            # 连锁反应
            analysis.chain_reaction_detected = chain_reaction.get("detected", False)
            analysis.chain_reaction_depth = chain_reaction.get("depth", 0)
            analysis.chain_reaction_affected_projects = chain_reaction.get("affected_projects", [])
            analysis.dependency_tree = chain_reaction.get("dependency_tree", {})
            analysis.critical_dependencies = chain_reaction.get("critical_dependencies", [])
            
            # 综合风险
            analysis.overall_risk_score = Decimal(str(overall_risk.get("score", 0)))
            analysis.overall_risk_level = overall_risk.get("level")
            analysis.risk_factors = overall_risk.get("factors", [])
            analysis.recommended_action = overall_risk.get("recommended_action")
            analysis.ai_confidence_score = Decimal(str(overall_risk.get("confidence", 80)))
            
            # 分析摘要
            analysis.analysis_summary = overall_risk.get("summary")
            analysis.analysis_details = {
                "schedule": schedule_impact,
                "cost": cost_impact,
                "quality": quality_impact,
                "resource": resource_impact,
                "chain_reaction": chain_reaction,
                "overall": overall_risk
            }
            
            self.db.commit()
            logger.info(f"变更影响分析完成: change_id={change_request_id}, duration={analysis.analysis_duration_ms}ms")
            
            return analysis
            
        except Exception as e:
            analysis.analysis_status = "FAILED"
            analysis.analysis_summary = f"分析失败: {str(e)}"
            self.db.commit()
            logger.error(f"变更影响分析失败: {e}", exc_info=True)
            raise

    def _gather_analysis_context(
        self, change: ChangeRequest, project: Project
    ) -> Dict[str, Any]:
        """收集分析上下文数据"""
        # 获取项目任务
        tasks = self.db.query(Task).filter(
            Task.project_id == project.id
        ).all()
        
        # 获取任务依赖关系
        task_ids = [t.id for t in tasks]
        dependencies = self.db.query(TaskDependency).filter(
            TaskDependency.task_id.in_(task_ids)
        ).all() if task_ids else []
        
        # 获取里程碑
        milestones = self.db.query(ProjectMilestone).filter(
            ProjectMilestone.project_id == project.id
        ).all()
        
        return {
            "change": {
                "id": change.id,
                "code": change.change_code,
                "title": change.title,
                "description": change.description,
                "type": change.change_type.value if change.change_type else None,
                "source": change.change_source.value if change.change_source else None,
                "time_impact": change.time_impact,
                "cost_impact": float(change.cost_impact) if change.cost_impact else 0,
            },
            "project": {
                "id": project.id,
                "code": project.project_code,
                "name": project.project_name,
                "status": project.status,
                "budget": float(project.budget_amount) if project.budget_amount else 0,
                "start_date": project.plan_start.isoformat() if project.plan_start else None,
                "end_date": project.plan_end.isoformat() if project.plan_end else None,
            },
            "tasks": [
                {
                    "id": t.id,
                    "name": t.task_name,
                    "status": t.status,
                    "stage": t.stage,
                    "plan_start": t.plan_start.isoformat() if t.plan_start else None,
                    "plan_end": t.plan_end.isoformat() if t.plan_end else None,
                    "progress": t.progress_percent,
                }
                for t in tasks
            ],
            "dependencies": [
                {
                    "task_id": d.task_id,
                    "depends_on": d.depends_on_task_id,
                    "type": d.dependency_type,
                    "lag_days": d.lag_days,
                }
                for d in dependencies
            ],
            "milestones": [
                {
                    "id": m.id,
                    "name": m.milestone_name,
                    "plan_date": m.plan_date.isoformat() if m.plan_date else None,
                    "status": m.status,
                }
                for m in milestones
            ],
        }

    async def _analyze_schedule_impact(
        self, change: ChangeRequest, project: Project, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """分析进度影响"""
        prompt = f"""
你是一个项目管理专家，请分析以下变更请求对项目进度的影响：

**变更信息：**
- 变更标题：{change.title}
- 变更描述：{change.description}
- 变更类型：{change.change_type.value if change.change_type else '未指定'}
- 预计时间影响：{change.time_impact}天

**项目信息：**
- 项目名称：{project.project_name}
- 项目状态：{project.status}
- 计划开始：{context['project']['start_date']}
- 计划结束：{context['project']['end_date']}

**当前任务：**
共有 {len(context['tasks'])} 个任务，其中：
- 进行中：{len([t for t in context['tasks'] if t['status'] == 'IN_PROGRESS'])}
- 待开始：{len([t for t in context['tasks'] if t['status'] == 'TODO'])}

**请分析：**
1. 影响级别（NONE/LOW/MEDIUM/HIGH/CRITICAL）
2. 预计延期天数
3. 受影响的任务数量
4. 是否影响关键路径
5. 是否影响里程碑
6. 详细影响描述

请以JSON格式返回分析结果。
"""

        try:
            response = await call_glm_api(
                prompt=prompt,
                temperature=0.3,
                max_tokens=1500
            )
            
            # 解析AI响应
            ai_result = self._parse_ai_response(response, {
                "level": "MEDIUM",
                "delay_days": change.time_impact or 0,
                "affected_tasks_count": 0,
                "critical_path_affected": False,
                "milestone_affected": False,
                "description": "AI分析进行中...",
                "affected_tasks": [],
                "affected_milestones": [],
            })
            
            # 补充实际数据分析
            if change.time_impact and change.time_impact > 0:
                # 识别受影响的任务
                affected_tasks = self._find_affected_tasks(context)
                ai_result["affected_tasks"] = affected_tasks
                ai_result["affected_tasks_count"] = len(affected_tasks)
                
                # 识别受影响的里程碑
                affected_milestones = self._find_affected_milestones(context, change.time_impact)
                ai_result["affected_milestones"] = affected_milestones
                ai_result["milestone_affected"] = len(affected_milestones) > 0
            
            return ai_result
            
        except Exception as e:
            logger.error(f"进度影响分析失败: {e}")
            return {
                "level": "MEDIUM",
                "delay_days": change.time_impact or 0,
                "affected_tasks_count": 0,
                "critical_path_affected": False,
                "milestone_affected": False,
                "description": f"分析异常: {str(e)}",
                "affected_tasks": [],
                "affected_milestones": [],
            }

    async def _analyze_cost_impact(
        self, change: ChangeRequest, project: Project, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """分析成本影响"""
        cost_impact_value = float(change.cost_impact) if change.cost_impact else 0
        budget = float(project.budget_amount) if project.budget_amount else 0
        percentage = (cost_impact_value / budget * 100) if budget > 0 else 0
        
        level = "NONE"
        if percentage > 20:
            level = "CRITICAL"
        elif percentage > 10:
            level = "HIGH"
        elif percentage > 5:
            level = "MEDIUM"
        elif percentage > 0:
            level = "LOW"
        
        return {
            "level": level,
            "amount": cost_impact_value,
            "percentage": round(percentage, 2),
            "breakdown": {
                "labor": cost_impact_value * 0.6,
                "material": cost_impact_value * 0.3,
                "outsourcing": cost_impact_value * 0.1,
                "other": 0,
            },
            "description": f"预计成本影响 {cost_impact_value:,.2f} 元，占预算的 {percentage:.1f}%",
            "budget_exceeded": (float(project.actual_cost or 0) + cost_impact_value) > budget,
            "contingency_required": cost_impact_value * 1.2,  # 建议预留20%应急
        }

    async def _analyze_quality_impact(
        self, change: ChangeRequest, project: Project, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """分析质量影响"""
        # 基于变更类型判断质量影响
        change_type = change.change_type.value if change.change_type else "OTHER"
        
        level = "LOW"
        risk_areas = []
        mitigation_required = False
        
        if change_type in ["REQUIREMENT", "DESIGN"]:
            level = "MEDIUM"
            risk_areas = [
                {"area": "功能完整性", "risk_level": "MEDIUM", "description": "需求变更可能影响功能验收"},
                {"area": "测试覆盖", "risk_level": "MEDIUM", "description": "需要增加测试用例"}
            ]
            mitigation_required = True
        elif change_type == "TECHNICAL":
            level = "HIGH"
            risk_areas = [
                {"area": "技术稳定性", "risk_level": "HIGH", "description": "技术变更可能引入新风险"},
                {"area": "集成测试", "risk_level": "MEDIUM", "description": "需要全面回归测试"}
            ]
            mitigation_required = True
        
        return {
            "level": level,
            "risk_areas": risk_areas,
            "testing_impact": "需要增加测试时间和测试用例" if mitigation_required else "测试影响较小",
            "acceptance_impact": "可能影响验收标准" if level in ["HIGH", "CRITICAL"] else "验收影响可控",
            "mitigation_required": mitigation_required,
            "description": f"质量影响级别: {level}, 需要关注 {len(risk_areas)} 个风险领域",
        }

    async def _analyze_resource_impact(
        self, change: ChangeRequest, project: Project, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """分析资源影响"""
        time_impact = change.time_impact or 0
        cost_impact = float(change.cost_impact) if change.cost_impact else 0
        
        level = "NONE"
        additional_required = []
        reallocation_needed = False
        conflict_detected = False
        
        if time_impact > 10 or cost_impact > 50000:
            level = "MEDIUM"
            reallocation_needed = True
            additional_required = [
                {"type": "开发人员", "quantity": 1, "skill_required": "熟悉项目"},
                {"type": "测试人员", "quantity": 1, "skill_required": "质量保证"}
            ]
        
        if time_impact > 20 or cost_impact > 100000:
            level = "HIGH"
            conflict_detected = True
        
        return {
            "level": level,
            "additional_required": additional_required,
            "reallocation_needed": reallocation_needed,
            "conflict_detected": conflict_detected,
            "description": f"资源影响级别: {level}",
            "affected_allocations": [],
        }

    def _identify_chain_reactions(
        self, change: ChangeRequest, project: Project, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """识别连锁反应"""
        dependencies = context.get("dependencies", [])
        tasks = context.get("tasks", [])
        
        if not dependencies:
            return {
                "detected": False,
                "depth": 0,
                "affected_projects": [],
                "dependency_tree": {},
                "critical_dependencies": [],
            }
        
        # 构建依赖图
        dep_graph = {}
        for dep in dependencies:
            task_id = dep["task_id"]
            depends_on = dep["depends_on"]
            if task_id not in dep_graph:
                dep_graph[task_id] = []
            dep_graph[task_id].append(depends_on)
        
        # 计算连锁反应深度
        max_depth = 0
        for task in tasks:
            if task["status"] in ["PENDING", "TODO"]:
                depth = self._calculate_dependency_depth(task["id"], dep_graph)
                max_depth = max(max_depth, depth)
        
        detected = max_depth > 1
        
        return {
            "detected": detected,
            "depth": max_depth,
            "affected_projects": [],
            "dependency_tree": dep_graph,
            "critical_dependencies": [
                dep for dep in dependencies 
                if dep["type"] == "FS"  # Finish-to-Start是最常见的关键依赖
            ][:5],  # 最多返回5个关键依赖
        }

    def _calculate_dependency_depth(
        self, task_id: int, dep_graph: Dict[int, List[int]], visited: Optional[set] = None
    ) -> int:
        """计算依赖深度"""
        if visited is None:
            visited = set()
        
        if task_id in visited:
            return 0
        
        visited.add(task_id)
        
        if task_id not in dep_graph:
            return 1
        
        max_depth = 0
        for dep_id in dep_graph[task_id]:
            depth = self._calculate_dependency_depth(dep_id, dep_graph, visited)
            max_depth = max(max_depth, depth)
        
        return max_depth + 1

    def _calculate_overall_risk(
        self,
        schedule_impact: Dict[str, Any],
        cost_impact: Dict[str, Any],
        quality_impact: Dict[str, Any],
        resource_impact: Dict[str, Any],
        chain_reaction: Dict[str, Any]
    ) -> Dict[str, Any]:
        """计算综合风险"""
        # 影响级别权重
        level_scores = {
            "NONE": 0,
            "LOW": 25,
            "MEDIUM": 50,
            "HIGH": 75,
            "CRITICAL": 100
        }
        
        # 计算加权分数
        weights = {
            "schedule": 0.3,
            "cost": 0.25,
            "quality": 0.25,
            "resource": 0.15,
            "chain_reaction": 0.05,
        }
        
        scores = {
            "schedule": level_scores.get(schedule_impact.get("level", "NONE"), 0),
            "cost": level_scores.get(cost_impact.get("level", "NONE"), 0),
            "quality": level_scores.get(quality_impact.get("level", "NONE"), 0),
            "resource": level_scores.get(resource_impact.get("level", "NONE"), 0),
            "chain_reaction": 50 if chain_reaction.get("detected") else 0,
        }
        
        overall_score = sum(scores[k] * weights[k] for k in weights)
        
        # 确定风险级别
        if overall_score >= 75:
            level = "CRITICAL"
            recommended_action = "ESCALATE"
        elif overall_score >= 50:
            level = "HIGH"
            recommended_action = "MODIFY"
        elif overall_score >= 25:
            level = "MEDIUM"
            recommended_action = "APPROVE"
        else:
            level = "LOW"
            recommended_action = "APPROVE"
        
        # 风险因素
        risk_factors = [
            {"factor": k, "weight": weights[k], "score": scores[k]}
            for k in weights
            if scores[k] > 0
        ]
        
        # 生成摘要
        summary_parts = []
        if schedule_impact.get("delay_days", 0) > 0:
            summary_parts.append(f"进度延期{schedule_impact['delay_days']}天")
        if cost_impact.get("amount", 0) > 0:
            summary_parts.append(f"成本增加{cost_impact['amount']:,.0f}元")
        if quality_impact.get("mitigation_required"):
            summary_parts.append("质量风险需要缓解")
        if chain_reaction.get("detected"):
            summary_parts.append(f"检测到{chain_reaction['depth']}层连锁反应")
        
        summary = f"综合风险等级: {level}。" + "；".join(summary_parts) + f"。建议行动: {recommended_action}。"
        
        return {
            "score": round(overall_score, 2),
            "level": level,
            "recommended_action": recommended_action,
            "factors": risk_factors,
            "summary": summary,
            "confidence": 85,  # AI置信度
        }

    def _find_affected_tasks(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """查找受影响的任务"""
        tasks = context.get("tasks", [])
        # 简化逻辑：返回所有进行中和待开始的任务
        return [
            {
                "task_id": t["id"],
                "task_name": t["name"],
                "impact_type": "DELAY",
                "delay_days": context["change"].get("time_impact", 0),
            }
            for t in tasks
            if t["status"] in ["TODO", "IN_PROGRESS"]
        ][:10]  # 最多返回10个

    def _find_affected_milestones(
        self, context: Dict[str, Any], delay_days: int
    ) -> List[Dict[str, Any]]:
        """查找受影响的里程碑"""
        from datetime import timedelta
        
        milestones = context.get("milestones", [])
        affected = []
        
        for m in milestones:
            if m["plan_date"]:
                from datetime import datetime
                original_date = datetime.fromisoformat(m["plan_date"])
                new_date = original_date + timedelta(days=delay_days)
                affected.append({
                    "milestone_id": m["id"],
                    "name": m["name"],
                    "original_date": m["plan_date"],
                    "new_date": new_date.isoformat(),
                })
        
        return affected

    def _parse_ai_response(
        self, response: str, default: Dict[str, Any]
    ) -> Dict[str, Any]:
        """解析AI响应"""
        try:
            # 尝试提取JSON
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                # 合并默认值
                for key in default:
                    if key not in result:
                        result[key] = default[key]
                return result
        except Exception as e:
            logger.warning(f"AI响应解析失败: {e}")
        
        return default
