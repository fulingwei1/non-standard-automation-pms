#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
补充白色家电 + 汽车电子两个重点行业的竞争对手。

来源：网络搜索（金凯博同赛道公司）+ 行业知识
金凯博官网确认：kingcableate.com 服务新能源/汽车电子/白色家电/功率半导体
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "app.db"

FOCUS_COMPETITORS = [
    # ===== 白色家电PCBA测试（金凯博重点行业，之前空白）=====
    {
        "name": "派捷智能(PTI)",
        "competitor_type": "白色家电PCBA测试设备厂商（深圳）",
        "strengths": "专注家电电子功能模块测试；有电蚊香/空调电机控制器ICT+FCT整线方案；深耕家电行业",
        "weaknesses": "仅家电单一行业；规模小；不覆盖新能源/汽车电子；整线集成能力有限",
        "good_at": "白色家电PCBA测试、家电控制器ICT/FCT、电蚊香/空调电机控制器",
        "price_level": "中",
        "delivery_time": "45-60天",
        "counter_strategy": "【打多行业+规模牌】派捷只在白电领域，金凯博覆盖白电+新能源+汽车电子多行业。白电正面竞争：强调金凯博海尔/美的/长虹客户案例+整线集成能力（含涂覆/点胶/分板，派捷做不了）。多行业经验带来方案更成熟。",
    },
    {
        "name": "协立商(Kyoritsu)",
        "competitor_type": "ICT/FCT治具与设备厂商（深圳，日资背景）",
        "strengths": "ICT/FCT治具专业能力强；日资品控体系；PCBA测试经验",
        "weaknesses": "偏治具/单机，不做整线集成；规模小；行业覆盖窄；价格偏高",
        "good_at": "ICT/FCT治具、PCB/PCBA测试夹具",
        "price_level": "中高",
        "delivery_time": "未知",
        "counter_strategy": "【打整线+性价比牌】协立商做治具/单机，金凯博做整线交钥匙。客户要的是整线方案不是治具。强调金凯博从治具到整线全覆盖+价格更优。",
    },
    # ===== 汽车电子测试（金凯博重点行业）=====
    {
        "name": "金蚂蚁国创(NIL)",
        "competitor_type": "汽车电子ECU测试设备厂商",
        "strengths": "ECU在线生产测试全覆盖（ICT/FCT/EOL/软件注入/老化）；客户含一汽/东风/陕汽/潍柴；商用车领域强",
        "weaknesses": "偏商用车ECU，乘用车新能源覆盖弱；不做白电/3C；整线集成经验少",
        "good_at": "ECU测试、发动机ECU/BMS/VCU/MCU测试、T-BOX FCT、商用车电子",
        "price_level": "中高",
        "delivery_time": "60-90天",
        "counter_strategy": "【打乘用车新能源+整线牌】NIL强在商用车ECU，金凯博在乘用车新能源（比亚迪/吉利威睿）更强。NIL做单机测试，金凯博做整线集成。强调新能源BMS/电驱测试案例+整线交付能力。",
    },
    {
        "name": "明波通信",
        "competitor_type": "汽车电子FT/ICT自动化测试厂商（新三板）",
        "strengths": "FT/ICT自动化测试设备；新三板上市有资金；汽车电子+工业自动化双赛道",
        "weaknesses": "规模偏小；偏通信测试背景；整线能力待验证；品牌知名度低",
        "good_at": "FT/ICT自动化测试、汽车电子、工业自动化",
        "price_level": "中",
        "delivery_time": "未知",
        "counter_strategy": "【打规模+案例牌】明波规模小品牌弱。强调金凯博比亚迪/吉利/长城等头部车企案例+完整产品线（KC2700/KC2900系列）+整线集成。",
    },
    {
        "name": "特创科技",
        "competitor_type": "FCT/ICT治具及自动化设备厂商（江苏）",
        "strengths": "FCT/ICT治具研发加工装配一体；区域性客户基础",
        "weaknesses": "偏治具加工，不做系统级方案；规模小；无整线能力；技术深度有限",
        "good_at": "FCT/ICT治具、自动化设备方案",
        "price_level": "低中",
        "delivery_time": "45-60天",
        "counter_strategy": "【打系统级+整线牌】特创做治具加工，金凯博做系统级测试方案+整线。强调金凯博自主研发测试系统（非治具组装）+KC产品系列成熟度。",
    },
    {
        "name": "SPEA",
        "competitor_type": "半导体/PCBA测试设备外资品牌（意大利）",
        "strengths": "国际知名品牌；汽车电子测试经验丰富（Bosch/大陆/法雷奥客户）；技术领先",
        "weaknesses": "外资品牌价格昂贵（2-3倍）；交期长（3-6个月）；服务响应慢；国产替代趋势下市场份额下降",
        "good_at": "半导体测试、汽车电子PCBA测试、ICT/FCT高端机型",
        "price_level": "高",
        "delivery_time": "90-180天",
        "counter_strategy": "【打国产替代+性价比+服务牌】SPEA是高端外资但价格贵2-3倍、交期3-6个月。强调金凯博性能对标SPEA中端机型、价格低40-50%、交期快一倍、本土7x24服务。国产替代趋势是最大机会。",
    },
    {
        "name": "TRI(德凯)",
        "competitor_type": "ICT/FCT测试设备外资品牌（台湾）",
        "strengths": "ICT+FCT一体化方案；多核心并行测试；长生命周期治具；自动校正自诊断；Bosch/大陆客户",
        "weaknesses": "台资品牌价格偏高；交期偏长；大陆服务团队规模有限；对中小客户关注度低",
        "good_at": "ICT/FCT一体化测试、汽车电子PCBA、长生命周期治具",
        "price_level": "中高",
        "delivery_time": "60-90天",
        "counter_strategy": "【打性价比+定制+服务牌】TRI技术成熟但价格高、对中小客户关注度低。强调金凯博对每个客户的定制化服务+价格优势+快速响应。TRI的标准化产品 vs 金凯博的定制方案。",
    },
    # ===== 国际对标（金凯博自动化整体对标）=====
    {
        "name": "雅马哈发动机",
        "competitor_type": "自动化贴片/检测设备巨头（日资）",
        "strengths": "全球品牌；SMT全 line 设备；技术领先；资金雄厚",
        "weaknesses": "价格极高；交期长；定制化能力弱（标准化产品）；不专注PCBA功能测试",
        "good_at": "SMD贴片、AOI/SPI检测、印刷机",
        "price_level": "高",
        "delivery_time": "90-180天",
        "counter_strategy": "【打专注度+性价比牌】雅马哈什么都做但PCBA功能测试不是强项。金凯博专注ICT/FCT功能测试，在这个细分更专业。价格只有雅马哈的1/3-1/2。",
    },
]


def main():
    conn = sqlite3.connect(DB_PATH)
    existing = {r[0] for r in conn.execute("SELECT name FROM competitors")}
    inserted = 0
    for c in FOCUS_COMPETITORS:
        if c["name"] in existing:
            print(f"  跳过(已存在): {c['name']}")
            continue
        conn.execute(
            """INSERT INTO competitors
            (name, competitor_type, strengths, weaknesses, good_at,
             price_level, delivery_time, counter_strategy,
             encounter_count, is_active, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?, 0, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)""",
            (c["name"], c["competitor_type"], c["strengths"], c["weaknesses"],
             c["good_at"], c["price_level"], c["delivery_time"], c["counter_strategy"]),
        )
        inserted += 1
        print(f"  新增: {c['name']} ({c['competitor_type'][:25]})")

    conn.commit()
    total = conn.execute("SELECT COUNT(*) FROM competitors").fetchone()[0]
    # 按行业统计
    print(f"\n完成：新增 {inserted} 个，competitors 表共 {total} 条")
    print("\n行业分布:")
    for kw, label in [("白电", "白色家电"), ("汽车", "汽车电子"), ("电源", "电源/负载"), ("半导体", "半导体"), ("面板", "面板")]:
        cnt = conn.execute("SELECT COUNT(*) FROM competitors WHERE good_at LIKE ? OR competitor_type LIKE ?", (f"%{kw}%", f"%{kw}%")).fetchone()[0]
        if cnt: print(f"  {label}: {cnt} 个")
    conn.close()


if __name__ == "__main__":
    main()
