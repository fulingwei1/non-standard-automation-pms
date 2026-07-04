#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
售前弹药库 M2：给案例库批量生成 embedding 向量

前置条件：百炼 key 已开通 text-embedding-v3 权限。
  - 没开通时会自动跳过 API 调用，提示去开通
  - 开通后跑此脚本，给所有 embedding 为空的案例生成向量并入库

幂等：已有 embedding 的案例跳过（--force 强制重算）。

运行：
    python scripts/generate_case_embeddings.py             # 给空案例生成
    python scripts/generate_case_embeddings.py --force     # 全部重算
    python scripts/generate_case_embeddings.py --dry-run   # 只看会处理哪些
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

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("gen_embeddings")


def build_case_text(case: sqlite3.Row) -> str:
    """把案例的关键字段拼成一句待向量化的文本。"""
    parts = [
        case["case_name"] or "",
        case["industry"] or "",
        case["equipment_type"] or "",
        case["technical_highlights"] or "",
        case["lessons_learned"] or "",
        case["project_summary"] or "",
    ]
    tags = case["tags"]
    if tags:
        try:
            tag_list = json.loads(tags) if isinstance(tags, str) else tags
            if isinstance(tag_list, list):
                parts.append(" ".join(str(t) for t in tag_list))
        except Exception:
            pass
    return " ".join(p for p in parts if p).strip()


def serialize_embedding(emb: list) -> bytes:
    """把 float list 序列化成 BLOB 存储（JSON 编码，兼容现有读取逻辑）。"""
    return json.dumps(emb).encode("utf-8")


def main():
    parser = argparse.ArgumentParser(description="给案例库批量生成 embedding")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--force", action="store_true", help="重算已有 embedding 的案例")
    parser.add_argument("--dry-run", action="store_true", help="只看不写")
    parser.add_argument("--batch-size", type=int, default=20, help="单次 API 调用的案例数（百炼上限25）")
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row

    where = "" if args.force else "WHERE embedding IS NULL"
    rows = conn.execute(
        f"SELECT id, case_name, industry, equipment_type, technical_highlights, "
        f"lessons_learned, project_summary, tags, embedding FROM presale_knowledge_case {where}"
    ).fetchall()

    logger.info(f"待处理案例: {len(rows)} 条 (force={args.force}, dry_run={args.dry_run})")

    if args.dry_run:
        for r in rows:
            txt = build_case_text(r)
            print(f"  [{r['id']}] {r['case_name'][:30]} -> {txt[:60]}...")
        return

    if not rows:
        logger.info("无待处理案例，退出")
        return

    # 加载 AI 客户端
    try:
        from app.services.ai_client_service import AIClientService
        ai = AIClientService()
    except Exception as e:
        logger.error(f"AI 客户端加载失败: {e}")
        sys.exit(1)

    # 先测一次 embedding 是否可用（用第一条试水）
    test_text = build_case_text(rows[0])
    test = ai.embed_texts([test_text])
    if not test.get("ok"):
        logger.error(
            "❌ embedding API 不可用: %s\n"
            "👉 请到阿里云百炼控制台给当前 ALIBABA_API_KEY 开通 text-embedding-v3 权限，"
            "或检查 key 是否是标准 dashscope key（非 Coding Plan 专属 key）。",
            test.get("error"),
        )
        sys.exit(1)

    logger.info(f"✓ embedding API 可用（dim={len(test['embeddings'][0])}），开始批量处理")

    # 批量处理
    success, failed = 0, 0
    for i in range(0, len(rows), args.batch_size):
        batch = rows[i : i + args.batch_size]
        texts = [build_case_text(r) for r in batch]
        result = ai.embed_texts(texts)
        if not result.get("ok"):
            logger.warning(f"批次 {i//args.batch_size} 失败: {result.get('error')}，跳过")
            failed += len(batch)
            continue
        embeddings = result["embeddings"]
        for row, emb in zip(batch, embeddings):
            conn.execute(
                "UPDATE presale_knowledge_case SET embedding = ? WHERE id = ?",
                (serialize_embedding(emb), row["id"]),
            )
            success += 1
        conn.commit()
        logger.info(f"批次 {i//args.batch_size + 1}: 已写入 {success}/{len(rows)}")

    conn.close()
    logger.info(f"完成: 成功 {success}, 失败 {failed}")


if __name__ == "__main__":
    main()
