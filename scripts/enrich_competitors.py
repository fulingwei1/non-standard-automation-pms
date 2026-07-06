#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
深度研判 14 个竞争对手，补充应对策略和擅长领域。

基于金凯博产品规划分析.xls 的原始数据 + 行业背景，为每个对手写：
  - good_at: 擅长领域（让检索精准）
  - counter_strategy: 具体应对策略（怎么打它，让 AI 引用）

分四档策略：
  第一梯队外资（CHROMA/Keysight）：打"国产替代+性价比+服务响应"
  第二梯队外资（EA/AMETEK/TDK）：打"交期+本地服务+定制灵活"
  第一梯队内资（科威尔/AINUO/IETCH）：打"产品稳定性+技术排他性+全产品线"
  第三梯队（斯康达/NGI/KIKUSUI）：不必重点打，客户自然淘汰
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "app.db"

# 深度研判数据
COMPETITOR_INTEL = {
    "CHROMA": {
        "good_at": "全系电源/负载/系统，新能源电池测试、车载充电机、光伏储能",
        "counter_strategy": (
            "【打国产替代牌】CHROMA 受华为体系影响存在供应链风险，客户担心断供。"
            "强调费思泰克完全自主可控，性能指标对标 CHROMA 62000 系列，"
            "价格低 30-40%，交期快 8-12 周。"
            "重点客户：新能源车企在国产化要求下倾向选内资品牌。"
        ),
    },
    "Keysight": {
        "good_at": "高端精密测量、研发实验室、计量校准",
        "counter_strategy": (
            "【打性价比+贴牌风险牌】Keysight 电源产品多是贴牌（实际是 TDK-Lambda/EA 代工），"
            "价格虚高 2-3 倍。强调费思泰克自有研发、出厂价直销。"
            "对研发客户：Keysight 品牌溢价不等于生产线必须。"
            "对产线客户：产线设备看重的是稳定性和成本，不是品牌光环。"
        ),
    },
    "EA": {
        "good_at": "宽量程高精度直流电源、实验室级、半导体测试",
        "counter_strategy": (
            "【打交期牌】EA 德国进口交货周期 16-24 周，远长于费思泰克 6-10 周。"
            "对交期敏感客户（新能源扩产期）这是致命弱点。"
            "EA 售后需返厂德国，费思泰克 48 小时到场。"
        ),
    },
    "AMETEK": {
        "good_at": "航空航天电源、可编程交流电源、功率分析仪",
        "counter_strategy": (
            "【打服务效率牌】AMETEK 美国品牌中国区服务团队小，响应慢。"
            "目前客户多在找替代品牌。强调费思泰克本土团队 7x24 响应。"
            "AMETEK 强项在交流电源和功率分析仪，直流源/载领域我们可正面竞争。"
        ),
    },
    "TDK": {
        "good_at": "高功率密度电源、母公司配套（TDK-Lambda 体系）、医疗电源",
        "counter_strategy": (
            "【打销售+服务牌】TDK 技术过硬但中国区销售能力弱、服务速度慢，"
            "很多客户'想买但找不到人'。强调费思泰克销售覆盖+技术支持前置。"
            "TDK 强在标准电源，定制化能力弱，测试系统级需求我们优势大。"
        ),
    },
    "KIKUSUI": {
        "good_at": "传统精密电源/负载、日本市场、电子元器件老化测试",
        "counter_strategy": (
            "【打价格牌】KIKUSUI 日本进口价格昂贵（同类高 50-100%），"
            "服务效率低（返厂日本）。现在市场份额已被国产替代蚕食。"
            "客户选它多为历史惯性，新项目我们正面竞争胜算大。"
        ),
    },
    "IETCH": {
        "good_at": "全产品线快速跟随、新能源电池测试、代理体系",
        "counter_strategy": (
            "【打可靠性牌】IETCH（艾德克斯）产品跟随速度快、营销猛，"
            "但可靠性一般、服务水平一般（返修率高）。"
            "强调费思泰克 MTBF（平均无故障时间）数据、客户长期使用案例。"
            "IETCH 容易陷入参数战，我们强调实际产线稳定性而非实验室指标。"
        ),
    },
    "Faithtech": {
        "good_at": "电源+负载全产品线、国产替代、新能源三电测试",
        "counter_strategy": (
            "【自身定位】费思泰克就是我方品牌。优势：产品线完整、跟随快、指标精、服务快。"
            "需提升：稳定性验证、技术排他性（独有功能避免同质化价格战）。"
            "策略：对标 CHROMA/Keysight 性能，定价低于外资 30%，高于低端国产，"
            "走'高性能国产替代'路线。"
        ),
    },
    "科威尔": {
        "good_at": "双向直流电源、燃料电池/电解槽测试、大功率电力测试",
        "counter_strategy": (
            "【打全产品线牌】科威尔强项窄（双向电源+三电测试），"
            "缺少中小功率产品、行业覆盖窄（聚焦氢能/燃料电池）。"
            "强调费思泰克全功率段覆盖（从实验室级到产线级）、全行业覆盖。"
            "科威尔已上市估值高，客户议价时'你是上市公司不差钱'可压价。"
        ),
    },
    "北京大华": {
        "good_at": "传统直流电源、军工/教育/科研、稳压电源",
        "counter_strategy": (
            "【打南方市场+负载牌】北京大华强在北方军工教育市场，"
            "但'源前载弱'（电源强负载弱）、产业市场弱、'北强南弱'。"
            "南方工业客户是我们的地盘。强调费思泰克源+载+系统一体化，"
            "大华做不了测试系统级方案。"
        ),
    },
    "斯康达": {
        "good_at": "低价电源、简单集成",
        "counter_strategy": (
            "【不必重点打】低端品牌，性能/可靠性/研发投入都差。"
            "客户选它纯为低价。我们强调'一分钱一分货'：产线停机 1 小时损失远超价差。"
            "可用三档报价里的经济型挡它，标准型/高端型不与其纠缠。"
        ),
    },
    "AINUO": {
        "good_at": "性价比电源、集成方案、电气安全测试",
        "counter_strategy": (
            "【打技术指标牌】AINUO（安博诺/艾诺）价格有竞争力有集成能力，"
            "但核心技术指标较差（精度/动态响应/纹波）。"
            "强调费思泰克指标实测对比数据（特别是动态响应和纹波，产线测试关键指标）。"
            "AINUO 强在安规测试（耐压/绝缘/接地），我们在电源/负载领域性能更优。"
        ),
    },
    "NGI": {
        "good_at": "BMS仿真测试、大功率直流负载、电池模拟器",
        "counter_strategy": (
            "【打质量+服务牌】NGI（恩智/星云）BMS 仿真有特点、大功率负载低价，"
            "但质量不可靠、服务响应慢、产品换代慢。"
            "BMS 测试领域正面竞争：强调费思泰克 BMS 测试案例（比亚迪等）、"
            "长期稳定性数据、4小时响应承诺。"
        ),
    },
    "上海航裕": {
        "good_at": "未知（数据缺失，需补充调研）",
        "counter_strategy": "数据不足，需销售团队补充该对手信息后再制定策略。",
    },
}


def main():
    conn = sqlite3.connect(DB_PATH)
    updated = 0
    for name, intel in COMPETITOR_INTEL.items():
        result = conn.execute(
            "UPDATE competitors SET good_at=?, counter_strategy=? WHERE name=?",
            (intel["good_at"], intel["counter_strategy"], name),
        )
        if result.rowcount > 0:
            updated += 1
            print(f"✓ {name}: good_at + counter_strategy 已更新")
        else:
            print(f"✗ {name}: 未找到（表里没这个名字）")

    conn.commit()
    print(f"\n完成：更新 {updated}/{len(COMPETITOR_INTEL)} 个对手的深度研判")

    # 验证
    print("\n=== 抽样验证 ===")
    for row in conn.execute(
        "SELECT name, good_at, substr(counter_strategy,1,80) FROM competitors WHERE name IN ('CHROMA','Keysight','科威尔','NGI')"
    ):
        print(f"\n【{row[0]}】")
        print(f"  擅长: {row[1]}")
        print(f"  策略: {row[2]}...")

    conn.close()


if __name__ == "__main__":
    main()
