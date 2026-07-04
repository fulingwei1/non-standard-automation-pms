"""
售前弹药库统一视图服务

把多源数据整合成一个"弹药库"，供售前智能体和销售查询复用：
  - case_lib    历史案例（presale_knowledge_case，含技术亮点/教训/标签）
  - quote_ammo  历史报价明细（quote_versions + quote_items，给报价区间）
  - solution_tpl 方案模板（presale_solution_templates）
  - module_lib  标准模块库（ai_standard_modules，给 BOM 模板）

核心对外能力：
  search_ammo(query, industry, equipment_type, top_k)
    -> 相似案例 + 同类设备报价区间 + 推荐方案模板 + 标准模块
  quote_range(industry, equipment_type)
    -> {min, p25, median, p75, max, sample_count, margin_range}

设计原则：
  - 不依赖 embedding（M2 才补），先用关键词 + 行业/设备过滤做召回
  - 报价区间用真实 quote_versions 聚合，过滤掉明显脏数据（毛利<-50% 或 >80%）
  - 返回结构扁平，方便前端/智能体直接用
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


# 行业缩写/同义词扩展（embedding 不可用时，用这个弥补关键词检索的语义鸿沟）
# 键是查询里可能出现的词，值是案例库里对应的同义词列表
SYNONYMS = {
    "bms": ["电池管理", "电池管理系统", "bms"],
    "ict": ["ict", "在线测试", "电路测试"],
    "fct": ["fct", "功能测试", "功能检测"],
    "eol": ["eol", "下线测试", "下线检测"],
    "aoi": ["aoi", "光学检测", "视觉检测", "外观检测"],
    "sic": ["碳化硅", "sic", "功率器件"],
    "gan": ["氮化镓", "gan", "功率器件"],
    "电驱": ["电机", "电机控制", "电驱", "驱动"],
    "压缩机": ["压缩机", "空调压缩机", "白电压缩机"],
    "电子负载": ["电子负载", "大电流", "功率负载"],
    "800v": ["800v", "高压", "高压电驱"],
    "1000a": ["1000a", "大电流"],
    "老化": ["老化", "老化测试", "老化房", "burn-in"],
    "烧录": ["烧录", "烧录器", "编程器", "programmer"],
    "smt": ["smt", "表面贴装", "贴片"],
    "动力电池": ["动力电池", "锂电池", "电池包", "pack"],
    "新能源汽车": ["新能源汽车", "电动汽车", "新能源", "ev"],
    "医疗": ["医疗", "医疗器械", "医用"],
    "消费电子": ["消费电子", "手机", "平板", "3c"],
}


def _expand_synonyms(query: str) -> str:
    """把查询里的缩写/术语扩展成同义词拼接，弥补关键词检索的语义鸿沟。"""
    ql = query.lower()
    extras = []
    for kw, syns in SYNONYMS.items():
        if kw in ql:
            extras.extend(syns)
    return (query + " " + " ".join(extras)) if extras else query


class AmmoLibraryService:
    """售前弹药库统一视图"""

    def __init__(self, db: Session):
        self.db = db

    # ============= 主入口：综合检索 =============

    def search_ammo(
        self,
        query: str,
        industry: Optional[str] = None,
        equipment_type: Optional[str] = None,
        top_k: int = 5,
    ) -> Dict[str, Any]:
        """
        综合检索弹药库。

        Args:
            query: 自然语言查询（如"800V电驱测试系统"）
            industry: 行业过滤
            equipment_type: 设备类型过滤（ICT测试/FCT测试/EOL测试/烧录设备/老化设备/视觉检测）
            top_k: 返回案例数

        Returns:
            {
                "query": ...,
                "similar_cases": [...],       # 相似历史案例
                "quote_range": {...},         # 同类设备报价区间
                "solution_templates": [...],  # 推荐方案模板
                "standard_modules": [...],    # 标准模块（BOM 模板）
                "summary": "...",             # 一句话总结
            }
        """
        similar_cases = self._search_cases(
            query, industry, equipment_type, top_k
        )
        quote_range = self.quote_range(industry, equipment_type)
        solution_templates = self._search_solution_templates(
            industry, equipment_type, top_k=3
        )
        standard_modules = self._search_standard_modules(equipment_type, top_k=5)

        summary = self._build_summary(
            query, similar_cases, quote_range, solution_templates
        )

        return {
            "query": query,
            "filters": {"industry": industry, "equipment_type": equipment_type},
            "similar_cases": similar_cases,
            "quote_range": quote_range,
            "solution_templates": solution_templates,
            "standard_modules": standard_modules,
            "summary": summary,
        }

    # ============= 案例检索 =============

    def _search_cases(
        self,
        query: str,
        industry: Optional[str],
        equipment_type: Optional[str],
        top_k: int,
    ) -> List[Dict[str, Any]]:
        """
        召回相似案例：优先 embedding 语义检索，失败/无向量时回退关键词。

        embedding 来自百炼 text-embedding-v3（generate_case_embeddings.py 预生成）。
        百炼 key 无 embedding 权限时自动回退关键词，不报错。
        """
        sql = """
            SELECT id, case_name, source_project_id, industry, equipment_type,
                   customer_name, project_amount, project_summary,
                   technical_highlights, success_factors, lessons_learned,
                   tags, quality_score, embedding
            FROM presale_knowledge_case
            WHERE is_public = 1
              AND case_name NOT LIKE 'presale_knowledge_case_%'
              AND case_name NOT LIKE 'case_name_%'
              AND case_name NOT LIKE '%_name_%'
        """
        params: Dict[str, Any] = {}
        conditions = []
        if industry:
            conditions.append("industry = :industry")
            params["industry"] = industry
        if equipment_type:
            conditions.append("equipment_type = :equipment_type")
            params["equipment_type"] = equipment_type
        if conditions:
            sql += " AND " + " AND ".join(conditions)

        rows = self.db.execute(text(sql), params).mappings().all()
        rows = [dict(r) for r in rows]
        if not rows:
            return []

        # 尝试 embedding 语义检索
        scored = self._semantic_score(query, rows)
        if scored is None:
            # embedding 不可用 → 关键词打分 + 同义词扩展（弥补语义鸿沟）
            expanded = _expand_synonyms(query)
            query_terms = [t for t in expanded.replace("/", " ").split() if len(t) >= 2]
            scored = [(r, self._keyword_score(expanded, query_terms, r)) for r in rows]

        scored.sort(key=lambda x: x[1], reverse=True)
        return [
            {
                **{k: v for k, v in r.items() if k != "embedding"},  # 不返回 embedding
                "tags": _safe_json_loads(r.get("tags")),
                "project_amount": float(r["project_amount"]) if r.get("project_amount") else None,
                "quality_score": float(r["quality_score"]) if r.get("quality_score") else None,
                "match_score": round(s, 3),
            }
            for r, s in scored[:top_k]
            if s > 0 or len(scored) <= top_k  # 没匹配也返回（数量不足时）
        ]

    def _semantic_score(self, query: str, rows: List[Dict[str, Any]]):
        """
        用 embedding 算 query 与各案例的余弦相似度。
        返回 [(case, score), ...]；embedding 不可用（无 key/无向量）返回 None 触发回退。
        """
        # 至少要有一条案例有 embedding 才值得调 API
        has_embedding = any(_parse_embedding(r.get("embedding")) for r in rows)
        if not has_embedding:
            return None

        try:
            from app.services.ai_client_service import AIClientService
            import numpy as np

            ai = AIClientService()
            result = ai.embed_texts([query])
            if not result.get("ok"):
                return None  # key 无权限或失败 → 回退关键词

            query_vec = np.array(result["embeddings"][0])
            qn = np.linalg.norm(query_vec)

            scored = []
            for r in rows:
                case_vec = _parse_embedding(r.get("embedding"))
                if not case_vec:
                    scored.append((r, 0.0))
                    continue
                cv = np.array(case_vec)
                cn = np.linalg.norm(cv)
                sim = float(np.dot(query_vec, cv) / (qn * cn)) if qn > 0 and cn > 0 else 0.0
                scored.append((r, sim))
            return scored
        except Exception:
            logger.debug("语义检索失败，回退关键词", exc_info=True)
            return None

    @staticmethod
    def _keyword_score(query: str, terms: List[str], case: Dict) -> float:
        """简单关键词命中打分。"""
        if not terms:
            return 0.1
        blob = " ".join(
            str(case.get(k) or "")
            for k in ("case_name", "industry", "equipment_type", "technical_highlights",
                      "lessons_learned", "project_summary", "tags")
        ).lower()
        score = 0.0
        for t in terms:
            tl = t.lower()
            if tl in blob:
                score += 1.0
                # 命中 equipment_type 或 tags 权重更高
                if tl in (str(case.get("equipment_type") or "").lower()):
                    score += 1.5
        return score

    # ============= 报价区间聚合 =============

    def quote_range(
        self,
        industry: Optional[str] = None,
        equipment_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        从历史报价聚合同类设备的报价/毛利区间。

        关联链：projects(customer_id) → customers → opportunities → quotes → quote_versions
        过滤：total_price > 0；毛利落在 [-50%, 80%] 区间（剔除脏数据）
        """
        sql = """
            SELECT qv.total_price, qv.cost_total, qv.gross_margin, qv.lead_time_days
            FROM quote_versions qv
            JOIN quotes q ON qv.quote_id = q.id
            JOIN opportunities o ON q.opportunity_id = o.id
            JOIN customers c ON o.customer_id = c.id
            LEFT JOIN projects p ON p.customer_id = c.id
            WHERE qv.total_price > 0
        """
        params: Dict[str, Any] = {}
        conditions = []
        if industry:
            # 项目行业或客户行业任一命中
            conditions.append("(p.industry = :industry OR c.industry = :industry)")
            params["industry"] = industry
        if equipment_type:
            conditions.append("p.product_category = :equipment_type")
            params["equipment_type"] = equipment_type
        if conditions:
            sql += " AND " + " AND ".join(conditions)

        rows = self.db.execute(text(sql), params).mappings().all()

        prices = [float(r["total_price"]) for r in rows if r["total_price"]]
        # 毛利过滤脏值
        margins = [
            float(r["gross_margin"])
            for r in rows
            if r["gross_margin"] is not None and -50 <= float(r["gross_margin"]) <= 80
        ]
        lead_times = [
            float(r["lead_time_days"])
            for r in rows
            if r["lead_time_days"] and float(r["lead_time_days"]) > 0
        ]

        if not prices:
            return {
                "sample_count": 0,
                "note": "无匹配历史报价数据",
            }

        prices.sort()
        margins.sort()
        lead_times.sort()

        return {
            "sample_count": len(prices),
            "price": {
                "min": prices[0],
                "p25": _percentile(prices, 25),
                "median": _percentile(prices, 50),
                "p75": _percentile(prices, 75),
                "max": prices[-1],
            },
            "margin_pct": {
                "min": margins[0] if margins else None,
                "median": _percentile(margins, 50) if margins else None,
                "max": margins[-1] if margins else None,
            },
            "lead_time_days": {
                "min": lead_times[0] if lead_times else None,
                "median": _percentile(lead_times, 50) if lead_times else None,
                "max": lead_times[-1] if lead_times else None,
            },
        }

    # ============= 成本对标（P4） =============

    def get_standard_costs(self, keyword: Optional[str] = None) -> List[Dict[str, Any]]:
        """查询标准件价格库（报价聚合 + 真实采购历史，两个来源都查）。"""
        sql = (
            "SELECT cost_code, cost_name, cost_category, specification, unit, "
            "standard_cost, cost_source, source_description FROM standard_costs "
            "WHERE is_active = 1 AND cost_source IN ('HISTORICAL_QUOTE', 'PURCHASE_HISTORY')"
        )
        params: Dict[str, Any] = {}
        if keyword:
            sql += " AND (cost_name LIKE :kw OR specification LIKE :kw)"
            params["kw"] = f"%{keyword}%"
        sql += " ORDER BY standard_cost DESC"
        rows = self.db.execute(text(sql), params).mappings().all()
        return [
            {
                "cost_code": r["cost_code"],
                "cost_name": r["cost_name"],
                "category": r["cost_category"],
                "spec": r["specification"],
                "unit": r["unit"],
                "standard_cost": float(r["standard_cost"]) if r["standard_cost"] else None,
                "source": r["source_description"],
            }
            for r in rows
        ]

    def benchmark_quote_items(
        self, items: List[Dict[str, Any]], tolerance_pct: float = 20.0
    ) -> Dict[str, Any]:
        """
        报价项级成本对标：把一组报价明细 vs 标准件库，逐项给偏差%。

        Args:
            items: 报价明细 [{"name":"电控柜与PLC程序","price":120000,"qty":1}, ...]
            tolerance_pct: 偏差阈值（默认 20%），超阈值的标记为 warning

        Returns:
            {
                "items": [{"name","price","std_cost","variance_pct","status","source"}],
                "summary": {"total","matched","warnings","avg_variance_pct"},
                "note": "..."
            }
        """
        if not items:
            return {"items": [], "summary": {}, "note": "无报价明细"}

        # 拉全量标准件库做匹配（量小，内存匹配）
        all_std = {s["cost_name"]: s for s in self.get_standard_costs()}

        result_items = []
        matched = 0
        warnings = 0
        variances = []

        for item in items:
            name = (item.get("name") or item.get("item_name") or "").strip()
            price = float(item.get("price") or item.get("unit_price") or 0)
            qty = float(item.get("qty") or 1)
            total = price * qty if price else 0

            # 模糊匹配标准件库（包含关系）
            std = None
            if name:
                for std_name, std_item in all_std.items():
                    if name in std_name or std_name in name:
                        std = std_item
                        break

            if std and std.get("standard_cost"):
                std_cost = float(std["standard_cost"])
                variance_pct = round((total - std_cost) / std_cost * 100, 1) if std_cost else 0
                status = "ok" if abs(variance_pct) <= tolerance_pct else "warning"
                matched += 1
                if status == "warning":
                    warnings += 1
                variances.append(abs(variance_pct))
                result_items.append({
                    "name": name,
                    "price": total,
                    "std_cost": std_cost,
                    "std_source": std.get("source", "")[:80],
                    "variance_pct": variance_pct,
                    "status": status,
                })
            else:
                result_items.append({
                    "name": name,
                    "price": total,
                    "std_cost": None,
                    "variance_pct": None,
                    "status": "no_match",
                })

        avg_var = round(sum(variances) / len(variances), 1) if variances else None
        return {
            "items": result_items,
            "summary": {
                "total": len(items),
                "matched": matched,
                "warnings": warnings,
                "avg_variance_pct": avg_var,
            },
            "note": (
                f"对标 {len(items)} 项报价，{matched} 项命中标准件库，"
                f"{warnings} 项偏差超 {tolerance_pct}%"
                + (f"，平均偏差 {avg_var}%" if avg_var is not None else "")
            ),
        }

    # ============= 方案模板检索 =============

    def _search_solution_templates(
        self,
        industry: Optional[str],
        equipment_type: Optional[str],
        top_k: int = 3,
    ) -> List[Dict[str, Any]]:
        sql = """
            SELECT id, name, code, industry, equipment_type, complexity_level,
                   typical_cost_range_min, typical_cost_range_max,
                   success_rate, usage_count, is_active
            FROM presale_solution_templates
            WHERE is_active = 1
        """
        params: Dict[str, Any] = {}
        conditions = []
        if industry:
            conditions.append("industry = :industry")
            params["industry"] = industry
        if equipment_type:
            conditions.append("equipment_type = :equipment_type")
            params["equipment_type"] = equipment_type
        if conditions:
            sql += " AND " + " AND ".join(conditions)
        sql += " LIMIT :top_k"
        params["top_k"] = top_k

        rows = self.db.execute(text(sql), params).mappings().all()
        return [
            {
                **dict(r),
                "typical_cost_range_min": float(r["typical_cost_range_min"])
                if r.get("typical_cost_range_min") else None,
                "typical_cost_range_max": float(r["typical_cost_range_max"])
                if r.get("typical_cost_range_max") else None,
                "success_rate": float(r["success_rate"]) if r.get("success_rate") else None,
            }
            for r in rows
        ]

    # ============= 标准模块（BOM 模板）检索 =============

    def _search_standard_modules(
        self,
        equipment_type: Optional[str],
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """标准模块库（机架/电控柜/视觉模组等），给 BOM 模板推荐用。"""
        sql = """
            SELECT module_name, category, description, typical_components,
                   ref_cost, source_count
            FROM ai_standard_modules
        """
        params: Dict[str, Any] = {}
        conditions = []
        # 按设备类型做弱关联（description LIKE）
        if equipment_type:
            kw = equipment_type.replace("测试", "").replace("设备", "")
            conditions.append("(description LIKE :kw OR category LIKE :kw)")
            params["kw"] = f"%{kw}%"
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY source_count DESC LIMIT :top_k"
        params["top_k"] = top_k

        rows = self.db.execute(text(sql), params).mappings().all()
        return [
            {
                "module_name": r["module_name"],
                "category": r["category"],
                "description": r["description"],
                "typical_components": _safe_json_loads(r.get("typical_components")),
                "ref_cost": float(r["ref_cost"]) if r.get("ref_cost") else None,
                "source_count": r["source_count"],
            }
            for r in rows
        ]

    # ============= 总结生成 =============

    @staticmethod
    def _build_summary(
        query: str,
        cases: List[Dict[str, Any]],
        quote_range: Dict[str, Any],
        templates: List[Dict[str, Any]],
    ) -> str:
        """生成一句话总结，方便智能体/前端直接展示。"""
        parts = [f"针对「{query}」"]
        if cases:
            parts.append(f"找到 {len(cases)} 个相似历史案例")
        if quote_range.get("sample_count"):
            pr = quote_range.get("price", {})
            mr = quote_range.get("margin_pct", {})
            parts.append(
                f"历史报价 {pr.get('min')}~{pr.get('max')} 元"
                f"（中位 {pr.get('median')}，毛利中位 {mr.get('median')}%）"
            )
        if templates:
            parts.append(f"推荐 {len(templates)} 个方案模板")
        return "，".join(parts) if len(parts) > 1 else parts[0]


# ============= 工具函数 =============

def _percentile(sorted_list: List[float], pct: float) -> Optional[float]:
    """计算分位数（输入需已排序）。"""
    if not sorted_list:
        return None
    k = (len(sorted_list) - 1) * (pct / 100.0)
    f = int(k)
    c = min(f + 1, len(sorted_list) - 1)
    if f == c:
        return sorted_list[f]
    return sorted_list[f] + (sorted_list[c] - sorted_list[f]) * (k - f)


def _safe_json_loads(val) -> Any:
    """安全解析 JSON 字段，失败返回原值。"""
    if val is None:
        return None
    if isinstance(val, (list, dict)):
        return val
    try:
        import json
        return json.loads(val)
    except Exception:
        return val


def _parse_embedding(val) -> Optional[list]:
    """从 BLOB/JSON 解析 embedding 向量，失败返回 None。"""
    if val is None:
        return None
    if isinstance(val, list):
        return val
    try:
        import json
        if isinstance(val, (bytes, bytearray)):
            val = val.decode("utf-8")
        emb = json.loads(val)
        return emb if isinstance(emb, list) and emb else None
    except Exception:
        return None
