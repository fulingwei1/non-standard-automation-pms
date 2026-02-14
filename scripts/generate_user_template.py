#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成用户导入模板文件
"""

import pandas as pd
from pathlib import Path

# 项目根目录
ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data"

# 确保 data 目录存在
DATA_DIR.mkdir(exist_ok=True)

# 模板数据
template_data = {
    "用户名": ["zhangsan", "lisi", "wangwu"],
    "密码": ["123456", "123456", ""],  # 空表示使用默认密码
    "真实姓名": ["张三", "李四", "王五"],
    "邮箱": ["zhangsan@example.com", "lisi@example.com", "wangwu@example.com"],
    "手机号": ["13800138000", "13800138001", ""],
    "工号": ["EMP001", "EMP002", "EMP003"],
    "部门": ["技术部", "销售部", "市场部"],
    "职位": ["工程师", "销售经理", "市场专员"],
    "角色": ["普通用户", "销售经理,普通用户", "普通用户"],  # 多个角色用逗号分隔
    "是否启用": ["是", "是", "否"],
}

df = pd.DataFrame(template_data)

# 生成 Excel 文件
excel_path = DATA_DIR / "user_import_template.xlsx"
df.to_excel(excel_path, index=False, engine="openpyxl")
print(f"✅ Excel 模板已生成: {excel_path}")

# 生成 CSV 文件
csv_path = DATA_DIR / "user_import_template.csv"
df.to_csv(csv_path, index=False, encoding="utf-8-sig")
print(f"✅ CSV 模板已生成: {csv_path}")

print("\n模板文件包含以下字段:")
print(", ".join(df.columns))
print(f"\n示例数据: {len(df)} 行")
