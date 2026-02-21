# Schemas 测试

本目录包含 Pydantic 数据验证模式(Schema)的单元测试。

## 📁 目录结构

```
schemas/
├── project/          # 项目相关 Schema 测试
│   ├── test_project_schema.py
│   ├── test_project_member_schema.py
│   └── test_milestone_schema.py
├── sales/            # 销售相关 Schema 测试
│   ├── test_customer_schema.py
│   ├── test_opportunity_schema.py
│   ├── test_contract_schema.py
│   └── test_quote_schema.py
├── procurement/      # 采购相关 Schema 测试
│   ├── test_supplier_schema.py
│   └── test_material_schema.py
├── finance/          # 财务相关 Schema 测试
│   ├── test_invoice_schema.py
│   └── test_payment_schema.py
├── auth/             # 认证相关 Schema 测试
│   ├── test_user_schema.py
│   ├── test_role_schema.py
│   └── test_permission_schema.py
└── conftest.py       # 共享 Fixtures
```

## 🎯 测试覆盖

每个 Schema 测试文件包含以下测试用例：

1. **有效数据测试** - 测试符合规范的数据通过验证
2. **必填字段测试** - 测试缺少必填字段时抛出错误
3. **字段类型测试** - 测试字段类型验证
4. **格式验证测试** - 测试邮箱、电话等格式验证
5. **长度约束测试** - 测试字符串长度限制
6. **数值范围测试** - 测试数值的最小/最大值
7. **枚举值测试** - 测试枚举类型字段
8. **额外字段测试** - 测试禁止额外字段
9. **嵌套模型测试** - 测试嵌套的 Schema 验证
10. **自定义验证器测试** - 测试自定义验证逻辑
11. **部分更新测试** - 测试可选字段的更新
12. **序列化测试** - 测试数据序列化输出

## 🚀 运行测试

### 运行所有 Schemas 测试
```bash
pytest tests/unit/schemas/ -v
```

### 运行特定模块测试
```bash
# 项目 Schema
pytest tests/unit/schemas/project/ -v

# 销售 Schema
pytest tests/unit/schemas/sales/ -v

# 采购 Schema
pytest tests/unit/schemas/procurement/ -v

# 财务 Schema
pytest tests/unit/schemas/finance/ -v

# 认证 Schema
pytest tests/unit/schemas/auth/ -v
```

### 运行单个测试文件
```bash
pytest tests/unit/schemas/project/test_project_schema.py -v
```

### 生成覆盖率报告
```bash
pytest tests/unit/schemas/ \
    --cov=app/schemas \
    --cov-report=html \
    --cov-report=term
```

## 📊 测试统计

- **总测试文件**: 14
- **预估测试用例数**: ~170+
- **覆盖的 Schema**: 14+

### 模块分布
- 项目模块: 3 个测试文件
- 销售模块: 4 个测试文件
- 采购模块: 2 个测试文件
- 财务模块: 2 个测试文件
- 认证模块: 3 个测试文件

## 🔧 技术栈

- **验证框架**: Pydantic V2
- **测试框架**: pytest
- **数据验证**: 类型注解 + 自定义验证器

## 📝 常见验证模式

### 1. 必填字段验证
```python
def test_required_fields():
    with pytest.raises(ValidationError) as exc_info:
        MySchema()
    assert "field_name" in str(exc_info.value)
```

### 2. 格式验证
```python
def test_email_format():
    with pytest.raises(ValidationError):
        MySchema(email="invalid-email")
```

### 3. 数值范围验证
```python
def test_positive_amount():
    with pytest.raises(ValidationError):
        MySchema(amount=-100)
```

### 4. 长度限制
```python
def test_max_length():
    long_string = "A" * 300
    with pytest.raises(ValidationError):
        MySchema(field=long_string)
```

## 🎓 Pydantic 最佳实践

1. 使用类型注解明确字段类型
2. 设置合理的默认值
3. 添加字段描述和示例
4. 使用自定义验证器处理复杂逻辑
5. 区分 Create/Update/Response Schema
6. 禁止额外字段 (`model_config = ConfigDict(extra='forbid')`)

## 🐛 测试注意事项

- 某些测试可能跳过，如果对应的 Schema 尚未实现
- ValidationError 的错误信息可能因 Pydantic 版本而异
- 使用 `pytest.skip` 处理依赖缺失的情况

## 📅 创建时间

2026-02-21

## 📧 维护者

OpenClaw AI Agent
