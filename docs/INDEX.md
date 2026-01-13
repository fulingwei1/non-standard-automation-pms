# 文档索引 - 非标自动化项目管理系统

> 最后更新: 2026-01-13  
> 📋 [文档整理报告](DOCUMENTATION_ORGANIZATION_REPORT.md) - 查看文档整理详情

## 目录结构

```
docs/
├── api/              # API 接口文档
├── deployment/       # 部署和配置文档
│   └── PROJECT_RUN_GUIDE.md  # 项目运行指南
├── design/           # 设计文档
├── modules/          # 模块文档
│   ├── acceptance/   # 验收管理
│   ├── alert/        # 预警管理
│   ├── ecn/          # 工程变更管理
│   ├── finance/      # 财务成本管理
│   ├── hr/           # 人力资源管理
│   ├── procurement/  # 采购物料管理
│   ├── production/   # 生产管理
│   ├── project/      # 项目管理
│   └── sales/        # 销售管理
├── progress/         # 开发进度文档
│   ├── modules/      # 模块完成报告
│   ├── sprints/      # Sprint 迭代记录
│   └── SYSTEM_FEATURES_COMPLETE_SUMMARY.md  # 系统功能完整统计
├── technical/        # 技术文档
├── testing/          # 测试文档
│   └── INTEGRATION_TEST_REPORT.md  # 集成测试报告
└── user-guides/      # 用户手册
```

---

## 快速入口

### 入门指南
- [系统设计文档](design/非标自动化项目管理系统_设计文档.md)
- [技术架构设计](design/项目管理系统_技术架构设计.md)
- [DEMO 演示指南](user-guides/DEMO_GUIDE.md)

### 模块设计文档
| 模块 | 文档 |
|------|------|
| 项目管理 | [详细设计](design/项目管理模块_详细设计文档.md) |
| 采购物料 | [详细设计](design/采购与物料管理模块_详细设计文档.md) |
| 工程变更 | [详细设计](design/变更管理模块_详细设计文档.md) |
| 验收管理 | [详细设计](design/验收管理模块_详细设计文档.md) |
| 预警异常 | [详细设计](design/预警与异常管理模块_详细设计文档.md) |
| 外协管理 | [详细设计](design/外协管理模块_详细设计文档.md) |
| 销售管理 | [详细设计](design/销售管理模块_线索到回款_设计文档.md) |
| 权限管理 | [详细设计](design/权限管理模块_详细设计文档.md) |
| 角色管理 | [详细设计](design/角色管理模块_详细设计文档.md) |

### API 参考
- [API 快速参考](api/API_QUICK_REFERENCE.md)
- [项目管理 API](api/PROJECT_API_SUMMARY.md)
- [销售管理 API](api/SALES_MODULE_SUMMARY.md)
- [预警管理 API](api/ALERT_EXCEPTION_API_SUMMARY.md)

### 用户手册
- [项目管理用户手册](user-guides/项目管理模块用户手册.md)
- [问题管理用户手册](user-guides/用户手册_问题管理模块.md)
- [任职资格使用说明](user-guides/任职资格体系使用说明.md)
- [技术评审使用说明](user-guides/技术评审模块使用说明.md)

### 技术文档
- [架构图](technical/ARCHITECTURE_DIAGRAM.md)
- [数据字典](technical/数据字典.md)
- [代码审查清单](technical/CODE_REVIEW_CHECKLIST.md)
- [安全审查清单](technical/SECURITY_REVIEW_CHECKLIST.md)

### 进度文档
- [系统功能完整统计](progress/SYSTEM_FEATURES_COMPLETE_SUMMARY.md)

### 测试文档
- [UAT 测试计划](testing/UAT_TEST_PLAN.md)
- [UAT 就绪报告](testing/UAT_READINESS_REPORT.md)
- [测试结果](testing/TEST_RESULTS.md)
- [集成测试报告](testing/INTEGRATION_TEST_REPORT.md)

### 部署文档
- [项目运行指南](deployment/PROJECT_RUN_GUIDE.md)

---

## 根目录重要文件

| 文件 | 说明 |
|------|------|
| [CLAUDE.md](../CLAUDE.md) | AI 助手开发指南 |
| [README.md](../README.md) | 项目说明文件 |

---

## 文档命名规范

- **设计文档**: `模块名_详细设计文档.md`
- **API 文档**: `MODULE_API_SUMMARY.md`
- **用户手册**: `模块名用户手册.md` 或 `MODULE_GUIDE.md`
- **进度报告**: `模块名_Sprint/Issue完成总结.md`
- **技术文档**: `FEATURE_IMPLEMENTATION.md`
