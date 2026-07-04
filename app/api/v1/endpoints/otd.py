# -*- coding: utf-8 -*-
"""
OTD 项目交付智能体 API

端点：
  GET  /otd/scan                  全量 OTD 扫描（实时，同步，限 200 项目）
  GET  /otd/scan/{project_id}     单项目 10 维全景
  GET  /otd/metrics               7 核心指标聚合（支持 start_date/end_date）
  GET  /otd/metrics/{project_id}  单项目指标
  POST /otd/scan/run              手动触发后台扫描任务（管理员）
"""
from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter(prefix="/otd", tags=["OTD项目交付智能体"])


def _require_pmo_or_admin(current_user: User) -> None:
    """权限门禁：仅 PMO/管理员可手动触发扫描。读取类端点不限制。

    解析用户角色：User.roles 是 UserRole 关系（lazy dynamic），
    每个 UserRole.role.role_code 才是真正的角色编码。
    无角色配置时放行（开发环境友好）。
    """
    if getattr(current_user, "is_superuser", False):
        return

    role_codes: set = set()
    roles = getattr(current_user, "roles", None)
    if roles is not None:
        try:
            for ur in roles:
                # ur 是 UserRole，role_code 在 ur.role 上
                code = getattr(getattr(ur, "role", None), "role_code", None)
                if code:
                    role_codes.add(code)
        except Exception:
            pass

    # 无角色配置时放行（兼容开发环境/未配角色的用户）
    if not role_codes:
        return

    allowed = role_codes & {"ADMIN", "PMO", "SUPER_ADMIN", "pmo", "admin"}
    if not allowed:
        raise HTTPException(status_code=403, detail="仅 PMO/管理员可执行此操作")


# ================================================================
# 扫描端点
# ================================================================


@router.get("/scan", response_model=ResponseModel, summary="OTD 全量交付风险扫描")
def otd_scan(
    create_alerts: bool = Query(
        False, description="是否对 HIGH/CRITICAL 产出预警并推送（默认 False，仅查看）"
    ),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    实时扫描执行中项目（生命周期 S2~S8）的 10 维 OTD 风险。

    默认 create_alerts=False（只读查看，不产预警），
    设为 true 时会对 HIGH/CRITICAL 项目创建 AlertRecord 并推送站内+邮件。
    """
    from app.services.otd import OTDScanService

    result = OTDScanService(db).batch_scan(
        active_only=True, create_alerts=create_alerts
    )
    return ResponseModel(
        code=200,
        message=(
            f"扫描 {result['scanned']} 个项目，发现 {result['with_risk']} 个有风险，"
            f"其中 {result['high_or_critical']} 个 HIGH/CRITICAL"
            + (f"，新建 {result['alerts_created']} 条预警" if create_alerts else "")
        ),
        data=result,
    )


# 手动触发后台扫描（注意：静态路由 /scan/run 必须排在动态路由 /scan/{project_id} 前面，
# 否则 "run" 会被 {project_id} 吃掉 —— AGENTS.md 铁律 #6）
class ScanRunResponse(BaseModel):
    job_status: str
    message: str


@router.post(
    "/scan/run",
    response_model=ResponseModel,
    summary="手动触发 OTD 每日扫描任务（PMO/管理员）",
)
def otd_scan_run(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    同步执行一次完整的 OTD 扫描（含预警产出与推送）。
    用于 PMO 主动触发，不等定时任务。
    """
    _require_pmo_or_admin(current_user)
    from app.services.otd import OTDScanService

    result = OTDScanService(db).batch_scan(
        active_only=True, create_alerts=True, create_snapshot=True
    )
    return ResponseModel(
        code=200,
        message=(
            f"扫描完成：{result['scanned']} 个项目，"
            f"{result['high_or_critical']} 个 HIGH/CRITICAL，"
            f"新建 {result['alerts_created']} 条预警"
        ),
        data=result,
    )


@router.get(
    "/scan/trend",
    response_model=ResponseModel,
    summary="全局风险趋势（每日各等级项目数 + 维度命中热力图）",
)
def otd_global_trend(
    days: int = Query(30, description="趋势天数（默认 30）"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """全局 OTD 风险趋势。照抄 risk_analytics.py 的 /risk-report/trend。"""
    from app.services.otd.trend_service import OTDTrendService

    result = OTDTrendService(db).get_global_trend(days)
    return ResponseModel(
        code=200,
        message=f"全局风险趋势（{days} 天，{result['total_snapshots']} 条快照）",
        data=result,
    )


@router.get(
    "/scan/{project_id}", response_model=ResponseModel, summary="单项目 OTD 全景"
)
def otd_scan_project(
    project_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """单项目 10 维 OTD 风险全景（含可选 AI 归因 suggestion）。"""
    from app.services.otd import OTDScanService

    profile = OTDScanService(db).scan_project(project_id)
    return ResponseModel(
        code=200,
        message=f"项目 {profile.get('project_code')} OTD 风险等级 {profile.get('severity')}",
        data=profile,
    )


@router.get(
    "/scan/{project_id}/trend",
    response_model=ResponseModel,
    summary="单项目风险趋势（severity/各维度命中随时间）",
)
def otd_project_trend(
    project_id: int,
    days: int = Query(30, description="趋势天数（默认 30）"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """单项目风险趋势。照抄 HealthTrendService.get_health_trend。"""
    from app.services.otd.trend_service import OTDTrendService

    result = OTDTrendService(db).get_project_trend(project_id, days)
    if "error" in result:
        return ResponseModel(code=404, message=result["error"], data=result)
    return ResponseModel(
        code=200,
        message=f"项目风险趋势（{days} 天，{result.get('snapshot_count', 0)} 条快照）",
        data=result,
    )


# ================================================================
# 指标端点
# ================================================================


@router.get("/metrics", response_model=ResponseModel, summary="OTD 7 核心指标")
def otd_metrics(
    start_date: Optional[date] = Query(None, description="起始日期（默认本季度初）"),
    end_date: Optional[date] = Query(None, description="结束日期（默认本季度末）"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """7 核心指标聚合：准时交付率/延期天数/返工/变更/毛利/验收周期/投诉率。"""
    from app.services.otd import OTDMetricsService

    result = OTDMetricsService(db).get_metrics(start_date, end_date)
    return ResponseModel(code=200, message="OTD 核心指标", data=result)


@router.get(
    "/metrics/{project_id}", response_model=ResponseModel, summary="单项目 OTD 指标"
)
def otd_project_metrics(
    project_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    from app.services.otd import OTDMetricsService

    result = OTDMetricsService(db).get_project_metrics(project_id)
    if "error" in result:
        return ResponseModel(code=404, message=result["error"], data=result)
    return ResponseModel(code=200, message="单项目 OTD 指标", data=result)
