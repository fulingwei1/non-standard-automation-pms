# -*- coding: utf-8 -*-
"""业务模块体系（模块化单体）。

本包是"按业务域的模块化单体"重构的落点：每个业务域最终迁移为
`app/modules/<key>/` 下的自包含包（models/services/api/schemas/tests），
通过 manifest 声明边界，由 import-linter 强制隔离，按 `tenant_modules`
表对租户开通。域划分与迁移路线见 docs/refactor/MODULE_MAP.md，
目录与边界约定见 docs/refactor/MODULE_CONVENTIONS.md。
"""

from app.modules.registry import (  # noqa: F401
    MODULES,
    ModuleManifest,
    get_module,
    iter_business_modules,
)
