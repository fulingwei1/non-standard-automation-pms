# -*- coding: utf-8 -*-
"""
销售排名服务

负责：
- 读取/保存销售排名权重配置
- 计算综合评分和排名结果
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.enums import InvoiceStatusEnum
from app.models.sales import (
    Contract,
    Invoice,
    SalesRankingConfig,
)
from app.models.user import User
from app.services.sales_team_service import SalesTeamService


class SalesRankingService:
    """销售排名计算和配置服务"""

    PRIMARY_METRIC_KEYS = ["contract_amount", "acceptance_amount", "collection_amount"]
    PRIMARY_WEIGHT_TARGET = 0.8
    TOTAL_WEIGHT_TARGET = 1.0

    ALLOWED_METRIC_SOURCES = {
        "contract_amount": "contract_amount",
        "acceptance_amount": "acceptance_amount",
        "collection_amount": "collection_amount",
        "opportunity_count": "opportunity_count",
        "lead_conversion_rate": "lead_conversion_rate",
        "modeling_rate": "modeling_rate",
        "info_completeness": "info_completeness",
        "follow_up_total": "follow_up_total",
        "follow_up_visit": "follow_up_visit",
        "pipeline_amount": "pipeline_amount",
        "avg_est_margin": "avg_est_margin",
    }

    DEFAULT_METRICS: List[Dict[str, Any]] = [
        {
            "key": "contract_amount",
            "label": "合同金额",
            "weight": 0.4,
            "data_source": "contract_amount",
            "description": "统计周期内签订合同金额",
            "is_primary": True,
        },
        {
            "key": "acceptance_amount",
            "label": "验收金额",
            "weight": 0.2,
            "data_source": "acceptance_amount",
            "description": "已审批/已开票金额，代表验收进度",
            "is_primary": True,
        },
        {
            "key": "collection_amount",
            "label": "回款金额",
            "weight": 0.2,
            "data_source": "collection_amount",
            "description": "周期内已回款金额",
            "is_primary": True,
        },
        {
            "key": "opportunity_count",
            "label": "商机数量",
            "weight": 0.05,
            "data_source": "opportunity_count",
            "description": "创建并推进的商机数量",
            "is_primary": False,
        },
        {
            "key": "lead_conversion_rate",
            "label": "线索成功率",
            "weight": 0.05,
            "data_source": "lead_conversion_rate",
            "description": "线索转商机的转化率",
            "is_primary": False,
        },
        {
            "key": "follow_up_total",
            "label": "跟进行为次数",
            "weight": 0.05,
            "data_source": "follow_up_total",
            "description": "电话、拜访、会议等总跟进次数",
            "is_primary": False,
        },
        {
            "key": "avg_est_margin",
            "label": "平均预估毛利率",
            "weight": 0.05,
            "data_source": "avg_est_margin",
            "description": "商机的平均预估毛利率",
            "is_primary": False,
        },
    ]

    def __init__(self, db: Session):
        self.db = db
        self.team_service = SalesTeamService(db)

    # -------------------------------
    # 配置管理
    # -------------------------------

    def get_active_config(self) -> SalesRankingConfig:
        config = (
            self.db.query(SalesRankingConfig)
            .order_by(SalesRankingConfig.updated_at.desc())
            .first()
        )
        if config:
            return config

        config = SalesRankingConfig(metrics=self.DEFAULT_METRICS)
        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)
        return config

    def save_config(
        self,
        metrics: List[Dict[str, Any]],
        operator_id: Optional[int] = None,
    ) -> SalesRankingConfig:
        """保存新的排名配置"""
        validated_metrics = self._validate_metrics(metrics)
        config = SalesRankingConfig(
            metrics=validated_metrics,
            created_by=operator_id,
            updated_by=operator_id,
        )
        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)
        return config

    def _validate_metrics(self, metrics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not metrics:
            raise ValueError("至少需要配置一条指标")

        normalized: List[Dict[str, Any]] = []
        seen_keys = set()
        primary_weight = 0.0
        total_weight = 0.0

        for metric in metrics:
            key = metric.get("key")
            data_source = metric.get("data_source")
            weight = float(metric.get("weight", 0))
            label = metric.get("label") or key

            if not key or key in seen_keys:
                raise ValueError("指标 key 不能为空且不能重复")
            seen_keys.add(key)

            if data_source not in self.ALLOWED_METRIC_SOURCES:
                raise ValueError(f"不支持的数据来源: {data_source}")

            if weight <= 0:
                raise ValueError("指标权重必须大于0")

            is_primary = bool(metric.get("is_primary", key in self.PRIMARY_METRIC_KEYS))

            normalized_metric = {
                "key": key,
                "label": label,
                "weight": round(weight, 4),
                "data_source": data_source,
                "description": metric.get("description"),
                "is_primary": is_primary,
            }
            normalized.append(normalized_metric)

            total_weight += weight
            if is_primary or key in self.PRIMARY_METRIC_KEYS:
                primary_weight += weight

        if abs(total_weight - self.TOTAL_WEIGHT_TARGET) > 0.0001:
            raise ValueError("所有指标权重之和必须等于 1.0")

        if abs(primary_weight - self.PRIMARY_WEIGHT_TARGET) > 0.0001:
            raise ValueError("签单额、验收金额、回款金额三项权重之和必须为 0.8")

        return sorted(normalized, key=lambda x: x["weight"], reverse=True)

    # -------------------------------
    # 排名计算
    # -------------------------------

    def calculate_rankings(
        self,
        users: List[User],
        start_datetime: datetime,
        end_datetime: datetime,
        ranking_type: str = "score",
    ) -> Dict[str, Any]:
        if not users:
            config = self.get_active_config()
            return {
                "rankings": [],
                "config": {"metrics": config.metrics, "total_weight": 1.0},
                "ranking_type": ranking_type,
            }

        config = self.get_active_config()
        metrics_config = config.metrics or self.DEFAULT_METRICS

        user_ids = [user.id for user in users]

        lead_quality_map = self.team_service.get_lead_quality_stats_map(
            user_ids, start_datetime, end_datetime
        )
        follow_up_map = self.team_service.get_followup_statistics_map(
            user_ids, start_datetime, end_datetime
        )
        opportunity_map = self.team_service.get_opportunity_stats_map(
            user_ids, start_datetime, end_datetime
        )
        acceptance_map = self._get_acceptance_amount_map(
            user_ids, start_datetime, end_datetime
        )

        aggregated_data: Dict[int, Dict[str, float]] = {}
        for user in users:
            lead_stats = lead_quality_map.get(user.id, {})
            follow_stats = follow_up_map.get(user.id, {})
            opp_stats = opportunity_map.get(user.id, {})

            aggregated_data[user.id] = {
                "contract_amount": 0.0,
                "contract_count": 0,
                "lead_count": lead_stats.get("total_leads", 0),
                "lead_conversion_rate": lead_stats.get("conversion_rate", 0.0),
                "modeling_rate": lead_stats.get("modeling_rate", 0.0),
                "info_completeness": lead_stats.get("avg_completeness", 0.0),
                "follow_up_total": follow_stats.get("total", 0),
                "follow_up_visit": follow_stats.get("VISIT", 0),
                "opportunity_count": opp_stats.get("opportunity_count", 0),
                "pipeline_amount": opp_stats.get("pipeline_amount", 0.0),
                "avg_est_margin": opp_stats.get("avg_est_margin", 0.0),
                "acceptance_amount": acceptance_map.get(user.id, 0.0),
                "collection_amount": 0.0,
            }

        # 合同、回款
        contract_data = self._get_contract_and_collection_data(
            user_ids, start_datetime, end_datetime
        )
        for user_id, data in contract_data.items():
            aggregated_data[user_id]["contract_amount"] = data["contract_amount"]
            aggregated_data[user_id]["contract_count"] = data["contract_count"]
            aggregated_data[user_id]["collection_amount"] = data["collection_amount"]

        max_values: Dict[str, float] = {}
        for metric in metrics_config:
            source = metric.get("data_source")
            max_values[source] = max(
                aggregated_data[user.id].get(source, 0) or 0 for user in users
            ) or 1.0

        ranking_entries: List[Dict[str, Any]] = []
        for user in users:
            data = aggregated_data[user.id]
            metrics_details: List[Dict[str, Any]] = []
            total_score = 0.0

            for metric in metrics_config:
                source = metric.get("data_source")
                value = float(data.get(source, 0) or 0)
                max_value = max_values.get(source) or 1.0
                normalized = value / max_value if max_value else 0.0
                partial_score = normalized * metric["weight"]
                total_score += partial_score

                metrics_details.append(
                    {
                        "key": metric["key"],
                        "label": metric["label"],
                        "weight": metric["weight"],
                        "value": value,
                        "normalized_value": round(normalized, 4),
                        "score": round(partial_score * 100, 2),
                    }
                )

            ranking_entries.append(
                {
                    "user_id": user.id,
                    "user_name": user.real_name or user.username,
                    "username": user.username,
                    "department_name": user.department or "",
                    "score": round(total_score * 100, 2),
                    "contract_amount": data.get("contract_amount", 0.0),
                    "acceptance_amount": data.get("acceptance_amount", 0.0),
                    "collection_amount": data.get("collection_amount", 0.0),
                    "metrics": metrics_details,
                    "raw_metrics": data,
                }
            )

        # 排序
        sort_key = ranking_type
        if ranking_type == "score" or ranking_type not in self.ALLOWED_METRIC_SOURCES:
            sort_key = "score"
            ranking_type = "score"

        if sort_key == "score":
            ranking_entries.sort(key=lambda item: item["score"], reverse=True)
        else:
            ranking_entries.sort(
                key=lambda item: item["raw_metrics"].get(sort_key, 0), reverse=True
            )

        for idx, entry in enumerate(ranking_entries, start=1):
            entry["rank"] = idx
            entry.pop("raw_metrics", None)

        return {
            "ranking_type": ranking_type,
            "rankings": ranking_entries,
            "config": {
                "metrics": metrics_config,
                "total_weight": sum(m.get("weight", 0) for m in metrics_config),
            },
            "max_values": max_values,
        }

    def _get_contract_and_collection_data(
        self,
        user_ids: List[int],
        start_datetime: datetime,
        end_datetime: datetime,
    ) -> Dict[int, Dict[str, float]]:
        result: Dict[int, Dict[str, float]] = {
            user_id: {"contract_amount": 0.0, "contract_count": 0, "collection_amount": 0.0}
            for user_id in user_ids
        }

        if not user_ids:
            return result

        # 合同金额
        contract_query = (
            self.db.query(
                Contract.owner_id.label("owner_id"),
                func.count(Contract.id).label("count"),
                func.sum(func.coalesce(Contract.contract_amount, 0)).label(
                    "contract_amount"
                ),
            )
            .filter(Contract.owner_id.in_(user_ids))
            .filter(Contract.created_at >= start_datetime)
            .filter(Contract.created_at <= end_datetime)
            .group_by(Contract.owner_id)
        )
        for row in contract_query.all():
            result[row.owner_id]["contract_amount"] = float(row.contract_amount or 0)
            result[row.owner_id]["contract_count"] = int(row.count or 0)

        # 回款金额
        invoice_query = (
            self.db.query(
                Contract.owner_id.label("owner_id"),
                func.sum(func.coalesce(Invoice.paid_amount, 0)).label("paid_amount"),
            )
            .join(Contract, Invoice.contract_id == Contract.id)
            .filter(Contract.owner_id.in_(user_ids))
            .filter(Invoice.payment_status.in_(["PAID", "PARTIAL"]))
            .filter(Invoice.paid_date.isnot(None))
        )
        invoice_query = invoice_query.filter(Invoice.paid_date >= start_datetime.date())
        invoice_query = invoice_query.filter(Invoice.paid_date <= end_datetime.date())
        invoice_query = invoice_query.group_by(Contract.owner_id)

        for row in invoice_query.all():
            result[row.owner_id]["collection_amount"] = float(row.paid_amount or 0)

        return result

    def _get_acceptance_amount_map(
        self,
        user_ids: List[int],
        start_datetime: datetime,
        end_datetime: datetime,
    ) -> Dict[int, float]:
        if not user_ids:
            return {}

        query = (
            self.db.query(
                Contract.owner_id.label("owner_id"),
                func.sum(func.coalesce(Invoice.amount, 0)).label("acceptance_amount"),
            )
            .join(Invoice, Invoice.contract_id == Contract.id)
            .filter(Contract.owner_id.in_(user_ids))
            .filter(
                Invoice.status.in_(
                    [InvoiceStatusEnum.APPROVED.value, InvoiceStatusEnum.ISSUED.value]
                )
            )
            .filter(Invoice.created_at >= start_datetime)
            .filter(Invoice.created_at <= end_datetime)
            .group_by(Contract.owner_id)
        )

        return {
            row.owner_id: float(row.acceptance_amount or 0) for row in query.all()
        }
