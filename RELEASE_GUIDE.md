# 📦 发布指南 (Release Guide)

本指南说明如何为项目创建新的发布版本。

---

## 🎯 发布流程

### 1. 准备阶段

#### 检查待发布内容

```bash
# 查看最近的提交
git log --oneline -20

# 查看已关闭的 Issue
# https://github.com/fulingwei1/non-standard-automation-pms/issues?q=is%3Aissue+is%3Aclosed

# 查看已合并的 PR
# https://github.com/fulingwei1/non-standard-automation-pms/pulls?q=is%3Apr+is%3Amerged
```

#### 更新 CHANGELOG.md

在 `CHANGELOG.md` 顶部添加新版本记录：

```markdown
## [1.1.0] - 2026-04-04

### ✨ 新增
- 功能 1
- 功能 2

### 🐛 修复
- 修复问题 1
- 修复问题 2

### 🔄 变更
- 变更说明
```

### 2. 版本号规则

遵循 [语义化版本 2.0.0](https://semver.org/lang/zh-CN/)：

- **MAJOR.MINOR.PATCH** (主版本号。次版本号。修订号)

**版本号递增规则**：
- **MAJOR**：不兼容的 API 变更 → 1.0.0 → 2.0.0
- **MINOR**：向后兼容的功能新增 → 1.0.0 → 1.1.0
- **PATCH**：向后兼容的问题修正 → 1.0.0 → 1.0.1

### 3. 创建 Release Tag

```bash
# 确保在 main 分支
git checkout main
git pull origin main

# 运行测试
cd api && pytest
cd ../frontend && pnpm run test:run

# 创建并推送 Tag
git tag -a v1.1.0 -m "Release v1.1.0 - 功能描述"
git push origin v1.1.0
```

### 4. 创建 GitHub Release

1. 访问：https://github.com/fulingwei1/non-standard-automation-pms/releases/new

2. 填写信息：
   - **Tag version**: `v1.1.0`
   - **Release title**: `v1.1.0 - 版本名称`
   - **Description**: 从 CHANGELOG.md 复制版本说明

3. 点击 **Publish release**

### 5. 发布后检查

- [ ] GitHub Actions CI 通过
- [ ] Release 页面显示正确
- [ ] CHANGELOG.md 已更新
- [ ] 文档已同步更新

---

## 📋 发布清单

### 每次发布前检查

- [ ] 所有测试通过
- [ ] 代码审查完成
- [ ] CHANGELOG.md 已更新
- [ ] 文档已更新
- [ ] 没有未解决的严重 Bug
- [ ] 性能测试通过（如适用）

### 大版本发布额外检查

- [ ] 向后兼容性检查
- [ ] 迁移指南已编写
- [ ] 升级说明已发布
- [ ] 通知所有用户

---

## 🚨 紧急修复流程

### Hotfix 发布

```bash
# 从最新 Release Tag 创建分支
git checkout -b hotfix/issue-xxx v1.0.0

# 修复问题
# ...

# 创建 Tag
git tag -a v1.0.1 -m "Hotfix v1.0.1 - 修复 XXX 问题"
git push origin v1.0.1

# 合并回 main 和 develop
git checkout main
git merge v1.0.1
git checkout develop
git merge v1.0.1
```

---

## 📊 发布周期建议

| 版本类型 | 周期 | 示例 |
|---------|------|------|
| **大版本** | 每季度 | v1.0.0 → v2.0.0 |
| **小版本** | 每月 | v1.0.0 → v1.1.0 |
| **修正版本** | 按需 | v1.0.0 → v1.0.1 |

---

## 🔗 相关链接

- [GitHub Releases](https://github.com/fulingwei1/non-standard-automation-pms/releases)
- [CHANGELOG.md](CHANGELOG.md)
- [语义化版本规范](https://semver.org/lang/zh-CN/)

---

**发布愉快！** 🎉
