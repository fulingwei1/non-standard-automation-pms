#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化评分规则数据
"""

import json
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.models.base import get_session
from app.models.sales import ScoringRule
from app.models.user import User


def seed_scoring_rules():
    """初始化评分规则"""
    db = get_session()
    
    try:
        # 检查是否已有规则
        existing = db.query(ScoringRule).filter(ScoringRule.version == "2.0").first()
        if existing:
            print("评分规则 v2.0 已存在，跳过初始化")
            return
        
        # 读取评分规则JSON文件（优先使用项目内的文件）
        # 1. 优先使用项目内的文件
        rules_file = project_root / "data" / "scoring_rules" / "scoring_rules_v2.0.json"
        # 2. 如果不存在，尝试从presales-project读取（向后兼容）
        if not rules_file.exists():
            rules_file = project_root / "presales-project" / "presales-evaluation-system" / "scoring_rules_v2.0.json"
        # 3. 如果都不存在，使用默认规则
        if not rules_file.exists():
            print(f"警告: 评分规则文件不存在: {rules_file}")
            # 使用简化的规则
            rules_json = json.dumps({
                "version": "2.0",
                "scales": {
                    "total_score_max": 100,
                    "pass_threshold": 60,
                    "decision_thresholds": [
                        {"min_score": 75, "decision": "推荐立项", "description": "项目质量优秀"},
                        {"min_score": 60, "decision": "有条件立项", "description": "项目基本合格"},
                        {"min_score": 45, "decision": "暂缓", "description": "项目存在风险"},
                        {"min_score": 0, "decision": "不建议立项", "description": "项目不符合标准"}
                    ]
                },
                "evaluation_criteria": {
                    "customer_nature": {
                        "name": "客户性质",
                        "field": "customerType",
                        "max_points": 10,
                        "options": [
                            {"value": "老客户成交", "points": 10},
                            {"value": "新客户", "points": 6}
                        ]
                    }
                }
            }, ensure_ascii=False)
        else:
            with open(rules_file, 'r', encoding='utf-8') as f:
                rules_data = json.load(f)
                rules_json = json.dumps(rules_data, ensure_ascii=False)
        
        # 获取admin用户
        admin = db.query(User).filter(User.username == "admin").first()
        created_by = admin.id if admin else None
        
        # 创建评分规则
        rule = ScoringRule(
            version="2.0",
            rules_json=rules_json,
            is_active=True,
            description="技术评估评分规则 v2.0",
            created_by=created_by
        )
        
        db.add(rule)
        db.commit()
        
        print("✅ 评分规则初始化成功")
        print(f"   版本: 2.0")
        print(f"   状态: 已激活")
        
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_scoring_rules()

