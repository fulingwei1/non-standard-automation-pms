# 模块化单体·目录与边界约定（MODULE_CONVENTIONS）

> 配套文档：域划分与迁移路线见 `MODULE_MAP.md`。本文规定"迁进来的模块长什么样、边界怎么锁、怎么按租户开通、什么标准算上线"。P1 立规于 2026-07-06 落地。

## 1. 目录约定

每个业务域迁移为 `app/modules/<key>/` 下的自包含包（key 见 `app/modules/registry.py`，与 MODULE_MAP §1 一致）：

```
app/modules/presale/
├── __init__.py          # 只导出公共接口（见 §3），不泄漏内部实现
├── manifest.py          # 引用 registry 中的 ModuleManifest；声明本模块路由聚合器
├── models/              # 本域 ORM 模型（全部表必须有 tenant_id 处置）
├── services/            # 本域业务逻辑
├── api/                 # 本域路由；聚合 router 挂 require_module("<key>") 闸门
├── schemas/
└── tests/               # 本域测试（pytest app/modules/presale/tests 独立可跑）
```

迁移期间旧目录（app/services、app/api/v1/endpoints、app/models 平铺层）**只减不增**：新代码一律写进 modules/，改到哪个域的旧代码就顺手迁哪个域。

## 2. 模块注册与租户开通

- **注册表**：`app/modules/registry.py` 是全部模块的唯一权威清单（6 个 always_on 平台模块 + 15 个业务模块，含 `depends_on` 依赖声明）。新增模块 = 在 registry 加一条 manifest，勿自造 key。
- **开通表**：`tenant_modules`（租户×模块×状态/到期），超管通过 `PUT /tenants/{id}/modules/{key}` 管理；前端用 `GET /my/modules` 拿当前租户生效快照做菜单/路由闸门。
- **后端闸门**：模块路由聚合器必须挂 `app.api.deps.require_module("<key>")`；未开通返回 403 + `X-Module-Required` 头。
- **闸门模式**（`settings.MODULE_GATING_MODE`，沿用 TENANT_ENFORCE_MODE 的灰度模式）：
  - `off`：全放行（回滚开关）
  - `grandfather`（当前默认）：缺行=视为已开通，存量租户零感知；只拦显式 DISABLED/过期
  - `strict`：缺行=未开通即拦；新租户体系成熟后切换
- 开通/停用校验依赖关系：开通前 `depends_on` 必须已开通；停用前依赖者必须先停用。

## 3. 边界规则（import-linter 强制）

- 配置在根目录 `.importlinter`，CI/本地由 `tests/unit/test_tenant_module_gate.py::TestImportBoundaries` 守护（跑 pytest 即生效）。
- 现行合同：① models 不得 import services/api；② services 不得 import api；③ modules/ 下业务模块彼此 independence（模块迁入时把包名加进合同）。
- **模块间协作只有三条许可通道**：
  1. import 对方 `__init__.py` 导出的公共接口（服务门面/只读查询函数）；
  2. 事件（platform-notify / 未来的领域事件总线）；
  3. 平台层能力（approval/notify/file/ai/infra 任何模块都可用）。
  直接 import 别的模块的 models/内部 service = 违规，合同会拦。
- 函数级懒加载 import 不在合同统计内（grimp 只看模块级），是打破循环的许可手段，但 MODULE_MAP §7 列出的存量函数级跨层调用（gate_checks 等）在对应域迁移时仍应清零。

## 4. 模块成熟度与上线闸门

| 级别 | 含义 | 升级条件 |
|---|---|---|
| L0 原型 | 代码在 modules/ 下但未挂闸门 | — |
| L1 内测 | 仅自有租户开通 | 模块测试独立全绿 |
| L2 试点 | 指定租户开通 | 功能审计中属本域的问题清零 + import-linter 无违规 + tenant_id 全覆盖 |
| L3 GA | 所有租户可订阅 | 试点租户验收通过 |

## 5. 迁移一个域的标准动作（P2 起逐域执行）

1. 按 MODULE_MAP §2/§5 把散落文件归拢进 `app/modules/<key>/`（含错放在别的域目录里的）；
2. 旧 import 路径留薄 shim（一个迭代周期后删）；
3. 把模块包名加进 `.importlinter` 的 independence 合同；违规按 §3 三通道改写；
4. 路由聚合器挂 `require_module`；前端菜单接 `/my/modules`；
5. 跑模块测试 + 全局冒烟（路由表对比），按 §4 评级。
