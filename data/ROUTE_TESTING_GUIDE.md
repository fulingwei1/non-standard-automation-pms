# API路由测试快速指南

## 概述

Team 2创建了完整的API路由测试工具链，用于扫描和验证系统中的740个API routes。

## 工具列表

### 1. extract_routes.py - 路由提取
提取所有registered routes，生成JSON格式列表。

```bash
python3 scripts/extract_routes.py
```

**输出**: `data/extracted_routes.json`

### 2. verify_core_apis.py - 核心API验证
快速验证12个核心业务endpoints是否正常。

```bash
python3 scripts/verify_core_apis.py
```

**输出**: `data/core_api_verification.txt`

### 3. test_all_routes.py - 完整路由测试
批量测试所有GET endpoints，自动分类结果。

```bash
python3 scripts/test_all_routes.py
```

**输出**: 
- `data/route_test_report.txt` (文本报告)
- `data/route_test_results.json` (JSON格式)

### 4. debug_auth.py - 认证调试
诊断认证和token相关问题。

```bash
python3 scripts/debug_auth.py
```

## 使用流程

### 标准流程

```bash
cd ~/.openclaw/workspace/non-standard-automation-pms

# 步骤1: 提取所有routes
python3 scripts/extract_routes.py

# 步骤2: 快速验证核心API (等待60秒避免rate limiting)
sleep 60
python3 scripts/verify_core_apis.py

# 步骤3: 如果核心API正常，运行完整测试
python3 scripts/test_all_routes.py

# 步骤4: 查看结果
cat data/route_test_report.txt
```

### 问题诊断流程

如果遇到认证问题：

```bash
# 运行调试脚本
sleep 60  # 等待rate limiting
python3 scripts/debug_auth.py
```

## 报告解读

### route_test_report.txt

测试结果分为8类：

1. **✅ 正常 (2xx)** - 成功响应
2. **🔒 需要权限 (401/403)** - 权限问题 (可能正常)
3. **⚠️ 路径参数缺失** - 需要路径参数，已跳过
4. **❌ 404 Not Found** - 路由不存在 ⚠️
5. **❌ 422 Validation Error** - 参数验证失败 ⚠️
6. **❌ 500 Server Error** - 服务器错误 ⚠️
7. **⏭️ 跳过测试** - 非GET或需要body
8. **❓ 其他错误** - 未分类的错误

### 关注重点

优先修复：
- ❌ 404 Not Found
- ❌ 500 Server Error
- ❌ 422 Validation Error (如果不应该出现)

## 注意事项

### Rate Limiting

登录接口有速率限制 (5次/分钟)，因此：

1. 测试之间至少间隔60秒
2. 脚本已内置自动重试和延迟
3. 如果仍遇到429错误，等待更长时间

### Token过期

Token有效期24小时，但测试会自动获取新token。

### 服务器状态

确保服务器运行在 http://127.0.0.1:8000

```bash
# 检查服务器
curl http://127.0.0.1:8000/health

# 或查看文档
open http://127.0.0.1:8000/docs
```

## 常见问题

### Q: 所有API返回401？
**A**: 检查User2FA模型是否已导出 (已修复in `app/models/__init__.py`)

### Q: 测试很慢？
**A**: 正常，740个routes需要时间。可以先运行`verify_core_apis.py`快速检查。

### Q: 429 Too Many Requests？
**A**: 等待60-120秒后重试。

### Q: 如何只测试特定模块？
**A**: 修改`verify_core_apis.py`中的`core_endpoints`列表。

## 输出文件位置

所有输出文件在 `data/` 目录：

```
data/
├── extracted_routes.json          # 740个routes列表
├── route_test_report.txt          # 测试报告 (文本)
├── route_test_results.json        # 测试结果 (JSON)
├── core_api_verification.txt      # 核心API验证
├── route_fix_plan.md              # 修复方案
├── team2_final_report.md          # 技术报告
└── team2_deliverables.md          # 交付清单
```

## 下一步

1. ✅ 核心API验证通过 → 运行完整测试
2. ❌ 发现问题 → 查看`route_fix_plan.md`
3. 📝 生成报告 → 提交问题清单给开发团队

## 支持

- **技术报告**: `data/team2_final_report.md`
- **修复方案**: `data/route_fix_plan.md`
- **任务总结**: `TEAM2_COMPLETION.md`

---

*创建时间: 2026-02-16*  
*维护者: Team 2 Subagent*
