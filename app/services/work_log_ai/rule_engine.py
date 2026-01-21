# -*- coding: utf-8 -*-
"""
规则引擎模块
提供基于规则的工作日志分析功能（AI不可用时的fallback）
"""

import re
from datetime import date
from decimal import Decimal
from typing import Any, Dict, List

from app.utils.holiday_utils import get_work_type


class RuleEngineMixin:
    """规则引擎分析功能混入类"""

    def _analyze_with_rules(
        self,
        content: str,
        user_projects: List[Dict[str, Any]],
        work_date: date
    ) -> Dict[str, Any]:
        """
        使用规则引擎分析工作日志内容（AI不可用时的fallback）

        Args:
            content: 工作日志内容
            user_projects: 用户参与的项目列表
            work_date: 工作日期

        Returns:
            分析结果
        """
        work_items = []
        total_hours = Decimal("0")

        # 1. 尝试提取工时信息（使用正则表达式）
        # 匹配模式：如"6小时"、"4.5h"、"工作8小时"等
        hour_patterns = [
            r'(\d+\.?\d*)\s*小时',
            r'(\d+\.?\d*)\s*h',
            r'工作\s*(\d+\.?\d*)\s*小时',
            r'耗时\s*(\d+\.?\d*)\s*小时',
        ]

        extracted_hours = []
        for pattern in hour_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                try:
                    hours = float(match)
                    if 0 < hours <= 12:  # 合理的工时范围
                        extracted_hours.append(hours)
                except ValueError:
                    continue

        # 2. 尝试匹配项目
        matched_project = None
        for project in user_projects:
            # 检查项目编码是否在工作日志中
            if project['code'] in content:
                matched_project = project
                break

            # 检查项目名称关键词是否在工作日志中
            for keyword in project['keywords']:
                if keyword and keyword in content:
                    matched_project = project
                    break

            if matched_project:
                break

        # 3. 如果没有明确提到项目，使用最常用的项目
        if not matched_project and user_projects:
            matched_project = user_projects[0]  # 使用最常用的项目

        # 4. 判断工作类型（使用节假日工具）
        work_type = get_work_type(work_date)

        # 5. 构建工作项
        if extracted_hours:
            # 如果有明确的工时信息，使用提取的工时
            for hours in extracted_hours:
                work_items.append({
                    "work_content": content[:100],  # 截取前100字作为工作内容
                    "hours": float(hours),
                    "project_id": matched_project['id'] if matched_project else None,
                    "project_code": matched_project['code'] if matched_project else None,
                    "project_name": matched_project['name'] if matched_project else None,
                    "work_type": work_type,
                    "confidence": 0.7  # 规则引擎的置信度较低
                })
                total_hours += Decimal(str(hours))
        else:
            # 如果没有明确的工时信息，根据内容长度和复杂度估算
            # 简单规则：内容越长，工时越多（但不超过8小时）
            estimated_hours = min(8.0, max(2.0, len(content) / 50))  # 每50字约1小时，最少2小时，最多8小时

            work_items.append({
                "work_content": content,
                "hours": estimated_hours,
                "project_id": matched_project['id'] if matched_project else None,
                "project_code": matched_project['code'] if matched_project else None,
                "project_name": matched_project['name'] if matched_project else None,
                "work_type": work_type,
                "confidence": 0.5  # 估算的置信度更低
            })
            total_hours = Decimal(str(estimated_hours))

        return {
            "work_items": work_items,
            "total_hours": float(total_hours),
            "confidence": 0.6,  # 规则引擎的整体置信度
            "analysis_notes": "使用规则引擎分析（AI服务未配置）",
            "suggested_projects": [p for p in user_projects[:5]]  # 推荐前5个最常用的项目
        }
