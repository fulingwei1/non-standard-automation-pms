# -*- coding: utf-8 -*-
"""
变更历史模块
提供模板变更记录的写入和查询功能
"""

from typing import Any, Dict, List, Optional

from app.models.stage_template import StageTemplate, StageTemplateChangeLog


class ChangeLogMixin:
    """变更历史功能混入类"""

    def record_change(
        self,
        template_id: int,
        action: str,
        changed_by: Optional[int] = None,
        target_type: Optional[str] = None,
        target_id: Optional[int] = None,
        target_name: Optional[str] = None,
        change_description: Optional[str] = None,
        change_detail: Optional[Dict[str, Any]] = None,
    ) -> StageTemplateChangeLog:
        """
        记录一条变更日志

        Args:
            template_id: 模板ID
            action: 操作类型
            changed_by: 操作人ID
            target_type: 目标类型 (TEMPLATE/STAGE/NODE)
            target_id: 目标ID
            target_name: 目标名称快照
            change_description: 修改说明
            change_detail: 变更详情 {field: {old: ..., new: ...}}
        """
        log = StageTemplateChangeLog(
            template_id=template_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            target_name=target_name,
            change_description=change_description,
            change_detail=change_detail,
            changed_by=changed_by,
        )
        self.db.add(log)

        # 同步更新模板的 updated_by 和 change_description
        template = (
            self.db.query(StageTemplate).filter(StageTemplate.id == template_id).first()
        )
        if template:
            if changed_by is not None:
                template.updated_by = changed_by
            if change_description:
                template.change_description = change_description

        self.db.flush()
        return log

    def get_change_logs(
        self,
        template_id: int,
        limit: int = 50,
        offset: int = 0,
        action: Optional[str] = None,
    ) -> List[StageTemplateChangeLog]:
        """
        查询模板变更历史

        Args:
            template_id: 模板ID
            limit: 返回条数
            offset: 偏移量
            action: 按操作类型筛选
        """
        query = self.db.query(StageTemplateChangeLog).filter(
            StageTemplateChangeLog.template_id == template_id
        )

        if action:
            query = query.filter(StageTemplateChangeLog.action == action)

        return (
            query.order_by(StageTemplateChangeLog.id.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def _diff_fields(self, old_obj, new_values: Dict[str, Any]) -> Dict[str, Any]:
        """
        比较对象旧值与新值，返回变更详情

        Returns:
            Dict: {field_name: {"old": old_value, "new": new_value}}
        """
        detail = {}
        for key, new_val in new_values.items():
            if new_val is None:
                continue
            old_val = getattr(old_obj, key, None)
            if old_val != new_val:
                detail[key] = {"old": old_val, "new": new_val}
        return detail if detail else None
