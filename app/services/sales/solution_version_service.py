# -*- coding: utf-8 -*-
"""
方案版本服务

管理方案版本的创建、审批和查询。
"""

import re
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.presale_ai_solution import PresaleAISolution
from app.models.sales.solution_version import SolutionVersion


class SolutionVersionService:
    """方案版本服务

    职责：
    1. 创建新版本
    2. 审批版本
    3. 版本查询
    4. 版本比较
    """

    def __init__(self, db: Session):
        self.db = db

    async def create_version(
        self,
        solution_id: int,
        content: dict,
        created_by: int,
        change_reason: Optional[str] = None,
    ) -> SolutionVersion:
        """创建新版本

        版本号规则：
        - 首个版本：V1.0
        - draft 状态下修改：V1.1, V1.2, ...
        - approved 后再修改：V2.0, V3.0, ...

        Args:
            solution_id: 方案ID
            content: 版本内容（generated_solution, bom_list 等）
            created_by: 创建人ID
            change_reason: 变更原因

        Returns:
            新创建的版本
        """
        solution = self.db.query(PresaleAISolution).get(solution_id)
        if not solution:
            raise ValueError(f"方案不存在: {solution_id}")

        # 获取最新版本
        latest = self._get_latest_version(solution_id)

        # 计算版本号
        version_no = self._calculate_next_version(latest)

        # 创建新版本
        version = SolutionVersion(
            solution_id=solution_id,
            version_no=version_no,
            parent_version_id=latest.id if latest else None,
            change_reason=change_reason,
            change_summary=content.get("change_summary", f"基于 {latest.version_no if latest else '初始'} 创建"),
            # 方案内容
            generated_solution=content.get("generated_solution"),
            architecture_diagram=content.get("architecture_diagram"),
            topology_diagram=content.get("topology_diagram"),
            signal_flow_diagram=content.get("signal_flow_diagram"),
            bom_list=content.get("bom_list"),
            technical_parameters=content.get("technical_parameters"),
            process_flow=content.get("process_flow"),
            solution_description=content.get("solution_description"),
            # AI 元数据
            ai_model_used=content.get("ai_model_used"),
            confidence_score=content.get("confidence_score"),
            quality_score=content.get("quality_score"),
            generation_time_seconds=content.get("generation_time_seconds"),
            prompt_tokens=content.get("prompt_tokens"),
            completion_tokens=content.get("completion_tokens"),
            # 创建信息
            created_by=created_by,
            status="draft",
        )

        self.db.add(version)
        self.db.commit()
        self.db.refresh(version)

        return version

    async def submit_for_review(
        self,
        version_id: int,
    ) -> SolutionVersion:
        """提交审核

        将版本状态从 draft 改为 pending_review。

        Args:
            version_id: 版本ID

        Returns:
            更新后的版本
        """
        version = self.db.query(SolutionVersion).get(version_id)
        if not version:
            raise ValueError(f"版本不存在: {version_id}")

        if version.status != "draft":
            raise ValueError(f"只能提交 draft 状态的版本，当前状态：{version.status}")

        version.status = "pending_review"
        self.db.commit()

        return version

    async def approve_version(
        self,
        version_id: int,
        approved_by: int,
        comments: Optional[str] = None,
    ) -> SolutionVersion:
        """审批版本

        审批通过后：
        1. 更新版本状态为 approved
        2. 更新 solution.current_version_id

        Args:
            version_id: 版本ID
            approved_by: 审批人ID
            comments: 审批意见

        Returns:
            审批后的版本
        """
        version = self.db.query(SolutionVersion).get(version_id)
        if not version:
            raise ValueError(f"版本不存在: {version_id}")

        if version.status != "pending_review":
            raise ValueError(f"只能审批 pending_review 状态的版本，当前状态：{version.status}")

        # 更新版本状态
        version.status = "approved"
        version.approved_by = approved_by
        version.approved_at = datetime.now()
        version.approval_comments = comments

        # 更新主表当前版本
        solution = self.db.query(PresaleAISolution).get(version.solution_id)
        solution.current_version_id = version.id

        self.db.commit()

        return version

    async def reject_version(
        self,
        version_id: int,
        rejected_by: int,
        comments: str,
    ) -> SolutionVersion:
        """驳回版本

        Args:
            version_id: 版本ID
            rejected_by: 驳回人ID
            comments: 驳回原因（必填）

        Returns:
            驳回后的版本
        """
        if not comments:
            raise ValueError("驳回必须填写原因")

        version = self.db.query(SolutionVersion).get(version_id)
        if not version:
            raise ValueError(f"版本不存在: {version_id}")

        if version.status != "pending_review":
            raise ValueError(f"只能驳回 pending_review 状态的版本，当前状态：{version.status}")

        version.status = "rejected"
        version.approved_by = rejected_by
        version.approved_at = datetime.now()
        version.approval_comments = comments

        self.db.commit()

        return version

    async def get_version_history(
        self,
        solution_id: int,
    ) -> List[SolutionVersion]:
        """获取版本历史

        Args:
            solution_id: 方案ID

        Returns:
            版本列表（按创建时间降序）
        """
        return (
            self.db.query(SolutionVersion)
            .filter(SolutionVersion.solution_id == solution_id)
            .order_by(SolutionVersion.created_at.desc())
            .all()
        )

    async def compare_versions(
        self,
        version_id_1: int,
        version_id_2: int,
    ) -> dict:
        """比较两个版本

        Args:
            version_id_1: 版本1 ID
            version_id_2: 版本2 ID

        Returns:
            差异对比结果
        """
        v1 = self.db.query(SolutionVersion).get(version_id_1)
        v2 = self.db.query(SolutionVersion).get(version_id_2)

        if not v1 or not v2:
            raise ValueError("版本不存在")

        # 比较关键字段
        fields_to_compare = [
            "generated_solution",
            "architecture_diagram",
            "bom_list",
            "technical_parameters",
        ]

        differences = {}
        for field in fields_to_compare:
            val1 = getattr(v1, field)
            val2 = getattr(v2, field)
            if val1 != val2:
                differences[field] = {
                    "version_1": val1,
                    "version_2": val2,
                }

        return {
            "version_1": {
                "id": v1.id,
                "version_no": v1.version_no,
                "status": v1.status,
                "created_at": v1.created_at.isoformat() if v1.created_at else None,
            },
            "version_2": {
                "id": v2.id,
                "version_no": v2.version_no,
                "status": v2.status,
                "created_at": v2.created_at.isoformat() if v2.created_at else None,
            },
            "differences": differences,
            "has_differences": len(differences) > 0,
        }

    def _get_latest_version(self, solution_id: int) -> Optional[SolutionVersion]:
        """获取最新版本"""
        return (
            self.db.query(SolutionVersion)
            .filter(SolutionVersion.solution_id == solution_id)
            .order_by(SolutionVersion.created_at.desc())
            .first()
        )

    def _calculate_next_version(self, latest: Optional[SolutionVersion]) -> str:
        """计算下一个版本号

        规则：
        - 首个版本：V1.0
        - draft/pending_review/rejected 基础上：次版本号 +1
        - approved 基础上：主版本号 +1，次版本号归零
        """
        if not latest:
            return "V1.0"

        # 解析当前版本号
        match = re.match(r"V(\d+)\.(\d+)", latest.version_no)
        if not match:
            return "V1.0"

        major = int(match.group(1))
        minor = int(match.group(2))

        if latest.status == "approved":
            # 基于已审批版本创建，主版本号 +1
            return f"V{major + 1}.0"
        else:
            # 基于未审批版本创建，次版本号 +1
            return f"V{major}.{minor + 1}"
