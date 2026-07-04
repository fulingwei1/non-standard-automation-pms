#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
售前弹药库 M1.1：项目分类回填脚本

问题：projects 表里 industry/product_category 填充率仅 19%，project_category/outcome 全空。
这会让"按行业/设备类型/中标状态检索弹药"完全失效。

做法：扫所有 industry 或 product_category 为空的项目，拼出
  project_name + customer_name + customer.industry + description + contract_amount + stage
作为上下文，调 AIClientService 让 AI 推断：
  industry / product_category / project_category / outcome

安全策略：
  - 默认 --dry-run，只输出待确认清单，不写库
  - --apply 才真正 UPDATE
  - 已有值的字段不覆盖（--force 可强制覆盖）
  - AI 返回非法枚举值时跳过该字段

运行：
    python scripts/backfill_project_taxonomy.py                 # 只看清单
    python scripts/backfill_project_taxonomy.py --apply         # 写库
    python scripts/backfill_project_taxonomy.py --apply --limit 5  # 先试 5 条
"""

from __future__ import annotations

import argparse
import json
import logging
import sqlite3
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

DEFAULT_DB_PATH = ROOT_DIR / "data" / "app.db"

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("backfill_taxonomy")

# ============= 受控枚举（用于校验 AI 输出） =============
# 取值参考 seed_complete_demo_data.py 与现有 DB 真实取值，AI 必须落在白名单内。
VALID_INDUSTRY = {
    "新能源汽车", "动力电池", "消费电子", "通信设备", "电子制造",
    "智能家电", "智能硬件", "锂电设备", "汽车电子", "汽车制造",
    "医疗电子", "工业控制", "新能源", "轨道交通", "航空航天",
}

VALID_PRODUCT_CATEGORY = {
    "ICT测试", "FCT测试", "EOL测试", "烧录设备", "老化设备", "视觉检测",
    "ICT测试设备", "FCT测试设备", "EOL测试设备", "AOI检测设备",
}

VALID_PROJECT_CATEGORY = {
    "销售", "研发", "改造", "维保",
}

# outcome: WON=中标交付 / LOST=丢标 / PENDING=未结（stage<S9 视为未结）
VALID_OUTCOME = {"WON", "LOST", "PENDING"}


def load_ai_client():
    """加载 AI 客户端，失败则用规则兜底。"""
    try:
        from app.services.ai_client_service import AIClientService
        return AIClientService(), True
    except Exception as e:
        logger.warning(f"AI 客户端不可用，将仅用规则兜底: {e}")
        return None, False


def infer_with_ai(ai_client, project: dict) -> dict:
    """用 AI 推断四个分类字段，返回 {industry, product_category, project_category, outcome}。"""
    ctx = (
        f"项目名称: {project['project_name']}\n"
        f"客户名称: {project.get('customer_name') or '未知'}\n"
        f"客户行业(来自客户表): {project.get('customer_industry') or '未知'}\n"
        f"项目描述: {project.get('description') or '无'}\n"
        f"合同金额: {project.get('contract_amount') or '未填'}\n"
        f"当前阶段: {project.get('stage') or '未知'}\n"
    )
    prompt = (
        "你是非标自动化测试设备行业（ICT/FCT/EOL/烧录/老化/视觉检测）的售前专家。"
        "根据下面项目信息，推断它的分类。严格只输出 JSON，不要任何解释。\n\n"
        f"{ctx}\n\n"
        "输出格式（字段值必须在括号白名单内，无法判断就用 null）：\n"
        '{"industry": "新能源汽车|动力电池|消费电子|通信设备|电子制造|智能家电|'
        '智能硬件|锂电设备|汽车电子|汽车制造|医疗电子|工业控制|新能源|轨道交通|航空航天",\n'
        ' "product_category": "ICT测试|FCT测试|EOL测试|烧录设备|老化设备|视觉检测",\n'
        ' "project_category": "销售|研发|改造|维保",\n'
        ' "outcome": "WON|LOST|PENDING"}\n\n'
        "outcome 判断：阶段 S9 或有实际结项迹象=WON，明显失败的=LOST，其余=PENDING。"
    )
    try:
        result = ai_client.generate_solution(
            prompt, model="qwen3-coder-plus", temperature=0.1, max_tokens=300
        )
        raw = result.get("content") or result.get("text") or ""
        # 容错：AI 可能包 ```json
        raw = raw.strip().strip("`")
        if raw.startswith("json"):
            raw = raw[4:].strip()
        data = json.loads(raw)
        return {
            "industry": data.get("industry"),
            "product_category": data.get("product_category"),
            "project_category": data.get("project_category"),
            "outcome": data.get("outcome"),
        }
    except Exception as e:
        logger.debug(f"AI 推断失败(project_id={project['id']}): {e}")
        return {}


def infer_by_rule(project: dict) -> dict:
    """规则兜底：从客户行业/项目名/阶段做基础推断。"""
    result = {}
    name = (project.get("project_name") or "")
    cust_ind = project.get("customer_industry")
    stage = project.get("stage") or ""

    # industry：优先继承客户行业
    if cust_ind:
        result["industry"] = cust_ind

    # product_category：关键词匹配
    name_lower = name.lower()
    for kw, cat in [
        ("ICT", "ICT测试"), ("FCT", "FCT测试"), ("EOL", "EOL测试"),
        ("烧录", "烧录设备"), ("老化", "老化设备"),
        ("AOI", "视觉检测"), ("视觉", "视觉检测"), ("检测", "视觉检测"),
    ]:
        if kw.lower() in name_lower:
            result["product_category"] = cat
            break

    # outcome：靠阶段
    if stage in ("S9",):
        result["outcome"] = "WON"
    elif stage:
        result["outcome"] = "PENDING"

    return result


def validate(field: str, value):
    """校验 AI/规则 输出是否在白名单内，非法则丢弃。"""
    if value is None:
        return None
    valid_map = {
        "industry": VALID_INDUSTRY,
        "product_category": VALID_PRODUCT_CATEGORY,
        "project_category": VALID_PROJECT_CATEGORY,
        "outcome": VALID_OUTCOME,
    }
    if field not in valid_map:
        return None
    return value if value in valid_map[field] else None


def main():
    parser = argparse.ArgumentParser(description="回填项目分类字段")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH, help="SQLite 路径")
    parser.add_argument("--apply", action="store_true", help="真正写库（默认只看清单）")
    parser.add_argument("--force", action="store_true", help="覆盖已有值（默认只填空字段）")
    parser.add_argument("--limit", type=int, default=0, help="只处理前 N 条（0=不限）")
    parser.add_argument("--json", type=Path, help="把清单导出到 JSON 文件供 review")
    args = parser.parse_args()

    if not args.db.exists():
        logger.error(f"数据库不存在: {args.db}")
        sys.exit(1)

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row

    # 选出需要处理的项目：industry 或 product_category 为空
    where = "" if args.force else "WHERE (p.industry IS NULL OR p.industry='' OR p.product_category IS NULL OR p.product_category='')"
    sql = (
        "SELECT p.id, p.project_name, p.customer_name, p.industry, p.product_category, "
        "p.project_category, p.outcome, p.stage, p.contract_amount, p.description, c.industry AS customer_industry "
        "FROM projects p LEFT JOIN customers c ON p.customer_id = c.id "
        f"{where} ORDER BY p.id"
    )
    rows = conn.execute(sql).fetchall()
    if args.limit > 0:
        rows = rows[: args.limit]

    logger.info(f"待处理项目: {len(rows)} 条 (force={args.force}, apply={args.apply})")

    ai_client, ai_ok = load_ai_client()

    review_list = []
    stats = {"ai_success": 0, "rule_fallback": 0, "skipped": 0}

    for r in rows:
        project = dict(r)
        # 先 AI，失败用规则
        inferred = {}
        if ai_ok:
            inferred = infer_with_ai(ai_client, project)
            if inferred:
                stats["ai_success"] += 1
            else:
                inferred = infer_by_rule(project)
                stats["rule_fallback"] += 1
        else:
            inferred = infer_by_rule(project)
            if inferred:
                stats["rule_fallback"] += 1

        # 校验白名单
        clean = {}
        for f in ("industry", "product_category", "project_category", "outcome"):
            v = validate(f, inferred.get(f))
            if v is not None:
                # 非强制模式下不覆盖已有值
                if not args.force and project.get(f):
                    continue
                clean[f] = v

        if not clean:
            stats["skipped"] += 1
            continue

        review_list.append({
            "id": project["id"],
            "project_name": project["project_name"],
            "before": {
                "industry": project.get("industry"),
                "product_category": project.get("product_category"),
                "project_category": project.get("project_category"),
                "outcome": project.get("outcome"),
            },
            "after": clean,
        })

        if args.apply and clean:
            set_clause = ", ".join(f"{k} = ?" for k in clean)
            params = list(clean.values()) + [project["id"]]
            conn.execute(
                f"UPDATE projects SET {set_clause} WHERE id = ?", params
            )
            logger.info(
                f"[UPDATE] 项目#{project['id']} {project['project_name'][:30]} -> {clean}"
            )

    if args.apply:
        conn.commit()
        logger.info(f"已写库 {len(review_list)} 条")

    conn.close()

    # 统计
    logger.info(f"统计: {stats}")
    logger.info(
        f"已处理 {len(review_list)} 条 "
        f"(ai_success={stats['ai_success']}, rule_fallback={stats['rule_fallback']}, skipped={stats['skipped']})"
    )

    if args.json:
        args.json.write_text(
            json.dumps(review_list, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        logger.info(f"清单已导出到 {args.json}")
    else:
        # 打印前 20 条预览
        print(json.dumps(review_list[:20], ensure_ascii=False, indent=2))

    if not args.apply:
        logger.info("提示：当前是 dry-run。确认清单后加 --apply 写库。")


if __name__ == "__main__":
    main()
