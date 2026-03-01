"""
统一任务中心服务
聚合所有类型任务，提供统一的任务管理接口

任务来源：
1. 项目WBS任务 - 项目分解产生
2. 岗位职责任务 - 定期自动生成
3. 流程待办任务 - 工作流推送
4. 转办协作任务 - 同事委托
5. 遗留历史任务 - 未完成累积
6. 预警跟踪任务 - 预警系统生成
7. 个人自建任务 - 自己创建
8. 临时指派任务 - 领导安排
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum
from datetime import datetime, date, timedelta


class TaskType(Enum):
    """任务类型"""
    JOB_DUTY = "job_duty"           # 岗位职责
    PROJECT_WBS = "project_wbs"     # 项目WBS
    WORKFLOW = "workflow"           # 流程待办
    TRANSFER = "transfer"           # 转办任务
    LEGACY = "legacy"               # 遗留任务
    ALERT = "alert"                 # 预警任务
    PERSONAL = "personal"           # 个人自建
    ASSIGNED = "assigned"           # 临时指派


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"             # 待接收
    ACCEPTED = "accepted"           # 已接收
    IN_PROGRESS = "in_progress"     # 进行中
    PAUSED = "paused"               # 已暂停
    SUBMITTED = "submitted"         # 已提交(待验收)
    APPROVED = "approved"           # 已通过
    REJECTED = "rejected"           # 已驳回
    COMPLETED = "completed"         # 已完成
    CANCELLED = "cancelled"         # 已取消


class TaskPriority(Enum):
    """优先级"""
    URGENT = "urgent"       # 紧急
    HIGH = "high"           # 高
    MEDIUM = "medium"       # 中
    LOW = "low"             # 低


class RecurrenceFrequency(Enum):
    """周期频率"""
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


@dataclass
class TaskSource:
    """任务来源"""
    source_type: str        # project/workflow/job_duty/manual/system
    source_id: Optional[int]
    source_name: str
    source_url: Optional[str] = None


@dataclass
class TaskDeliverable:
    """交付物"""
    name: str
    type: str               # document/design/code/report
    required: bool = True
    uploaded: bool = False
    file_url: Optional[str] = None


@dataclass 
class UnifiedTask:
    """统一任务模型"""
    id: int
    task_code: str
    title: str
    description: Optional[str]
    task_type: TaskType
    
    # 来源
    source: TaskSource
    parent_task_id: Optional[int] = None
    
    # 项目关联
    project_id: Optional[int] = None
    project_code: Optional[str] = None
    project_name: Optional[str] = None
    project_level: Optional[str] = None
    wbs_code: Optional[str] = None
    
    # 人员
    assignee_id: int = 0
    assignee_name: str = ""
    assigner_id: Optional[int] = None
    assigner_name: Optional[str] = None
    
    # 时间
    plan_start_date: Optional[date] = None
    plan_end_date: Optional[date] = None
    actual_start_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    deadline: Optional[datetime] = None
    
    # 工时
    estimated_hours: float = 0
    actual_hours: float = 0
    
    # 状态
    status: TaskStatus = TaskStatus.PENDING
    progress: int = 0
    priority: TaskPriority = TaskPriority.MEDIUM
    is_urgent: bool = False
    
    # 周期性
    is_recurring: bool = False
    recurrence_rule: Optional[str] = None
    
    # 转办
    is_transferred: bool = False
    transfer_from_id: Optional[int] = None
    transfer_from_name: Optional[str] = None
    transfer_reason: Optional[str] = None
    transfer_time: Optional[datetime] = None
    
    # 交付物
    deliverables: List[TaskDeliverable] = field(default_factory=list)
    
    # 标签
    tags: List[str] = field(default_factory=list)
    category: Optional[str] = None
    
    # 时间戳
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @property
    def is_overdue(self) -> bool:
        """是否逾期"""
        if not self.deadline:
            return False
        return datetime.now() > self.deadline and self.status not in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]
    
    @property
    def is_due_today(self) -> bool:
        """是否今日到期"""
        if not self.deadline:
            return False
        return self.deadline.date() == date.today()
    
    @property
    def is_due_this_week(self) -> bool:
        """是否本周到期"""
        if not self.deadline:
            return False
        today = date.today()
        week_end = today + timedelta(days=(6 - today.weekday()))
        return today <= self.deadline.date() <= week_end
    
    @property
    def hours_until_deadline(self) -> Optional[float]:
        """距离截止还有多少小时"""
        if not self.deadline:
            return None
        delta = self.deadline - datetime.now()
        return delta.total_seconds() / 3600
    
    @property
    def type_label(self) -> str:
        """任务类型标签"""
        labels = {
            TaskType.JOB_DUTY: "岗位职责",
            TaskType.PROJECT_WBS: "项目任务",
            TaskType.WORKFLOW: "流程待办",
            TaskType.TRANSFER: "转办任务",
            TaskType.LEGACY: "遗留任务",
            TaskType.ALERT: "预警任务",
            TaskType.PERSONAL: "个人任务",
            TaskType.ASSIGNED: "临时指派"
        }
        return labels.get(self.task_type, "其他")
    
    @property
    def status_label(self) -> str:
        """状态标签"""
        labels = {
            TaskStatus.PENDING: "待接收",
            TaskStatus.ACCEPTED: "已接收",
            TaskStatus.IN_PROGRESS: "进行中",
            TaskStatus.PAUSED: "已暂停",
            TaskStatus.SUBMITTED: "待验收",
            TaskStatus.APPROVED: "已通过",
            TaskStatus.REJECTED: "已驳回",
            TaskStatus.COMPLETED: "已完成",
            TaskStatus.CANCELLED: "已取消"
        }
        return labels.get(self.status, "未知")
    
    @property
    def priority_label(self) -> str:
        """优先级标签"""
        labels = {
            TaskPriority.URGENT: "紧急",
            TaskPriority.HIGH: "高",
            TaskPriority.MEDIUM: "中",
            TaskPriority.LOW: "低"
        }
        return labels.get(self.priority, "中")
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "id": self.id,
            "task_code": self.task_code,
            "title": self.title,
            "description": self.description,
            "task_type": self.task_type.value,
            "type_label": self.type_label,
            "source": {
                "type": self.source.source_type,
                "id": self.source.source_id,
                "name": self.source.source_name,
                "url": self.source.source_url
            },
            "project": {
                "id": self.project_id,
                "code": self.project_code,
                "name": self.project_name,
                "level": self.project_level,
                "wbs_code": self.wbs_code
            } if self.project_id else None,
            "assignee": {
                "id": self.assignee_id,
                "name": self.assignee_name
            },
            "assigner": {
                "id": self.assigner_id,
                "name": self.assigner_name
            } if self.assigner_id else None,
            "schedule": {
                "plan_start": self.plan_start_date.isoformat() if self.plan_start_date else None,
                "plan_end": self.plan_end_date.isoformat() if self.plan_end_date else None,
                "deadline": self.deadline.isoformat() if self.deadline else None,
                "actual_start": self.actual_start_date.isoformat() if self.actual_start_date else None,
                "actual_end": self.actual_end_date.isoformat() if self.actual_end_date else None
            },
            "hours": {
                "estimated": self.estimated_hours,
                "actual": self.actual_hours
            },
            "status": self.status.value,
            "status_label": self.status_label,
            "progress": self.progress,
            "priority": self.priority.value,
            "priority_label": self.priority_label,
            "is_urgent": self.is_urgent,
            "is_overdue": self.is_overdue,
            "is_due_today": self.is_due_today,
            "is_due_this_week": self.is_due_this_week,
            "hours_until_deadline": self.hours_until_deadline,
            "is_recurring": self.is_recurring,
            "transfer": {
                "is_transferred": self.is_transferred,
                "from_id": self.transfer_from_id,
                "from_name": self.transfer_from_name,
                "reason": self.transfer_reason,
                "time": self.transfer_time.isoformat() if self.transfer_time else None
            } if self.is_transferred else None,
            "deliverables": [
                {"name": d.name, "type": d.type, "required": d.required, "uploaded": d.uploaded}
                for d in self.deliverables
            ],
            "tags": self.tags,
            "category": self.category,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


@dataclass
class JobDutyTemplate:
    """岗位职责模板"""
    id: int
    position_id: int
    position_name: str
    department_id: int
    duty_name: str
    duty_description: str
    frequency: RecurrenceFrequency
    day_of_week: Optional[int] = None      # 1-7
    day_of_month: Optional[int] = None     # 1-31
    month_of_year: Optional[int] = None    # 1-12
    auto_generate: bool = True
    generate_before_days: int = 3
    deadline_offset_days: int = 0
    default_priority: TaskPriority = TaskPriority.MEDIUM
    estimated_hours: float = 0
    is_active: bool = True


@dataclass
class TaskStatistics:
    """任务统计"""
    total: int = 0
    pending: int = 0
    in_progress: int = 0
    completed: int = 0
    overdue: int = 0
    due_today: int = 0
    due_this_week: int = 0
    urgent: int = 0
    
    by_type: Dict[str, int] = field(default_factory=dict)
    by_project: Dict[str, int] = field(default_factory=dict)
    by_priority: Dict[str, int] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "total": self.total,
            "pending": self.pending,
            "in_progress": self.in_progress,
            "completed": self.completed,
            "overdue": self.overdue,
            "due_today": self.due_today,
            "due_this_week": self.due_this_week,
            "urgent": self.urgent,
            "by_type": self.by_type,
            "by_project": self.by_project,
            "by_priority": self.by_priority
        }


class TaskCenterService:
    """任务中心服务"""
    
    def __init__(self):
        pass
    
    def get_my_tasks(
        self,
        user_id: int,
        task_type: Optional[TaskType] = None,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        project_id: Optional[int] = None,
        is_overdue: Optional[bool] = None,
        is_due_today: Optional[bool] = None,
        keyword: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "smart"
    ) -> Dict:
        """
        获取我的所有任务
        
        聚合来源：
        1. 项目WBS任务
        2. 岗位职责任务
        3. 流程待办
        4. 转办任务
        5. 遗留任务
        6. 预警任务
        7. 个人自建
        8. 临时指派
        """
        all_tasks = []
        
        # 1. 获取项目WBS任务
        project_tasks = self._get_project_tasks(user_id)
        all_tasks.extend(project_tasks)
        
        # 2. 生成岗位职责任务
        job_duty_tasks = self._generate_job_duty_tasks(user_id)
        all_tasks.extend(job_duty_tasks)
        
        # 3. 获取流程待办
        workflow_tasks = self._get_workflow_tasks(user_id)
        all_tasks.extend(workflow_tasks)
        
        # 4. 获取转办任务
        transfer_tasks = self._get_transfer_tasks(user_id)
        all_tasks.extend(transfer_tasks)
        
        # 5. 获取遗留任务
        legacy_tasks = self._get_legacy_tasks(user_id)
        all_tasks.extend(legacy_tasks)
        
        # 6. 获取预警任务
        alert_tasks = self._get_alert_tasks(user_id)
        all_tasks.extend(alert_tasks)
        
        # 7. 获取个人自建
        personal_tasks = self._get_personal_tasks(user_id)
        all_tasks.extend(personal_tasks)
        
        # 8. 获取临时指派
        assigned_tasks = self._get_assigned_tasks(user_id)
        all_tasks.extend(assigned_tasks)
        
        # 应用筛选
        filtered_tasks = self._apply_filters(
            all_tasks, task_type, status, priority, 
            project_id, is_overdue, is_due_today, keyword
        )
        
        # 排序
        sorted_tasks = self._sort_tasks(filtered_tasks, sort_by)
        
        # 分页
        total = len(sorted_tasks)
        start = (page - 1) * page_size
        end = start + page_size
        paged_tasks = sorted_tasks[start:end]
        
        return {
            "tasks": [t.to_dict() for t in paged_tasks],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    
    def get_task_statistics(self, user_id: int) -> TaskStatistics:
        """获取任务统计"""
        all_tasks = []
        
        # 聚合所有任务
        all_tasks.extend(self._get_project_tasks(user_id))
        all_tasks.extend(self._generate_job_duty_tasks(user_id))
        all_tasks.extend(self._get_workflow_tasks(user_id))
        all_tasks.extend(self._get_transfer_tasks(user_id))
        all_tasks.extend(self._get_legacy_tasks(user_id))
        all_tasks.extend(self._get_alert_tasks(user_id))
        all_tasks.extend(self._get_personal_tasks(user_id))
        all_tasks.extend(self._get_assigned_tasks(user_id))
        
        # 只统计未完成的
        active_tasks = [t for t in all_tasks if t.status not in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]]
        
        stats = TaskStatistics()
        stats.total = len(active_tasks)
        
        for task in active_tasks:
            # 状态统计
            if task.status == TaskStatus.PENDING:
                stats.pending += 1
            elif task.status == TaskStatus.IN_PROGRESS:
                stats.in_progress += 1
            
            # 时间统计
            if task.is_overdue:
                stats.overdue += 1
            if task.is_due_today:
                stats.due_today += 1
            if task.is_due_this_week:
                stats.due_this_week += 1
            if task.is_urgent:
                stats.urgent += 1
            
            # 类型统计
            type_key = task.task_type.value
            stats.by_type[type_key] = stats.by_type.get(type_key, 0) + 1
            
            # 项目统计
            if task.project_name:
                stats.by_project[task.project_name] = stats.by_project.get(task.project_name, 0) + 1
            
            # 优先级统计
            priority_key = task.priority.value
            stats.by_priority[priority_key] = stats.by_priority.get(priority_key, 0) + 1
        
        return stats
    
    def get_today_tasks(self, user_id: int) -> List[UnifiedTask]:
        """获取今日任务"""
        result = self.get_my_tasks(user_id, is_due_today=True, page_size=100)
        return [self._dict_to_task(t) for t in result['tasks']]
    
    def get_urgent_tasks(self, user_id: int) -> List[UnifiedTask]:
        """获取紧急任务"""
        result = self.get_my_tasks(user_id, page_size=100)
        tasks = [self._dict_to_task(t) for t in result['tasks']]
        return [t for t in tasks if t.is_urgent or t.is_overdue]
    
    def get_overdue_tasks(self, user_id: int) -> List[UnifiedTask]:
        """获取逾期任务"""
        result = self.get_my_tasks(user_id, is_overdue=True, page_size=100)
        return [self._dict_to_task(t) for t in result['tasks']]
    
    # ==================== 任务来源获取方法 ====================
    
    def _get_project_tasks(self, user_id: int) -> List[UnifiedTask]:
        """获取项目WBS任务"""
        # 模拟数据
        tasks = [
            UnifiedTask(
                id=1001,
                task_code="T2025010001",
                title="机械结构3D建模",
                description="完成XX设备的机械结构三维建模",
                task_type=TaskType.PROJECT_WBS,
                source=TaskSource("project", 1, "XX自动化测试设备"),
                project_id=1,
                project_code="PRJ2025001",
                project_name="XX自动化测试设备",
                project_level="A",
                wbs_code="1.2.3",
                assignee_id=user_id,
                assignee_name="张三",
                assigner_id=100,
                assigner_name="张经理",
                plan_start_date=date(2025, 1, 1),
                plan_end_date=date(2025, 1, 10),
                deadline=datetime(2025, 1, 5, 18, 0),
                estimated_hours=40,
                actual_hours=24,
                status=TaskStatus.IN_PROGRESS,
                progress=60,
                priority=TaskPriority.HIGH,
                deliverables=[
                    TaskDeliverable("结构3D模型", "design", True, False),
                    TaskDeliverable("BOM清单", "document", True, False)
                ],
                created_at=datetime(2025, 1, 1, 9, 0)
            ),
            UnifiedTask(
                id=1002,
                task_code="T2025010002",
                title="电气原理图设计",
                description="完成控制系统电气原理图",
                task_type=TaskType.PROJECT_WBS,
                source=TaskSource("project", 1, "XX自动化测试设备"),
                project_id=1,
                project_code="PRJ2025001",
                project_name="XX自动化测试设备",
                project_level="A",
                wbs_code="2.1.1",
                assignee_id=user_id,
                assignee_name="张三",
                assigner_id=100,
                assigner_name="张经理",
                deadline=datetime(2025, 1, 8, 18, 0),
                estimated_hours=32,
                actual_hours=0,
                status=TaskStatus.PENDING,
                priority=TaskPriority.MEDIUM,
                created_at=datetime(2025, 1, 2, 9, 0)
            ),
            UnifiedTask(
                id=1003,
                task_code="T2025010003",
                title="YY产线PLC程序开发",
                description="编写产线控制程序",
                task_type=TaskType.PROJECT_WBS,
                source=TaskSource("project", 2, "YY产线改造"),
                project_id=2,
                project_code="PRJ2025002",
                project_name="YY产线改造",
                project_level="B",
                wbs_code="3.1.2",
                assignee_id=user_id,
                assignee_name="张三",
                deadline=datetime(2025, 1, 15, 18, 0),
                estimated_hours=60,
                actual_hours=20,
                status=TaskStatus.IN_PROGRESS,
                progress=35,
                priority=TaskPriority.MEDIUM,
                created_at=datetime(2024, 12, 20, 9, 0)
            )
        ]
        return tasks
    
    def _generate_job_duty_tasks(self, user_id: int) -> List[UnifiedTask]:
        """生成岗位职责任务"""
        today = date.today()
        tasks = []
        
        # 模拟：周报任务（每周五）
        if today.weekday() == 4:  # 周五
            tasks.append(UnifiedTask(
                id=2001,
                task_code="JD2025010001",
                title="提交本周周报",
                description="总结本周工作进展，填写周报表",
                task_type=TaskType.JOB_DUTY,
                source=TaskSource("job_duty", 1, "工程师岗位职责"),
                assignee_id=user_id,
                assignee_name="张三",
                deadline=datetime.combine(today, datetime.strptime("18:00", "%H:%M").time()),
                estimated_hours=1,
                status=TaskStatus.PENDING,
                priority=TaskPriority.MEDIUM,
                is_recurring=True,
                recurrence_rule="FREQ=WEEKLY;BYDAY=FR",
                tags=["周报", "定期"],
                created_at=datetime.now()
            ))
        
        # 模拟：月度设备检查（每月1号）
        if today.day == 1:
            tasks.append(UnifiedTask(
                id=2002,
                task_code="JD2025010002",
                title="月度设备巡检",
                description="对负责区域的设备进行月度检查",
                task_type=TaskType.JOB_DUTY,
                source=TaskSource("job_duty", 2, "工程师岗位职责"),
                assignee_id=user_id,
                assignee_name="张三",
                deadline=datetime.combine(today + timedelta(days=2), datetime.strptime("18:00", "%H:%M").time()),
                estimated_hours=4,
                status=TaskStatus.PENDING,
                priority=TaskPriority.MEDIUM,
                is_recurring=True,
                recurrence_rule="FREQ=MONTHLY;BYMONTHDAY=1",
                tags=["巡检", "定期"],
                created_at=datetime.now()
            ))
        
        return tasks
    
    def _get_workflow_tasks(self, user_id: int) -> List[UnifiedTask]:
        """获取流程待办任务"""
        tasks = [
            UnifiedTask(
                id=3001,
                task_code="WF2025010001",
                title="图纸评审 - XX设备机械图纸",
                description="请评审并签字确认机械结构图纸",
                task_type=TaskType.WORKFLOW,
                source=TaskSource("workflow", 101, "图纸评审流程", "/workflow/101"),
                project_id=1,
                project_name="XX自动化测试设备",
                assignee_id=user_id,
                assignee_name="张三",
                assigner_id=102,
                assigner_name="李工",
                deadline=datetime(2025, 1, 4, 18, 0),
                status=TaskStatus.PENDING,
                priority=TaskPriority.HIGH,
                tags=["评审", "待签字"],
                created_at=datetime(2025, 1, 3, 10, 0)
            )
        ]
        return tasks
    
    def _get_transfer_tasks(self, user_id: int) -> List[UnifiedTask]:
        """获取转办任务"""
        tasks = [
            UnifiedTask(
                id=4001,
                task_code="TR2025010001",
                title="协助调试XX设备",
                description="老王出差，请帮忙调试设备传感器部分",
                task_type=TaskType.TRANSFER,
                source=TaskSource("transfer", 4001, "王工转办"),
                project_id=1,
                project_name="XX自动化测试设备",
                assignee_id=user_id,
                assignee_name="张三",
                deadline=datetime(2025, 1, 3, 17, 0),
                status=TaskStatus.IN_PROGRESS,
                progress=50,
                priority=TaskPriority.HIGH,
                is_transferred=True,
                transfer_from_id=103,
                transfer_from_name="王工",
                transfer_reason="出差无法处理，请帮忙跟进",
                transfer_time=datetime(2025, 1, 2, 14, 0),
                created_at=datetime(2025, 1, 2, 14, 0)
            )
        ]
        return tasks
    
    def _get_legacy_tasks(self, user_id: int) -> List[UnifiedTask]:
        """获取遗留任务"""
        tasks = [
            UnifiedTask(
                id=5001,
                task_code="LG2024120001",
                title="整理ZZ项目技术文档",
                description="ZZ项目已交付，需整理归档技术文档",
                task_type=TaskType.LEGACY,
                source=TaskSource("project", 3, "ZZ检测系统"),
                project_id=3,
                project_name="ZZ检测系统",
                assignee_id=user_id,
                assignee_name="张三",
                status=TaskStatus.IN_PROGRESS,
                progress=30,
                priority=TaskPriority.LOW,
                tags=["文档", "归档"],
                created_at=datetime(2024, 12, 15, 9, 0)
            )
        ]
        return tasks
    
    def _get_alert_tasks(self, user_id: int) -> List[UnifiedTask]:
        """获取预警任务"""
        tasks = [
            UnifiedTask(
                id=6001,
                task_code="AL2025010001",
                title="【预警】YY项目进度落后需加快",
                description="YY项目当前进度落后计划15%，请加快推进",
                task_type=TaskType.ALERT,
                source=TaskSource("alert", 201, "进度预警"),
                project_id=2,
                project_name="YY产线改造",
                assignee_id=user_id,
                assignee_name="张三",
                status=TaskStatus.IN_PROGRESS,
                priority=TaskPriority.URGENT,
                is_urgent=True,
                tags=["预警", "进度"],
                created_at=datetime(2025, 1, 2, 8, 0)
            )
        ]
        return tasks
    
    def _get_personal_tasks(self, user_id: int) -> List[UnifiedTask]:
        """获取个人自建任务"""
        tasks = [
            UnifiedTask(
                id=7001,
                task_code="PS2025010001",
                title="学习西门子PLC编程",
                description="完成在线课程第5-8章节",
                task_type=TaskType.PERSONAL,
                source=TaskSource("personal", 7001, "个人学习"),
                assignee_id=user_id,
                assignee_name="张三",
                deadline=datetime(2025, 1, 10, 23, 59),
                status=TaskStatus.IN_PROGRESS,
                progress=40,
                priority=TaskPriority.LOW,
                tags=["学习", "提升"],
                created_at=datetime(2025, 1, 1, 20, 0)
            )
        ]
        return tasks
    
    def _get_assigned_tasks(self, user_id: int) -> List[UnifiedTask]:
        """获取临时指派任务"""
        tasks = [
            UnifiedTask(
                id=8001,
                task_code="AS2025010001",
                title="准备客户演示材料",
                description="准备XX设备的客户演示PPT和视频",
                task_type=TaskType.ASSIGNED,
                source=TaskSource("assigned", 8001, "张经理指派"),
                project_id=1,
                project_name="XX自动化测试设备",
                assignee_id=user_id,
                assignee_name="张三",
                assigner_id=100,
                assigner_name="张经理",
                deadline=datetime(2025, 1, 6, 12, 0),
                status=TaskStatus.PENDING,
                priority=TaskPriority.HIGH,
                is_urgent=True,
                created_at=datetime(2025, 1, 3, 9, 0)
            )
        ]
        return tasks
    
    # ==================== 辅助方法 ====================
    
    def _apply_filters(
        self,
        tasks: List[UnifiedTask],
        task_type: Optional[TaskType],
        status: Optional[TaskStatus],
        priority: Optional[TaskPriority],
        project_id: Optional[int],
        is_overdue: Optional[bool],
        is_due_today: Optional[bool],
        keyword: Optional[str]
    ) -> List[UnifiedTask]:
        """应用筛选条件"""
        result = tasks
        
        if task_type:
            result = [t for t in result if t.task_type == task_type]
        
        if status:
            result = [t for t in result if t.status == status]
        else:
            # 默认不显示已完成和已取消
            result = [t for t in result if t.status not in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]]
        
        if priority:
            result = [t for t in result if t.priority == priority]
        
        if project_id:
            result = [t for t in result if t.project_id == project_id]
        
        if is_overdue:
            result = [t for t in result if t.is_overdue]
        
        if is_due_today:
            result = [t for t in result if t.is_due_today]
        
        if keyword:
            keyword_lower = keyword.lower()
            result = [t for t in result if 
                      keyword_lower in t.title.lower() or 
                      (t.description and keyword_lower in t.description.lower()) or
                      (t.project_name and keyword_lower in t.project_name.lower())]
        
        return result
    
    def _sort_tasks(self, tasks: List[UnifiedTask], sort_by: str) -> List[UnifiedTask]:
        """排序任务"""
        if sort_by == "smart":
            return self._smart_sort(tasks)
        elif sort_by == "deadline":
            return sorted(tasks, key=lambda t: (t.deadline or datetime.max, -self._get_priority_score(t)))
        elif sort_by == "priority":
            return sorted(tasks, key=lambda t: -self._get_priority_score(t))
        elif sort_by == "created":
            return sorted(tasks, key=lambda t: t.created_at or datetime.min, reverse=True)
        else:
            return tasks
    
    def _smart_sort(self, tasks: List[UnifiedTask]) -> List[UnifiedTask]:
        """智能排序"""
        def get_score(task: UnifiedTask) -> float:
            score = 0
            
            # 紧急标记 +1000
            if task.is_urgent:
                score += 1000
            
            # 已逾期 +800
            if task.is_overdue:
                score += 800
            
            # 今日到期 +500
            if task.is_due_today:
                score += 500
            
            # 优先级
            priority_scores = {
                TaskPriority.URGENT: 400,
                TaskPriority.HIGH: 200,
                TaskPriority.MEDIUM: 100,
                TaskPriority.LOW: 0
            }
            score += priority_scores.get(task.priority, 0)
            
            # 距离截止时间
            if task.hours_until_deadline is not None:
                if task.hours_until_deadline < 0:
                    score += 300  # 已逾期
                elif task.hours_until_deadline < 24:
                    score += 200  # 24小时内
                elif task.hours_until_deadline < 72:
                    score += 100  # 3天内
            
            # 流程待办优先
            if task.task_type == TaskType.WORKFLOW:
                score += 50
            
            # 转办任务优先
            if task.task_type == TaskType.TRANSFER:
                score += 30
            
            return score
        
        return sorted(tasks, key=get_score, reverse=True)
    
    def _get_priority_score(self, task: UnifiedTask) -> int:
        """获取优先级分数"""
        scores = {
            TaskPriority.URGENT: 4,
            TaskPriority.HIGH: 3,
            TaskPriority.MEDIUM: 2,
            TaskPriority.LOW: 1
        }
        return scores.get(task.priority, 0)
    
    def _dict_to_task(self, d: Dict) -> UnifiedTask:
        """字典转任务对象（简化版）"""
        # 实际实现需要完整转换
        return UnifiedTask(
            id=d['id'],
            task_code=d['task_code'],
            title=d['title'],
            description=d.get('description'),
            task_type=TaskType(d['task_type']),
            source=TaskSource(
                d['source']['type'],
                d['source']['id'],
                d['source']['name']
            ),
            assignee_id=d['assignee']['id'],
            assignee_name=d['assignee']['name'],
            status=TaskStatus(d['status']),
            priority=TaskPriority(d['priority']),
            is_urgent=d.get('is_urgent', False)
        )


# 工厂方法
def create_task_center_service() -> TaskCenterService:
    return TaskCenterService()


# 测试
if __name__ == "__main__":
    service = create_task_center_service()
    
    print("=" * 60)
    print("获取我的所有任务")
    print("=" * 60)
    
    result = service.get_my_tasks(user_id=1)
    print(f"总数: {result['total']}")
    
    for task in result['tasks'][:5]:
        print(f"[{task['type_label']}] {task['title']} - {task['status_label']}")
        if task.get('is_overdue'):
            print("  ⚠️ 已逾期!")
        if task.get('is_due_today'):
            print("  📅 今日到期")
    
    print("\n" + "=" * 60)
    print("任务统计")
    print("=" * 60)
    
    stats = service.get_task_statistics(user_id=1)
    print(f"待处理: {stats.pending}")
    print(f"进行中: {stats.in_progress}")
    print(f"今日到期: {stats.due_today}")
    print(f"已逾期: {stats.overdue}")
    print(f"紧急: {stats.urgent}")
    print(f"按类型: {stats.by_type}")
