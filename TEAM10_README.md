# Team 10: 售前AI系统集成与前端UI

## 🎯 项目简介

售前AI系统是一套智能化的售前工作辅助平台，集成了9大AI功能，提供完整的售前工作流自动化解决方案。

### 核心功能

✨ **AI工作流引擎** - 自动化售前工作流程  
📊 **智能仪表盘** - 实时监控AI使用情况  
🤖 **9大AI功能** - 涵盖售前全流程  
📱 **响应式设计** - 支持PC和移动端  
🔐 **安全审计** - 完整的操作日志记录  

---

## 🚀 快速开始

### 前置要求

- Python 3.9+
- Node.js 18+
- MySQL 8.0+
- Git

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd non-standard-automation-pms
```

2. **安装后端依赖**
```bash
pip install -r requirements.txt
```

3. **配置数据库**
```bash
# 创建数据库
mysql -u root -p -e "CREATE DATABASE presale_ai CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 运行迁移
alembic upgrade head

# 运行Team 10迁移
alembic upgrade team10_ai_integration
```

4. **配置环境变量**
```bash
cp .env.example .env
# 编辑.env文件，配置数据库和API密钥
```

5. **启动后端服务**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

6. **安装前端依赖**
```bash
cd frontend
npm install
```

7. **启动前端服务**
```bash
npm run dev
```

8. **访问系统**
- 前端: http://localhost:5173
- 后端API: http://localhost:8000
- API文档: http://localhost:8000/docs

---

## 📚 文档

### 用户文档
- [用户使用手册](docs/TEAM10_USER_MANUAL.md) - 详细的使用指南
- [快速上手视频](docs/videos/) - 操作演示视频

### 技术文档
- [API完整文档](docs/TEAM10_API_DOCUMENTATION.md) - 所有API端点说明
- [系统管理员手册](docs/TEAM10_ADMIN_MANUAL.md) - 部署和维护指南
- [实施总结报告](docs/TEAM10_IMPLEMENTATION_REPORT.md) - 项目实施详情

---

## 🏗️ 项目结构

```
non-standard-automation-pms/
├── app/                          # 后端应用
│   ├── api/                      # API路由
│   │   └── v1/
│   │       └── presale_ai_integration.py  # AI集成API
│   ├── models/                   # 数据模型
│   │   └── presale_ai.py         # AI相关模型
│   ├── schemas/                  # Pydantic Schemas
│   │   └── presale_ai.py         # AI相关Schemas
│   └── services/                 # 业务逻辑
│       └── presale_ai_integration.py  # AI集成服务
├── frontend/                     # 前端应用
│   └── src/
│       ├── pages/PresaleAI/      # AI页面
│       │   ├── AIDashboard.jsx   # AI仪表盘
│       │   └── AIWorkbench.jsx   # AI工作台
│       ├── components/PresaleAI/ # AI组件
│       │   ├── AIStatsChart.jsx
│       │   ├── AIWorkflowProgress.jsx
│       │   └── AIFeedbackDialog.jsx
│       └── services/
│           └── presaleAIService.js  # AI服务API
├── migrations/                   # 数据库迁移
│   └── versions/
│       └── team10_ai_integration_tables.py
├── tests/                        # 测试文件
│   └── test_presale_ai_integration.py
└── docs/                         # 文档
    ├── TEAM10_API_DOCUMENTATION.md
    ├── TEAM10_USER_MANUAL.md
    └── TEAM10_ADMIN_MANUAL.md
```

---

## 🤖 AI功能列表

| 功能 | 说明 | API端点 | 状态 |
|------|------|---------|------|
| 需求理解 | AI分析客户需求 | `/ai/requirement/analyze` | ✅ |
| 方案生成 | 自动生成技术方案 | `/ai/solution/generate` | ✅ |
| 成本估算 | 智能成本评估 | `/ai/cost/estimate` | ✅ |
| 赢率预测 | 项目赢率分析 | `/ai/winrate/predict` | ✅ |
| 报价生成 | 生成正式报价 | `/ai/quotation/generate` | ✅ |
| 知识库 | 推荐相关知识 | `/ai/knowledge/search` | ✅ |
| 话术助手 | 推荐销售话术 | `/ai/script/recommend` | ✅ |
| 情绪分析 | 分析客户情绪 | `/ai/emotion/analyze` | ✅ |
| 移动助手 | 移动端AI助手 | `/ai/mobile/*` | ✅ |

---

## 🧪 测试

### 运行后端测试

```bash
# 运行所有测试
pytest

# 运行AI集成测试
pytest tests/test_presale_ai_integration.py

# 查看测试覆盖率
pytest --cov=app tests/
```

### 运行前端测试

```bash
cd frontend

# 运行组件测试
npm test

# 运行E2E测试
npm run test:e2e
```

---

## 📊 API端点

### 核心端点

```bash
# 获取AI仪表盘统计
GET /api/v1/presale/ai/dashboard/stats?days=30

# 启动AI工作流
POST /api/v1/presale/ai/workflow/start
{
  "presale_ticket_id": 123,
  "initial_data": {},
  "auto_run": true
}

# 获取工作流状态
GET /api/v1/presale/ai/workflow/status/{ticket_id}

# 提交AI反馈
POST /api/v1/presale/ai/feedback
{
  "ai_function": "requirement",
  "rating": 5,
  "feedback_text": "很好用"
}

# 健康检查
GET /api/v1/presale/ai/health-check
```

完整API文档请查看: [TEAM10_API_DOCUMENTATION.md](docs/TEAM10_API_DOCUMENTATION.md)

---

## 🛠️ 配置

### AI功能配置

通过API更新AI配置:

```bash
curl -X POST "http://localhost:8000/api/v1/presale/ai/config/update?ai_function=requirement" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": true,
    "temperature": 0.7,
    "max_tokens": 2000,
    "timeout_seconds": 30
  }'
```

### 环境变量

主要配置项 (`.env`):

```bash
# 数据库
DATABASE_URL=mysql+pymysql://user:pass@localhost/presale_ai

# AI服务
OPENAI_API_KEY=sk-xxx
OPENAI_MODEL=gpt-4

# 安全
SECRET_KEY=your-secret-key
```

---

## 🎯 使用示例

### Python示例

```python
import requests

# 认证
headers = {"Authorization": "Bearer YOUR_TOKEN"}

# 获取AI统计
response = requests.get(
    "http://localhost:8000/api/v1/presale/ai/dashboard/stats",
    headers=headers
)
print(response.json())

# 启动工作流
workflow_data = {
    "presale_ticket_id": 123,
    "auto_run": True
}
response = requests.post(
    "http://localhost:8000/api/v1/presale/ai/workflow/start",
    headers=headers,
    json=workflow_data
)
print(response.json())
```

### JavaScript示例

```javascript
// 获取AI统计
const stats = await fetch('/api/v1/presale/ai/dashboard/stats', {
  headers: { 'Authorization': 'Bearer TOKEN' }
}).then(res => res.json());

console.log(stats);

// 提交反馈
const feedback = await fetch('/api/v1/presale/ai/feedback', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer TOKEN',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    ai_function: 'requirement',
    rating: 5,
    feedback_text: '非常好用'
  })
}).then(res => res.json());
```

---

## 🐛 故障排查

### 常见问题

**Q: AI处理失败**
```bash
# 检查AI配置
curl http://localhost:8000/api/v1/presale/ai/config

# 查看健康状态
curl http://localhost:8000/api/v1/presale/ai/health-check
```

**Q: 数据库连接失败**
```bash
# 检查MySQL状态
systemctl status mysql

# 测试连接
mysql -u user -p presale_ai
```

**Q: 前端无法访问API**
```bash
# 检查CORS配置
# 查看 app/main.py 中的 CORS 设置
```

---

## 📈 性能

### 性能指标

- API响应时间: <200ms
- AI处理时间: <25s
- 页面加载时间: <1s
- 并发支持: 100+ 用户

### 优化建议

1. 启用Redis缓存
2. 配置数据库连接池
3. 使用CDN加速静态资源
4. 启用Gzip压缩

---

## 🔐 安全

### 安全特性

- ✅ JWT认证
- ✅ 权限控制
- ✅ 操作审计日志
- ✅ 数据加密传输
- ✅ SQL注入防护
- ✅ XSS防护

### 安全最佳实践

1. 定期更新依赖
2. 使用强密码策略
3. 定期备份数据
4. 监控异常访问
5. 启用HTTPS

---

## 🤝 贡献

欢迎贡献代码！

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

---

## 📞 支持

### 获取帮助

- 📧 技术支持: support@example.com
- 📱 电话: 400-XXX-XXXX
- 💬 在线文档: http://docs.example.com
- 🐛 问题反馈: [GitHub Issues](https://github.com/xxx/issues)

### 培训资源

- [视频教程](docs/videos/)
- [在线培训](https://training.example.com)
- [FAQ](docs/FAQ.md)

---

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

---

## 🎉 致谢

感谢所有贡献者的辛勤付出！

特别感谢：
- Team 1-9 提供的AI功能模块
- 产品团队提供的需求和设计
- 测试团队提供的反馈

---

**Team 10 - 售前AI系统集成团队**

最后更新: 2026-02-15
