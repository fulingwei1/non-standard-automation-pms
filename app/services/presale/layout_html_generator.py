# -*- coding: utf-8 -*-
"""
产线布局图 HTML 生成器

把整线方案的 line_stations 数据，渲染成可视化 HTML 布局图。
灵感来自金凯博样本《DIP产线布局图_详细版.html》——用 HTML+CSS 色块+箭头画整线，
客供设备虚线区分，浏览器直接打开，手机/平板都能看。

两种模式：
  1. AI 生成（_generate_layout_with_ai）：让 AI 基于需求自主设计布局，灵活但可能不稳定
  2. 模板渲染（render_layout_html）：基于结构化 line_stations 数据套模板，稳定

默认用模式2（稳定），AI 模式1 作为补充。
"""
import json
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("presale.layout")

# 设备类别 → 颜色映射（对齐样本 HTML 的配色）
CATEGORY_COLORS = {
    "传输": "#B8D4E8",
    "测试": "#FFD699",
    "涂覆": "#C8E6C9",
    "点胶": "#C8E6C9",
    "固化": "#FFCCCC",
    "分板": "#E1BEE7",
    "包装": "#FFF9C4",
    "辅助": "#FFF9C4",
    "客供": "#EEEEEE",
}

CSS_TEMPLATE = """
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: "Microsoft YaHei", Arial, sans-serif; background: #f5f5f5; padding: 20px; }
.container { background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); overflow-x: auto; }
h1 { text-align: center; color: #333; margin-bottom: 10px; font-size: 22px; }
.subtitle { text-align: center; color: #666; margin-bottom: 25px; font-size: 13px; }
.section { margin-bottom: 25px; }
.section-title { font-size: 14px; font-weight: bold; color: #0066cc; margin-bottom: 10px; padding: 5px 10px; background: #e3f2fd; border-radius: 4px; display: inline-block; }
.line-container { display: flex; align-items: center; flex-wrap: wrap; gap: 2px; }
.equipment { display: flex; flex-direction: column; align-items: center; justify-content: center; margin: 0 2px; padding: 8px 6px; border-radius: 4px; font-size: 11px; text-align: center; min-height: 64px; min-width: 60px; border: 2px solid #666; }
.equipment.customer { border: 2px dashed #999; }
.equipment .name { font-weight: bold; margin-bottom: 3px; }
.equipment .size { font-size: 9px; color: #555; }
.equipment .ct { font-size: 9px; color: #cc0000; margin-top: 2px; }
.arrow { width: 24px; height: 2px; background: #cc0000; position: relative; flex-shrink: 0; }
.arrow::after { content: ''; position: absolute; right: 0; top: -4px; border: 5px solid transparent; border-left: 8px solid #cc0000; }
.note { margin-top: 15px; padding: 12px; background: #fff3e0; border-left: 4px solid #ff9800; border-radius: 4px; font-size: 12px; }
.legend { display: flex; flex-wrap: wrap; gap: 15px; margin-top: 20px; padding: 12px; background: #fafafa; border-radius: 4px; }
.legend-item { display: flex; align-items: center; gap: 6px; font-size: 11px; }
.legend-color { width: 20px; height: 14px; border-radius: 3px; border: 1px solid #666; }
.legend-color.dashed { border: 2px dashed #999; }
table { width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 11px; }
th, td { border: 1px solid #ddd; padding: 6px; text-align: center; }
th { background: #f5f5f5; font-weight: bold; }
"""


def render_layout_html(
    project_name: str,
    requirement_summary: str,
    stations: List[Dict[str, Any]],
    customer_equipments: List[Dict[str, Any]] = None,
) -> str:
    """
    基于结构化工位数据，渲染产线布局图 HTML。

    Args:
        project_name: 项目名
        requirement_summary: 需求摘要（用于副标题）
        stations: 工位列表 [{station, function, key_equipment, ct_seconds, is_customer}]
        customer_equipments: 客供设备列表（额外标注用）
    """
    # 按工位顺序渲染
    stations_html = []
    for i, s in enumerate(stations):
        name = s.get("station") or s.get("name") or f"工位{i+1}"
        eq = s.get("key_equipment") or ""
        ct = s.get("ct_seconds")
        is_customer = s.get("is_customer") or "客供" in name or "客供" in str(eq)

        # 推断颜色
        category = _infer_category(name, eq)
        color = "#EEEEEE" if is_customer else CATEGORY_COLORS.get(category, "#B8D4E8")

        css_class = "equipment customer" if is_customer else "equipment"
        style = f"background: {color};"
        if is_customer:
            style = ""  # customer class 自带背景

        station_html = f'<div class="{css_class}" style="{style}">'
        station_html += f'<div class="name">{name}</div>'
        if eq:
            station_html += f'<div class="size">{str(eq)[:20]}</div>'
        if ct:
            station_html += f'<div class="ct">CT {ct}s</div>'
        station_html += "</div>"

        stations_html.append(station_html)
        # 工位之间加箭头（最后一个不加）
        if i < len(stations) - 1:
            stations_html.append('<div class="arrow"></div>')

    stations_block = "\n                    ".join(stations_html)

    # 客供设备提示
    customer_note = ""
    if customer_equipments:
        names = [c.get("equipment", "") for c in customer_equipments[:5]]
        customer_note = (
            '<div class="note"><strong>客供设备（虚线边框）</strong>：'
            + "、".join(n for n in names if n)
            + "。需提前确认接口协议，联调责任边界。</div>"
        )

    # 图例
    legend_items = []
    for cat, color in CATEGORY_COLORS.items():
        if cat == "客供":
            legend_items.append(
                f'<div class="legend-item"><div class="legend-color dashed" style="background:{color}"></div><span>{cat}设备</span></div>'
            )
        else:
            legend_items.append(
                f'<div class="legend-item"><div class="legend-color" style="background:{color}"></div><span>{cat}</span></div>'
            )
    legend_html = "\n                ".join(legend_items)

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{project_name} - 产线布局图</title>
<style>{CSS_TEMPLATE}</style>
</head>
<body>
<div class="container">
    <h1>🏭 {project_name} - 产线布局图</h1>
    <p class="subtitle">{requirement_summary}</p>

    <div class="section">
        <div class="section-title">📋 整线工位流程（{len(stations)} 个工位）</div>
        <div class="line-container">
                    {stations_block}
        </div>
    </div>

    {customer_note}

    <div class="legend">
                {legend_html}
    </div>

    <div class="note">
        <strong>📝 说明</strong>：本图为方案示意图，色块代表工位设备，红色箭头代表物料流向。
        虚线边框为客供设备。实际布局以 CAD 图纸为准，需客户确认后方可制作。
    </div>

    <div style="text-align:center; margin-top:15px; color:#999; font-size:11px;">
        由售前智能体自动生成 | {__import__("datetime").datetime.now().strftime("%Y-%m-%d")} | 示意图非精确比例
    </div>
</div>
</body>
</html>"""
    return html


def _infer_category(name: str, equipment: str) -> str:
    """根据工位/设备名推断类别（决定颜色）。"""
    text = f"{name} {equipment}".lower()
    if any(k in text for k in ["ict", "fct", "测试", "检测", "aoi"]):
        return "测试"
    if any(k in text for k in ["涂覆", "三防"]):
        return "涂覆"
    if any(k in text for k in ["点胶", "胶"]):
        return "点胶"
    if any(k in text for k in ["固化", "uv", "炉"]):
        return "固化"
    if any(k in text for k in ["分板", "切割", "铣"]):
        return "分板"
    if any(k in text for k in ["包装", "下料", "皮带"]):
        return "包装"
    if any(k in text for k in ["插件", "波峰焊", "喷雾"]):
        return "客供"
    return "传输"


def generate_layout_with_ai(
    ai, requirement_text: str, line_stations: List[Dict], project_name: str
) -> Optional[str]:
    """
    让 AI 基于需求+工位数据，生成增强版的 HTML 布局图。
    AI 负责补充分段（如"第一段：DIP段"）和布局优化建议，CSS 骨架固定。
    """
    stations_brief = json.dumps(line_stations[:15], ensure_ascii=False)
    prompt = (
        "你是产线布局设计专家。基于以下整线工位数据，生成一份产线布局图 HTML。\n\n"
        f"项目：{project_name}\n需求：{requirement_text[:200]}\n"
        f"工位数据：{stations_brief}\n\n"
        "要求：\n"
        "1. 把工位按工艺段分组（如'上板DIP段/测试段/涂覆点胶段/下料段'），每段一个 section\n"
        "2. 每个工位用色块表示，工位间用红色箭头连接\n"
        "3. 客供设备用虚线边框（class='equipment customer'）\n"
        "4. 涂覆/测试/固化/分板用不同颜色区分\n"
        "5. 底部加图例和说明\n"
        f"6. CSS 必须用这个骨架（不要改）：\n<style>{CSS_TEMPLATE}</style>\n\n"
        "直接输出完整 HTML 文档（<!DOCTYPE html> 开头），不要解释。"
        "色块背景色用：传输#B8D4E8 测试#FFD699 涂覆#C8E6C9 固化#FFCCCC 分板#E1BEE7 客供#EEEEEE。"
    )
    try:
        resp = ai.generate_solution(prompt, model="qwen3-coder-plus", temperature=0.3, max_tokens=4000)
        html = resp.get("content") or ""
        # 清理可能的 markdown 包裹
        html = html.strip()
        if html.startswith("```html"):
            html = html[7:]
        if html.startswith("```"):
            html = html[3:]
        if html.endswith("```"):
            html = html[:-3]
        html = html.strip()
        if "<!DOCTYPE" in html or "<html" in html:
            return html
        return None
    except Exception as e:
        logger.warning("AI 布局图生成失败: %s", e)
        return None


# ============================================================
# 技术规格书 HTML
# ============================================================

def render_spec_html(
    project_name: str,
    requirement_summary: str,
    deep_solution: Dict[str, Any],
    parsed: Dict[str, Any],
) -> str:
    """生成技术规格书 HTML（关键参数可视化卡片）。"""
    # 从方案数据抽设备规格
    equipment = deep_solution.get("equipment_selection", [])
    subsystems = deep_solution.get("subsystems", []) + deep_solution.get("line_stations", [])
    key_specs = parsed.get("key_specs", [])

    spec_css = CSS_TEMPLATE + """
    .spec-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 12px; margin-top: 12px; }
    .spec-card { border: 1px solid #e0e0e0; border-radius: 8px; padding: 12px; background: #fafafa; }
    .spec-card h4 { color: #0066cc; font-size: 13px; margin-bottom: 8px; border-bottom: 2px solid #e3f2fd; padding-bottom: 4px; }
    .spec-row { display: flex; justify-content: space-between; font-size: 11px; padding: 3px 0; border-bottom: 1px dotted #eee; }
    .spec-row .label { color: #666; }
    .spec-row .value { color: #333; font-weight: 500; text-align: right; }
    .key-spec-box { background: #e3f2fd; border-radius: 8px; padding: 12px; margin-bottom: 15px; }
    .key-spec-box h3 { color: #1565c0; font-size: 14px; margin-bottom: 8px; }
    .key-spec-tags { display: flex; flex-wrap: wrap; gap: 8px; }
    .key-spec-tag { background: #fff; border: 1px solid #90caf9; border-radius: 12px; padding: 4px 10px; font-size: 11px; color: #1565c0; }
    """

    # 关键指标卡
    key_spec_html = ""
    if key_specs:
        tags = "".join(f'<span class="key-spec-tag">{s}</span>' for s in key_specs[:10])
        key_spec_html = f'<div class="key-spec-box"><h3>🎯 关键技术指标</h3><div class="key-spec-tags">{tags}</div></div>'

    # 设备规格卡片
    cards_html = ""
    for eq in equipment[:12]:
        item = eq.get("item", "")
        spec = eq.get("spec", "")
        brand = eq.get("brand_suggestion", "")
        qty = eq.get("qty", eq.get("reason", ""))
        cards_html += f'''
        <div class="spec-card">
            <h4>{item}</h4>
            <div class="spec-row"><span class="label">规格</span><span class="value">{spec[:40]}</span></div>
            <div class="spec-row"><span class="label">品牌建议</span><span class="value">{brand}</span></div>
            {f'<div class="spec-row"><span class="label">数量</span><span class="value">{qty}</span></div>' if qty else ''}
        </div>'''

    # 子系统/工位卡片
    for ss in subsystems[:8]:
        name = ss.get("station") or ss.get("name", "")
        func = ss.get("function", "")
        cost = ss.get("ref_cost", ss.get("ct_seconds", ""))
        ct = ss.get("ct_seconds")
        cards_html += f'''
        <div class="spec-card">
            <h4>{name}</h4>
            <div class="spec-row"><span class="label">功能</span><span class="value">{(func or "")[:40]}</span></div>
            {f'<div class="spec-row"><span class="label">参考成本</span><span class="value">{cost}</span></div>' if cost else ''}
            {f'<div class="spec-row"><span class="label">节拍</span><span class="value">{ct}s</span></div>' if ct else ''}
        </div>'''

    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{project_name} - 技术规格书</title><style>{spec_css}</style></head>
<body><div class="container">
<h1>📋 {project_name} - 技术规格书关键信息</h1>
<p class="subtitle">{requirement_summary}</p>
{key_spec_html}
<h3 style="color:#0066cc;font-size:15px;margin:15px 0 5px;">🔧 核心设备规格</h3>
<div class="spec-grid">{cards_html}</div>
<div style="text-align:center;margin-top:15px;color:#999;font-size:11px;">由售前智能体自动生成 | {__import__("datetime").datetime.now().strftime("%Y-%m-%d")}</div>
</div></body></html>"""


# ============================================================
# 项目进度甘特图 HTML
# ============================================================

def render_gantt_html(
    project_name: str,
    requirement_summary: str,
    deep_solution: Dict[str, Any],
) -> str:
    """生成项目进度甘特图 HTML。"""
    phases = deep_solution.get("implementation_phases", [])

    gantt_css = CSS_TEMPLATE + """
    .gantt-table { width: 100%; border-collapse: collapse; margin-top: 12px; font-size: 11px; min-width: 900px; }
    .gantt-table th { background: #0066cc; color: white; padding: 8px 4px; text-align: center; border: 1px solid #1565c0; min-width: 50px; }
    .gantt-table td { border: 1px solid #ddd; padding: 6px 4px; text-align: center; }
    .gantt-table .task-name { text-align: left; padding-left: 10px; font-weight: 500; min-width: 140px; }
    .gantt-table .duration { color: #1565c0; font-weight: 600; }
    .gantt-bar { background: linear-gradient(90deg, #1e88e5, #42a5f5); border-radius: 3px; height: 20px; margin: 2px 1px; }
    .gantt-bar.critical { background: linear-gradient(90deg, #e53935, #ef5350); }
    .total-row { background: #e8f5e9; font-weight: bold; }
    """

    # 解析周数（从 phases 的 duration 里抽数字，"4周"→4）
    import re
    total_weeks = 0
    phase_weeks = []
    for ph in phases:
        dur = ph.get("duration", "")
        nums = re.findall(r"\d+", str(dur))
        weeks = int(nums[0]) if nums else 2
        phase_weeks.append(weeks)
        total_weeks += weeks

    if total_weeks == 0:
        total_weeks = 8  # 默认 8 周

    # 生成周列头
    week_cols = ""
    for w in range(1, total_weeks + 1):
        week_cols += f"<th>W{w}</th>"

    # 生成任务行（带甘特条）
    rows_html = ""
    current_start = 0
    for i, ph in enumerate(phases):
        name = ph.get("phase", f"阶段{i+1}")
        dur = ph.get("duration", f"{phase_weeks[i]}周")
        deliverables = ph.get("deliverables", "")
        weeks = phase_weeks[i]

        # 甘特条单元格
        bar_cells = ""
        for w in range(total_weeks):
            if current_start <= w < current_start + weeks:
                is_critical = i == 0 or "采购" in name or "设计" in name
                cls = "gantt-bar critical" if is_critical else "gantt-bar"
                bar_cells += f'<td><div class="{cls}"></div></td>'
            else:
                bar_cells += '<td></td>'
        current_start += weeks

        rows_html += f"""
        <tr>
            <td class="task-name">{name}<div style="font-size:9px;color:#999;font-weight:normal;">{deliverables[:30]}</div></td>
            <td class="duration">{dur}</td>
            {bar_cells}
        </tr>"""

    # 总行
    total_bar = "".join(f'<td><div class="gantt-bar" style="opacity:0.3"></div></td>' for _ in range(total_weeks))
    rows_html += f'<tr class="total-row"><td class="task-name">总计</td><td class="duration">{total_weeks}周</td>{total_bar}</tr>'

    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{project_name} - 项目进度计划</title><style>{gantt_css}</style></head>
<body><div class="container">
<h1>📅 {project_name} - 项目进度甘特图</h1>
<p class="subtitle">{requirement_summary} | 总工期 {total_weeks} 周</p>
<div style="overflow-x:auto;">
<table class="gantt-table">
<thead><tr><th>任务</th><th>工期</th>{week_cols}</tr></thead>
<tbody>{rows_html}</tbody>
</table>
</div>
<div class="note"><strong>说明</strong>：红色条为关键路径（设计/采购阶段），蓝色为常规阶段。工期基于方案估算，实际以合同为准。</div>
<div style="text-align:center;margin-top:15px;color:#999;font-size:11px;">由售前智能体自动生成 | {__import__("datetime").datetime.now().strftime("%Y-%m-%d")}</div>
</div></body></html>"""


# ============================================================
# 技术响应表 HTML（招标响应，客户要求 vs 我方响应）
# ============================================================

def render_response_html_with_ai(
    ai, project_name: str, requirement_text: str, deep_solution: Dict[str, Any],
) -> Optional[str]:
    """让 AI 基于客户需求逐条生成响应表（招标必备格式）。"""
    resp_css = CSS_TEMPLATE + """
    .resp-table { width: 100%; border-collapse: collapse; margin-top: 12px; font-size: 11px; }
    .resp-table th { background: #0066cc; color: white; padding: 8px; border: 1px solid #1565c0; text-align: center; }
    .resp-table td { border: 1px solid #ddd; padding: 8px; vertical-align: top; }
    .resp-table .req { background: #fafafa; }
    .resp-table .yes { color: #2e7d32; font-weight: bold; }
    .resp-table .partial { color: #f57c00; font-weight: bold; }
    .resp-table .no { color: #c62828; font-weight: bold; }
    .resp-table .section-header { background: #e3f2fd; font-weight: bold; color: #1565c0; }
    """
    prompt = (
        "你是售前投标专家。基于客户技术要求，生成一份技术响应表 HTML。\n\n"
        f"项目：{project_name}\n客户需求：\n{requirement_text[:1500]}\n\n"
        "要求：\n"
        "1. 把客户需求按类别分组（如'总体要求/生产能力/测试要求/涂覆点胶/信息化/安全/交付'），每个类别一个 section header 行\n"
        "2. 每条要求一行：序号 | 客户要求 | 性质(★关键/●一般) | 我方响应(详细说明如何满足) | 响应结果(完全响应/部分响应/偏离)\n"
        "3. 响应结果用颜色区分：完全响应=绿色,部分响应=橙色,偏离=红色\n"
        "4. 我方响应要具体（写清方案怎么做），不能只写'满足'\n"
        f"5. CSS 用这个骨架：\n<style>{resp_css}</style>\n\n"
        "直接输出完整 HTML（<!DOCTYPE html>开头），不要解释。"
    )
    try:
        resp = ai.generate_solution(prompt, model="qwen3-coder-plus", temperature=0.3, max_tokens=4000)
        html = (resp.get("content") or "").strip()
        if html.startswith("```html"):
            html = html[7:]
        if html.startswith("```"):
            html = html[3:]
        if html.endswith("```"):
            html = html[:-3]
        html = html.strip()
        if "<!DOCTYPE" in html or "<html" in html:
            return html
        return None
    except Exception as e:
        logger.warning("AI 响应表生成失败: %s", e)
        return None
