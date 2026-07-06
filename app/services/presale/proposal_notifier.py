# -*- coding: utf-8 -*-
"""
售前方案审核通知（飞书）。

销售提交审核时，发飞书消息给售前工程师，提醒去审核。
用 lark-cli 发送（复用符哥环境的飞书机器人基建）。

配置：
  环境变量 PRESALE_REVIEW_LARK_CHAT_ID：审核通知群/用户的 chat_id（oc_xxx）
  不配则跳过通知（不阻塞提交流程）。
"""
import logging
import os
import subprocess
from typing import Optional

logger = logging.getLogger("presale.notifier")

LARK_CLI_BIN = "/Users/flw/.nvm/versions/node/v24.15.0/bin/lark-cli"


def notify_review_submitted(
    proposal_id: int,
    title: str,
    submitted_by: str,
    version_count: int,
    requirement_text: str,
) -> bool:
    """
    销售提交审核 → 发飞书消息给售前工程师。

    消息发到环境变量 PRESALE_REVIEW_LARK_CHAT_ID 指定的群/用户。
    不配该变量则跳过（不报错）。
    """
    chat_id = os.getenv("PRESALE_REVIEW_LARK_CHAT_ID", "")
    if not chat_id:
        logger.info("未配 PRESALE_REVIEW_LARK_CHAT_ID，跳过飞书通知")
        return False

    msg = (
        f"📋 **新方案待审核**\n\n"
        f"**方案**：{title}\n"
        f"**提交人**：{submitted_by}\n"
        f"**版本**：v{version_count}\n"
        f"**需求**：{requirement_text[:80]}\n\n"
        f"请前往 PMS「方案审核」页面处理 → /presales/proposal-review"
    )

    try:
        result = subprocess.run(
            [LARK_CLI_BIN, "im", "+messages-send",
             "--as", "bot",
             "--chat-id", chat_id,
             "--markdown", msg],
            capture_output=True, text=True, timeout=15, check=False,
        )
        if result.returncode == 0:
            logger.info("飞书审核通知已发送：方案#%s → %s", proposal_id, chat_id)
            return True
        else:
            err = (result.stdout or "") + (result.stderr or "")
            logger.warning("飞书通知发送失败: %s", err[:150])
            return False
    except Exception as e:
        logger.warning("飞书通知异常: %s", e)
        return False
