# -*- coding: utf-8 -*-
"""AI 日报/周报自动推送定时任务。

数据源：销售活动(customer_communications) + 任务进展(tasks) —— 覆盖销售/PM/工程师。
推送通道：系统站内 + 邮件 + 企微（用户已启用则发，未配置自动跳过）。
幂等：同一用户同一天只推一次。可在管理端开关/调时间(SchedulerTaskConfig)。
"""
import logging
from datetime import datetime

from sqlalchemy import text

from app.models.base import SessionLocal

logger = logging.getLogger(__name__)


def _job_enabled(task_id: str) -> bool:
    """读 SchedulerTaskConfig 的开关（无配置=默认启用）。"""
    try:
        from app.models.scheduler_config import SchedulerTaskConfig
        db = SessionLocal()
        try:
            cfg = db.query(SchedulerTaskConfig).filter(SchedulerTaskConfig.task_id == task_id).first()
            return True if cfg is None else bool(cfg.is_enabled)
        finally:
            db.close()
    except Exception:  # noqa: BLE001
        return True


def _generate_report(sales_acts, tasks, label):
    """AI 汇总（销售活动 + 任务进展）成日报正文，失败兜底拼接。"""
    parts = []
    if sales_acts:
        parts.append("【客户/销售活动】\n" + "\n".join(f"- {a[0]}: {a[1]}" for a in sales_acts if a[1]))
    if tasks:
        parts.append("【任务/项目进展】\n" + "\n".join(f"- {t[0]}（{t[2]}，进度{t[3] or 0}%）" for t in tasks))
    raw = "\n".join(parts)
    try:
        from app.services.ai_client_service import AIClientService
        resp = AIClientService().generate_solution(
            prompt=(f"你是员工本人。把下面今天的销售活动与任务进展整理成简洁的{label}"
                    "(分'已完成/进展''下一步计划''需协调/风险'三段，条理清晰)，直接输出正文：\n" + raw),
            model="qwen3-coder-plus", temperature=0.3, max_tokens=1100)
        txt = (resp.get("content") or "").strip()
        if txt and "mock" not in str(resp.get("model", "")).lower():
            return txt
    except Exception as exc:  # noqa: BLE001
        logger.warning("日报AI生成失败，兜底拼接: %s", str(exc)[:120])
    return raw or f"今日暂无可汇总内容"


def _push_multichannel(db, uid, ntype, title, content, extra):
    """系统站内(必达) + 邮件/企微(用户启用则发)。"""
    # 1) 系统站内（成熟稳定）
    try:
        from app.services.sales_reminder.base import create_notification
        create_notification(db=db, user_id=uid, notification_type=ntype, title=title,
                            content=content[:1000], source_type="ai_report",
                            link_url="/ai/assistant", priority="NORMAL", extra_data=extra)
    except Exception as exc:  # noqa: BLE001
        logger.error("系统通知创建失败 uid=%s: %s", uid, str(exc)[:120])
        return False
    # 2) 邮件 + 企微（best-effort，未配置/未启用自动跳过）
    try:
        from app.services.notification.unified_notification_service import UnifiedNotificationService
        from app.services.notification.channels.base import NotificationRequest, NotificationChannel
        svc = UnifiedNotificationService(db)
        svc.send_notification(NotificationRequest(
            recipient_id=uid, notification_type=ntype, category="ai_report",
            title=title, content=content[:1500],
            channels=[NotificationChannel.EMAIL, NotificationChannel.WECHAT],
            source_type="ai_report", link_url="/ai/assistant", extra_data=extra))
    except Exception as exc:  # noqa: BLE001
        logger.info("邮件/企微推送跳过 uid=%s: %s", uid, str(exc)[:100])
    return True


def push_daily_reports(period: str = "day", max_users: int = 50):
    """扫描当日有销售活动或任务进展的用户，生成并推送日报（多通道、幂等）。"""
    task_id = "push_ai_weekly_reports" if period == "week" else "push_ai_daily_reports"
    if not _job_enabled(task_id):
        logger.info("日报推送任务已在管理端关闭，跳过")
        return {"period": period, "pushed": 0, "disabled": True}

    days = 1 if period == "day" else 7
    label = "日报" if days == 1 else "周报"
    ntype = "DAILY_REPORT" if days == 1 else "WEEKLY_REPORT"
    win = f"-{days} day"
    db = SessionLocal()
    pushed = 0
    try:
        # 候选用户 = 有销售活动的 ∪ 有任务更新的
        uset = set()
        for (u,) in db.execute(text("SELECT DISTINCT created_by FROM customer_communications "
                                    "WHERE created_by IS NOT NULL AND created_at >= datetime('now', :d)"), {"d": win}).all():
            uset.add(u)
        for (u,) in db.execute(text("SELECT DISTINCT owner_id FROM tasks "
                                    "WHERE owner_id IS NOT NULL AND updated_at >= datetime('now', :d)"), {"d": win}).all():
            uset.add(u)
        today = datetime.now().strftime("%Y-%m-%d")
        for uid in list(uset)[:max_users]:
            exists = db.execute(text("SELECT 1 FROM notifications WHERE user_id=:u AND notification_type=:t "
                                     "AND created_at >= :d LIMIT 1"), {"u": uid, "t": ntype, "d": today}).first()
            if exists:
                continue
            acts = db.execute(text("SELECT topic, content FROM customer_communications "
                                   "WHERE created_by=:u AND created_at >= datetime('now', :d) ORDER BY created_at DESC LIMIT 30"),
                              {"u": uid, "d": win}).all()
            tks = db.execute(text("SELECT task_name, stage, status, progress_percent FROM tasks "
                                  "WHERE owner_id=:u AND updated_at >= datetime('now', :d) ORDER BY updated_at DESC LIMIT 30"),
                             {"u": uid, "d": win}).all()
            if not acts and not tks:
                continue
            report = _generate_report(acts, tks, label)
            if _push_multichannel(db, uid, ntype,
                                  f"📋 你的AI{label}已生成（{today}）", report,
                                  {"period": period, "activity_count": len(acts), "task_count": len(tks)}):
                pushed += 1
        db.commit()
        logger.info("AI%s推送完成：%s 位用户", label, pushed)
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        logger.error("AI%s推送失败: %s", label, str(exc)[:200])
    finally:
        db.close()
    return {"period": period, "pushed": pushed}


def push_weekly_reports():
    """周报推送（供周五定时调用）。"""
    return push_daily_reports(period="week")
