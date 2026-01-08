# API安全审查检查清单

**审查日期：** _____________
**审查人员：** _____________
**系统：** 工程师进度管理系统
**版本：** v1.0.0

---

## 📋 审查概述

### 审查目标
- ✅ 识别OWASP Top 10安全风险
- ✅ 验证认证和授权机制
- ✅ 检查输入验证和输出编码
- ✅ 评估文件上传安全性
- ✅ 检查敏感数据保护

### 审查范围
- **API端点：** 16个工程师端点
- **认证系统：** JWT token认证
- **文件上传：** 任务完成证明上传
- **数据库：** SQLAlchemy ORM

---

## 🔐 OWASP Top 10 安全检查

### 1. A01:2021 – 失效的访问控制 (Broken Access Control)

#### 1.1 认证验证

**检查点：所有敏感端点都需要认证**

| 端点 | 需要认证 | 检查方法 | 状态 |
|------|---------|---------|------|
| GET /my-projects | ✅ | 检查 `Depends(deps.get_current_user)` | ⏳ |
| POST /tasks | ✅ | 检查依赖注入 | ⏳ |
| PUT /tasks/{id}/progress | ✅ | 检查依赖注入 | ⏳ |
| PUT /tasks/{id}/complete | ✅ | 检查依赖注入 | ⏳ |
| GET /tasks/pending-approval | ✅ | 检查依赖注入 | ⏳ |
| PUT /tasks/{id}/approve | ✅ | 检查依赖注入 | ⏳ |

**验证方法：**
```bash
# 测试未认证访问
curl -X GET "http://localhost:8000/api/v1/engineers/my-projects"
# 预期结果：401 Unauthorized
```

**代码审查：**
```python
# app/api/v1/endpoints/engineers.py
# 每个端点应包含：
async def endpoint_name(
    current_user: User = Depends(deps.get_current_user),  # ✅ 必需
    db: Session = Depends(deps.get_db)
):
```

- [ ] 所有16个端点都包含 `Depends(deps.get_current_user)`
- [ ] 无匿名可访问的敏感端点

---

#### 1.2 水平权限控制

**检查点：用户只能访问自己的资源**

**任务更新权限检查：**
```python
# engineers.py:265-269
if task.assignee_id != current_user.id:
    raise HTTPException(
        status_code=403,
        detail="您只能更新分配给自己的任务"
    )
```

**测试场景：**
| 操作 | 权限要求 | 代码位置 | 检查 |
|------|---------|---------|------|
| 更新任务进度 | task.assignee_id == user.id | engineers.py:265 | ⏳ |
| 完成任务 | task.assignee_id == user.id | engineers.py:368 | ⏳ |
| 报告延期 | task.assignee_id == user.id | engineers.py:532 | ⏳ |
| 删除证明 | proof.uploaded_by == user.id | engineers.py:891 | ⏳ |

**验证方法：**
```bash
# 1. 用户A创建任务
curl -X POST "/api/v1/engineers/tasks" -H "Authorization: Bearer <TOKEN_A>"

# 2. 用户B尝试更新用户A的任务
curl -X PUT "/api/v1/engineers/tasks/1/progress" -H "Authorization: Bearer <TOKEN_B>"

# 预期结果：403 Forbidden
```

- [ ] 任务操作都验证了 `assignee_id`
- [ ] 证明材料操作验证了 `uploaded_by`
- [ ] 无跨用户访问漏洞

---

#### 1.3 垂直权限控制

**检查点：PM审批权限验证**

**PM审批权限检查：**
```python
# engineers.py:592-609
approval_workflow = (
    db.query(TaskApprovalWorkflow)
    .filter(
        TaskApprovalWorkflow.task_id == task_id,
        TaskApprovalWorkflow.approver_id == current_user.id,  # ✅ 验证审批人
        TaskApprovalWorkflow.decision == ApprovalDecision.PENDING,
    )
    .first()
)

if not approval_workflow:
    raise HTTPException(
        status_code=403,
        detail="您没有权限审批此任务"
    )
```

**测试场景：**
| 操作 | 权限要求 | 代码位置 | 检查 |
|------|---------|---------|------|
| 批准任务 | approver_id == user.id | engineers.py:592-609 | ⏳ |
| 拒绝任务 | approver_id == user.id | engineers.py:697 | ⏳ |

**验证方法：**
```bash
# 普通工程师尝试审批
curl -X PUT "/api/v1/engineers/tasks/1/approve" \
  -H "Authorization: Bearer <ENGINEER_TOKEN>"

# 预期结果：403 Forbidden
```

- [ ] PM审批端点验证了 `approver_id`
- [ ] 普通工程师无法审批
- [ ] 无权限提升漏洞

---

### 2. A02:2021 – 加密机制失效 (Cryptographic Failures)

#### 2.1 JWT Token安全性

**检查点：**
```python
# app/core/security.py
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
```

- [ ] SECRET_KEY强度足够（至少32字节随机）
- [ ] 使用安全算法（HS256或RS256）
- [ ] Token包含过期时间（exp claim）
- [ ] Token过期时间合理（不超过24小时）
- [ ] SECRET_KEY存储在环境变量，不在代码中硬编码

**验证方法：**
```bash
# 检查配置
grep -r "SECRET_KEY" app/core/config.py
# 应从环境变量读取，有默认随机值

# 检查token过期
curl -X GET "/api/v1/engineers/my-projects" \
  -H "Authorization: Bearer <EXPIRED_TOKEN>"
# 预期结果：401 Unauthorized
```

---

#### 2.2 密码存储

**检查点：**
```python
# app/core/security.py
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
```

- [ ] 使用bcrypt算法（安全的单向哈希）
- [ ] 不存储明文密码
- [ ] 密码哈希不可逆

**代码审查：**
```python
# app/core/security.py:4-5
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
```

- [ ] bcrypt算法正确配置 ✅
- [ ] 无MD5/SHA1等弱算法

---

#### 2.3 敏感数据传输

**检查点：**
- [ ] 生产环境强制使用HTTPS
- [ ] Token只在Authorization头中传输，不在URL
- [ ] 响应中不包含敏感信息（密码哈希等）

**验证方法：**
```bash
# 检查响应中是否有password_hash
curl -X GET "/api/v1/engineers/my-projects" \
  -H "Authorization: Bearer <TOKEN>" | grep password

# 应该没有结果
```

---

### 3. A03:2021 – 注入 (Injection)

#### 3.1 SQL注入防护

**检查点：使用ORM参数化查询**

**所有数据库查询都应使用SQLAlchemy ORM：**
```python
# ✅ 正确示例（参数化查询）
task = db.query(TaskUnified).filter(TaskUnified.id == task_id).first()

# ❌ 错误示例（原始SQL拼接 - 不应存在）
db.execute(f"SELECT * FROM task_unified WHERE id = {task_id}")
```

**检查项：**
- [ ] 无原始SQL字符串拼接
- [ ] 所有查询使用ORM或参数化查询
- [ ] 用户输入全部通过Pydantic验证

**代码审查：**
```bash
# 搜索潜在的SQL注入点
grep -r "db.execute" app/api/v1/endpoints/engineers.py
grep -r "f\"SELECT" app/api/v1/endpoints/engineers.py

# 应该没有结果（所有查询都用ORM）
```

**测试方法：**
```bash
# 尝试SQL注入
curl -X POST "/api/v1/engineers/tasks" \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": 1,
    "title": "'; DROP TABLE task_unified; --",
    "task_importance": "GENERAL",
    "priority": "MEDIUM"
  }'

# 应安全处理，不执行SQL命令
```

- [ ] SQL注入测试通过
- [ ] 数据库表完整

---

#### 3.2 命令注入防护

**检查点：文件操作安全**

**文件路径构造：**
```python
# engineers.py:499-503
file_extension = os.path.splitext(file.filename)[1].lower()
unique_filename = f"{uuid.uuid4()}{file_extension}"
file_path = os.path.join(UPLOAD_DIR, unique_filename)
```

- [ ] 使用UUID生成文件名，不使用用户输入
- [ ] 使用 `os.path.join` 构造路径
- [ ] 无 `os.system()` 或 `subprocess` 调用（除非必要）

**验证方法：**
```bash
# 检查命令注入漏洞
grep -r "os.system" app/
grep -r "subprocess" app/
grep -r "eval" app/

# 应该没有结果或有明确的安全处理
```

---

### 4. A04:2021 – 不安全设计 (Insecure Design)

#### 4.1 业务逻辑安全

**重要任务审批流程：**
```python
# engineers.py:118-137
if task_data.task_importance == TaskImportance.IMPORTANT:
    if not task_data.justification:
        raise HTTPException(...)  # ✅ 强制要求理由

    task_db.status = TaskStatus.PENDING_APPROVAL  # ✅ 状态控制

    approval_workflow = TaskApprovalWorkflow(...)  # ✅ 创建审批流
```

**检查项：**
- [ ] 重要任务必须审批，不能绕过
- [ ] 一般任务无需审批（符合设计）
- [ ] 审批状态流转正确（PENDING → APPROVED/REJECTED）
- [ ] 无竞争条件（并发创建任务）

**状态转换验证：**
```
PENDING_APPROVAL → (approve) → ACCEPTED ✅
PENDING_APPROVAL → (reject) → REJECTED ✅

ACCEPTED → (update progress) → IN_PROGRESS ✅
IN_PROGRESS → (complete) → COMPLETED ✅

COMPLETED → (update progress) → ❌ 应拒绝
REJECTED → (update progress) → ❌ 应拒绝
```

- [ ] 状态机实现正确
- [ ] 无非法状态转换

---

#### 4.2 速率限制和防滥用

**当前状态：**
- ⚠️ 未实现API速率限制
- ⚠️ 未实现请求频率限制

**建议：**
```python
# 添加速率限制中间件（未来改进）
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/tasks")
@limiter.limit("10/minute")  # 每分钟最多10个请求
async def create_task(...):
    ...
```

- [ ] P2优先级：实现API速率限制
- [ ] P2优先级：防止批量任务创建滥用

---

### 5. A05:2021 – 安全配置错误 (Security Misconfiguration)

#### 5.1 调试模式

**检查点：**
```python
# app/core/config.py
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
```

- [ ] 生产环境 `DEBUG=false`
- [ ] 生产环境无详细错误堆栈暴露
- [ ] 生产环境无Swagger UI（或需要认证）

**验证方法：**
```bash
# 检查配置文件
cat .env | grep DEBUG
# 生产环境应为：DEBUG=false

# 检查错误响应
curl -X GET "http://localhost:8000/api/v1/engineers/tasks/99999" \
  -H "Authorization: Bearer <TOKEN>"

# 不应返回完整堆栈跟踪
```

---

#### 5.2 CORS配置

**检查点：**
```python
# app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,  # 应来自配置
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

- [ ] `allow_origins` 不是 `["*"]`（生产环境）
- [ ] 只允许可信域名
- [ ] `allow_credentials=True` 时必须指定具体域名

**验证方法：**
```bash
# 检查CORS配置
grep -A5 "CORSMiddleware" app/main.py

# 检查环境变量
echo $CORS_ORIGINS
# 应为具体域名列表，如 ["https://app.example.com"]
```

---

#### 5.3 依赖版本

**检查点：**
- [ ] `requirements.txt` 中所有依赖版本固定
- [ ] 无已知高危漏洞的包版本
- [ ] 定期更新依赖

**验证方法：**
```bash
# 检查已知漏洞
pip install safety
safety check -r requirements.txt

# 检查过期包
pip list --outdated
```

---

### 6. A06:2021 – 易受攻击和过时的组件 (Vulnerable and Outdated Components)

#### 6.1 依赖安全扫描

**当前依赖：**
```
fastapi
uvicorn
sqlalchemy
pydantic
python-jose[cryptography]
passlib[bcrypt]
python-multipart
```

**检查项：**
- [ ] 所有包都是最新稳定版本
- [ ] 无CVE高危漏洞
- [ ] 定期审计（每季度）

**扫描工具：**
```bash
# 安装扫描工具
pip install pip-audit safety

# 扫描漏洞
pip-audit
safety check

# 查看报告
```

---

### 7. A07:2021 – 身份识别和身份验证失败 (Identification and Authentication Failures)

#### 7.1 密码策略

**当前状态：**
- ⚠️ 未实现密码复杂度要求
- ⚠️ 未实现密码历史记录

**建议：**
```python
def validate_password_strength(password: str) -> bool:
    """验证密码强度"""
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):  # 大写字母
        return False
    if not re.search(r"[a-z]", password):  # 小写字母
        return False
    if not re.search(r"\d", password):     # 数字
        return False
    return True
```

- [ ] P2优先级：实现密码强度验证
- [ ] P2优先级：实现密码过期策略

---

#### 7.2 会话管理

**JWT Token策略：**
```python
# app/core/config.py
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24小时
```

**检查项：**
- [ ] Token过期时间合理（24小时）
- [ ] 无刷新token机制（可能需要添加）
- [ ] Token无法主动撤销（考虑添加黑名单）

**建议改进：**
- [ ] P2优先级：实现Refresh Token机制
- [ ] P2优先级：实现Token黑名单（用于注销）

---

#### 7.3 多因素认证

**当前状态：**
- ❌ 未实现MFA

**建议：**
- [ ] P3优先级：考虑为PM审批操作添加MFA

---

### 8. A08:2021 – 软件和数据完整性失效 (Software and Data Integrity Failures)

#### 8.1 文件完整性

**文件上传验证：**
```python
# engineers.py:496-510
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf", ".doc", ".docx"}

# 验证文件大小
if file.size > MAX_FILE_SIZE:
    raise HTTPException(...)

# 验证文件扩展名
file_extension = os.path.splitext(file.filename)[1].lower()
if file_extension not in ALLOWED_EXTENSIONS:
    raise HTTPException(...)
```

**检查项：**
- [ ] 文件大小限制（10MB） ✅
- [ ] 文件类型白名单 ✅
- [ ] 文件名安全处理（UUID重命名） ✅
- [ ] 文件内容验证（TODO：添加MIME类型验证）⚠️

**改进建议：**
```python
import magic  # python-magic

# 验证实际MIME类型，不只是扩展名
mime = magic.from_buffer(await file.read(1024), mime=True)
if mime not in ALLOWED_MIME_TYPES:
    raise HTTPException(...)
```

- [ ] P1优先级：添加MIME类型验证
- [ ] P2优先级：添加病毒扫描（ClamAV）

---

#### 8.2 数据完整性

**数据库约束：**
```sql
-- migrations/20260107_engineer_progress_sqlite.sql

-- 外键约束
FOREIGN KEY (project_id) REFERENCES projects(id),
FOREIGN KEY (assignee_id) REFERENCES users(id),

-- CHECK约束
CHECK (progress >= 0 AND progress <= 100),
CHECK (actual_hours >= 0),
CHECK (estimated_hours >= 0),

-- 唯一性约束
task_code VARCHAR(50) UNIQUE NOT NULL,
```

**检查项：**
- [ ] 外键约束完整 ✅
- [ ] CHECK约束保证数据有效性 ✅
- [ ] 唯一性约束防止重复 ✅

---

### 9. A09:2021 – 安全日志和监控失效 (Security Logging and Monitoring Failures)

#### 9.1 日志记录

**当前状态：**
- ⚠️ 未实现全面的审计日志
- ⚠️ 未记录认证失败
- ⚠️ 未记录权限拒绝

**建议：**
```python
import logging

logger = logging.getLogger(__name__)

# 记录认证失败
@router.post("/login")
async def login(...):
    if not verify_password(...):
        logger.warning(f"Failed login attempt for user: {username} from IP: {request.client.host}")
        raise HTTPException(...)

# 记录权限拒绝
if task.assignee_id != current_user.id:
    logger.warning(f"User {current_user.id} attempted to access task {task_id} without permission")
    raise HTTPException(...)

# 记录敏感操作
logger.info(f"User {current_user.id} approved task {task_id}")
```

**建议实现的日志：**
- [ ] P1优先级：登录/登出事件
- [ ] P1优先级：权限拒绝事件
- [ ] P1优先级：审批操作
- [ ] P2优先级：文件上传/删除
- [ ] P2优先级：异常错误

---

#### 9.2 监控和告警

**当前状态：**
- ❌ 未实现实时监控
- ❌ 未实现异常告警

**建议：**
- [ ] P2优先级：集成APM工具（Sentry, New Relic）
- [ ] P2优先级：设置告警规则（多次登录失败、异常错误率）
- [ ] P3优先级：实时安全事件监控

---

### 10. A10:2021 – 服务器端请求伪造 (Server-Side Request Forgery - SSRF)

#### 10.1 外部请求

**当前状态：**
- ✅ 系统不进行外部HTTP请求
- ✅ 无URL参数接受用户输入

**检查项：**
- [ ] 无基于用户输入的HTTP请求
- [ ] 无基于用户输入的文件读取
- [ ] 文件上传路径限制在 `uploads/` 目录内

**验证方法：**
```bash
# 搜索潜在的SSRF点
grep -r "requests.get" app/
grep -r "urllib.request" app/
grep -r "httpx" app/

# 应该没有结果（系统不做外部请求）
```

---

## 🔍 附加安全检查

### 11. 信息泄露

**检查点：**

**错误消息：**
- [ ] 错误消息不泄露系统内部信息
- [ ] 不暴露数据库结构
- [ ] 不暴露文件路径

**示例：**
```python
# ✅ 正确 - 通用错误消息
raise HTTPException(status_code=404, detail="任务不存在")

# ❌ 错误 - 泄露细节
raise HTTPException(
    status_code=500,
    detail=f"Database error: {str(e)} at /var/www/app/models/task.py:123"
)
```

**响应头：**
- [ ] 移除 `Server` 头或混淆版本信息
- [ ] 添加安全响应头：
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `X-XSS-Protection: 1; mode=block`
  - `Strict-Transport-Security: max-age=31536000`

**验证方法：**
```bash
# 检查响应头
curl -I "http://localhost:8000/health"

# 应包含安全头，不暴露敏感信息
```

---

### 12. 业务逻辑漏洞

**并发问题：**

**任务编码生成：**
```python
# engineers.py:95-99
max_code = db.query(func.max(TaskUnified.task_code)).scalar()
sequence = int(max_code.split("-")[-1]) + 1 if max_code else 1
```

- [ ] ⚠️ **潜在竞争条件**：两个并发请求可能生成相同编码
- [ ] P1优先级：使用数据库序列或乐观锁

**改进建议：**
```python
from sqlalchemy.exc import IntegrityError

# 方案1：使用数据库序列（MySQL）
CREATE SEQUENCE task_code_seq START WITH 1 INCREMENT BY 1;

# 方案2：重试机制
max_retries = 3
for attempt in range(max_retries):
    try:
        task_code = generate_task_code()
        db.add(task)
        db.commit()
        break
    except IntegrityError:
        db.rollback()
        if attempt == max_retries - 1:
            raise
```

**价格/金额操作：**
- [ ] N/A - 系统不涉及金额计算

---

### 13. 数据隐私

**个人数据保护：**

**数据最小化：**
- [ ] 只收集必要的用户数据
- [ ] 响应不包含敏感字段（password_hash等）

**数据访问控制：**
```python
# schemas/task_center.py - 响应模型
class TaskUnifiedResponse(BaseModel):
    id: int
    task_code: str
    title: str
    # ...
    # ✅ 不包含敏感字段

    class Config:
        from_attributes = True
```

**数据保留：**
- [ ] 使用软删除（`is_active=False`）而非硬删除 ✅
- [ ] 考虑数据归档策略（未来）

---

## 📊 安全评分

### 评分标准

| 类别 | 权重 | 最低分 | 实际得分 | 状态 |
|------|------|--------|---------|------|
| 访问控制 | 25% | 8.0/10 | ___/10 | ⏳ |
| 认证机制 | 20% | 8.5/10 | ___/10 | ⏳ |
| 注入防护 | 20% | 9.0/10 | ___/10 | ⏳ |
| 数据保护 | 15% | 8.0/10 | ___/10 | ⏳ |
| 文件安全 | 10% | 7.5/10 | ___/10 | ⏳ |
| 日志监控 | 10% | 6.0/10 | ___/10 | ⏳ |

**综合安全评分：** _______ / 10

---

## 🐛 发现的安全问题

### 高危（P0）

| 问题ID | 描述 | 位置 | 修复建议 | 截止日期 |
|-------|------|------|---------|---------|
| ___ | ___ | ___ | ___ | ___ |

### 中危（P1）

| 问题ID | 描述 | 位置 | 修复建议 | 截止日期 |
|-------|------|------|---------|---------|
| P1-SEC-001 | 任务编码生成有竞争条件 | engineers.py:95 | 使用数据库序列 | ___ |
| P1-SEC-002 | 文件上传缺少MIME类型验证 | engineers.py:496 | 添加python-magic验证 | ___ |
| P1-SEC-003 | 缺少审计日志 | 全局 | 实现logging | ___ |

### 低危（P2）

| 问题ID | 描述 | 位置 | 修复建议 | 截止日期 |
|-------|------|------|---------|---------|
| P2-SEC-001 | 无API速率限制 | 全局 | 添加slowapi | ___ |
| P2-SEC-002 | 无密码强度验证 | auth模块 | 实现密码策略 | ___ |
| P2-SEC-003 | 无Refresh Token机制 | security.py | 实现双token | ___ |

---

## ✅ 安全决策

**审查结论：**
- [ ] ✅ 通过 - 安全性良好，可以部署
- [ ] ⚠️ 通过 - 有轻微问题但可接受，建议修复P1问题后部署
- [ ] ❌ 不通过 - 存在高危漏洞，必须修复后重新审查

**修复计划：**
1. **立即修复（P0）：** _______________
2. **本周修复（P1）：** _______________
3. **下周修复（P2）：** _______________

---

## 📚 参考资源

- [OWASP Top 10 2021](https://owasp.org/Top10/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [SQLAlchemy Security](https://docs.sqlalchemy.org/en/14/faq/security.html)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)

---

## 🔧 安全工具推荐

### 静态分析
```bash
# 安装Bandit（Python安全扫描）
pip install bandit

# 扫描代码
bandit -r app/

# 依赖漏洞扫描
pip install safety
safety check
```

### 动态测试
```bash
# 安装OWASP ZAP或Burp Suite进行渗透测试
```

### 持续监控
```bash
# 集成Sentry错误监控
pip install sentry-sdk
```

---

**审查负责人签名：** _______________
**日期：** _______________

---

**文档版本：** 1.0
**创建日期：** 2026-01-07
**最后更新：** 2026-01-07
