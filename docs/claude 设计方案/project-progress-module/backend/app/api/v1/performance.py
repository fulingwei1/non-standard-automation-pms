"""
绩效报告 API
支持多角色权限的绩效查询和报告生成
"""
from fastapi import APIRouter, Query, HTTPException
from datetime import date, datetime

from app.services.performance_engine import (
    ReportPeriodType,
    create_report_generator
)

router = APIRouter(prefix="/performance", tags=["绩效报告"])


# ==================== 权限检查 ====================

def check_view_permission(viewer_id: int, viewer_role: str, target_user_id: int, target_dept_id: int = None) -> bool:
    """
    检查查看权限
    
    权限规则：
    - 自己可以看自己
    - 总经理可以看所有人
    - 部门经理可以看本部门
    - 项目经理可以看项目成员
    - 组长可以看本组
    """
    if viewer_id == target_user_id:
        return True
    
    if viewer_role == "gm":
        return True
    
    if viewer_role == "dept_manager":
        # 检查是否同部门（实际需要查数据库）
        return True
    
    if viewer_role == "pm":
        # 检查是否项目成员（实际需要查数据库）
        return True
    
    if viewer_role == "team_leader":
        # 检查是否本组成员
        return True
    
    return False


# ==================== 个人绩效接口 ====================

@router.get("/my", summary="查看我的绩效")
async def get_my_performance(
    period: str = Query("monthly", description="周期: weekly/monthly/quarterly"),
    year: int = Query(None, description="年份"),
    month: int = Query(None, description="月份"),
    # 实际应从JWT获取当前用户
    current_user_id: int = Query(1, description="当前用户ID（测试用）")
):
    """
    查看自己的绩效报告
    
    每个人都可以查看自己的绩效，包括：
    - 工时指标
    - 任务指标
    - 质量指标
    - 协作指标
    - 绩效得分和等级
    - 项目贡献
    - 趋势分析
    - 亮点和待改进
    """
    # 计算周期日期
    if not year:
        year = datetime.now().year
    if not month:
        month = datetime.now().month
    
    period_type = ReportPeriodType(period)
    
    if period_type == ReportPeriodType.MONTHLY:
        period_start = date(year, month, 1)
        if month == 12:
            period_end = date(year + 1, 1, 1)
        else:
            period_end = date(year, month + 1, 1)
        period_end = period_end - __import__('datetime').timedelta(days=1)
    elif period_type == ReportPeriodType.WEEKLY:
        # 本周
        today = date.today()
        period_start = today - __import__('datetime').timedelta(days=today.weekday())
        period_end = period_start + __import__('datetime').timedelta(days=6)
    else:
        period_start = date(year, 1, 1)
        period_end = date(year, 12, 31)
    
    generator = create_report_generator()
    report = generator.generate_individual_report(
        user_id=current_user_id,
        period_type=period_type,
        period_start=period_start,
        period_end=period_end,
        viewer_id=current_user_id,
        viewer_role="engineer"  # 自己看自己
    )
    
    return {
        "code": 200,
        "data": report.to_dict()
    }


@router.get("/user/{user_id}", summary="查看指定人员绩效")
async def get_user_performance(
    user_id: int,
    period: str = Query("monthly", description="周期"),
    year: int = Query(None, description="年份"),
    month: int = Query(None, description="月份"),
    # 实际应从JWT获取
    current_user_id: int = Query(100, description="当前用户ID"),
    current_user_role: str = Query("dept_manager", description="当前用户角色")
):
    """
    查看指定人员的绩效报告
    
    权限控制：
    - 总经理：可查看所有人
    - 部门经理：可查看本部门人员
    - 项目经理：可查看项目成员
    - 组长：可查看本组成员
    - 普通员工：仅可查看自己
    """
    # 权限检查
    if not check_view_permission(current_user_id, current_user_role, user_id):
        raise HTTPException(status_code=403, detail="无权查看该人员绩效")
    
    # 计算周期
    if not year:
        year = datetime.now().year
    if not month:
        month = datetime.now().month
    
    period_type = ReportPeriodType(period)
    period_start = date(year, month, 1)
    if month == 12:
        period_end = date(year + 1, 1, 1) - __import__('datetime').timedelta(days=1)
    else:
        period_end = date(year, month + 1, 1) - __import__('datetime').timedelta(days=1)
    
    generator = create_report_generator()
    report = generator.generate_individual_report(
        user_id=user_id,
        period_type=period_type,
        period_start=period_start,
        period_end=period_end,
        viewer_id=current_user_id,
        viewer_role=current_user_role
    )
    
    return {
        "code": 200,
        "data": report.to_dict()
    }


# ==================== 团队绩效接口 ====================

@router.get("/team/{team_id}", summary="查看团队绩效汇总")
async def get_team_performance(
    team_id: int,
    period: str = Query("monthly", description="周期"),
    year: int = Query(None, description="年份"),
    month: int = Query(None, description="月份"),
    current_user_role: str = Query("dept_manager", description="当前用户角色")
):
    """
    查看团队绩效汇总
    
    仅部门经理及以上可查看，包括：
    - 团队平均分、最高分、最低分
    - 等级分布
    - 成员排名
    - 环比和部门对比
    """
    if current_user_role not in ["gm", "dept_manager", "team_leader"]:
        raise HTTPException(status_code=403, detail="无权查看团队绩效")
    
    if not year:
        year = datetime.now().year
    if not month:
        month = datetime.now().month
    
    period_start = date(year, month, 1)
    if month == 12:
        period_end = date(year + 1, 1, 1) - __import__('datetime').timedelta(days=1)
    else:
        period_end = date(year, month + 1, 1) - __import__('datetime').timedelta(days=1)
    
    generator = create_report_generator()
    summary = generator.generate_team_summary(
        team_id=team_id,
        period_type=ReportPeriodType(period),
        period_start=period_start,
        period_end=period_end
    )
    
    return {
        "code": 200,
        "data": summary.to_dict()
    }


@router.get("/department/{dept_id}", summary="查看部门绩效汇总")
async def get_department_performance(
    dept_id: int,
    period: str = Query("monthly", description="周期"),
    year: int = Query(None, description="年份"),
    month: int = Query(None, description="月份"),
    current_user_role: str = Query("gm", description="当前用户角色")
):
    """
    查看部门绩效汇总
    
    仅部门经理及以上可查看
    """
    if current_user_role not in ["gm", "dept_manager"]:
        raise HTTPException(status_code=403, detail="无权查看部门绩效")
    
    # 复用团队汇总逻辑
    if not year:
        year = datetime.now().year
    if not month:
        month = datetime.now().month
    
    period_start = date(year, month, 1)
    if month == 12:
        period_end = date(year + 1, 1, 1) - __import__('datetime').timedelta(days=1)
    else:
        period_end = date(year, month + 1, 1) - __import__('datetime').timedelta(days=1)
    
    generator = create_report_generator()
    
    # 部门下所有团队汇总
    teams = [1, 2, 3]  # 模拟部门下的团队
    all_members = []
    
    for team_id in teams:
        summary = generator.generate_team_summary(
            team_id=team_id,
            period_type=ReportPeriodType(period),
            period_start=period_start,
            period_end=period_end
        )
        all_members.extend(summary.members_ranking)
    
    # 重新排名
    all_members.sort(key=lambda x: x['score'], reverse=True)
    for i, m in enumerate(all_members):
        m['dept_rank'] = i + 1
    
    scores = [m['score'] for m in all_members]
    
    return {
        "code": 200,
        "data": {
            "dept_id": dept_id,
            "dept_name": "研发部",
            "period": f"{year}-{month:02d}",
            "member_count": len(all_members),
            "avg_score": round(sum(scores) / len(scores), 1) if scores else 0,
            "max_score": max(scores) if scores else 0,
            "min_score": min(scores) if scores else 0,
            "level_distribution": {
                "excellent": len([m for m in all_members if m['level'] == 'excellent']),
                "good": len([m for m in all_members if m['level'] == 'good']),
                "qualified": len([m for m in all_members if m['level'] == 'qualified']),
                "needs_improvement": len([m for m in all_members if m['level'] == 'needs_improvement'])
            },
            "members_ranking": all_members[:20]  # 只返回前20
        }
    }


# ==================== 项目绩效接口 ====================

@router.get("/project/{project_id}", summary="查看项目成员绩效")
async def get_project_performance(
    project_id: int,
    period: str = Query("monthly", description="周期"),
    year: int = Query(None, description="年份"),
    month: int = Query(None, description="月份"),
    current_user_role: str = Query("pm", description="当前用户角色")
):
    """
    查看项目成员绩效
    
    项目经理及以上可查看，展示：
    - 项目整体进度
    - 各成员在项目中的贡献
    - 工时投入
    - 任务完成情况
    """
    if current_user_role not in ["gm", "dept_manager", "pm"]:
        raise HTTPException(status_code=403, detail="无权查看项目绩效")
    
    if not year:
        year = datetime.now().year
    if not month:
        month = datetime.now().month
    
    period_start = date(year, month, 1)
    if month == 12:
        period_end = date(year + 1, 1, 1) - __import__('datetime').timedelta(days=1)
    else:
        period_end = date(year, month + 1, 1) - __import__('datetime').timedelta(days=1)
    
    generator = create_report_generator()
    report = generator.generate_project_progress(
        project_id=project_id,
        period_start=period_start,
        period_end=period_end
    )
    
    return {
        "code": 200,
        "data": report.to_dict()
    }


@router.get("/project/{project_id}/progress", summary="项目进展报告")
async def get_project_progress_report(
    project_id: int,
    period: str = Query("weekly", description="周期: weekly/monthly"),
    current_user_role: str = Query("pm", description="当前用户角色")
):
    """
    生成项目进展报告
    
    包括：
    - 整体进度对比（计划vs实际）
    - 里程碑状态
    - 工时投入分析
    - 成本分析
    - 成员绩效
    - 风险与问题
    - 本期完成事项
    - 下期计划
    """
    today = date.today()
    
    if period == "weekly":
        period_start = today - __import__('datetime').timedelta(days=today.weekday())
        period_end = period_start + __import__('datetime').timedelta(days=6)
    else:
        period_start = date(today.year, today.month, 1)
        if today.month == 12:
            period_end = date(today.year + 1, 1, 1) - __import__('datetime').timedelta(days=1)
        else:
            period_end = date(today.year, today.month + 1, 1) - __import__('datetime').timedelta(days=1)
    
    generator = create_report_generator()
    report = generator.generate_project_progress(
        project_id=project_id,
        period_start=period_start,
        period_end=period_end
    )
    
    return {
        "code": 200,
        "data": report.to_dict()
    }


# ==================== 绩效对比接口 ====================

@router.get("/compare", summary="绩效对比")
async def compare_performance(
    user_ids: str = Query(..., description="用户ID列表，逗号分隔"),
    period: str = Query("monthly", description="周期"),
    year: int = Query(None, description="年份"),
    month: int = Query(None, description="月份"),
    current_user_role: str = Query("dept_manager", description="当前用户角色")
):
    """
    对比多人绩效
    
    仅管理层可用，用于绩效评定参考
    """
    if current_user_role not in ["gm", "dept_manager"]:
        raise HTTPException(status_code=403, detail="无权进行绩效对比")
    
    ids = [int(x) for x in user_ids.split(",")]
    
    if not year:
        year = datetime.now().year
    if not month:
        month = datetime.now().month
    
    period_start = date(year, month, 1)
    if month == 12:
        period_end = date(year + 1, 1, 1) - __import__('datetime').timedelta(days=1)
    else:
        period_end = date(year, month + 1, 1) - __import__('datetime').timedelta(days=1)
    
    generator = create_report_generator()
    
    comparisons = []
    for user_id in ids:
        report = generator.generate_individual_report(
            user_id=user_id,
            period_type=ReportPeriodType(period),
            period_start=period_start,
            period_end=period_end,
            viewer_id=100,
            viewer_role=current_user_role
        )
        
        comparisons.append({
            "user_id": user_id,
            "user_name": report.user_name,
            "department": report.department,
            "total_score": report.score.total_score,
            "level": report.score.level.value,
            "workload_score": report.score.workload_score,
            "task_score": report.score.task_score,
            "quality_score": report.score.quality_score,
            "collaboration_score": report.score.collaboration_score,
            "task_completion_rate": report.tasks.completion_rate,
            "on_time_rate": report.tasks.on_time_rate,
            "highlights_count": len(report.highlights),
            "improvements_count": len(report.improvements)
        })
    
    # 按总分排序
    comparisons.sort(key=lambda x: x['total_score'], reverse=True)
    
    return {
        "code": 200,
        "data": {
            "period": f"{year}-{month:02d}",
            "comparisons": comparisons
        }
    }


# ==================== 趋势分析接口 ====================

@router.get("/trends/{user_id}", summary="绩效趋势分析")
async def get_performance_trends(
    user_id: int,
    period: str = Query("monthly", description="周期"),
    count: int = Query(6, description="期数"),
    current_user_id: int = Query(1, description="当前用户ID"),
    current_user_role: str = Query("engineer", description="当前用户角色")
):
    """
    获取绩效趋势数据
    
    用于绘制趋势图表
    """
    # 权限检查
    if user_id != current_user_id and current_user_role not in ["gm", "dept_manager", "pm", "team_leader"]:
        raise HTTPException(status_code=403, detail="无权查看该人员趋势")
    
    # 模拟趋势数据
    trends = [
        {"period": "2024-12", "score": 82.5, "level": "good", "workload": 85, "task": 80, "quality": 88, "collaboration": 75},
        {"period": "2024-11", "score": 78.3, "level": "qualified", "workload": 80, "task": 75, "quality": 82, "collaboration": 70},
        {"period": "2024-10", "score": 85.1, "level": "good", "workload": 88, "task": 85, "quality": 90, "collaboration": 78},
        {"period": "2024-09", "score": 80.2, "level": "good", "workload": 82, "task": 78, "quality": 85, "collaboration": 72},
        {"period": "2024-08", "score": 76.8, "level": "qualified", "workload": 78, "task": 72, "quality": 80, "collaboration": 68},
        {"period": "2024-07", "score": 79.5, "level": "qualified", "workload": 80, "task": 76, "quality": 83, "collaboration": 70},
    ][:count]
    
    # 计算趋势
    if len(trends) >= 2:
        trend_direction = "up" if trends[0]['score'] > trends[1]['score'] else "down"
        trend_change = trends[0]['score'] - trends[1]['score']
    else:
        trend_direction = "stable"
        trend_change = 0
    
    return {
        "code": 200,
        "data": {
            "user_id": user_id,
            "period_type": period,
            "trends": trends,
            "analysis": {
                "trend_direction": trend_direction,
                "trend_change": round(trend_change, 1),
                "avg_score": round(sum(t['score'] for t in trends) / len(trends), 1),
                "best_month": max(trends, key=lambda x: x['score'])['period'],
                "worst_month": min(trends, key=lambda x: x['score'])['period']
            }
        }
    }


# ==================== 排行榜接口 ====================

@router.get("/ranking", summary="绩效排行榜")
async def get_performance_ranking(
    scope: str = Query("department", description="范围: team/department/company"),
    scope_id: int = Query(None, description="范围ID"),
    period: str = Query("monthly", description="周期"),
    year: int = Query(None, description="年份"),
    month: int = Query(None, description="月份"),
    limit: int = Query(10, description="返回数量"),
    current_user_role: str = Query("dept_manager", description="当前用户角色")
):
    """
    获取绩效排行榜
    
    根据查看者权限展示不同范围
    """
    # 权限检查
    if scope == "company" and current_user_role != "gm":
        raise HTTPException(status_code=403, detail="无权查看公司级排行")
    if scope == "department" and current_user_role not in ["gm", "dept_manager"]:
        raise HTTPException(status_code=403, detail="无权查看部门级排行")
    
    # 模拟排行数据
    ranking = [
        {"rank": 1, "user_id": 1, "user_name": "张三", "department": "机械组", "score": 92.5, "level": "excellent", "change": 2},
        {"rank": 2, "user_id": 5, "user_name": "周八", "department": "电气组", "score": 90.2, "level": "excellent", "change": 0},
        {"rank": 3, "user_id": 2, "user_name": "李四", "department": "电气组", "score": 88.5, "level": "good", "change": 1},
        {"rank": 4, "user_id": 6, "user_name": "吴九", "department": "软件组", "score": 86.8, "level": "good", "change": -2},
        {"rank": 5, "user_id": 3, "user_name": "王五", "department": "软件组", "score": 85.2, "level": "good", "change": 0},
        {"rank": 6, "user_id": 7, "user_name": "郑十", "department": "机械组", "score": 82.0, "level": "good", "change": 1},
        {"rank": 7, "user_id": 4, "user_name": "赵六", "department": "测试组", "score": 80.5, "level": "good", "change": -1},
        {"rank": 8, "user_id": 8, "user_name": "钱十一", "department": "电气组", "score": 78.3, "level": "qualified", "change": 0},
        {"rank": 9, "user_id": 9, "user_name": "孙十二", "department": "软件组", "score": 75.6, "level": "qualified", "change": 2},
        {"rank": 10, "user_id": 10, "user_name": "李十三", "department": "机械组", "score": 72.1, "level": "qualified", "change": -3},
    ][:limit]
    
    if not year:
        year = datetime.now().year
    if not month:
        month = datetime.now().month
    
    return {
        "code": 200,
        "data": {
            "scope": scope,
            "scope_name": "研发部" if scope == "department" else "全公司",
            "period": f"{year}-{month:02d}",
            "ranking": ranking,
            "total_count": 45,  # 模拟
            "stats": {
                "avg_score": 83.2,
                "median_score": 82.0,
                "top_10_percent_threshold": 88.5
            }
        }
    }
