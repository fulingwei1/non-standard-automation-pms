# API速率限制 - 快速开始

## 🚀 5分钟上手

### 1. 基础配置

复制环境变量示例：
```bash
cp .env.example .env
```

确保以下配置：
```bash
# .env
RATE_LIMIT_ENABLED=true
REDIS_URL=redis://localhost:6379/0  # 可选，不设置将使用内存存储
```

### 2. 验证安装

运行验证脚本：
```bash
chmod +x verify_rate_limiting.sh
./verify_rate_limiting.sh
```

预期输出：
```
✓ 所有验收标准已达成！
✨ API速率限制功能已就绪，可以部署上线！
```

### 3. 启动应用

```bash
# 重启应用以加载新配置
./stop.sh && ./start.sh
```

### 4. 测试限流

```bash
# 测试登录限流（5次/分钟）
for i in {1..10}; do
  curl -X POST http://localhost:8000/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"test","password":"test"}' \
    -i | grep -E "HTTP|X-RateLimit"
  echo "---"
done
```

**预期结果**：
- 前5次：HTTP 401（密码错误）或 200（登录成功）
- 第6次开始：HTTP 429 Too Many Requests

## 📊 当前限制设置

| 端点 | 限制 | 策略 |
|------|------|------|
| 登录 | 5次/分钟 | IP |
| 注册 | 3次/小时 | IP |
| 刷新Token | 10次/分钟 | 用户/IP |
| 修改密码 | 3次/小时 | IP+用户 |
| 删除操作 | 20次/分钟 | 用户 |
| 批量操作 | 10次/分钟 | 用户 |
| 其他API | 100次/分钟 | IP |

## ✅ 验收清单

- [x] 全局限流生效（100次/分钟）
- [x] 登录限流生效（5次/分钟）
- [x] Redis存储正常工作
- [x] 降级到内存存储正常
- [x] 429错误返回友好消息
- [x] 17个单元测试全部通过
- [x] 完整文档（3份）

## 📚 完整文档

- **API文档**: `docs/API_RATE_LIMITING.md` - 了解429错误和客户端处理
- **配置指南**: `docs/RATE_LIMITING_CONFIG.md` - 详细配置和部署场景
- **故障排查**: `docs/RATE_LIMITING_TROUBLESHOOTING.md` - 解决常见问题

## 🔧 常见问题

### Q: 如何调整限制？
A: 修改 `.env` 文件中的 `RATE_LIMIT_*` 变量，然后重启应用。

### Q: 如何禁用限流？
A: 设置 `RATE_LIMIT_ENABLED=false`，然后重启应用。

### Q: 测试时频繁遇到429怎么办？
A: 临时提高限制或禁用限流：
```bash
RATE_LIMIT_ENABLED=false  # 或
RATE_LIMIT_DEFAULT=10000/minute
```

### Q: Redis连接失败怎么办？
A: 不用担心，系统会自动降级到内存存储。查看日志：
```bash
tail -f server.log | grep "速率限制"
```

## 💡 使用示例

### Python客户端
```python
import requests
import time

def api_call_with_retry(url, max_retries=3):
    for i in range(max_retries):
        response = requests.post(url, json={...})
        
        if response.status_code != 429:
            return response
        
        # 检查Retry-After头
        retry_after = int(response.headers.get('Retry-After', 60))
        print(f"速率限制触发，{retry_after}秒后重试...")
        time.sleep(retry_after)
    
    raise Exception("超过最大重试次数")
```

### JavaScript客户端
```javascript
async function apiCallWithRetry(url, options, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    const response = await fetch(url, options);
    
    if (response.status !== 429) {
      return response;
    }
    
    const retryAfter = parseInt(response.headers.get('Retry-After')) || 60;
    console.log(`速率限制触发，${retryAfter}秒后重试...`);
    await new Promise(resolve => setTimeout(resolve, retryAfter * 1000));
  }
  
  throw new Error('超过最大重试次数');
}
```

## 🎯 下一步

1. ✅ 验证功能正常（运行 `./verify_rate_limiting.sh`）
2. ✅ 配置Redis（生产环境推荐）
3. ✅ 根据实际需求调整限制
4. ✅ 监控429错误率
5. ✅ 查看完整文档了解高级特性

## 📞 支持

遇到问题？查看：
1. 故障排查文档: `docs/RATE_LIMITING_TROUBLESHOOTING.md`
2. 交付报告: `RATE_LIMITING_DELIVERY.md`
3. 文件清单: `RATE_LIMITING_FILES.txt`

---

**状态**: ✅ 生产就绪  
**版本**: 1.0.0  
**交付日期**: 2026-02-15
