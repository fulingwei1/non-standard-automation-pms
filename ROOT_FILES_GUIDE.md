# 根目录文件说明

本文档说明项目根目录中各个文件的作用。

## 📋 配置文件

### 环境配置
- **`.env.example`** - 环境变量模板文件，展示项目需要的所有环境变量
- **`.env.local`** - 本地开发环境变量（不提交到Git）
- **`.env.production`** - 生产环境变量
- **`.env.vercel`** - Vercel部署平台的环境变量

### 代码质量配置
- **`.coveragerc`** - Python代码覆盖率工具配置
- **`.pre-commit-config.yaml`** - Git提交前自动检查配置（代码格式、质量检查等）
- **`.cursorrules`** - Cursor IDE的自定义规则配置
- **`pytest.ini`** - pytest测试框架配置

### 部署配置
- **`vercel.json`** - Vercel平台部署配置
- **`docker-compose.yml`** - Docker容器编排配置（开发环境）
- **`docker-compose.production.yml`** - Docker容器编排配置（生产环境）
- **`Dockerfile`** - Docker镜像构建配置
- **`Dockerfile.fullstack`** - 全栈应用的Docker镜像配置

### 依赖管理
- **`requirements.txt`** - Python项目依赖包列表

### Git配置
- **`.gitignore`** - Git忽略文件列表（不提交到版本库的文件）

## 📚 文档文件

### 核心文档
- **`README.md`** - 项目主文档，包含项目介绍、安装、使用说明
- **`CLAUDE.md`** - AI助手开发指南，说明如何使用AI辅助开发
- **`STARTUP.md`** - 项目启动指南
- **`DEPLOYMENT_GUIDE.md`** - 部署指南（英文）
- **`部署说明.md`** - 部署说明（中文）
- **`免费云部署指南.md`** - 免费云平台部署指南
- **`VERCEL_SUPABASE_DEPLOYMENT.md`** - Vercel + Supabase部署说明
- **`PROJECT_STRUCTURE.md`** - 项目目录结构说明（刚创建的）

### 其他文档（已移动到 `docs/guides/`）
- **`DEMO_ACCOUNTS.md`** - 演示账户信息
- **`SECURITY_FIXES.md`** - 安全修复记录
- **`VERCEL_SUPABASE_DEPLOYMENT.md`** - Vercel+Supabase部署说明
- **`免费云部署指南.md`** - 免费云部署指南
- **`部署说明.md`** - 部署说明
- **`CURSOR_GLM_CONFIG_INFO.txt`** - Cursor GLM配置信息

> 注意：这些文档已移动到 `docs/guides/` 目录。

## 🚀 启动脚本

- **`start.sh`** - 启动应用服务
- **`stop.sh`** - 停止应用服务
- **`status.sh`** - 查看服务状态
- **`quick_start.sh`** - 快速启动脚本

## 🗄️ 数据库文件（已移动到 `scripts/database/`）

- **`supabase-setup.sql`** - Supabase数据库初始化SQL脚本

> 注意：此文件已移动到 `scripts/database/` 目录。

## 📊 测试和覆盖率文件

- **`.coverage`** - 代码覆盖率数据文件（二进制）
- **`coverage.xml`** - 代码覆盖率XML报告（用于CI/CD）

## 📝 日志文件（已移动到 `logs/` 目录）

- **`test_coverage_output.log`** - 测试覆盖率输出日志
- **`test_run_filtered_output.log`** - 过滤后的测试运行日志
- **`test_run_output.log`** - 测试运行输出日志

> 注意：这些日志文件已移动到 `logs/` 目录，可以定期清理。

## 📁 目录说明

- **`tests/`** - 测试代码目录
- **`uploads/`** - 用户上传文件目录
- **`website/`** - 网站相关文件
- **`untitled folder/`** - 未命名文件夹（可能是临时文件夹）

## 🔍 文件查找指南

### 需要修改配置？
- 环境变量 → `.env.local` 或 `.env.production`
- 测试配置 → `pytest.ini`
- 代码质量 → `.pre-commit-config.yaml`
- 部署配置 → `vercel.json` 或 `docker-compose.yml`

### 需要查看文档？
- 项目介绍 → `README.md`
- 开发指南 → `CLAUDE.md`
- 启动说明 → `STARTUP.md`
- 部署说明 → `DEPLOYMENT_GUIDE.md` 或 `部署说明.md`
- 项目结构 → `PROJECT_STRUCTURE.md`

### 需要运行项目？
- 快速启动 → `./quick_start.sh`
- 启动服务 → `./start.sh`
- 停止服务 → `./stop.sh`
- 查看状态 → `./status.sh`

## ⚠️ 注意事项

1. **`.env.*` 文件**：包含敏感信息，不要提交到Git
2. **`.coverage` 文件**：测试覆盖率数据，可以删除后重新生成
3. **日志文件**：可以定期清理，不影响项目运行
4. **`untitled folder`**：如果是空文件夹，可以删除

## 🧹 建议清理的文件

以下文件可以定期清理或移动到 `logs/` 目录：
- `test_*.log` - 测试日志文件
- `.coverage` - 覆盖率数据（可重新生成）
