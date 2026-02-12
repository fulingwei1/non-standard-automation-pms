# -*- coding: utf-8 -*-
"""
管理节律配置 - 自动生成
从 management_rhythm.py 拆分
"""

# -*- coding: utf-8 -*-
"""
管理节律 API endpoints
包含：节律配置、战略会议、行动项、仪表盘、会议地图
"""
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_keyword_filter, apply_pagination
from app.models.management_rhythm import (
    ManagementRhythmConfig,
)
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.management_rhythm import (
    RhythmConfigCreate,
    RhythmConfigResponse,
    RhythmConfigUpdate,
    StrategicStructureTemplate,
)

router = APIRouter()



from fastapi import APIRouter

router = APIRouter(
    prefix="/management-rhythm/configs",
    tags=["configs"]
)

# 共 5 个路由

# ==================== 管理节律配置 ====================

@router.get("/management-rhythm/configs", response_model=PaginatedResponse)
def read_rhythm_configs(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    rhythm_level: Optional[str] = Query(None, description="节律层级筛选"),
    cycle_type: Optional[str] = Query(None, description="周期类型筛选"),
    is_active: Optional[str] = Query(None, description="是否启用筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索（配置名称）"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取节律配置列表
    """
    query = db.query(ManagementRhythmConfig)

    if rhythm_level:
        query = query.filter(ManagementRhythmConfig.rhythm_level == rhythm_level)

    if cycle_type:
        query = query.filter(ManagementRhythmConfig.cycle_type == cycle_type)

    if is_active:
        query = query.filter(ManagementRhythmConfig.is_active == is_active)

    query = apply_keyword_filter(query, ManagementRhythmConfig, keyword, ["config_name"])

    total = query.count()
    configs = apply_pagination(query.order_by(desc(ManagementRhythmConfig.created_at)), pagination.offset, pagination.limit).all()

    items = []
    for config in configs:
        items.append(RhythmConfigResponse(
            id=config.id,
            rhythm_level=config.rhythm_level,
            cycle_type=config.cycle_type,
            config_name=config.config_name,
            description=config.description,
            meeting_template=config.meeting_template if config.meeting_template else {},
            key_metrics=config.key_metrics if config.key_metrics else [],
            output_artifacts=config.output_artifacts if config.output_artifacts else [],
            is_active=config.is_active,
            created_by=config.created_by,
            created_at=config.created_at,
            updated_at=config.updated_at,
        ))

    return PaginatedResponse(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pagination.pages_for_total(total)
    )


@router.post("/management-rhythm/configs", response_model=RhythmConfigResponse, status_code=status.HTTP_201_CREATED)
def create_rhythm_config(
    config_data: RhythmConfigCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建节律配置
    """
    config = ManagementRhythmConfig(
        rhythm_level=config_data.rhythm_level,
        cycle_type=config_data.cycle_type,
        config_name=config_data.config_name,
        description=config_data.description,
        meeting_template=config_data.meeting_template,
        key_metrics=config_data.key_metrics,
        output_artifacts=config_data.output_artifacts,
        is_active=config_data.is_active or "ACTIVE",
        created_by=current_user.id,
    )

    db.add(config)
    db.commit()
    db.refresh(config)

    return RhythmConfigResponse(
        id=config.id,
        rhythm_level=config.rhythm_level,
        cycle_type=config.cycle_type,
        config_name=config.config_name,
        description=config.description,
        meeting_template=config.meeting_template if config.meeting_template else {},
        key_metrics=config.key_metrics if config.key_metrics else [],
        output_artifacts=config.output_artifacts if config.output_artifacts else [],
        is_active=config.is_active,
        created_by=config.created_by,
        created_at=config.created_at,
        updated_at=config.updated_at,
    )


@router.get("/management-rhythm/configs/{config_id}", response_model=RhythmConfigResponse)
def read_rhythm_config(
    config_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取节律配置详情
    """
    config = db.query(ManagementRhythmConfig).filter(ManagementRhythmConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="节律配置不存在")

    return RhythmConfigResponse(
        id=config.id,
        rhythm_level=config.rhythm_level,
        cycle_type=config.cycle_type,
        config_name=config.config_name,
        description=config.description,
        meeting_template=config.meeting_template if config.meeting_template else {},
        key_metrics=config.key_metrics if config.key_metrics else [],
        output_artifacts=config.output_artifacts if config.output_artifacts else [],
        is_active=config.is_active,
        created_by=config.created_by,
        created_at=config.created_at,
        updated_at=config.updated_at,
    )


@router.put("/management-rhythm/configs/{config_id}", response_model=RhythmConfigResponse)
def update_rhythm_config(
    config_id: int,
    config_data: RhythmConfigUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新节律配置
    """
    config = db.query(ManagementRhythmConfig).filter(ManagementRhythmConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="节律配置不存在")

    update_data = config_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(config, field, value)

    db.commit()
    db.refresh(config)

    return RhythmConfigResponse(
        id=config.id,
        rhythm_level=config.rhythm_level,
        cycle_type=config.cycle_type,
        config_name=config.config_name,
        description=config.description,
        meeting_template=config.meeting_template if config.meeting_template else {},
        key_metrics=config.key_metrics if config.key_metrics else [],
        output_artifacts=config.output_artifacts if config.output_artifacts else [],
        is_active=config.is_active,
        created_by=config.created_by,
        created_at=config.created_at,
        updated_at=config.updated_at,
    )


@router.get("/management-rhythm/strategic-structure-template", response_model=StrategicStructureTemplate)
def get_strategic_structure_template(
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取五层战略结构模板
    """
    return StrategicStructureTemplate(
        vision={
            "mission": "我们希望通过____，让____变得更好",
            "vision": "最终成为一家怎样的公司",
            "why_exist": "存在的意义",
            "three_years_later": "三年后希望被怎么记住",
            "long_term_value": "为谁创造长期价值",
            "standard_expression": "我们希望通过（核心使命或创新方式），让（核心客户群体或社会群体）在（关键领域）获得（理想的未来状态），并最终成为一家怎样的公司（愿景）"
        },
        opportunity={
            "market_trend": "未来三年的行业关键趋势",
            "customer_demand": "客户需求本质",
            "competitive_gap": "竞争空位",
            "our_advantage": "我们的优势",
            "four_in_one": {
                "industry_growth": "行业是否有增长",
                "competitive_gap": "竞争是否有空隙",
                "customer_demand": "客户是否有需求",
                "our_advantage": "我们是否有优势"
            },
            "why_we_win": "凭什么能赢的逻辑",
            "standard_expression": "我们认为未来（时间周期）内，（关键趋势或结构性变化）将成为行业增长的决定力量，我们将通过（关键能力或资源杠杆），抓住（结构性机会），满足（什么本质需求），瞄准（什么竞争空位），从而建立（长期竞争势能）"
        },
        positioning={
            "market_segment": "聚焦的赛道/细分市场",
            "differentiation": "差异化方式",
            "target_customers": "核心客户群体",
            "value_proposition": "独特价值主张",
            "competitive_barrier": "竞争壁垒",
            "standard_expression": "我们选择聚焦（核心赛道/细分市场），以（核心打法/差异化路径）形成竞争壁垒，为（核心客户群体）提供（独特价值主张）"
        },
        goals={
            "strategic_hypothesis": "战略假设",
            "key_metrics": [],
            "annual_goals": "年度目标",
            "quarterly_goals": "季度目标",
            "monthly_goals": "月度目标",
            "standard_expression": "围绕上述战略机会，我们设定以下关键验证目标：通过（关键指标/OKR/KPI）衡量（假设是否成立），确保（战略成果）在（时间周期）内得到验证"
        },
        path={
            "value_chain": "价值流路径(客户需求→产品方案→交付体验→复购机制)",
            "customer_need_essence": "客户需求本质是什么",
            "product_solution": "我们在客户需求本质上应该提供什么产品",
            "service_experience": "我们在客户需求本质上应该创造什么体验",
            "repurchase_mechanism": "我们在客户需求本质上如何让客户持续复购",
            "execution_order": "执行次序",
            "rhythm": "节奏(周执行/月验证/季校准/年复盘)",
            "resources": "兵力投入",
            "campaigns": "战役系统",
            "standard_expression": "我们将通过（核心路径结构），实现战略目标，并以（经营节奏、次序、兵力、战役机制）保障战略持续运行与动态优化"
        }
    )



