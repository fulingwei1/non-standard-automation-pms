# -*- coding: utf-8 -*-
"""AI 后台任务服务：线程池执行 + DB 状态跟踪 + 轮询。

不引入 Celery/Redis，用进程内 ThreadPoolExecutor + SQLite 任务表实现。
提交后立即返回 job_id，客户端轮询 GET /ai-jobs/{id} 获取状态与结果。
"""
import json
import logging
import os
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Any, Callable, Dict, Optional

from sqlalchemy import text

from app.models.ai_job import AIGenerationJob
from app.models.base import SessionLocal

logger = logging.getLogger("ai.jobs")

# 进程内线程池（AI 生成为 IO 密集，等待大模型返回）
_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="ai-job")

# 单个任务允许的最大运行时长（秒）；线程池不跨重启，超过即视为卡死
_DEFAULT_MAX_RUNTIME_SECONDS = 1800


def _max_runtime_seconds() -> int:
    try:
        return int(os.getenv("AI_JOB_MAX_RUNTIME_SECONDS", str(_DEFAULT_MAX_RUNTIME_SECONDS)))
    except ValueError:
        return _DEFAULT_MAX_RUNTIME_SECONDS

# job_type -> handler(session, params, user_id) -> JSON安全的结果dict
_HANDLERS: Dict[str, Callable[[Any, Dict[str, Any], Optional[int]], Dict[str, Any]]] = {}


def register_handler(job_type: str, fn: Callable) -> None:
    _HANDLERS[job_type] = fn


def submit(db, job_type: str, params: Dict[str, Any], user_id: Optional[int]) -> AIGenerationJob:
    """创建任务并提交后台执行，立即返回（PENDING）。"""
    if job_type not in _HANDLERS:
        raise ValueError(f"未知任务类型: {job_type}")
    job = AIGenerationJob(
        job_type=job_type, status="PENDING", params=params, progress=0, created_by=user_id
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    job_id = job.id
    _executor.submit(_run_job, job_id, job_type, params, user_id)
    logger.info("[AI任务] 已提交 job_id=%s type=%s", job_id, job_type)
    return job


def _run_job(job_id: int, job_type: str, params: Dict[str, Any], user_id: Optional[int]) -> None:
    """后台线程执行体：独立 Session，更新状态/结果。"""
    session = SessionLocal()
    try:
        job = session.query(AIGenerationJob).filter(AIGenerationJob.id == job_id).first()
        if not job:
            return
        job.status = "RUNNING"
        job.started_at = datetime.now()
        job.progress = 10
        session.commit()

        handler = _HANDLERS[job_type]
        result = handler(session, params, user_id)

        job = session.query(AIGenerationJob).filter(AIGenerationJob.id == job_id).first()
        job.status = "SUCCESS"
        job.result = result
        job.progress = 100
        job.finished_at = datetime.now()
        session.commit()
        logger.info("[AI任务] 完成 job_id=%s type=%s", job_id, job_type)
    except Exception as e:  # noqa: BLE001
        logger.warning("[AI任务] 失败 job_id=%s error=%s", job_id, str(e)[:200])
        try:
            session.rollback()
            job = session.query(AIGenerationJob).filter(AIGenerationJob.id == job_id).first()
            if job:
                job.status = "FAILED"
                job.error = str(e)[:1000]
                job.finished_at = datetime.now()
                session.commit()
        except Exception:  # noqa: BLE001
            pass
    finally:
        session.close()


def recover_stale_jobs(db=None) -> int:
    """进程启动时调用：线程池不跨重启，上一进程遗留的 PENDING/RUNNING 已无人推进，标记 FAILED。"""
    from app.models import base as _base  # 运行时解析会话工厂，避免导入期绑定

    owns_session = db is None
    session = _base.get_session() if owns_session else db
    try:
        stale = (
            session.query(AIGenerationJob)
            .filter(AIGenerationJob.status.in_(("PENDING", "RUNNING")))
            .all()
        )
        now = datetime.now()
        for job in stale:
            job.status = "FAILED"
            job.error = "进程重启导致任务中断，请重新提交"
            job.finished_at = now
        session.commit()
        if stale:
            logger.warning("[AI任务] 启动恢复：%s 个遗留任务标记 FAILED ids=%s",
                           len(stale), [j.id for j in stale])
        return len(stale)
    finally:
        if owns_session:
            session.close()


def _mark_failed_if_overtime(db, job: Optional[AIGenerationJob]) -> None:
    """惰性超时判定：轮询时发现任务超过最大运行时长仍未完成，标记 FAILED。"""
    if not job or job.status not in ("PENDING", "RUNNING"):
        return
    anchor = job.started_at or job.created_at
    if not anchor:
        return
    limit = _max_runtime_seconds()
    if (datetime.now() - anchor).total_seconds() <= limit:
        return
    job.status = "FAILED"
    job.error = f"任务超过最大运行时长 {limit} 秒未完成，已判定超时终止"
    job.finished_at = datetime.now()
    db.commit()
    logger.warning("[AI任务] 超时终止 job_id=%s type=%s", job.id, job.job_type)


def get(db, job_id: int) -> Optional[AIGenerationJob]:
    job = db.query(AIGenerationJob).filter(AIGenerationJob.id == job_id).first()
    _mark_failed_if_overtime(db, job)
    return job


# ==================== 任务处理器注册 ====================

def _handle_three_tier_quotation(session, params: Dict[str, Any], user_id: Optional[int]) -> Dict[str, Any]:
    """三档报价（3 次串行大模型调用，重）。"""
    from app.schemas.presale_ai_quotation import ThreeTierQuotationRequest
    from app.services.presale.presale_ai_quotation_service import AIQuotationGeneratorService

    request = ThreeTierQuotationRequest(**params)
    service = AIQuotationGeneratorService(session)
    basic, standard, premium = service.generate_three_tier_quotations(request, user_id or 1)

    def _brief(q):
        return {
            "id": q.id,
            "quotation_number": q.quotation_number,
            "quotation_type": getattr(q.quotation_type, "value", q.quotation_type),
            "total": float(q.total or 0),
            "item_count": len(q.items or []),
        }

    return {"basic": _brief(basic), "standard": _brief(standard), "premium": _brief(premium)}


register_handler("three_tier_quotation", _handle_three_tier_quotation)


def _handle_presale_solution_generation(session, params: Dict[str, Any], user_id: Optional[int]) -> Dict[str, Any]:
    """售前 AI 方案生成（单次重 AI 调用；requirement_analysis_id 自动带出分析内容）。"""
    from app.schemas.presale_ai_solution import SolutionGenerationRequest
    from app.services.presale.presale_ai_service import PresaleAIService

    request = SolutionGenerationRequest(**params)
    service = PresaleAIService(session)
    return service.generate_solution(request, user_id or 1)


register_handler("presale_solution_generation", _handle_presale_solution_generation)


def _extract_json(content: str) -> Dict[str, Any]:
    """从大模型输出里提取 JSON 对象。"""
    if not content:
        return {}
    for candidate in (content, ):
        try:
            return json.loads(candidate)
        except Exception:  # noqa: BLE001
            pass
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:  # noqa: BLE001
            pass
    m = re.search(r"\{.*\}", content, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:  # noqa: BLE001
            pass
    return {}


def _match_candidates(session, customer_id, customer_name) -> Dict[str, Any]:
    """按 customer_id 或抽取到的客户名，匹配候选商机/项目。"""
    cid = customer_id
    customer = None
    if cid:
        row = session.execute(
            text("SELECT id, customer_name FROM customers WHERE id=:i"), {"i": cid}
        ).first()
        if row:
            customer = {"id": row[0], "customer_name": row[1]}
    if not cid and customer_name:
        row = session.execute(
            text("SELECT id, customer_name FROM customers WHERE customer_name LIKE :n LIMIT 1"),
            {"n": f"%{customer_name}%"},
        ).first()
        if row:
            cid = row[0]
            customer = {"id": row[0], "customer_name": row[1]}
    opportunities, projects = [], []
    if cid:
        opportunities = [
            {"id": r[0], "opp_name": r[1], "stage": r[2]}
            for r in session.execute(
                text("SELECT id, opp_name, stage FROM opportunities WHERE customer_id=:c ORDER BY id DESC LIMIT 5"),
                {"c": cid},
            ).all()
        ]
        projects = [
            {"id": r[0], "project_code": r[1], "project_name": r[2]}
            for r in session.execute(
                text("SELECT id, project_code, project_name FROM projects WHERE customer_id=:c ORDER BY id DESC LIMIT 5"),
                {"c": cid},
            ).all()
        ]
    return {"customer": customer, "opportunities": opportunities, "projects": projects}


def _handle_parse_meeting_minutes(session, params: Dict[str, Any], user_id: Optional[int]) -> Dict[str, Any]:
    """上传的销售会议纪要 → AI 抽取结构化要点 + 匹配候选商机/项目。"""
    from app.services.ai_client_service import AIClientService

    minutes = (params.get("minutes_text") or "").strip()
    customer_id = params.get("customer_id")
    prompt = f"""你是非标自动化行业的资深销售助理。请从下面的销售会议纪要中抽取结构化信息，严格只输出 JSON：
{{
  "customer_name": "客户名称(如提及,否则空)",
  "participants": ["参会人"],
  "topic": "会议主题",
  "key_demands": ["关键诉求/技术需求"],
  "competitors": ["提及的竞争对手(如有)"],
  "budget": "预算或金额(如提及,否则空)",
  "next_actions": ["下一步行动项"],
  "commitments": ["我方承诺事项"],
  "importance": "high|medium|low",
  "summary": "80字以内会议摘要",
  "next_meeting_checklist": {{
    "to_obtain": ["下次会议前/中需要向客户获取的关键信息(尤其是缺失的技术参数)"],
    "to_confirm": ["需要与客户确认/对齐的事项(避免理解偏差)"],
    "technical_gaps": ["当前技术需求中不清晰、有歧义或有风险、可能导致方案返工的点"]
  }}
}}

特别注意：非标自动化项目常因技术需求不清晰而失败。请基于本次纪要，站在项目落地角度，
尽可能全面地列出 next_meeting_checklist——把客户还没说清、我方必须问清的技术细节
（节拍、精度、兼容机型、接口协议、来料状态、产能、验收标准、现场条件等）都点出来。

会议纪要：
\"\"\"{minutes}\"\"\"

只返回合法 JSON，不要额外解释。"""
    ai = AIClientService()
    resp = ai.generate_solution(
        prompt=prompt, model="qwen3-coder-plus", temperature=0.2, max_tokens=1500
    )
    from app.services.ai_client_service import is_mock_response

    if is_mock_response(resp):
        raise ValueError("AI 服务不可用（返回的是演示数据），纪要解析失败；请检查 AI 密钥配置后重试")
    structured = _extract_json(resp.get("content") or "")
    candidates = _match_candidates(session, customer_id, structured.get("customer_name"))
    return {
        "structured": structured,
        "candidates": candidates,
        "ai_model": resp.get("model"),
        "usage": resp.get("usage"),
    }


register_handler("parse_meeting_minutes", _handle_parse_meeting_minutes)
