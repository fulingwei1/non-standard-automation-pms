# 变更日志 (Changelog)

本文件记录项目的所有重要变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

---

## [未发布]

### 计划中
- 移动端适配
- 多语言支持（国际化）
- 高级报表导出功能

---

## [1.0.0] - 2026-04-04

### 🎉 首次正式发布

#### ✨ 新增功能

**核心模块**
- 多租户 SaaS 架构（支持 10-10,000 租户）
- 项目全生命周期管理
- 销售订单管理
- 采购管理
- 库存管理
- 工时管理系统

**AI 智能功能**
- AI 成本预测引擎（LSTM + XGBoost）
- AI 工时分析热力图
- AI 风险评分系统
- 智能负荷预警

**成本管理**
- EVM 挣值管理（PV/EV/AC/CPI/SPI）
- 标准成本库
- 成本超支预警
- 毛利率分析

**权限与安全**
- RBAC 角色权限管理
- JWT 认证
- API 速率限制
- 数据加密存储

**数据分析**
- 实时 Dashboard
- 项目甘特图
- 多维度报表
- 数据导出（Excel/PDF）

#### 🏗️ 技术架构

**后端**
- Python 3.10+ / FastAPI 0.115+
- PostgreSQL 15+ / SQLAlchemy 2.0+
- Redis 缓存
- APScheduler 任务调度

**前端**
- React 18+ / TypeScript 5+
- Vite 5+
- Ant Design 5+
- Tailwind CSS

**部署**
- Docker 容器化
- Vercel Serverless 支持
- GitHub Actions CI/CD

#### 📚 文档

- 完整 API 文档（OpenAPI/Swagger）
- 架构设计文档
- 部署指南
- 开发指南
- 用户手册

#### 🧪 测试

- 后端单元测试（pytest）
- 前端单元测试（vitest）
- E2E 测试（Playwright）
- 代码覆盖率报告（Codecov）

---

## [0.1.0] - 2025-12-01

### 🚧 内部测试版

- 核心功能开发完成
- 小范围内部测试
- 基础架构搭建

---

## 版本说明

### 语义化版本

- **MAJOR.MINOR.PATCH**（主版本号。次版本号。修订号）
- **MAJOR**：不兼容的 API 变更
- **MINOR**：向后兼容的功能新增
- **PATCH**：向后兼容的问题修正

### 发布周期

- **大版本**：每季度发布一次
- **小版本**：每月发布一次
- **修正版本**：按需发布

---

## 相关链接

- [GitHub Releases](https://github.com/fulingwei1/non-standard-automation-pms/releases)
- [Issue Tracker](https://github.com/fulingwei1/non-standard-automation-pms/issues)
- [项目文档](docs/README.md)
