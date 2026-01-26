# -*- coding: utf-8 -*-
"""
阶段模板种子数据

创建预置的阶段模板：
- full_lifecycle_22: 完整22阶段流程（销售→售前→执行→收尾）
- standard_9: 标准9阶段（兼容现有S1-S9）
- quick_5: 快速开发5阶段（重复产品）
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session

from app.models.base import SessionLocal
from app.models.stage_template import NodeDefinition, StageDefinition, StageTemplate
from app.models.enums import (
    CompletionMethodEnum,
    NodeTypeEnum,
    StageCategoryEnum,
    TemplateProjectTypeEnum,
)


# ==================== 完整22阶段模板 ====================

FULL_LIFECYCLE_22 = {
    "template_code": "full_lifecycle_22",
    "template_name": "完整22阶段流程",
    "description": "适用于全新产品的完整项目生命周期管理，包含销售、售前、执行、收尾四大类共22个阶段",
    "project_type": TemplateProjectTypeEnum.NEW.value,
    "is_default": True,
    "stages": [
        # === 销售阶段 (1-4) ===
        {
            "stage_code": "S01",
            "stage_name": "市场开拓",
            "sequence": 1,
            "category": StageCategoryEnum.SALES.value,
            "estimated_days": 30,
            "is_milestone": False,
            "nodes": [
                {"node_code": "S01.1", "node_name": "市场调研", "node_type": NodeTypeEnum.TASK.value},
                {"node_code": "S01.2", "node_name": "客户拜访", "node_type": NodeTypeEnum.TASK.value},
                {"node_code": "S01.3", "node_name": "需求收集", "node_type": NodeTypeEnum.DELIVERABLE.value},
            ],
        },
        {
            "stage_code": "S02",
            "stage_name": "线索获取",
            "sequence": 2,
            "category": StageCategoryEnum.SALES.value,
            "estimated_days": 14,
            "nodes": [
                {"node_code": "S02.1", "node_name": "线索登记", "node_type": NodeTypeEnum.TASK.value},
                {"node_code": "S02.2", "node_name": "初步评估", "node_type": NodeTypeEnum.TASK.value},
            ],
        },
        {
            "stage_code": "S03",
            "stage_name": "商机培育",
            "sequence": 3,
            "category": StageCategoryEnum.SALES.value,
            "estimated_days": 30,
            "nodes": [
                {"node_code": "S03.1", "node_name": "方案沟通", "node_type": NodeTypeEnum.TASK.value},
                {"node_code": "S03.2", "node_name": "商务洽谈", "node_type": NodeTypeEnum.TASK.value},
            ],
        },
        {
            "stage_code": "S04",
            "stage_name": "需求评审",
            "sequence": 4,
            "category": StageCategoryEnum.SALES.value,
            "estimated_days": 7,
            "is_milestone": True,
            "nodes": [
                {"node_code": "S04.1", "node_name": "需求文档编写", "node_type": NodeTypeEnum.DELIVERABLE.value},
                {"node_code": "S04.2", "node_name": "需求评审会议", "node_type": NodeTypeEnum.APPROVAL.value},
            ],
        },
        # === 售前阶段 (5-8) ===
        {
            "stage_code": "S05",
            "stage_name": "初立项",
            "sequence": 5,
            "category": StageCategoryEnum.PRESALES.value,
            "estimated_days": 3,
            "is_milestone": True,
            "nodes": [
                {"node_code": "S05.1", "node_name": "初立项申请", "node_type": NodeTypeEnum.DELIVERABLE.value},
                {"node_code": "S05.2", "node_name": "初立项审批", "node_type": NodeTypeEnum.APPROVAL.value},
            ],
        },
        {
            "stage_code": "S06",
            "stage_name": "售前方案",
            "sequence": 6,
            "category": StageCategoryEnum.PRESALES.value,
            "estimated_days": 14,
            "nodes": [
                {"node_code": "S06.1", "node_name": "技术方案设计", "node_type": NodeTypeEnum.DELIVERABLE.value},
                {"node_code": "S06.2", "node_name": "方案内部评审", "node_type": NodeTypeEnum.APPROVAL.value},
                {"node_code": "S06.3", "node_name": "客户方案讲解", "node_type": NodeTypeEnum.TASK.value},
            ],
        },
        {
            "stage_code": "S07",
            "stage_name": "报价投标",
            "sequence": 7,
            "category": StageCategoryEnum.PRESALES.value,
            "estimated_days": 14,
            "nodes": [
                {"node_code": "S07.1", "node_name": "成本核算", "node_type": NodeTypeEnum.TASK.value},
                {"node_code": "S07.2", "node_name": "报价审批", "node_type": NodeTypeEnum.APPROVAL.value},
                {"node_code": "S07.3", "node_name": "投标文件编制", "node_type": NodeTypeEnum.DELIVERABLE.value},
            ],
        },
        {
            "stage_code": "S08",
            "stage_name": "合同签订",
            "sequence": 8,
            "category": StageCategoryEnum.PRESALES.value,
            "estimated_days": 7,
            "is_milestone": True,
            "nodes": [
                {"node_code": "S08.1", "node_name": "合同条款确认", "node_type": NodeTypeEnum.TASK.value},
                {"node_code": "S08.2", "node_name": "合同审批", "node_type": NodeTypeEnum.APPROVAL.value},
                {"node_code": "S08.3", "node_name": "合同签署", "node_type": NodeTypeEnum.DELIVERABLE.value},
            ],
        },
        # === 执行阶段 (9-20) ===
        {
            "stage_code": "S09",
            "stage_name": "正式立项",
            "sequence": 9,
            "category": StageCategoryEnum.EXECUTION.value,
            "estimated_days": 3,
            "is_milestone": True,
            "nodes": [
                {"node_code": "S09.1", "node_name": "项目启动会", "node_type": NodeTypeEnum.TASK.value},
                {"node_code": "S09.2", "node_name": "立项审批", "node_type": NodeTypeEnum.APPROVAL.value},
            ],
        },
        {
            "stage_code": "S10",
            "stage_name": "方案设计",
            "sequence": 10,
            "category": StageCategoryEnum.EXECUTION.value,
            "estimated_days": 14,
            "nodes": [
                {"node_code": "S10.1", "node_name": "总体方案设计", "node_type": NodeTypeEnum.DELIVERABLE.value},
                {"node_code": "S10.2", "node_name": "方案评审", "node_type": NodeTypeEnum.APPROVAL.value},
            ],
        },
        {
            "stage_code": "S11",
            "stage_name": "详细设计",
            "sequence": 11,
            "category": StageCategoryEnum.EXECUTION.value,
            "estimated_days": 21,
            "nodes": [
                {"node_code": "S11.1", "node_name": "机械详细设计", "node_type": NodeTypeEnum.DELIVERABLE.value},
                {"node_code": "S11.2", "node_name": "电气详细设计", "node_type": NodeTypeEnum.DELIVERABLE.value},
                {"node_code": "S11.3", "node_name": "软件详细设计", "node_type": NodeTypeEnum.DELIVERABLE.value},
                {"node_code": "S11.4", "node_name": "设计评审", "node_type": NodeTypeEnum.APPROVAL.value},
            ],
        },
        {
            "stage_code": "S12",
            "stage_name": "采购外协",
            "sequence": 12,
            "category": StageCategoryEnum.EXECUTION.value,
            "estimated_days": 30,
            "nodes": [
                {"node_code": "S12.1", "node_name": "BOM发布", "node_type": NodeTypeEnum.TASK.value},
                {"node_code": "S12.2", "node_name": "采购下单", "node_type": NodeTypeEnum.TASK.value},
                {"node_code": "S12.3", "node_name": "外协下单", "node_type": NodeTypeEnum.TASK.value},
                {"node_code": "S12.4", "node_name": "物料到货检验", "node_type": NodeTypeEnum.TASK.value},
            ],
        },
        {
            "stage_code": "S13",
            "stage_name": "机械装配",
            "sequence": 13,
            "category": StageCategoryEnum.EXECUTION.value,
            "estimated_days": 21,
            "nodes": [
                {"node_code": "S13.1", "node_name": "结构件装配", "node_type": NodeTypeEnum.TASK.value},
                {"node_code": "S13.2", "node_name": "机械调试", "node_type": NodeTypeEnum.TASK.value},
            ],
        },
        {
            "stage_code": "S14",
            "stage_name": "电气装配",
            "sequence": 14,
            "category": StageCategoryEnum.EXECUTION.value,
            "estimated_days": 14,
            "nodes": [
                {"node_code": "S14.1", "node_name": "布线安装", "node_type": NodeTypeEnum.TASK.value},
                {"node_code": "S14.2", "node_name": "电气调试", "node_type": NodeTypeEnum.TASK.value},
            ],
        },
        {
            "stage_code": "S15",
            "stage_name": "软件开发",
            "sequence": 15,
            "category": StageCategoryEnum.EXECUTION.value,
            "estimated_days": 30,
            "is_parallel": True,
            "nodes": [
                {"node_code": "S15.1", "node_name": "程序编写", "node_type": NodeTypeEnum.TASK.value},
                {"node_code": "S15.2", "node_name": "单元测试", "node_type": NodeTypeEnum.TASK.value},
                {"node_code": "S15.3", "node_name": "代码评审", "node_type": NodeTypeEnum.APPROVAL.value},
            ],
        },
        {
            "stage_code": "S16",
            "stage_name": "整机联调",
            "sequence": 16,
            "category": StageCategoryEnum.EXECUTION.value,
            "estimated_days": 14,
            "nodes": [
                {"node_code": "S16.1", "node_name": "机电联调", "node_type": NodeTypeEnum.TASK.value},
                {"node_code": "S16.2", "node_name": "功能验证", "node_type": NodeTypeEnum.TASK.value},
            ],
        },
        {
            "stage_code": "S17",
            "stage_name": "内部验收",
            "sequence": 17,
            "category": StageCategoryEnum.EXECUTION.value,
            "estimated_days": 7,
            "is_milestone": True,
            "nodes": [
                {"node_code": "S17.1", "node_name": "内部测试", "node_type": NodeTypeEnum.TASK.value},
                {"node_code": "S17.2", "node_name": "问题整改", "node_type": NodeTypeEnum.TASK.value},
                {"node_code": "S17.3", "node_name": "内部验收签字", "node_type": NodeTypeEnum.APPROVAL.value},
            ],
        },
        {
            "stage_code": "S18",
            "stage_name": "出厂发运",
            "sequence": 18,
            "category": StageCategoryEnum.EXECUTION.value,
            "estimated_days": 7,
            "nodes": [
                {"node_code": "S18.1", "node_name": "包装清点", "node_type": NodeTypeEnum.TASK.value},
                {"node_code": "S18.2", "node_name": "物流安排", "node_type": NodeTypeEnum.TASK.value},
                {"node_code": "S18.3", "node_name": "发货确认", "node_type": NodeTypeEnum.DELIVERABLE.value},
            ],
        },
        {
            "stage_code": "S19",
            "stage_name": "现场安装",
            "sequence": 19,
            "category": StageCategoryEnum.EXECUTION.value,
            "estimated_days": 14,
            "nodes": [
                {"node_code": "S19.1", "node_name": "设备就位", "node_type": NodeTypeEnum.TASK.value},
                {"node_code": "S19.2", "node_name": "安装调试", "node_type": NodeTypeEnum.TASK.value},
                {"node_code": "S19.3", "node_name": "人员培训", "node_type": NodeTypeEnum.TASK.value},
            ],
        },
        {
            "stage_code": "S20",
            "stage_name": "客户验收",
            "sequence": 20,
            "category": StageCategoryEnum.EXECUTION.value,
            "estimated_days": 7,
            "is_milestone": True,
            "nodes": [
                {"node_code": "S20.1", "node_name": "验收测试", "node_type": NodeTypeEnum.TASK.value},
                {"node_code": "S20.2", "node_name": "问题整改", "node_type": NodeTypeEnum.TASK.value},
                {"node_code": "S20.3", "node_name": "验收签字", "node_type": NodeTypeEnum.APPROVAL.value},
            ],
        },
        # === 收尾阶段 (21-22) ===
        {
            "stage_code": "S21",
            "stage_name": "项目收尾",
            "sequence": 21,
            "category": StageCategoryEnum.CLOSURE.value,
            "estimated_days": 14,
            "nodes": [
                {"node_code": "S21.1", "node_name": "项目总结", "node_type": NodeTypeEnum.DELIVERABLE.value},
                {"node_code": "S21.2", "node_name": "经验沉淀", "node_type": NodeTypeEnum.TASK.value},
                {"node_code": "S21.3", "node_name": "项目结项审批", "node_type": NodeTypeEnum.APPROVAL.value},
            ],
        },
        {
            "stage_code": "S22",
            "stage_name": "质保服务",
            "sequence": 22,
            "category": StageCategoryEnum.CLOSURE.value,
            "estimated_days": 365,
            "nodes": [
                {"node_code": "S22.1", "node_name": "质保期服务", "node_type": NodeTypeEnum.TASK.value},
                {"node_code": "S22.2", "node_name": "质保期结束确认", "node_type": NodeTypeEnum.APPROVAL.value},
            ],
        },
    ],
}


# ==================== 标准9阶段模板 ====================

STANDARD_9 = {
    "template_code": "standard_9",
    "template_name": "标准9阶段（兼容）",
    "description": "兼容现有S1-S9阶段定义，适用于快速交付项目",
    "project_type": TemplateProjectTypeEnum.CUSTOM.value,
    "is_default": True,
    "stages": [
        {"stage_code": "S1", "stage_name": "需求进入", "sequence": 1, "category": StageCategoryEnum.PRESALES.value, "estimated_days": 7},
        {"stage_code": "S2", "stage_name": "方案设计", "sequence": 2, "category": StageCategoryEnum.PRESALES.value, "estimated_days": 14, "is_milestone": True},
        {"stage_code": "S3", "stage_name": "采购备料", "sequence": 3, "category": StageCategoryEnum.EXECUTION.value, "estimated_days": 21},
        {"stage_code": "S4", "stage_name": "加工制造", "sequence": 4, "category": StageCategoryEnum.EXECUTION.value, "estimated_days": 30},
        {"stage_code": "S5", "stage_name": "装配调试", "sequence": 5, "category": StageCategoryEnum.EXECUTION.value, "estimated_days": 21},
        {"stage_code": "S6", "stage_name": "出厂验收", "sequence": 6, "category": StageCategoryEnum.EXECUTION.value, "estimated_days": 7, "is_milestone": True},
        {"stage_code": "S7", "stage_name": "包装发运", "sequence": 7, "category": StageCategoryEnum.EXECUTION.value, "estimated_days": 7},
        {"stage_code": "S8", "stage_name": "现场安装", "sequence": 8, "category": StageCategoryEnum.EXECUTION.value, "estimated_days": 14},
        {"stage_code": "S9", "stage_name": "质保结项", "sequence": 9, "category": StageCategoryEnum.CLOSURE.value, "estimated_days": 365, "is_milestone": True},
    ],
}


# ==================== 快速5阶段模板 ====================

QUICK_5 = {
    "template_code": "quick_5",
    "template_name": "快速5阶段（重复产品）",
    "description": "适用于重复生产的标准产品，跳过设计阶段",
    "project_type": TemplateProjectTypeEnum.REPEAT.value,
    "is_default": True,
    "stages": [
        {"stage_code": "Q1", "stage_name": "订单确认", "sequence": 1, "category": StageCategoryEnum.PRESALES.value, "estimated_days": 3, "is_milestone": True},
        {"stage_code": "Q2", "stage_name": "生产制造", "sequence": 2, "category": StageCategoryEnum.EXECUTION.value, "estimated_days": 21},
        {"stage_code": "Q3", "stage_name": "测试验收", "sequence": 3, "category": StageCategoryEnum.EXECUTION.value, "estimated_days": 7, "is_milestone": True},
        {"stage_code": "Q4", "stage_name": "发货交付", "sequence": 4, "category": StageCategoryEnum.EXECUTION.value, "estimated_days": 7},
        {"stage_code": "Q5", "stage_name": "售后质保", "sequence": 5, "category": StageCategoryEnum.CLOSURE.value, "estimated_days": 180},
    ],
}


def create_template(db: Session, template_data: dict) -> StageTemplate:
    """创建单个模板及其阶段和节点"""
    # 检查是否已存在
    existing = db.query(StageTemplate).filter(
        StageTemplate.template_code == template_data["template_code"]
    ).first()

    if existing:
        print(f"  模板 {template_data['template_code']} 已存在，跳过")
        return existing

    # 创建模板
    template = StageTemplate(
        template_code=template_data["template_code"],
        template_name=template_data["template_name"],
        description=template_data.get("description"),
        project_type=template_data.get("project_type", TemplateProjectTypeEnum.CUSTOM.value),
        is_default=template_data.get("is_default", False),
    )
    db.add(template)
    db.flush()

    # 创建阶段
    stages_data = template_data.get("stages", [])
    for stage_data in stages_data:
        stage = StageDefinition(
            template_id=template.id,
            stage_code=stage_data["stage_code"],
            stage_name=stage_data["stage_name"],
            sequence=stage_data["sequence"],
            category=stage_data.get("category", StageCategoryEnum.EXECUTION.value),
            estimated_days=stage_data.get("estimated_days"),
            is_required=stage_data.get("is_required", True),
            is_milestone=stage_data.get("is_milestone", False),
            is_parallel=stage_data.get("is_parallel", False),
        )
        db.add(stage)
        db.flush()

        # 创建节点
        nodes_data = stage_data.get("nodes", [])
        for i, node_data in enumerate(nodes_data):
            node = NodeDefinition(
                stage_definition_id=stage.id,
                node_code=node_data["node_code"],
                node_name=node_data["node_name"],
                node_type=node_data.get("node_type", NodeTypeEnum.TASK.value),
                sequence=i + 1,
                completion_method=node_data.get("completion_method", CompletionMethodEnum.MANUAL.value),
                is_required=node_data.get("is_required", True),
            )
            db.add(node)

    print(f"  ✓ 创建模板: {template.template_code} - {template.template_name}")
    print(f"    阶段数: {len(stages_data)}")

    return template


def seed_templates(db: Session):
    """种子数据入口"""
    print("开始初始化阶段模板...")

    templates = [FULL_LIFECYCLE_22, STANDARD_9, QUICK_5]

    for template_data in templates:
        create_template(db, template_data)

    db.commit()
    print("\n模板初始化完成!")


def main():
    """主函数"""
    db = SessionLocal()
    try:
        seed_templates(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
