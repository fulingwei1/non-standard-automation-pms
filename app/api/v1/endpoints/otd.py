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
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
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
    detail_level: str = Query(
        "summary",
        description="full=完整 risk_items(详情用) / summary=精简(列表用,响应小10倍)",
    ),
    force_refresh: bool = Query(
        False, description="强制刷新，跳过缓存（PM 改了项目状态后立即看最新数据）"
    ),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    实时扫描执行中项目（生命周期 S2~S8）的 11 维 OTD 风险。

    - create_alerts=False（默认）：只读查看，不产预警，不调 AI（快）
    - create_alerts=True：产预警+推送，调 AI 归因
    - detail_level=summary（默认）：精简模式，适合列表；full 适合详情下钻
    - force_refresh=True：跳过缓存，立即重算（PM 改了项目状态后用）
    - 只读模式（create_alerts=False）带 120s 缓存
    """
    from app.services.otd import OTDScanService

    # 只读模式缓存 120s（create_alerts=True 不缓存，避免漏发预警）
    if not create_alerts and not force_refresh:
        from app.utils.cache_decorator import get_cache_service

        cache = get_cache_service()
        cache_key = f"otd_scan:{detail_level}"
        cached = cache.get(cache_key)
        if cached is not None:
            cached["_from_cache"] = True
            return ResponseModel(
                code=200, message="(缓存) OTD 扫描结果", data=cached
            )

    result = OTDScanService(db).batch_scan(
        active_only=True,
        create_alerts=create_alerts,
        detail_level=detail_level,
    )

    # 只读模式写缓存（force_refresh 后也写缓存，供后续普通请求使用）
    if not create_alerts:
        result["_from_cache"] = False
        cache.set(cache_key, result, expire_seconds=120)

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


# ================================================================
# 对比端点（静态路由，排在 /scan/{project_id} 前面）
# ================================================================


@router.get(
    "/compare",
    response_model=ResponseModel,
    summary="项目间对比（风险/毛利/进度并排）",
)
def otd_compare_projects(
    ids: str = Query(..., description="项目ID列表，逗号分隔，如 ids=1,2,3"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """多项目并排对比：风险等级/毛利/进度/变更/延期。

    找出多项目共有的风险维度（shared_risks）。
    """
    from app.services.otd.compare_service import OTDCompareService

    try:
        project_ids = [int(x.strip()) for x in ids.split(",") if x.strip()]
    except ValueError:
        raise HTTPException(status_code=400, detail="ids 参数格式错误，应为逗号分隔的数字")

    if not project_ids:
        raise HTTPException(status_code=400, detail="至少提供 1 个项目ID")
    if len(project_ids) > 10:
        raise HTTPException(status_code=400, detail="最多对比 10 个项目")

    result = OTDCompareService(db).compare_projects(project_ids)
    return ResponseModel(
        code=200,
        message=f"对比 {result['project_count']} 个项目，{len(result['shared_risks'])} 个共有风险维度",
        data=result,
    )


@router.get(
    "/compare/trend",
    response_model=ResponseModel,
    summary="时间对比（本期 vs 上期指标变化）",
)
def otd_compare_trend(
    days: int = Query(30, description="对比周期天数（默认 30 天）"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """全局指标"本期 vs 上期"变化，direction 标注 better/worse/stable。"""
    from app.services.otd.compare_service import OTDCompareService

    result = OTDCompareService(db).compare_trend(days)
    s = result["summary"]
    return ResponseModel(
        code=200,
        message=(
            f"时间对比（{days}天）：{s['better_count']} 项改善 / "
            f"{s['worse_count']} 项恶化 / {s['stable_count']} 项持平"
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


@router.get("/scan/export", summary="导出 OTD 扫描结果到 Excel")
def otd_scan_export(
    detail_level: str = Query(
        "summary",
        description="full=完整 risk_items(详情用) / summary=精简(列表用,响应小10倍)",
    ),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """导出 OTD 全量扫描结果到 Excel。

    生成包含项目编码、项目名称、阶段、风险等级、主因等信息的 Excel 文件。
    summary 模式导出精简信息，full 模式导出完整风险维度详情。
    """
    from app.services.otd import OTDScanService
    from app.services.otd.otd_export_service import OTDExportService

    # 执行扫描（不缓存，导出需要最新数据）
    scan_data = OTDScanService(db).batch_scan(
        active_only=True,
        create_alerts=False,
        detail_level=detail_level,
    )

    # 导出到 Excel
    excel_file = OTDExportService.export_scan_to_excel(scan_data, detail_level)
    excel_file.seek(0)

    # 返回文件流
    filename = f"OTD风险扫描_{date.today().isoformat()}.xlsx"
    return StreamingResponse(
        excel_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"},
    )


@router.get(
    "/scan/{project_id}/export", summary="导出单项目 OTD 扫描结果到 Excel"
)
def otd_scan_project_export(
    project_id: int,
    include_ai: bool = Query(True, description="是否包含 AI 归因建议"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """导出单项目 OTD 扫描结果到 Excel（多 Sheet：项目概览 + 风险维度）。"""
    from app.services.otd import OTDScanService
    from app.services.otd.otd_export_service import OTDExportService

    profile = OTDScanService(db).scan_project(project_id, include_ai=include_ai)
    if "error" in profile:
        raise HTTPException(status_code=404, detail=profile["error"])

    excel_file = OTDExportService.export_project_scan_to_excel(profile)
    excel_file.seek(0)
    filename = f"OTD_{profile.get('project_code', project_id)}_{date.today().isoformat()}.xlsx"
    return StreamingResponse(
        excel_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"},
    )


@router.get(
    "/scan/{project_id}", response_model=ResponseModel, summary="单项目 OTD 全景"
)
def otd_scan_project(
    project_id: int,
    include_ai: bool = Query(True, description="是否调 AI 归因（false 跳过，响应更快）"),
    force_refresh: bool = Query(
        False, description="强制刷新，跳过缓存（PM 改了项目状态后立即看最新数据）"
    ),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """单项目 11 维 OTD 风险全景。

    - include_ai=false：跳过 AI 归因（省 2-5 秒），用规则兜底给 suggestion
    - force_refresh=true：跳过缓存，立即重算（PM 改了项目状态后用）
    """
    from app.services.otd import OTDScanService

    # 缓存 60s（单项目扫描，include_ai 影响缓存 key）
    if not force_refresh:
        from app.utils.cache_decorator import get_cache_service

        cache = get_cache_service()
        cache_key = f"otd_scan_project:{project_id}:{include_ai}"
        cached = cache.get(cache_key)
        if cached is not None:
            cached["_from_cache"] = True
            return ResponseModel(
                code=200,
                message=f"(缓存) 项目 {cached.get('project_code')} OTD 风险等级 {cached.get('severity')}",
                data=cached,
            )

    profile = OTDScanService(db).scan_project(project_id, include_ai=include_ai)

    # 写缓存
    if not force_refresh:
        profile["_from_cache"] = False
        cache.set(cache_key, profile, expire_seconds=60)

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
    include_offenders: bool = Query(
        True, description="是否包含 top_offenders 下钻（拖后腿的项目 Top5）"
    ),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """7 核心指标聚合 + 下钻：每个指标含 top_offenders（拖后腿的项目 Top5）。

    设 include_offenders=false 可只看聚合数字（响应更小）。
    """
    from app.services.otd import OTDMetricsService

    result = OTDMetricsService(db).get_metrics(
        start_date, end_date, include_offenders=include_offenders
    )
    return ResponseModel(code=200, message="OTD 核心指标", data=result)


@router.get("/metrics/export", summary="导出 OTD 7 核心指标到 Excel")
def otd_metrics_export(
    start_date: Optional[date] = Query(None, description="起始日期（默认本季度初）"),
    end_date: Optional[date] = Query(None, description="结束日期（默认本季度末）"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """导出 OTD 7 核心指标到 Excel。

    生成包含指标概览和下钻数据（top_offenders）的 Excel 文件。
    """
    from app.services.otd import OTDMetricsService
    from app.services.otd.margin_export_service import MarginExportService

    # 获取指标数据
    metrics_data = OTDMetricsService(db).get_metrics(
        start_date, end_date, include_offenders=True
    )

    # 导出到 Excel
    excel_file = MarginExportService.export_metrics_to_excel(metrics_data)
    excel_file.seek(0)

    # 返回文件流
    filename = f"OTD核心指标_{date.today().isoformat()}.xlsx"
    return StreamingResponse(
        excel_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"},
    )


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
