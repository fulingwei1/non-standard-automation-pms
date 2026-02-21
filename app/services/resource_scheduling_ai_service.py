# -*- coding: utf-8 -*-
"""
资源调度AI服务 - 基于GLM-5
"""

import json
import os
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.models.resource_scheduling import (
    ResourceConflictDetection,
    ResourceDemandForecast,
    ResourceSchedulingSuggestion,
    ResourceUtilizationAnalysis,
)
from app.models.project.core import Project
from app.models.user import User
from app.services.ai_client_service import AIClientService
from app.utils.db_helpers import save_obj


class ResourceSchedulingAIService:
    """资源调度AI服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.ai_client = AIClientService()
    
    # ========================================================================
    # 1. 资源冲突检测
    # ========================================================================
    
    def detect_resource_conflicts(
        self,
        resource_id: Optional[int] = None,
        resource_type: str = "PERSON",
        project_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[ResourceConflictDetection]:
        """
        检测资源冲突
        
        检测逻辑：
        1. 查询资源的所有分配记录
        2. 检测时间重叠
        3. 计算总分配比例
        4. 判断是否超负荷（>100%）
        5. AI评估严重程度
        """
        from app.models.pmo.resource_closure import PmoResourceAllocation as PMOResourceAllocation
        
        # 查询分配记录
        query = self.db.query(PMOResourceAllocation)
        
        if resource_id:
            query = query.filter(PMOResourceAllocation.resource_id == resource_id)
        
        if project_id:
            query = query.filter(PMOResourceAllocation.project_id == project_id)
        
        if start_date and end_date:
            query = query.filter(
                or_(
                    and_(
                        PMOResourceAllocation.start_date <= end_date,
                        PMOResourceAllocation.end_date >= start_date,
                    ),
                    and_(
                        PMOResourceAllocation.start_date >= start_date,
                        PMOResourceAllocation.start_date <= end_date,
                    ),
                )
            )
        
        allocations = query.filter(PMOResourceAllocation.status == "PLANNED").all()
        
        # 按资源分组
        resource_allocations = {}
        for alloc in allocations:
            rid = alloc.resource_id
            if rid not in resource_allocations:
                resource_allocations[rid] = []
            resource_allocations[rid].append(alloc)
        
        # 检测冲突
        conflicts = []
        for rid, allocs in resource_allocations.items():
            # 两两比较
            for i in range(len(allocs)):
                for j in range(i + 1, len(allocs)):
                    alloc_a = allocs[i]
                    alloc_b = allocs[j]
                    
                    # 计算重叠
                    overlap_start = max(alloc_a.start_date, alloc_b.start_date)
                    overlap_end = min(alloc_a.end_date, alloc_b.end_date)
                    
                    if overlap_start <= overlap_end:
                        # 有重叠
                        total_allocation = (alloc_a.allocation_percent or 0) + (alloc_b.allocation_percent or 0)
                        
                        if total_allocation > 100:
                            # 发现冲突
                            conflict = self._create_conflict_record(
                                resource_id=rid,
                                resource_type=resource_type,
                                alloc_a=alloc_a,
                                alloc_b=alloc_b,
                                overlap_start=overlap_start,
                                overlap_end=overlap_end,
                                total_allocation=total_allocation,
                            )
                            conflicts.append(conflict)
        
        return conflicts
    
    def _create_conflict_record(
        self,
        resource_id: int,
        resource_type: str,
        alloc_a: Any,
        alloc_b: Any,
        overlap_start: date,
        overlap_end: date,
        total_allocation: Decimal,
    ) -> ResourceConflictDetection:
        """创建冲突记录"""
        
        # 获取项目信息
        project_a = self.db.query(Project).filter(Project.id == alloc_a.project_id).first()
        project_b = self.db.query(Project).filter(Project.id == alloc_b.project_id).first()
        
        # 计算冲突天数
        overlap_days = (overlap_end - overlap_start).days + 1
        
        # 计算过度分配
        over_allocation = total_allocation - 100
        
        # 确定严重程度
        severity = self._calculate_severity(over_allocation, overlap_days)
        
        # 生成冲突编码
        conflict_code = f"RC-{resource_id}-{overlap_start.strftime('%Y%m%d')}-{overlap_end.strftime('%Y%m%d')}"
        
        # AI风险评估
        ai_risk_factors, ai_impact_analysis, ai_confidence = self._ai_assess_conflict(
            resource_id=resource_id,
            project_a=project_a,
            project_b=project_b,
            over_allocation=over_allocation,
            overlap_days=overlap_days,
        )
        
        conflict = ResourceConflictDetection(
            conflict_type="PERSON",
            conflict_code=conflict_code,
            conflict_name=f"{alloc_a.resource_name} - 资源冲突",
            
            resource_id=resource_id,
            resource_type=resource_type,
            resource_name=alloc_a.resource_name,
            department_name=alloc_a.resource_dept,
            
            project_a_id=alloc_a.project_id,
            project_a_code=project_a.project_code if project_a else None,
            project_a_name=project_a.project_name if project_a else None,
            allocation_a_id=alloc_a.id,
            allocation_a_percent=alloc_a.allocation_percent,
            start_date_a=alloc_a.start_date,
            end_date_a=alloc_a.end_date,
            
            project_b_id=alloc_b.project_id,
            project_b_code=project_b.project_code if project_b else None,
            project_b_name=project_b.project_name if project_b else None,
            allocation_b_id=alloc_b.id,
            allocation_b_percent=alloc_b.allocation_percent,
            start_date_b=alloc_b.start_date,
            end_date_b=alloc_b.end_date,
            
            overlap_start=overlap_start,
            overlap_end=overlap_end,
            overlap_days=overlap_days,
            
            total_allocation=total_allocation,
            over_allocation=over_allocation,
            severity=severity,
            priority_score=self._calculate_priority_score(severity, overlap_days),
            
            planned_hours_a=alloc_a.planned_hours,
            planned_hours_b=alloc_b.planned_hours,
            total_planned_hours=(alloc_a.planned_hours or 0) + (alloc_b.planned_hours or 0),
            
            detected_by="AI",
            ai_confidence=ai_confidence,
            ai_risk_factors=json.dumps(ai_risk_factors, ensure_ascii=False),
            ai_impact_analysis=json.dumps(ai_impact_analysis, ensure_ascii=False),
            
            status="DETECTED",
            is_resolved=False,
        )
        
        save_obj(self.db, conflict)
        
        return conflict
    
    def _calculate_severity(self, over_allocation: Decimal, overlap_days: int) -> str:
        """计算严重程度"""
        
        if over_allocation >= 50 or overlap_days >= 30:
            return "CRITICAL"
        elif over_allocation >= 30 or overlap_days >= 14:
            return "HIGH"
        elif over_allocation >= 10 or overlap_days >= 7:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _calculate_priority_score(self, severity: str, overlap_days: int) -> int:
        """计算优先级评分"""
        
        base_score = {
            "LOW": 30,
            "MEDIUM": 50,
            "HIGH": 75,
            "CRITICAL": 95,
        }.get(severity, 50)
        
        # 时间越长，优先级越高
        time_bonus = min(overlap_days, 30)
        
        return min(base_score + time_bonus, 100)
    
    def _ai_assess_conflict(
        self,
        resource_id: int,
        project_a: Optional[Project],
        project_b: Optional[Project],
        over_allocation: Decimal,
        overlap_days: int,
    ) -> Tuple[List[str], Dict[str, Any], Decimal]:
        """AI评估冲突风险和影响"""
        
        prompt = f"""
作为项目管理资源调度专家，分析以下资源冲突：

## 冲突概况
- 资源ID: {resource_id}
- 项目A: {project_a.project_name if project_a else '未知'}
- 项目B: {project_b.project_name if project_b else '未知'}
- 过度分配: {over_allocation}%
- 冲突天数: {overlap_days}天

## 任务
1. 识别主要风险因素（3-5个关键点）
2. 分析对项目的潜在影响（进度、质量、成本）
3. 给出置信度评估（0-1）

以JSON格式输出：
{{
    "risk_factors": ["风险1", "风险2", "风险3"],
    "impact_analysis": {{
        "schedule_impact": "影响描述",
        "quality_impact": "影响描述",
        "cost_impact": "影响描述",
        "team_impact": "影响描述"
    }},
    "confidence": 0.85
}}
"""
        
        try:
            response = self.ai_client.generate_solution(
                prompt=prompt,
                model="glm-5",
                temperature=0.3,
                max_tokens=800,
            )
            
            result = json.loads(response.get("content", "{}"))
            
            return (
                result.get("risk_factors", ["资源超负荷", "项目进度风险"]),
                result.get("impact_analysis", {}),
                Decimal(str(result.get("confidence", 0.7))),
            )
        except Exception as e:
            # AI调用失败，返回默认值
            return (
                ["资源超负荷", "项目进度风险", "团队士气影响"],
                {
                    "schedule_impact": "可能导致项目延期",
                    "quality_impact": "质量可能下降",
                    "cost_impact": "可能增加成本",
                },
                Decimal("0.6"),
            )
    
    # ========================================================================
    # 2. AI生成调度方案
    # ========================================================================
    
    def generate_scheduling_suggestions(
        self,
        conflict_id: int,
        max_suggestions: int = 3,
        prefer_minimal_impact: bool = True,
    ) -> List[ResourceSchedulingSuggestion]:
        """
        AI生成多个调度方案
        
        策略类型：
        1. RESCHEDULE - 重新安排时间
        2. REALLOCATE - 调整资源分配比例
        3. HIRE - 招聘新人
        4. OVERTIME - 加班
        5. PRIORITIZE - 优先级调整
        """
        
        conflict = self.db.query(ResourceConflictDetection).filter(
            ResourceConflictDetection.id == conflict_id
        ).first()
        
        if not conflict:
            raise ValueError(f"Conflict {conflict_id} not found")
        
        # 调用AI生成方案
        ai_suggestions = self._ai_generate_solutions(conflict, max_suggestions)
        
        # 保存方案到数据库
        suggestions = []
        for idx, ai_sug in enumerate(ai_suggestions):
            suggestion = self._create_suggestion_record(
                conflict=conflict,
                ai_suggestion=ai_sug,
                rank=idx + 1,
                is_recommended=(idx == 0),  # 第一个方案推荐
            )
            suggestions.append(suggestion)
        
        # 更新冲突记录
        conflict.has_ai_suggestion = True
        conflict.suggested_solution_id = suggestions[0].id if suggestions else None
        conflict.status = "ANALYZING"
        self.db.commit()
        
        return suggestions
    
    def _ai_generate_solutions(
        self,
        conflict: ResourceConflictDetection,
        max_suggestions: int,
    ) -> List[Dict[str, Any]]:
        """AI生成调度方案"""
        
        prompt = f"""
作为资源调度优化专家，为以下冲突生成{max_suggestions}个最优调度方案：

## 冲突详情
- 资源: {conflict.resource_name} ({conflict.department_name})
- 项目A: {conflict.project_a_name} ({conflict.allocation_a_percent}%)
  时间: {conflict.start_date_a} - {conflict.end_date_a}
- 项目B: {conflict.project_b_name} ({conflict.allocation_b_percent}%)
  时间: {conflict.start_date_b} - {conflict.end_date_b}
- 冲突期: {conflict.overlap_start} - {conflict.overlap_end} ({conflict.overlap_days}天)
- 过度分配: {conflict.over_allocation}%
- 严重程度: {conflict.severity}

## 要求
为每个方案提供：
1. 方案类型 (RESCHEDULE/REALLOCATE/HIRE/OVERTIME/PRIORITIZE)
2. 策略名称和描述
3. 具体调整措施
4. 优劣分析
5. 影响评估
6. 执行步骤
7. 各项评分（可行性、影响、成本、风险、效率，0-100分）

以JSON数组格式输出，示例：
[
  {{
    "solution_type": "REALLOCATE",
    "strategy_name": "调整资源分配比例",
    "strategy_description": "将项目B的分配比例降低...",
    "adjustments": {{
      "project_a": {{"action": "KEEP", "allocation_percent": 60}},
      "project_b": {{"action": "REDUCE", "allocation_percent": 40}}
    }},
    "pros": ["最小影响", "快速实施"],
    "cons": ["项目B进度可能放缓"],
    "risks": ["需要项目B负责人同意"],
    "affected_projects": [{{"project_id": {conflict.project_b_id}, "impact": "进度延缓10%"}}],
    "timeline_impact_days": 3,
    "cost_impact": 0,
    "quality_impact": "LOW",
    "execution_steps": ["与项目B PM沟通", "调整资源分配", "更新项目计划"],
    "estimated_duration_days": 2,
    "feasibility_score": 85,
    "impact_score": 25,
    "cost_score": 10,
    "risk_score": 20,
    "efficiency_score": 80,
    "ai_reasoning": "该方案通过降低项目B的资源占用..."
  }}
]
"""
        
        try:
            start_time = datetime.now()
            response = self.ai_client.generate_solution(
                prompt=prompt,
                model="glm-5",
                temperature=0.4,
                max_tokens=4000,
            )
            
            content = response.get("content", "[]")
            suggestions = json.loads(content)
            
            # 记录AI Token消耗（模拟值）
            tokens_used = response.get("tokens_used", len(content) // 2)
            
            for sug in suggestions:
                sug["ai_tokens_used"] = tokens_used // len(suggestions)
                sug["ai_generated_at"] = datetime.now().isoformat()
            
            return suggestions[:max_suggestions]
        
        except Exception as e:
            # AI失败，返回默认方案
            return self._get_default_suggestions(conflict)
    
    def _get_default_suggestions(self, conflict: ResourceConflictDetection) -> List[Dict[str, Any]]:
        """默认调度方案（AI失败时使用）"""
        
        return [
            {
                "solution_type": "REALLOCATE",
                "strategy_name": "调整资源分配比例",
                "strategy_description": "降低一个项目的资源占用",
                "adjustments": {
                    "project_a": {"action": "KEEP", "allocation_percent": conflict.allocation_a_percent},
                    "project_b": {"action": "REDUCE", "allocation_percent": 100 - conflict.allocation_a_percent},
                },
                "pros": ["快速实施", "成本低"],
                "cons": ["影响项目进度"],
                "risks": ["需要沟通"],
                "affected_projects": [{"project_id": conflict.project_b_id, "impact": "轻微"}],
                "timeline_impact_days": 5,
                "cost_impact": 0,
                "quality_impact": "LOW",
                "execution_steps": ["沟通", "调整", "确认"],
                "estimated_duration_days": 2,
                "feasibility_score": 80,
                "impact_score": 30,
                "cost_score": 10,
                "risk_score": 25,
                "efficiency_score": 75,
                "ai_reasoning": "系统默认方案",
            }
        ]
    
    def _create_suggestion_record(
        self,
        conflict: ResourceConflictDetection,
        ai_suggestion: Dict[str, Any],
        rank: int,
        is_recommended: bool,
    ) -> ResourceSchedulingSuggestion:
        """创建方案记录"""
        
        # 生成方案编码
        suggestion_code = f"RS-{conflict.id}-{rank}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # 计算AI综合评分
        ai_score = (
            (ai_suggestion.get("feasibility_score", 70) * 0.3) +
            ((100 - ai_suggestion.get("impact_score", 30)) * 0.2) +
            ((100 - ai_suggestion.get("cost_score", 20)) * 0.2) +
            ((100 - ai_suggestion.get("risk_score", 25)) * 0.15) +
            (ai_suggestion.get("efficiency_score", 75) * 0.15)
        )
        
        suggestion = ResourceSchedulingSuggestion(
            conflict_id=conflict.id,
            suggestion_code=suggestion_code,
            suggestion_name=ai_suggestion.get("strategy_name", f"方案{rank}"),
            
            solution_type=ai_suggestion.get("solution_type", "REALLOCATE"),
            solution_category="AI",
            
            strategy_name=ai_suggestion.get("strategy_name"),
            strategy_description=ai_suggestion.get("strategy_description"),
            
            adjustments=json.dumps(ai_suggestion.get("adjustments", {}), ensure_ascii=False),
            
            ai_score=Decimal(str(ai_score)),
            feasibility_score=Decimal(str(ai_suggestion.get("feasibility_score", 70))),
            impact_score=Decimal(str(ai_suggestion.get("impact_score", 30))),
            cost_score=Decimal(str(ai_suggestion.get("cost_score", 20))),
            risk_score=Decimal(str(ai_suggestion.get("risk_score", 25))),
            efficiency_score=Decimal(str(ai_suggestion.get("efficiency_score", 75))),
            
            pros=json.dumps(ai_suggestion.get("pros", []), ensure_ascii=False),
            cons=json.dumps(ai_suggestion.get("cons", []), ensure_ascii=False),
            risks=json.dumps(ai_suggestion.get("risks", []), ensure_ascii=False),
            
            affected_projects=json.dumps(ai_suggestion.get("affected_projects", []), ensure_ascii=False),
            affected_resources=json.dumps(ai_suggestion.get("affected_resources", []), ensure_ascii=False),
            timeline_impact_days=ai_suggestion.get("timeline_impact_days", 0),
            cost_impact=Decimal(str(ai_suggestion.get("cost_impact", 0))),
            quality_impact=ai_suggestion.get("quality_impact", "LOW"),
            
            execution_steps=json.dumps(ai_suggestion.get("execution_steps", []), ensure_ascii=False),
            estimated_duration_days=ai_suggestion.get("estimated_duration_days", 3),
            prerequisites=json.dumps(ai_suggestion.get("prerequisites", []), ensure_ascii=False),
            
            ai_reasoning=ai_suggestion.get("ai_reasoning"),
            ai_model="GLM-5",
            ai_version="1.0",
            ai_generated_at=datetime.now(),
            ai_tokens_used=ai_suggestion.get("ai_tokens_used", 500),
            
            rank_order=rank,
            is_recommended=is_recommended,
            recommendation_reason="AI综合评分最高" if is_recommended else None,
            
            status="PENDING",
        )
        
        save_obj(self.db, suggestion)
        
        return suggestion
    
    # ========================================================================
    # 3. 资源需求预测
    # ========================================================================
    
    def forecast_resource_demand(
        self,
        forecast_period: str = "3MONTH",
        resource_type: str = "PERSON",
        skill_category: Optional[str] = None,
    ) -> List[ResourceDemandForecast]:
        """
        预测未来资源需求
        
        预测方法：
        1. 历史数据分析
        2. 项目计划分析
        3. AI趋势预测
        """
        
        # 计算预测时间范围
        today = date.today()
        period_map = {
            "1MONTH": 30,
            "3MONTH": 90,
            "6MONTH": 180,
            "1YEAR": 365,
        }
        days = period_map.get(forecast_period, 90)
        forecast_end = today + timedelta(days=days)
        
        # 查询未来项目
        future_projects = self.db.query(Project).filter(
            and_(
                Project.planned_start_date <= forecast_end,
                Project.planned_end_date >= today,
                Project.is_active == True,
            )
        ).all()
        
        # AI预测
        ai_forecast = self._ai_forecast_demand(
            projects=future_projects,
            forecast_period=forecast_period,
            resource_type=resource_type,
            skill_category=skill_category,
        )
        
        # 创建预测记录
        forecast = self._create_forecast_record(
            forecast_start=today,
            forecast_end=forecast_end,
            forecast_period=forecast_period,
            resource_type=resource_type,
            skill_category=skill_category,
            ai_forecast=ai_forecast,
        )
        
        return [forecast]
    
    def _ai_forecast_demand(
        self,
        projects: List[Project],
        forecast_period: str,
        resource_type: str,
        skill_category: Optional[str],
    ) -> Dict[str, Any]:
        """AI预测资源需求"""
        
        # 构建项目摘要
        project_summary = []
        for p in projects[:20]:  # 限制数量
            project_summary.append({
                "name": p.project_name,
                "start": str(p.start_date),
                "end": str(p.end_date),
                "stage": p.stage,
            })
        
        prompt = f"""
作为资源规划专家，预测未来{forecast_period}的资源需求：

## 输入数据
- 资源类型: {resource_type}
- 技能类别: {skill_category or '全部'}
- 项目数量: {len(projects)}
- 主要项目: {json.dumps(project_summary[:10], ensure_ascii=False)}

## 预测任务
1. 预测资源需求量
2. 识别需求峰值
3. 分析技能缺口
4. 提供招聘/培训建议
5. 成本估算

以JSON格式输出：
{{
    "predicted_demand": 15,
    "demand_gap": 3,
    "gap_severity": "SHORTAGE",
    "predicted_total_hours": 5400,
    "predicted_peak_hours": 240,
    "predicted_utilization": 85,
    "driving_projects": [{{"project_id": 1, "impact": "高"}}],
    "recommendations": ["招聘2名高级工程师", "培训3名初级工程师"],
    "hiring_suggestion": {{"role": "高级工程师", "count": 2, "timeline": "1个月内"}},
    "estimated_cost": 150000,
    "risk_level": "MEDIUM",
    "ai_confidence": 0.78
}}
"""
        
        try:
            response = self.ai_client.generate_solution(
                prompt=prompt,
                model="glm-5",
                temperature=0.3,
                max_tokens=2000,
            )
            
            return json.loads(response.get("content", "{}"))
        except Exception:
            return {
                "predicted_demand": 10,
                "demand_gap": 0,
                "gap_severity": "BALANCED",
                "predicted_utilization": 75,
                "ai_confidence": 0.5,
            }
    
    def _create_forecast_record(
        self,
        forecast_start: date,
        forecast_end: date,
        forecast_period: str,
        resource_type: str,
        skill_category: Optional[str],
        ai_forecast: Dict[str, Any],
    ) -> ResourceDemandForecast:
        """创建预测记录"""
        
        forecast_code = f"RF-{forecast_period}-{forecast_start.strftime('%Y%m%d')}"
        
        forecast = ResourceDemandForecast(
            forecast_code=forecast_code,
            forecast_name=f"{forecast_period}资源需求预测",
            forecast_period=forecast_period,
            
            forecast_start_date=forecast_start,
            forecast_end_date=forecast_end,
            
            resource_type=resource_type,
            skill_category=skill_category,
            
            predicted_demand=ai_forecast.get("predicted_demand", 10),
            demand_gap=ai_forecast.get("demand_gap", 0),
            gap_severity=ai_forecast.get("gap_severity", "BALANCED"),
            
            predicted_total_hours=Decimal(str(ai_forecast.get("predicted_total_hours", 0))),
            predicted_peak_hours=Decimal(str(ai_forecast.get("predicted_peak_hours", 0))),
            predicted_utilization=Decimal(str(ai_forecast.get("predicted_utilization", 70))),
            
            driving_projects=json.dumps(ai_forecast.get("driving_projects", []), ensure_ascii=False),
            project_count=len(ai_forecast.get("driving_projects", [])),
            
            ai_model="GLM-5",
            ai_confidence=Decimal(str(ai_forecast.get("ai_confidence", 0.7))),
            
            recommendations=json.dumps(ai_forecast.get("recommendations", []), ensure_ascii=False),
            hiring_suggestion=json.dumps(ai_forecast.get("hiring_suggestion", {}), ensure_ascii=False),
            
            estimated_cost=Decimal(str(ai_forecast.get("estimated_cost", 0))),
            
            risk_level=ai_forecast.get("risk_level", "LOW"),
            
            status="ACTIVE",
        )
        
        save_obj(self.db, forecast)
        
        return forecast
    
    # ========================================================================
    # 4. 资源利用率分析
    # ========================================================================
    
    def analyze_resource_utilization(
        self,
        resource_id: int,
        start_date: date,
        end_date: date,
        analysis_period: str = "WEEKLY",
    ) -> ResourceUtilizationAnalysis:
        """
        分析资源利用率
        
        指标：
        1. 利用率 = 实际工时 / 可用工时
        2. 分配率 = 分配工时 / 可用工时
        3. 效率率 = 实际工时 / 分配工时
        """
        
        from app.models.timesheet import Timesheet
        
        # 查询工时记录
        timesheets = self.db.query(Timesheet).filter(
            and_(
                Timesheet.user_id == resource_id,
                Timesheet.work_date >= start_date,
                Timesheet.work_date <= end_date,
                Timesheet.status == "APPROVED",
            )
        ).all()
        
        # 计算统计数据
        period_days = (end_date - start_date).days + 1
        working_days = period_days * 5 // 7  # 简化：假设5天工作制
        
        total_available_hours = Decimal(str(working_days * 8))  # 8小时/天
        total_actual_hours = sum(Decimal(str(ts.hours)) for ts in timesheets)
        
        utilization_rate = (total_actual_hours / total_available_hours * 100) if total_available_hours > 0 else 0
        
        # AI洞察
        ai_insights = self._ai_analyze_utilization(
            resource_id=resource_id,
            utilization_rate=utilization_rate,
            total_hours=total_actual_hours,
            period_days=period_days,
        )
        
        # 创建分析记录
        analysis_code = f"RU-{resource_id}-{start_date.strftime('%Y%m%d')}"
        
        analysis = ResourceUtilizationAnalysis(
            analysis_code=analysis_code,
            analysis_name=f"资源{resource_id}利用率分析",
            analysis_period=analysis_period,
            
            period_start_date=start_date,
            period_end_date=end_date,
            period_days=period_days,
            
            resource_id=resource_id,
            resource_type="PERSON",
            
            total_available_hours=total_available_hours,
            total_actual_hours=total_actual_hours,
            
            utilization_rate=utilization_rate,
            
            utilization_status=self._determine_utilization_status(utilization_rate),
            is_idle_resource=(utilization_rate < 50),
            is_overloaded=(utilization_rate > 100),
            
            ai_insights=json.dumps(ai_insights, ensure_ascii=False),
        )
        
        save_obj(self.db, analysis)
        
        return analysis
    
    def _determine_utilization_status(self, utilization_rate: Decimal) -> str:
        """确定利用状态"""
        
        if utilization_rate < 50:
            return "UNDERUTILIZED"
        elif utilization_rate <= 90:
            return "NORMAL"
        elif utilization_rate <= 110:
            return "OVERUTILIZED"
        else:
            return "CRITICAL"
    
    def _ai_analyze_utilization(
        self,
        resource_id: int,
        utilization_rate: Decimal,
        total_hours: Decimal,
        period_days: int,
    ) -> Dict[str, Any]:
        """AI分析利用率"""
        
        prompt = f"""
分析资源利用率：

- 资源ID: {resource_id}
- 利用率: {utilization_rate}%
- 总工时: {total_hours}小时
- 分析周期: {period_days}天

提供洞察和建议（JSON格式）：
{{
    "key_insights": ["洞察1", "洞察2"],
    "optimization_suggestions": ["建议1", "建议2"],
    "reallocation_opportunities": []
}}
"""
        
        try:
            response = self.ai_client.generate_solution(
                prompt=prompt,
                model="glm-5",
                temperature=0.3,
                max_tokens=500,
            )
            return json.loads(response.get("content", "{}"))
        except Exception:
            return {
                "key_insights": ["利用率正常"],
                "optimization_suggestions": [],
            }
