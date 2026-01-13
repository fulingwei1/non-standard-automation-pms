# 工程师绩效评价体系 - 文件说明

## 📁 文件清单

### 核心文档
| 文件 | 说明 |
|-----|------|
| `engineer-performance-system-complete.md` | **完整设计文档**（主文档，包含所有内容） |

### 前端原型（可直接浏览器打开）
| 文件 | 说明 |
|-----|------|
| `multi-role-performance-platform.html` | **多岗位统一平台**（首页总览、排名、个人绩效、协作、知识贡献、配置） |
| `mechanical-engineer-performance-prototype.html` | 机械工程师专属页面（设计评审、ECN统计） |
| `test-engineer-performance-prototype.html` | 测试工程师专属页面（Bug跟踪、代码库） |
| `electrical-engineer-performance-prototype.html` | 电气工程师专属页面（图纸管理、PLC模块库） |

### API实现（Python FastAPI）
| 文件 | 说明 |
|-----|------|
| `multi_role_performance_api.py` | 多岗位统一API（25+接口） |
| `electrical_performance_api.py` | 电气工程师专属API |

### 分模块设计文档
| 文件 | 说明 |
|-----|------|
| `multi-role-performance-platform.md` | 多岗位平台设计说明 |
| `test-engineer-performance-system.md` | 测试工程师体系设计 |
| `electrical-engineer-performance-system.md` | 电气工程师体系设计 |
| `engineer-performance-data-integration.md` | 数据集成策略 |

---

## 🚀 快速开始

1. **查看完整设计**：打开 `engineer-performance-system-complete.md`
2. **预览前端效果**：用浏览器打开 `.html` 文件
3. **运行API服务**：
   ```bash
   pip install fastapi uvicorn
   uvicorn multi_role_performance_api:app --reload
   ```

---

## 📊 系统概览

```
多岗位工程师绩效管理平台
├── 机械工程师（35人）
├── 测试工程师（15人）
└── 电气工程师（30人）

统一五维评价框架：
├── 技术能力（30%）
├── 项目执行（25%）
├── 成本/质量（20%）
├── 知识沉淀（15%）
└── 团队协作（10%）
```

---

## ⚠️ 重要原则

**权重配置只能按「岗位类型 + 职级」设定，不能针对个人！**

确保评价公平性，同一岗位同一级别的所有工程师使用相同标准。

---

## 📅 版本信息

- 版本：1.0
- 日期：2024年12月
- 维护：研发部
