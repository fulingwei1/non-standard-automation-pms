#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查指定项目编码是否存在
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.base import get_db_session
from app.models.project import Project

def check_projects(project_codes):
    """检查项目是否存在"""
    print(f"\n检查项目: {', '.join(project_codes)}\n")
    print("=" * 60)
    
    with get_db_session() as db:
        for code in project_codes:
            project = db.query(Project).filter(Project.project_code == code).first()
            
            if project:
                print(f"✅ {code}: 存在")
                print(f"   - 项目名称: {project.project_name}")
                print(f"   - 项目ID: {project.id}")
                print(f"   - 阶段: {project.stage}")
                print(f"   - 健康度: {project.health}")
                print(f"   - 进度: {project.progress_pct}%")
                print(f"   - 是否启用: {project.is_active}")
                print()
            else:
                print(f"❌ {code}: 不存在")
                print()
    
    print("=" * 60)
    
    # 统计所有项目
    total = db.query(Project).count()
    active = db.query(Project).filter(Project.is_active == True).count()
    print(f"\n数据库统计:")
    print(f"  - 总项目数: {total}")
    print(f"  - 启用项目数: {active}")

if __name__ == "__main__":
    # 要检查的项目编码
    project_codes = ["PJ250111", "PJ250110", "PJ250109"]
    check_projects(project_codes)
