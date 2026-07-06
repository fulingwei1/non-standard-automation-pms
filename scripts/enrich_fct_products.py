#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
补全 KC2700 FCT 全系列的详细参数。

从产品名解析：在线/离线 + 双轨/多轨 + 双工位/多工位 + 显示/SPI
推断：自动化程度/工位数/产能UPH/典型节拍/适用场景/价格区间
"""
import re
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "app.db"

# KC2700 系列参数矩阵（基于产品命名规则推断 + 行业标准）
# 命名规则：[离线/在线式][显示][双轨/多轨]双工位/多工位FCT[+显示][+3D SPI]
FCT_MATRIX = {
    # 离线双工位（入门级，实验室/小批量）
    "KC2701": {"auto": "半自动", "stations": 2, "rails": 1, "uph": "100-300", "ct": 30, "price": "15-25万", "scene": "实验室验证/小批量产线", "desc": "基础款双工位FCT，手动上下料，适合产品验证和小批量生产"},
    "KC2702": {"auto": "半自动", "stations": 2, "rails": 1, "uph": "100-300", "ct": 30, "price": "18-28万", "scene": "需要测试数据可视化的场景", "desc": "带显示屏，可实时查看测试波形和数据，方便调试"},
    "KC2703": {"auto": "半自动", "stations": 2, "rails": 1, "uph": "100-300", "ct": 30, "price": "25-35万", "scene": "需要外观检测+功能测试的组合", "desc": "集成3D SPI，功能测试的同时做焊膏检测，减少工序"},

    # 离线双轨双工位（中端，中小批量）
    "KC2704": {"auto": "半自动", "stations": 2, "rails": 2, "uph": "200-500", "ct": 25, "price": "25-35万", "scene": "中等批量产线", "desc": "双轨设计，左右轨可同时测不同产品，换产不停机"},
    "KC2705": {"auto": "半自动", "stations": 2, "rails": 2, "uph": "200-500", "ct": 25, "price": "30-40万", "scene": "中等批量+焊膏检测", "desc": "双轨双工位+3D SPI，效率与检测一体"},
    "KC2708": {"auto": "半自动", "stations": 2, "rails": 2, "uph": "200-500", "ct": 25, "price": "28-38万", "scene": "需要实时数据监控", "desc": "双轨双工位带显示，便于产线监控"},

    # 在线式双轨双工位（量产主流）
    "KC2706": {"auto": "全自动", "stations": 2, "rails": 2, "uph": "400-800", "ct": 20, "price": "35-50万", "scene": "量产线主力机型", "desc": "在线式双轨双工位，自动上下料，UPH可达800，产线标配"},
    "KC2707": {"auto": "全自动", "stations": 2, "rails": 2, "uph": "400-800", "ct": 20, "price": "40-55万", "scene": "量产+焊膏检测", "desc": "在线双轨+3D SPI，量产同时监控焊膏质量"},
    "KC2709": {"auto": "全自动", "stations": 2, "rails": 2, "uph": "400-800", "ct": 20, "price": "38-52万", "scene": "量产+数据可视化", "desc": "在线双轨+显示，产线实时监控测试状态"},
    "KC2710": {"auto": "全自动", "stations": 2, "rails": 2, "uph": "400-800", "ct": 20, "price": "45-60万", "scene": "高端量产线", "desc": "在线双轨+显示+3D SPI，全功能量产顶配"},

    # 离线多工位（大批量/多品种）
    "KC2711": {"auto": "半自动", "stations": 4, "rails": 2, "uph": "500-1000", "ct": 15, "price": "35-50万", "scene": "大批量/多品种换产", "desc": "多工位并行测试，UPH翻倍，适合多品种混线"},
    "KC2712": {"auto": "半自动", "stations": 4, "rails": 2, "uph": "500-1000", "ct": 15, "price": "40-55万", "scene": "大批量+焊膏检测", "desc": "多工位+3D SPI，大批量+检测一体"},
    "KC2715": {"auto": "半自动", "stations": 4, "rails": 2, "uph": "500-1000", "ct": 15, "price": "38-52万", "scene": "大批量+数据监控", "desc": "多工位+显示，大批量产线监控"},

    # 在线式多工位（高端量产）
    "KC2713": {"auto": "全自动", "stations": 4, "rails": 2, "uph": "800-1500", "ct": 12, "price": "50-70万", "scene": "高产能量产线", "desc": "在线多工位并行，UPH最高1500，高速产线首选"},
    "KC2714": {"auto": "全自动", "stations": 4, "rails": 2, "uph": "800-1500", "ct": 12, "price": "55-75万", "scene": "高产能+焊膏检测", "desc": "在线多工位+3D SPI，高端量产+检测"},
    "KC2716": {"auto": "全自动", "stations": 4, "rails": 2, "uph": "800-1500", "ct": 12, "price": "52-72万", "scene": "高产能+监控", "desc": "在线多工位+显示，高速产线监控"},
    "KC2717": {"auto": "全自动", "stations": 4, "rails": 2, "uph": "800-1500", "ct": 12, "price": "60-80万", "scene": "顶级量产线", "desc": "在线多工位+显示+3D SPI，全功能顶配"},

    # 离线/在线多轨多工位（超大产能）
    "KC2718": {"auto": "半自动", "stations": 6, "rails": 3, "uph": "1000-2000", "ct": 10, "price": "55-75万", "scene": "超大产能/多产线", "desc": "多轨多工位，UPH最高2000，超大产能定制"},
    "KC2719": {"auto": "全自动", "stations": 6, "rails": 3, "uph": "1000-2000", "ct": 10, "price": "65-90万", "scene": "超大产能自动线", "desc": "在线多轨多工位，全自动超大产能，整线集成标配"},

    # 通用FCT测试系统
    "KC3202": {"auto": "可定制", "stations": 0, "rails": 0, "uph": "定制", "ct": 0, "price": "20-100万", "scene": "定制化FCT系统", "desc": "通用FCT测试平台，可根据客户需求定制工位数/轨道/自动化程度"},
}

# FCT 核心技术规格（从鼎新需求提取，作为标准参数）
FCT_CORE_SPEC = (
    "测控架构：FPGA+ARM模块化设计；单步测试时间<50ms；OK板通过率≥99%；"
    "工控机：I7-10700+/16GB/240G SSD+1T HDD；"
    "DAQ采集卡：12bit+/1MS/s/16通道+；"
    "交流电压测量：0-250VAC精度0.2%/16通道；"
    "交流电流测量：0-10A精度0.2%/16通道；"
    "直流电压测量：0-500VDC精度0.2%/8通道；"
    "换产时间：单工位治具≤5分钟"
)


def main():
    conn = sqlite3.connect(DB_PATH)
    updated = 0
    for code, spec in FCT_MATRIX.items():
        # test_types
        test_types = "FCT功能测试"
        if "+3D SPI" in spec["desc"] or "SPI" in spec["desc"]:
            test_types += "+3D焊膏检测"
        if "显示" in spec["desc"]:
            test_types += "+数据可视化"

        # max_throughput_uph（取区间上限）
        uph_match = re.search(r"(\d+)-(\d+)", str(spec["uph"]))
        max_uph = int(uph_match.group(2)) if uph_match else None

        conn.execute(
            """UPDATE advantage_products SET
            description = ?,
            test_types = ?,
            typical_ct_seconds = ?,
            max_throughput_uph = ?,
            automation_level = ?,
            workstation_count = ?,
            rail_type = ?
            WHERE product_code = ?""",
            (
                f"{spec['desc']}。适用场景：{spec['scene']}。参考价格：{spec['price']}。{FCT_CORE_SPEC}",
                test_types,
                spec["ct"] if spec["ct"] else None,
                max_uph,
                spec["auto"],
                spec["stations"] if spec["stations"] else None,
                f"{spec['rails']}轨" if spec["rails"] else None,
                code,
            ),
        )
        updated += 1
        print(f"  ✓ {code}: {spec['auto']} {spec['stations']}工位 {spec['rails']}轨 UPH{spec['uph']} {spec['price']}")

    conn.commit()
    print(f"\n完成：更新 {updated} 个 KC2700/KC3200 FCT 产品参数")

    # 验证
    print("\n=== 抽样验证 ===")
    for row in conn.execute(
        "SELECT product_code, product_name, automation_level, workstation_count, max_throughput_uph, "
        "substr(description,1,60) FROM advantage_products WHERE product_code IN ('KC2706','KC2713','KC2719') ORDER BY product_code"
    ):
        print(f"\n  {row[0]} {row[1]}")
        print(f"  自动化:{row[2]} 工位:{row[3]} 最大UPH:{row[4]}")
        print(f"  描述:{row[5]}...")

    conn.close()


if __name__ == "__main__":
    main()
