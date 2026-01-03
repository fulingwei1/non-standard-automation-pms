"""
多角色报表引擎 (Multi-Role Report Engine)

设计理念：
1. 同一套数据，多种视角呈现
2. 角色决定结构、语言和重点
3. 风险偏好影响预警阈值
4. 权限控制数据粒度
5. 可扩展的报表模板系统

角色视角矩阵：
┌─────────────┬────────────────┬────────────────┬────────────────┐
│    角色      │    关注重点     │    决策权限     │    风险偏好    │
├─────────────┼────────────────┼────────────────┼────────────────┤
│ 总经理(GM)   │ 经营指标/战略   │ 全部           │ 宏观风险       │
│ 部门经理     │ 资源/效率/成本  │ 本部门         │ 部门级风险     │
│ 项目经理(PM) │ 进度/质量/交付  │ 所负责项目     │ 项目级风险     │
│ 技术负责人   │ 技术/质量/资源  │ 技术决策       │ 技术风险       │
│ 工程师       │ 任务/工时/绩效  │ 个人任务       │ 个人任务风险   │
│ PMC         │ 计划/物料/产能  │ 生产计划       │ 交付风险       │
│ 财务        │ 成本/收入/现金流 │ 财务审批       │ 财务风险       │
└─────────────┴────────────────┴────────────────┴────────────────┘
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
from enum import Enum
from datetime import datetime, date, timedelta
from abc import ABC, abstractmethod
import json


# ==================== 基础类型定义 ====================

class RoleType(Enum):
    """角色类型"""
    GM = "gm"                      # 总经理
    DEPT_MANAGER = "dept_manager"  # 部门经理
    PM = "pm"                      # 项目经理
    TE = "te"                      # 技术负责人
    ENGINEER = "engineer"          # 工程师
    PMC = "pmc"                    # PMC计划员
    FINANCE = "finance"            # 财务
    QA = "qa"                      # 品质


class ReportType(Enum):
    """报表类型"""
    PROJECT_WEEKLY = "project_weekly"       # 项目周报
    PROJECT_MONTHLY = "project_monthly"     # 项目月报
    DEPT_WEEKLY = "dept_weekly"             # 部门周报
    DEPT_MONTHLY = "dept_monthly"           # 部门月报
    COMPANY_MONTHLY = "company_monthly"     # 公司月报
    COST_ANALYSIS = "cost_analysis"         # 成本分析
    WORKLOAD_ANALYSIS = "workload_analysis" # 负荷分析
    QUALITY_REPORT = "quality_report"       # 质量报告
    RISK_REPORT = "risk_report"             # 风险报告
    CUSTOM = "custom"                       # 自定义报表


class ReportPeriod(Enum):
    """报表周期"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    CUSTOM = "custom"


class RiskLevel(Enum):
    """风险等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RoleConfig:
    """角色配置"""
    role: RoleType
    display_name: str
    focus_areas: List[str]           # 关注领域
    data_scope: str                  # 数据范围
    risk_thresholds: Dict[str, float]  # 风险阈值
    metrics_priority: List[str]      # 指标优先级
    language_style: str              # 语言风格：formal/concise/detailed
    chart_preferences: List[str]     # 图表偏好
    action_oriented: bool            # 是否行动导向
    show_recommendations: bool       # 是否显示建议
    show_trends: bool                # 是否显示趋势
    aggregation_level: str           # 聚合级别：summary/detail/granular


# ==================== 角色配置库 ====================

ROLE_CONFIGS: Dict[RoleType, RoleConfig] = {
    RoleType.GM: RoleConfig(
        role=RoleType.GM,
        display_name="总经理",
        focus_areas=["经营指标", "战略目标", "重大风险", "关键项目", "资源瓶颈"],
        data_scope="company",
        risk_thresholds={"progress_delay": 0.15, "cost_overrun": 0.10, "quality_issue": 0.05},
        metrics_priority=["revenue", "profit_margin", "project_completion_rate", "customer_satisfaction", "resource_utilization"],
        language_style="formal",
        chart_preferences=["kpi_dashboard", "trend_line", "comparison_bar"],
        action_oriented=True,
        show_recommendations=True,
        show_trends=True,
        aggregation_level="summary"
    ),
    
    RoleType.DEPT_MANAGER: RoleConfig(
        role=RoleType.DEPT_MANAGER,
        display_name="部门经理",
        focus_areas=["部门效率", "人员负荷", "项目分布", "成本控制", "团队绩效"],
        data_scope="department",
        risk_thresholds={"progress_delay": 0.10, "cost_overrun": 0.08, "workload_overload": 1.2},
        metrics_priority=["team_utilization", "project_count", "on_time_delivery", "cost_variance", "quality_score"],
        language_style="concise",
        chart_preferences=["workload_heatmap", "gantt_overview", "resource_bar"],
        action_oriented=True,
        show_recommendations=True,
        show_trends=True,
        aggregation_level="detail"
    ),
    
    RoleType.PM: RoleConfig(
        role=RoleType.PM,
        display_name="项目经理",
        focus_areas=["项目进度", "里程碑", "风险问题", "资源需求", "客户沟通"],
        data_scope="project",
        risk_thresholds={"task_delay": 0.05, "milestone_risk": 0.10, "scope_change": 0.15},
        metrics_priority=["schedule_performance", "milestone_completion", "issue_count", "resource_allocation", "budget_variance"],
        language_style="detailed",
        chart_preferences=["gantt_chart", "burndown", "issue_tracker", "milestone_timeline"],
        action_oriented=True,
        show_recommendations=True,
        show_trends=True,
        aggregation_level="granular"
    ),
    
    RoleType.TE: RoleConfig(
        role=RoleType.TE,
        display_name="技术负责人",
        focus_areas=["技术方案", "设计质量", "技术风险", "资源技能", "知识沉淀"],
        data_scope="project",
        risk_thresholds={"design_issue": 0.05, "tech_debt": 0.10, "skill_gap": 0.15},
        metrics_priority=["design_review_pass_rate", "technical_issue_count", "rework_rate", "documentation_coverage"],
        language_style="detailed",
        chart_preferences=["issue_breakdown", "quality_trend", "skill_matrix"],
        action_oriented=True,
        show_recommendations=True,
        show_trends=True,
        aggregation_level="granular"
    ),
    
    RoleType.ENGINEER: RoleConfig(
        role=RoleType.ENGINEER,
        display_name="工程师",
        focus_areas=["个人任务", "工时统计", "技能提升", "协作情况"],
        data_scope="personal",
        risk_thresholds={"task_overdue": 0.0, "workload": 1.0},
        metrics_priority=["task_completion", "hours_logged", "on_time_rate", "collaboration_score"],
        language_style="concise",
        chart_preferences=["task_list", "time_tracking", "calendar_view"],
        action_oriented=True,
        show_recommendations=False,
        show_trends=False,
        aggregation_level="granular"
    ),
    
    RoleType.PMC: RoleConfig(
        role=RoleType.PMC,
        display_name="PMC计划员",
        focus_areas=["生产计划", "物料齐套", "产能负荷", "交付风险"],
        data_scope="company",
        risk_thresholds={"material_shortage": 0.05, "capacity_overload": 0.9, "delivery_risk": 0.10},
        metrics_priority=["material_readiness", "capacity_utilization", "on_time_delivery", "plan_accuracy"],
        language_style="concise",
        chart_preferences=["capacity_chart", "material_status", "delivery_calendar"],
        action_oriented=True,
        show_recommendations=True,
        show_trends=True,
        aggregation_level="detail"
    ),
    
    RoleType.FINANCE: RoleConfig(
        role=RoleType.FINANCE,
        display_name="财务",
        focus_areas=["项目成本", "预算执行", "应收账款", "现金流"],
        data_scope="company",
        risk_thresholds={"budget_overrun": 0.05, "receivable_overdue": 30, "cash_flow_risk": 0.15},
        metrics_priority=["actual_vs_budget", "profit_margin", "cash_collection", "cost_breakdown"],
        language_style="formal",
        chart_preferences=["cost_waterfall", "budget_variance", "cash_flow_chart"],
        action_oriented=False,
        show_recommendations=True,
        show_trends=True,
        aggregation_level="detail"
    ),
    
    RoleType.QA: RoleConfig(
        role=RoleType.QA,
        display_name="品质工程师",
        focus_areas=["质量指标", "问题追溯", "检验记录", "改进措施"],
        data_scope="company",
        risk_thresholds={"defect_rate": 0.02, "customer_complaint": 0.01, "audit_finding": 0.05},
        metrics_priority=["first_pass_yield", "defect_count", "customer_satisfaction", "audit_score"],
        language_style="detailed",
        chart_preferences=["pareto_chart", "control_chart", "trend_analysis"],
        action_oriented=True,
        show_recommendations=True,
        show_trends=True,
        aggregation_level="granular"
    ),
}


# ==================== 报表数据结构 ====================

@dataclass
class ReportSection:
    """报表章节"""
    id: str
    title: str
    order: int
    content_type: str  # text/table/chart/kpi/alert/recommendation
    content: Any
    visible_to: List[RoleType] = field(default_factory=list)
    importance: str = "normal"  # critical/high/normal/low


@dataclass
class ReportMetric:
    """报表指标"""
    id: str
    name: str
    value: Any
    unit: str = ""
    target: Optional[float] = None
    previous: Optional[float] = None
    trend: Optional[str] = None  # up/down/stable
    status: str = "normal"  # good/warning/critical
    sparkline_data: List[float] = field(default_factory=list)


@dataclass
class ReportAlert:
    """报表预警"""
    id: str
    level: RiskLevel
    title: str
    description: str
    affected_items: List[str]
    suggested_actions: List[str]
    owner: str
    due_date: Optional[date] = None


@dataclass
class ReportRecommendation:
    """报表建议"""
    id: str
    category: str
    title: str
    description: str
    impact: str  # high/medium/low
    effort: str  # high/medium/low
    priority_score: float


@dataclass
class GeneratedReport:
    """生成的报表"""
    id: str
    title: str
    subtitle: str
    report_type: ReportType
    period: ReportPeriod
    generated_at: datetime
    generated_for: RoleType
    scope_description: str
    sections: List[ReportSection]
    metrics: List[ReportMetric]
    alerts: List[ReportAlert]
    recommendations: List[ReportRecommendation]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "id": self.id,
            "title": self.title,
            "subtitle": self.subtitle,
            "report_type": self.report_type.value,
            "period": self.period.value,
            "generated_at": self.generated_at.isoformat(),
            "generated_for": self.generated_for.value,
            "scope_description": self.scope_description,
            "sections": [self._section_to_dict(s) for s in self.sections],
            "metrics": [self._metric_to_dict(m) for m in self.metrics],
            "alerts": [self._alert_to_dict(a) for a in self.alerts],
            "recommendations": [self._recommendation_to_dict(r) for r in self.recommendations],
            "metadata": self.metadata
        }
    
    def _section_to_dict(self, section: ReportSection) -> Dict:
        return {
            "id": section.id,
            "title": section.title,
            "order": section.order,
            "content_type": section.content_type,
            "content": section.content,
            "importance": section.importance
        }
    
    def _metric_to_dict(self, metric: ReportMetric) -> Dict:
        return {
            "id": metric.id,
            "name": metric.name,
            "value": metric.value,
            "unit": metric.unit,
            "target": metric.target,
            "previous": metric.previous,
            "trend": metric.trend,
            "status": metric.status,
            "sparkline_data": metric.sparkline_data
        }
    
    def _alert_to_dict(self, alert: ReportAlert) -> Dict:
        return {
            "id": alert.id,
            "level": alert.level.value,
            "title": alert.title,
            "description": alert.description,
            "affected_items": alert.affected_items,
            "suggested_actions": alert.suggested_actions,
            "owner": alert.owner,
            "due_date": alert.due_date.isoformat() if alert.due_date else None
        }
    
    def _recommendation_to_dict(self, rec: ReportRecommendation) -> Dict:
        return {
            "id": rec.id,
            "category": rec.category,
            "title": rec.title,
            "description": rec.description,
            "impact": rec.impact,
            "effort": rec.effort,
            "priority_score": rec.priority_score
        }


# ==================== 数据提供者接口 ====================

class DataProvider(ABC):
    """数据提供者抽象基类"""
    
    @abstractmethod
    def get_projects(self, scope: str, scope_id: Optional[int] = None) -> List[Dict]:
        """获取项目数据"""
        pass
    
    @abstractmethod
    def get_tasks(self, scope: str, scope_id: Optional[int] = None) -> List[Dict]:
        """获取任务数据"""
        pass
    
    @abstractmethod
    def get_timesheets(self, scope: str, scope_id: Optional[int] = None, 
                       start_date: date = None, end_date: date = None) -> List[Dict]:
        """获取工时数据"""
        pass
    
    @abstractmethod
    def get_users(self, scope: str, scope_id: Optional[int] = None) -> List[Dict]:
        """获取人员数据"""
        pass
    
    @abstractmethod
    def get_costs(self, scope: str, scope_id: Optional[int] = None) -> List[Dict]:
        """获取成本数据"""
        pass
    
    @abstractmethod
    def get_alerts(self, scope: str, scope_id: Optional[int] = None) -> List[Dict]:
        """获取预警数据"""
        pass


class MockDataProvider(DataProvider):
    """模拟数据提供者（用于测试）"""
    
    def get_projects(self, scope: str, scope_id: Optional[int] = None) -> List[Dict]:
        return [
            {"id": 1, "name": "XX自动化测试设备", "code": "PRJ2025001", "customer": "XX科技", 
             "level": "A", "status": "active", "progress": 68, "health": "good",
             "plan_start": "2025-01-15", "plan_end": "2025-04-30", 
             "budget": 500000, "actual_cost": 320000, "pm": "张经理"},
            {"id": 2, "name": "YY产线改造", "code": "PRJ2025002", "customer": "YY电子",
             "level": "B", "status": "active", "progress": 45, "health": "warning",
             "plan_start": "2025-02-01", "plan_end": "2025-03-31",
             "budget": 200000, "actual_cost": 95000, "pm": "王经理"},
            {"id": 3, "name": "ZZ检测系统", "code": "PRJ2025003", "customer": "ZZ精密",
             "level": "C", "status": "active", "progress": 82, "health": "good",
             "plan_start": "2024-12-01", "plan_end": "2025-01-20",
             "budget": 80000, "actual_cost": 72000, "pm": "李经理"},
        ]
    
    def get_tasks(self, scope: str, scope_id: Optional[int] = None) -> List[Dict]:
        return [
            {"id": 1, "project_id": 1, "name": "机械结构设计", "status": "completed", "progress": 100, "owner": "张工"},
            {"id": 2, "project_id": 1, "name": "电气设计", "status": "in_progress", "progress": 60, "owner": "李工"},
            {"id": 3, "project_id": 1, "name": "软件开发", "status": "in_progress", "progress": 40, "owner": "王工"},
            {"id": 4, "project_id": 2, "name": "方案设计", "status": "completed", "progress": 100, "owner": "赵工"},
            {"id": 5, "project_id": 2, "name": "采购", "status": "in_progress", "progress": 30, "owner": "钱工"},
        ]
    
    def get_timesheets(self, scope: str, scope_id: Optional[int] = None,
                       start_date: date = None, end_date: date = None) -> List[Dict]:
        return [
            {"user_id": 1, "user_name": "张工", "project_id": 1, "hours": 40, "week": "2025-W01"},
            {"user_id": 2, "user_name": "李工", "project_id": 1, "hours": 35, "week": "2025-W01"},
            {"user_id": 3, "user_name": "王工", "project_id": 1, "hours": 42, "week": "2025-W01"},
            {"user_id": 4, "user_name": "赵工", "project_id": 2, "hours": 38, "week": "2025-W01"},
        ]
    
    def get_users(self, scope: str, scope_id: Optional[int] = None) -> List[Dict]:
        return [
            {"id": 1, "name": "张工", "dept": "机械组", "role": "engineer", "utilization": 0.95},
            {"id": 2, "name": "李工", "dept": "电气组", "role": "engineer", "utilization": 0.85},
            {"id": 3, "name": "王工", "dept": "软件组", "role": "engineer", "utilization": 1.05},
            {"id": 4, "name": "赵工", "dept": "机械组", "role": "engineer", "utilization": 0.90},
        ]
    
    def get_costs(self, scope: str, scope_id: Optional[int] = None) -> List[Dict]:
        return [
            {"project_id": 1, "category": "人工", "budget": 200000, "actual": 180000},
            {"project_id": 1, "category": "物料", "budget": 250000, "actual": 120000},
            {"project_id": 1, "category": "外协", "budget": 50000, "actual": 20000},
            {"project_id": 2, "category": "人工", "budget": 80000, "actual": 45000},
            {"project_id": 2, "category": "物料", "budget": 100000, "actual": 40000},
        ]
    
    def get_alerts(self, scope: str, scope_id: Optional[int] = None) -> List[Dict]:
        return [
            {"id": 1, "level": "high", "type": "progress_delay", "project_id": 2, 
             "title": "YY产线改造进度滞后", "description": "当前进度45%，计划进度60%，滞后15%"},
            {"id": 2, "level": "medium", "type": "workload_overload", "user_id": 3,
             "title": "王工负荷过高", "description": "当前负荷率105%，超过标准"},
            {"id": 3, "level": "low", "type": "milestone_risk", "project_id": 3,
             "title": "ZZ检测系统交付风险", "description": "距离交付还有15天，剩余任务较多"},
        ]


# ==================== 报表生成器 ====================

class ReportGenerator:
    """报表生成器"""
    
    def __init__(self, data_provider: DataProvider):
        self.data_provider = data_provider
        self.role_configs = ROLE_CONFIGS
    
    def generate_report(
        self,
        report_type: ReportType,
        role: RoleType,
        period: ReportPeriod = ReportPeriod.WEEKLY,
        scope_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        custom_params: Optional[Dict] = None
    ) -> GeneratedReport:
        """
        生成报表
        
        Args:
            report_type: 报表类型
            role: 查看角色
            period: 报表周期
            scope_id: 作用域ID（项目ID/部门ID等）
            start_date: 开始日期
            end_date: 结束日期
            custom_params: 自定义参数
        
        Returns:
            GeneratedReport: 生成的报表
        """
        config = self.role_configs.get(role)
        if not config:
            raise ValueError(f"未知角色: {role}")
        
        # 确定日期范围
        if not end_date:
            end_date = date.today()
        if not start_date:
            if period == ReportPeriod.WEEKLY:
                start_date = end_date - timedelta(days=7)
            elif period == ReportPeriod.MONTHLY:
                start_date = end_date - timedelta(days=30)
            elif period == ReportPeriod.QUARTERLY:
                start_date = end_date - timedelta(days=90)
            else:
                start_date = end_date - timedelta(days=7)
        
        # 获取数据
        data_scope = config.data_scope
        projects = self.data_provider.get_projects(data_scope, scope_id)
        tasks = self.data_provider.get_tasks(data_scope, scope_id)
        timesheets = self.data_provider.get_timesheets(data_scope, scope_id, start_date, end_date)
        users = self.data_provider.get_users(data_scope, scope_id)
        costs = self.data_provider.get_costs(data_scope, scope_id)
        alerts = self.data_provider.get_alerts(data_scope, scope_id)
        
        # 根据报表类型生成报表
        generator_method = self._get_generator_method(report_type)
        return generator_method(
            role=role,
            config=config,
            period=period,
            start_date=start_date,
            end_date=end_date,
            projects=projects,
            tasks=tasks,
            timesheets=timesheets,
            users=users,
            costs=costs,
            alerts=alerts,
            custom_params=custom_params or {}
        )
    
    def _get_generator_method(self, report_type: ReportType) -> Callable:
        """获取报表生成方法"""
        generators = {
            ReportType.PROJECT_WEEKLY: self._generate_project_weekly,
            ReportType.PROJECT_MONTHLY: self._generate_project_monthly,
            ReportType.DEPT_WEEKLY: self._generate_dept_weekly,
            ReportType.DEPT_MONTHLY: self._generate_dept_monthly,
            ReportType.COMPANY_MONTHLY: self._generate_company_monthly,
            ReportType.COST_ANALYSIS: self._generate_cost_analysis,
            ReportType.WORKLOAD_ANALYSIS: self._generate_workload_analysis,
            ReportType.RISK_REPORT: self._generate_risk_report,
        }
        return generators.get(report_type, self._generate_project_weekly)
    
    def _generate_project_weekly(self, role: RoleType, config: RoleConfig, **kwargs) -> GeneratedReport:
        """生成项目周报"""
        projects = kwargs.get('projects', [])
        tasks = kwargs.get('tasks', [])
        alerts = kwargs.get('alerts', [])
        start_date = kwargs.get('start_date')
        end_date = kwargs.get('end_date')
        
        # 根据角色调整报表内容
        sections = []
        metrics = []
        report_alerts = []
        recommendations = []
        
        # === 核心指标 ===
        if role == RoleType.GM:
            # 总经理视角：关注整体经营
            metrics = [
                ReportMetric("active_projects", "进行中项目", len([p for p in projects if p['status'] == 'active']), "个", 
                           sparkline_data=[10, 11, 12, 12, 12]),
                ReportMetric("avg_progress", "平均进度", f"{sum(p['progress'] for p in projects) / len(projects):.0f}" if projects else "0", "%",
                           target=70, previous=62, trend="up", status="good"),
                ReportMetric("health_good", "健康项目", len([p for p in projects if p.get('health') == 'good']), "个"),
                ReportMetric("total_budget", "总预算", f"{sum(p['budget'] for p in projects)/10000:.0f}", "万元"),
            ]
            
            sections.append(ReportSection(
                id="executive_summary",
                title="经营概览",
                order=1,
                content_type="text",
                content=self._generate_executive_summary(projects, role),
                importance="critical"
            ))
            
        elif role == RoleType.PM:
            # 项目经理视角：关注项目细节
            project = projects[0] if projects else {}
            completed_tasks = len([t for t in tasks if t.get('status') == 'completed'])
            total_tasks = len(tasks)
            
            metrics = [
                ReportMetric("project_progress", "项目进度", project.get('progress', 0), "%",
                           target=70, previous=65, trend="up", status="good"),
                ReportMetric("task_completion", "任务完成率", f"{completed_tasks}/{total_tasks}", "",
                           status="good" if completed_tasks/total_tasks > 0.8 else "warning"),
                ReportMetric("milestone_status", "里程碑状态", "2/3已完成", "",
                           status="good"),
                ReportMetric("issue_count", "未解决问题", 3, "个",
                           status="warning"),
            ]
            
            sections.append(ReportSection(
                id="progress_detail",
                title="本周进展详情",
                order=1,
                content_type="table",
                content=self._generate_task_table(tasks),
                importance="high"
            ))
            
        elif role == RoleType.ENGINEER:
            # 工程师视角：关注个人任务
            my_tasks = [t for t in tasks if t.get('owner') == '张工']  # 模拟当前用户
            
            metrics = [
                ReportMetric("my_tasks", "我的任务", len(my_tasks), "个"),
                ReportMetric("completed", "已完成", len([t for t in my_tasks if t.get('status') == 'completed']), "个"),
                ReportMetric("hours_logged", "本周工时", 40, "h", target=40),
                ReportMetric("on_time_rate", "按时完成率", 95, "%"),
            ]
            
            sections.append(ReportSection(
                id="my_task_list",
                title="我的任务清单",
                order=1,
                content_type="task_list",
                content=my_tasks,
                importance="high"
            ))
        
        # === 预警信息（根据角色过滤）===
        for alert_data in alerts:
            if self._should_show_alert(alert_data, role, config):
                report_alerts.append(ReportAlert(
                    id=str(alert_data['id']),
                    level=RiskLevel(alert_data['level']),
                    title=alert_data['title'],
                    description=alert_data['description'],
                    affected_items=[],
                    suggested_actions=self._generate_actions(alert_data, role),
                    owner="",
                ))
        
        # === 建议（仅对管理层角色）===
        if config.show_recommendations:
            recommendations = self._generate_recommendations(projects, tasks, alerts, role)
        
        # 生成报表标题
        title = self._generate_title(ReportType.PROJECT_WEEKLY, role, config)
        subtitle = f"{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}"
        
        return GeneratedReport(
            id=f"RPT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            title=title,
            subtitle=subtitle,
            report_type=ReportType.PROJECT_WEEKLY,
            period=ReportPeriod.WEEKLY,
            generated_at=datetime.now(),
            generated_for=role,
            scope_description=self._get_scope_description(config),
            sections=sections,
            metrics=metrics,
            alerts=report_alerts,
            recommendations=recommendations,
            metadata={
                "role_config": config.display_name,
                "data_scope": config.data_scope,
                "language_style": config.language_style
            }
        )
    
    def _generate_project_monthly(self, **kwargs) -> GeneratedReport:
        """生成项目月报"""
        # 类似周报，但聚合级别更高
        return self._generate_project_weekly(**kwargs)
    
    def _generate_dept_weekly(self, **kwargs) -> GeneratedReport:
        """生成部门周报"""
        return self._generate_project_weekly(**kwargs)
    
    def _generate_dept_monthly(self, **kwargs) -> GeneratedReport:
        """生成部门月报"""
        return self._generate_project_weekly(**kwargs)
    
    def _generate_company_monthly(self, **kwargs) -> GeneratedReport:
        """生成公司月报"""
        return self._generate_project_weekly(**kwargs)
    
    def _generate_cost_analysis(self, role: RoleType, config: RoleConfig, **kwargs) -> GeneratedReport:
        """生成成本分析报表"""
        projects = kwargs.get('projects', [])
        costs = kwargs.get('costs', [])
        
        sections = []
        metrics = []
        
        # 成本汇总
        total_budget = sum(p['budget'] for p in projects)
        total_actual = sum(p['actual_cost'] for p in projects)
        variance = (total_actual - total_budget) / total_budget * 100 if total_budget > 0 else 0
        
        if role == RoleType.GM or role == RoleType.FINANCE:
            metrics = [
                ReportMetric("total_budget", "总预算", f"{total_budget/10000:.0f}", "万元"),
                ReportMetric("total_actual", "实际成本", f"{total_actual/10000:.0f}", "万元"),
                ReportMetric("variance", "成本偏差", f"{variance:+.1f}", "%", 
                           status="good" if variance <= 5 else "warning" if variance <= 10 else "critical"),
                ReportMetric("remaining", "剩余预算", f"{(total_budget-total_actual)/10000:.0f}", "万元"),
            ]
            
            sections.append(ReportSection(
                id="cost_breakdown",
                title="成本构成分析",
                order=1,
                content_type="chart",
                content={"type": "waterfall", "data": costs},
                importance="high"
            ))
            
            sections.append(ReportSection(
                id="project_cost_comparison",
                title="项目成本对比",
                order=2,
                content_type="table",
                content=self._generate_cost_table(projects),
                importance="normal"
            ))
        
        return GeneratedReport(
            id=f"COST-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            title=self._generate_title(ReportType.COST_ANALYSIS, role, config),
            subtitle="成本分析报表",
            report_type=ReportType.COST_ANALYSIS,
            period=ReportPeriod.MONTHLY,
            generated_at=datetime.now(),
            generated_for=role,
            scope_description=self._get_scope_description(config),
            sections=sections,
            metrics=metrics,
            alerts=[],
            recommendations=[],
        )
    
    def _generate_workload_analysis(self, role: RoleType, config: RoleConfig, **kwargs) -> GeneratedReport:
        """生成负荷分析报表"""
        users = kwargs.get('users', [])
        timesheets = kwargs.get('timesheets', [])
        
        metrics = []
        sections = []
        alerts = []
        
        avg_utilization = sum(u['utilization'] for u in users) / len(users) if users else 0
        overloaded = [u for u in users if u['utilization'] > 1.0]
        underloaded = [u for u in users if u['utilization'] < 0.7]
        
        if role in [RoleType.GM, RoleType.DEPT_MANAGER]:
            metrics = [
                ReportMetric("avg_utilization", "平均负荷率", f"{avg_utilization*100:.0f}", "%",
                           target=85, status="good" if 0.7 <= avg_utilization <= 1.0 else "warning"),
                ReportMetric("total_users", "人员总数", len(users), "人"),
                ReportMetric("overloaded", "超负荷人员", len(overloaded), "人",
                           status="warning" if overloaded else "good"),
                ReportMetric("underloaded", "低负荷人员", len(underloaded), "人"),
            ]
            
            sections.append(ReportSection(
                id="workload_heatmap",
                title="负荷热力图",
                order=1,
                content_type="chart",
                content={"type": "heatmap", "data": users},
                importance="high"
            ))
            
            for user in overloaded:
                alerts.append(ReportAlert(
                    id=f"WL-{user['id']}",
                    level=RiskLevel.HIGH if user['utilization'] > 1.2 else RiskLevel.MEDIUM,
                    title=f"{user['name']}负荷过高",
                    description=f"当前负荷率{user['utilization']*100:.0f}%",
                    affected_items=[user['name']],
                    suggested_actions=["调整任务分配", "考虑增加人手", "评估任务优先级"],
                    owner=user.get('dept', '')
                ))
        
        return GeneratedReport(
            id=f"WL-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            title=self._generate_title(ReportType.WORKLOAD_ANALYSIS, role, config),
            subtitle="负荷分析报表",
            report_type=ReportType.WORKLOAD_ANALYSIS,
            period=ReportPeriod.WEEKLY,
            generated_at=datetime.now(),
            generated_for=role,
            scope_description=self._get_scope_description(config),
            sections=sections,
            metrics=metrics,
            alerts=alerts,
            recommendations=[],
        )
    
    def _generate_risk_report(self, role: RoleType, config: RoleConfig, **kwargs) -> GeneratedReport:
        """生成风险报告"""
        alerts = kwargs.get('alerts', [])
        projects = kwargs.get('projects', [])
        
        # 根据角色风险偏好过滤
        filtered_alerts = [a for a in alerts if self._should_show_alert(a, role, config)]
        
        metrics = [
            ReportMetric("total_risks", "风险总数", len(filtered_alerts), "项"),
            ReportMetric("high_risks", "高风险", len([a for a in filtered_alerts if a['level'] == 'high']), "项",
                       status="critical" if any(a['level'] == 'high' for a in filtered_alerts) else "good"),
            ReportMetric("medium_risks", "中风险", len([a for a in filtered_alerts if a['level'] == 'medium']), "项"),
            ReportMetric("low_risks", "低风险", len([a for a in filtered_alerts if a['level'] == 'low']), "项"),
        ]
        
        report_alerts = [
            ReportAlert(
                id=str(a['id']),
                level=RiskLevel(a['level']),
                title=a['title'],
                description=a['description'],
                affected_items=[],
                suggested_actions=self._generate_actions(a, role),
                owner=""
            )
            for a in filtered_alerts
        ]
        
        return GeneratedReport(
            id=f"RISK-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            title=self._generate_title(ReportType.RISK_REPORT, role, config),
            subtitle="风险报告",
            report_type=ReportType.RISK_REPORT,
            period=ReportPeriod.WEEKLY,
            generated_at=datetime.now(),
            generated_for=role,
            scope_description=self._get_scope_description(config),
            sections=[],
            metrics=metrics,
            alerts=report_alerts,
            recommendations=[],
        )
    
    # === 辅助方法 ===
    
    def _generate_title(self, report_type: ReportType, role: RoleType, config: RoleConfig) -> str:
        """生成报表标题"""
        type_names = {
            ReportType.PROJECT_WEEKLY: "项目周报",
            ReportType.PROJECT_MONTHLY: "项目月报",
            ReportType.DEPT_WEEKLY: "部门周报",
            ReportType.DEPT_MONTHLY: "部门月报",
            ReportType.COMPANY_MONTHLY: "公司月报",
            ReportType.COST_ANALYSIS: "成本分析",
            ReportType.WORKLOAD_ANALYSIS: "负荷分析",
            ReportType.RISK_REPORT: "风险报告",
        }
        
        base_title = type_names.get(report_type, "报表")
        
        # 根据角色调整标题
        if role == RoleType.GM:
            return f"经营{base_title}"
        elif role == RoleType.FINANCE:
            return f"财务{base_title}"
        elif role == RoleType.ENGINEER:
            return f"个人{base_title}"
        
        return base_title
    
    def _get_scope_description(self, config: RoleConfig) -> str:
        """获取范围描述"""
        scope_map = {
            "company": "全公司",
            "department": "本部门",
            "project": "所负责项目",
            "personal": "个人"
        }
        return scope_map.get(config.data_scope, "全部")
    
    def _should_show_alert(self, alert: Dict, role: RoleType, config: RoleConfig) -> bool:
        """判断是否应该显示预警"""
        level = alert.get('level', 'low')
        thresholds = config.risk_thresholds
        
        # 高风险对所有角色可见
        if level == 'high' or level == 'critical':
            return True
        
        # 中风险对管理层可见
        if level == 'medium' and role in [RoleType.GM, RoleType.DEPT_MANAGER, RoleType.PM]:
            return True
        
        # 低风险仅对直接相关角色可见
        if level == 'low' and role in [RoleType.PM, RoleType.TE]:
            return True
        
        return False
    
    def _generate_actions(self, alert: Dict, role: RoleType) -> List[str]:
        """根据角色生成建议行动"""
        alert_type = alert.get('type', '')
        
        if role == RoleType.GM:
            return ["安排专项会议讨论", "评估资源调配方案", "跟进整改进展"]
        elif role == RoleType.PM:
            return ["分析根本原因", "制定纠偏措施", "更新项目计划", "及时向上汇报"]
        elif role == RoleType.DEPT_MANAGER:
            return ["调整人员分配", "评估优先级", "协调跨部门资源"]
        else:
            return ["及时处理", "向上级反馈"]
    
    def _generate_executive_summary(self, projects: List[Dict], role: RoleType) -> str:
        """生成执行摘要"""
        active = len([p for p in projects if p['status'] == 'active'])
        healthy = len([p for p in projects if p.get('health') == 'good'])
        
        if role == RoleType.GM:
            return f"""
本周项目整体运行平稳。共有 {active} 个项目进行中，其中 {healthy} 个项目健康状态良好。
重点关注：YY产线改造项目进度滞后，建议本周安排专题讨论。
建议行动：1) 评估YY项目资源配置；2) 跟进ZZ项目交付准备。
"""
        elif role == RoleType.PM:
            return f"""
本周完成主要任务3项，新增任务2项。里程碑进展符合预期。
存在问题：电气设计资源紧张，建议协调增援。
下周计划：完成软件框架开发，启动联调测试。
"""
        return "报表摘要"
    
    def _generate_task_table(self, tasks: List[Dict]) -> List[Dict]:
        """生成任务表格数据"""
        return [
            {
                "name": t['name'],
                "owner": t.get('owner', ''),
                "status": t.get('status', ''),
                "progress": t.get('progress', 0)
            }
            for t in tasks
        ]
    
    def _generate_cost_table(self, projects: List[Dict]) -> List[Dict]:
        """生成成本表格数据"""
        return [
            {
                "project": p['name'],
                "budget": p['budget'],
                "actual": p['actual_cost'],
                "variance": (p['actual_cost'] - p['budget']) / p['budget'] * 100 if p['budget'] > 0 else 0
            }
            for p in projects
        ]
    
    def _generate_recommendations(self, projects: List[Dict], tasks: List[Dict], 
                                  alerts: List[Dict], role: RoleType) -> List[ReportRecommendation]:
        """生成建议"""
        recommendations = []
        
        # 基于数据分析生成建议
        if any(a['level'] == 'high' for a in alerts):
            recommendations.append(ReportRecommendation(
                id="REC-001",
                category="风险管理",
                title="建议召开风险专项会议",
                description="当前存在高风险预警，建议尽快组织相关人员讨论应对方案。",
                impact="high",
                effort="low",
                priority_score=9.0
            ))
        
        # 根据项目进度生成建议
        delayed_projects = [p for p in projects if p.get('health') == 'warning']
        if delayed_projects:
            recommendations.append(ReportRecommendation(
                id="REC-002",
                category="进度管理",
                title="关注进度滞后项目",
                description=f"有{len(delayed_projects)}个项目进度滞后，建议分析原因并制定赶工计划。",
                impact="high",
                effort="medium",
                priority_score=8.5
            ))
        
        return recommendations


# ==================== API接口 ====================

def create_report_generator(data_provider: DataProvider = None) -> ReportGenerator:
    """创建报表生成器实例"""
    if data_provider is None:
        data_provider = MockDataProvider()
    return ReportGenerator(data_provider)


def generate_report_for_role(
    role: str,
    report_type: str,
    period: str = "weekly",
    scope_id: int = None
) -> Dict:
    """
    为指定角色生成报表
    
    Args:
        role: 角色代码 (gm/dept_manager/pm/te/engineer/pmc/finance/qa)
        report_type: 报表类型
        period: 周期 (daily/weekly/monthly/quarterly)
        scope_id: 作用域ID
    
    Returns:
        报表数据字典
    """
    generator = create_report_generator()
    
    try:
        role_type = RoleType(role)
        rpt_type = ReportType(report_type)
        prd = ReportPeriod(period)
    except ValueError as e:
        return {"error": str(e)}
    
    report = generator.generate_report(
        report_type=rpt_type,
        role=role_type,
        period=prd,
        scope_id=scope_id
    )
    
    return report.to_dict()


# ==================== 测试 ====================

if __name__ == "__main__":
    # 测试不同角色生成报表
    generator = create_report_generator()
    
    print("=" * 60)
    print("测试多角色报表生成")
    print("=" * 60)
    
    roles_to_test = [RoleType.GM, RoleType.PM, RoleType.ENGINEER]
    
    for role in roles_to_test:
        print(f"\n{'='*40}")
        print(f"角色: {ROLE_CONFIGS[role].display_name}")
        print(f"关注领域: {', '.join(ROLE_CONFIGS[role].focus_areas)}")
        print(f"{'='*40}")
        
        report = generator.generate_report(
            report_type=ReportType.PROJECT_WEEKLY,
            role=role
        )
        
        print(f"报表标题: {report.title}")
        print(f"核心指标数: {len(report.metrics)}")
        for metric in report.metrics:
            print(f"  - {metric.name}: {metric.value}{metric.unit}")
        print(f"预警数量: {len(report.alerts)}")
        print(f"建议数量: {len(report.recommendations)}")
