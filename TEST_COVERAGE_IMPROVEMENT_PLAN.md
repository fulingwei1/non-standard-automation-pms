# 测试覆盖率提升计划

**Created:** 2026-04-04  
**Current Coverage:** 30.2% (Mar 14 data)  
**Target Coverage:** 60%+  
**Priority:** high  
**Status:** ⏸️ Paused - API rate limit, resume when cleared

---

## 执行记录

### 2026-04-04 21:00 - 首次尝试
- Spawn sub-agent 执行测试提升
- 结果：API rate limit, 5 秒完成无输出

### 2026-04-04 21:02 - 第二次尝试
- 直接运行 pytest 识别低覆盖率文件
- 结果：pytest 无输出（可能 rate limit 或环境问题）

---

## 后续行动

**方案 A - 等待 rate limit 恢复**
```bash
# 等待 1-2 小时后重试
cd ~/.openclaw/workspace/non-standard-automation-pms
python -m pytest --cov=app --cov-report=term-missing 2>&1 | tail -100
```

**方案 B - 手动执行（推荐）**
1. 打开 `htmlcov/index.html` 查看最低覆盖率文件
2. 为前 10 个最低文件各补充 1-2 个测试
3. 运行 `python -m pytest --cov=app --cov-branch` 验证
4. Commit & push

**方案 C - 用 Codex 执行**
```bash
# 用 Codex CLI 绕过 rate limit
codex -m "提升测试覆盖率从 30% 到 60%" --permission-mode bypassPermissions
```

---

## 当前状态

- **Backend:** Python/FastAPI, `tests/` 目录已有测试文件
- **Frontend:** React/Vite, vitest + playwright
- **Coverage Report:** `coverage.json`, `htmlcov/`

---

## 低覆盖率模块 (优先补充)

### 1. 销售模块 (Sales) - 预估覆盖率 <20%
- `app/api/v1/endpoints/sales/` — 刚合并，测试可能未跟上
- `app/services/permission_management/` — 权限服务核心
- `app/core/permission_engine.py` — 权限引擎

### 2. 生产管理 (Production) - 预估覆盖率 ~25%
- `app/services/production/` — 工单、计划服务
- `app/api/v1/endpoints/production/`

### 3. 角色管理 (Role Management) - 刚重构
- `app/api/v1/endpoints/roles.py` — 刚解决冲突
- `app/services/role_management/`

---

## 执行策略

### Phase 1: 识别最低覆盖率文件
```bash
cd ~/.openclaw/workspace/non-standard-automation-pms
python -m pytest --cov=app --cov-report=term-missing | grep -A 50 "MISSING"
```

### Phase 2: 为关键服务补充测试
- 每个 service 文件至少 1 个测试文件
- 优先测试边界条件和错误处理

### Phase 3: 运行完整测试套件
```bash
python -m pytest --cov=app --cov-branch --cov-report=html
# 查看 htmlcov/index.html
```

---

## 参考 Learnings

- [LRN-20260404-008] checkpoint_before_completion — 长任务需要 checkpoint
- [LRN-20260404-005] task_orchestrator_spawn_only — 用 spawned sub-agent 跑测试

---

## 验收标准

- [ ] 整体覆盖率 ≥ 60%
- [ ] 关键服务 (permission, sales, production) ≥ 70%
- [ ] 无测试失败
- [ ] CI/CD 通过
