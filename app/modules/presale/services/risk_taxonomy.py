# -*- coding: utf-8 -*-
"""
金凯博售前风险标签库

来自《非标报价相似项目检索 MVP》风险标签库 sheet，19 个标准标签分 5 类。
让 AI 用这套统一标签体系，而不是随意编造风险分类——这样统计和检索才能对齐。
"""

# 风险标签库（类型 → [标签列表]，每个标签含说明和典型影响）
RISK_TAXONOMY = {
    "技术风险": [
        {"tag": "视觉难度高", "desc": "检测精度、光源、算法或误判率要求高", "impact": "调试周期长、相机/光源增加"},
        {"tag": "节拍过紧", "desc": "客户要求节拍接近设备能力边界", "impact": "机构复杂、调试风险高"},
        {"tag": "工件来料不稳定", "desc": "尺寸、表面、位置一致性差", "impact": "夹具和视觉方案反复修改"},
        {"tag": "夹具变更多", "desc": "产品型号多或定位基准不稳定", "impact": "加工件和调试成本上升"},
        {"tag": "客户接口复杂", "desc": "MES、扫码、数据库、上位机接口多", "impact": "软件调试周期增加"},
    ],
    "成本风险": [
        {"tag": "非标加工件多", "desc": "机加件数量多、精度高或交期紧", "impact": "加工成本和延期风险"},
        {"tag": "外购件价格波动", "desc": "机器人、相机、传感器、伺服等价格不稳定", "impact": "成本超预算"},
        {"tag": "现场调试时间长", "desc": "客户现场条件复杂或验收标准高", "impact": "人工和差旅成本增加"},
        {"tag": "售后返工", "desc": "验收后仍需整改或新增功能", "impact": "售后追加成本"},
    ],
    "需求风险": [
        {"tag": "需求描述不完整", "desc": "客户资料缺少节拍、工件、验收标准等", "impact": "报价漏项"},
        {"tag": "验收标准模糊", "desc": "未明确良率、精度、节拍、稳定性", "impact": "后期扯皮和返工"},
        {"tag": "客户样品不足", "desc": "没有足够样品做验证", "impact": "方案判断失真"},
        {"tag": "方案边界不清", "desc": "上下游接口、设备范围不明确", "impact": "范围蔓延"},
    ],
    "商务风险": [
        {"tag": "压价严重", "desc": "客户目标价明显低于合理成本", "impact": "毛利不足"},
        {"tag": "付款条件差", "desc": "回款周期长或尾款比例高", "impact": "现金流压力"},
        {"tag": "交期过紧", "desc": "客户要求交期短于正常周期", "impact": "加急采购和加班成本"},
        {"tag": "客户变更多", "desc": "客户历史变更频繁", "impact": "执行成本失控"},
    ],
    "复用风险": [
        {"tag": "历史项目年份太久", "desc": "老项目价格和供应链已变化", "impact": "参考价失真"},
        {"tag": "技术路线过时", "desc": "参考项目的技术方案已被淘汰", "impact": "参考价值下降"},
        {"tag": "供应链已变化", "desc": "关键供应商停产或涨价", "impact": "成本和交期风险"},
    ],
}


def get_all_tags() -> list:
    """返回所有标签的扁平列表（供 AI 选择）。"""
    result = []
    for rtype, tags in RISK_TAXONOMY.items():
        for t in tags:
            result.append({"type": rtype, "tag": t["tag"], "desc": t["desc"], "impact": t["impact"]})
    return result


def get_tags_for_prompt() -> str:
    """生成给 AI prompt 用的标签说明文本。"""
    lines = ["必须从以下标准风险标签库里选择标签（不要自创）："]
    for rtype, tags in RISK_TAXONOMY.items():
        lines.append(f"\n【{rtype}】")
        for t in tags:
            lines.append(f"- {t['tag']}：{t['desc']}（影响：{t['impact']}）")
    return "\n".join(lines)


# 相似度权重（来自相似度规则 sheet）
SIMILARITY_WEIGHTS = {
    "equipment_type": 25,   # 设备类型
    "process_flow": 20,     # 工艺流程
    "workpiece_type": 15,   # 工件类型
    "cycle_time": 15,       # 节拍/产能
    "automation_level": 10, # 自动化程度
    "industry": 10,         # 行业/客户类型
    "semantic": 5,          # 文档语义相似
}
