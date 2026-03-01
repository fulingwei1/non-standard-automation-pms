# -*- coding: utf-8 -*-
"""
销售组织架构管理
支持 4 层层级：销售 → 销售经理 → 销售总监 → 销售总经理
"""

from typing import Any, Optional, List, Dict
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, Path, Query, Body
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User

router = APIRouter()


# ========== 1. 组织架构数据模型 ==========

@router.get("/organization/structure", summary="组织架构结构")
def get_organization_structure(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取完整的销售组织架构
    
    4 层层级：
    - L1: 销售总经理 (GM) - 管理整个销售团队
    - L2: 销售总监 (Director) - 每个分公司/子公司 1 名
    - L3: 销售经理 (Manager) - 带领 3-5 人
    - L4: 销售 (Sales) - 销售工程师/销售助理
    """
    
    structure = {
        "organization_name": "金凯博自动化测试 - 销售总部",
        "total_members": 28,
        "levels": 4,
        
        # 组织层级定义
        "level_definitions": [
            {
                "level": 1,
                "name": "销售总经理",
                "code": "GM",
                "description": "负责管理整个销售总监团队",
                "scope": "全公司",
                "reporting_to": "CEO",
            },
            {
                "level": 2,
                "name": "销售总监",
                "code": "Director",
                "description": "每个分公司/子公司设 1 名",
                "scope": "分公司/子公司",
                "reporting_to": "销售总经理",
                "managers_count": "2-3 个销售经理",
            },
            {
                "level": 3,
                "name": "销售经理",
                "code": "Manager",
                "description": "带领 3-5 人团队",
                "scope": "销售团队",
                "reporting_to": "销售总监",
                "team_size": "3-5 人",
            },
            {
                "level": 4,
                "name": "销售",
                "code": "Sales",
                "description": "销售工程师/销售助理",
                "scope": "个人贡献",
                "reporting_to": "销售经理",
                "roles": ["销售工程师", "销售助理"],
            },
        ],
        
        # 完整组织树
        "organization_tree": {
            "id": 1,
            "name": "销售总部",
            "level": "GM",
            "person": {
                "id": 1,
                "name": "陈总",
                "title": "销售总经理",
                "email": "chen@goldenkab.com",
            },
            "metrics": {
                "quota_annual": 800000000,
                "achieved_ytd": 512000000,
                "achievement_rate": 64.0,
                "team_size": 28,
                "pipeline_total": 450000000,
                "pipeline_weighted": 285000000,
            },
            "children": [
                {
                    "id": 2,
                    "name": "深圳分公司",
                    "level": "Director",
                    "person": {
                        "id": 2,
                        "name": "张总监",
                        "title": "销售总监",
                        "email": "zhang.sz@goldenkab.com",
                    },
                    "metrics": {
                        "quota_annual": 300000000,
                        "achieved_ytd": 198000000,
                        "achievement_rate": 66.0,
                        "team_size": 10,
                        "pipeline_total": 180000000,
                        "pipeline_weighted": 120000000,
                    },
                    "children": [
                        {
                            "id": 5,
                            "name": "华南一区",
                            "level": "Manager",
                            "person": {
                                "id": 5,
                                "name": "张三",
                                "title": "销售经理",
                                "email": "zhangsan@goldenkab.com",
                            },
                            "metrics": {
                                "quota_annual": 100000000,
                                "achieved_ytd": 68000000,
                                "achievement_rate": 68.0,
                                "team_size": 4,
                                "pipeline_total": 65000000,
                                "pipeline_weighted": 45000000,
                            },
                            "children": [
                                {
                                    "id": 11,
                                    "name": "张三",
                                    "level": "Sales",
                                    "role": "销售工程师",
                                    "metrics": {
                                        "quota": 50000000,
                                        "achieved": 32000000,
                                        "rate": 64.0,
                                        "opportunities": 3,
                                    },
                                },
                                {
                                    "id": 12,
                                    "name": "李小妹",
                                    "level": "Sales",
                                    "role": "销售工程师",
                                    "metrics": {
                                        "quota": 30000000,
                                        "achieved": 22000000,
                                        "rate": 73.3,
                                        "opportunities": 2,
                                    },
                                },
                                {
                                    "id": 13,
                                    "name": "王小助",
                                    "level": "Sales",
                                    "role": "销售助理",
                                    "metrics": {
                                        "quota": 20000000,
                                        "achieved": 14000000,
                                        "rate": 70.0,
                                        "opportunities": 2,
                                    },
                                },
                            ],
                        },
                        {
                            "id": 6,
                            "name": "华南二区",
                            "level": "Manager",
                            "person": {
                                "id": 6,
                                "name": "李四",
                                "title": "销售经理",
                            },
                            "metrics": {
                                "quota_annual": 100000000,
                                "achieved_ytd": 65000000,
                                "achievement_rate": 65.0,
                                "team_size": 3,
                                "pipeline_total": 55000000,
                                "pipeline_weighted": 38000000,
                            },
                            "children": [
                                {"id": 14, "name": "赵六", "level": "Sales", "role": "销售工程师"},
                                {"id": 15, "name": "钱七", "level": "Sales", "role": "销售工程师"},
                                {"id": 16, "name": "孙八", "level": "Sales", "role": "销售助理"},
                            ],
                        },
                        {
                            "id": 7,
                            "name": "华南三区",
                            "level": "Manager",
                            "person": {"id": 7, "name": "王五", "title": "销售经理"},
                            "metrics": {
                                "quota_annual": 100000000,
                                "achieved_ytd": 65000000,
                                "achievement_rate": 65.0,
                                "team_size": 3,
                            },
                            "children": [
                                {"id": 17, "name": "周九", "level": "Sales"},
                                {"id": 18, "name": "吴十", "level": "Sales"},
                                {"id": 19, "name": "郑十一", "level": "Sales"},
                            ],
                        },
                    ],
                },
                {
                    "id": 3,
                    "name": "苏州分公司",
                    "level": "Director",
                    "person": {
                        "id": 3,
                        "name": "李总监",
                        "title": "销售总监",
                        "email": "li.suzhou@goldenkab.com",
                    },
                    "metrics": {
                        "quota_annual": 280000000,
                        "achieved_ytd": 175000000,
                        "achievement_rate": 62.5,
                        "team_size": 10,
                        "pipeline_total": 150000000,
                        "pipeline_weighted": 95000000,
                    },
                    "children": [
                        {
                            "id": 8,
                            "name": "华东一区",
                            "level": "Manager",
                            "person": {"id": 8, "name": "赵经理", "title": "销售经理"},
                            "children": [
                                {"id": 20, "name": "队员 A", "level": "Sales"},
                                {"id": 21, "name": "队员 B", "level": "Sales"},
                                {"id": 22, "name": "队员 C", "level": "Sales"},
                                {"id": 23, "name": "队员 D", "level": "Sales"},
                            ],
                        },
                        {
                            "id": 9,
                            "name": "华东二区",
                            "level": "Manager",
                            "person": {"id": 9, "name": "钱经理", "title": "销售经理"},
                            "children": [
                                {"id": 24, "name": "队员 E", "level": "Sales"},
                                {"id": 25, "name": "队员 F", "level": "Sales"},
                                {"id": 26, "name": "队员 G", "level": "Sales"},
                            ],
                        },
                    ],
                },
                {
                    "id": 4,
                    "name": "合肥分公司",
                    "level": "Director",
                    "person": {
                        "id": 4,
                        "name": "王总监",
                        "title": "销售总监",
                        "email": "wang.hefei@goldenkab.com",
                    },
                    "metrics": {
                        "quota_annual": 220000000,
                        "achieved_ytd": 139000000,
                        "achievement_rate": 63.2,
                        "team_size": 8,
                        "pipeline_total": 120000000,
                        "pipeline_weighted": 70000000,
                    },
                    "children": [
                        {
                            "id": 10,
                            "name": "华北一区",
                            "level": "Manager",
                            "person": {"id": 10, "name": "孙经理", "title": "销售经理"},
                            "children": [
                                {"id": 27, "name": "队员 H", "level": "Sales"},
                                {"id": 28, "name": "队员 I", "level": "Sales"},
                                {"id": 29, "name": "队员 J", "level": "Sales"},
                            ],
                        },
                    ],
                },
            ],
        },
    }
    
    return structure


# ========== 2. 层级数据汇总 API ==========

@router.get("/organization/rollup/{level}/{person_id}", summary="层级数据汇总")
def get_hierarchy_rollup(
    level: str = Path(..., description="层级：GM/Director/Manager/Sales"),
    person_id: int = Path(..., description="人员 ID"),
    include_details: bool = Query(True, description="是否包含详细下属数据"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取指定层级的数据汇总
    
    支持：
    - 销售总经理：汇总所有总监数据
    - 销售总监：汇总所有经理数据
    - 销售经理：汇总所有销售数据
    - 销售：个人数据
    """
    
    # 示例：销售经理视图
    if level == "Manager" and person_id == 5:
        return {
            "person": {
                "id": 5,
                "name": "张三",
                "title": "销售经理",
                "team": "华南一区",
                "direct_reports": 3,
            },
            
            # 个人业绩
            "personal_metrics": {
                "quota": 50000000,
                "achieved": 32000000,
                "rate": 64.0,
                "opportunities": 3,
                "pipeline": 3500000,
            },
            
            # 团队汇总（下属 3 人）
            "team_rollup": {
                "total_members": 3,
                "quota_total": 100000000,
                "achieved_total": 68000000,
                "achievement_rate": 68.0,
                "opportunities_total": 7,
                "pipeline_total": 65000000,
                "pipeline_weighted": 45000000,
            },
            
            # 下属明细
            "team_members": [
                {
                    "id": 11,
                    "name": "张三",
                    "role": "销售工程师",
                    "quota": 50000000,
                    "achieved": 32000000,
                    "rate": 64.0,
                    "opportunities": 3,
                    "top_opportunity": "宁德时代 FCT (350 万)",
                },
                {
                    "id": 12,
                    "name": "李小妹",
                    "role": "销售工程师",
                    "quota": 30000000,
                    "achieved": 22000000,
                    "rate": 73.3,
                    "opportunities": 2,
                    "top_opportunity": "亿纬锂能 烧录 (180 万)",
                },
                {
                    "id": 13,
                    "name": "王小助",
                    "role": "销售助理",
                    "quota": 20000000,
                    "achieved": 14000000,
                    "rate": 70.0,
                    "opportunities": 2,
                    "top_opportunity": "某客户 测试线 (150 万)",
                },
            ],
            
            # 团队排名
            "team_ranking": {
                "vs_company": {
                    "rank": 3,
                    "total_teams": 8,
                    "percentile": 62.5,
                },
                "vs_director": {
                    "rank": 1,
                    "total_teams": 3,
                    "percentile": 100,
                    "director": "张总监（深圳）",
                },
            },
            
            # 风险预警
            "alerts": [
                {
                    "type": "warning",
                    "message": "王小助 连续 2 周无新商机",
                    "member_id": 13,
                },
                {
                    "type": "info",
                    "message": "李小妹 完成率 73.3%，团队第一",
                    "member_id": 12,
                },
            ],
        }
    
    # 示例：销售总监视图
    elif level == "Director" and person_id == 2:
        return {
            "person": {
                "id": 2,
                "name": "张总监",
                "title": "销售总监",
                "branch": "深圳分公司",
                "direct_reports": 3,  # 3 个销售经理
            },
            
            # 分公司汇总
            "branch_metrics": {
                "quota_annual": 300000000,
                "achieved_ytd": 198000000,
                "achievement_rate": 66.0,
                "team_size": 10,
                "pipeline_total": 180000000,
                "pipeline_weighted": 120000000,
            },
            
            # 下属经理汇总
            "managers_rollup": [
                {
                    "id": 5,
                    "name": "张三",
                    "team": "华南一区",
                    "team_size": 4,
                    "quota": 100000000,
                    "achieved": 68000000,
                    "rate": 68.0,
                    "rank": 1,
                },
                {
                    "id": 6,
                    "name": "李四",
                    "team": "华南二区",
                    "team_size": 3,
                    "quota": 100000000,
                    "achieved": 65000000,
                    "rate": 65.0,
                    "rank": 2,
                },
                {
                    "id": 7,
                    "name": "王五",
                    "team": "华南三区",
                    "team_size": 3,
                    "quota": 100000000,
                    "achieved": 65000000,
                    "rate": 65.0,
                    "rank": 3,
                },
            ],
            
            # 分公司对比
            "branch_comparison": [
                {"branch": "深圳分公司", "rate": 66.0, "rank": 1},
                {"branch": "苏州分公司", "rate": 62.5, "rank": 2},
                {"branch": "合肥分公司", "rate": 63.2, "rank": 3},
            ],
        }
    
    # 示例：销售总经理视图
    elif level == "GM":
        return {
            "person": {
                "id": 1,
                "name": "陈总",
                "title": "销售总经理",
                "direct_reports": 3,  # 3 个总监
            },
            
            # 公司整体
            "company_metrics": {
                "quota_annual": 800000000,
                "achieved_ytd": 512000000,
                "achievement_rate": 64.0,
                "yoy_growth": 28.0,
                "team_size": 28,
                "pipeline_total": 450000000,
                "pipeline_weighted": 285000000,
            },
            
            # 总监汇总
            "directors_rollup": [
                {
                    "id": 2,
                    "name": "张总监",
                    "branch": "深圳分公司",
                    "team_size": 10,
                    "quota": 300000000,
                    "achieved": 198000000,
                    "rate": 66.0,
                    "yoy": 32.0,
                    "rank": 1,
                },
                {
                    "id": 3,
                    "name": "李总监",
                    "branch": "苏州分公司",
                    "team_size": 10,
                    "quota": 280000000,
                    "achieved": 175000000,
                    "rate": 62.5,
                    "yoy": 25.0,
                    "rank": 2,
                },
                {
                    "id": 4,
                    "name": "王总监",
                    "branch": "合肥分公司",
                    "team_size": 8,
                    "quota": 220000000,
                    "achieved": 139000000,
                    "rate": 63.2,
                    "yoy": 22.0,
                    "rank": 3,
                },
            ],
            
            # 战略机会
            "strategic_opportunities": [
                {"name": "宁德时代 战略合作", "value": 50000000, "owner": "张三", "win_rate": 75},
                {"name": "比亚迪 二期", "value": 40000000, "owner": "李四", "win_rate": 82},
            ],
        }
    
    return {}


# ========== 3. 组织绩效对比 ==========

@router.get("/organization/performance-comparison", summary="组织绩效对比")
def get_organization_performance_comparison(
    level: str = Query("all", description="层级：all/GM/Director/Manager/Sales"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    组织绩效对比分析
    
    支持：
    - 分公司对比（总监级）
    - 团队对比（经理级）
    - 个人对比（销售级）
    """
    
    comparison = {
        "analysis_date": date.today().isoformat(),
        
        # 分公司对比（总监级）
        "branch_comparison": [
            {
                "branch": "深圳分公司",
                "director": "张总监",
                "quota": 300000000,
                "achieved": 198000000,
                "rate": 66.0,
                "yoy": 32.0,
                "team_size": 10,
                "avg_quota_per_person": 30000000,
                "rank": 1,
            },
            {
                "branch": "苏州分公司",
                "director": "李总监",
                "quota": 280000000,
                "achieved": 175000000,
                "rate": 62.5,
                "yoy": 25.0,
                "team_size": 10,
                "avg_quota_per_person": 28000000,
                "rank": 2,
            },
            {
                "branch": "合肥分公司",
                "director": "王总监",
                "quota": 220000000,
                "achieved": 139000000,
                "rate": 63.2,
                "yoy": 22.0,
                "team_size": 8,
                "avg_quota_per_person": 27500000,
                "rank": 3,
            },
        ],
        
        # 团队对比（经理级）
        "team_comparison": [
            {
                "team": "华南一区",
                "manager": "张三",
                "branch": "深圳分公司",
                "quota": 100000000,
                "achieved": 68000000,
                "rate": 68.0,
                "team_size": 4,
                "rank": 1,
            },
            {
                "team": "华南二区",
                "manager": "李四",
                "branch": "深圳分公司",
                "quota": 100000000,
                "achieved": 65000000,
                "rate": 65.0,
                "team_size": 3,
                "rank": 2,
            },
            {
                "team": "华南三区",
                "manager": "王五",
                "branch": "深圳分公司",
                "quota": 100000000,
                "achieved": 65000000,
                "rate": 65.0,
                "team_size": 3,
                "rank": 3,
            },
            {
                "team": "华东一区",
                "manager": "赵经理",
                "branch": "苏州分公司",
                "quota": 100000000,
                "achieved": 62000000,
                "rate": 62.0,
                "team_size": 4,
                "rank": 4,
            },
            {
                "team": "华东二区",
                "manager": "钱经理",
                "branch": "苏州分公司",
                "quota": 80000000,
                "achieved": 48000000,
                "rate": 60.0,
                "team_size": 3,
                "rank": 5,
            },
            {
                "team": "华北一区",
                "manager": "孙经理",
                "branch": "合肥分公司",
                "quota": 80000000,
                "achieved": 47000000,
                "rate": 58.8,
                "team_size": 3,
                "rank": 6,
            },
        ],
        
        # 个人对比（销售级）- Top 10
        "individual_ranking": [
            {"rank": 1, "name": "李小妹", "team": "华南一区", "rate": 73.3, "quota": 30000000},
            {"rank": 2, "name": "王小助", "team": "华南一区", "rate": 70.0, "quota": 20000000},
            {"rank": 3, "name": "张三", "team": "华南一区", "rate": 64.0, "quota": 50000000},
            {"rank": 4, "name": "赵六", "team": "华南二区", "rate": 62.0, "quota": 35000000},
            {"rank": 5, "name": "钱七", "team": "华南二区", "rate": 60.0, "quota": 30000000},
        ],
    }
    
    return comparison
