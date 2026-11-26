#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从金凯博 100 个真实项目目录导入案例。

目录结构：001-L-龙光传-T13T电动空调控制面板FCT测试设备-签单
格式：编号-销售代号-销售名-项目名-是否签单

每个目录含：报价单(xlsx)、技术方案(docx/pdf)、技术要求(xlsx)
本脚本：
  1. 从目录名提取：项目名/销售/是否签单
  2. 从报价单提取：报价金额/成本/毛利
  3. 从技术方案文件名推断：设备类型/行业
  4. 导入 presale_knowledge_case
"""
import os
import re
import sys
import sqlite3
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

CASES_DIR = "/Users/flw/Desktop/售前项目汇总-100个匹配案例/售前项目汇总-100个匹配案例"
DB_PATH = Path(__file__).resolve().parents[1] / "data" / "app.db"

# 设备类型关键词映射
EQUIPMENT_KEYWORDS = {
    "BMS": "BMS测试", "bms": "BMS测试",
    "FCT": "FCT测试", "fct": "FCT测试",
    "ICT": "ICT测试", "ict": "ICT测试",
    "EOL": "EOL测试", "eol": "EOL测试",
    "老化": "老化设备", "老化": "老化设备",
    "烧录": "烧录设备",
    "涂覆": "涂覆机",
    "点胶": "点胶机",
    "分板": "分板机",
    "充放电": "充放电设备",
    "OBC": "OBC测试", "obc": "OBC测试",
    "电驱": "电驱测试",
    "继电器": "继电器测试",
    "遥控器": "遥控器测试",
    "传感器": "传感器测试",
    "PACK": "PACK测试", "pack": "PACK测试",
    "DCR": "DCR测试",
    "VC": "VC测试",
    "HIL": "HIL测试",
    "产线": "自动化产线",
    "香氛": "香氛模块测试",
}

# 行业关键词映射
INDUSTRY_KEYWORDS = {
    "比亚迪": "新能源汽车", "吉利": "新能源汽车", "威睿": "新能源汽车",
    "欣旺达": "新能源", "宁德": "新能源", "楚能": "新能源",
    "中航": "新能源", "福森": "新能源", "特隆美": "新能源",
    "海尔": "白色家电", "美的": "白色家电", "TCL": "白色家电",
    "海信": "白色家电", "长虹": "白色家电",
    "和而泰": "汽车电子", "大族": "激光设备",
    "小米": "消费电子", "歌尔": "消费电子",
    "三达兴": "汽车电子", "林荣魁": "汽车电子",
}


def parse_dir_name(dirname):
    """从目录名提取结构化信息。"""
    # 格式：001-L-龙光传-T13T电动空调控制面板FCT测试设备-签单
    # 或：003-S-宋魁-参考资料
    parts = dirname.split("-", 3)  # 最多分4段
    info = {
        "dir_code": "",
        "sales_code": "",
        "sales_name": "",
        "project_name": dirname,
        "is_won": "未知",
    }

    if len(parts) >= 4:
        info["dir_code"] = parts[0]
        info["sales_code"] = parts[1]
        info["sales_name"] = parts[2]
        rest = parts[3]
        # 检查是否签单
        if "已签单" in rest or "签单" in rest:
            info["is_won"] = "是"
            rest = rest.replace("-已签单", "").replace("-签单", "").replace("已签单", "").replace("签单", "")
        info["project_name"] = rest.strip()
    elif len(parts) >= 3:
        info["dir_code"] = parts[0]
        info["sales_code"] = parts[1]
        info["sales_name"] = parts[2] if not parts[2].isdigit() else ""

    return info


def infer_equipment(project_name):
    """从项目名推断设备类型。"""
    for kw, eq_type in EQUIPMENT_KEYWORDS.items():
        if kw in project_name:
            return eq_type
    return "测试设备"


def infer_industry(project_name):
    """从项目名推断行业。"""
    for kw, industry in INDUSTRY_KEYWORDS.items():
        if kw in project_name:
            return industry
    return None


def extract_quote_from_xlsx(xlsx_path):
    """从报价单 Excel 提取报价金额。"""
    try:
        import openpyxl
        wb = openpyxl.load_workbook(xlsx_path, data_only=True, read_only=True)
        for sn in wb.sheetnames[:2]:  # 只看前2个sheet
            ws = wb[sn]
            for row in ws.iter_rows(max_row=50, values_only=True):
                for cell in row:
                    if cell and isinstance(cell, str):
                        # 找"合计""总价""总计"附近的数字
                        if any(kw in cell for kw in ["合计", "总价", "总计", "金额合计", "报价合计"]):
                            # 找同一行或下一行的数字
                            for c in row:
                                if isinstance(c, (int, float)) and c > 10000:  # 大于1万才有意义
                                    wb.close()
                                    return float(c)
        wb.close()
    except Exception:
        pass
    return None


def find_quote_file(dir_path):
    """在目录里找报价单文件。"""
    for root, _, files in os.walk(dir_path):
        for f in files:
            if "报价" in f and (f.endswith(".xlsx") or f.endswith(".xls")):
                return os.path.join(root, f)
    return None


def find_spec_file(dir_path):
    """在目录里找技术方案文件。"""
    for root, _, files in os.walk(dir_path):
        for f in files:
            if any(kw in f for kw in ["方案", "技术", "规格"]) and (f.endswith(".docx") or f.endswith(".pdf") or f.endswith(".pptx")):
                return f
    return None


def main():
    if not os.path.exists(CASES_DIR):
        print(f"目录不存在: {CASES_DIR}")
        sys.exit(1)

    # 收集所有项目目录
    dirs = sorted([d for d in os.listdir(CASES_DIR) if os.path.isdir(os.path.join(CASES_DIR, d)) and d[0].isdigit()])
    print(f"找到 {len(dirs)} 个项目目录")

    conn = sqlite3.connect(DB_PATH)
    # 查已有案例名
    existing = {r[0] for r in conn.execute("SELECT case_name FROM presale_knowledge_case").fetchall()}

    imported = 0
    skipped = 0

    for dirname in dirs:
        dir_path = os.path.join(CASES_DIR, dirname)
        info = parse_dir_name(dirname)
        project_name = info["project_name"]

        if not project_name or project_name == "参考资料" or project_name == "新建文件夹":
            skipped += 1
            continue

        # 跳过已存在
        if project_name in existing:
            skipped += 1
            continue

        # 推断设备类型和行业
        equipment_type = infer_equipment(project_name)
        industry = infer_industry(project_name)

        # 从报价单提取金额
        quote_amount = None
        quote_file = find_quote_file(dir_path)
        if quote_file:
            quote_amount = extract_quote_from_xlsx(quote_file)

        # 技术方案文件名
        spec_file = find_spec_file(dir_path)

        # 构建案例摘要
        summary_parts = [project_name]
        if info["sales_name"]:
            summary_parts.append(f"销售：{info['sales_name']}")
        if info["is_won"] == "是":
            summary_parts.append("已签单")
        project_summary = "，".join(summary_parts)

        # 技术亮点（从项目名+文件名推断）
        tech_highlights = f"设备类型：{equipment_type}"
        if spec_file:
            tech_highlights += f"。技术方案：{spec_file[:40]}"

        # 插入案例
        try:
            conn.execute(
                """INSERT INTO presale_knowledge_case
                (case_name, industry, equipment_type, project_amount, project_summary,
                 technical_highlights, quality_score, is_public, is_won,
                 created_at, updated_at)
                VALUES (?,?,?,?,?, ?,?, 1, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)""",
                (
                    project_name,
                    industry,
                    equipment_type,
                    quote_amount,
                    project_summary,
                    tech_highlights,
                    0.85 if info["is_won"] == "是" else 0.6,
                    info["is_won"],
                ),
            )
            existing.add(project_name)
            imported += 1

            amount_str = f"¥{quote_amount:,.0f}" if quote_amount else "无报价"
            won_str = "✓签单" if info["is_won"] == "是" else ""
            print(f"  [{imported}] {project_name[:35]:<35} | {equipment_type:<10} | {industry or '?':<8} | {amount_str} {won_str}")
        except Exception as e:
            print(f"  ✗ {project_name}: {e}")
            skipped += 1

    conn.commit()

    # 统计
    total_cases = conn.execute("SELECT COUNT(*) FROM presale_knowledge_case WHERE case_name NOT LIKE '%_name_%'").fetchone()[0]
    print(f"\n完成：导入 {imported} 条，跳过 {skipped} 条")
    print(f"案例库总数：{total_cases}")

    # 按设备类型统计
    print("\n设备类型分布：")
    for row in conn.execute(
        "SELECT equipment_type, COUNT(*) FROM presale_knowledge_case "
        "WHERE case_name NOT LIKE '%_name_%' GROUP BY equipment_type ORDER BY COUNT(*) DESC LIMIT 10"
    ):
        print(f"  {row[0]}: {row[1]}")

    # 按行业统计
    print("\n行业分布：")
    for row in conn.execute(
        "SELECT industry, COUNT(*) FROM presale_knowledge_case "
        "WHERE industry IS NOT NULL AND industry != '' AND case_name NOT LIKE '%_name_%' "
        "GROUP BY industry ORDER BY COUNT(*) DESC LIMIT 8"
    ):
        print(f"  {row[0]}: {row[1]}")

    # 签单率
    won = conn.execute(
        "SELECT COUNT(*) FROM presale_knowledge_case WHERE is_won = '是'"
    ).fetchone()[0]
    print(f"\n签单案例：{won} 条")

    conn.close()


if __name__ == "__main__":
    main()
