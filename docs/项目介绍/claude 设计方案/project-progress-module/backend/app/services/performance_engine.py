"""
绩效报告引擎 (Performance Report Engine)

设计理念：
1. 多维度绩效评估 - 工时、任务、质量、协作
2. 角色权限控制 - 自己看自己、领导看下属、全局看全部
3. 实时计算 - 基于实际数据动态生成
4. 对比分析 - 同比、环比、团队对比

权限矩阵：
┌─────────────┬────────────────────────────────────────────┐
│    角色      │              可查看范围                      │
├─────────────┼────────────────────────────────────────────┤
│ 总经理       │ 全公司所有人绩效 + 部门汇总 + 公司汇总       │
│ 部门经理     │ 本部门所有人绩效 + 部门汇总 + 自己           │
│ 项目经理     │ 项目成员绩效（项目维度）+ 自己               │
│ 组长        │ 本组成员绩效 + 自己                          │
│ 工程师      │ 仅自己的绩效                                 │
└─────────────┴────────────────────────────────────────────┘
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime, date, timedelta
from decimal import Decimal
import json


# ==================== 枚举定义 ====================

class PerformanceViewLevel(Enum):
    """绩效查看权限级别"""
    SELF = "self"                  # 仅自己
    TEAM = "team"                  # 团队/小组
    PROJECT = "project"            # 项目组
    DEPARTMENT = "department"      # 部门
    COMPANY = "company"            # 全公司


class ReportPeriodType(Enum):
    """报告周期类型"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class PerformanceLevel(Enum):
    """绩效等级"""
    EXCELLENT = "excellent"    # 优秀 A
    GOOD = "good"              # 良好 B
    QUALIFIED = "qualified"    # 合格 C
    NEEDS_IMPROVEMENT = "needs_improvement"  # 待改进 D
    UNQUALIFIED = "unqualified"  # 不合格 E


# ==================== 数据结构 ====================

@dataclass
class WorkloadMetrics:
    """工时指标"""
    standard_hours: float        # 标准工时
    actual_hours: float          # 实际工时
    overtime_hours: float        # 加班工时
    billable_hours: float        # 有效工时（可计费）
    utilization_rate: float      # 利用率
    overtime_rate: float         # 加班率
    attendance_rate: float       # 出勤率
    leave_days: float            # 请假天数


@dataclass
class TaskMetrics:
    """任务指标"""
    total_assigned: int          # 分配任务数
    completed: int               # 完成数
    in_progress: int             # 进行中
    overdue: int                 # 逾期数
    completion_rate: float       # 完成率
    on_time_rate: float          # 按时完成率
    avg_completion_days: float   # 平均完成天数
    complexity_weighted_score: float  # 复杂度加权得分


@dataclass
class QualityMetrics:
    """质量指标"""
    first_pass_rate: float       # 一次通过率
    rework_count: int            # 返工次数
    defect_count: int            # 缺陷数
    review_pass_rate: float      # 评审通过率
    customer_satisfaction: float  # 客户满意度（如有）
    documentation_score: float   # 文档完整度


@dataclass
class CollaborationMetrics:
    """协作指标"""
    support_given: int           # 支援他人次数
    support_received: int        # 接受支援次数
    knowledge_sharing: int       # 知识分享次数
    meeting_participation: int   # 会议参与次数
    communication_score: float   # 沟通评分


@dataclass
class ProjectContribution:
    """项目贡献"""
    project_id: int
    project_name: str
    project_level: str           # A/B/C
    role: str                    # 角色
    hours_contributed: float     # 贡献工时
    tasks_completed: int         # 完成任务数
    contribution_rate: float     # 贡献占比
    performance_in_project: str  # 项目内表现评价


@dataclass
class PerformanceScore:
    """绩效得分"""
    workload_score: float        # 工时得分 (权重20%)
    task_score: float            # 任务得分 (权重35%)
    quality_score: float         # 质量得分 (权重25%)
    collaboration_score: float   # 协作得分 (权重10%)
    extra_score: float           # 额外加分 (权重10%)
    total_score: float           # 总分
    level: PerformanceLevel      # 绩效等级
    rank_in_team: int            # 团队排名
    rank_in_dept: int            # 部门排名
    percentile: float            # 百分位


@dataclass
class TrendData:
    """趋势数据"""
    period: str                  # 周期标识
    score: float                 # 得分
    level: str                   # 等级
    highlight: str               # 亮点


@dataclass
class PerformanceReport:
    """绩效报告"""
    report_id: str
    user_id: int
    user_name: str
    department: str
    position: str
    period_type: ReportPeriodType
    period_start: date
    period_end: date
    generated_at: datetime
    
    # 各维度指标
    workload: WorkloadMetrics
    tasks: TaskMetrics
    quality: QualityMetrics
    collaboration: CollaborationMetrics
    
    # 项目贡献
    project_contributions: List[ProjectContribution]
    
    # 绩效得分
    score: PerformanceScore
    
    # 趋势数据
    trends: List[TrendData]
    
    # 亮点与待改进
    highlights: List[str]
    improvements: List[str]
    
    # 领导评语（仅领导可见时填写）
    manager_comment: Optional[str] = None
    
    # 元数据
    view_level: PerformanceViewLevel = PerformanceViewLevel.SELF
    is_self_view: bool = True
    
    def to_dict(self) -> Dict:
        """转换为字典，支持JSON序列化"""
        return {
            "report_id": self.report_id,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "department": self.department,
            "position": self.position,
            "period_type": self.period_type.value,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "generated_at": self.generated_at.isoformat(),
            "workload": self._workload_to_dict(),
            "tasks": self._tasks_to_dict(),
            "quality": self._quality_to_dict(),
            "collaboration": self._collaboration_to_dict(),
            "project_contributions": [self._contribution_to_dict(c) for c in self.project_contributions],
            "score": self._score_to_dict(),
            "trends": [{"period": t.period, "score": t.score, "level": t.level, "highlight": t.highlight} for t in self.trends],
            "highlights": self.highlights,
            "improvements": self.improvements,
            "manager_comment": self.manager_comment,
            "view_level": self.view_level.value,
            "is_self_view": self.is_self_view
        }
    
    def _workload_to_dict(self) -> Dict:
        return {
            "standard_hours": self.workload.standard_hours,
            "actual_hours": self.workload.actual_hours,
            "overtime_hours": self.workload.overtime_hours,
            "billable_hours": self.workload.billable_hours,
            "utilization_rate": round(self.workload.utilization_rate * 100, 1),
            "overtime_rate": round(self.workload.overtime_rate * 100, 1),
            "attendance_rate": round(self.workload.attendance_rate * 100, 1),
            "leave_days": self.workload.leave_days
        }
    
    def _tasks_to_dict(self) -> Dict:
        return {
            "total_assigned": self.tasks.total_assigned,
            "completed": self.tasks.completed,
            "in_progress": self.tasks.in_progress,
            "overdue": self.tasks.overdue,
            "completion_rate": round(self.tasks.completion_rate * 100, 1),
            "on_time_rate": round(self.tasks.on_time_rate * 100, 1),
            "avg_completion_days": round(self.tasks.avg_completion_days, 1),
            "complexity_weighted_score": round(self.tasks.complexity_weighted_score, 1)
        }
    
    def _quality_to_dict(self) -> Dict:
        return {
            "first_pass_rate": round(self.quality.first_pass_rate * 100, 1),
            "rework_count": self.quality.rework_count,
            "defect_count": self.quality.defect_count,
            "review_pass_rate": round(self.quality.review_pass_rate * 100, 1),
            "customer_satisfaction": self.quality.customer_satisfaction,
            "documentation_score": round(self.quality.documentation_score, 1)
        }
    
    def _collaboration_to_dict(self) -> Dict:
        return {
            "support_given": self.collaboration.support_given,
            "support_received": self.collaboration.support_received,
            "knowledge_sharing": self.collaboration.knowledge_sharing,
            "meeting_participation": self.collaboration.meeting_participation,
            "communication_score": round(self.collaboration.communication_score, 1)
        }
    
    def _contribution_to_dict(self, c: ProjectContribution) -> Dict:
        return {
            "project_id": c.project_id,
            "project_name": c.project_name,
            "project_level": c.project_level,
            "role": c.role,
            "hours_contributed": c.hours_contributed,
            "tasks_completed": c.tasks_completed,
            "contribution_rate": round(c.contribution_rate * 100, 1),
            "performance_in_project": c.performance_in_project
        }
    
    def _score_to_dict(self) -> Dict:
        return {
            "workload_score": round(self.score.workload_score, 1),
            "task_score": round(self.score.task_score, 1),
            "quality_score": round(self.score.quality_score, 1),
            "collaboration_score": round(self.score.collaboration_score, 1),
            "extra_score": round(self.score.extra_score, 1),
            "total_score": round(self.score.total_score, 1),
            "level": self.score.level.value,
            "level_text": self._get_level_text(self.score.level),
            "rank_in_team": self.score.rank_in_team,
            "rank_in_dept": self.score.rank_in_dept,
            "percentile": round(self.score.percentile, 1)
        }
    
    def _get_level_text(self, level: PerformanceLevel) -> str:
        texts = {
            PerformanceLevel.EXCELLENT: "优秀",
            PerformanceLevel.GOOD: "良好",
            PerformanceLevel.QUALIFIED: "合格",
            PerformanceLevel.NEEDS_IMPROVEMENT: "待改进",
            PerformanceLevel.UNQUALIFIED: "不合格"
        }
        return texts.get(level, "未知")


@dataclass
class TeamPerformanceSummary:
    """团队绩效汇总"""
    team_id: int
    team_name: str
    period_type: ReportPeriodType
    period_start: date
    period_end: date
    
    # 汇总指标
    member_count: int
    avg_score: float
    max_score: float
    min_score: float
    
    # 等级分布
    excellent_count: int
    good_count: int
    qualified_count: int
    needs_improvement_count: int
    
    # 排名
    members_ranking: List[Dict]  # [{user_id, user_name, score, level, rank}]
    
    # 团队对比
    vs_last_period: float        # 环比
    vs_dept_avg: float           # 与部门平均对比
    
    def to_dict(self) -> Dict:
        return {
            "team_id": self.team_id,
            "team_name": self.team_name,
            "period_type": self.period_type.value,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "member_count": self.member_count,
            "avg_score": round(self.avg_score, 1),
            "max_score": round(self.max_score, 1),
            "min_score": round(self.min_score, 1),
            "level_distribution": {
                "excellent": self.excellent_count,
                "good": self.good_count,
                "qualified": self.qualified_count,
                "needs_improvement": self.needs_improvement_count
            },
            "members_ranking": self.members_ranking,
            "vs_last_period": round(self.vs_last_period, 1),
            "vs_dept_avg": round(self.vs_dept_avg, 1)
        }


@dataclass
class ProjectProgressReport:
    """项目进展报告"""
    project_id: int
    project_code: str
    project_name: str
    customer: str
    level: str
    pm_name: str
    period_start: date
    period_end: date
    generated_at: datetime
    
    # 整体进度
    plan_progress: float         # 计划进度
    actual_progress: float       # 实际进度
    progress_deviation: float    # 进度偏差
    health_status: str           # 健康状态
    
    # 里程碑
    milestones: List[Dict]       # [{name, plan_date, actual_date, status}]
    
    # 工时投入
    total_plan_hours: float      # 计划总工时
    total_actual_hours: float    # 实际总工时
    hours_deviation: float       # 工时偏差
    
    # 成本
    budget: float
    actual_cost: float
    cost_deviation: float
    
    # 成员绩效
    team_performance: List[Dict]  # [{user_id, user_name, role, hours, tasks, score}]
    
    # 风险与问题
    risks: List[Dict]
    issues: List[Dict]
    
    # 本期完成
    completed_tasks: List[Dict]
    
    # 下期计划
    next_period_plan: List[Dict]
    
    def to_dict(self) -> Dict:
        return {
            "project_id": self.project_id,
            "project_code": self.project_code,
            "project_name": self.project_name,
            "customer": self.customer,
            "level": self.level,
            "pm_name": self.pm_name,
            "period": f"{self.period_start.isoformat()} ~ {self.period_end.isoformat()}",
            "generated_at": self.generated_at.isoformat(),
            "progress": {
                "plan": round(self.plan_progress * 100, 1),
                "actual": round(self.actual_progress * 100, 1),
                "deviation": round(self.progress_deviation * 100, 1),
                "health": self.health_status
            },
            "milestones": self.milestones,
            "hours": {
                "plan": self.total_plan_hours,
                "actual": self.total_actual_hours,
                "deviation": round(self.hours_deviation * 100, 1)
            },
            "cost": {
                "budget": self.budget,
                "actual": self.actual_cost,
                "deviation": round(self.cost_deviation * 100, 1)
            },
            "team_performance": self.team_performance,
            "risks": self.risks,
            "issues": self.issues,
            "completed_tasks": self.completed_tasks,
            "next_period_plan": self.next_period_plan
        }


# ==================== 绩效计算引擎 ====================

class PerformanceEngine:
    """绩效计算引擎"""
    
    # 权重配置
    WEIGHTS = {
        "workload": 0.20,      # 工时 20%
        "task": 0.35,          # 任务 35%
        "quality": 0.25,       # 质量 25%
        "collaboration": 0.10,  # 协作 10%
        "extra": 0.10          # 额外 10%
    }
    
    # 等级阈值
    LEVEL_THRESHOLDS = {
        PerformanceLevel.EXCELLENT: 90,
        PerformanceLevel.GOOD: 80,
        PerformanceLevel.QUALIFIED: 60,
        PerformanceLevel.NEEDS_IMPROVEMENT: 40,
        PerformanceLevel.UNQUALIFIED: 0
    }
    
    def __init__(self):
        pass
    
    def calculate_workload_score(self, metrics: WorkloadMetrics) -> float:
        """计算工时得分"""
        score = 0
        
        # 利用率得分 (40分)
        if metrics.utilization_rate >= 0.95:
            score += 40
        elif metrics.utilization_rate >= 0.85:
            score += 35
        elif metrics.utilization_rate >= 0.75:
            score += 30
        elif metrics.utilization_rate >= 0.60:
            score += 20
        else:
            score += 10
        
        # 出勤率得分 (30分)
        score += min(30, metrics.attendance_rate * 30)
        
        # 有效工时占比得分 (30分)
        if metrics.actual_hours > 0:
            billable_ratio = metrics.billable_hours / metrics.actual_hours
            score += min(30, billable_ratio * 30)
        
        return score
    
    def calculate_task_score(self, metrics: TaskMetrics) -> float:
        """计算任务得分"""
        score = 0
        
        # 完成率得分 (40分)
        score += min(40, metrics.completion_rate * 40)
        
        # 按时完成率得分 (35分)
        score += min(35, metrics.on_time_rate * 35)
        
        # 复杂度加权得分 (25分)
        score += min(25, metrics.complexity_weighted_score / 4)
        
        return score
    
    def calculate_quality_score(self, metrics: QualityMetrics) -> float:
        """计算质量得分"""
        score = 0
        
        # 一次通过率 (40分)
        score += min(40, metrics.first_pass_rate * 40)
        
        # 返工惩罚 (-5分/次，最多扣20分)
        score -= min(20, metrics.rework_count * 5)
        
        # 评审通过率 (30分)
        score += min(30, metrics.review_pass_rate * 30)
        
        # 文档完整度 (30分)
        score += min(30, metrics.documentation_score / 100 * 30)
        
        return max(0, score)
    
    def calculate_collaboration_score(self, metrics: CollaborationMetrics) -> float:
        """计算协作得分"""
        score = 0
        
        # 支援他人 (30分)
        score += min(30, metrics.support_given * 5)
        
        # 知识分享 (30分)
        score += min(30, metrics.knowledge_sharing * 10)
        
        # 沟通评分 (40分)
        score += min(40, metrics.communication_score / 100 * 40)
        
        return score
    
    def calculate_total_score(
        self,
        workload: WorkloadMetrics,
        tasks: TaskMetrics,
        quality: QualityMetrics,
        collaboration: CollaborationMetrics,
        extra_points: float = 0
    ) -> PerformanceScore:
        """计算总绩效得分"""
        
        workload_score = self.calculate_workload_score(workload)
        task_score = self.calculate_task_score(tasks)
        quality_score = self.calculate_quality_score(quality)
        collab_score = self.calculate_collaboration_score(collaboration)
        
        # 加权总分
        total = (
            workload_score * self.WEIGHTS["workload"] +
            task_score * self.WEIGHTS["task"] +
            quality_score * self.WEIGHTS["quality"] +
            collab_score * self.WEIGHTS["collaboration"] +
            extra_points * self.WEIGHTS["extra"]
        )
        
        # 确定等级
        level = PerformanceLevel.UNQUALIFIED
        for lvl, threshold in self.LEVEL_THRESHOLDS.items():
            if total >= threshold:
                level = lvl
                break
        
        return PerformanceScore(
            workload_score=workload_score,
            task_score=task_score,
            quality_score=quality_score,
            collaboration_score=collab_score,
            extra_score=extra_points,
            total_score=total,
            level=level,
            rank_in_team=0,  # 需要后续计算
            rank_in_dept=0,
            percentile=0
        )
    
    def determine_highlights(
        self,
        workload: WorkloadMetrics,
        tasks: TaskMetrics,
        quality: QualityMetrics,
        collaboration: CollaborationMetrics
    ) -> List[str]:
        """识别亮点"""
        highlights = []
        
        if workload.utilization_rate >= 0.95:
            highlights.append("工时利用率优秀，达到95%以上")
        
        if tasks.on_time_rate >= 0.95:
            highlights.append("任务按时完成率优秀，达到95%以上")
        
        if tasks.completion_rate >= 0.90:
            highlights.append("任务完成率高，达到90%以上")
        
        if quality.first_pass_rate >= 0.95:
            highlights.append("一次通过率优秀，达到95%以上")
        
        if quality.rework_count == 0:
            highlights.append("本周期无返工记录，质量稳定")
        
        if collaboration.support_given >= 3:
            highlights.append(f"积极支援团队，帮助同事{collaboration.support_given}次")
        
        if collaboration.knowledge_sharing >= 2:
            highlights.append(f"主动分享知识{collaboration.knowledge_sharing}次")
        
        return highlights
    
    def determine_improvements(
        self,
        workload: WorkloadMetrics,
        tasks: TaskMetrics,
        quality: QualityMetrics,
        collaboration: CollaborationMetrics
    ) -> List[str]:
        """识别待改进项"""
        improvements = []
        
        if workload.utilization_rate < 0.75:
            improvements.append("工时利用率偏低，建议合理规划工作安排")
        
        if tasks.overdue > 0:
            improvements.append(f"有{tasks.overdue}个任务逾期，建议加强时间管理")
        
        if tasks.on_time_rate < 0.80:
            improvements.append("按时完成率不足80%，建议提前规划、及时汇报风险")
        
        if quality.rework_count >= 2:
            improvements.append(f"本周期返工{quality.rework_count}次，建议加强自检")
        
        if quality.first_pass_rate < 0.80:
            improvements.append("一次通过率不足80%，建议提升交付质量")
        
        if collaboration.communication_score < 70:
            improvements.append("沟通协作得分偏低，建议加强团队沟通")
        
        return improvements


# ==================== 报告生成器 ====================

class PerformanceReportGenerator:
    """绩效报告生成器"""
    
    def __init__(self):
        self.engine = PerformanceEngine()
    
    def generate_individual_report(
        self,
        user_id: int,
        period_type: ReportPeriodType,
        period_start: date,
        period_end: date,
        viewer_id: int,
        viewer_role: str
    ) -> PerformanceReport:
        """
        生成个人绩效报告
        
        Args:
            user_id: 被查看人ID
            period_type: 周期类型
            period_start: 开始日期
            period_end: 结束日期
            viewer_id: 查看者ID
            viewer_role: 查看者角色
        """
        # 判断查看权限
        is_self = (user_id == viewer_id)
        view_level = self._determine_view_level(viewer_role, is_self)
        
        # 获取用户基本信息（模拟）
        user_info = self._get_user_info(user_id)
        
        # 获取各维度数据（模拟）
        workload = self._get_workload_metrics(user_id, period_start, period_end)
        tasks = self._get_task_metrics(user_id, period_start, period_end)
        quality = self._get_quality_metrics(user_id, period_start, period_end)
        collaboration = self._get_collaboration_metrics(user_id, period_start, period_end)
        
        # 获取项目贡献
        contributions = self._get_project_contributions(user_id, period_start, period_end)
        
        # 计算绩效得分
        score = self.engine.calculate_total_score(workload, tasks, quality, collaboration)
        score = self._calculate_rankings(score, user_id, user_info['dept_id'])
        
        # 获取趋势数据
        trends = self._get_trends(user_id, period_type, 6)
        
        # 识别亮点和待改进
        highlights = self.engine.determine_highlights(workload, tasks, quality, collaboration)
        improvements = self.engine.determine_improvements(workload, tasks, quality, collaboration)
        
        # 领导评语（仅领导查看下属时可见）
        manager_comment = None
        if not is_self and view_level in [PerformanceViewLevel.DEPARTMENT, PerformanceViewLevel.COMPANY]:
            manager_comment = self._get_manager_comment(user_id, period_start, period_end)
        
        return PerformanceReport(
            report_id=f"PERF-{user_id}-{period_start.strftime('%Y%m%d')}",
            user_id=user_id,
            user_name=user_info['name'],
            department=user_info['dept_name'],
            position=user_info['position'],
            period_type=period_type,
            period_start=period_start,
            period_end=period_end,
            generated_at=datetime.now(),
            workload=workload,
            tasks=tasks,
            quality=quality,
            collaboration=collaboration,
            project_contributions=contributions,
            score=score,
            trends=trends,
            highlights=highlights,
            improvements=improvements,
            manager_comment=manager_comment,
            view_level=view_level,
            is_self_view=is_self
        )
    
    def generate_team_summary(
        self,
        team_id: int,
        period_type: ReportPeriodType,
        period_start: date,
        period_end: date
    ) -> TeamPerformanceSummary:
        """生成团队绩效汇总"""
        
        # 获取团队成员（模拟）
        members = self._get_team_members(team_id)
        
        # 计算每个成员的绩效
        member_scores = []
        for member in members:
            workload = self._get_workload_metrics(member['id'], period_start, period_end)
            tasks = self._get_task_metrics(member['id'], period_start, period_end)
            quality = self._get_quality_metrics(member['id'], period_start, period_end)
            collaboration = self._get_collaboration_metrics(member['id'], period_start, period_end)
            score = self.engine.calculate_total_score(workload, tasks, quality, collaboration)
            
            member_scores.append({
                "user_id": member['id'],
                "user_name": member['name'],
                "score": score.total_score,
                "level": score.level.value
            })
        
        # 排序
        member_scores.sort(key=lambda x: x['score'], reverse=True)
        for i, m in enumerate(member_scores):
            m['rank'] = i + 1
        
        # 统计
        scores = [m['score'] for m in member_scores]
        levels = [m['level'] for m in member_scores]
        
        return TeamPerformanceSummary(
            team_id=team_id,
            team_name=self._get_team_name(team_id),
            period_type=period_type,
            period_start=period_start,
            period_end=period_end,
            member_count=len(members),
            avg_score=sum(scores) / len(scores) if scores else 0,
            max_score=max(scores) if scores else 0,
            min_score=min(scores) if scores else 0,
            excellent_count=levels.count('excellent'),
            good_count=levels.count('good'),
            qualified_count=levels.count('qualified'),
            needs_improvement_count=levels.count('needs_improvement'),
            members_ranking=member_scores,
            vs_last_period=5.2,  # 模拟数据
            vs_dept_avg=3.1
        )
    
    def generate_project_progress(
        self,
        project_id: int,
        period_start: date,
        period_end: date
    ) -> ProjectProgressReport:
        """生成项目进展报告"""
        
        # 获取项目信息（模拟）
        project = self._get_project_info(project_id)
        
        # 获取项目成员绩效
        team_perf = self._get_project_team_performance(project_id, period_start, period_end)
        
        return ProjectProgressReport(
            project_id=project_id,
            project_code=project['code'],
            project_name=project['name'],
            customer=project['customer'],
            level=project['level'],
            pm_name=project['pm_name'],
            period_start=period_start,
            period_end=period_end,
            generated_at=datetime.now(),
            plan_progress=0.70,
            actual_progress=0.68,
            progress_deviation=-0.02,
            health_status="good",
            milestones=[
                {"name": "方案设计", "plan_date": "2025-01-10", "actual_date": "2025-01-08", "status": "completed"},
                {"name": "结构设计", "plan_date": "2025-01-20", "actual_date": None, "status": "in_progress"},
                {"name": "电气设计", "plan_date": "2025-02-01", "actual_date": None, "status": "pending"},
            ],
            total_plan_hours=800,
            total_actual_hours=560,
            hours_deviation=-0.05,
            budget=500000,
            actual_cost=320000,
            cost_deviation=-0.04,
            team_performance=team_perf,
            risks=[
                {"id": 1, "level": "medium", "description": "关键物料交期存在风险", "owner": "采购", "status": "monitoring"}
            ],
            issues=[
                {"id": 1, "level": "low", "description": "图纸细节需要与客户确认", "owner": "张工", "status": "open"}
            ],
            completed_tasks=[
                {"name": "机械结构3D建模", "owner": "张工", "hours": 40},
                {"name": "电气原理图设计", "owner": "李工", "hours": 32},
            ],
            next_period_plan=[
                {"name": "结构图纸出图", "owner": "张工", "plan_hours": 24},
                {"name": "电气控制柜设计", "owner": "李工", "plan_hours": 40},
            ]
        )
    
    # ==================== 辅助方法（模拟数据）====================
    
    def _determine_view_level(self, viewer_role: str, is_self: bool) -> PerformanceViewLevel:
        """确定查看权限级别"""
        if is_self:
            return PerformanceViewLevel.SELF
        
        role_levels = {
            "gm": PerformanceViewLevel.COMPANY,
            "dept_manager": PerformanceViewLevel.DEPARTMENT,
            "pm": PerformanceViewLevel.PROJECT,
            "team_leader": PerformanceViewLevel.TEAM,
            "engineer": PerformanceViewLevel.SELF
        }
        return role_levels.get(viewer_role, PerformanceViewLevel.SELF)
    
    def _get_user_info(self, user_id: int) -> Dict:
        """获取用户信息"""
        users = {
            1: {"id": 1, "name": "张三", "dept_id": 1, "dept_name": "机械组", "position": "机械工程师"},
            2: {"id": 2, "name": "李四", "dept_id": 2, "dept_name": "电气组", "position": "电气工程师"},
            3: {"id": 3, "name": "王五", "dept_id": 3, "dept_name": "软件组", "position": "软件工程师"},
        }
        return users.get(user_id, {"id": user_id, "name": f"用户{user_id}", "dept_id": 1, "dept_name": "未知", "position": "工程师"})
    
    def _get_workload_metrics(self, user_id: int, start: date, end: date) -> WorkloadMetrics:
        """获取工时指标"""
        return WorkloadMetrics(
            standard_hours=176,
            actual_hours=185,
            overtime_hours=15,
            billable_hours=168,
            utilization_rate=0.91,
            overtime_rate=0.08,
            attendance_rate=1.0,
            leave_days=0
        )
    
    def _get_task_metrics(self, user_id: int, start: date, end: date) -> TaskMetrics:
        """获取任务指标"""
        return TaskMetrics(
            total_assigned=15,
            completed=12,
            in_progress=2,
            overdue=1,
            completion_rate=0.80,
            on_time_rate=0.92,
            avg_completion_days=3.5,
            complexity_weighted_score=85
        )
    
    def _get_quality_metrics(self, user_id: int, start: date, end: date) -> QualityMetrics:
        """获取质量指标"""
        return QualityMetrics(
            first_pass_rate=0.92,
            rework_count=1,
            defect_count=2,
            review_pass_rate=0.95,
            customer_satisfaction=4.5,
            documentation_score=88
        )
    
    def _get_collaboration_metrics(self, user_id: int, start: date, end: date) -> CollaborationMetrics:
        """获取协作指标"""
        return CollaborationMetrics(
            support_given=3,
            support_received=1,
            knowledge_sharing=2,
            meeting_participation=8,
            communication_score=85
        )
    
    def _get_project_contributions(self, user_id: int, start: date, end: date) -> List[ProjectContribution]:
        """获取项目贡献"""
        return [
            ProjectContribution(
                project_id=1,
                project_name="XX自动化测试设备",
                project_level="A",
                role="主设计",
                hours_contributed=120,
                tasks_completed=8,
                contribution_rate=0.35,
                performance_in_project="优秀"
            ),
            ProjectContribution(
                project_id=2,
                project_name="YY产线改造",
                project_level="B",
                role="协助",
                hours_contributed=45,
                tasks_completed=3,
                contribution_rate=0.15,
                performance_in_project="良好"
            )
        ]
    
    def _calculate_rankings(self, score: PerformanceScore, user_id: int, dept_id: int) -> PerformanceScore:
        """计算排名"""
        score.rank_in_team = 2
        score.rank_in_dept = 5
        score.percentile = 85.0
        return score
    
    def _get_trends(self, user_id: int, period_type: ReportPeriodType, count: int) -> List[TrendData]:
        """获取趋势数据"""
        return [
            TrendData("2024-12", 82.5, "good", "任务完成率提升"),
            TrendData("2024-11", 78.3, "qualified", ""),
            TrendData("2024-10", 85.1, "good", "质量表现优秀"),
            TrendData("2024-09", 80.2, "good", ""),
            TrendData("2024-08", 76.8, "qualified", ""),
            TrendData("2024-07", 79.5, "qualified", ""),
        ]
    
    def _get_manager_comment(self, user_id: int, start: date, end: date) -> str:
        """获取领导评语"""
        return "本月表现稳定，任务完成质量较高，建议继续保持。在团队协作方面有明显进步。"
    
    def _get_team_members(self, team_id: int) -> List[Dict]:
        """获取团队成员"""
        return [
            {"id": 1, "name": "张三"},
            {"id": 2, "name": "李四"},
            {"id": 3, "name": "王五"},
            {"id": 4, "name": "赵六"},
        ]
    
    def _get_team_name(self, team_id: int) -> str:
        """获取团队名称"""
        teams = {1: "机械组", 2: "电气组", 3: "软件组"}
        return teams.get(team_id, f"团队{team_id}")
    
    def _get_project_info(self, project_id: int) -> Dict:
        """获取项目信息"""
        return {
            "id": project_id,
            "code": "PRJ2025001",
            "name": "XX自动化测试设备",
            "customer": "XX科技有限公司",
            "level": "A",
            "pm_name": "张经理"
        }
    
    def _get_project_team_performance(self, project_id: int, start: date, end: date) -> List[Dict]:
        """获取项目团队绩效"""
        return [
            {"user_id": 1, "user_name": "张三", "role": "机械主设计", "hours": 80, "tasks": 5, "score": 88.5, "level": "good"},
            {"user_id": 2, "user_name": "李四", "role": "电气主设计", "hours": 72, "tasks": 4, "score": 85.2, "level": "good"},
            {"user_id": 3, "user_name": "王五", "role": "软件工程师", "hours": 60, "tasks": 3, "score": 82.0, "level": "good"},
            {"user_id": 4, "user_name": "赵六", "role": "调试工程师", "hours": 40, "tasks": 2, "score": 78.5, "level": "qualified"},
        ]


# ==================== 工厂方法 ====================

def create_report_generator() -> PerformanceReportGenerator:
    """创建报告生成器"""
    return PerformanceReportGenerator()


# ==================== 测试 ====================

if __name__ == "__main__":
    generator = create_report_generator()
    
    # 测试个人绩效报告（自己看自己）
    print("=" * 60)
    print("测试：自己查看自己的绩效报告")
    print("=" * 60)
    
    report = generator.generate_individual_report(
        user_id=1,
        period_type=ReportPeriodType.MONTHLY,
        period_start=date(2024, 12, 1),
        period_end=date(2024, 12, 31),
        viewer_id=1,  # 自己
        viewer_role="engineer"
    )
    
    print(f"报告ID: {report.report_id}")
    print(f"姓名: {report.user_name}")
    print(f"部门: {report.department}")
    print(f"绩效得分: {report.score.total_score:.1f}")
    print(f"绩效等级: {report.score.level.value}")
    print(f"亮点: {report.highlights}")
    print(f"待改进: {report.improvements}")
    
    print("\n" + "=" * 60)
    print("测试：领导查看下属的绩效报告")
    print("=" * 60)
    
    report2 = generator.generate_individual_report(
        user_id=1,
        period_type=ReportPeriodType.MONTHLY,
        period_start=date(2024, 12, 1),
        period_end=date(2024, 12, 31),
        viewer_id=100,  # 领导
        viewer_role="dept_manager"
    )
    
    print(f"领导评语: {report2.manager_comment}")
    print(f"查看级别: {report2.view_level.value}")
