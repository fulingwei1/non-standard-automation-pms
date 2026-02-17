# -*- coding: utf-8 -*-
"""
机台管理服务
包含：编码生成、状态验证、项目聚合计算
"""

from decimal import Decimal
from typing import Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.project import Machine, Project
from app.utils.db_helpers import save_obj


# 阶段优先级映射（数值越小优先级越高，表示越靠前）
STAGE_PRIORITY = {
    "S1": 1, "S2": 2, "S3": 3, "S4": 4, "S5": 5,
    "S6": 6, "S7": 7, "S8": 8, "S9": 9
}

# 健康度优先级映射（H3最严重 > H2警告 > H1正常 > H4完结）
HEALTH_PRIORITY = {
    "H3": 1,  # 阻塞 - 最高优先
    "H2": 2,  # 有风险
    "H1": 3,  # 正常
    "H4": 4,  # 已完结
}

# 有效阶段列表
VALID_STAGES = ["S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9"]
VALID_HEALTH = ["H1", "H2", "H3", "H4"]


class MachineService:
    """机台管理服务"""

    def __init__(self, db: Session):
        self.db = db

    def generate_machine_code(self, project_id: int) -> Tuple[str, int]:
        """
        生成机台编码

        格式：{项目编码}-PN{序号}
        示例：PJ250712001-PN001

        Args:
            project_id: 项目ID

        Returns:
            Tuple[str, int]: (机台编码, 机台序号)
        """
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"项目不存在: {project_id}")

        # 查询项目下最大的机台序号
        max_no = self.db.query(func.max(Machine.machine_no)).filter(
            Machine.project_id == project_id
        ).scalar() or 0

        next_no = max_no + 1
        machine_code = f"{project.project_code}-PN{next_no:03d}"

        return machine_code, next_no

    def validate_stage(self, stage: str) -> bool:
        """验证阶段是否有效"""
        return stage in VALID_STAGES

    def validate_health(self, health: str) -> bool:
        """验证健康度是否有效"""
        return health in VALID_HEALTH

    def validate_stage_transition(
        self, current_stage: str, new_stage: str
    ) -> Tuple[bool, str]:
        """
        验证阶段转移是否合法

        规则：
        - 阶段只能向前推进，不能回退（除非管理员强制）
        - S9是终态，不能再变更

        Args:
            current_stage: 当前阶段
            new_stage: 目标阶段

        Returns:
            Tuple[bool, str]: (是否合法, 错误消息)
        """
        if current_stage not in STAGE_PRIORITY:
            return False, f"无效的当前阶段: {current_stage}"

        if new_stage not in STAGE_PRIORITY:
            return False, f"无效的目标阶段: {new_stage}"

        if current_stage == "S9":
            return False, "S9是终态，无法变更阶段"

        current_priority = STAGE_PRIORITY[current_stage]
        new_priority = STAGE_PRIORITY[new_stage]

        if new_priority < current_priority:
            return False, f"阶段只能向前推进，不能从 {current_stage} 回退到 {new_stage}"

        return True, ""


class ProjectAggregationService:
    """项目聚合计算服务"""

    def __init__(self, db: Session):
        self.db = db

    def calculate_project_progress(self, project_id: int) -> Decimal:
        """
        计算项目进度

        算法：项目进度 = 所有机台进度的平均值
        如果没有机台，返回0

        Args:
            project_id: 项目ID

        Returns:
            Decimal: 项目进度百分比 (0-100)
        """
        result = self.db.query(func.avg(Machine.progress_pct)).filter(
            Machine.project_id == project_id
        ).scalar()

        if result is None:
            return Decimal("0.00")

        return Decimal(str(result)).quantize(Decimal("0.01"))

    def calculate_project_stage(self, project_id: int) -> str:
        """
        计算项目阶段

        算法：项目阶段 = 所有机台中最靠前的阶段
        例如：有机台在S2，有机台在S5，则项目阶段为S2

        Args:
            project_id: 项目ID

        Returns:
            str: 项目阶段 (S1-S9)
        """
        machines = self.db.query(Machine.stage).filter(
            Machine.project_id == project_id
        ).all()

        if not machines:
            return "S1"  # 无机台时默认S1

        stages = [m.stage for m in machines if m.stage in STAGE_PRIORITY]
        if not stages:
            return "S1"

        # 找出优先级最高（数值最小）的阶段
        earliest_stage = min(stages, key=lambda s: STAGE_PRIORITY.get(s, 999))
        return earliest_stage

    def calculate_project_health(self, project_id: int) -> str:
        """
        计算项目健康度

        算法：
        - 如果任一机台为H3（阻塞），项目为H3
        - 如果任一机台为H2（有风险），项目为H2
        - 如果所有机台都是H4（已完结），项目为H4
        - 否则为H1（正常）

        Args:
            project_id: 项目ID

        Returns:
            str: 项目健康度 (H1-H4)
        """
        machines = self.db.query(Machine.health).filter(
            Machine.project_id == project_id
        ).all()

        if not machines:
            return "H1"  # 无机台时默认H1

        health_values = [m.health for m in machines if m.health in HEALTH_PRIORITY]
        if not health_values:
            return "H1"

        # 检查是否有阻塞
        if "H3" in health_values:
            return "H3"

        # 检查是否有风险
        if "H2" in health_values:
            return "H2"

        # 检查是否全部完结
        if all(h == "H4" for h in health_values):
            return "H4"

        return "H1"

    def update_project_aggregation(self, project_id: int) -> Project:
        """
        更新项目的聚合数据（进度、阶段、健康度）

        Args:
            project_id: 项目ID

        Returns:
            Project: 更新后的项目对象
        """
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"项目不存在: {project_id}")

        project.progress_pct = self.calculate_project_progress(project_id)
        project.stage = self.calculate_project_stage(project_id)
        project.health = self.calculate_project_health(project_id)

        save_obj(self.db, project)

        return project

    def get_project_machine_summary(self, project_id: int) -> dict:
        """
        获取项目机台汇总信息

        Args:
            project_id: 项目ID

        Returns:
            dict: 汇总信息
        """
        machines = self.db.query(Machine).filter(
            Machine.project_id == project_id
        ).all()

        if not machines:
            return {
                "total_machines": 0,
                "stage_distribution": {},
                "health_distribution": {},
                "avg_progress": Decimal("0.00"),
                "completed_count": 0,
                "at_risk_count": 0,
                "blocked_count": 0,
            }

        stage_dist = {}
        health_dist = {}
        total_progress = Decimal("0")
        completed = 0
        at_risk = 0
        blocked = 0

        for machine in machines:
            # 阶段分布
            stage_dist[machine.stage] = stage_dist.get(machine.stage, 0) + 1

            # 健康度分布
            health_dist[machine.health] = health_dist.get(machine.health, 0) + 1

            # 进度累加
            total_progress += machine.progress_pct or Decimal("0")

            # 计数
            if machine.stage == "S9":
                completed += 1
            if machine.health == "H2":
                at_risk += 1
            if machine.health == "H3":
                blocked += 1

        return {
            "total_machines": len(machines),
            "stage_distribution": stage_dist,
            "health_distribution": health_dist,
            "avg_progress": (total_progress / len(machines)).quantize(Decimal("0.01")),
            "completed_count": completed,
            "at_risk_count": at_risk,
            "blocked_count": blocked,
        }
