# Admin 用户密码说明

## 为什么会有两个密码？

### 历史原因

1. **默认密码 `password123`**
   - 这是数据库初始化脚本 (`init_db.py`) 中设置的默认密码
   - 当首次运行 `python3 init_db.py` 时，会创建 admin 用户，密码为 `password123`

2. **重置密码 `admin`**
   - 为了方便用户记忆，使用 `create_admin.py` 脚本将密码重置为 `admin`
   - 这个脚本会更新现有用户的密码

### 当前状态

**当前有效的密码**: `admin`

- 使用 `create_admin.py` 脚本后，密码已更新为 `admin`
- 旧的密码 `password123` 不再有效（除非重新初始化数据库）

## 推荐做法

### 方案1: 统一使用 `admin`（推荐）

**优点**:
- 简单易记
- 与用户名相同，方便记忆
- 已通过 `create_admin.py` 设置

**使用**:
```bash
# 如果密码不是 admin，可以重置
python3 create_admin.py admin admin
```

### 方案2: 使用默认密码 `password123`

**优点**:
- 符合安全最佳实践（密码与用户名不同）
- 是系统默认设置

**使用**:
```bash
# 重置为默认密码
python3 create_admin.py admin password123
```

## 如何重置密码

使用 `create_admin.py` 脚本：

```bash
# 重置为 admin
python3 create_admin.py admin admin

# 或重置为 password123
python3 create_admin.py admin password123

# 或自定义密码
python3 create_admin.py admin your_custom_password
```

## 安全建议

⚠️ **生产环境注意事项**:

1. **不要使用默认密码**
   - 生产环境必须使用强密码
   - 建议使用随机生成的强密码

2. **定期更换密码**
   - 定期更新管理员密码
   - 使用密码管理工具

3. **限制管理员账号**
   - 只给必要的人员管理员权限
   - 使用最小权限原则

## 常见问题

### Q: 为什么我输入 `password123` 登录失败？

A: 如果之前运行过 `create_admin.py admin admin`，密码已经被更新为 `admin`。旧的 `password123` 不再有效。

### Q: 如何知道当前密码是什么？

A: 运行以下命令测试：
```bash
python3 create_admin.py admin admin  # 设置为 admin
# 或
python3 create_admin.py admin password123  # 设置为 password123
```

### Q: 可以同时使用两个密码吗？

A: 不可以。密码是唯一的，更新后会覆盖旧的密码。

## 总结

- **当前有效密码**: `admin`（如果运行过 `create_admin.py admin admin`）
- **默认密码**: `password123`（仅在首次初始化数据库时）
- **推荐**: 统一使用 `admin`，简单易记
- **生产环境**: 必须使用强密码
