# -*- coding: utf-8 -*-
"""
看板 - 自动生成
从 assembly_kit.py 拆分
"""

# -*- coding: utf-8 -*-
"""
齐套分析模块 API 端点

基于装配工艺路径的智能齐套分析系统
"""

import logging
from datetime import date
from decimal import Decimal
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

logger = logging.getLogger(__name__)
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.api import deps
from app.common.dashboard.base import BaseDashboardEndpoint
from app.models import (
    AssemblyStage,
    BomHeader,
    Machine,
    MaterialReadiness,
    Project,
    SchedulingSuggestion,
    ShortageDetail,
    User,
)
from app.schemas.assembly_kit import (  # Stage; Template; Category Mapping; BOM Assembly Attrs; Readiness; Shortage; Alert Rule; Suggestion; Dashboard
    AssemblyDashboardResponse,
    AssemblyDashboardStageStats,
    AssemblyDashboardStats,
    MaterialReadinessResponse,
    SchedulingSuggestionResponse,
)
from app.schemas.common import ResponseModel

router = APIRouter()



from fastapi import APIRouter

router = APIRouter(
    prefix="/assembly-kit/dashboard",
    tags=["dashboard"]
)

# 共 1 个路由

# ==================== 看板 ====================

def _calculate_dashboard_stats(recent_analyses):
    """计算看板基础统计"""
    total = len(recent_analyses)
    can_start = sum(1 for r in recent_analyses if r.can_start)
    not_ready = sum(1 for r in recent_analyses if r.blocking_kit_rate < 50)
    partial = total - can_start - not_ready
    avg_kit = sum(r.overall_kit_rate for r in recent_analyses) / total if total > 0 else Decimal(0)
    avg_blocking = sum(r.blocking_kit_rate for r in recent_analyses) / total if total > 0 else Decimal(0)
    return {
        'total': total, 'can_start': can_start, 'partial': partial,
        'not_ready': not_ready, 'avg_kit': avg_kit, 'avg_blocking': avg_blocking
    }


def _calculate_stage_stats(db, stages, recent_analyses, total_projects):
    """计算分阶段统计"""
    stage_stats = []
    for stage in stages:
        can_start, blocked, total_rate = 0, 0, Decimal(0)
        for r in recent_analyses:
            rate_info = (r.stage_kit_rates or {}).get(stage.stage_code, {})
            if rate_info.get("can_start", False):
                can_start += 1
            else:
                blocked += 1
            total_rate += Decimal(rate_info.get("kit_rate", 0))

        stage_stats.append(AssemblyDashboardStageStats(
            stage_code=stage.stage_code,
            stage_name=stage.stage_name,
            can_start_count=can_start,
            blocked_count=blocked,
            avg_kit_rate=round(total_rate / total_projects, 2) if total_projects > 0 else Decimal(0)
        ))
    return stage_stats


def _build_recent_analyses_list(db, recent_analyses, Project, BomHeader, Machine):
    """构建最近分析列表"""
    recent_list = []
    for r in recent_analyses[:10]:
        project = db.query(Project).filter(Project.id == r.project_id).first()
        bom = db.query(BomHeader).filter(BomHeader.id == r.bom_id).first()
        machine = db.query(Machine).filter(Machine.id == r.machine_id).first() if r.machine_id else None

        recent_list.append(MaterialReadinessResponse(
            id=r.id, readiness_no=r.readiness_no, project_id=r.project_id,
            machine_id=r.machine_id, bom_id=r.bom_id,
            check_date=r.planned_start_date or date.today(),
            overall_kit_rate=r.overall_kit_rate, blocking_kit_rate=r.blocking_kit_rate,
            can_start=r.can_start, first_blocked_stage=r.first_blocked_stage,
            estimated_ready_date=r.estimated_ready_date, stage_kit_rates=[],
            project_no=project.project_code if project else None,
            project_name=project.project_name if project else None,
            machine_no=machine.machine_code if machine else None,
            bom_no=bom.bom_no if bom else None,
            analysis_time=r.analysis_time, analyzed_by=r.analyzed_by, created_at=r.created_at
        ))
    return recent_list


class AssemblyKitDashboardEndpoint(BaseDashboardEndpoint):
    """装配齐套Dashboard端点"""
    
    module_name = "assembly-kit"
    permission_required = None
    
    def __init__(self):
        """初始化路由，支持project_ids参数"""
        # 先创建router，不调用super().__init__()
        self.router = APIRouter(
            prefix="/assembly-kit/dashboard",
            tags=["dashboard"]
        )
        self._register_custom_routes()
    
    def _register_custom_routes(self):
        """注册自定义路由"""
        user_dependency = self._get_user_dependency()
        
        async def dashboard_endpoint(
            db: Session = Depends(deps.get_db),
            project_ids: Optional[str] = Query(None, description="项目ID列表，逗号分隔"),
            current_user: User = Depends(user_dependency),
        ):
            return self._get_dashboard_handler(db, current_user, project_ids)
        
        # 主dashboard端点（保持原有路径）
        self.router.add_api_route(
            "/dashboard",
            dashboard_endpoint,
            methods=["GET"],
            summary="获取装配齐套看板数据",
            response_model=ResponseModel
        )
    
    def get_dashboard_data(
        self,
        db: Session,
        current_user: User,
        project_ids: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取装配齐套看板数据"""
        # 获取最近的齐套分析记录(每个项目取最新一条)
        subquery = db.query(
            MaterialReadiness.project_id,
            func.max(MaterialReadiness.id).label("max_id")
        ).group_by(MaterialReadiness.project_id).subquery()

        query = db.query(MaterialReadiness).join(
            subquery,
            and_(
                MaterialReadiness.project_id == subquery.c.project_id,
                MaterialReadiness.id == subquery.c.max_id
            )
        )

        if project_ids:
            ids = [int(x) for x in project_ids.split(",") if x.strip().isdigit()]
            if ids:
                query = query.filter(MaterialReadiness.project_id.in_(ids))

        recent_analyses = query.all()

        # 空数据返回
        if not recent_analyses:
            dashboard_response = AssemblyDashboardResponse(
                stats=AssemblyDashboardStats(
                    total_projects=0, can_start_count=0, partial_ready_count=0,
                    not_ready_count=0, avg_kit_rate=Decimal(0), avg_blocking_rate=Decimal(0)
                ),
                stage_stats=[], alert_summary={"L1": 0, "L2": 0, "L3": 0, "L4": 0},
                recent_analyses=[], pending_suggestions=[]
            )
            result = dashboard_response.model_dump()
            result["stats"] = []
            return result

        # 使用辅助函数计算统计数据
        stats = _calculate_dashboard_stats(recent_analyses)
        stages = db.query(AssemblyStage).filter(AssemblyStage.is_active).order_by(AssemblyStage.stage_order).all()
        stage_stats = _calculate_stage_stats(db, stages, recent_analyses, stats['total'])

        # 预警汇总
        alert_summary = {
            level: db.query(ShortageDetail).filter(
                ShortageDetail.alert_level == level, ShortageDetail.shortage_qty > 0
            ).count()
            for level in ["L1", "L2", "L3", "L4"]
        }

        # 构建响应数据
        recent_list = _build_recent_analyses_list(db, recent_analyses, Project, BomHeader, Machine)

        # 待处理建议
        pending_suggestions = db.query(SchedulingSuggestion).filter(
            SchedulingSuggestion.status == "pending"
        ).order_by(SchedulingSuggestion.priority_score.desc()).limit(5).all()

        suggestion_list = []
        for s in pending_suggestions:
            project = db.query(Project).filter(Project.id == s.project_id).first()
            machine = db.query(Machine).filter(Machine.id == s.machine_id).first() if s.machine_id else None

            data = SchedulingSuggestionResponse.model_validate(s)
            data.project_no = project.project_no if project else None
            data.project_name = project.name if project else None
            data.machine_no = machine.machine_no if machine else None
            suggestion_list.append(data)

        dashboard_response = AssemblyDashboardResponse(
            stats=AssemblyDashboardStats(
                total_projects=stats['total'],
                can_start_count=stats['can_start'],
                partial_ready_count=stats['partial'],
                not_ready_count=stats['not_ready'],
                avg_kit_rate=round(stats['avg_kit'], 2),
                avg_blocking_rate=round(stats['avg_blocking'], 2)
            ),
            stage_stats=stage_stats,
            alert_summary=alert_summary,
            recent_analyses=recent_list,
            pending_suggestions=suggestion_list
        )
        
        # 转换为字典并添加统计卡片
        result = dashboard_response.model_dump()
        
        # 使用基类方法创建统计卡片
        stat_cards = [
            self.create_stat_card(
                key="total_projects",
                label="项目总数",
                value=stats['total'],
                unit="个",
                icon="project"
            ),
            self.create_stat_card(
                key="can_start_count",
                label="可启动项目",
                value=stats['can_start'],
                unit="个",
                icon="start",
                color="success"
            ),
            self.create_stat_card(
                key="not_ready_count",
                label="未就绪项目",
                value=stats['not_ready'],
                unit="个",
                icon="blocked",
                color="warning"
            ),
            self.create_stat_card(
                key="avg_kit_rate",
                label="平均齐套率",
                value=round(float(stats['avg_kit']), 1),
                unit="%",
                icon="kit_rate"
            ),
            self.create_stat_card(
                key="avg_blocking_rate",
                label="平均阻塞率",
                value=round(float(stats['avg_blocking']), 1),
                unit="%",
                icon="blocking",
                color="danger"
            ),
        ]
        
        result["stat_cards"] = stat_cards
        return result
    
    def _get_dashboard_handler(
        self,
        db: Session,
        current_user: User,
        project_ids: Optional[str] = None
    ) -> ResponseModel:
        """Dashboard处理器，支持project_ids参数"""
        try:
            data = self.get_dashboard_data(db, current_user, project_ids)
            # 移除stat_cards，因为AssemblyDashboardResponse不包含这个字段
            dashboard_data = data.copy()
            dashboard_data.pop("stat_cards", [])
            
            # 构建AssemblyDashboardResponse
            try:
                dashboard_response = AssemblyDashboardResponse(**dashboard_data)
            except Exception:
                # Validation error fallback - return raw data
                return ResponseModel(code=200, message="success", data=dashboard_data)
            
            return ResponseModel(
                code=200,
                message="success",
                data=dashboard_response
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"获取仪表板数据失败: {str(e)}"
            )


# 创建端点实例并获取路由
dashboard_endpoint = AssemblyKitDashboardEndpoint()
router = dashboard_endpoint.router



