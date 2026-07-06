# -*- coding: utf-8 -*-
"""
售前智能体工具注册表（P1）

把分散的查询/AI 能力统一注册成"工具"，供 Agent 自主决策时调用。
每个工具包含：
  - name: 工具名（模型用它选工具）
  - description: 描述（告诉模型这个工具能干什么）
  - parameters: JSON Schema（模型按它生成参数）
  - handler: 实际执行的函数

设计原则：
  - 轻量：不引入框架，就是个 dict + register/execute 两个方法
  - 工具白名单：Agent 节点只能调用注册过的工具，防幻觉
  - handler 签名统一：handler(**args) -> str（返回字符串喂给模型）
  - 安全：handler 内部 try/except，永不抛异常到循环外
"""
import json
import logging
from typing import Any, Callable, Dict, List, Optional

from sqlalchemy.orm import Session

from app.services.presale.ammo_library_service import AmmoLibraryService

logger = logging.getLogger("presale.tools")


class ToolRegistry:
    """工具注册表"""

    def __init__(self, db: Session):
        self.db = db
        self._tools: Dict[str, Dict[str, Any]] = {}
        self._register_defaults()

    def register(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        handler: Callable[..., str],
    ) -> None:
        """注册一个工具。"""
        self._tools[name] = {
            "name": name,
            "description": description,
            "parameters": parameters,
            "handler": handler,
        }

    def get_openai_tools(self, names: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """返回 OpenAI function calling 格式的工具定义（供 chat_with_tools 用）。

        Args:
            names: 限定返回哪些工具（None=全部，白名单控制）
        """
        result = []
        for name, tool in self._tools.items():
            if names and name not in names:
                continue
            result.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["parameters"],
                },
            })
        return result

    def execute(self, name: str, args: Dict[str, Any]) -> str:
        """执行工具（Agent 循环调用此方法）。失败返回错误字符串，不抛异常。"""
        tool = self._tools.get(name)
        if not tool:
            return f"错误：未知工具 '{name}'。可用工具：{list(self._tools.keys())}"
        try:
            result = tool["handler"](**(args or {}))
            return result if isinstance(result, str) else json.dumps(result, ensure_ascii=False, default=str)
        except Exception as e:
            logger.warning("工具执行失败 %s args=%s err=%s", name, str(args)[:100], e)
            return f"工具 {name} 执行失败：{e}"

    # ============= 默认工具注册（金凯博售前场景） =============

    def _register_defaults(self) -> None:
        """注册售前智能体可用的工具集。"""
        ammo = AmmoLibraryService(self.db)

        # 1. 综合检索弹药库
        self.register(
            name="search_ammo",
            description=(
                "检索历史售前弹药库：相似项目案例 + 同类设备报价区间 + 推荐方案模板 + 标准模块。"
                "用于回答'有没有类似项目''这类设备大概多少钱'。"
            ),
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "查询内容，如'BMS测试设备'或'800V电驱'"},
                    "industry": {"type": "string", "description": "行业过滤（可选），如'新能源汽车'"},
                    "equipment_type": {"type": "string", "description": "设备类型过滤（可选），如'老化设备'"},
                },
                "required": ["query"],
            },
            handler=lambda query, industry=None, equipment_type=None: _tool_search_ammo(
                ammo, query, industry, equipment_type
            ),
        )

        # 2. 查报价区间
        self.register(
            name="quote_range",
            description=(
                "查询某类设备的历史报价区间（最低/中位/最高 + 毛利区间 + 交期）。"
                "用于报价时对标历史价格。"
            ),
            parameters={
                "type": "object",
                "properties": {
                    "industry": {"type": "string", "description": "行业（可选）"},
                    "equipment_type": {"type": "string", "description": "设备类型（可选），如'ICT测试'"},
                },
            },
            handler=lambda industry=None, equipment_type=None: _tool_quote_range(
                ammo, industry, equipment_type
            ),
        )

        # 3. 查历史案例的验收难点/教训
        self.register(
            name="case_lessons",
            description=(
                "查询某类项目的历史教训/验收难点（从相似案例库提取）。"
                "用于风险深挖时找'这类项目常踩什么坑'。"
            ),
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "项目类型关键词，如'BMS'或'老化测试'"},
                    "top_k": {"type": "integer", "description": "返回条数（默认5）"},
                },
                "required": ["query"],
            },
            handler=lambda query, top_k=5: _tool_case_lessons(ammo, query, top_k),
        )

        # 4. 查标准模块库（BOM 模板）
        self.register(
            name="standard_modules",
            description=(
                "查询标准模块库（机架/电控柜/视觉模组等），含参考成本和典型组件。"
                "用于估算 BOM 和关键部件。"
            ),
            parameters={
                "type": "object",
                "properties": {
                    "keyword": {"type": "string", "description": "模块关键词（可选），如'视觉'或'电控'"},
                },
            },
            handler=lambda keyword=None: _tool_standard_modules(ammo, keyword),
        )

        # 5. 查标准件价格库（P4 成本对标）
        self.register(
            name="standard_costs",
            description=(
                "查询标准件价格库（从历史报价聚合的部件级标准成本，含样本数和价格波动度CV）。"
                "用于回答'这个部件历史报多少钱''这个报价偏高还是偏低'。"
            ),
            parameters={
                "type": "object",
                "properties": {
                    "keyword": {"type": "string", "description": "部件关键词，如'电控柜'或'视觉'或'机器人'"},
                },
            },
            handler=lambda keyword=None: _tool_standard_costs(ammo, keyword),
        )

        # 6. 查金凯博优势产品库（KC2700 FCT 全系列等，核心卖点数据）
        self.register(
            name="advantage_products",
            description=(
                "查询金凯博优势产品库（自有产品系列，含型号/规格/产能/价格/核心技术）。"
                "用于方案选型时引用我方真实产品型号和参数。"
                "如查FCT产品传keyword='FCT'，查ICT传'ICT'。"
            ),
            parameters={
                "type": "object",
                "properties": {
                    "keyword": {"type": "string", "description": "产品关键词，如'FCT''ICT''BMS''老化'"},
                },
            },
            handler=lambda keyword=None: _tool_advantage_products(keyword),
        )

        # 7. 查金凯博公司知识库（销售问"我们做过什么/客户/技术实力"时用）
        self.register(
            name="company_brief",
            description=(
                "查询金凯博公司知识库：公司简介/业务领域/典型客户/技术实力/产品体系/发展历程。"
                "销售问'我们做过什么''有哪些客户''技术强在哪''有没有类似案例'时用这个工具。"
                "category可选：overview(概览)/business(业务领域)/customers(客户)/tech(技术)/products(产品)"
            ),
            parameters={
                "type": "object",
                "properties": {
                    "category": {"type": "string", "description": "分类（可选）：overview/business/customers/tech/products。不传则全部返回"},
                    "keyword": {"type": "string", "description": "关键词搜索（可选），如'汽车电子''BMS''客户'"},
                },
            },
            handler=lambda category=None, keyword=None: _tool_company_brief(category, keyword),
        )


# ============= 工具实现（包装 AmmoLibraryService，返回模型友好的字符串） =============

def _tool_search_ammo(ammo: AmmoLibraryService, query: str, industry: str, equipment_type: str) -> str:
    r = ammo.search_ammo(query, industry=industry, equipment_type=equipment_type, top_k=5)
    lines = []
    cases = r.get("similar_cases", [])
    if cases:
        lines.append(f"找到 {len(cases)} 个相似案例：")
        for i, c in enumerate(cases, 1):
            lines.append(
                f"  {i}. {c.get('case_name','')}（{c.get('equipment_type','')} / {c.get('industry','')}）"
                f" 亮点：{c.get('technical_highlights','')[:60]}"
                f" 教训：{c.get('lessons_learned','')[:60]}"
            )
    else:
        lines.append("无相似历史案例。")
    qr = r.get("quote_range", {})
    if qr.get("sample_count"):
        p = qr.get("price", {})
        lines.append(
            f"历史报价：{p.get('min')}~{p.get('max')}元（中位 {p.get('median')}），"
            f"样本 {qr.get('sample_count')} 条"
        )
    return "\n".join(lines)


def _tool_quote_range(ammo: AmmoLibraryService, industry: str, equipment_type: str) -> str:
    qr = ammo.quote_range(industry=industry, equipment_type=equipment_type)
    if not qr.get("sample_count"):
        return "无匹配的历史报价数据。"
    p = qr.get("price", {})
    m = qr.get("margin_pct", {})
    lt = qr.get("lead_time_days", {})
    return (
        f"基于 {qr.get('sample_count')} 条历史报价："
        f"价格 {p.get('min')}~{p.get('max')}元（中位 {p.get('median')}），"
        f"毛利 {m.get('min')}%~{m.get('max')}%（中位 {m.get('median')}%），"
        f"交期 {lt.get('min')}~{lt.get('max')}天（中位 {lt.get('median')}）。"
    )


def _tool_case_lessons(ammo: AmmoLibraryService, query: str, top_k: int) -> str:
    r = ammo.search_ammo(query, top_k=top_k)
    cases = r.get("similar_cases", [])
    if not cases:
        return "无相关历史教训。"
    lines = [f"找到 {len(cases)} 个相关项目的教训："]
    for c in cases:
        if c.get("lessons_learned"):
            lines.append(f"- [{c.get('equipment_type','')}] {c.get('lessons_learned','')[:120]}")
    return "\n".join(lines) if len(lines) > 1 else "相关案例无教训记录。"


def _tool_standard_modules(ammo: AmmoLibraryService, keyword: Optional[str]) -> str:
    # 复用 ammo 的内部检索（带 keyword 过滤）
    modules = ammo._search_standard_modules(equipment_type=keyword, top_k=8)
    if not modules:
        return "无匹配标准模块。"
    lines = [f"找到 {len(modules)} 个标准模块："]
    total = 0
    for m in modules:
        cost = m.get("ref_cost") or 0
        total += cost
        comps = m.get("typical_components") or []
        comp_str = "、".join(f"{c.get('name','')}×{c.get('qty','')}" for c in comps[:3])
        lines.append(f"- {m.get('module_name','')}（{m.get('category','')}）参考成本{cost}元，组件：{comp_str}")
    lines.append(f"合计参考成本：{total}元")
    return "\n".join(lines)


def _tool_company_brief(category: Optional[str] = None, keyword: Optional[str] = None) -> str:
    """查金凯博公司知识库。"""
    from sqlalchemy import text
    from app.models.base import SessionLocal
    db = SessionLocal()
    try:
        sql = "SELECT category, key, content FROM company_profile WHERE is_active=1"
        params = {}
        conditions = []
        if category:
            conditions.append("category = :cat")
            params["cat"] = category
        if keyword:
            conditions.append("(key LIKE :kw OR content LIKE :kw)")
            params["kw"] = f"%{keyword}%"
        if conditions:
            sql += " AND " + " AND ".join(conditions)
        sql += " ORDER BY sort_order LIMIT 10"
        rows = db.execute(text(sql), params).all()
        if not rows:
            return "无匹配的公司信息。"
        lines = [f"找到 {len(rows)} 条公司信息："]
        for r in rows:
            lines.append(f"\n【{r[1]}】")
            lines.append(r[2])
        return "\n".join(lines)
    finally:
        db.close()


def _tool_advantage_products(keyword: Optional[str]) -> str:
    """查金凯博优势产品库（KC2700 FCT 全系列等，核心卖点）。"""
    from sqlalchemy import text
    from app.models.base import SessionLocal
    db = SessionLocal()
    try:
        kw = f"%{keyword}%" if keyword else "%FCT%"
        rows = db.execute(text(
            "SELECT product_code, product_name, automation_level, workstation_count, "
            "max_throughput_uph, typical_ct_seconds, rail_type, test_types, "
            "substr(description,1,120) FROM advantage_products "
            "WHERE is_active=1 AND (product_name LIKE :kw OR test_types LIKE :kw OR description LIKE :kw) "
            "ORDER BY product_code LIMIT 10"
        ), {"kw": kw}).all()
        if not rows:
            rows = db.execute(text(
                "SELECT product_code, product_name, automation_level, workstation_count, "
                "max_throughput_uph, typical_ct_seconds, rail_type, test_types, "
                "substr(description,1,120) FROM advantage_products "
                "WHERE is_active=1 ORDER BY product_code LIMIT 8"
            )).all()
        if not rows:
            return "无匹配的优势产品。"
        lines = [f"找到 {len(rows)} 个金凯博优势产品（我方真实产品线）："]
        for r in rows:
            lines.append(
                f"- {r[1]}（{r[0]}）：{r[2] or ''} {r[3] or 0}工位 {r[6] or ''} "
                f"UPH{r[4] or '?'} CT{r[5] or '?'}s | {r[7] or ''} | {r[8] or ''}"
            )
        return "\n".join(lines)
    finally:
        db.close()


def _tool_standard_costs(ammo: AmmoLibraryService, keyword: Optional[str]) -> str:
    """查标准件价格库（部件级历史成本）。"""

    std_costs = ammo.get_standard_costs(keyword=keyword)
    if not std_costs:
        return "无匹配的标准件价格数据。"
    lines = [f"找到 {len(std_costs)} 个标准件价格："]
    for sc in std_costs[:10]:
        src = sc.get("source", "")
        cost_source = sc.get("cost_source", "")
        # 来源标注：PURCHASE_HISTORY=真实采购价（更权威），HISTORICAL_QUOTE=报价均价
        source_tag = "采购价" if cost_source == "PURCHASE_HISTORY" else "报价均价"
        cv_flag = ""
        if "CV=" in src:
            try:
                cv_val = float(src.split("CV=")[1].rstrip("%"))
                if cv_val > 50:
                    cv_flag = "（⚠波动大）"
                elif cv_val == 0:
                    cv_flag = "（✓价格稳定）"
            except Exception:
                pass
        lines.append(
            f"- {sc.get('cost_name','')}（{sc.get('category','')}/{source_tag}）标准成本 {sc.get('standard_cost',0)} 元/{sc.get('unit','')} "
            f"{cv_flag}"
        )
    return "\n".join(lines)
