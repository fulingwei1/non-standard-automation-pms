#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
导入金凯博自动化本体竞争对手（来自《竞争对手资料》目录60+文件 + 研报分析）

这些是金凯博自动化（ICT/FCT/涂覆/点胶/整线集成）的直接对手，
和费思泰克（电源/负载）的对手不同。

按业务领域分5类：
  ICT/FCT测试设备 | 半导体检测 | 锂电测试 | 自动化集成 | 仪器
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "app.db"

# 自动化本体竞争对手情报（基于研报+文件名+行业知识）
AUTOMATION_COMPETITORS = [
    # ===== ICT/FCT测试设备（金凯博最直接的对手）=====
    {
        "name": "博杰股份",
        "short_name": "博杰",
        "competitor_type": "ICT/FCT测试设备厂商（A股上市，营收8亿+）",
        "strengths": "自动化测试+组装并重；毛利率50%+经营效率高；5G射频声学风口；客户含苹果链",
        "weaknesses": "偏3C消费电子，新能源/白电覆盖弱；标准化产品为主定制少；单价高",
        "good_at": "ICT/FCT测试、射频测试、声学测试、3C消费电子自动化",
        "price_level": "高",
        "delivery_time": "60-90天",
        "counter_strategy": "【打行业覆盖+定制牌】博杰强在3C标准化测试，但白电/新能源覆盖弱。强调金凯博在白电（海尔/美的/长虹）和新能源（比亚迪/吉利威睿）的客户基础。博杰偏标准化产品，金凯博可深度定制整线方案。",
    },
    {
        "name": "华峰测控",
        "short_name": "华峰",
        "competitor_type": "半导体测试设备龙头（A股上市，模拟ATE龙头）",
        "strengths": "国内半导体测试机龙头；进口替代；产品性能国内领先；客户资源优秀；技术积累深",
        "weaknesses": "专注半导体测试（模拟/SoC），不做整线；非ICT/FCT领域；单价极高；交期长",
        "good_at": "半导体测试机（模拟/混合信号/SoC）、晶圆级测试",
        "price_level": "高",
        "delivery_time": "90天+",
        "counter_strategy": "【打领域差异牌】华峰是半导体测试龙头，但金凯博做的是PCBA级ICT/FCT和整线，领域不同。客户做PCBA测试选金凯博（性价比+整线能力），做芯片测试才选华峰。不在同一赛道正面竞争。",
    },
    {
        "name": "鑫信腾",
        "short_name": "信腾",
        "competitor_type": "汽车电子自动化测试设备厂商",
        "strengths": "汽车电子自动化经验；有产品介绍视频资料；专注汽车电子领域",
        "weaknesses": "业务范围窄（仅汽车电子）；规模小知名度低；整线集成能力待验证",
        "good_at": "汽车电子PCBA测试、自动化测试设备",
        "price_level": "中",
        "delivery_time": "未知",
        "counter_strategy": "【打规模+全行业牌】鑫信腾只做汽车电子，金凯博覆盖3C/白电/新能源/汽车电子多行业。汽车电子领域我们有比亚迪案例，正面竞争。强调多行业经验带来的方案成熟度。",
    },
    # ===== 锂电/新能源测试（金凯博新能源业务的对）=====
    {
        "name": "星云股份",
        "short_name": "星云",
        "competitor_type": "锂电池检测设备厂商（A股上市，中高端定位）",
        "strengths": "锂电检测深耕多年；客户含宁德时代/比亚迪/国轩高科；锂电池组自动化组装线；中高端定位",
        "weaknesses": "专注锂电检测，3C/白电不覆盖；组装线能力一般；测试设备单价偏高",
        "good_at": "锂电池检测系统、电池组自动化组装、储能测试",
        "price_level": "高",
        "delivery_time": "60-90天",
        "counter_strategy": "【打多行业+性价比牌】星云只在锂电领域强，金凯博覆盖3C/白电/新能源全覆盖。锂电测试正面竞争：强调金凯博比亚迪/TTI/中航锂电/吉利威睿案例，且整线能力（含ICT/FCT/涂覆/点胶）比星云的单一检测更全。",
    },
    {
        "name": "杭可科技",
        "short_name": "杭可",
        "competitor_type": "锂电后道设备龙头（A股上市，充放电设备专家）",
        "strengths": "锂电后道充放电设备龙头；在手订单充足；优质客户；工艺优势；产销率90%+",
        "weaknesses": "只做锂电后道（充放电/化成），不做前道测试；不做3C/白电；非ICT/FCT领域",
        "good_at": "锂电池充放电设备、化成分容设备、锂电后道整线",
        "price_level": "高",
        "delivery_time": "90-120天",
        "counter_strategy": "【打领域差异牌】杭可是锂电后道（化成/充放电）龙头，金凯博做的是电池包EOL/充放电测试线。在充放电领域正面竞争时强调金凯博的整线集成能力（含信息化对接/AGV回流），不只是单机设备。",
    },
    {
        "name": "恒翼能",
        "short_name": "恒翼能",
        "competitor_type": "锂电测试设备厂商",
        "strengths": "锂电测试设备系列完整；有产品系列介绍资料",
        "weaknesses": "规模较小；知名度低于星云/杭可；非上市；资金实力有限",
        "good_at": "锂电池测试设备",
        "price_level": "中",
        "delivery_time": "未知",
        "counter_strategy": "【打规模+案例牌】恒翼能规模小案例少。强调金凯博比亚迪/吉利威睿等头部客户案例+上市公司资金实力+售后保障。锂电测试领域我们是更有保障的选择。",
    },
    # ===== 自动化集成商（整线项目对手）=====
    {
        "name": "先惠技术",
        "short_name": "先惠",
        "competitor_type": "智能自动化集成商（A股上市，模组/PACK产线）",
        "strengths": "乘智能自动化春风；龙头效应；模组/PACK自动化产线；上市公司",
        "weaknesses": "偏锂电模组/PACK组装，不做PCBA测试；测试能力弱；3C/白电不覆盖",
        "good_at": "锂电池模组/PACK自动化组装线、智能产线集成",
        "price_level": "高",
        "delivery_time": "90-120天",
        "counter_strategy": "【打测试能力牌】先惠强在组装线集成但测试能力弱。整线项目里测试段（ICT/FCT）是我们的强项。可打'测试+组装全集成'vs先惠的'只组装不测试'。",
    },
    {
        "name": "赢合科技",
        "short_name": "赢合",
        "competitor_type": "锂电自动化平台型公司（A股上市，前中后道全覆盖）",
        "strengths": "锂电前中后道全覆盖；自动化平台型公司；规模大；优质企业",
        "weaknesses": "只做锂电，不覆盖3C/白电/汽车电子；产品线太宽导致专注度不够；近年战略调整",
        "good_at": "锂电池全段自动化产线（涂布/卷绕/叠片/组装/检测）",
        "price_level": "高",
        "delivery_time": "120天+",
        "counter_strategy": "【打专注度+多行业牌】赢合什么都做但都不够精。金凯博专注测试设备和DIP线，在这个细分领域更专业。多行业覆盖（3C/白电/新能源）vs 赢合的单一锂电。",
    },
    {
        "name": "沃镭智能",
        "short_name": "沃镭",
        "competitor_type": "智能制造自动化装备商（有招股说明书）",
        "strengths": "智能制造自动化方案；正在筹备上市",
        "weaknesses": "规模偏小；品牌知名度有限；具体产品线不明",
        "good_at": "智能制造自动化装备",
        "price_level": "中",
        "delivery_time": "未知",
        "counter_strategy": "【打成熟度牌】沃镭还在成长期。强调金凯博多年行业经验+成熟产品线+头部客户案例。客户选成熟供应商更安心。",
    },
    # ===== 仪器/测量（间接对手）=====
    {
        "name": "精测电子",
        "short_name": "精测",
        "competitor_type": "泛半导体检测设备龙头（A股上市，AOI/检测）",
        "strengths": "检测产品线最齐全；研发投入14%收入占比；毛利率47%；AOI光学检测龙头；布局半导体+新能源",
        "weaknesses": "偏面板/半导体检测，不做PCBA功能测试；不做整线集成；单价高",
        "good_at": "AOI光学检测、面板检测、半导体检测、新能源检测",
        "price_level": "高",
        "delivery_time": "60-90天",
        "counter_strategy": "【打领域差异+整线牌】精测强在AOI光学检测（面板/半导体），金凯博做ICT/FCT功能测试+整线。AOI段可合作，功能测试段我们有优势。整线集成能力精测不具备。",
    },
    {
        "name": "华兴源创",
        "short_name": "华兴",
        "competitor_type": "面板/半导体检测设备商（A股上市，进口替代）",
        "strengths": "面板检测+半导体检测；进口替代；业务多点开花",
        "weaknesses": "专注面板/半导体，不做PCBA测试/整线；非3C/白电/新能源领域",
        "good_at": "面板检测、半导体检测、进口替代",
        "price_level": "高",
        "delivery_time": "90天+",
        "counter_strategy": "【打领域差异牌】华兴做面板/半导体检测，和金凯博PCBA测试/整线不在同一赛道。遇到客户同时有面板和PCBA需求时可互补，但PCBA测试和整线是我们的强项。",
    },
    {
        "name": "燕麦科技",
        "short_name": "燕麦",
        "competitor_type": "自动化测试设备厂商",
        "strengths": "专注自动化测试；有资料整理",
        "weaknesses": "规模小；产品线窄；知名度低；具体优势不明显",
        "good_at": "自动化测试设备",
        "price_level": "中",
        "delivery_time": "未知",
        "counter_strategy": "【打规模+产品线牌】燕麦规模小产品线窄。强调金凯博KC2700/KC2900完整产品系列+多行业案例+整线集成能力。",
    },
    {
        "name": "北京中科泛华",
        "short_name": "泛华",
        "competitor_type": "测控技术公司（NXI测控系统）",
        "strengths": "NXI测控系统技术；有测控系统介绍资料",
        "weaknesses": "偏测控系统/仪器，非整线集成；规模小；市场覆盖窄",
        "good_at": "NXI测控系统、测控仪器",
        "price_level": "中",
        "delivery_time": "未知",
        "counter_strategy": "【打整线集成牌】泛华做测控系统/仪器，不做整线。金凯博从测试设备到整线集成全覆盖，客户要的是交钥匙方案不是单机。",
    },
    {
        "name": "湖北德普电气",
        "short_name": "德普",
        "competitor_type": "电气测试设备厂商",
        "strengths": "有产品BP资料",
        "weaknesses": "规模小；产品线不明；知名度低",
        "good_at": "电气测试设备",
        "price_level": "中",
        "delivery_time": "未知",
        "counter_strategy": "【打规模+品牌牌】规模小品牌弱。强调金凯博行业地位+客户基础+产品成熟度。",
    },
    {
        "name": "浙江仕能",
        "short_name": "仕能",
        "competitor_type": "自动化装备方案商",
        "strengths": "有2022和2025两版公司简介（持续经营）",
        "weaknesses": "规模偏小；具体产品线不明",
        "good_at": "自动化装备",
        "price_level": "中",
        "delivery_time": "未知",
        "counter_strategy": "【打成熟度牌】强调金凯博多年经验+成熟产品+上市公司背景。",
    },
    {
        "name": "鼎泰佳创",
        "short_name": "鼎泰",
        "competitor_type": "自动化设备厂商",
        "strengths": "有公司简介资料",
        "weaknesses": "规模小；知名度低；产品线不明",
        "good_at": "自动化设备",
        "price_level": "中",
        "delivery_time": "未知",
        "counter_strategy": "【打规模牌】小厂对手，强调金凯博规模优势+案例+售后保障。",
    },
]


def main():
    conn = sqlite3.connect(DB_PATH)

    # 不清空（保留费思泰克的14个电源对手），只追加自动化对手
    existing = {r[0] for r in conn.execute("SELECT name FROM competitors")}
    inserted = 0
    for c in AUTOMATION_COMPETITORS:
        if c["name"] in existing:
            # 更新已有
            conn.execute(
                """UPDATE competitors SET competitor_type=?, strengths=?, weaknesses=?,
                good_at=?, price_level=?, delivery_time=?, counter_strategy=?
                WHERE name=?""",
                (c["competitor_type"], c["strengths"], c["weaknesses"],
                 c["good_at"], c["price_level"], c["delivery_time"],
                 c["counter_strategy"], c["name"]),
            )
            print(f"  更新: {c['name']}")
        else:
            conn.execute(
                """INSERT INTO competitors
                (name, short_name, competitor_type, strengths, weaknesses,
                 good_at, price_level, delivery_time, counter_strategy,
                 encounter_count, is_active, created_at, updated_at)
                VALUES (?,?,?,?,?,?,?,?,?, 0, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)""",
                (c["name"], c.get("short_name"), c["competitor_type"],
                 c["strengths"], c["weaknesses"], c["good_at"],
                 c["price_level"], c["delivery_time"], c["counter_strategy"]),
            )
            inserted += 1
            print(f"  新增: {c['name']}")

    conn.commit()
    total = conn.execute("SELECT COUNT(*) FROM competitors").fetchone()[0]
    print(f"\n完成：新增 {inserted} 个自动化对手，competitors 表共 {total} 条")
    conn.close()


if __name__ == "__main__":
    main()
