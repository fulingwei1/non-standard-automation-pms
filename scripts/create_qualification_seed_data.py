# -*- coding: utf-8 -*-
"""
任职资格体系种子数据
创建默认等级体系、常见岗位能力模型模板
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.models.base import get_session, init_db
from app.models.qualification import (
    QualificationLevel, PositionCompetencyModel
)


def create_qualification_levels(db):
    """创建任职资格等级"""
    levels = [
        {
            'level_code': 'ASSISTANT',
            'level_name': '助理级',
            'level_order': 1,
            'role_type': None,  # 通用
            'description': '助理级岗位，0-1年经验，在指导下完成基础工作，学习阶段'
        },
        {
            'level_code': 'JUNIOR',
            'level_name': '初级',
            'level_order': 2,
            'role_type': None,
            'description': '初级岗位，1-2年经验，能够独立完成基础工作，具备基本技能'
        },
        {
            'level_code': 'MIDDLE',
            'level_name': '中级',
            'level_order': 3,
            'role_type': None,
            'description': '中级岗位，2-4年经验，能够独立完成常规工作，具备一定的问题解决能力'
        },
        {
            'level_code': 'SENIOR',
            'level_name': '高级',
            'level_order': 4,
            'role_type': None,
            'description': '高级岗位，4-6年经验，能够独立完成复杂工作，具备较强的技术能力和业务理解'
        },
        {
            'level_code': 'EXPERT',
            'level_name': '专家级',
            'level_order': 5,
            'role_type': None,
            'description': '专家级岗位，6年以上经验，在专业领域有深入理解，能够指导他人，解决复杂问题，制定技术方案'
        }
    ]

    for level_data in levels:
        existing = db.query(QualificationLevel).filter(
            QualificationLevel.level_code == level_data['level_code']
        ).first()
        
        if not existing:
            level = QualificationLevel(**level_data)
            db.add(level)
            print(f"创建等级: {level_data['level_code']} - {level_data['level_name']}")
        else:
            print(f"等级已存在: {level_data['level_code']} - {level_data['level_name']}")

    db.commit()


def create_engineer_competency_models(db):
    """创建工程师岗位能力模型"""
    # 获取等级
    levels = {level.level_code: level for level in db.query(QualificationLevel).all()}
    
    engineer_subtypes = ['ME', 'EE', 'SW', 'TE']
    
    for subtype in engineer_subtypes:
        for level_code, level in levels.items():
            # 根据等级设置不同的能力要求
            if level_code == 'ASSISTANT':
                competency_dimensions = {
                    "technical_skills": {
                        "name": "专业技能",
                        "weight": 40,
                        "items": [
                            {"name": "基础设计能力", "description": "能够完成基础设计任务", "score_range": [0, 100]},
                            {"name": "编程/绘图能力", "description": "掌握基础编程或绘图技能", "score_range": [0, 100]},
                            {"name": "调试能力", "description": "能够进行基础调试", "score_range": [0, 100]}
                        ]
                    },
                    "business_skills": {
                        "name": "业务能力",
                        "weight": 20,
                        "items": [
                            {"name": "需求理解", "description": "能够理解基本需求", "score_range": [0, 100]},
                            {"name": "方案设计", "description": "能够参与方案设计", "score_range": [0, 100]}
                        ]
                    },
                    "communication_skills": {
                        "name": "沟通协作",
                        "weight": 20,
                        "items": [
                            {"name": "团队协作", "description": "能够与团队成员协作", "score_range": [0, 100]},
                            {"name": "跨部门沟通", "description": "能够进行基本沟通", "score_range": [0, 100]}
                        ]
                    },
                    "learning_skills": {
                        "name": "学习成长",
                        "weight": 10,
                        "items": [
                            {"name": "技术学习", "description": "主动学习新技术", "score_range": [0, 100]},
                            {"name": "知识分享", "description": "参与知识分享", "score_range": [0, 100]}
                        ]
                    },
                    "project_management_skills": {
                        "name": "项目管理",
                        "weight": 10,
                        "items": [
                            {"name": "任务管理", "description": "能够管理自己的任务", "score_range": [0, 100]},
                            {"name": "进度控制", "description": "能够控制任务进度", "score_range": [0, 100]}
                        ]
                    }
                }
            elif level_code == 'JUNIOR':
                competency_dimensions = {
                    "technical_skills": {
                        "name": "专业技能",
                        "weight": 35,
                        "items": [
                            {"name": "设计能力", "description": "能够独立完成常规设计", "score_range": [0, 100]},
                            {"name": "编程/绘图能力", "description": "熟练掌握编程或绘图技能", "score_range": [0, 100]},
                            {"name": "调试能力", "description": "能够独立调试", "score_range": [0, 100]},
                            {"name": "问题解决", "description": "能够解决常见问题", "score_range": [0, 100]}
                        ]
                    },
                    "business_skills": {
                        "name": "业务能力",
                        "weight": 25,
                        "items": [
                            {"name": "需求理解", "description": "能够深入理解需求", "score_range": [0, 100]},
                            {"name": "方案设计", "description": "能够设计常规方案", "score_range": [0, 100]}
                        ]
                    },
                    "communication_skills": {
                        "name": "沟通协作",
                        "weight": 20,
                        "items": [
                            {"name": "团队协作", "description": "能够有效协作", "score_range": [0, 100]},
                            {"name": "跨部门沟通", "description": "能够进行有效沟通", "score_range": [0, 100]}
                        ]
                    },
                    "learning_skills": {
                        "name": "学习成长",
                        "weight": 10,
                        "items": [
                            {"name": "技术学习", "description": "持续学习新技术", "score_range": [0, 100]},
                            {"name": "知识分享", "description": "主动分享知识", "score_range": [0, 100]}
                        ]
                    },
                    "project_management_skills": {
                        "name": "项目管理",
                        "weight": 10,
                        "items": [
                            {"name": "任务管理", "description": "能够管理多个任务", "score_range": [0, 100]},
                            {"name": "进度控制", "description": "能够有效控制进度", "score_range": [0, 100]}
                        ]
                    }
                }
            elif level_code == 'MIDDLE':
                competency_dimensions = {
                    "technical_skills": {
                        "name": "专业技能",
                        "weight": 35,
                        "items": [
                            {"name": "设计能力", "description": "能够独立完成常规设计", "score_range": [0, 100]},
                            {"name": "编程/绘图能力", "description": "熟练掌握编程或绘图技能", "score_range": [0, 100]},
                            {"name": "调试能力", "description": "能够独立调试", "score_range": [0, 100]},
                            {"name": "问题解决", "description": "能够解决常见问题", "score_range": [0, 100]}
                        ]
                    },
                    "business_skills": {
                        "name": "业务能力",
                        "weight": 25,
                        "items": [
                            {"name": "需求理解", "description": "能够深入理解需求", "score_range": [0, 100]},
                            {"name": "方案设计", "description": "能够设计常规方案", "score_range": [0, 100]}
                        ]
                    },
                    "communication_skills": {
                        "name": "沟通协作",
                        "weight": 20,
                        "items": [
                            {"name": "团队协作", "description": "能够有效协作", "score_range": [0, 100]},
                            {"name": "跨部门沟通", "description": "能够进行有效沟通", "score_range": [0, 100]}
                        ]
                    },
                    "learning_skills": {
                        "name": "学习成长",
                        "weight": 10,
                        "items": [
                            {"name": "技术学习", "description": "持续学习新技术", "score_range": [0, 100]},
                            {"name": "知识分享", "description": "主动分享知识", "score_range": [0, 100]}
                        ]
                    },
                    "project_management_skills": {
                        "name": "项目管理",
                        "weight": 10,
                        "items": [
                            {"name": "任务管理", "description": "能够管理多个任务", "score_range": [0, 100]},
                            {"name": "进度控制", "description": "能够有效控制进度", "score_range": [0, 100]}
                        ]
                    }
                }
            else:  # SENIOR, EXPERT 使用更高级的要求
                competency_dimensions = {
                    "technical_skills": {
                        "name": "专业技能",
                        "weight": 30,
                        "items": [
                            {"name": "设计能力", "description": "能够设计复杂系统", "score_range": [0, 100]},
                            {"name": "编程/绘图能力", "description": "精通编程或绘图技能", "score_range": [0, 100]},
                            {"name": "调试能力", "description": "能够解决复杂问题", "score_range": [0, 100]},
                            {"name": "技术架构", "description": "能够设计技术架构", "score_range": [0, 100]}
                        ]
                    },
                    "business_skills": {
                        "name": "业务能力",
                        "weight": 30,
                        "items": [
                            {"name": "需求理解", "description": "能够深入理解业务需求", "score_range": [0, 100]},
                            {"name": "方案设计", "description": "能够设计创新方案", "score_range": [0, 100]},
                            {"name": "业务洞察", "description": "具备业务洞察力", "score_range": [0, 100]}
                        ]
                    },
                    "communication_skills": {
                        "name": "沟通协作",
                        "weight": 15,
                        "items": [
                            {"name": "团队协作", "description": "能够领导团队协作", "score_range": [0, 100]},
                            {"name": "跨部门沟通", "description": "能够进行高效沟通", "score_range": [0, 100]},
                            {"name": "客户沟通", "description": "能够与客户沟通", "score_range": [0, 100]}
                        ]
                    },
                    "learning_skills": {
                        "name": "学习成长",
                        "weight": 10,
                        "items": [
                            {"name": "技术学习", "description": "持续学习前沿技术", "score_range": [0, 100]},
                            {"name": "知识分享", "description": "主动分享和传授知识", "score_range": [0, 100]},
                            {"name": "技术研究", "description": "进行技术研究", "score_range": [0, 100]}
                        ]
                    },
                    "project_management_skills": {
                        "name": "项目管理",
                        "weight": 15,
                        "items": [
                            {"name": "任务管理", "description": "能够管理复杂项目", "score_range": [0, 100]},
                            {"name": "进度控制", "description": "能够有效控制项目进度", "score_range": [0, 100]},
                            {"name": "风险管理", "description": "能够识别和管理风险", "score_range": [0, 100]}
                        ]
                    }
                }

            # 检查是否已存在
            existing = db.query(PositionCompetencyModel).filter(
                PositionCompetencyModel.position_type == 'ENGINEER',
                PositionCompetencyModel.position_subtype == subtype,
                PositionCompetencyModel.level_id == level.id
            ).first()

            if not existing:
                model = PositionCompetencyModel(
                    position_type='ENGINEER',
                    position_subtype=subtype,
                    level_id=level.id,
                    competency_dimensions=competency_dimensions,
                    is_active=True
                )
                db.add(model)
                print(f"创建能力模型: ENGINEER-{subtype} {level_code}")
            else:
                print(f"能力模型已存在: ENGINEER-{subtype} {level_code}")

    db.commit()


def create_sales_competency_models(db):
    """创建销售岗位能力模型"""
    levels = {level.level_code: level for level in db.query(QualificationLevel).all()}
    
    for level_code, level in levels.items():
        competency_dimensions = {
            "business_skills": {
                "name": "业务能力",
                "weight": 40,
                "items": [
                    {"name": "客户开发", "description": "开发新客户的能力", "score_range": [0, 100]},
                    {"name": "需求挖掘", "description": "挖掘客户需求", "score_range": [0, 100]},
                    {"name": "方案制定", "description": "制定销售方案", "score_range": [0, 100]}
                ]
            },
            "customer_service_skills": {
                "name": "客户服务",
                "weight": 30,
                "items": [
                    {"name": "客户关系维护", "description": "维护客户关系", "score_range": [0, 100]},
                    {"name": "客户满意度", "description": "提升客户满意度", "score_range": [0, 100]},
                    {"name": "售后服务", "description": "提供售后服务", "score_range": [0, 100]}
                ]
            },
            "communication_skills": {
                "name": "沟通协作",
                "weight": 20,
                "items": [
                    {"name": "沟通能力", "description": "与客户沟通的能力", "score_range": [0, 100]},
                    {"name": "谈判能力", "description": "商务谈判能力", "score_range": [0, 100]},
                    {"name": "团队协作", "description": "与内部团队协作", "score_range": [0, 100]}
                ]
            },
            "learning_skills": {
                "name": "学习成长",
                "weight": 10,
                "items": [
                    {"name": "产品学习", "description": "学习产品知识", "score_range": [0, 100]},
                    {"name": "市场学习", "description": "学习市场趋势", "score_range": [0, 100]}
                ]
            }
        }

        existing = db.query(PositionCompetencyModel).filter(
            PositionCompetencyModel.position_type == 'SALES',
            PositionCompetencyModel.level_id == level.id
        ).first()

        if not existing:
            model = PositionCompetencyModel(
                position_type='SALES',
                position_subtype=None,
                level_id=level.id,
                competency_dimensions=competency_dimensions,
                is_active=True
            )
            db.add(model)
            print(f"创建能力模型: SALES {level_code}")
        else:
            print(f"能力模型已存在: SALES {level_code}")

    db.commit()


def create_customer_service_competency_models(db):
    """创建客服岗位能力模型"""
    levels = {level.level_code: level for level in db.query(QualificationLevel).all()}
    
    for level_code, level in levels.items():
        competency_dimensions = {
            "customer_service_skills": {
                "name": "客户服务",
                "weight": 50,
                "items": [
                    {"name": "客户沟通", "description": "与客户有效沟通的能力", "score_range": [0, 100]},
                    {"name": "问题解决", "description": "解决客户问题的能力", "score_range": [0, 100]},
                    {"name": "客户满意度", "description": "提升客户满意度", "score_range": [0, 100]},
                    {"name": "投诉处理", "description": "处理客户投诉", "score_range": [0, 100]}
                ]
            },
            "business_skills": {
                "name": "业务能力",
                "weight": 25,
                "items": [
                    {"name": "产品知识", "description": "掌握产品知识", "score_range": [0, 100]},
                    {"name": "需求理解", "description": "理解客户需求", "score_range": [0, 100]},
                    {"name": "服务流程", "description": "熟悉服务流程", "score_range": [0, 100]}
                ]
            },
            "communication_skills": {
                "name": "沟通协作",
                "weight": 15,
                "items": [
                    {"name": "沟通技巧", "description": "掌握沟通技巧", "score_range": [0, 100]},
                    {"name": "团队协作", "description": "与团队协作", "score_range": [0, 100]},
                    {"name": "跨部门沟通", "description": "跨部门沟通协调", "score_range": [0, 100]}
                ]
            },
            "learning_skills": {
                "name": "学习成长",
                "weight": 10,
                "items": [
                    {"name": "业务学习", "description": "持续学习业务知识", "score_range": [0, 100]},
                    {"name": "技能提升", "description": "提升服务技能", "score_range": [0, 100]}
                ]
            }
        }

        existing = db.query(PositionCompetencyModel).filter(
            PositionCompetencyModel.position_type == 'CUSTOMER_SERVICE',
            PositionCompetencyModel.level_id == level.id
        ).first()

        if not existing:
            model = PositionCompetencyModel(
                position_type='CUSTOMER_SERVICE',
                position_subtype=None,
                level_id=level.id,
                competency_dimensions=competency_dimensions,
                is_active=True
            )
            db.add(model)
            print(f"创建能力模型: CUSTOMER_SERVICE {level_code}")
        else:
            print(f"能力模型已存在: CUSTOMER_SERVICE {level_code}")

    db.commit()


def create_worker_competency_models(db):
    """创建生产工人岗位能力模型"""
    levels = {level.level_code: level for level in db.query(QualificationLevel).all()}
    
    for level_code, level in levels.items():
        if level_code == 'ASSISTANT':
            competency_dimensions = {
                "technical_skills": {
                    "name": "专业技能",
                    "weight": 50,
                    "items": [
                        {"name": "基础操作", "description": "掌握基础操作技能", "score_range": [0, 100]},
                        {"name": "工具使用", "description": "正确使用工具", "score_range": [0, 100]},
                        {"name": "安全规范", "description": "遵守安全规范", "score_range": [0, 100]}
                    ]
                },
                "quality_skills": {
                    "name": "质量意识",
                    "weight": 30,
                    "items": [
                        {"name": "质量检查", "description": "进行质量检查", "score_range": [0, 100]},
                        {"name": "质量标准", "description": "了解质量标准", "score_range": [0, 100]}
                    ]
                },
                "efficiency_skills": {
                    "name": "效率能力",
                    "weight": 10,
                    "items": [
                        {"name": "工作效率", "description": "提高工作效率", "score_range": [0, 100]},
                        {"name": "时间管理", "description": "管理工作时间", "score_range": [0, 100]}
                    ]
                },
                "learning_skills": {
                    "name": "学习成长",
                    "weight": 10,
                    "items": [
                        {"name": "技能学习", "description": "学习新技能", "score_range": [0, 100]},
                        {"name": "经验积累", "description": "积累工作经验", "score_range": [0, 100]}
                    ]
                }
            }
        elif level_code == 'JUNIOR':
            competency_dimensions = {
                "technical_skills": {
                    "name": "专业技能",
                    "weight": 45,
                    "items": [
                        {"name": "操作技能", "description": "熟练掌握操作技能", "score_range": [0, 100]},
                        {"name": "工具使用", "description": "熟练使用工具", "score_range": [0, 100]},
                        {"name": "安全规范", "description": "严格遵守安全规范", "score_range": [0, 100]},
                        {"name": "设备维护", "description": "基础设备维护", "score_range": [0, 100]}
                    ]
                },
                "quality_skills": {
                    "name": "质量意识",
                    "weight": 30,
                    "items": [
                        {"name": "质量检查", "description": "独立进行质量检查", "score_range": [0, 100]},
                        {"name": "质量标准", "description": "掌握质量标准", "score_range": [0, 100]},
                        {"name": "问题识别", "description": "识别质量问题", "score_range": [0, 100]}
                    ]
                },
                "efficiency_skills": {
                    "name": "效率能力",
                    "weight": 15,
                    "items": [
                        {"name": "工作效率", "description": "保持较高工作效率", "score_range": [0, 100]},
                        {"name": "时间管理", "description": "有效管理时间", "score_range": [0, 100]},
                        {"name": "流程优化", "description": "参与流程优化", "score_range": [0, 100]}
                    ]
                },
                "learning_skills": {
                    "name": "学习成长",
                    "weight": 10,
                    "items": [
                        {"name": "技能学习", "description": "持续学习新技能", "score_range": [0, 100]},
                        {"name": "经验分享", "description": "分享工作经验", "score_range": [0, 100]}
                    ]
                }
            }
        else:  # MIDDLE, SENIOR, EXPERT
            competency_dimensions = {
                "technical_skills": {
                    "name": "专业技能",
                    "weight": 40,
                    "items": [
                        {"name": "操作技能", "description": "精通操作技能", "score_range": [0, 100]},
                        {"name": "工具使用", "description": "精通工具使用", "score_range": [0, 100]},
                        {"name": "安全规范", "description": "严格执行安全规范", "score_range": [0, 100]},
                        {"name": "设备维护", "description": "设备维护和故障排除", "score_range": [0, 100]},
                        {"name": "工艺改进", "description": "参与工艺改进", "score_range": [0, 100]}
                    ]
                },
                "quality_skills": {
                    "name": "质量意识",
                    "weight": 30,
                    "items": [
                        {"name": "质量检查", "description": "全面进行质量检查", "score_range": [0, 100]},
                        {"name": "质量标准", "description": "深入理解质量标准", "score_range": [0, 100]},
                        {"name": "问题识别", "description": "快速识别质量问题", "score_range": [0, 100]},
                        {"name": "质量改进", "description": "提出质量改进建议", "score_range": [0, 100]}
                    ]
                },
                "efficiency_skills": {
                    "name": "效率能力",
                    "weight": 20,
                    "items": [
                        {"name": "工作效率", "description": "保持高效率工作", "score_range": [0, 100]},
                        {"name": "时间管理", "description": "优秀的时间管理", "score_range": [0, 100]},
                        {"name": "流程优化", "description": "主导流程优化", "score_range": [0, 100]},
                        {"name": "团队协作", "description": "高效团队协作", "score_range": [0, 100]}
                    ]
                },
                "learning_skills": {
                    "name": "学习成长",
                    "weight": 10,
                    "items": [
                        {"name": "技能学习", "description": "持续学习前沿技能", "score_range": [0, 100]},
                        {"name": "经验分享", "description": "主动分享和传授经验", "score_range": [0, 100]},
                        {"name": "技能传承", "description": "培养新员工", "score_range": [0, 100]}
                    ]
                }
            }

        existing = db.query(PositionCompetencyModel).filter(
            PositionCompetencyModel.position_type == 'WORKER',
            PositionCompetencyModel.level_id == level.id
        ).first()

        if not existing:
            model = PositionCompetencyModel(
                position_type='WORKER',
                position_subtype=None,
                level_id=level.id,
                competency_dimensions=competency_dimensions,
                is_active=True
            )
            db.add(model)
            print(f"创建能力模型: WORKER {level_code}")
        else:
            print(f"能力模型已存在: WORKER {level_code}")

    db.commit()


def main():
    """主函数"""
    print("开始创建任职资格体系种子数据...")
    
    # 初始化数据库
    init_db()
    
    # 获取数据库会话
    with get_session() as db:
        try:
            # 创建等级
            print("\n1. 创建任职资格等级...")
            create_qualification_levels(db)
            
            # 创建工程师能力模型
            print("\n2. 创建工程师岗位能力模型...")
            create_engineer_competency_models(db)
            
            # 创建销售能力模型
            print("\n3. 创建销售岗位能力模型...")
            create_sales_competency_models(db)
            
            # 创建客服能力模型
            print("\n4. 创建客服岗位能力模型...")
            create_customer_service_competency_models(db)
            
            # 创建生产工人能力模型
            print("\n5. 创建生产工人岗位能力模型...")
            create_worker_competency_models(db)
            
            print("\n任职资格体系种子数据创建完成！")
            
        except Exception as e:
            db.rollback()
            print(f"错误: {e}")
            raise


if __name__ == "__main__":
    main()

