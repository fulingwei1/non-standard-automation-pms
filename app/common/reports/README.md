# 统一报表框架使用指南

## 快速开始

### 步骤1: 创建报表生成器

```python
from app.common.reports.base import BaseReportGenerator

class ProjectReportGenerator(BaseReportGenerator):
    async def generate_data(self):
        # 实现数据生成逻辑
        return {
            "title": "项目报表",
            "items": [...]
        }
```

### 步骤2: 导出报表

```python
report = ProjectReportGenerator(config)

# 导出为不同格式
json_data = await report.export("json")
pdf_data = await report.export("pdf")
excel_data = await report.export("excel")
word_data = await report.export("word")
```

---

## 支持的格式

- **JSON**: 结构化数据
- **PDF**: 使用reportlab生成
- **Excel**: 使用pandas和openpyxl生成
- **Word**: 使用python-docx生成

---

## 配置驱动

### YAML配置示例

```yaml
name: 项目汇总报表
description: 项目数据汇总报表
template: templates/reports/project_report.html
fields:
  - key: project_code
    label: 项目编码
    type: string
  - key: project_name
    label: 项目名称
    type: string
  - key: status
    label: 状态
    type: enum
filters:
  status:
    type: select
    options: [ACTIVE, COMPLETED, CANCELLED]
```

---

## 更多示例

查看 `example_usage.py` 获取更多使用示例。
