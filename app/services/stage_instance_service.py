# -*- coding: utf-8 -*-
"""
阶段实例服务
处理项目阶段/节点的实例化、状态流转、进度计算
"""

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_
from sqlalchemy.orm import Session, joinedload

from app.models.enums import (
    CompletionMethodEnum,
    NodeTypeEnum,
    StageStatusEnum,
)
from app.models.project import Project
from app.models.stage_instance import (
    ProjectNodeInstance,
    ProjectStageInstance,
)
from app.models.stage_template import (
    NodeDefinition,
    StageDefinition,
    StageTemplate,
)


class StageInstanceService:
    """阶段实例服务类"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== 项目实例化 ====================

    def initialize_project_stages(
        self,
        project_id: int,
        template_id: int,
        start_date: Optional[date] = None,
        adjustments: Optional[Dict[str, Any]] = None,
    ) -> List[ProjectStageInstance]:
        """
        根据模板初始化项目的阶段和节点

        Args:
            project_id: 项目ID
            template_id: 模板ID
            start_date: 项目开始日期（用于计算计划日期）
            adjustments: 调整配置（可跳过某些阶段/节点）
                {
                    "skip_stages": ["STAGE_CODE1", "STAGE_CODE2"],
                    "skip_nodes": ["NODE_CODE1", "NODE_CODE2"],
                    "stage_overrides": {
                        "STAGE_CODE": {"estimated_days": 10, "stage_name": "新名称"}
                    },
                    "node_overrides": {
                        "NODE_CODE": {"estimated_days": 5, "is_required": False}
                    }
                }

        Returns:
            List[ProjectStageInstance]: 创建的阶段实例列表
        """
        # 验证项目存在
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"项目 {project_id} 不存在")

        # 获取模板（包含完整结构）
        template = self.db.query(StageTemplate).options(
            joinedload(StageTemplate.stages).joinedload(StageDefinition.nodes)
        ).filter(StageTemplate.id == template_id).first()

        if not template:
            raise ValueError(f"模板 {template_id} 不存在")

        # 检查项目是否已有阶段实例
        existing_count = self.db.query(ProjectStageInstance).filter(
            ProjectStageInstance.project_id == project_id
        ).count()

        if existing_count > 0:
            raise ValueError(f"项目 {project_id} 已有阶段实例，请先清除")

        adjustments = adjustments or {}
        skip_stages = set(adjustments.get("skip_stages", []))
        skip_nodes = set(adjustments.get("skip_nodes", []))
        stage_overrides = adjustments.get("stage_overrides", {})
        node_overrides = adjustments.get("node_overrides", {})

        # 计算日期
        current_date = start_date or date.today()
        created_stages = []
        node_def_to_instance = {}  # 节点定义ID -> 实例ID 映射（用于依赖转换）

        # 按顺序创建阶段实例
        for stage_def in sorted(template.stages, key=lambda s: s.sequence):
            if stage_def.stage_code in skip_stages:
                continue

            # 应用阶段覆盖
            stage_override = stage_overrides.get(stage_def.stage_code, {})
            estimated_days = stage_override.get("estimated_days", stage_def.estimated_days) or 0

            stage_instance = ProjectStageInstance(
                project_id=project_id,
                stage_definition_id=stage_def.id,
                stage_code=stage_def.stage_code,
                stage_name=stage_override.get("stage_name", stage_def.stage_name),
                sequence=stage_def.sequence,
                status=StageStatusEnum.PENDING.value,
                planned_start_date=current_date,
                planned_end_date=current_date + timedelta(days=estimated_days) if estimated_days else None,
                is_modified=bool(stage_override),
            )
            self.db.add(stage_instance)
            self.db.flush()

            # 创建节点实例
            node_start_date = current_date
            for node_def in sorted(stage_def.nodes, key=lambda n: n.sequence):
                if node_def.node_code in skip_nodes:
                    continue

                # 应用节点覆盖
                node_override = node_overrides.get(node_def.node_code, {})
                node_estimated_days = node_override.get("estimated_days", node_def.estimated_days) or 0

                node_instance = ProjectNodeInstance(
                    project_id=project_id,
                    stage_instance_id=stage_instance.id,
                    node_definition_id=node_def.id,
                    node_code=node_def.node_code,
                    node_name=node_override.get("node_name", node_def.node_name),
                    node_type=node_def.node_type,
                    sequence=node_def.sequence,
                    status=StageStatusEnum.PENDING.value,
                    completion_method=node_def.completion_method,
                    is_required=node_override.get("is_required", node_def.is_required),
                    planned_date=node_start_date + timedelta(days=node_estimated_days) if node_estimated_days else None,
                )
                self.db.add(node_instance)
                self.db.flush()

                node_def_to_instance[node_def.id] = node_instance.id

                # 累加节点工期
                if node_estimated_days:
                    node_start_date = node_start_date + timedelta(days=node_estimated_days)

            # 更新下一阶段的开始日期
            if estimated_days:
                current_date = current_date + timedelta(days=estimated_days)

            created_stages.append(stage_instance)

        # 第二遍：转换节点依赖关系（定义ID -> 实例ID）
        for stage_instance in created_stages:
            for node_instance in stage_instance.nodes:
                if node_instance.node_definition_id:
                    node_def = self.db.query(NodeDefinition).filter(
                        NodeDefinition.id == node_instance.node_definition_id
                    ).first()
                    if node_def and node_def.dependency_node_ids:
                        instance_deps = [
                            node_def_to_instance[def_id]
                            for def_id in node_def.dependency_node_ids
                            if def_id in node_def_to_instance
                        ]
                        if instance_deps:
                            node_instance.dependency_node_instance_ids = instance_deps

        # 更新项目关联
        project.stage_template_id = template_id
        if created_stages:
            project.current_stage_instance_id = created_stages[0].id
            first_stage_nodes = list(created_stages[0].nodes)
            if first_stage_nodes:
                project.current_node_instance_id = first_stage_nodes[0].id

        self.db.flush()
        return created_stages

    def clear_project_stages(self, project_id: int) -> int:
        """
        清除项目的所有阶段实例

        Args:
            project_id: 项目ID

        Returns:
            int: 删除的阶段实例数量
        """
        # 先清除项目的当前阶段引用
        self.db.query(Project).filter(Project.id == project_id).update({
            "stage_template_id": None,
            "current_stage_instance_id": None,
            "current_node_instance_id": None,
        })

        # 删除节点实例（会由 cascade 自动删除，但显式删除更清晰）
        self.db.query(ProjectNodeInstance).filter(
            ProjectNodeInstance.project_id == project_id
        ).delete()

        # 删除阶段实例
        count = self.db.query(ProjectStageInstance).filter(
            ProjectStageInstance.project_id == project_id
        ).delete()

        return count

    # ==================== 状态流转 ====================

    def start_stage(
        self,
        stage_instance_id: int,
        actual_start_date: Optional[date] = None,
    ) -> ProjectStageInstance:
        """
        开始阶段

        Args:
            stage_instance_id: 阶段实例ID
            actual_start_date: 实际开始日期

        Returns:
            ProjectStageInstance: 更新后的阶段实例
        """
        stage = self.db.query(ProjectStageInstance).filter(
            ProjectStageInstance.id == stage_instance_id
        ).first()

        if not stage:
            raise ValueError(f"阶段实例 {stage_instance_id} 不存在")

        if stage.status != StageStatusEnum.PENDING.value:
            raise ValueError(f"阶段当前状态为 {stage.status}，无法开始")

        stage.status = StageStatusEnum.IN_PROGRESS.value
        stage.actual_start_date = actual_start_date or date.today()

        # 更新项目的当前阶段
        self.db.query(Project).filter(
            Project.id == stage.project_id
        ).update({"current_stage_instance_id": stage_instance_id})

        self.db.flush()
        return stage

    def complete_stage(
        self,
        stage_instance_id: int,
        actual_end_date: Optional[date] = None,
        auto_start_next: bool = True,
    ) -> Tuple[ProjectStageInstance, Optional[ProjectStageInstance]]:
        """
        完成阶段

        Args:
            stage_instance_id: 阶段实例ID
            actual_end_date: 实际结束日期
            auto_start_next: 是否自动开始下一阶段

        Returns:
            Tuple[当前阶段, 下一阶段（如有）]
        """
        stage = self.db.query(ProjectStageInstance).filter(
            ProjectStageInstance.id == stage_instance_id
        ).first()

        if not stage:
            raise ValueError(f"阶段实例 {stage_instance_id} 不存在")

        if stage.status != StageStatusEnum.IN_PROGRESS.value:
            raise ValueError(f"阶段当前状态为 {stage.status}，无法完成")

        # 检查是否所有必需节点都已完成
        incomplete_required = self.db.query(ProjectNodeInstance).filter(
            and_(
                ProjectNodeInstance.stage_instance_id == stage_instance_id,
                ProjectNodeInstance.is_required == True,
                ProjectNodeInstance.status.notin_([
                    StageStatusEnum.COMPLETED.value,
                    StageStatusEnum.SKIPPED.value
                ])
            )
        ).count()

        if incomplete_required > 0:
            raise ValueError(f"还有 {incomplete_required} 个必需节点未完成")

        stage.status = StageStatusEnum.COMPLETED.value
        stage.actual_end_date = actual_end_date or date.today()

        # 查找下一阶段
        next_stage = None
        if auto_start_next:
            next_stage = self.db.query(ProjectStageInstance).filter(
                and_(
                    ProjectStageInstance.project_id == stage.project_id,
                    ProjectStageInstance.sequence > stage.sequence,
                    ProjectStageInstance.status == StageStatusEnum.PENDING.value
                )
            ).order_by(ProjectStageInstance.sequence).first()

            if next_stage:
                self.start_stage(next_stage.id)

        self.db.flush()
        return stage, next_stage

    def skip_stage(
        self,
        stage_instance_id: int,
        reason: Optional[str] = None,
    ) -> ProjectStageInstance:
        """
        跳过阶段

        Args:
            stage_instance_id: 阶段实例ID
            reason: 跳过原因

        Returns:
            ProjectStageInstance: 更新后的阶段实例
        """
        stage = self.db.query(ProjectStageInstance).filter(
            ProjectStageInstance.id == stage_instance_id
        ).first()

        if not stage:
            raise ValueError(f"阶段实例 {stage_instance_id} 不存在")

        if stage.status not in [StageStatusEnum.PENDING.value, StageStatusEnum.IN_PROGRESS.value]:
            raise ValueError(f"阶段当前状态为 {stage.status}，无法跳过")

        stage.status = StageStatusEnum.SKIPPED.value
        stage.remark = reason or stage.remark
        stage.is_modified = True

        # 跳过所有未完成的节点
        self.db.query(ProjectNodeInstance).filter(
            and_(
                ProjectNodeInstance.stage_instance_id == stage_instance_id,
                ProjectNodeInstance.status.in_([
                    StageStatusEnum.PENDING.value,
                    StageStatusEnum.IN_PROGRESS.value
                ])
            )
        ).update({"status": StageStatusEnum.SKIPPED.value})

        self.db.flush()
        return stage

    # ==================== 节点操作 ====================

    def start_node(
        self,
        node_instance_id: int,
    ) -> ProjectNodeInstance:
        """开始节点"""
        node = self.db.query(ProjectNodeInstance).filter(
            ProjectNodeInstance.id == node_instance_id
        ).first()

        if not node:
            raise ValueError(f"节点实例 {node_instance_id} 不存在")

        if node.status != StageStatusEnum.PENDING.value:
            raise ValueError(f"节点当前状态为 {node.status}，无法开始")

        # 检查依赖是否满足
        if not self._check_node_dependencies(node):
            raise ValueError("前置依赖节点未完成")

        node.status = StageStatusEnum.IN_PROGRESS.value

        # 更新项目的当前节点
        self.db.query(Project).filter(
            Project.id == node.project_id
        ).update({"current_node_instance_id": node_instance_id})

        # 如果所属阶段还未开始，自动开始阶段
        stage = node.stage_instance
        if stage.status == StageStatusEnum.PENDING.value:
            self.start_stage(stage.id)

        self.db.flush()
        return node

    def complete_node(
        self,
        node_instance_id: int,
        completed_by: Optional[int] = None,
        actual_date: Optional[date] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        approval_record_id: Optional[int] = None,
        remark: Optional[str] = None,
    ) -> ProjectNodeInstance:
        """
        完成节点

        Args:
            node_instance_id: 节点实例ID
            completed_by: 完成人ID
            actual_date: 实际完成日期
            attachments: 附件列表
            approval_record_id: 审批记录ID（审批类节点）
            remark: 备注

        Returns:
            ProjectNodeInstance: 更新后的节点实例
        """
        node = self.db.query(ProjectNodeInstance).filter(
            ProjectNodeInstance.id == node_instance_id
        ).first()

        if not node:
            raise ValueError(f"节点实例 {node_instance_id} 不存在")

        if node.status not in [StageStatusEnum.PENDING.value, StageStatusEnum.IN_PROGRESS.value]:
            raise ValueError(f"节点当前状态为 {node.status}，无法完成")

        # 验证完成条件
        self._validate_node_completion(node, attachments, approval_record_id)

        node.status = StageStatusEnum.COMPLETED.value
        node.completed_by = completed_by
        node.completed_at = datetime.now()
        node.actual_date = actual_date or date.today()

        if attachments:
            node.attachments = attachments
        if approval_record_id:
            node.approval_record_id = approval_record_id
        if remark:
            node.remark = remark

        # 检查是否可以自动完成下一个节点
        self._try_auto_complete_next_nodes(node)

        # 检查阶段是否可以自动完成
        self._check_stage_completion(node.stage_instance_id)

        self.db.flush()
        return node

    def skip_node(
        self,
        node_instance_id: int,
        reason: Optional[str] = None,
    ) -> ProjectNodeInstance:
        """跳过节点"""
        node = self.db.query(ProjectNodeInstance).filter(
            ProjectNodeInstance.id == node_instance_id
        ).first()

        if not node:
            raise ValueError(f"节点实例 {node_instance_id} 不存在")

        if node.status not in [StageStatusEnum.PENDING.value, StageStatusEnum.IN_PROGRESS.value]:
            raise ValueError(f"节点当前状态为 {node.status}，无法跳过")

        node.status = StageStatusEnum.SKIPPED.value
        node.remark = reason or node.remark

        self.db.flush()
        return node

    # ==================== 进度查询 ====================

    def get_project_progress(self, project_id: int) -> Dict[str, Any]:
        """
        获取项目阶段进度

        Returns:
            Dict: {
                "total_stages": 总阶段数,
                "completed_stages": 已完成阶段数,
                "current_stage": 当前阶段信息,
                "total_nodes": 总节点数,
                "completed_nodes": 已完成节点数,
                "progress_pct": 整体进度百分比,
                "stages": [阶段列表]
            }
        """
        stages = self.db.query(ProjectStageInstance).filter(
            ProjectStageInstance.project_id == project_id
        ).options(
            joinedload(ProjectStageInstance.nodes)
        ).order_by(ProjectStageInstance.sequence).all()

        total_stages = len(stages)
        completed_stages = sum(1 for s in stages if s.status == StageStatusEnum.COMPLETED.value)

        total_nodes = 0
        completed_nodes = 0
        current_stage = None

        stage_list = []
        for stage in stages:
            nodes = list(stage.nodes)
            stage_total = len(nodes)
            stage_completed = sum(1 for n in nodes if n.status == StageStatusEnum.COMPLETED.value)

            total_nodes += stage_total
            completed_nodes += stage_completed

            if stage.status == StageStatusEnum.IN_PROGRESS.value:
                current_stage = {
                    "id": stage.id,
                    "stage_code": stage.stage_code,
                    "stage_name": stage.stage_name,
                    "progress_pct": round(stage_completed / stage_total * 100, 1) if stage_total > 0 else 0,
                }

            stage_list.append({
                "id": stage.id,
                "stage_code": stage.stage_code,
                "stage_name": stage.stage_name,
                "status": stage.status,
                "sequence": stage.sequence,
                "total_nodes": stage_total,
                "completed_nodes": stage_completed,
                "progress_pct": round(stage_completed / stage_total * 100, 1) if stage_total > 0 else 0,
                "planned_start_date": stage.planned_start_date.isoformat() if stage.planned_start_date else None,
                "planned_end_date": stage.planned_end_date.isoformat() if stage.planned_end_date else None,
                "actual_start_date": stage.actual_start_date.isoformat() if stage.actual_start_date else None,
                "actual_end_date": stage.actual_end_date.isoformat() if stage.actual_end_date else None,
            })

        return {
            "total_stages": total_stages,
            "completed_stages": completed_stages,
            "current_stage": current_stage,
            "total_nodes": total_nodes,
            "completed_nodes": completed_nodes,
            "progress_pct": round(completed_nodes / total_nodes * 100, 1) if total_nodes > 0 else 0,
            "stages": stage_list,
        }

    def get_stage_detail(self, stage_instance_id: int) -> Dict[str, Any]:
        """获取阶段详情（包含所有节点）"""
        stage = self.db.query(ProjectStageInstance).options(
            joinedload(ProjectStageInstance.nodes)
        ).filter(ProjectStageInstance.id == stage_instance_id).first()

        if not stage:
            return None

        nodes = []
        for node in sorted(stage.nodes, key=lambda n: n.sequence):
            nodes.append({
                "id": node.id,
                "node_code": node.node_code,
                "node_name": node.node_name,
                "node_type": node.node_type,
                "status": node.status,
                "sequence": node.sequence,
                "completion_method": node.completion_method,
                "is_required": node.is_required,
                "planned_date": node.planned_date.isoformat() if node.planned_date else None,
                "actual_date": node.actual_date.isoformat() if node.actual_date else None,
                "completed_by": node.completed_by,
                "completed_at": node.completed_at.isoformat() if node.completed_at else None,
                "attachments": node.attachments,
                "dependency_node_instance_ids": node.dependency_node_instance_ids,
                "can_start": self._check_node_dependencies(node) if node.status == StageStatusEnum.PENDING.value else False,
            })

        return {
            "id": stage.id,
            "project_id": stage.project_id,
            "stage_code": stage.stage_code,
            "stage_name": stage.stage_name,
            "status": stage.status,
            "sequence": stage.sequence,
            "planned_start_date": stage.planned_start_date.isoformat() if stage.planned_start_date else None,
            "planned_end_date": stage.planned_end_date.isoformat() if stage.planned_end_date else None,
            "actual_start_date": stage.actual_start_date.isoformat() if stage.actual_start_date else None,
            "actual_end_date": stage.actual_end_date.isoformat() if stage.actual_end_date else None,
            "is_modified": stage.is_modified,
            "remark": stage.remark,
            "nodes": nodes,
        }

    # ==================== 调整操作 ====================

    def add_custom_node(
        self,
        stage_instance_id: int,
        node_code: str,
        node_name: str,
        node_type: str = NodeTypeEnum.TASK.value,
        completion_method: str = CompletionMethodEnum.MANUAL.value,
        is_required: bool = False,
        planned_date: Optional[date] = None,
        insert_after_node_id: Optional[int] = None,
    ) -> ProjectNodeInstance:
        """
        在阶段中添加自定义节点

        Args:
            stage_instance_id: 阶段实例ID
            node_code: 节点编码
            node_name: 节点名称
            node_type: 节点类型
            completion_method: 完成方式
            is_required: 是否必需
            planned_date: 计划日期
            insert_after_node_id: 插入位置（在此节点之后）

        Returns:
            ProjectNodeInstance: 创建的节点实例
        """
        stage = self.db.query(ProjectStageInstance).filter(
            ProjectStageInstance.id == stage_instance_id
        ).first()

        if not stage:
            raise ValueError(f"阶段实例 {stage_instance_id} 不存在")

        # 确定序号
        if insert_after_node_id:
            after_node = self.db.query(ProjectNodeInstance).filter(
                ProjectNodeInstance.id == insert_after_node_id
            ).first()
            sequence = after_node.sequence + 1 if after_node else 0

            # 后移其他节点
            self.db.query(ProjectNodeInstance).filter(
                and_(
                    ProjectNodeInstance.stage_instance_id == stage_instance_id,
                    ProjectNodeInstance.sequence >= sequence
                )
            ).update({"sequence": ProjectNodeInstance.sequence + 1})
        else:
            # 添加到末尾
            max_seq = self.db.query(ProjectNodeInstance).filter(
                ProjectNodeInstance.stage_instance_id == stage_instance_id
            ).count()
            sequence = max_seq

        node = ProjectNodeInstance(
            project_id=stage.project_id,
            stage_instance_id=stage_instance_id,
            node_code=node_code,
            node_name=node_name,
            node_type=node_type,
            sequence=sequence,
            status=StageStatusEnum.PENDING.value,
            completion_method=completion_method,
            is_required=is_required,
            planned_date=planned_date,
        )
        self.db.add(node)

        # 标记阶段已修改
        stage.is_modified = True

        self.db.flush()
        return node

    def update_node_planned_date(
        self,
        node_instance_id: int,
        planned_date: date,
    ) -> ProjectNodeInstance:
        """更新节点计划日期"""
        node = self.db.query(ProjectNodeInstance).filter(
            ProjectNodeInstance.id == node_instance_id
        ).first()

        if not node:
            raise ValueError(f"节点实例 {node_instance_id} 不存在")

        node.planned_date = planned_date
        self.db.flush()
        return node

    # ==================== 辅助方法 ====================

    def _check_node_dependencies(self, node: ProjectNodeInstance) -> bool:
        """检查节点依赖是否满足"""
        if not node.dependency_node_instance_ids:
            return True

        # 检查所有依赖节点是否已完成
        incomplete = self.db.query(ProjectNodeInstance).filter(
            and_(
                ProjectNodeInstance.id.in_(node.dependency_node_instance_ids),
                ProjectNodeInstance.status.notin_([
                    StageStatusEnum.COMPLETED.value,
                    StageStatusEnum.SKIPPED.value
                ])
            )
        ).count()

        return incomplete == 0

    def _validate_node_completion(
        self,
        node: ProjectNodeInstance,
        attachments: Optional[List[Dict[str, Any]]],
        approval_record_id: Optional[int],
    ) -> None:
        """验证节点完成条件"""
        # 检查依赖
        if not self._check_node_dependencies(node):
            raise ValueError("前置依赖节点未完成")

        # 检查附件要求
        node_def = node.node_definition
        if node_def and node_def.required_attachments:
            if not attachments and not node.attachments:
                raise ValueError("该节点要求上传附件")

        # 检查审批要求
        if node.completion_method == CompletionMethodEnum.APPROVAL.value:
            if not approval_record_id:
                raise ValueError("审批类节点需要关联审批记录")

    def _try_auto_complete_next_nodes(self, completed_node: ProjectNodeInstance) -> None:
        """尝试自动完成依赖于当前节点的自动节点"""
        # 查找依赖于当前节点的自动完成节点
        dependent_nodes = self.db.query(ProjectNodeInstance).filter(
            and_(
                ProjectNodeInstance.stage_instance_id == completed_node.stage_instance_id,
                ProjectNodeInstance.completion_method == CompletionMethodEnum.AUTO.value,
                ProjectNodeInstance.status == StageStatusEnum.PENDING.value
            )
        ).all()

        for node in dependent_nodes:
            if node.dependency_node_instance_ids and completed_node.id in node.dependency_node_instance_ids:
                if self._check_node_dependencies(node):
                    # 检查自动完成条件
                    if self._check_auto_condition(node):
                        node.status = StageStatusEnum.COMPLETED.value
                        node.completed_at = datetime.now()
                        node.actual_date = date.today()

    def _check_auto_condition(self, node: ProjectNodeInstance) -> bool:
        """检查自动完成条件"""
        node_def = node.node_definition
        if not node_def or not node_def.auto_condition:
            # 无条件配置，依赖满足即可完成
            return True

        # TODO: 实现自动条件检查逻辑
        # auto_condition 可能包含：
        # - "all_dependencies": 所有依赖完成即完成
        # - "percentage": 依赖完成百分比达到阈值
        # - "custom": 自定义条件
        return True

    def _check_stage_completion(self, stage_instance_id: int) -> None:
        """检查阶段是否可以自动完成"""
        # 检查所有必需节点是否完成
        incomplete = self.db.query(ProjectNodeInstance).filter(
            and_(
                ProjectNodeInstance.stage_instance_id == stage_instance_id,
                ProjectNodeInstance.is_required == True,
                ProjectNodeInstance.status.notin_([
                    StageStatusEnum.COMPLETED.value,
                    StageStatusEnum.SKIPPED.value
                ])
            )
        ).count()

        # 如果所有必需节点完成，可以提示用户完成阶段（但不自动完成）
        # 自动完成阶段可能不符合业务需求，保留手动确认
        pass
