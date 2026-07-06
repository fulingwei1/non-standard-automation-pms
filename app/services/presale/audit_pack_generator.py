# -*- coding: utf-8 -*-
"""
验厂资料包生成引擎。

销售上传客户验厂清单 → AI 逐条分析清单要求 → 从公司知识库匹配内容 → 生成 HTML 资料包。

核心逻辑：
  1. AI 解析验厂清单，把客户要求分类（公司资质/产能设备/质量控制/EHS/客户案例/财务等）
  2. 对每个类别，从 company_profile 知识库查匹配内容
  3. 对查不到的内容，AI 标注"需补充"（诚实，不编造）
  4. 生成结构化 HTML 资料包（客户可直接用）
"""
import json
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.ai_client_service import AIClientService

logger = logging.getLogger("presale.audit_pack")

CSS = """
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: "Microsoft YaHei", Arial, sans-serif; background: #f5f5f5; padding: 20px; }
.container { max-width: 1000px; margin: 0 auto; background: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
h1 { color: #1a237e; font-size: 22px; text-align: center; margin-bottom: 5px; }
.subtitle { text-align: center; color: #666; margin-bottom: 30px; font-size: 13px; }
h2 { color: #1a237e; font-size: 16px; margin: 25px 0 10px; padding-bottom: 5px; border-bottom: 2px solid #e3f2fd; }
.section { margin-bottom: 20px; }
.req-item { margin-bottom: 12px; padding: 12px; border: 1px solid #e0e0e0; border-radius: 6px; }
.req-item .req-title { font-weight: bold; color: #333; margin-bottom: 5px; font-size: 13px; }
.req-item .our-response { font-size: 12px; color: #555; line-height: 1.6; }
.req-item .status { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 10px; margin-left: 8px; }
.status.ready { background: #c8e6c9; color: #2e7d32; }
.status.partial { background: #fff9c4; color: #f57f17; }
.status.need { background: #ffcdd2; color: #c62828; }
.cover-page { text-align: center; padding: 60px 20px; border: 2px solid #1a237e; border-radius: 8px; margin-bottom: 30px; }
.cover-page h1 { font-size: 28px; margin-bottom: 10px; }
.cover-page .company { font-size: 18px; color: #1a237e; margin: 15px 0; }
.cover-page .info { margin-top: 20px; font-size: 13px; color: #666; line-height: 2; }
.note { margin-top: 20px; padding: 15px; background: #fff3e0; border-left: 4px solid #ff9800; border-radius: 4px; font-size: 12px; }
"""


def generate_audit_pack(
    db: Session,
    ai: AIClientService,
    checklist_text: str,
    customer_name: str,
    customer_industry: str = None,
) -> str:
    """
    主入口：读验厂清单 → AI 分析 → 生成 HTML 资料包。

    Returns: HTML 字符串
    """
    # 1. 查公司知识库全量（给 AI 当素材）
    company_data = _load_company_profile(db)

    # 2. AI 分析清单 + 匹配内容
    analysis = _analyze_checklist(ai, checklist_text, company_data, customer_name, customer_industry)

    # 3. 渲染 HTML
    return _render_html(customer_name, customer_industry, checklist_text, analysis)


def _load_company_profile(db: Session) -> str:
    """加载公司知识库全量。"""
    rows = db.execute(text(
        "SELECT category, key, content FROM company_profile WHERE is_active=1 ORDER BY sort_order"
    )).all()
    if not rows:
        return "（公司知识库暂无数据）"
    lines = []
    for r in rows:
        lines.append(f"【{r[1]}】\n{r[2]}")
    return "\n\n".join(lines)


def _analyze_checklist(
    ai: AIClientService,
    checklist_text: str,
    company_data: str,
    customer_name: str,
    customer_industry: str,
) -> Dict[str, Any]:
    """
    AI 读验厂清单，逐条分析并匹配公司资料。

    返回 {title, subtitle, sections: [{title, items: [{req, response, status}]}], summary}
    """
    prompt = (
        "你是金凯博自动化测试公司的资质专员。客户发来了验厂/资质审查清单，"
        "请逐条分析清单要求，并从公司资料库中匹配对应内容，生成验厂资料包。\n\n"
        f"## 客户信息\n客户：{customer_name}\n行业：{customer_industry or '未指定'}\n\n"
        f"## 客户验厂清单\n{checklist_text[:2000]}\n\n"
        f"## 金凯博公司资料库\n{company_data[:3000]}\n\n"
        "## 输出要求\n"
        "严格输出 JSON：\n"
        "{\n"
        '  "title": "资料包标题（如：金凯博供应商资质审查资料包）",\n'
        '  "subtitle": "副标题（为客户XXX准备）",\n'
        '  "sections": [\n'
        "    {\n"
        '      "title": "分类标题（如：公司基本资质/产能与设备/质量控制/EHS/客户业绩）",\n'
        '      "items": [\n'
        '        {\n'
        '          "req": "客户清单中的要求（原文或概括）",\n'
        '          "response": "我方的对应资料/说明（从公司资料库匹配，详细写）",\n'
        '          "status": "ready（已有资料）/ partial（部分满足）/ need（需补充，标注缺什么）"\n'
        "        }\n"
        "      ]\n"
        "    }\n"
        "  ],\n"
        '  "summary": {"ready": 数字, "partial": 数字, "need": 数字, "note": "总体说明"},\n'
        '  "missing_items": ["标注所有 status=need 的项，提醒销售需要补充什么资料"]\n'
        "}\n"
        "要求：\n"
        "1. 必须覆盖清单里的每一项要求，不能遗漏\n"
        "2. response 要从公司资料库里真实匹配，有就写有，没有就标 need\n"
        "3. 不要编造公司没有的资质或案例\n"
        "4. 按验厂清单的逻辑分类（不是按公司资料库的分类）"
    )
    try:
        resp = ai.generate_solution(prompt, model="qwen3-coder-plus", temperature=0.3, max_tokens=3000)
        raw = resp.get("content") or ""
        raw = raw.strip().strip("`")
        if raw.startswith("json"):
            raw = raw[4:].strip()
        result = json.loads(raw)
        result["ok"] = True
        return result
    except Exception as e:
        logger.warning("验厂清单分析失败: %s", e)
        return {
            "title": "金凯博验厂资料包",
            "subtitle": f"为{customer_name}准备",
            "sections": [{"title": "原始清单", "items": [{"req": checklist_text[:200], "response": "AI解析失败，请人工处理", "status": "need"}]}],
            "summary": {"ready": 0, "partial": 0, "need": 1, "note": "AI 分析失败"},
            "ok": False,
        }


def _render_html(
    customer_name: str,
    customer_industry: str,
    checklist_text: str,
    analysis: Dict[str, Any],
) -> str:
    """渲染 HTML 资料包。"""

    # 封面
    cover = f"""
    <div class="cover-page">
        <h1>{analysis.get('title', '验厂资料包')}</h1>
        <div class="company">深圳市金凯博自动化测试有限公司</div>
        <div class="info">
            客户：{customer_name}<br>
            行业：{customer_industry or '-'}<br>
            日期：{datetime_now()}<br>
            本资料仅供 {customer_name} 验厂/资质审查使用
        </div>
    </div>"""

    # 各分类
    sections_html = ""
    for sec in analysis.get("sections", []):
        items_html = ""
        for item in sec.get("items", []):
            status = item.get("status", "need")
            status_label = {"ready": "✓ 已有", "partial": "△ 部分满足", "need": "✗ 需补充"}.get(status, "")
            items_html += f"""
            <div class="req-item">
                <div class="req-title">{item.get('req', '')}<span class="status {status}">{status_label}</span></div>
                <div class="our-response">{item.get('response', '')}</div>
            </div>"""
        sections_html += f'<h2>{sec.get("title", "")}</h2><div class="section">{items_html}</div>'

    # 统计 + 缺失提醒
    summary = analysis.get("summary", {})
    missing = analysis.get("missing_items", [])
    summary_html = f"""
    <div class="note">
        <strong>资料覆盖度：✓已有 {summary.get('ready', 0)} 项 | △部分 {summary.get('partial', 0)} 项 | ✗需补充 {summary.get('need', 0)} 项</strong>
        <br>{summary.get('note', '')}
    </div>"""

    missing_html = ""
    if missing:
        missing_html = '<h2>⚠️ 需销售补充的资料</h2><div class="section">'
        for m in missing:
            missing_html += f'<div class="req-item"><div class="req-title">需补充</div><div class="our-response">{m}</div></div>'
        missing_html += "</div>"

    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{analysis.get('title', '验厂资料包')}</title><style>{CSS}</style></head>
<body><div class="container">
{cover}
{sections_html}
{summary_html}
{missing_html}
<div style="text-align:center;margin-top:30px;color:#999;font-size:11px;">
    深圳市金凯博自动化测试有限公司 | 本资料由 AI 辅助生成，请人工确认后使用 | {datetime_now()}
</div>
</div></body></html>"""


def datetime_now():
    from datetime import datetime
    return datetime.now().strftime("%Y年%m月%d日")
