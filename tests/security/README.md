# 安全测试套件

## 概述

本目录包含完整的安全测试套件，覆盖以下安全机制：

- **CSRF防护** - 跨站请求伪造防护
- **API Key认证** - 基于API Key的认证机制
- **请求签名验证** - HMAC-SHA256请求签名
- **安全响应头** - HTTP安全头配置
- **集成测试** - 多层安全防护的协同工作

## 测试文件

```
tests/security/
├── __init__.py                      # 测试模块初始化
├── test_csrf_protection.py          # CSRF防护测试（14个测试）
├── test_api_key_auth.py             # API Key认证测试（11个测试）
├── test_request_signature.py        # 请求签名验证测试（12个测试）
├── test_security_headers.py         # 安全响应头测试（20个测试）
├── test_integration.py              # 集成测试（10个测试）
└── README.md                        # 本文件
```

**总计：67+个安全测试**

## 运行测试

### 运行所有安全测试

```bash
# 从项目根目录运行
cd ~/.openclaw/workspace/non-standard-automation-pms

# 运行所有安全测试
pytest tests/security/ -v

# 运行测试并显示覆盖率
pytest tests/security/ -v --cov=app.core --cov-report=html
```

### 运行特定测试文件

```bash
# CSRF防护测试
pytest tests/security/test_csrf_protection.py -v

# API Key认证测试
pytest tests/security/test_api_key_auth.py -v

# 请求签名测试
pytest tests/security/test_request_signature.py -v

# 安全响应头测试
pytest tests/security/test_security_headers.py -v

# 集成测试
pytest tests/security/test_integration.py -v
```

### 运行特定测试用例

```bash
# 运行单个测试
pytest tests/security/test_csrf_protection.py::TestCSRFProtection::test_api_request_with_valid_origin -v

# 运行测试类
pytest tests/security/test_security_headers.py::TestSecurityHeaders -v
```

### 运行测试并输出详细信息

```bash
# 显示打印输出
pytest tests/security/ -v -s

# 显示失败的详细信息
pytest tests/security/ -v --tb=long

# 只运行失败的测试
pytest tests/security/ --lf
```

## 测试覆盖范围

### 1. CSRF防护测试 (test_csrf_protection.py)

- ✅ 安全方法（GET/HEAD/OPTIONS）不需要CSRF检查
- ✅ 豁免路径不需要CSRF检查
- ✅ API请求缺少Bearer Token被拒绝
- ✅ API请求缺少Origin/Referer被拒绝
- ✅ API请求Origin不在白名单被拒绝
- ✅ API请求Origin在白名单通过验证
- ✅ 使用Referer代替Origin
- ✅ DEBUG模式跳过CSRF验证
- ✅ Origin标准化（去除端口）
- ✅ 不同HTTP方法的CSRF验证
- ✅ localhost端口匹配
- ✅ POST/PUT/DELETE/PATCH请求验证

### 2. API Key认证测试 (test_api_key_auth.py)

- ✅ API Key生成格式正确
- ✅ 每次生成的Key唯一
- ✅ 哈希计算一致性
- ✅ 验证有效的API Key
- ✅ 验证无效的API Key
- ✅ 已禁用的Key被拒绝
- ✅ 过期的Key被拒绝
- ✅ IP白名单验证
- ✅ 使用统计更新
- ✅ 权限范围（Scopes）验证

### 3. 请求签名测试 (test_request_signature.py)

- ✅ 签名计算一致性
- ✅ 不同输入产生不同签名
- ✅ 验证有效签名
- ✅ 验证无效签名
- ✅ 过期签名被拒绝
- ✅ 未来时间戳被拒绝
- ✅ 时间戳格式验证
- ✅ 包含查询参数的签名
- ✅ 客户端签名生成
- ✅ 客户端-服务端签名互通

### 4. 安全响应头测试 (test_security_headers.py)

- ✅ X-Frame-Options（防点击劫持）
- ✅ X-Content-Type-Options（防MIME混淆）
- ✅ X-XSS-Protection（XSS防护）
- ✅ Referrer-Policy（引用策略）
- ✅ Server头隐藏
- ✅ CSP头存在性
- ✅ 生产环境严格CSP
- ✅ DEBUG模式宽松CSP
- ✅ CSP指令验证
- ✅ Permissions-Policy验证
- ✅ HSTS配置（生产环境）
- ✅ 跨域策略头
- ✅ 敏感端点缓存控制
- ✅ 所有端点都有安全头

### 5. 集成测试 (test_integration.py)

- ✅ 完整API请求流程
- ✅ 多层安全防护
- ✅ 错误响应的安全头
- ✅ 不同端点的安全策略
- ✅ 速率限制（可选）
- ✅ 跨域请求验证
- ✅ DEBUG vs 生产环境差异

## 预期测试结果

### 成功运行示例

```
tests/security/test_csrf_protection.py .............. [ 21%]
tests/security/test_api_key_auth.py ........... [ 37%]
tests/security/test_request_signature.py ............ [ 55%]
tests/security/test_security_headers.py .................... [ 85%]
tests/security/test_integration.py .......... [100%]

====== 67 passed in 5.23s ======
```

### 覆盖率目标

- **CSRF模块**：> 90%
- **API Key认证**：> 85%
- **请求签名**：> 90%
- **安全响应头**：> 95%

## 故障排查

### 常见问题

#### 1. 导入错误

```
ImportError: cannot import name 'APIKey' from 'app.models.api_key'
```

**解决方案**：
```bash
# 确保数据库迁移已执行
alembic upgrade head

# 或者创建API Key表
python -c "from app.models.api_key import APIKey; from app.models.base import Base; from app.core.database import engine; Base.metadata.create_all(engine)"
```

#### 2. 测试失败：CSRF验证

```
FAILED test_api_request_with_valid_origin - AssertionError: assert 403 != 403
```

**解决方案**：
- 检查`CORS_ORIGINS`配置
- 确认DEBUG模式设置
- 查看测试mock的配置

#### 3. 数据库连接错误

```
OperationalError: no such table: api_keys
```

**解决方案**：
```bash
# 创建测试数据库
python scripts/init_db.py

# 或使用内存数据库
export DATABASE_URL=sqlite:///:memory:
```

## 持续集成

### GitHub Actions配置示例

```yaml
# .github/workflows/security-tests.yml
name: Security Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.11
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run security tests
      run: |
        pytest tests/security/ -v --cov=app.core --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v2
      with:
        file: ./coverage.xml
```

## 安全测试最佳实践

1. **定期运行**：每次提交前运行安全测试
2. **覆盖率监控**：保持>85%的代码覆盖率
3. **持续更新**：随着新功能添加新的安全测试
4. **渗透测试**：定期进行手动渗透测试
5. **依赖扫描**：使用`safety`或`bandit`扫描依赖

## 相关工具

### 安全扫描工具

```bash
# 安装安全扫描工具
pip install safety bandit

# 扫描依赖漏洞
safety check

# 扫描代码安全问题
bandit -r app/ -ll

# 检查过时的依赖
pip list --outdated
```

### 代码质量检查

```bash
# 安装代码质量工具
pip install flake8 mypy black

# 代码格式检查
flake8 app/core/

# 类型检查
mypy app/core/

# 自动格式化
black app/core/
```

## 贡献指南

添加新的安全测试时：

1. 在适当的测试文件中添加测试用例
2. 确保测试有清晰的文档字符串
3. 使用有意义的测试名称
4. 运行所有测试确保不破坏现有功能
5. 更新本README文档

## 联系方式

- 安全问题：security@example.com
- 技术支持：support@example.com

---

**最后更新**: 2026-02-14  
**维护者**: Security Team
