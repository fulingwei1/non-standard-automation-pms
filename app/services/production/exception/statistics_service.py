# -*- coding: utf-8 -*-
"""
异常统计分析服务
"""
from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.models.production import (
    EscalationLevel,
    ExceptionHandlingFlow,
    ExceptionPDCA,
    ProductionException,
)
from app.schemas.production.exception_enhancement import (
    ExceptionStatisticsResponse,
    RecurrenceAnalysisResponse,
)


class StatisticsService:
    def __init__(self, db: Session):
        self.db = db

    def get_exception_statistics(
        self,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
    ) -> ExceptionStatisticsResponse:
        """异常统计分析"""
        query = self.db.query(ProductionException)

        # 时间范围过滤
        if start_date:
            query = query.filter(ProductionException.report_time >= start_date)
        if end_date:
            query = query.filter(ProductionException.report_time <= end_date)

        # 总数
        total_count = query.count()

        effective_start = start_date or datetime(2000, 1, 1)
        effective_end = end_date or datetime.now()

        # 按类型统计
        by_type = {}
        type_stats = (
            self.db.query(
                ProductionException.exception_type,
                func.count(ProductionException.id).label("count"),
            )
            .filter(
                ProductionException.report_time >= effective_start,
                ProductionException.report_time <= effective_end,
            )
            .group_by(ProductionException.exception_type)
            .all()
        )

        for type_name, count in type_stats:
            by_type[type_name] = count

        # 按级别统计
        by_level = {}
        level_stats = (
            self.db.query(
                ProductionException.exception_level,
                func.count(ProductionException.id).label("count"),
            )
            .filter(
                ProductionException.report_time >= effective_start,
                ProductionException.report_time <= effective_end,
            )
            .group_by(ProductionException.exception_level)
            .all()
        )

        for level_name, count in level_stats:
            by_level[level_name] = count

        # 按状态统计
        by_status = {}
        status_stats = (
            self.db.query(
                ProductionException.status, func.count(ProductionException.id).label("count")
            )
            .filter(
                ProductionException.report_time >= effective_start,
                ProductionException.report_time <= effective_end,
            )
            .group_by(ProductionException.status)
            .all()
        )

        for status_name, count in status_stats:
            by_status[status_name] = count

        # 平均解决时长
        flows = (
            self.db.query(ExceptionHandlingFlow)
            .join(ProductionException, ExceptionHandlingFlow.exception_id == ProductionException.id)
            .filter(
                ProductionException.report_time >= effective_start,
                ProductionException.report_time <= effective_end,
                ExceptionHandlingFlow.total_duration_minutes.isnot(None),
            )
            .all()
        )

        avg_resolution_time = None
        if flows:
            total_minutes = sum(f.total_duration_minutes or 0 for f in flows)
            avg_resolution_time = total_minutes / len(flows)

        # 升级率
        escalated_count = (
            self.db.query(ExceptionHandlingFlow)
            .join(ProductionException, ExceptionHandlingFlow.exception_id == ProductionException.id)
            .filter(
                ProductionException.report_time >= effective_start,
                ProductionException.report_time <= effective_end,
                ExceptionHandlingFlow.escalation_level != EscalationLevel.NONE,
            )
            .count()
        )

        escalation_rate = (escalated_count / total_count * 100) if total_count > 0 else 0

        # 重复异常率（简化版）
        recurrence_rate = 0.0

        # 高频异常TOP10
        top_exceptions = (
            self.db.query(
                ProductionException.exception_type,
                ProductionException.title,
                func.count(ProductionException.id).label("count"),
            )
            .filter(
                ProductionException.report_time >= effective_start,
                ProductionException.report_time <= effective_end,
            )
            .group_by(ProductionException.exception_type, ProductionException.title)
            .order_by(desc("count"))
            .limit(10)
            .all()
        )

        top_exceptions_list = [
            {"type": exc_type, "title": title, "count": count}
            for exc_type, title, count in top_exceptions
        ]

        return ExceptionStatisticsResponse(
            total_count=total_count,
            by_type=by_type,
            by_level=by_level,
            by_status=by_status,
            avg_resolution_time_minutes=avg_resolution_time,
            escalation_rate=escalation_rate,
            recurrence_rate=recurrence_rate,
            top_exceptions=top_exceptions_list,
        )

    def analyze_recurrence(
        self,
        exception_type: Optional[str],
        days: int,
    ) -> List[RecurrenceAnalysisResponse]:
        """重复异常分析"""
        start_date = datetime.now() - timedelta(days=days)

        query = self.db.query(ProductionException).filter(
            ProductionException.report_time >= start_date
        )

        if exception_type:
            query = query.filter(ProductionException.exception_type == exception_type)

        exceptions = query.all()

        # 按异常类型分组
        type_groups = {}
        for exc in exceptions:
            if exc.exception_type not in type_groups:
                type_groups[exc.exception_type] = []
            type_groups[exc.exception_type].append(exc)

        results = []
        for exc_type, exc_list in type_groups.items():
            # 查找相似异常（标题相似度 > 60%）
            similar_groups = self.find_similar_exceptions(exc_list)

            # 时间趋势
            time_trend = self.analyze_time_trend(exc_list, days)

            # 常见根因（从PDCA记录中提取）
            common_root_causes = self.extract_common_root_causes([e.id for e in exc_list])

            results.append(
                RecurrenceAnalysisResponse(
                    exception_type=exc_type,
                    total_occurrences=len(exc_list),
                    similar_exceptions=similar_groups,
                    time_trend=time_trend,
                    common_root_causes=common_root_causes,
                    recommended_actions=[
                        "建立标准作业程序",
                        "加强人员培训",
                        "优化设备维护计划",
                        "建立预警机制",
                    ],
                )
            )

        return results

    def find_similar_exceptions(self, exceptions: list) -> List[dict]:
        """查找相似异常（Jaccard相似度算法）"""
        title_groups = {}
        for exc in exceptions:
            title = exc.title.lower()
            # 简单分词
            words = set(title.split())

            matched = False
            for existing_title, group in title_groups.items():
                existing_words = set(existing_title.split())
                # 计算Jaccard相似度
                intersection = len(words & existing_words)
                union = len(words | existing_words)
                similarity = intersection / union if union > 0 else 0

                if similarity > 0.6:
                    group.append(exc)
                    matched = True
                    break

            if not matched:
                title_groups[title] = [exc]

        # 只返回出现2次以上的
        similar = []
        for title, group in title_groups.items():
            if len(group) >= 2:
                similar.append(
                    {
                        "pattern": title,
                        "count": len(group),
                        "exception_ids": [e.id for e in group],
                    }
                )

        return sorted(similar, key=lambda x: x["count"], reverse=True)[:10]

    def analyze_time_trend(self, exceptions: list, days: int) -> List[dict]:
        """分析时间趋势"""
        # 按日期分组统计
        date_counts = {}
        for exc in exceptions:
            date_key = exc.report_time.strftime("%Y-%m-%d")
            date_counts[date_key] = date_counts.get(date_key, 0) + 1

        # 生成趋势数据
        trend = []
        start_date = datetime.now() - timedelta(days=days)
        for i in range(days):
            date = start_date + timedelta(days=i)
            date_key = date.strftime("%Y-%m-%d")
            trend.append(
                {
                    "date": date_key,
                    "count": date_counts.get(date_key, 0),
                }
            )

        return trend

    def extract_common_root_causes(self, exception_ids: List[int]) -> List[str]:
        """提取常见根因"""
        pdca_records = (
            self.db.query(ExceptionPDCA)
            .filter(
                ExceptionPDCA.exception_id.in_(exception_ids),
                ExceptionPDCA.plan_root_cause.isnot(None),
            )
            .all()
        )

        root_causes = [p.plan_root_cause for p in pdca_records if p.plan_root_cause]

        # 简化版：返回前3个
        return root_causes[:3] if root_causes else ["暂无根因分析"]
