# -*- coding: utf-8 -*-
"""
工作日志数据采集
"""
import logging
import re
from datetime import date
from typing import Any, Dict

from sqlalchemy.orm import Session

from app.models.work_log import WorkLog

from .constants import (
    COLLABORATION_KEYWORDS,
    KNOWLEDGE_SHARING_PATTERNS,
    NEGATIVE_KEYWORDS,
    POSITIVE_KEYWORDS,
    PROBLEM_SOLVING_PATTERNS,
    TECH_BREAKTHROUGH_PATTERNS,
    TECH_KEYWORDS,
)

logger = logging.getLogger(__name__)


def extract_self_evaluation_from_work_logs(
    db: Session,
    engineer_id: int,
    start_date: date,
    end_date: date
) -> Dict[str, Any]:
    """
    从工作日志中提取自我评价数据

    Returns:
        {
            'positive_count': int,
            'negative_count': int,
            'tech_mentions': int,
            'collaboration_mentions': int,
            'problem_solving_count': int,
            'knowledge_sharing_count': int,
            'tech_breakthrough_count': int,
            'total_logs': int,
            'self_evaluation_score': float
        }
    """
    try:
        work_logs = db.query(WorkLog).filter(
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
                'self_evaluation_score': 75.0
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

            for keyword in POSITIVE_KEYWORDS:
                positive_count += len(re.findall(keyword, content))

            for keyword in NEGATIVE_KEYWORDS:
                negative_count += len(re.findall(keyword, content))

            for keyword in TECH_KEYWORDS:
                tech_mentions += len(re.findall(keyword, content))

            for keyword in COLLABORATION_KEYWORDS:
                collaboration_mentions += len(re.findall(keyword, content))

            for pattern in PROBLEM_SOLVING_PATTERNS:
                if re.search(pattern, content):
                    problem_solving_count += 1
                    positive_count += 2
                    break

            for pattern in KNOWLEDGE_SHARING_PATTERNS:
                if re.search(pattern, content):
                    knowledge_sharing_count += 1
                    positive_count += 2
                    collaboration_mentions += 1
                    break

            for pattern in TECH_BREAKTHROUGH_PATTERNS:
                if re.search(pattern, content):
                    tech_breakthrough_count += 1
                    positive_count += 3
                    tech_mentions += 2
                    break

        total_keywords = positive_count + negative_count
        if total_keywords > 0:
            positive_ratio = positive_count / total_keywords
            base_score = 75.0 + (positive_ratio - 0.5) * 50
        else:
            base_score = 75.0

        scenario_bonus = 0
        if problem_solving_count > 0:
            scenario_bonus += min(problem_solving_count * 2, 10)
        if knowledge_sharing_count > 0:
            scenario_bonus += min(knowledge_sharing_count * 1.5, 8)
        if tech_breakthrough_count > 0:
            scenario_bonus += min(tech_breakthrough_count * 3, 12)

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
