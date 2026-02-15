# 报价单PDF模板

## 模板目录结构

```
quotation_pdf/
├── basic/          # 基础版模板
├── standard/       # 标准版模板
├── premium/        # 高级版模板
└── README.md       # 说明文档
```

## 模板说明

### 基础版模板（Basic）
- 适用场景：小型项目、标准化产品
- 特点：简洁明了、价格透明
- 包含内容：
  - 基本项目清单
  - 简单的价格明细
  - 标准付款条款

### 标准版模板（Standard）
- 适用场景：中型项目、定制化需求
- 特点：详细清晰、专业规范
- 包含内容：
  - 详细项目清单
  - 完整价格明细（含税费、折扣）
  - 灵活付款条款
  - 项目说明

### 高级版模板（Premium）
- 适用场景：大型项目、复杂系统
- 特点：精美设计、完整专业
- 包含内容：
  - 超详细项目清单
  - 完整价格明细
  - 定制化付款条款
  - 项目背景说明
  - 实施计划
  - 售后服务说明
  - 公司资质证明

## 使用方法

### 1. 基本使用

```python
from app.services.quotation_pdf_service import QuotationPDFService

pdf_service = QuotationPDFService()
pdf_path = pdf_service.generate_pdf(quotation)
```

### 2. 带公司信息

```python
company_info = {
    'logo_path': 'path/to/logo.png',
    'name': '科技有限公司',
    'address': '北京市朝阳区XXX',
    'phone': '010-12345678',
    'email': 'contact@company.com'
}

pdf_path = pdf_service.generate_pdf(quotation, company_info)
```

### 3. 生成对比PDF

```python
pdf_path = pdf_service.generate_comparison_pdf([basic, standard, premium])
```

## 自定义模板

如需自定义PDF样式，可以：

1. 修改 `app/services/quotation_pdf_service.py` 中的样式配置
2. 添加自定义字体（中文字体路径）
3. 调整颜色方案
4. 修改表格布局

## 注意事项

1. 确保安装 ReportLab: `pip install reportlab`
2. 中文显示需要正确的字体文件
3. PDF文件保存在 `uploads/quotations/` 目录
4. 建议定期清理旧的PDF文件
