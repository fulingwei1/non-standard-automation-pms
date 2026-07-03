# -*- coding: utf-8 -*-
"""商机阶段流转守卫。"""

from typing import Any

from fastapi import HTTPException

from app.models.enums import OpportunityStageEnum


TERMINAL_OPPORTUNITY_STAGES = {
    OpportunityStageEnum.WON.value,
    OpportunityStageEnum.LOST.value,
}

VALID_OPPORTUNITY_STAGES = {stage.value for stage in OpportunityStageEnum}


def normalize_opportunity_stage(stage: Any) -> str:
    """把 Enum/字符串阶段归一成大写字符串。"""
    if isinstance(stage, OpportunityStageEnum):
        return stage.value
    return str(stage or "").strip().upper()


def validate_opportunity_stage_value(stage: Any) -> str:
    target = normalize_opportunity_stage(stage)
    if target not in VALID_OPPORTUNITY_STAGES:
        raise HTTPException(
            status_code=400,
            detail=f"无效的商机阶段，必须是: {', '.join(sorted(VALID_OPPORTUNITY_STAGES))}",
        )
    return target


def validate_opportunity_stage_transition(
    current_stage: Any,
    target_stage: Any,
    *,
    allow_direct_win: bool = False,
) -> str:
    """校验商机阶段是否允许从 current_stage 流转到 target_stage。"""
    current = normalize_opportunity_stage(current_stage)
    target = validate_opportunity_stage_value(target_stage)

    if current == target:
        return target

    if current in TERMINAL_OPPORTUNITY_STAGES:
        raise HTTPException(
            status_code=400,
            detail=f"非法商机阶段流转：{current} → {target}，终态商机不能通过通用更新改写",
        )

    if (
        target == OpportunityStageEnum.WON.value
        and not allow_direct_win
        and current != OpportunityStageEnum.CLOSING.value
    ):
        raise HTTPException(
            status_code=400,
            detail="非法商机阶段流转：非 CLOSING 商机不能通过通用阶段更新直接标记赢单",
        )

    return target
