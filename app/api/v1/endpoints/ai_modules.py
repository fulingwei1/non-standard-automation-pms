# -*- coding: utf-8 -*-
"""M1 · 标准模块库：AI 从历史 BOM 挖出可复用模块（支撑配置式设计/模块级报价）。"""
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services import ai_job_service

router = APIRouter(prefix="/ai-modules", tags=["AI标准模块库"])


@router.post("/extract", response_model=ResponseModel, summary="AI从历史BOM挖出标准模块")
def extract_modules(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """扫描历史 BOM 明细 → AI 归纳成非标测试设备的可复用标准模块 → 存入模块库。"""
    import json as _json

    from app.services.ai_client_service import AIClientService

    rows = db.execute(
        text(
            "SELECT material_name, specification, source_type, unit_price, level "
            "FROM bom_items WHERE material_name IS NOT NULL AND material_name != '' LIMIT 300"
        )
    ).all()
    if not rows:
        return ResponseModel(code=200, message="暂无BOM数据可挖掘", data={"modules": 0})

    items = "\n".join(
        f"- {r[0]}｜{r[1] or ''}｜{r[2] or ''}｜¥{r[3] or 0}" for r in rows
    )
    prompt = (
        "你是非标自动化设计专家。下面是历史项目的 BOM 明细（名称｜规格｜来源｜单价）。"
        "请把它们归纳成**可复用的标准模块**（如 视觉检测模组/上下料模组/电控柜/传送模组/测试工位/定位夹具/机架总成 等），"
        "严格只输出 JSON 数组：\n"
        '[{"module_name":"模块名","category":"机械|电气|视觉|测试|结构|软件",'
        '"description":"一句话用途","typical_components":[{"name":"组件","qty":1,"unit_price":0}],'
        '"ref_cost":该模块参考总成本}]\n\n'
        f"BOM 明细：\n{items}\n\n输出 6-12 个模块，只返回合法 JSON 数组。"
    )
    resp = AIClientService().generate_solution(
        prompt=prompt, model="qwen3-coder-plus", temperature=0.3, max_tokens=2500
    )
    content = resp.get("content") or ""
    parsed = ai_job_service._extract_json(content)
    modules = parsed if isinstance(parsed, list) else (parsed.get("modules") if isinstance(parsed, dict) else None)
    if not isinstance(modules, list):
        # 兜底：尝试数组截取
        import re
        m = re.search(r"\[.*\]", content, re.DOTALL)
        modules = _json.loads(m.group(0)) if m else []

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    saved = 0
    for mod in modules:
        if not isinstance(mod, dict) or not mod.get("module_name"):
            continue
        comps = mod.get("typical_components") or []
        try:
            ref_cost = float(mod.get("ref_cost") or 0)
        except (TypeError, ValueError):
            ref_cost = 0
        exists = db.execute(
            text("SELECT id FROM ai_standard_modules WHERE module_name=:n"), {"n": mod["module_name"]}
        ).first()
        payload = {
            "n": mod["module_name"][:100], "c": (mod.get("category") or "")[:50],
            "d": mod.get("description") or "", "tc": _json.dumps(comps, ensure_ascii=False),
            "rc": ref_cost, "u": current_user.id, "now": now,
        }
        if exists:
            db.execute(text(
                "UPDATE ai_standard_modules SET category=:c, description=:d, typical_components=:tc, "
                "ref_cost=:rc, source_count=source_count+1, updated_at=:now WHERE module_name=:n"), payload)
        else:
            db.execute(text(
                "INSERT INTO ai_standard_modules(module_name, category, description, typical_components, "
                "ref_cost, source_count, created_by, created_at, updated_at) "
                "VALUES(:n,:c,:d,:tc,:rc,1,:u,:now,:now)"), payload)
        saved += 1
    db.commit()
    return ResponseModel(code=200, message=f"AI 挖出 {saved} 个标准模块", data={"modules": saved})


@router.get("/standardization-advice", response_model=ResponseModel, summary="M7 复用率量化+标准化沉淀建议")
def standardization_advice(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """按模块出现频次量化复用，AI 建议优先标准化/产品化哪些模块，把非标推向可配置化交付。"""
    from app.services.ai_client_service import AIClientService

    rows = db.execute(text(
        "SELECT module_name, category, ref_cost, source_count FROM ai_standard_modules ORDER BY source_count DESC LIMIT 30")).all()
    if not rows:
        return ResponseModel(code=200, message="模块库为空，请先AI挖模块", data={"advice": []})
    total = sum(r[3] or 1 for r in rows)
    stats = [{"module": r[0], "category": r[1], "ref_cost": float(r[2] or 0),
              "occurrences": r[3], "reuse_share": round((r[3] or 1) / total * 100, 1)} for r in rows]
    brief = "；".join(f"{s['module']}(出现{s['occurrences']}次,占{s['reuse_share']}%)" for s in stats[:12])
    prompt = ("你是非标自动化标准化专家。根据各模块的复用频次，建议优先标准化/产品化哪些模块，严格只输出 JSON：\n"
              '{"priority":[{"module":"模块","action":"标准化|参数化|产品化","benefit":"预期收益"}],'
              '"reuse_summary":"整体复用/标准化程度评估","next_step":"下一步标准化建议"}\n\n'
              f"模块复用数据：{brief}\n\n只返回合法 JSON。")
    s = {}
    try:
        s = ai_job_service._extract_json(AIClientService().generate_solution(
            prompt=prompt, model="qwen3-coder-plus", temperature=0.3, max_tokens=1500).get("content") or "") or {}
    except Exception:  # noqa: BLE001
        s = {}
    return ResponseModel(code=200, message="标准化建议生成完成", data={"stats": stats, **s})


@router.get("", response_model=ResponseModel, summary="标准模块库列表")
def list_modules(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    import json as _json

    rows = db.execute(
        text("SELECT id, module_name, category, description, typical_components, ref_cost, source_count "
             "FROM ai_standard_modules ORDER BY source_count DESC, id DESC")
    ).all()
    mods = []
    for r in rows:
        try:
            comps = _json.loads(r[4]) if r[4] else []
        except Exception:  # noqa: BLE001
            comps = []
        mods.append({
            "id": r[0], "module_name": r[1], "category": r[2], "description": r[3],
            "components": comps, "ref_cost": float(r[5] or 0), "source_count": r[6],
        })
    return ResponseModel(code=200, message="ok", data={"total": len(mods), "modules": mods})
