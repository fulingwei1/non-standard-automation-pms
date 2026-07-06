# -*- coding: utf-8 -*-
"""模块注册表：全部业务域的唯一权威清单。

- `always_on=True` 的平台模块不参与租户开通（所有租户始终可用）。
- 业务模块按 `tenant_modules` 表逐租户开通，闸门逻辑见
  app/services/tenant_module_service.py 与 app/api/deps.py::require_module。
- `depends_on` 声明模块间依赖：开通某模块前其依赖必须已开通，
  停用某模块前依赖它的模块必须先停用。
- key 与 docs/refactor/MODULE_MAP.md §1 的域代号一一对应，勿自造。
"""

from dataclasses import dataclass, field
from typing import Dict, Iterator, Optional, Tuple


@dataclass(frozen=True)
class ModuleManifest:
    key: str
    name: str
    description: str
    always_on: bool = False  # 平台层=True：不参与租户开通
    depends_on: Tuple[str, ...] = field(default_factory=tuple)


_PLATFORM = [
    ModuleManifest("platform-auth", "租户与权限", "租户/用户/角色/权限/数据权限/会话/2FA/组织", always_on=True),
    ModuleManifest("platform-approval", "审批引擎", "统一审批流引擎", always_on=True),
    ModuleManifest("platform-notify", "通知告警", "通知/提醒/告警等通用消息能力", always_on=True),
    ModuleManifest("platform-file", "文件文档", "文件上传/导入导出/Excel/PDF/docx 通用文档能力", always_on=True),
    ModuleManifest("platform-ai", "AI 基础设施", "AI 网关/AI jobs/AI feedback", always_on=True),
    ModuleManifest("platform-infra", "基础设施", "缓存/备份/调度器/监控/状态机引擎", always_on=True),
]

_BUSINESS = [
    ModuleManifest("presale", "售前", "售前评估/AI 报价/方案/技术评估/需求提取", depends_on=("sales",)),
    ModuleManifest("sales", "销售", "客户/合同/订单/回款/开票/目标/漏斗"),
    ModuleManifest("project", "项目管理", "项目主干/阶段/里程碑/进度/风险/任务中心/OTD"),
    ModuleManifest("engineering", "工程设计", "技术评审/技术规格/研发项目", depends_on=("project",)),
    ModuleManifest("ecn", "工程变更", "ECN/变更影响分析", depends_on=("project",)),
    ModuleManifest("bom-material", "BOM 物料", "BOM/物料主数据"),
    ModuleManifest("procurement", "采购外协", "采购/外协/供应商", depends_on=("bom-material",)),
    ModuleManifest("inventory-kitting", "库存齐套", "库存/齐套/缺料/仓库", depends_on=("bom-material",)),
    ModuleManifest("production", "生产制造", "车间/工单/报工/安装派工/现场/设备/质量", depends_on=("project",)),
    ModuleManifest("acceptance", "验收交付", "验收/交付", depends_on=("project",)),
    ModuleManifest("aftersales", "售后服务", "售后/服务工单/ITR/SLA"),
    ModuleManifest("cost-finance", "成本财务", "成本/预算/EVM/毛利/结算/标准成本", depends_on=("project",)),
    ModuleManifest("performance-hr", "绩效人事", "绩效/奖金/工时/排班/人员匹配/HR/文化墙"),
    ModuleManifest("analytics", "经营分析", "看板/报表中心/经营统计"),
    ModuleManifest("strategy-pmo", "战略 PMO", "战略/PMO/经营节奏/最佳实践/知识库/踩坑库"),
]

MODULES: Dict[str, ModuleManifest] = {m.key: m for m in _PLATFORM + _BUSINESS}


def get_module(key: str) -> Optional[ModuleManifest]:
    return MODULES.get(key)


def iter_business_modules() -> Iterator[ModuleManifest]:
    for m in MODULES.values():
        if not m.always_on:
            yield m
