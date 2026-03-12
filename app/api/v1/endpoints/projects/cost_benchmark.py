# -*- coding: utf-8 -*-
"""
成本对标 API

提供项目成本对标分析的 API 端点：
- 查找相似历史项目
- 创建对标分析
- 获取对标记录
- 生成对标报告
"""

from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.services.project.cost_benchmark_service import CostBenchmarkService

router = APIRouter()


# ==================== Schema ====================


class SimilarProjectItem(BaseModel):
    """相似项目信息"""

    project_id: int
    project_name: str
    project_no: Optional[str] = None
    customer_name: Optional[str] = None
    industry: Optional[str] = None
    test_type: Optional[str] = None
    total_cost: float
    completed_at: Optional[str] = None
    total_score: float
    similarity_level: str
    industry_score: float
    test_type_score: float
    scale_score: float
    complexity_score: float
    customer_score: float


class CreateBenchmarkRequest(BaseModel):
    """创建对标请求"""

    benchmark_project_id: int = Field(..., description="对标项目ID")


class BenchmarkResponse(BaseModel):
    """对标记录响应"""

    id: int
    project_id: int
    benchmark_project_id: int
    similarity_score: float
    similarity_level: str
    industry_score: float
    test_type_score: float
    scale_score: float
    complexity_score: float
    customer_score: float
    current_estimated_cost: float
    benchmark_actual_cost: float
    cost_variance: float
    cost_variance_ratio: float


class BenchmarkReportResponse(BaseModel):
    """对标报告响应"""

    project_id: int
    benchmark_count: int
    average_similarity: Optional[float] = None
    average_cost_variance_ratio: Optional[float] = None
    risk_level: Optional[str] = None
    message: Optional[str] = None


# ==================== API ====================


@router.get(
    "/{project_id}/similar-projects",
    response_model=List[SimilarProjectItem],
    summary="查找相似历史项目",
    description="根据项目特征（行业、测试类型、规模等）查找相似的已完成项目",
)
def find_similar_projects(
    project_id: int,
    top_k: int = Query(10, ge=1, le=50, description="返回数量"),
    min_similarity: float = Query(30.0, ge=0, le=100, description="最小相似度"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """查找与指定项目相似的历史项目"""
    service = CostBenchmarkService(db)

    try:
        similar_projects = service.find_similar_projects(
            project_id=project_id,
            top_k=top_k,
            min_similarity=min_similarity,
        )
        return similar_projects
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post(
    "/{project_id}/cost-benchmark",
    response_model=BenchmarkResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建对标分析",
    description="创建当前项目与指定历史项目的成本对标分析",
)
def create_benchmark(
    project_id: int,
    data: CreateBenchmarkRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """创建成本对标分析"""
    service = CostBenchmarkService(db)

    try:
        benchmark = service.create_benchmark_analysis(
            project_id=project_id,
            benchmark_project_id=data.benchmark_project_id,
            analyzed_by=current_user.id,
        )
        return BenchmarkResponse(
            id=benchmark.id,
            project_id=benchmark.project_id,
            benchmark_project_id=benchmark.benchmark_project_id,
            similarity_score=float(benchmark.similarity_score or 0),
            similarity_level=benchmark.similarity_level or "LOW",
            industry_score=float(benchmark.industry_score or 0),
            test_type_score=float(benchmark.test_type_score or 0),
            scale_score=float(benchmark.scale_score or 0),
            complexity_score=float(benchmark.complexity_score or 0),
            customer_score=float(benchmark.customer_score or 0),
            current_estimated_cost=float(benchmark.current_estimated_cost or 0),
            benchmark_actual_cost=float(benchmark.benchmark_actual_cost or 0),
            cost_variance=float(benchmark.cost_variance or 0),
            cost_variance_ratio=float(benchmark.cost_variance_ratio or 0),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/{project_id}/cost-benchmark",
    response_model=List[BenchmarkResponse],
    summary="获取对标记录",
    description="获取项目的所有成本对标记录",
)
def get_benchmarks(
    project_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取项目的对标记录列表"""
    service = CostBenchmarkService(db)
    benchmarks = service.get_project_benchmarks(project_id)

    return [
        BenchmarkResponse(
            id=b.id,
            project_id=b.project_id,
            benchmark_project_id=b.benchmark_project_id,
            similarity_score=float(b.similarity_score or 0),
            similarity_level=b.similarity_level or "LOW",
            industry_score=float(b.industry_score or 0),
            test_type_score=float(b.test_type_score or 0),
            scale_score=float(b.scale_score or 0),
            complexity_score=float(b.complexity_score or 0),
            customer_score=float(b.customer_score or 0),
            current_estimated_cost=float(b.current_estimated_cost or 0),
            benchmark_actual_cost=float(b.benchmark_actual_cost or 0),
            cost_variance=float(b.cost_variance or 0),
            cost_variance_ratio=float(b.cost_variance_ratio or 0),
        )
        for b in benchmarks
    ]


@router.get(
    "/{project_id}/cost-benchmark/report",
    response_model=BenchmarkReportResponse,
    summary="生成对标报告",
    description="生成项目成本对标分析报告，包含风险评估",
)
def generate_benchmark_report(
    project_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """生成对标分析报告"""
    service = CostBenchmarkService(db)
    report = service.generate_benchmark_report(project_id)

    return BenchmarkReportResponse(
        project_id=report["project_id"],
        benchmark_count=report["benchmark_count"],
        average_similarity=report.get("average_similarity"),
        average_cost_variance_ratio=report.get("average_cost_variance_ratio"),
        risk_level=report.get("risk_level"),
        message=report.get("message"),
    )
