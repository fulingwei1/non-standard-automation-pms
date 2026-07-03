# -*- coding: utf-8 -*-
"""管理员后台：可视化配置 AI 接入（Key/Base URL/模型/超时）+ 一键测试连接。"""
import time
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter(prefix="/admin/ai-config", tags=["管理员-AI配置"])

# 可后台配置的键（含中文标签/是否敏感）
FIELDS = [
    # 厂商切换：模型名前缀决定路由 qwen*→阿里百炼 / glm*→智谱 / gpt*→OpenAI / kimi*→月之暗面
    {"key": "AI_DEFAULT_MODEL", "label": "默认模型(切换厂商)", "secret": False, "group": "通用",
     "placeholder": "qwen3.7-plus / glm-5 / gpt-4o / kimi"},
    {"key": "ALIBABA_API_KEY", "label": "API Key", "secret": True, "group": "阿里百炼", "placeholder": "sk-..."},
    {"key": "ALIBABA_BASE_URL", "label": "Base URL", "secret": False, "group": "阿里百炼", "placeholder": "https://coding.dashscope.aliyuncs.com/v1"},
    {"key": "ALIBABA_MODEL", "label": "主模型(含视觉)", "secret": False, "group": "阿里百炼", "placeholder": "qwen3.7-plus"},
    {"key": "ALIBABA_FAST_MODEL", "label": "快模型(结构化任务)", "secret": False, "group": "阿里百炼", "placeholder": "qwen3-coder-plus"},
    {"key": "ALIBABA_TIMEOUT", "label": "超时(秒)", "secret": False, "group": "阿里百炼", "placeholder": "300"},
    {"key": "ZHIPU_API_KEY", "label": "智谱 API Key", "secret": True, "group": "其他厂商", "placeholder": "glm-5 用"},
    {"key": "OPENAI_API_KEY", "label": "OpenAI API Key", "secret": True, "group": "其他厂商", "placeholder": "gpt-* 用"},
    {"key": "KIMI_API_KEY", "label": "Kimi API Key", "secret": True, "group": "其他厂商", "placeholder": "kimi 用"},
]


def _require_admin(user: User):
    if getattr(user, "is_superuser", False):
        return
    role = (getattr(user, "role", "") or "").lower()
    if "admin" in role or "超级" in (getattr(user, "role", "") or ""):
        return
    raise HTTPException(status_code=403, detail="仅管理员可配置 AI 接入")


def _mask(v: str) -> str:
    if not v:
        return ""
    return v[:4] + "****" + v[-4:] if len(v) > 10 else "****"


@router.get("", response_model=ResponseModel, summary="读取AI接入配置")
def get_config(db: Session = Depends(deps.get_db), current_user: User = Depends(security.get_current_active_user)) -> Any:
    _require_admin(current_user)
    import os

    from app.services.ai_client_service import load_ai_settings

    cfg = load_ai_settings(force=True)
    fields = []
    for f in FIELDS:
        db_val = cfg.get(f["key"], "")
        env_val = os.getenv(f["key"], "")
        raw = db_val or env_val
        fields.append({
            **f,
            "source": "后台配置" if db_val else ("环境变量" if env_val else "未配置"),
            "value": _mask(raw) if f["secret"] else raw,
            "configured": bool(raw),
        })
    return ResponseModel(code=200, message="ok", data={"fields": fields})


class ConfigUpdate(BaseModel):
    values: Dict[str, str]  # {key: value}；secret 传空串表示不修改


@router.put("", response_model=ResponseModel, summary="保存AI接入配置")
def update_config(body: ConfigUpdate, db: Session = Depends(deps.get_db),
                  current_user: User = Depends(security.get_current_active_user)) -> Any:
    _require_admin(current_user)
    from app.services.ai_client_service import load_ai_settings

    allowed = {f["key"] for f in FIELDS}
    secret_keys = {f["key"] for f in FIELDS if f["secret"]}
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    saved = []
    for k, v in body.values.items():
        if k not in allowed:
            continue
        # 敏感字段传空串 => 不覆盖已有值
        if k in secret_keys and (v is None or v == ""):
            continue
        db.execute(text(
            "INSERT INTO ai_settings(key, value, updated_at, updated_by) VALUES(:k,:v,:t,:u) "
            "ON CONFLICT(key) DO UPDATE SET value=:v, updated_at=:t, updated_by=:u"),
            {"k": k, "v": v, "t": now, "u": current_user.id})
        saved.append(k)
    db.commit()
    load_ai_settings(force=True)  # 立即刷新缓存，新会话即用新配置
    return ResponseModel(code=200, message=f"已保存 {len(saved)} 项配置（即时生效）", data={"saved": saved})


class TestReq(BaseModel):
    prompt: Optional[str] = "用一句话确认你已连通。"
    model: Optional[str] = None  # 不传则用当前默认模型；传 glm-5/gpt-4o/kimi 可单测对应厂商


@router.post("/test", response_model=ResponseModel, summary="测试AI连接")
def test_connection(body: TestReq, db: Session = Depends(deps.get_db),
                    current_user: User = Depends(security.get_current_active_user)) -> Any:
    _require_admin(current_user)
    from app.services.ai_client_service import AIClientService, load_ai_settings

    load_ai_settings(force=True)
    svc = AIClientService()
    if not (svc.qwen_api_key or svc.zhipu_api_key or svc.openai_api_key or svc.kimi_api_key):
        raise HTTPException(status_code=400, detail="未配置任何厂商 API Key，无法测试")
    # 默认模型是 qwen 系时用快模型省时；显式指定 model 时按指定的测
    test_model = body.model or (
        svc.qwen_fast_model if svc.default_model.startswith("qwen") else svc.default_model
    )
    t0 = time.time()
    try:
        resp = svc.generate_solution(prompt=body.prompt, model=test_model, temperature=0.2, max_tokens=100)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"连接失败：{str(e)[:150]}")
    content = (resp.get("content") or "").strip()
    ok = bool(content) and "mock" not in str(resp.get("model", "")).lower()
    return ResponseModel(code=200 if ok else 502,
                         message="连接正常" if ok else "返回异常（可能是Key无效走了降级/mock）",
                         data={"ok": ok, "model": resp.get("model"), "latency_s": round(time.time() - t0, 2),
                               "sample": content[:120], "usage": resp.get("usage")})


REPORT_JOBS = {
    "daily": {"task_id": "push_ai_daily_reports", "name": "AI日报自动推送", "default": {"hour": 18, "minute": 30}},
    "weekly": {"task_id": "push_ai_weekly_reports", "name": "AI周报自动推送", "default": {"day_of_week": "fri", "hour": 17, "minute": 30}},
}


@router.get("/report-schedule", response_model=ResponseModel, summary="读取日报/周报推送排程")
def get_report_schedule(db: Session = Depends(deps.get_db), current_user: User = Depends(security.get_current_active_user)) -> Any:
    _require_admin(current_user)
    from app.models.scheduler_config import SchedulerTaskConfig

    out = {}
    for k, meta in REPORT_JOBS.items():
        cfg = db.query(SchedulerTaskConfig).filter(SchedulerTaskConfig.task_id == meta["task_id"]).first()
        cron = (cfg.cron_config if cfg and cfg.cron_config else meta["default"])
        out[k] = {"enabled": (cfg.is_enabled if cfg else True), "cron": cron, "name": meta["name"]}
    return ResponseModel(code=200, message="ok", data=out)


class ReportScheduleUpdate(BaseModel):
    kind: str  # daily|weekly
    enabled: bool = True
    hour: int = 18
    minute: int = 30
    day_of_week: Optional[str] = None  # weekly 用，如 'fri'


@router.put("/report-schedule", response_model=ResponseModel, summary="设置日报/周报推送时间与开关")
def update_report_schedule(body: ReportScheduleUpdate, db: Session = Depends(deps.get_db),
                           current_user: User = Depends(security.get_current_active_user)) -> Any:
    _require_admin(current_user)
    from app.models.scheduler_config import SchedulerTaskConfig

    meta = REPORT_JOBS.get(body.kind)
    if not meta:
        raise HTTPException(status_code=400, detail="kind 需为 daily 或 weekly")
    if not (0 <= body.hour <= 23 and 0 <= body.minute <= 59):
        raise HTTPException(status_code=400, detail="时间不合法")
    cron = {"hour": body.hour, "minute": body.minute}
    if body.kind == "weekly":
        cron["day_of_week"] = body.day_of_week or "fri"

    cfg = db.query(SchedulerTaskConfig).filter(SchedulerTaskConfig.task_id == meta["task_id"]).first()
    if not cfg:
        cfg = SchedulerTaskConfig(task_id=meta["task_id"], task_name=meta["name"],
                                  module="app.utils.scheduled_tasks",
                                  callable_name="push_daily_reports" if body.kind == "daily" else "push_weekly_reports",
                                  category="AI")
        db.add(cfg)
    cfg.is_enabled = body.enabled
    cfg.cron_config = cron
    cfg.updated_by = current_user.id
    db.commit()

    # 热重排运行中的 apscheduler job（失败不影响保存，重启后按DB配置生效）
    live = None
    try:
        from app.utils.scheduler import scheduler
        if scheduler.running:
            if body.enabled:
                scheduler.reschedule_job(meta["task_id"], trigger="cron", **cron)
                live = "已重排并生效"
            else:
                scheduler.pause_job(meta["task_id"])
                live = "已暂停"
    except Exception as e:  # noqa: BLE001
        live = f"配置已存(重启后生效): {str(e)[:60]}"
    return ResponseModel(code=200, message="排程已更新", data={"cron": cron, "enabled": body.enabled, "live": live})


@router.post("/push-reports", response_model=ResponseModel, summary="立即触发AI日报/周报推送")
def push_reports_now(period: str = "day", current_user: User = Depends(security.get_current_active_user)) -> Any:
    """管理员手动立即推送（定时任务默认每天18:30/周五17:30自动执行）。"""
    _require_admin(current_user)
    from app.utils.scheduled_tasks.ai_report_tasks import push_daily_reports

    result = push_daily_reports(period="week" if period == "week" else "day")
    return ResponseModel(code=200, message=f"已推送 {result.get('pushed', 0)} 位用户", data=result)
