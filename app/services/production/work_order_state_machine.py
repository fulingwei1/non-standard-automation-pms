# -*- coding: utf-8 -*-
"""
工单状态机

定义工单状态的合法转换规则，并提供校验函数。
"""
from typing import Dict, List

# ---------------------------------------------------------------------------
# 合法状态转换表
#
# 键：当前状态
# 值：允许转入的目标状态列表
# ---------------------------------------------------------------------------
VALID_TRANSITIONS: Dict[str, List[str]] = {
    # 待派工 → 已派工 / 已取消
    "PENDING": ["ASSIGNED", "CANCELLED"],
    # 已派工 → 已开工 / 已取消
    "ASSIGNED": ["STARTED", "CANCELLED"],
    # 已开工 → 已暂停 / 已完工 / 已取消
    "STARTED": ["PAUSED", "COMPLETED", "CANCELLED"],
    # 已暂停 → 已开工（恢复） / 已完工 / 已取消
    "PAUSED": ["STARTED", "COMPLETED", "CANCELLED"],
    # 终态：不允许任何转换
    "COMPLETED": [],
    "APPROVED": [],
    "CANCELLED": [],
}


def validate_transition(current_status: str, new_status: str) -> None:
    """校验状态转换是否合法。

    Parameters
    ----------
    current_status:
        工单当前状态（WorkOrderStatusEnum 的字符串值）。
    new_status:
        期望转入的目标状态。

    Raises
    ------
    ValueError
        当目标状态不在当前状态允许的转换列表中时抛出，并附带清晰的错误说明。
    """
    if current_status == new_status:
        raise ValueError(
            f"工单当前状态已经是 '{current_status}'，无需重复操作。"
        )

    allowed = VALID_TRANSITIONS.get(current_status)

    if allowed is None:
        raise ValueError(
            f"未知的工单状态 '{current_status}'，无法执行状态转换。"
        )

    if new_status not in allowed:
        if allowed:
            allowed_str = "、".join(allowed)
            raise ValueError(
                f"工单当前状态为 '{current_status}'，不允许转换到 '{new_status}'。"
                f"当前状态可转换到：{allowed_str}。"
            )
        else:
            raise ValueError(
                f"工单当前状态为 '{current_status}'（终态），不允许任何状态转换。"
            )


def get_allowed_transitions(current_status: str) -> List[str]:
    """返回当前状态下允许转入的目标状态列表。

    Parameters
    ----------
    current_status:
        工单当前状态（WorkOrderStatusEnum 的字符串值）。

    Returns
    -------
    List[str]
        允许的目标状态列表；若当前状态未知则返回空列表。
    """
    return list(VALID_TRANSITIONS.get(current_status, []))
