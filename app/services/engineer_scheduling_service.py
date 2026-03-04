# -*- coding: utf-8 -*-
"""
工程师智能排产与风险预警服务

功能：
1. 工程师能力模型提取（从历史数据）
2. 任务量分析与预警
3. 项目冲突检测
4. 风险预警与决策支持
"""

from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.engineer_capacity import (
    EngineerCapacity,
    EngineerTaskAssignment,
    WorkloadWarning,
)
from app.models.project import Project
from app.models.user import User


class EngineerSchedulingService:
    """工程师智能排产服务"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== 工程师能力模型提取 ====================

    def extract_engineer_capacity(self, engineer_id: int) -> Dict[str, Any]:
        """
        从历史工作数据提取工程师能力模型

        分析维度：
        1. 同时负责项目数（承载力）
        2. 各阶段工作效率
        3. 质量评分
        4. 按时交付率
        """

        # 1. 查询历史任务分配
        tasks = (
            self.db.query(EngineerTaskAssignment)
            .filter(
                EngineerTaskAssignment.engineer_id == engineer_id,
                EngineerTaskAssignment.status.in_(["COMPLETED", "IN_PROGRESS"]),
            )
            .all()
        )

        if not tasks:
            return self._get_default_capacity(engineer_id)

        # 2. 计算平均同时负责项目数
        project_periods = []
        for task in tasks:
            if task.planned_start_date and task.planned_end_date:
                project_periods.append(
                    {
                        "project_id": task.project_id,
                        "start": task.planned_start_date,
                        "end": task.planned_end_date,
                    }
                )

        # 按月份统计同时负责的项目数
        monthly_projects = defaultdict(set)
        for period in project_periods:
            current = period["start"]
            while current <= period["end"]:
                month_key = current.strftime("%Y-%m")
                monthly_projects[month_key].add(period["project_id"])
                current += timedelta(days=30)

        concurrent_counts = [len(projects) for projects in monthly_projects.values()]
        avg_concurrent = (
            sum(concurrent_counts) / len(concurrent_counts) if concurrent_counts else 1.0
        )
        max_concurrent = max(concurrent_counts) if concurrent_counts else 1

        # 3. 计算工作效率（按任务类型）
        task_type_stats = defaultdict(lambda: {"estimated": 0, "actual": 0, "count": 0})
        for task in tasks:
            if task.estimated_hours > 0 and task.actual_hours > 0:
                task_type_stats[task.task_type]["estimated"] += task.estimated_hours
                task_type_stats[task.task_type]["actual"] += task.actual_hours
                task_type_stats[task.task_type]["count"] += 1

        efficiency = {}
        for task_type, stats in task_type_stats.items():
            if stats["estimated"] > 0:
                # 效率 = 预估/实际，>1 表示比预估快，<1 表示比预估慢
                efficiency[task_type] = round(stats["actual"] / stats["estimated"], 2)

        # 4. 质量评分
        completed_tasks = [t for t in tasks if t.status == "COMPLETED" and t.quality_score]
        avg_quality = (
            sum(t.quality_score for t in completed_tasks) / len(completed_tasks)
            if completed_tasks
            else 5.0
        )

        # 5. 按时交付率
        on_time_count = sum(1 for t in tasks if t.is_on_time)
        on_time_rate = (on_time_count / len(tasks) * 100) if tasks else 100.0

        # 6. 返工率
        rework_count = sum(1 for t in tasks if t.has_rework)
        rework_rate = (rework_count / len(tasks) * 100) if tasks else 0.0

        # 7. 技能标签提取（从任务类型）
        skill_tags = list(set([t.task_type for t in tasks if t.task_type]))

        return {
            "engineer_id": engineer_id,
            "avg_concurrent_projects": round(avg_concurrent, 1),
            "max_concurrent_projects": max_concurrent,
            "efficiency": efficiency,
            "avg_quality_score": round(avg_quality, 1),
            "on_time_delivery_rate": round(on_time_rate, 1),
            "rework_rate": round(rework_rate, 1),
            "skill_tags": skill_tags,
            "total_tasks": len(tasks),
            "completed_tasks": len(completed_tasks),
        }

    def _get_default_capacity(self, engineer_id: int) -> Dict[str, Any]:
        """默认能力模型（无历史数据时）"""
        return {
            "engineer_id": engineer_id,
            "avg_concurrent_projects": 1.0,
            "max_concurrent_projects": 1,
            "efficiency": {},
            "avg_quality_score": 5.0,
            "on_time_delivery_rate": 100.0,
            "rework_rate": 0.0,
            "skill_tags": [],
            "total_tasks": 0,
        }

    def save_or_update_capacity(self, engineer_id: int) -> EngineerCapacity:
        """保存或更新工程师能力模型"""
        capacity_data = self.extract_engineer_capacity(engineer_id)

        engineer = self.db.query(User).filter(User.id == engineer_id).first()
        if not engineer:
            raise ValueError(f"工程师 {engineer_id} 不存在")

        # 查询现有记录
        capacity = (
            self.db.query(EngineerCapacity)
            .filter(EngineerCapacity.engineer_id == engineer_id)
            .first()
        )

        if capacity:
            # 更新
            capacity.avg_concurrent_projects = capacity_data["avg_concurrent_projects"]
            capacity.max_concurrent_projects = capacity_data["max_concurrent_projects"]
            capacity.avg_quality_score = capacity_data["avg_quality_score"]
            capacity.on_time_delivery_rate = capacity_data["on_time_delivery_rate"]
            capacity.rework_rate = capacity_data["rework_rate"]
            capacity.skill_tags = str(capacity_data["skill_tags"])
            capacity.last_evaluation_date = date.today()
        else:
            # 新建
            capacity = EngineerCapacity(
                engineer_id=engineer_id,
                engineer_name=engineer.real_name or engineer.username,
                department_id=engineer.department_id,
                avg_concurrent_projects=capacity_data["avg_concurrent_projects"],
                max_concurrent_projects=capacity_data["max_concurrent_projects"],
                avg_quality_score=capacity_data["avg_quality_score"],
                on_time_delivery_rate=capacity_data["on_time_delivery_rate"],
                rework_rate=capacity_data["rework_rate"],
                skill_tags=str(capacity_data["skill_tags"]),
                last_evaluation_date=date.today(),
            )
            self.db.add(capacity)

        self.db.commit()
        self.db.refresh(capacity)

        return capacity

    # ==================== 任务量分析与预警 ====================

    def analyze_engineer_workload(
        self,
        engineer_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        分析工程师任务量

        返回：
        - 当前任务数
        - 总工时
        - 负载状态（过载/正常/空闲）
        - 预警级别
        """
        if not start_date:
            start_date = date.today()
        if not end_date:
            end_date = start_date + timedelta(days=30)

        # 查询时间段内的任务
        tasks = (
            self.db.query(EngineerTaskAssignment)
            .filter(
                EngineerTaskAssignment.engineer_id == engineer_id,
                EngineerTaskAssignment.status.in_(["PENDING", "IN_PROGRESS"]),
                EngineerTaskAssignment.planned_start_date <= end_date,
                EngineerTaskAssignment.planned_end_date >= start_date,
            )
            .all()
        )

        # 获取能力模型
        capacity = (
            self.db.query(EngineerCapacity)
            .filter(EngineerCapacity.engineer_id == engineer_id)
            .first()
        )

        # 使用真实的多项目并行能力
        max_concurrent = (
            capacity.multi_project_capacity
            if capacity and capacity.multi_project_capacity > 0
            else 1
        )
        multi_project_efficiency = capacity.multi_project_efficiency if capacity else 1.0
        context_switch_cost = capacity.context_switch_cost if capacity else 0.2

        base_available_hours = capacity.available_hours_per_week if capacity else 40.0

        # 考虑 AI 效率提升
        ai_boost = (
            capacity.ai_efficiency_boost if capacity and capacity.ai_efficiency_boost > 1.0 else 1.0
        )

        # 考虑多项目效率（多项目时效率会打折扣）
        if unique_projects > 1:
            project_efficiency = multi_project_efficiency * (
                1 - context_switch_cost * (unique_projects - 1)
            )
            project_efficiency = max(0.5, project_efficiency)  # 最低 50% 效率
        else:
            project_efficiency = 1.0

        available_hours = base_available_hours * ai_boost * project_efficiency

        # 计算任务量
        total_tasks = len(tasks)
        total_hours = sum(t.estimated_hours or 0 for t in tasks)
        unique_projects = len(set(t.project_id for t in tasks))

        # 按周统计工时
        weekly_hours = defaultdict(float)
        for task in tasks:
            if task.planned_start_date and task.planned_end_date and task.estimated_hours:
                weeks = (task.planned_end_date - task.planned_start_date).days / 7
                if weeks > 0:
                    hours_per_week = task.estimated_hours / weeks
                    current = task.planned_start_date
                    while current <= task.planned_end_date:
                        week_key = current.strftime("%Y-W%W")
                        weekly_hours[week_key] += hours_per_week
                        current += timedelta(days=7)

        # 判断负载状态
        max_weekly_hours = max(weekly_hours.values()) if weekly_hours else 0
        workload_ratio = max_weekly_hours / available_hours if available_hours > 0 else 0

        if workload_ratio > 1.5:
            workload_status = "OVERLOAD"
            warning_level = "HIGH"
        elif workload_ratio > 1.2:
            workload_status = "OVERLOAD"
            warning_level = "MEDIUM"
        elif workload_ratio > 1.0:
            workload_status = "BUSY"
            warning_level = "LOW"
        elif workload_ratio < 0.5:
            workload_status = "IDLE"
            warning_level = "LOW"
        else:
            workload_status = "NORMAL"
            warning_level = None

        return {
            "engineer_id": engineer_id,
            "analysis_period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "total_tasks": total_tasks,
            "total_hours": total_hours,
            "unique_projects": unique_projects,
            "max_concurrent_projects": max_concurrent,
            "available_hours_per_week": available_hours,
            "max_weekly_hours": round(max_weekly_hours, 1),
            "workload_ratio": round(workload_ratio, 2),
            "workload_status": workload_status,
            "warning_level": warning_level,
            "weekly_breakdown": dict(weekly_hours),
        }

    # ==================== 项目冲突检测 ====================

    def detect_task_conflicts(
        self,
        engineer_id: int,
        new_task: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        检测新任务与现有任务的冲突

        Args:
            engineer_id: 工程师 ID
            new_task: 新任务信息 {project_id, task_type, planned_start_date, planned_end_date}

        Returns:
            冲突列表
        """

        new_start = new_task.get("planned_start_date")
        new_end = new_task.get("planned_end_date")

        if not new_start or not new_end:
            return []

        # 查询同一时间段内的现有任务
        existing_tasks = (
            self.db.query(EngineerTaskAssignment)
            .filter(
                EngineerTaskAssignment.engineer_id == engineer_id,
                EngineerTaskAssignment.status.in_(["PENDING", "IN_PROGRESS"]),
                EngineerTaskAssignment.planned_start_date <= new_end,
                EngineerTaskAssignment.planned_end_date >= new_start,
                EngineerTaskAssignment.id != new_task.get("id"),  # 排除自己
            )
            .all()
        )

        conflicts = []
        for task in existing_tasks:
            # 检查是否同一项目（同一项目不视为冲突）
            if task.project_id == new_task.get("project_id"):
                continue

            # 计算重叠天数
            overlap_start = max(new_start, task.planned_start_date)
            overlap_end = min(new_end, task.planned_end_date)
            overlap_days = (overlap_end - overlap_start).days + 1

            if overlap_days > 0:
                conflicts.append(
                    {
                        "conflict_task_id": task.id,
                        "conflict_task_no": task.assignment_no,
                        "conflict_project_id": task.project_id,
                        "conflict_task_type": task.task_type,
                        "overlap_days": overlap_days,
                        "overlap_start": overlap_start.isoformat(),
                        "overlap_end": overlap_end.isoformat(),
                        "severity": (
                            "HIGH" if overlap_days > 7 else "MEDIUM" if overlap_days > 3 else "LOW"
                        ),
                        "suggestion": f"建议调整时间或分配给其他工程师，重叠{overlap_days}天",
                    }
                )

        return conflicts

    # ==================== 风险预警生成 ====================

    def generate_workload_warnings(
        self,
        engineer_id: Optional[int] = None,
        project_id: Optional[int] = None,
        department_id: Optional[int] = None,
    ) -> List[WorkloadWarning]:
        """
        生成工作量预警

        可针对：
        - 个人（工程师）
        - 项目
        - 部门
        """
        warnings = []

        # 1. 工程师过载预警
        if engineer_id:
            workload = self.analyze_engineer_workload(engineer_id)

            if workload["warning_level"] in ["HIGH", "MEDIUM"]:
                engineer = self.db.query(User).filter(User.id == engineer_id).first()

                warning = WorkloadWarning(
                    warning_no=self._generate_warning_no(),
                    engineer_id=engineer_id,
                    warning_type="OVERLOAD",
                    warning_level=workload["warning_level"],
                    title=f"{engineer.real_name or engineer.username} 工作负载预警",
                    description=f"当前负责{workload['total_tasks']}个任务，总工时{workload['total_hours']}小时",
                    impact=f"周最大工时{workload['max_weekly_hours']}小时，超出可用工时{workload['workload_ratio']*100:.0f}%",
                    suggestion="建议：1) 重新分配部分任务 2) 调整项目排期 3) 增加人力",
                    data_snapshot=str(workload),
                )
                warnings.append(warning)
                self.db.add(warning)

        # 2. 项目冲突预警
        if project_id:
            # 查询项目相关的所有任务分配
            project_tasks = (
                self.db.query(EngineerTaskAssignment)
                .filter(
                    EngineerTaskAssignment.project_id == project_id,
                    EngineerTaskAssignment.status.in_(["PENDING", "IN_PROGRESS"]),
                )
                .all()
            )

            # 检查每个工程师的冲突
            engineer_conflicts = defaultdict(list)
            for task in project_tasks:
                conflicts = self.detect_task_conflicts(
                    task.engineer_id,
                    {
                        "id": task.id,
                        "project_id": task.project_id,
                        "planned_start_date": task.planned_start_date,
                        "planned_end_date": task.planned_end_date,
                    },
                )
                if conflicts:
                    engineer_conflicts[task.engineer_id].extend(conflicts)

            for eng_id, conflicts in engineer_conflicts.items():
                engineer = self.db.query(User).filter(User.id == eng_id).first()
                warning = WorkloadWarning(
                    warning_no=self._generate_warning_no(),
                    engineer_id=eng_id,
                    project_id=project_id,
                    warning_type="CONFLICT",
                    warning_level=(
                        "HIGH" if any(c["severity"] == "HIGH" for c in conflicts) else "MEDIUM"
                    ),
                    title=f"{engineer.real_name or engineer.username} 项目任务冲突",
                    description=f"发现{len(conflicts)}个任务时间冲突",
                    impact="可能影响项目进度和质量",
                    suggestion="建议：1) 调整任务时间 2) 分配给其他工程师 3) 延长工期",
                    data_snapshot=str(conflicts),
                )
                warnings.append(warning)
                self.db.add(warning)

        self.db.commit()

        return warnings

    def _generate_warning_no(self) -> str:
        """生成预警单号"""
        from datetime import datetime

        return f"WL{datetime.now().strftime('%Y%m%d%H%M%S')}"

    # ==================== 决策支持报告 ====================

    def generate_scheduling_report(
        self,
        project_id: int,
    ) -> Dict[str, Any]:
        """
        生成项目排产决策支持报告

        包含：
        - 项目任务总览
        - 工程师负载分析
        - 冲突风险提示
        - 排产建议
        """

        # 1. 项目信息
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return {"error": "项目不存在"}

        # 2. 项目相关任务
        project_tasks = (
            self.db.query(EngineerTaskAssignment)
            .filter(
                EngineerTaskAssignment.project_id == project_id,
                EngineerTaskAssignment.status.in_(["PENDING", "IN_PROGRESS"]),
            )
            .all()
        )

        # 3. 按工程师分组
        engineer_tasks = defaultdict(list)
        for task in project_tasks:
            engineer_tasks[task.engineer_id].append(task)

        # 4. 分析每个工程师的负载
        engineer_analysis = {}
        total_conflicts = 0

        for eng_id, tasks in engineer_tasks.items():
            engineer = self.db.query(User).filter(User.id == eng_id).first()
            workload = self.analyze_engineer_workload(eng_id)

            # 检测冲突
            conflicts = []
            for task in tasks:
                task_conflicts = self.detect_task_conflicts(
                    eng_id,
                    {
                        "id": task.id,
                        "project_id": task.project_id,
                        "planned_start_date": task.planned_start_date,
                        "planned_end_date": task.planned_end_date,
                    },
                )
                conflicts.extend(task_conflicts)

            total_conflicts += len(conflicts)

            engineer_analysis[eng_id] = {
                "engineer_name": engineer.real_name or engineer.username,
                "task_count": len(tasks),
                "total_hours": sum(t.estimated_hours or 0 for t in tasks),
                "workload_status": workload["workload_status"],
                "warning_level": workload["warning_level"],
                "conflicts": conflicts,
            }

        # 5. 生成建议
        suggestions = []

        if total_conflicts > 0:
            suggestions.append(f"⚠️ 发现{total_conflicts}个任务冲突，建议调整排期")

        overloaded = [
            eng for eng, data in engineer_analysis.items() if data["workload_status"] == "OVERLOAD"
        ]
        if overloaded:
            suggestions.append(f"⚠️ {len(overloaded)}名工程师过载，建议重新分配任务")

        idle = [eng for eng, data in engineer_analysis.items() if data["workload_status"] == "IDLE"]
        if idle:
            suggestions.append(f"💡 {len(idle)}名工程师工作量不饱和，可分配更多任务")

        return {
            "project_id": project_id,
            "project_name": project.project_name,
            "total_tasks": len(project_tasks),
            "total_engineers": len(engineer_tasks),
            "total_conflicts": total_conflicts,
            "engineer_analysis": engineer_analysis,
            "suggestions": suggestions,
            "generated_at": datetime.now().isoformat(),
        }

    # ==================== AI 能力评估 ====================

    def evaluate_ai_capability(self, engineer_id: int) -> Dict[str, Any]:
        """
        评估工程师的 AI 使用能力

        评估维度：
        1. AI 工具使用频率
        2. AI 代码/方案采纳率
        3. AI 带来的效率提升
        4. AI 学习能力

        等级划分：
        - NONE: 从不使用 AI
        - BASIC: 偶尔使用，基础功能
        - INTERMEDIATE: 经常使用，能提效 30-50%
        - ADVANCED: 深度使用，能提效 50-100%
        - EXPERT: AI 专家，能提效 100%+ 并指导他人
        """

        # 1. 查询历史任务数据
        tasks = (
            self.db.query(EngineerTaskAssignment)
            .filter(
                EngineerTaskAssignment.engineer_id == engineer_id,
                EngineerTaskAssignment.status == "COMPLETED",
                EngineerTaskAssignment.actual_hours > 0,
                EngineerTaskAssignment.estimated_hours > 0,
            )
            .all()
        )

        if not tasks:
            return self._get_default_ai_capability(engineer_id)

        # 2. 分析 AI 使用情况（从任务备注/工具使用记录中提取）
        # 这里假设有 AI 使用记录表，实际项目中需要创建 ai_usage_logs 表
        ai_usage_stats = self._analyze_ai_usage(engineer_id, tasks)

        # 3. 计算效率提升
        efficiency_boost = ai_usage_stats.get("efficiency_boost", 1.0)

        # 4. AI 代码采纳率
        ai_acceptance_rate = ai_usage_stats.get("acceptance_rate", 0.0)

        # 5. 每周节省工时
        saved_hours_per_week = ai_usage_stats.get("saved_hours", 0.0)

        # 6. AI 学习能力（从使用频率增长判断）
        learning_score = self._calculate_ai_learning_score(engineer_id)

        # 7. 综合评定等级
        ai_skill_level = self._determine_ai_skill_level(
            efficiency_boost, ai_acceptance_rate, saved_hours_per_week, learning_score
        )

        # 8. 常用 AI 工具
        ai_tools = ai_usage_stats.get("tools_used", [])

        # 9. 使用频率
        usage_frequency = self._determine_usage_frequency(ai_usage_stats)

        return {
            "engineer_id": engineer_id,
            "ai_skill_level": ai_skill_level,
            "ai_tools": ai_tools,
            "ai_usage_frequency": usage_frequency,
            "ai_efficiency_boost": round(efficiency_boost, 2),
            "ai_code_acceptance_rate": round(ai_acceptance_rate, 1),
            "ai_saved_hours": round(saved_hours_per_week, 1),
            "ai_learning_score": round(learning_score, 1),
            "analysis_details": ai_usage_stats,
        }

    def _analyze_ai_usage(self, engineer_id: int, tasks: list) -> Dict[str, Any]:
        """
        分析 AI 使用情况

        实际项目中需要：
        1. 创建 ai_usage_logs 表记录 AI 使用情况
        2. 集成 IDE 插件自动记录
        3. 或手动填写 AI 使用日志
        """
        # TODO: 实现 AI 使用日志分析
        # 这里先返回示例数据
        return {
            "efficiency_boost": 1.3,  # 效率提升 30%
            "acceptance_rate": 65.0,  # AI 代码采纳率 65%
            "saved_hours": 5.0,  # 每周节省 5 小时
            "tools_used": ["GitHub Copilot", "ChatGPT"],
            "usage_count": 45,  # 使用次数
            "last_usage_date": "2026-02-28",
        }

    def _calculate_ai_learning_score(self, engineer_id: int) -> float:
        """
        计算 AI 学习能力评分（1-10 分）

        考虑因素：
        1. AI 工具使用种类增长
        2. 使用频率增长
        3. 效率提升趋势
        """
        # TODO: 实现学习能力计算
        return 7.5  # 示例数据

    def _determine_ai_skill_level(
        self,
        efficiency_boost: float,
        acceptance_rate: float,
        saved_hours: float,
        learning_score: float,
    ) -> str:
        """
        确定 AI 技能等级

        标准：
        - EXPERT: 效率提升>100%, 采纳率>80%, 节省>10 小时/周
        - ADVANCED: 效率提升>50%, 采纳率>60%, 节省>5 小时/周
        - INTERMEDIATE: 效率提升>30%, 采纳率>40%, 节省>2 小时/周
        - BASIC: 效率提升>10%, 采纳率>20%
        - NONE: 不使用 AI
        """
        if efficiency_boost >= 2.0 and acceptance_rate >= 80 and saved_hours >= 10:
            return "EXPERT"
        elif efficiency_boost >= 1.5 and acceptance_rate >= 60 and saved_hours >= 5:
            return "ADVANCED"
        elif efficiency_boost >= 1.3 and acceptance_rate >= 40 and saved_hours >= 2:
            return "INTERMEDIATE"
        elif efficiency_boost >= 1.1 and acceptance_rate >= 20:
            return "BASIC"
        else:
            return "NONE"

    def _determine_usage_frequency(self, ai_usage_stats: dict) -> str:
        """确定使用频率"""
        usage_count = ai_usage_stats.get("usage_count", 0)

        if usage_count >= 20:  # 每天使用
            return "DAILY"
        elif usage_count >= 10:  # 经常使用
            return "OFTEN"
        elif usage_count >= 5:  # 有时使用
            return "SOMETIMES"
        elif usage_count >= 1:  # 偶尔使用
            return "RARELY"
        else:
            return "NEVER"

    def _get_default_ai_capability(self, engineer_id: int) -> Dict[str, Any]:
        """默认 AI 能力（无数据时）"""
        return {
            "engineer_id": engineer_id,
            "ai_skill_level": "NONE",
            "ai_tools": [],
            "ai_usage_frequency": "NEVER",
            "ai_efficiency_boost": 1.0,
            "ai_code_acceptance_rate": 0.0,
            "ai_saved_hours": 0.0,
            "ai_learning_score": 0.0,
        }

    def save_ai_capability(self, engineer_id: int) -> EngineerCapacity:
        """保存 AI 能力评估结果"""
        ai_capability = self.evaluate_ai_capability(engineer_id)

        capacity = (
            self.db.query(EngineerCapacity)
            .filter(EngineerCapacity.engineer_id == engineer_id)
            .first()
        )

        if not capacity:
            # 先创建能力模型
            capacity = self.save_or_update_capacity(engineer_id)

        # 更新 AI 能力字段
        capacity.ai_skill_level = ai_capability["ai_skill_level"]
        capacity.ai_tools = str(ai_capability["ai_tools"])
        capacity.ai_usage_frequency = ai_capability["ai_usage_frequency"]
        capacity.ai_efficiency_boost = ai_capability["ai_efficiency_boost"]
        capacity.ai_code_acceptance_rate = ai_capability["ai_code_acceptance_rate"]
        capacity.ai_saved_hours = ai_capability["ai_saved_hours"]
        capacity.ai_learning_score = ai_capability["ai_learning_score"]

        self.db.commit()
        self.db.refresh(capacity)

        return capacity

    # ==================== 核心能力评估 ====================

    def evaluate_core_capabilities(self, engineer_id: int) -> Dict[str, Any]:
        """
        评估工程师的核心能力

        包括：
        1. 多项目并行能力
        2. 标准化/模块化能力
        """
        # 1. 多项目并行能力
        multi_project_cap = self._evaluate_multi_project_capacity(engineer_id)

        # 2. 标准化/模块化能力
        standardization_cap = self._evaluate_standardization_capability(engineer_id)

        return {
            "engineer_id": engineer_id,
            "multi_project_capacity": multi_project_cap,
            "standardization_capability": standardization_cap,
        }

    def _evaluate_multi_project_capacity(self, engineer_id: int) -> Dict[str, Any]:
        """
        评估多项目并行能力

        评估维度：
        1. 历史同时负责项目数
        2. 多项目时的质量保持
        3. 上下文切换效率
        4. 交付准时率
        """
        # 查询历史任务
        tasks = (
            self.db.query(EngineerTaskAssignment)
            .filter(
                EngineerTaskAssignment.engineer_id == engineer_id,
                EngineerTaskAssignment.status == "COMPLETED",
            )
            .all()
        )

        if not tasks:
            return self._get_default_multi_project_capacity()

        # 1. 按月份统计同时负责的项目数
        from collections import defaultdict

        monthly_projects = defaultdict(set)

        for task in tasks:
            if task.planned_start_date and task.planned_end_date:
                current = task.planned_start_date
                while current <= task.planned_end_date:
                    month_key = current.strftime("%Y-%m")
                    monthly_projects[month_key].add(task.project_id)
                    current += timedelta(days=30)

        concurrent_counts = [len(projects) for projects in monthly_projects.values()]

        if not concurrent_counts:
            return self._get_default_multi_project_capacity()

        avg_concurrent = sum(concurrent_counts) / len(concurrent_counts)
        max_concurrent = max(concurrent_counts)

        # 2. 多项目时的质量保持
        single_project_tasks = [
            t
            for t in tasks
            if len(
                monthly_projects.get(
                    t.planned_start_date.strftime("%Y-%m") if t.planned_start_date else "", set()
                )
            )
            <= 1
        ]

        multi_project_tasks = [
            t
            for t in tasks
            if len(
                monthly_projects.get(
                    t.planned_start_date.strftime("%Y-%m") if t.planned_start_date else "", set()
                )
            )
            > 1
        ]

        single_quality = (
            sum(t.quality_score or 5.0 for t in single_project_tasks) / len(single_project_tasks)
            if single_project_tasks
            else 5.0
        )
        multi_quality = (
            sum(t.quality_score or 5.0 for t in multi_project_tasks) / len(multi_project_tasks)
            if multi_project_tasks
            else 5.0
        )

        # 质量保持率 = 多项目质量 / 单项目质量
        quality_retention = multi_quality / single_quality if single_quality > 0 else 1.0

        # 3. 上下文切换效率
        # 计算多项目时的效率损失
        single_on_time = (
            sum(1 for t in single_project_tasks if t.is_on_time) / len(single_project_tasks)
            if single_project_tasks
            else 1.0
        )
        multi_on_time = (
            sum(1 for t in multi_project_tasks if t.is_on_time) / len(multi_project_tasks)
            if multi_project_tasks
            else 1.0
        )

        # 切换成本 = 1 - (多项目准时率 / 单项目准时率)
        context_switch_cost = (
            max(0, 1 - (multi_on_time / single_on_time)) if single_on_time > 0 else 0.2
        )

        # 4. 多项目效率系数
        # >1 表示多任务处理效率高，<1 表示效率低
        multi_project_efficiency = quality_retention * (1 - context_switch_cost)

        # 综合评定
        return {
            "avg_concurrent_projects": round(avg_concurrent, 1),
            "max_concurrent_projects": max_concurrent,
            "multi_project_efficiency": round(multi_project_efficiency, 2),
            "context_switch_cost": round(context_switch_cost, 2),
            "quality_retention": round(quality_retention, 2),
            "single_project_quality": round(single_quality, 1),
            "multi_project_quality": round(multi_quality, 1),
            "single_project_on_time": round(single_on_time * 100, 1),
            "multi_project_on_time": round(multi_on_time * 100, 1),
        }

    def _evaluate_standardization_capability(self, engineer_id: int) -> Dict[str, Any]:
        """
        评估标准化/模块化能力

        评估维度：
        1. 方案复用率
        2. 创建的标准模块数量
        3. 文档质量
        4. 知识分享贡献
        """
        # TODO: 需要从以下数据源获取：
        # 1. 设计文档库 - 统计标准文档数量和质量
        # 2. 模块库 - 统计创建的标准模块
        # 3. 知识库 - 统计分享的经验和模板
        # 4. 任务数据 - 分析是否使用已有方案

        # 这里先返回示例数据
        # 实际项目中需要集成文档管理系统

        return {
            "standardization_score": 7.5,  # 标准化能力 7.5/10
            "modularity_score": 8.0,  # 模块化能力 8.0/10
            "reuse_rate": 65.0,  # 方案复用率 65%
            "standard_modules_created": 12,  # 创建 12 个标准模块
            "documentation_quality": 8.2,  # 文档质量 8.2/10
            "knowledge_sharing_count": 8,  # 知识分享 8 次
            "template_contributions": 5,  # 贡献模板 5 个
        }

    def _get_default_multi_project_capacity(self) -> Dict[str, Any]:
        """默认多项目能力"""
        return {
            "avg_concurrent_projects": 1.0,
            "max_concurrent_projects": 1,
            "multi_project_efficiency": 1.0,
            "context_switch_cost": 0.2,
            "quality_retention": 1.0,
            "single_project_quality": 5.0,
            "multi_project_quality": 5.0,
            "single_project_on_time": 100.0,
            "multi_project_on_time": 100.0,
        }

    def save_core_capabilities(self, engineer_id: int) -> EngineerCapacity:
        """保存核心能力评估结果"""
        core_caps = self.evaluate_core_capabilities(engineer_id)

        capacity = (
            self.db.query(EngineerCapacity)
            .filter(EngineerCapacity.engineer_id == engineer_id)
            .first()
        )

        if not capacity:
            capacity = self.save_or_update_capacity(engineer_id)

        # 更新多项目能力
        multi_proj = core_caps["multi_project_capacity"]
        capacity.multi_project_capacity = multi_proj["max_concurrent_projects"]
        capacity.multi_project_efficiency = multi_proj["multi_project_efficiency"]
        capacity.context_switch_cost = multi_proj["context_switch_cost"]

        # 更新标准化能力
        std_cap = core_caps["standardization_capability"]
        capacity.standardization_score = std_cap["standardization_score"]
        capacity.modularity_score = std_cap["modularity_score"]
        capacity.reuse_rate = std_cap["reuse_rate"]
        capacity.standard_modules_created = std_cap["standard_modules_created"]
        capacity.documentation_quality = std_cap["documentation_quality"]

        self.db.commit()
        self.db.refresh(capacity)

        return capacity
