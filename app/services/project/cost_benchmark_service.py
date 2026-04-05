# -*- coding: utf-8 -*-
"""
成本对标服务

提供历史项目对标分析功能，帮助评估新项目成本的合理性
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, desc
from sqlalchemy.orm import Session

from app.models.project import (
    BenchmarkConfiguration,
    Project,
    ProjectCostBenchmark,
    SimilarityLevelEnum,
)

logger = logging.getLogger(__name__)


class CostBenchmarkService:
    """成本对标服务"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== 配置管理 ====================

    def get_default_config(self) -> Optional[BenchmarkConfiguration]:
        """获取默认对标配置"""
        config = (
            self.db.query(BenchmarkConfiguration)
            .filter(
                and_(
                    BenchmarkConfiguration.is_active == True,
                    BenchmarkConfiguration.is_default == True,
                )
            )
            .first()
        )

        if not config:
            # 返回默认配置值
            return self._create_default_config()

        return config

    def _create_default_config(self) -> BenchmarkConfiguration:
        """创建默认配置（如果不存在）"""
        config = BenchmarkConfiguration(
            name="默认对标配置",
            description="系统默认的成本对标配置",
            industry_weight=Decimal("0.25"),
            test_type_weight=Decimal("0.25"),
            scale_weight=Decimal("0.20"),
            complexity_weight=Decimal("0.20"),
            customer_weight=Decimal("0.10"),
            high_threshold=Decimal("80"),
            medium_threshold=Decimal("50"),
            low_threshold=Decimal("30"),
            max_benchmarks=5,
            min_similarity=Decimal("30"),
            cost_variance_warning=Decimal("10"),
            cost_variance_alert=Decimal("20"),
            is_active=True,
            is_default=True,
        )
        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)
        return config

    # ==================== 相似项目查找 ====================

    def find_similar_projects(
        self,
        project_id: int,
        top_k: int = 5,
        min_similarity: float = 30.0,
    ) -> List[Dict[str, Any]]:
        """
        查找相似的历史项目

        Args:
            project_id: 当前项目ID
            top_k: 返回前K个相似项目
            min_similarity: 最小相似度阈值

        Returns:
            相似项目列表，包含相似度评分
        """
        # 获取当前项目
        current_project = self.db.query(Project).filter(Project.id == project_id).first()
        if not current_project:
            raise ValueError(f"项目不存在: {project_id}")

        # 获取配置
        config = self.get_default_config()

        # 查询已完成的历史项目（排除当前项目）
        historical_projects = (
            self.db.query(Project)
            .filter(
                and_(
                    Project.id != project_id,
                    Project.status.in_(["COMPLETED", "ACCEPTED", "WARRANTY"]),
                )
            )
            .all()
        )

        # 计算相似度
        similarities = []
        for hist_project in historical_projects:
            similarity = self._calculate_similarity(
                current_project, hist_project, config
            )
            if similarity["total_score"] >= min_similarity:
                similarities.append({
                    "project_id": hist_project.id,
                    "project_name": hist_project.name,
                    "project_no": hist_project.project_no,
                    "customer_name": getattr(hist_project, "customer_name", None),
                    "industry": getattr(hist_project, "industry", None),
                    "test_type": getattr(hist_project, "test_type", None),
                    "total_cost": float(hist_project.total_cost or 0),
                    "completed_at": hist_project.updated_at,
                    **similarity,
                })

        # 按相似度排序
        similarities.sort(key=lambda x: x["total_score"], reverse=True)

        return similarities[:top_k]

    def _calculate_similarity(
        self,
        current: Project,
        benchmark: Project,
        config: BenchmarkConfiguration,
    ) -> Dict[str, Any]:
        """计算两个项目的相似度"""
        # 行业相似度
        industry_score = self._calculate_industry_similarity(
            getattr(current, "industry", None),
            getattr(benchmark, "industry", None),
        )

        # 测试类型相似度
        test_type_score = self._calculate_test_type_similarity(
            getattr(current, "test_type", None),
            getattr(benchmark, "test_type", None),
        )

        # 规模相似度（基于预估成本）
        scale_score = self._calculate_scale_similarity(
            float(current.estimated_cost or 0),
            float(benchmark.total_cost or benchmark.estimated_cost or 0),
        )

        # 复杂度相似度（基于机台数量）
        complexity_score = self._calculate_complexity_similarity(
            getattr(current, "machine_count", 1),
            getattr(benchmark, "machine_count", 1),
        )

        # 客户类型相似度
        customer_score = self._calculate_customer_similarity(
            getattr(current, "customer_type", None),
            getattr(benchmark, "customer_type", None),
        )

        # 加权总分
        total_score = (
            industry_score * float(config.industry_weight) +
            test_type_score * float(config.test_type_weight) +
            scale_score * float(config.scale_weight) +
            complexity_score * float(config.complexity_weight) +
            customer_score * float(config.customer_weight)
        )

        # 确定相似度级别
        if total_score >= float(config.high_threshold):
            level = SimilarityLevelEnum.HIGH
        elif total_score >= float(config.medium_threshold):
            level = SimilarityLevelEnum.MEDIUM
        elif total_score >= float(config.low_threshold):
            level = SimilarityLevelEnum.LOW
        else:
            level = SimilarityLevelEnum.MINIMAL

        return {
            "total_score": round(total_score, 2),
            "similarity_level": level.value,
            "industry_score": round(industry_score, 2),
            "test_type_score": round(test_type_score, 2),
            "scale_score": round(scale_score, 2),
            "complexity_score": round(complexity_score, 2),
            "customer_score": round(customer_score, 2),
        }

    def _calculate_industry_similarity(
        self, industry1: Optional[str], industry2: Optional[str]
    ) -> float:
        """计算行业相似度"""
        if not industry1 or not industry2:
            return 50.0  # 缺失数据给中等分
        if industry1 == industry2:
            return 100.0
        # 可以添加行业关联性映射
        return 30.0

    def _calculate_test_type_similarity(
        self, type1: Optional[str], type2: Optional[str]
    ) -> float:
        """计算测试类型相似度"""
        if not type1 or not type2:
            return 50.0
        if type1 == type2:
            return 100.0
        # 可以添加测试类型关联性映射
        return 30.0

    def _calculate_scale_similarity(self, cost1: float, cost2: float) -> float:
        """计算规模相似度（基于成本）"""
        if cost1 <= 0 or cost2 <= 0:
            return 50.0

        ratio = min(cost1, cost2) / max(cost1, cost2)
        # 比例越接近1，相似度越高
        return ratio * 100

    def _calculate_complexity_similarity(self, count1: int, count2: int) -> float:
        """计算复杂度相似度（基于机台数量）"""
        if count1 <= 0 or count2 <= 0:
            return 50.0

        ratio = min(count1, count2) / max(count1, count2)
        return ratio * 100

    def _calculate_customer_similarity(
        self, type1: Optional[str], type2: Optional[str]
    ) -> float:
        """计算客户类型相似度"""
        if not type1 or not type2:
            return 50.0
        if type1 == type2:
            return 100.0
        return 30.0

    # ==================== 对标分析 ====================

    def create_benchmark_analysis(
        self,
        project_id: int,
        benchmark_project_id: int,
        analyzed_by: int,
    ) -> ProjectCostBenchmark:
        """
        创建对标分析记录

        Args:
            project_id: 当前项目ID
            benchmark_project_id: 对标项目ID
            analyzed_by: 分析人ID

        Returns:
            对标分析记录
        """
        # 获取项目
        current_project = self.db.query(Project).filter(Project.id == project_id).first()
        benchmark_project = self.db.query(Project).filter(
            Project.id == benchmark_project_id
        ).first()

        if not current_project or not benchmark_project:
            raise ValueError("项目不存在")

        # 获取配置
        config = self.get_default_config()

        # 计算相似度
        similarity = self._calculate_similarity(current_project, benchmark_project, config)

        # 计算成本对比
        current_cost = float(current_project.estimated_cost or 0)
        benchmark_cost = float(benchmark_project.total_cost or benchmark_project.estimated_cost or 0)
        cost_variance = current_cost - benchmark_cost
        cost_variance_ratio = (cost_variance / benchmark_cost * 100) if benchmark_cost > 0 else 0

        # 创建记录
        benchmark = ProjectCostBenchmark(
            project_id=project_id,
            benchmark_project_id=benchmark_project_id,
            similarity_score=Decimal(str(similarity["total_score"])),
            similarity_level=similarity["similarity_level"],
            industry_score=Decimal(str(similarity["industry_score"])),
            test_type_score=Decimal(str(similarity["test_type_score"])),
            scale_score=Decimal(str(similarity["scale_score"])),
            complexity_score=Decimal(str(similarity["complexity_score"])),
            customer_score=Decimal(str(similarity["customer_score"])),
            current_estimated_cost=Decimal(str(current_cost)),
            benchmark_actual_cost=Decimal(str(benchmark_cost)),
            cost_variance=Decimal(str(cost_variance)),
            cost_variance_ratio=Decimal(str(round(cost_variance_ratio, 2))),
            analyzed_by=analyzed_by,
            analyzed_at=datetime.now(),
        )

        self.db.add(benchmark)
        self.db.commit()
        self.db.refresh(benchmark)

        logger.info(
            f"创建对标分析: 项目 {project_id} vs {benchmark_project_id}, "
            f"相似度 {similarity['total_score']}%"
        )

        return benchmark

    def get_project_benchmarks(
        self, project_id: int
    ) -> List[ProjectCostBenchmark]:
        """获取项目的所有对标记录"""
        return (
            self.db.query(ProjectCostBenchmark)
            .filter(ProjectCostBenchmark.project_id == project_id)
            .order_by(desc(ProjectCostBenchmark.similarity_score))
            .all()
        )

    def generate_benchmark_report(
        self, project_id: int
    ) -> Dict[str, Any]:
        """
        生成对标分析报告

        Args:
            project_id: 项目ID

        Returns:
            对标分析报告
        """
        benchmarks = self.get_project_benchmarks(project_id)

        if not benchmarks:
            return {
                "project_id": project_id,
                "benchmark_count": 0,
                "message": "暂无对标分析数据",
            }

        # 汇总统计
        avg_similarity = sum(float(b.similarity_score) for b in benchmarks) / len(benchmarks)
        avg_cost_variance = sum(float(b.cost_variance_ratio or 0) for b in benchmarks) / len(benchmarks)

        # 风险评估
        risk_level = "LOW"
        if avg_cost_variance > 20:
            risk_level = "HIGH"
        elif avg_cost_variance > 10:
            risk_level = "MEDIUM"

        return {
            "project_id": project_id,
            "benchmark_count": len(benchmarks),
            "average_similarity": round(avg_similarity, 2),
            "average_cost_variance_ratio": round(avg_cost_variance, 2),
            "risk_level": risk_level,
            "benchmarks": [
                {
                    "benchmark_project_id": b.benchmark_project_id,
                    "similarity_score": float(b.similarity_score),
                    "similarity_level": b.similarity_level,
                    "cost_variance": float(b.cost_variance or 0),
                    "cost_variance_ratio": float(b.cost_variance_ratio or 0),
                }
                for b in benchmarks
            ],
            "generated_at": datetime.now().isoformat(),
        }
