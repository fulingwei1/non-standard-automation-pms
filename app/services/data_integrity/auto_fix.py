# -*- coding: utf-8 -*-
"""
自动修复模块
提供数据问题的自动修复建议和执行功能
"""

from typing import Any, Dict, List, Optional



class AutoFixMixin:
    """自动修复功能混入类"""

    def suggest_auto_fixes(
        self,
        engineer_id: int,
        period_id: int
    ) -> List[Dict[str, Any]]:
        """
        提供自动修复建议

        Args:
            engineer_id: 工程师ID
            period_id: 考核周期ID

        Returns:
            自动修复建议列表
        """
        suggestions = []
        report = self.check_data_completeness(engineer_id, period_id)

        # 1. 如果缺少跨部门协作评价，建议自动抽取
        if report['collab_ratings_count'] < 3:
            suggestions.append({
                'type': 'auto_select_collaborators',
                'action': '自动抽取合作人员进行评价',
                'description': '系统可以自动从项目成员中抽取5个合作人员进行匿名评价',
                'can_auto_fix': True
            })

        # 2. 如果缺少工作日志，建议提醒工程师
        if report['work_logs_count'] == 0:
            suggestions.append({
                'type': 'remind_work_log',
                'action': '提醒工程师填写工作日志',
                'description': '可以发送提醒通知，督促工程师填写工作日志',
                'can_auto_fix': False
            })

        # 3. 如果项目评价缺失，建议提醒项目管理部经理
        if '项目评价未完成' in str(report.get('warnings', [])):
            suggestions.append({
                'type': 'remind_project_evaluation',
                'action': '提醒项目管理部经理完成项目评价',
                'description': '可以发送提醒通知，督促项目管理部经理完成项目难度和工作量评价',
                'can_auto_fix': False
            })

        return suggestions

    def auto_fix_data_issues(
        self,
        engineer_id: int,
        period_id: int,
        fix_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        自动修复数据问题

        Args:
            engineer_id: 工程师ID
            period_id: 考核周期ID
            fix_types: 要修复的问题类型列表（如果为None则修复所有可自动修复的问题）

        Returns:
            修复结果
        """
        fixes_applied = []
        fixes_failed = []

        suggestions = self.suggest_auto_fixes(engineer_id, period_id)

        for suggestion in suggestions:
            if not suggestion.get('can_auto_fix', False):
                continue

            if fix_types and suggestion['type'] not in fix_types:
                continue

            try:
                if suggestion['type'] == 'auto_select_collaborators':
                    # 自动抽取合作人员
                    from app.services.collaboration_rating import (
                        CollaborationRatingService,
                    )
                    collab_service = CollaborationRatingService(self.db)

                    collaborators = collab_service.auto_select_collaborators(
                        engineer_id, period_id, target_count=5
                    )
                    if collaborators:
                        collab_service.create_rating_invitations(
                            engineer_id, period_id, collaborators
                        )
                        fixes_applied.append({
                            'type': suggestion['type'],
                            'action': suggestion['action'],
                            'result': f'已自动抽取{len(collaborators)}个合作人员'
                        })
                    else:
                        fixes_failed.append({
                            'type': suggestion['type'],
                            'reason': '未找到合适的合作人员'
                        })
            except Exception as e:
                fixes_failed.append({
                    'type': suggestion['type'],
                    'reason': str(e)
                })

        return {
            'engineer_id': engineer_id,
            'period_id': period_id,
            'fixes_applied': fixes_applied,
            'fixes_failed': fixes_failed,
            'total_applied': len(fixes_applied),
            'total_failed': len(fixes_failed)
        }
