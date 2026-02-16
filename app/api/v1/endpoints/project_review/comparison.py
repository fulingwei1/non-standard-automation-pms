"""
项目对比分析API端点
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.project_review import (
    ComparisonRequest,
    ComparisonResponse,
    ImprovementResponse
)
from app.services.project_review_ai import ProjectComparisonAnalyzer

router = APIRouter()


@router.post("/compare", response_model=ComparisonResponse)
async def compare_with_history(
    request: ComparisonRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    与历史项目对比
    
    - **review_id**: 复盘报告ID
    - **similarity_type**: 相似度类型（industry/type/scale）
    - **comparison_limit**: 对比项目数量
    """
    analyzer = ProjectComparisonAnalyzer(db)
    
    try:
        result = analyzer.compare_with_history(
            review_id=request.review_id,
            similarity_type=request.similarity_type,
            limit=request.comparison_limit
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    # 转换为响应格式
    from app.schemas.project_review.comparison import (
        ComparisonMetrics,
        VarianceAnalysis,
        ComparisonItem,
        ImprovementItem,
        BenchmarkItem
    )
    
    current_metrics = ComparisonMetrics(**result['comparison']['current'])
    historical_avg = ComparisonMetrics(**result['comparison']['historical_average'])
    variance = VarianceAnalysis(**result['comparison']['variance_analysis'])
    
    strengths = [ComparisonItem(**s) for s in result['analysis'].get('strengths', [])]
    weaknesses = [ComparisonItem(**w) for w in result['analysis'].get('weaknesses', [])]
    improvements = [ImprovementItem(**i) for i in result['analysis'].get('improvements', [])]
    
    benchmarks = {}
    for key, value in result['analysis'].get('benchmarks', {}).items():
        if isinstance(value, dict):
            benchmarks[key] = BenchmarkItem(**value)
    
    return ComparisonResponse(
        success=True,
        review_id=request.review_id,
        current_metrics=current_metrics,
        historical_average=historical_avg,
        variance_analysis=variance,
        strengths=strengths,
        weaknesses=weaknesses,
        improvements=improvements,
        benchmarks=benchmarks,
        similar_projects_count=len(result['similar_reviews'])
    )


@router.get("/{review_id}/improvements", response_model=ImprovementResponse)
async def get_improvements(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取改进建议
    
    基于历史项目对比，识别当前项目可以改进的方面
    """
    analyzer = ProjectComparisonAnalyzer(db)
    
    try:
        improvements = analyzer.identify_improvements(review_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    from app.schemas.project_review.comparison import ImprovementItem
    
    return ImprovementResponse(
        success=True,
        review_id=review_id,
        improvements=[ImprovementItem(**imp) for imp in improvements],
        total_count=len(improvements)
    )


@router.get("/{review_id}/benchmarks")
async def get_benchmarks(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取项目基准对比"""
    analyzer = ProjectComparisonAnalyzer(db)
    
    try:
        result = analyzer.compare_with_history(review_id, similarity_type='industry', limit=10)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    return {
        "review_id": review_id,
        "benchmarks": result['analysis'].get('benchmarks', {}),
        "comparison_base": result['comparison']
    }
