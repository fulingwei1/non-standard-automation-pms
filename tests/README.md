# 测试目录结构说明

## 目录组织

```
tests/
├── unit/                    # 单元测试（207个文件）
│   ├── test_*_service.py   # 服务层单元测试
│   ├── test_approval_*.py  # 审批引擎测试
│   └── test_*_utils.py     # 工具函数测试
│
├── integration/             # 集成测试（45个文件）
│   ├── api_test_helper.py  # API测试辅助工具
│   ├── test_*_api_ai.py    # AI生成的API集成测试
│   ├── test_*_api.py       # 手动编写的API集成测试
│   └── README_API_TESTING.md  # API测试框架文档
│
├── api/                    # API端点测试（42个文件）
│   └── test_*.py           # 各模块API端点测试
│
├── e2e/                    # 端到端测试（2个文件）
│   ├── test_business_workflows.py
│   └── test_project_lifecycle.py
│
├── performance/            # 性能测试（2个文件）
│   ├── test_health_calculation_performance.py
│   └── test_project_list_performance.py
│
├── scripts/                # 手动测试脚本
│   ├── test_*_apis.py      # 手动API测试脚本（使用requests）
│   └── *.sh                # Shell测试脚本
│
├── legacy/                 # 遗留测试文件
│   └── integration_test.py
│
├── utils/                  # 测试工具函数
│   └── mocks.py
│
├── conftest.py             # pytest配置和fixtures
├── factories.py            # 测试数据工厂
└── run_api_integration_tests.sh  # API集成测试运行脚本
```

## 测试类型说明

### 1. 单元测试 (`tests/unit/`)
- **用途**: 测试单个函数、类或模块的功能
- **特点**: 
  - 快速执行
  - 不依赖外部服务
  - 使用mock隔离依赖
- **运行**: `pytest tests/unit/ -v`

### 2. 集成测试 (`tests/integration/`)
- **用途**: 测试多个模块协同工作，特别是API端点
- **特点**:
  - 使用 `APITestHelper` 进行HTTP请求
  - 测试完整的API流程
  - 需要数据库连接
- **运行**: `pytest tests/integration/ -v`
- **文档**: 详见 `tests/integration/README_API_TESTING.md`

### 3. API测试 (`tests/api/`)
- **用途**: 测试API端点的基本功能
- **特点**: 
  - 与 `tests/integration/` 功能重叠
  - 可能包含更早期的测试实现
- **运行**: `pytest tests/api/ -v`

### 4. 端到端测试 (`tests/e2e/`)
- **用途**: 测试完整的业务流程
- **特点**:
  - 测试跨模块的完整流程
  - 执行时间较长
- **运行**: `pytest tests/e2e/ -v -m e2e`

### 5. 性能测试 (`tests/performance/`)
- **用途**: 测试系统性能指标
- **特点**:
  - 关注响应时间、吞吐量等
  - 可能需要特殊标记
- **运行**: `pytest tests/performance/ -v`

### 6. 手动测试脚本 (`tests/scripts/`)
- **用途**: 手动运行的测试脚本
- **特点**:
  - 使用 `requests` 直接调用API
  - 不是pytest测试套件
  - 需要手动执行
- **运行**: `python3 tests/scripts/test_*.py`

## 测试标记

使用 pytest markers 来分类测试：

```python
@pytest.mark.unit          # 单元测试
@pytest.mark.integration   # 集成测试
@pytest.mark.api           # API测试
@pytest.mark.e2e           # 端到端测试
@pytest.mark.slow          # 慢速测试
@pytest.mark.skip          # 跳过测试
```

## 运行测试

### 运行所有测试
```bash
pytest tests/ -v
```

### 运行特定类型测试
```bash
# 只运行单元测试
pytest tests/unit/ -v

# 只运行集成测试
pytest tests/integration/ -v

# 只运行API测试
pytest tests/api/ -v

# 使用标记运行
pytest -m unit -v
pytest -m integration -v
pytest -m "not slow" -v  # 排除慢速测试
```

### 运行特定文件
```bash
pytest tests/unit/test_stage_template_service.py -v
pytest tests/integration/test_projects_api_ai.py -v
```

### 运行API集成测试脚本
```bash
# 使用专用脚本
bash tests/run_api_integration_tests.sh

# 或指定模块
bash tests/run_api_integration_tests.sh projects
bash tests/run_api_integration_tests.sh materials
```

## 测试数据

- **测试数据工厂**: `tests/factories.py`
  - 使用 `factory_boy` 创建测试数据
  - 提供各种模型的工厂类

- **测试配置**: `tests/conftest.py`
  - pytest fixtures
  - 数据库会话管理
  - 测试用户创建

## 注意事项

1. **tests/api/ 和 tests/integration/ 的区别**:
   - `tests/integration/` 使用统一的 `APITestHelper`，更规范
   - `tests/api/` 可能包含更早期的实现
   - 建议新测试放在 `tests/integration/`

2. **手动测试脚本**:
   - `tests/scripts/` 中的文件不是pytest测试
   - 需要手动运行，用于调试或验证

3. **遗留文件**:
   - `tests/legacy/` 包含不再使用的测试文件
   - 保留用于参考，但不参与常规测试

## 测试覆盖率

查看测试覆盖率：
```bash
pytest --cov=app --cov-report=html
# 打开 htmlcov/index.html 查看详细报告
```

## 贡献指南

添加新测试时：
1. 单元测试 → `tests/unit/`
2. API集成测试 → `tests/integration/`
3. 端到端测试 → `tests/e2e/`
4. 性能测试 → `tests/performance/`
5. 手动脚本 → `tests/scripts/`

遵循现有测试的命名和结构约定。
