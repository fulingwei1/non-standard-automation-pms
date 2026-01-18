# -*- coding: utf-8 -*-
"""
工程师绩效数据采集 - 工作日志数据收集
从工作日志中提取自我评价数据
"""

import re
from datetime import date
from typing import Any, Dict

from sqlalchemy.orm import Session

from app.models.work_log import WorkLog
from .base import PerformanceDataCollectorBase


class WorkLogCollector(PerformanceDataCollectorBase):
    """工作日志数据收集器"""

    def extract_self_evaluation_from_work_logs(
        self,
        engineer_id: int,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        从工作日志中提取自我评价数据（增强版：支持上下文分析）

        Returns:
            {
                'positive_count': int,      # 积极词汇出现次数
                'negative_count': int,       # 消极词汇出现次数
                'tech_mentions': int,        # 技术相关提及次数
                'collaboration_mentions': int, # 协作相关提及次数
                'problem_solving_count': int,  # 问题解决场景次数
                'knowledge_sharing_count': int, # 知识分享场景次数
                'tech_breakthrough_count': int, # 技术突破场景次数
                'total_logs': int,           # 总日志数
                'self_evaluation_score': float  # 自我评价得分（0-100）
            }
        """
        try:
            work_logs = self.db.query(WorkLog).filter(
                WorkLog.user_id == engineer_id,
                WorkLog.work_date.between(start_date, end_date),
                WorkLog.status == 'SUBMITTED'
            ).all()

            if not work_logs:
                return {
                    'positive_count': 0,
                    'negative_count': 0,
                    'tech_mentions': 0,
                    'collaboration_mentions': 0,
                    'problem_solving_count': 0,
                    'knowledge_sharing_count': 0,
                    'tech_breakthrough_count': 0,
                    'total_logs': 0,
                    'self_evaluation_score': 75.0  # 默认值
                }

            positive_count = 0
            negative_count = 0
            tech_mentions = 0
            collaboration_mentions = 0
            problem_solving_count = 0
            knowledge_sharing_count = 0
            tech_breakthrough_count = 0

            for log in work_logs:
                if not log.content:
                    continue

                content = log.content.lower()

                # 统计积极词汇
                for keyword in self.POSITIVE_KEYWORDS:
                    positive_count += len(re.findall(keyword, content))

                # 统计消极词汇
                for keyword in self.NEGATIVE_KEYWORDS:
                    negative_count += len(re.findall(keyword, content))

                # 统计技术相关提及
                for keyword in self.TECH_KEYWORDS:
                    tech_mentions += len(re.findall(keyword, content))

                # 统计协作相关提及
                for keyword in self.COLLABORATION_KEYWORDS:
                    collaboration_mentions += len(re.findall(keyword, content))

                # 上下文分析：问题解决场景
                for pattern in self.PROBLEM_SOLVING_PATTERNS:
                    if re.search(pattern, content):
                        problem_solving_count += 1
                        positive_count += 2  # 问题解决是积极行为
                        break

                # 上下文分析：知识分享场景
                for pattern in self.KNOWLEDGE_SHARING_PATTERNS:
                    if re.search(pattern, content):
                        knowledge_sharing_count += 1
                        positive_count += 2  # 知识分享是积极行为
                        collaboration_mentions += 1
                        break

                # 上下文分析：技术突破场景
                for pattern in self.TECH_BREAKTHROUGH_PATTERNS:
                    if re.search(pattern, content):
                        tech_breakthrough_count += 1
                        positive_count += 3  # 技术突破是高度积极行为
                        tech_mentions += 2
                        break

            # 计算自我评价得分（增强版）
            # 基础分75，根据积极/消极词汇比例调整
            total_keywords = positive_count + negative_count
            if total_keywords > 0:
                positive_ratio = positive_count / total_keywords
                # 积极比例越高，得分越高（最高+25分）
                base_score = 75.0 + (positive_ratio - 0.5) * 50
            else:
                base_score = 75.0

            # 场景加分：问题解决、知识分享、技术突破
            scenario_bonus = 0
            if problem_solving_count > 0:
                scenario_bonus += min(problem_solving_count * 2, 10)  # 最多加10分
            if knowledge_sharing_count > 0:
                scenario_bonus += min(knowledge_sharing_count * 1.5, 8)  # 最多加8分
            if tech_breakthrough_count > 0:
                scenario_bonus += min(tech_breakthrough_count * 3, 12)  # 最多加12分

            self_evaluation_score = base_score + scenario_bonus
            self_evaluation_score = max(0, min(100, self_evaluation_score))

            return {
                'positive_count': positive_count,
                'negative_count': negative_count,
                'tech_mentions': tech_mentions,
                'collaboration_mentions': collaboration_mentions,
                'problem_solving_count': problem_solving_count,
                'knowledge_sharing_count': knowledge_sharing_count,
                'tech_breakthrough_count': tech_breakthrough_count,
                'total_logs': len(work_logs),
                'self_evaluation_score': round(self_evaluation_score, 2)
            }
        except Exception as e:
            # 异常处理：返回默认值
            return {
                'positive_count': 0,
                'negative_count': 0,
                'tech_mentions': 0,
                'collaboration_mentions': 0,
                'problem_solving_count': 0,
                'knowledge_sharing_count': 0,
                'tech_breakthrough_count': 0,
                'total_logs': 0,
                'self_evaluation_score': 75.0,
                'error': str(e)
            }
