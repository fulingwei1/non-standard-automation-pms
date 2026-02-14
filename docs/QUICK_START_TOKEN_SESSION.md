# Token刷新和会话管理 - 快速开始

## 5分钟快速上手

### 1. 安装依赖

```bash
pip install user-agents==2.2.0
```

### 2. 运行数据库迁移

```bash
# SQLite
sqlite3 data/app.db < migrations/20260214_user_sessions_sqlite.sql

# 或者 MySQL
# mysql -u root -p your_db < migrations/20260214_user_sessions_mysql.sql
```

### 3. 配置环境变量（可选）

```bash
# .env 文件
SECRET_KEY=your-secret-key-here
REDIS_URL=redis://localhost:6379/0
```

### 4. 启动服务

```bash
python -m app.main
```

## API使用示例

### 登录获取Token

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

**响应**：
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 86400,
  "refresh_expires_in": 604800
}
```

### 刷新Access Token

```bash
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "eyJ..."}'
```

### 查看活跃会话

```bash
curl -X GET http://localhost:8000/api/v1/auth/sessions \
  -H "Authorization: Bearer eyJ..."
```

### 强制下线其他设备

```bash
curl -X POST http://localhost:8000/api/v1/auth/sessions/revoke-all \
  -H "Authorization: Bearer eyJ..."
```

## 前端集成

### React示例

```javascript
import axios from 'axios';

class AuthService {
  constructor() {
    this.accessToken = null;
    this.refreshToken = null;
    
    // 设置axios拦截器
    this.setupInterceptors();
  }
  
  setupInterceptors() {
    // 请求拦截器：添加Token
    axios.interceptors.request.use(config => {
      if (this.accessToken) {
        config.headers.Authorization = `Bearer ${this.accessToken}`;
      }
      return config;
    });
    
    // 响应拦截器：自动刷新Token
    axios.interceptors.response.use(
      response => response,
      async error => {
        if (error.response?.status === 401) {
          try {
            await this.refresh();
            return axios.request(error.config);
          } catch (refreshError) {
            this.logout();
            window.location.href = '/login';
          }
        }
        return Promise.reject(error);
      }
    );
  }
  
  async login(username, password) {
    const response = await axios.post('/api/v1/auth/login', 
      new URLSearchParams({ username, password })
    );
    
    this.accessToken = response.data.access_token;
    this.refreshToken = response.data.refresh_token;
    
    // 设置自动刷新（提前5分钟）
    const refreshTime = (response.data.expires_in - 300) * 1000;
    setTimeout(() => this.refresh(), refreshTime);
    
    return response.data;
  }
  
  async refresh() {
    const response = await axios.post('/api/v1/auth/refresh', {
      refresh_token: this.refreshToken
    });
    
    this.accessToken = response.data.access_token;
    
    // 重新设置定时器
    const refreshTime = (response.data.expires_in - 300) * 1000;
    setTimeout(() => this.refresh(), refreshTime);
  }
  
  async logout(logoutAll = false) {
    await axios.post('/api/v1/auth/logout', { logout_all: logoutAll });
    this.accessToken = null;
    this.refreshToken = null;
  }
  
  async getSessions() {
    const response = await axios.get('/api/v1/auth/sessions');
    return response.data.sessions;
  }
  
  async revokeSession(sessionId) {
    await axios.post('/api/v1/auth/sessions/revoke', { session_id: sessionId });
  }
}

export default new AuthService();
```

### Vue示例

```javascript
// store/auth.js
export default {
  state: {
    accessToken: null,
    refreshToken: null,
    user: null,
  },
  
  mutations: {
    setTokens(state, { accessToken, refreshToken }) {
      state.accessToken = accessToken;
      state.refreshToken = refreshToken;
    },
    setUser(state, user) {
      state.user = user;
    },
  },
  
  actions: {
    async login({ commit }, { username, password }) {
      const response = await this.$axios.post('/api/v1/auth/login', 
        new URLSearchParams({ username, password })
      );
      
      commit('setTokens', {
        accessToken: response.data.access_token,
        refreshToken: response.data.refresh_token,
      });
      
      // 启动自动刷新
      this.dispatch('startAutoRefresh', response.data.expires_in);
    },
    
    async refresh({ state, commit }) {
      const response = await this.$axios.post('/api/v1/auth/refresh', {
        refresh_token: state.refreshToken
      });
      
      commit('setTokens', {
        accessToken: response.data.access_token,
        refreshToken: state.refreshToken, // 保持不变
      });
    },
    
    startAutoRefresh({ dispatch }, expiresIn) {
      // 提前5分钟刷新
      const refreshTime = (expiresIn - 300) * 1000;
      setTimeout(() => dispatch('refresh'), refreshTime);
    },
  },
};
```

## 测试

```bash
# 运行所有测试
pytest tests/test_session_management.py -v

# 运行特定测试
pytest tests/test_session_management.py::TestTokenGeneration -v

# 查看覆盖率
pytest tests/test_session_management.py --cov=app.services.session_service --cov-report=html
```

## 监控

### 查看活跃会话数
```bash
redis-cli
> KEYS session:*
> KEYS jwt:blacklist:*
```

### 查看日志
```bash
tail -f server.log | grep -E "(LOGIN|TOKEN_REFRESH|SESSION_REVOKE)"
```

## 常见问题

### Q1: Refresh Token过期了怎么办？
A: 用户需要重新登录。建议在客户端设置过期提醒。

### Q2: 如何清理过期会话？
A: 系统会自动清理，也可以手动调用：
```python
from app.services.session_service import SessionService
SessionService.cleanup_expired_sessions(db)
```

### Q3: Redis不可用会怎样？
A: 系统会自动降级到内存黑名单，但重启后会丢失。

### Q4: 如何修改会话数量限制？
A: 编辑 `app/services/session_service.py`：
```python
class SessionService:
    MAX_SESSIONS_PER_USER = 10  # 改为10个
```

## 下一步

- 📖 阅读完整文档：[TOKEN_SESSION_MANAGEMENT.md](./TOKEN_SESSION_MANAGEMENT.md)
- 🔒 了解安全措施：[SECURITY_TOKEN_SESSION.md](./SECURITY_TOKEN_SESSION.md)
- 📊 查看实施报告：[TOKEN_SESSION_IMPLEMENTATION_REPORT.md](../TOKEN_SESSION_IMPLEMENTATION_REPORT.md)

## 支持

遇到问题？
1. 查看日志：`tail -f server.log`
2. 检查Redis：`redis-cli ping`
3. 运行测试：`pytest tests/test_session_management.py -v`

祝使用愉快！🎉
