# 提交信息规范指南 (Commit Message Guide)

## 概述

本项目采用 [Conventional Commits](https://www.conventionalcommits.org/) 规范来标准化提交信息格式。这有助于：

- 自动生成 CHANGELOG
- 语义化版本管理
- 更清晰的项目历史
- 更好的团队协作

## 提交信息格式

### 基本格式

```
<type>: <description>

[optional body]

[optional footer]
```

### 带作用域的格式

```
<type>(scope): <description>

[optional body]

[optional footer]
```

## 类型 (Type)

提交类型必须是以下之一：

| 类型 | 说明 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat: add user authentication` |
| `fix` | Bug 修复 | `fix: resolve login redirect issue` |
| `refactor` | 代码重构（既不是新功能也不是 Bug 修复） | `refactor: simplify error handling` |
| `docs` | 文档变更 | `docs: update API documentation` |
| `test` | 测试相关 | `test: add unit tests for user service` |
| `chore` | 构建过程或辅助工具的变动 | `chore: update dependencies` |
| `perf` | 性能优化 | `perf: improve query performance` |
| `ci` | CI 配置文件和脚本的变动 | `ci: add GitHub Actions workflow` |

## 作用域 (Scope) - 可选

作用域用于说明提交影响的范围，例如：

- `feat(api)`: API 相关的新功能
- `fix(auth)`: 认证相关的 Bug 修复
- `refactor(database)`: 数据库相关的重构

常见作用域示例：
- `api` - API 端点
- `auth` - 认证/授权
- `ui` - 用户界面
- `database` - 数据库
- `config` - 配置
- `deps` - 依赖

## 描述 (Description)

- **必填**，简短描述变更内容
- 使用祈使句、现在时态："add" 而不是 "added" 或 "adds"
- 首字母小写
- 不以句号结尾
- 最少 10 个字符，建议不超过 72 个字符

### ✅ 好的描述示例

```
feat: add user registration endpoint
fix: resolve null pointer exception in login
refactor: extract validation logic into separate service
docs: update installation instructions
```

### ❌ 不好的描述示例

```
feat: Added user registration endpoint.  # 时态错误，有句号
fix: bug fix                             # 太简短，不够描述性
Update stuff                             # 缺少类型
FEAT: ADD LOGIN                          # 大写错误
```

## 正文 (Body) - 可选

正文应该包含变更的动机和与之前行为的对比：

```
feat: add user registration endpoint

Implement new REST API endpoint for user registration.
Includes email validation and password hashing.

This replaces the old registration flow that required
manual admin approval.
```

## 页脚 (Footer) - 可选

页脚用于引用问题追踪 ID 或说明破坏性变更：

```
fix: resolve database connection timeout

Increase connection pool size and add retry logic.

Closes #123
Fixes #456
```

### 破坏性变更 (Breaking Changes)

破坏性变更应该在页脚中使用 `BREAKING CHANGE:` 标记：

```
feat: update API response format

BREAKING CHANGE: API now returns data wrapped in 'data' field
instead of directly returning the payload. Update all API clients
accordingly.
```

## 完整示例

### 示例 1: 新功能

```
feat: add project health status calculation

Implement automated health status calculation based on:
- Schedule variance
- Budget variance
- Issue count and severity

Health status is updated daily via scheduler.

Related to #234
```

### 示例 2: Bug 修复

```
fix(auth): resolve JWT token expiration issue

Token expiration was not being properly validated,
allowing expired tokens to be used. Added proper
expiration check in authentication middleware.

Fixes #345
```

### 示例 3: 重构

```
refactor(services): extract notification logic into unified service

Consolidate notification handling from multiple services
into a single UnifiedNotificationService to reduce code
duplication and improve maintainability.
```

### 示例 4: 文档更新

```
docs: add deployment guide for production environment

Include step-by-step instructions for:
- Environment setup
- Database migration
- Service configuration
- Monitoring setup
```

### 示例 5: 测试

```
test: add integration tests for approval workflow

Cover the complete approval flow:
- Submission
- Multi-level approval
- Rejection handling
- Notification delivery
```

## Git Trailers

项目要求在提交信息中包含 Git trailers 用于任务追踪：

```
feat: add commit message normalization hooks

Nightshift-Task: commit-normalize
Nightshift-Ref: https://github.com/marcus/nightshift
```

常用的 trailers：
- `Nightshift-Task:` - 任务标识
- `Nightshift-Ref:` - 参考链接
- `Signed-off-by:` - 签署人
- `Co-authored-by:` - 共同作者
- `Reviewed-by:` - 审查人

## 验证

项目已配置 Git commit-msg hook 来自动验证提交信息格式：

- 提交类型必须是允许的类型之一
- 描述长度至少 10 个字符
- 格式必须符合规范

如果提交信息不符合规范，hook 会拒绝提交并显示错误信息。

## 配置文件

项目包含以下配置文件：

- `.git/hooks/commit-msg` - Git hook 脚本
- `.commitlintrc.json` - Commitlint 配置

## 最佳实践

1. **保持提交原子性**: 每个提交只做一件事
2. **频繁提交**: 小而频繁的提交比大而稀疏的提交更好
3. **清晰的描述**: 让团队成员能够快速理解变更
4. **引用问题**: 在提交中引用相关的问题编号
5. **避免混合变更**: 不要在一个提交中混合多种类型的变更

## 工具推荐

- **Commitizen**: 交互式提交信息生成工具
- **Commitlint**: 提交信息验证工具
- **Husky**: Git hooks 管理工具

## 参考资料

- [Conventional Commits 规范](https://www.conventionalcommits.org/)
- [Angular Commit Message Guidelines](https://github.com/angular/angular/blob/main/CONTRIBUTING.md#commit)
- [Git Commit Best Practices](https://chris.beams.io/posts/git-commit/)

---

**最后更新**: 2026-03-06
