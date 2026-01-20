# -*- coding: utf-8 -*-
"""
预置阶段模板数据

包含三个初始模板：
1. TPL_STANDARD - 标准全流程（新产品完整流程）
2. TPL_QUICK - 简易快速开发（简单新产品）
3. TPL_REPEAT - 重复生产（老产品复制）
"""

from typing import Any, Dict, List

# 标准全流程模板（9大阶段）
STANDARD_TEMPLATE: Dict[str, Any] = {
    "template_code": "TPL_STANDARD",
    "template_name": "标准全流程",
    "description": "适用于新产品开发的完整流程，包含售前支持、方案设计、采购、生产、调试、验收、交付全过程",
    "project_type": "NEW",
    "stages": [
        {
            "stage_code": "S1",
            "stage_name": "需求进入",
            "sequence": 0,
            "estimated_days": 7,
            "description": "接收客户需求，评估可行性",
            "is_required": True,
            "nodes": [
                {
                    "node_code": "S1N01",
                    "node_name": "需求接收登记",
                    "node_type": "TASK",
                    "sequence": 0,
                    "estimated_days": 1,
                    "completion_method": "MANUAL",
                    "is_required": True,
                    "description": "登记客户需求基本信息",
                },
                {
                    "node_code": "S1N02",
                    "node_name": "技术可行性评估",
                    "node_type": "TASK",
                    "sequence": 1,
                    "estimated_days": 3,
                    "completion_method": "MANUAL",
                    "is_required": True,
                    "description": "评估技术实现可行性",
                },
                {
                    "node_code": "S1N03",
                    "node_name": "商务报价",
                    "node_type": "TASK",
                    "sequence": 2,
                    "estimated_days": 2,
                    "completion_method": "MANUAL",
                    "is_required": True,
                    "description": "编制项目报价",
                },
                {
                    "node_code": "S1N04",
                    "node_name": "合同签订确认",
                    "node_type": "APPROVAL",
                    "sequence": 3,
                    "estimated_days": 1,
                    "completion_method": "APPROVAL",
                    "is_required": True,
                    "description": "确认合同签订",
                    "dependency_node_codes": ["S1N03"],
                },
            ]
        },
        {
            "stage_code": "S2",
            "stage_name": "方案设计",
            "sequence": 1,
            "estimated_days": 14,
            "description": "完成整体方案设计与技术评审",
            "is_required": True,
            "nodes": [
                {
                    "node_code": "S2N01",
                    "node_name": "需求澄清会议",
                    "node_type": "TASK",
                    "sequence": 0,
                    "estimated_days": 1,
                    "completion_method": "MANUAL",
                    "is_required": True,
                    "description": "与客户确认详细需求",
                },
                {
                    "node_code": "S2N02",
                    "node_name": "整体方案设计",
                    "node_type": "TASK",
                    "sequence": 1,
                    "estimated_days": 5,
                    "completion_method": "MANUAL",
                    "is_required": True,
                    "description": "编制整体技术方案",
                    "dependency_node_codes": ["S2N01"],
                },
                {
                    "node_code": "S2N03",
                    "node_name": "机械结构设计",
                    "node_type": "DELIVERABLE",
                    "sequence": 2,
                    "estimated_days": 5,
                    "completion_method": "UPLOAD",
                    "is_required": True,
                    "required_attachments": True,
                    "description": "完成机械结构设计图纸",
                    "dependency_node_codes": ["S2N02"],
                },
                {
                    "node_code": "S2N04",
                    "node_name": "电气设计",
                    "node_type": "DELIVERABLE",
                    "sequence": 3,
                    "estimated_days": 5,
                    "completion_method": "UPLOAD",
                    "is_required": True,
                    "required_attachments": True,
                    "description": "完成电气原理图和接线图",
                    "dependency_node_codes": ["S2N02"],
                },
                {
                    "node_code": "S2N05",
                    "node_name": "技术评审",
                    "node_type": "APPROVAL",
                    "sequence": 4,
                    "estimated_days": 1,
                    "completion_method": "APPROVAL",
                    "is_required": True,
                    "description": "技术方案评审通过",
                    "dependency_node_codes": ["S2N03", "S2N04"],
                },
            ]
        },
        {
            "stage_code": "S3",
            "stage_name": "采购备料",
            "sequence": 2,
            "estimated_days": 21,
            "description": "BOM确认和物料采购",
            "is_required": True,
            "nodes": [
                {
                    "node_code": "S3N01",
                    "node_name": "BOM编制",
                    "node_type": "DELIVERABLE",
                    "sequence": 0,
                    "estimated_days": 3,
                    "completion_method": "UPLOAD",
                    "is_required": True,
                    "required_attachments": True,
                    "description": "编制物料清单",
                },
                {
                    "node_code": "S3N02",
                    "node_name": "BOM评审",
                    "node_type": "APPROVAL",
                    "sequence": 1,
                    "estimated_days": 1,
                    "completion_method": "APPROVAL",
                    "is_required": True,
                    "description": "物料清单评审确认",
                    "dependency_node_codes": ["S3N01"],
                },
                {
                    "node_code": "S3N03",
                    "node_name": "采购申请",
                    "node_type": "TASK",
                    "sequence": 2,
                    "estimated_days": 1,
                    "completion_method": "MANUAL",
                    "is_required": True,
                    "description": "提交采购申请",
                    "dependency_node_codes": ["S3N02"],
                },
                {
                    "node_code": "S3N04",
                    "node_name": "供应商选择",
                    "node_type": "TASK",
                    "sequence": 3,
                    "estimated_days": 2,
                    "completion_method": "MANUAL",
                    "is_required": True,
                    "description": "选择供应商并下单",
                    "dependency_node_codes": ["S3N03"],
                },
                {
                    "node_code": "S3N05",
                    "node_name": "物料到货验收",
                    "node_type": "TASK",
                    "sequence": 4,
                    "estimated_days": 14,
                    "completion_method": "MANUAL",
                    "is_required": True,
                    "description": "物料到货并完成验收",
                    "dependency_node_codes": ["S3N04"],
                },
            ]
        },
        {
            "stage_code": "S4",
            "stage_name": "加工制造",
            "sequence": 3,
            "estimated_days": 21,
            "description": "机械加工和外协管理",
            "is_required": True,
            "nodes": [
                {
                    "node_code": "S4N01",
                    "node_name": "加工图纸发放",
                    "node_type": "TASK",
                    "sequence": 0,
                    "estimated_days": 1,
                    "completion_method": "MANUAL",
                    "is_required": True,
                    "description": "发放加工图纸给车间/外协",
                },
                {
                    "node_code": "S4N02",
                    "node_name": "自制件加工",
                    "node_type": "TASK",
                    "sequence": 1,
                    "estimated_days": 10,
                    "completion_method": "MANUAL",
                    "is_required": True,
                    "description": "内部加工自制零件",
                    "dependency_node_codes": ["S4N01"],
                },
                {
                    "node_code": "S4N03",
                    "node_name": "外协件加工",
                    "node_type": "TASK",
                    "sequence": 2,
                    "estimated_days": 14,
                    "completion_method": "MANUAL",
                    "is_required": False,
                    "description": "外协加工零件",
                    "dependency_node_codes": ["S4N01"],
                },
                {
                    "node_code": "S4N04",
                    "node_name": "零件检验入库",
                    "node_type": "TASK",
                    "sequence": 3,
                    "estimated_days": 2,
                    "completion_method": "MANUAL",
                    "is_required": True,
                    "description": "零件检验合格入库",
                    "dependency_node_codes": ["S4N02"],
                },
            ]
        },
        {
            "stage_code": "S5",
            "stage_name": "装配调试",
            "sequence": 4,
            "estimated_days": 14,
            "description": "设备装配和调试验证",
            "is_required": True,
            "nodes": [
                {
                    "node_code": "S5N01",
                    "node_name": "机械装配",
                    "node_type": "TASK",
                    "sequence": 0,
                    "estimated_days": 5,
                    "completion_method": "MANUAL",
                    "is_required": True,
                    "description": "完成机械部分装配",
                },
                {
                    "node_code": "S5N02",
                    "node_name": "电气接线",
                    "node_type": "TASK",
                    "sequence": 1,
                    "estimated_days": 3,
                    "completion_method": "MANUAL",
                    "is_required": True,
                    "description": "完成电气接线安装",
                    "dependency_node_codes": ["S5N01"],
                },
                {
                    "node_code": "S5N03",
                    "node_name": "程序调试",
                    "node_type": "TASK",
                    "sequence": 2,
                    "estimated_days": 4,
                    "completion_method": "MANUAL",
                    "is_required": True,
                    "description": "软件程序调试",
                    "dependency_node_codes": ["S5N02"],
                },
                {
                    "node_code": "S5N04",
                    "node_name": "联调测试",
                    "node_type": "TASK",
                    "sequence": 3,
                    "estimated_days": 2,
                    "completion_method": "MANUAL",
                    "is_required": True,
                    "description": "整机联调测试",
                    "dependency_node_codes": ["S5N03"],
                },
            ]
        },
        {
            "stage_code": "S6",
            "stage_name": "出厂验收",
            "sequence": 5,
            "estimated_days": 3,
            "description": "FAT出厂验收测试",
            "is_required": True,
            "nodes": [
                {
                    "node_code": "S6N01",
                    "node_name": "内部预验收",
                    "node_type": "TASK",
                    "sequence": 0,
                    "estimated_days": 1,
                    "completion_method": "MANUAL",
                    "is_required": True,
                    "description": "内部预验收检查",
                },
                {
                    "node_code": "S6N02",
                    "node_name": "客户FAT验收",
                    "node_type": "APPROVAL",
                    "sequence": 1,
                    "estimated_days": 1,
                    "completion_method": "APPROVAL",
                    "is_required": True,
                    "description": "客户出厂验收",
                    "dependency_node_codes": ["S6N01"],
                },
                {
                    "node_code": "S6N03",
                    "node_name": "FAT报告签署",
                    "node_type": "DELIVERABLE",
                    "sequence": 2,
                    "estimated_days": 1,
                    "completion_method": "UPLOAD",
                    "is_required": True,
                    "required_attachments": True,
                    "description": "FAT验收报告签署",
                    "dependency_node_codes": ["S6N02"],
                },
            ]
        },
        {
            "stage_code": "S7",
            "stage_name": "包装发运",
            "sequence": 6,
            "estimated_days": 3,
            "description": "设备包装和发货",
            "is_required": True,
            "nodes": [
                {
                    "node_code": "S7N01",
                    "node_name": "设备包装",
                    "node_type": "TASK",
                    "sequence": 0,
                    "estimated_days": 1,
                    "completion_method": "MANUAL",
                    "is_required": True,
                    "description": "设备包装入箱",
                },
                {
                    "node_code": "S7N02",
                    "node_name": "发货安排",
                    "node_type": "TASK",
                    "sequence": 1,
                    "estimated_days": 1,
                    "completion_method": "MANUAL",
                    "is_required": True,
                    "description": "安排物流发货",
                    "dependency_node_codes": ["S7N01"],
                },
                {
                    "node_code": "S7N03",
                    "node_name": "发货确认",
                    "node_type": "TASK",
                    "sequence": 2,
                    "estimated_days": 1,
                    "completion_method": "MANUAL",
                    "is_required": True,
                    "description": "确认发货到达",
                    "dependency_node_codes": ["S7N02"],
                },
            ]
        },
        {
            "stage_code": "S8",
            "stage_name": "现场安装",
            "sequence": 7,
            "estimated_days": 7,
            "description": "现场安装调试和SAT验收",
            "is_required": True,
            "nodes": [
                {
                    "node_code": "S8N01",
                    "node_name": "现场安装",
                    "node_type": "TASK",
                    "sequence": 0,
                    "estimated_days": 2,
                    "completion_method": "MANUAL",
                    "is_required": True,
                    "description": "现场设备安装",
                },
                {
                    "node_code": "S8N02",
                    "node_name": "现场调试",
                    "node_type": "TASK",
                    "sequence": 1,
                    "estimated_days": 3,
                    "completion_method": "MANUAL",
                    "is_required": True,
                    "description": "现场设备调试",
                    "dependency_node_codes": ["S8N01"],
                },
                {
                    "node_code": "S8N03",
                    "node_name": "客户SAT验收",
                    "node_type": "APPROVAL",
                    "sequence": 2,
                    "estimated_days": 1,
                    "completion_method": "APPROVAL",
                    "is_required": True,
                    "description": "客户现场验收",
                    "dependency_node_codes": ["S8N02"],
                },
                {
                    "node_code": "S8N04",
                    "node_name": "SAT报告签署",
                    "node_type": "DELIVERABLE",
                    "sequence": 3,
                    "estimated_days": 1,
                    "completion_method": "UPLOAD",
                    "is_required": True,
                    "required_attachments": True,
                    "description": "SAT验收报告签署",
                    "dependency_node_codes": ["S8N03"],
                },
            ]
        },
        {
            "stage_code": "S9",
            "stage_name": "质保结项",
            "sequence": 8,
            "estimated_days": 7,
            "description": "项目收尾和质保交接",
            "is_required": True,
            "nodes": [
                {
                    "node_code": "S9N01",
                    "node_name": "项目文档归档",
                    "node_type": "DELIVERABLE",
                    "sequence": 0,
                    "estimated_days": 2,
                    "completion_method": "UPLOAD",
                    "is_required": True,
                    "required_attachments": True,
                    "description": "整理归档项目文档",
                },
                {
                    "node_code": "S9N02",
                    "node_name": "客户培训",
                    "node_type": "TASK",
                    "sequence": 1,
                    "estimated_days": 2,
                    "completion_method": "MANUAL",
                    "is_required": False,
                    "description": "客户操作培训",
                },
                {
                    "node_code": "S9N03",
                    "node_name": "质保交接",
                    "node_type": "TASK",
                    "sequence": 2,
                    "estimated_days": 1,
                    "completion_method": "MANUAL",
                    "is_required": True,
                    "description": "移交售后质保服务",
                    "dependency_node_codes": ["S9N01"],
                },
                {
                    "node_code": "S9N04",
                    "node_name": "项目结项审批",
                    "node_type": "APPROVAL",
                    "sequence": 3,
                    "estimated_days": 1,
                    "completion_method": "APPROVAL",
                    "is_required": True,
                    "description": "项目结项审批确认",
                    "dependency_node_codes": ["S9N03"],
                },
                {
                    "node_code": "S9N05",
                    "node_name": "经验总结",
                    "node_type": "TASK",
                    "sequence": 4,
                    "estimated_days": 1,
                    "completion_method": "MANUAL",
                    "is_required": False,
                    "description": "项目经验总结归档",
                },
            ]
        },
    ]
}

# 简易快速开发模板（简化流程）
QUICK_TEMPLATE: Dict[str, Any] = {
    "template_code": "TPL_QUICK",
    "template_name": "简易快速开发",
    "description": "适用于简单新产品或小型改造项目，精简流程快速交付",
    "project_type": "SIMPLE",
    "stages": [
        {
            "stage_code": "Q1",
            "stage_name": "立项启动",
            "sequence": 0,
            "estimated_days": 3,
            "description": "快速立项和需求确认",
            "is_required": True,
            "nodes": [
                {
                    "node_code": "Q1N01",
                    "node_name": "需求确认",
                    "node_type": "TASK",
                    "sequence": 0,
                    "estimated_days": 1,
                    "completion_method": "MANUAL",
                    "is_required": True,
                    "description": "确认客户需求",
                },
                {
                    "node_code": "Q1N02",
                    "node_name": "快速方案",
                    "node_type": "TASK",
                    "sequence": 1,
                    "estimated_days": 2,
                    "completion_method": "MANUAL",
                    "is_required": True,
                    "description": "编制简易技术方案",
                    "dependency_node_codes": ["Q1N01"],
                },
            ]
        },
        {
            "stage_code": "Q2",
            "stage_name": "物料准备",
            "sequence": 1,
            "estimated_days": 14,
            "description": "物料采购和准备",
            "is_required": True,
            "nodes": [
                {
                    "node_code": "Q2N01",
                    "node_name": "BOM编制",
                    "node_type": "TASK",
                    "sequence": 0,
                    "estimated_days": 1,
                    "completion_method": "MANUAL",
                    "is_required": True,
                    "description": "编制物料清单",
                },
                {
                    "node_code": "Q2N02",
                    "node_name": "采购下单",
                    "node_type": "TASK",
                    "sequence": 1,
                    "estimated_days": 1,
                    "completion_method": "MANUAL",
                    "is_required": True,
                    "description": "采购物料下单",
                    "dependency_node_codes": ["Q2N01"],
                },
                {
                    "node_code": "Q2N03",
                    "node_name": "物���齐套",
                    "node_type": "TASK",
                    "sequence": 2,
                    "estimated_days": 12,
                    "completion_method": "MANUAL",
                    "is_required": True,
                    "description": "物料到齐确认",
                    "dependency_node_codes": ["Q2N02"],
                },
            ]
        },
        {
            "stage_code": "Q3",
            "stage_name": "生产装配",
            "sequence": 2,
            "estimated_days": 10,
            "description": "生产装配和调试",
            "is_required": True,
            "nodes": [
                {
                    "node_code": "Q3N01",
                    "node_name": "装配组装",
                    "node_type": "TASK",
                    "sequence": 0,
                    "estimated_days": 5,
                    "completion_method": "MANUAL",
                    "is_required": True,
                    "description": "设备装配",
                },
                {
                    "node_code": "Q3N02",
                    "node_name": "调试测试",
                    "node_type": "TASK",
                    "sequence": 1,
                    "estimated_days": 3,
                    "completion_method": "MANUAL",
                    "is_required": True,
                    "description": "设备调试",
                    "dependency_node_codes": ["Q3N01"],
                },
                {
                    "node_code": "Q3N03",
                    "node_name": "内部检验",
                    "node_type": "TASK",
                    "sequence": 2,
                    "estimated_days": 2,
                    "completion_method": "MANUAL",
                    "is_required": True,
                    "description": "内部质量检验",
                    "dependency_node_codes": ["Q3N02"],
                },
            ]
        },
        {
            "stage_code": "Q4",
            "stage_name": "验收交付",
            "sequence": 3,
            "estimated_days": 5,
            "description": "客户验收和交付",
            "is_required": True,
            "nodes": [
                {
                    "node_code": "Q4N01",
                    "node_name": "客户验收",
                    "node_type": "APPROVAL",
                    "sequence": 0,
                    "estimated_days": 2,
                    "completion_method": "APPROVAL",
                    "is_required": True,
                    "description": "客户验收确认",
                },
                {
                    "node_code": "Q4N02",
                    "node_name": "发货交付",
                    "node_type": "TASK",
                    "sequence": 1,
                    "estimated_days": 2,
                    "completion_method": "MANUAL",
                    "is_required": True,
                    "description": "发货并交付",
                    "dependency_node_codes": ["Q4N01"],
                },
                {
                    "node_code": "Q4N03",
                    "node_name": "项目结项",
                    "node_type": "TASK",
                    "sequence": 2,
                    "estimated_days": 1,
                    "completion_method": "MANUAL",
                    "is_required": True,
                    "description": "项目结项归档",
                    "dependency_node_codes": ["Q4N02"],
                },
            ]
        },
    ]
}

# 重复生产模板（最简流程）
REPEAT_TEMPLATE: Dict[str, Any] = {
    "template_code": "TPL_REPEAT",
    "template_name": "重复生产",
    "description": "适用于已有成熟产品的重复生产订单，跳过设计阶段直接生产",
    "project_type": "REPEAT",
    "stages": [
        {
            "stage_code": "R1",
            "stage_name": "订单确认",
            "sequence": 0,
            "estimated_days": 2,
            "description": "确认订单和生产计划",
            "is_required": True,
            "nodes": [
                {
                    "node_code": "R1N01",
                    "node_name": "订单登记",
                    "node_type": "TASK",
                    "sequence": 0,
                    "estimated_days": 1,
                    "completion_method": "MANUAL",
                    "is_required": True,
                    "description": "登记订单信息",
                },
                {
                    "node_code": "R1N02",
                    "node_name": "生产排期",
                    "node_type": "TASK",
                    "sequence": 1,
                    "estimated_days": 1,
                    "completion_method": "MANUAL",
                    "is_required": True,
                    "description": "安排生产计划",
                    "dependency_node_codes": ["R1N01"],
                },
            ]
        },
        {
            "stage_code": "R2",
            "stage_name": "物料准备",
            "sequence": 1,
            "estimated_days": 10,
            "description": "按照标准BOM准备物料",
            "is_required": True,
            "nodes": [
                {
                    "node_code": "R2N01",
                    "node_name": "库存检查",
                    "node_type": "TASK",
                    "sequence": 0,
                    "estimated_days": 1,
                    "completion_method": "MANUAL",
                    "is_required": True,
                    "description": "检查物料库存",
                },
                {
                    "node_code": "R2N02",
                    "node_name": "采购补料",
                    "node_type": "TASK",
                    "sequence": 1,
                    "estimated_days": 7,
                    "completion_method": "MANUAL",
                    "is_required": False,
                    "description": "采购缺料物料",
                    "dependency_node_codes": ["R2N01"],
                },
                {
                    "node_code": "R2N03",
                    "node_name": "物料齐套",
                    "node_type": "TASK",
                    "sequence": 2,
                    "estimated_days": 2,
                    "completion_method": "MANUAL",
                    "is_required": True,
                    "description": "物料齐套确认",
                    "dependency_node_codes": ["R2N01"],
                },
            ]
        },
        {
            "stage_code": "R3",
            "stage_name": "批量生产",
            "sequence": 2,
            "estimated_days": 14,
            "description": "批量生产装配",
            "is_required": True,
            "nodes": [
                {
                    "node_code": "R3N01",
                    "node_name": "生产任务下达",
                    "node_type": "TASK",
                    "sequence": 0,
                    "estimated_days": 1,
                    "completion_method": "MANUAL",
                    "is_required": True,
                    "description": "下达生产任务单",
                },
                {
                    "node_code": "R3N02",
                    "node_name": "批量装配",
                    "node_type": "TASK",
                    "sequence": 1,
                    "estimated_days": 10,
                    "completion_method": "MANUAL",
                    "is_required": True,
                    "description": "批量装配生产",
                    "dependency_node_codes": ["R3N01"],
                },
                {
                    "node_code": "R3N03",
                    "node_name": "调试测试",
                    "node_type": "TASK",
                    "sequence": 2,
                    "estimated_days": 2,
                    "completion_method": "MANUAL",
                    "is_required": True,
                    "description": "设备调试测试",
                    "dependency_node_codes": ["R3N02"],
                },
                {
                    "node_code": "R3N04",
                    "node_name": "质量检验",
                    "node_type": "TASK",
                    "sequence": 3,
                    "estimated_days": 1,
                    "completion_method": "MANUAL",
                    "is_required": True,
                    "description": "产品质量检验",
                    "dependency_node_codes": ["R3N03"],
                },
            ]
        },
        {
            "stage_code": "R4",
            "stage_name": "发货交付",
            "sequence": 3,
            "estimated_days": 3,
            "description": "包装发货交付",
            "is_required": True,
            "nodes": [
                {
                    "node_code": "R4N01",
                    "node_name": "包装入库",
                    "node_type": "TASK",
                    "sequence": 0,
                    "estimated_days": 1,
                    "completion_method": "MANUAL",
                    "is_required": True,
                    "description": "包装入成品库",
                },
                {
                    "node_code": "R4N02",
                    "node_name": "安排发货",
                    "node_type": "TASK",
                    "sequence": 1,
                    "estimated_days": 1,
                    "completion_method": "MANUAL",
                    "is_required": True,
                    "description": "安排物流发货",
                    "dependency_node_codes": ["R4N01"],
                },
                {
                    "node_code": "R4N03",
                    "node_name": "交付确认",
                    "node_type": "TASK",
                    "sequence": 2,
                    "estimated_days": 1,
                    "completion_method": "MANUAL",
                    "is_required": True,
                    "description": "客户签收确认",
                    "dependency_node_codes": ["R4N02"],
                },
            ]
        },
    ]
}

# 所有预置模板列表
PRESET_TEMPLATES: List[Dict[str, Any]] = [
    STANDARD_TEMPLATE,
    QUICK_TEMPLATE,
    REPEAT_TEMPLATE,
]


def get_preset_template(template_code: str) -> Optional[Dict[str, Any]]:
    """根据模板编码获取预置模板数据"""
    for template in PRESET_TEMPLATES:
        if template["template_code"] == template_code:
            return template
    return None


def init_preset_templates(template_service) -> List:
    """
    初始化预置模板到数据库

    Args:
        template_service: StageTemplateService 实例

    Returns:
        List[StageTemplate]: 创建的模板列表
    """
    created_templates = []

    for template_data in PRESET_TEMPLATES:
        try:
            # 检查是否已存在
            existing = template_service.db.query(
                template_service.db.query(StageTemplate).filter(
                    StageTemplate.template_code == template_data["template_code"]
                ).exists()
            ).scalar()

            if not existing:
                template = template_service.import_template(template_data)
                # 设置为默认（第一个同类型模板）
                template_service.set_default_template(template.id)
                created_templates.append(template)
        except Exception as e:
            print(f"初始化模板 {template_data['template_code']} 失败: {e}")

    return created_templates
