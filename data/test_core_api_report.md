# 核心业务API功能测试报告

**测试时间:** 2026-02-16T16:13:23.739980

## 测试概要

| 指标 | 数值 |
|------|------|
| 总测试数 | 53 |
| 通过 | 16 |
| 失败 | 37 |
| 成功率 | 30.19% |

## 模块测试结果

| 模块 | 总数 | 通过 | 失败 | 通过率 |
|------|------|------|------|--------|
| 用户管理 | 2 | 0 | 2 | 0.00% |
| 角色权限 | 3 | 0 | 3 | 0.00% |
| 项目管理 | 3 | 1 | 2 | 33.33% |
| 生产管理 | 8 | 1 | 7 | 12.50% |
| 销售管理 | 9 | 1 | 8 | 11.11% |

## 错误详情

### 错误 1: 用户管理 - 获取用户列表

**错误信息:** 获取用户列表 - 期望状态码200, 实际422

**响应内容:** ```
{"code":"VALIDATION_ERROR","message":"请求参数验证失败：query Field required","detail":[{"field":"query","message":"Field required"}]}
```

### 错误 2: 用户管理 - 创建用户

**错误信息:** 创建用户 - 期望状态码201, 实际422

**响应内容:** ```
{"code":"VALIDATION_ERROR","message":"请求参数验证失败：query Field required","detail":[{"field":"query","message":"Field required"}]}
```

### 错误 3: 角色权限 - 获取角色列表

**错误信息:** 获取角色列表 - 期望状态码200, 实际404

**响应内容:** ```
{"code":"HTTP_ERROR","message":"Not Found","detail":"Not Found"}
```

### 错误 4: 角色权限 - 获取权限列表

**错误信息:** 获取权限列表 - 期望状态码200, 实际404

**响应内容:** ```
{"code":"HTTP_ERROR","message":"Not Found","detail":"Not Found"}
```

### 错误 5: 角色权限 - 创建角色

**错误信息:** 创建角色 - 期望状态码201, 实际404

**响应内容:** ```
{"code":"HTTP_ERROR","message":"Not Found","detail":"Not Found"}
```

### 错误 6: 项目管理 - 获取项目统计

**错误信息:** 获取项目统计 - 期望状态码200, 实际422

**响应内容:** ```
{"code":"VALIDATION_ERROR","message":"请求参数验证失败：path Input should be a valid integer, unable to parse string as an integer","detail":[{"field":"path","message":"Input should be a valid integer, unable 
```

### 错误 7: 项目管理 - 创建项目

**错误信息:** 创建项目 - 期望状态码200, 实际422

**响应内容:** ```
{"code":"VALIDATION_ERROR","message":"请求参数验证失败：body Field required","detail":[{"field":"body","message":"Field required"}]}
```

### 错误 8: 项目管理 - 创建测试项目

**错误信息:** 创建测试项目 - 期望状态码201, 实际422

**响应内容:** ```
{"code":"VALIDATION_ERROR","message":"请求参数验证失败：body Field required","detail":[{"field":"body","message":"Field required"},{"field":"body","message":"Field required"}]}
```

### 错误 9: 项目管理 - 创建测试项目

**错误信息:** 创建测试项目 - 期望状态码201, 实际422

**响应内容:** ```
{"code":"VALIDATION_ERROR","message":"请求参数验证失败：body Field required","detail":[{"field":"body","message":"Field required"},{"field":"body","message":"Field required"}]}
```

### 错误 10: 项目管理 - 创建测试项目

**错误信息:** 创建测试项目 - 期望状态码201, 实际422

**响应内容:** ```
{"code":"VALIDATION_ERROR","message":"请求参数验证失败：body Field required","detail":[{"field":"body","message":"Field required"},{"field":"body","message":"Field required"}]}
```

### 错误 11: 项目管理 - 创建测试项目

**错误信息:** 创建测试项目 - 期望状态码201, 实际422

**响应内容:** ```
{"code":"VALIDATION_ERROR","message":"请求参数验证失败：body Field required","detail":[{"field":"body","message":"Field required"},{"field":"body","message":"Field required"}]}
```

### 错误 12: 项目管理 - 创建测试项目

**错误信息:** 创建测试项目 - 期望状态码201, 实际422

**响应内容:** ```
{"code":"VALIDATION_ERROR","message":"请求参数验证失败：body Field required","detail":[{"field":"body","message":"Field required"},{"field":"body","message":"Field required"}]}
```

### 错误 13: 项目管理 - 创建测试项目

**错误信息:** 创建测试项目 - 期望状态码201, 实际422

**响应内容:** ```
{"code":"VALIDATION_ERROR","message":"请求参数验证失败：body Field required","detail":[{"field":"body","message":"Field required"},{"field":"body","message":"Field required"}]}
```

### 错误 14: 项目管理 - 创建测试项目

**错误信息:** 创建测试项目 - 期望状态码201, 实际422

**响应内容:** ```
{"code":"VALIDATION_ERROR","message":"请求参数验证失败：body Field required","detail":[{"field":"body","message":"Field required"},{"field":"body","message":"Field required"}]}
```

### 错误 15: 项目管理 - 创建测试项目

**错误信息:** 创建测试项目 - 期望状态码201, 实际422

**响应内容:** ```
{"code":"VALIDATION_ERROR","message":"请求参数验证失败：body Field required","detail":[{"field":"body","message":"Field required"},{"field":"body","message":"Field required"}]}
```

### 错误 16: 项目管理 - 创建测试项目

**错误信息:** 创建测试项目 - 期望状态码201, 实际422

**响应内容:** ```
{"code":"VALIDATION_ERROR","message":"请求参数验证失败：body Field required","detail":[{"field":"body","message":"Field required"},{"field":"body","message":"Field required"}]}
```

### 错误 17: 生产管理 - 创建工单

**错误信息:** 创建工单 - 期望状态码200, 实际422

**响应内容:** ```
{"code":"VALIDATION_ERROR","message":"请求参数验证失败：body Field required","detail":[{"field":"body","message":"Field required"}]}
```

### 错误 18: 生产管理 - 创建测试工单

**错误信息:** 创建测试工单 - 期望状态码201, 实际422

**响应内容:** ```
{"code":"VALIDATION_ERROR","message":"请求参数验证失败：body Field required","detail":[{"field":"body","message":"Field required"},{"field":"body","message":"Field required"}]}
```

### 错误 19: 生产管理 - 创建测试工单

**错误信息:** 创建测试工单 - 期望状态码201, 实际422

**响应内容:** ```
{"code":"VALIDATION_ERROR","message":"请求参数验证失败：body Field required","detail":[{"field":"body","message":"Field required"},{"field":"body","message":"Field required"}]}
```

### 错误 20: 生产管理 - 创建测试工单

**错误信息:** 创建测试工单 - 期望状态码201, 实际422

**响应内容:** ```
{"code":"VALIDATION_ERROR","message":"请求参数验证失败：body Field required","detail":[{"field":"body","message":"Field required"},{"field":"body","message":"Field required"}]}
```

### 错误 21: 生产管理 - 质量检查列表

**错误信息:** 质量检查列表 - 期望状态码200, 实际404

**响应内容:** ```
{"code":"HTTP_ERROR","message":"Not Found","detail":"Not Found"}
```

### 错误 22: 生产管理 - 创建质量检查

**错误信息:** 创建质量检查 - 期望状态码200, 实际404

**响应内容:** ```
{"code":"HTTP_ERROR","message":"Not Found","detail":"Not Found"}
```

### 错误 23: 生产管理 - 物料跟踪列表

**错误信息:** 物料跟踪列表 - 期望状态码200, 实际404

**响应内容:** ```
{"code":"HTTP_ERROR","message":"Not Found","detail":"Not Found"}
```

### 错误 24: 生产管理 - 创建测试工单

**错误信息:** 创建测试工单 - 期望状态码201, 实际422

**响应内容:** ```
{"code":"VALIDATION_ERROR","message":"请求参数验证失败：body Field required","detail":[{"field":"body","message":"Field required"},{"field":"body","message":"Field required"}]}
```

### 错误 25: 生产管理 - 产能分析

**错误信息:** 产能分析 - 期望状态码200, 实际404

**响应内容:** ```
{"code":"HTTP_ERROR","message":"Not Found","detail":"Not Found"}
```

### 错误 26: 生产管理 - 设备状态

**错误信息:** 设备状态 - 期望状态码200, 实际404

**响应内容:** ```
{"code":"HTTP_ERROR","message":"Not Found","detail":"Not Found"}
```

### 错误 27: 生产管理 - 生产排程

**错误信息:** 生产排程 - 期望状态码200, 实际404

**响应内容:** ```
{"code":"HTTP_ERROR","message":"Not Found","detail":"Not Found"}
```

### 错误 28: 销售管理 - 客户管理列表

**错误信息:** 客户管理列表 - 期望状态码200, 实际500

**响应内容:** ```
Traceback (most recent call last):
  File "/Library/Frameworks/Python.framework/Versions/3.13/lib/python3.13/site-packages/sqlalchemy/engine/base.py", line 1967, in _exec_single_context
    self.diale
```

### 错误 29: 销售管理 - 创建客户

**错误信息:** 创建客户 - 期望状态码200, 实际422

**响应内容:** ```
{"code":"VALIDATION_ERROR","message":"请求参数验证失败：body Field required","detail":[{"field":"body","message":"Field required"}]}
```

### 错误 30: 销售管理 - 获取客户列表(临时)

**错误信息:** 获取客户列表(临时) - 期望状态码200, 实际500

**响应内容:** ```
Traceback (most recent call last):
  File "/Library/Frameworks/Python.framework/Versions/3.13/lib/python3.13/site-packages/sqlalchemy/engine/base.py", line 1967, in _exec_single_context
    self.diale
```

### 错误 31: 销售管理 - 创建测试客户

**错误信息:** 创建测试客户 - 期望状态码201, 实际422

**响应内容:** ```
{"code":"VALIDATION_ERROR","message":"请求参数验证失败：body Field required","detail":[{"field":"body","message":"Field required"}]}
```

### 错误 32: 销售管理 - 合同管理列表

**错误信息:** 合同管理列表 - 期望状态码200, 实际500

**响应内容:** ```
  + Exception Group Traceback (most recent call last):
  |   File "/Library/Frameworks/Python.framework/Versions/3.13/lib/python3.13/site-packages/starlette/_utils.py", line 77, in collapse_excgroups

```

### 错误 33: 销售管理 - 创建合同

**错误信息:** 创建合同 - 期望状态码200, 实际422

**响应内容:** ```
{"code":"VALIDATION_ERROR","message":"请求参数验证失败：body Field required","detail":[{"field":"body","message":"Field required"},{"field":"body","message":"Input should be a valid integer"}]}
```

### 错误 34: 销售管理 - 创建回款记录

**错误信息:** 创建回款记录 - 期望状态码200, 实际422

**响应内容:** ```
{"code":"VALIDATION_ERROR","message":"请求参数验证失败：query Field required","detail":[{"field":"query","message":"Field required"},{"field":"query","message":"Field required"},{"field":"query","message":"Fie
```

### 错误 35: 销售管理 - 销售业绩统计

**错误信息:** 销售业绩统计 - 期望状态码200, 实际404

**响应内容:** ```
{"code":"HTTP_ERROR","message":"Not Found","detail":"Not Found"}
```

### 错误 36: 销售管理 - 销售机会列表

**错误信息:** 销售机会列表 - 期望状态码200, 实际500

**响应内容:** ```
Traceback (most recent call last):
  File "/Library/Frameworks/Python.framework/Versions/3.13/lib/python3.13/site-packages/sqlalchemy/engine/base.py", line 1967, in _exec_single_context
    self.diale
```

### 错误 37: 销售管理 - 报价单列表

**错误信息:** 报价单列表 - 期望状态码200, 实际500

**响应内容:** ```
Traceback (most recent call last):
  File "/Library/Frameworks/Python.framework/Versions/3.13/lib/python3.13/site-packages/sqlalchemy/engine/base.py", line 1967, in _exec_single_context
    self.diale
```


## 测试覆盖范围

### 已测试模块

- ✅ 用户管理（CRUD操作）
- ✅ 角色权限管理
- ✅ 项目管理（核心API抽样）
- ✅ 生产管理（核心API抽样）
- ✅ 销售管理（核心API抽样）

### API覆盖率

- 总API数: 555+
- 已测试核心API: 53
- 覆盖率: ~9.5%