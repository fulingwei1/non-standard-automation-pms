# 剩余优化任务清单

## 🔴 P2 - 中等优先级

### 1. Presale Statistics双重prefix
- **问题**: `/presale/presale/statistics/*`
- **预计时间**: 5-10分钟
- **Team**: 1人

### 2. 预售模板404问题
- **问题**: `/api/v1/presale/templates` 返回404
- **预计时间**: 10-15分钟
- **Team**: 1人

## 🟡 P3 - 低优先级

### 3. 权限管理模块缺失
- **问题**: permissions.py不存在
- **影响**: 可用角色API代替
- **预计时间**: 30-45分钟
- **Team**: 1人（可选）

### 4. 工时分析Pydantic递归
- **问题**: 所有20个schema都递归错误
- **影响**: 基础工时功能正常
- **预计时间**: 1-2小时
- **Team**: 1人（深度调试，可选）

---

## 📊 推荐Agent Teams配置

**快速修复组** (2 Teams, ~15分钟):
- Team 1: Presale Statistics双重prefix
- Team 2: 预售模板404问题

**深度优化组** (2 Teams, ~1-2小时, 可选):
- Team 3: 权限管理模块创建
- Team 4: 工时分析Pydantic递归深度调试

---

**建议**: 先启动快速修复组（2 Teams），完成后再决定是否启动深度优化组
