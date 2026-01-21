# -*- coding: utf-8 -*-
"""
阶段模板相关枚举
"""
from enum import Enum


class NodeTypeEnum(str, Enum):
    """节点类型"""
    TASK = "TASK"  # 任务类 - 手动完成
    APPROVAL = "APPROVAL"  # 审批类 - 需审批流程
    DELIVERABLE = "DELIVERABLE"  # 交付物类 - 需上传附件


class CompletionMethodEnum(str, Enum):
    """完成方式"""
    MANUAL = "MANUAL"  # 手动标记完成
    APPROVAL = "APPROVAL"  # 审批通过后完成
    UPLOAD = "UPLOAD"  # 上传附件后完成
    AUTO = "AUTO"  # 自动完成（关联业务数据）


class StageStatusEnum(str, Enum):
    """阶段/节点状态"""
    PENDING = "PENDING"  # 待开始 - 灰色
    IN_PROGRESS = "IN_PROGRESS"  # 进行中 - 蓝色
    COMPLETED = "COMPLETED"  # 已完成 - 绿色
    DELAYED = "DELAYED"  # 已延期 - 红色
    BLOCKED = "BLOCKED"  # 受阻 - 橙色
    SKIPPED = "SKIPPED"  # 已跳过 - 灰色


class StageCategoryEnum(str, Enum):
    """阶段分类"""
    SALES = "sales"  # 销售阶段
    PRESALES = "presales"  # 售前阶段
    EXECUTION = "execution"  # 执行阶段
    CLOSURE = "closure"  # 收尾阶段


class ReviewResultEnum(str, Enum):
    """评审结果"""
    PASSED = "PASSED"  # 通过
    CONDITIONAL = "CONDITIONAL"  # 有条件通过
    FAILED = "FAILED"  # 未通过


class TemplateProjectTypeEnum(str, Enum):
    """模板适用的项目类型"""
    NEW = "NEW"  # 全新产品
    REPEAT = "REPEAT"  # 重复产品
    SIMPLE = "SIMPLE"  # 简单新产品
    CUSTOM = "CUSTOM"  # 自定义
