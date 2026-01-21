# 数据库脚本

本目录包含数据库相关的脚本文件。

## 文件说明

- **supabase-setup.sql** - Supabase 数据库初始化脚本

## 使用方法

### Supabase 初始化

```bash
# 在 Supabase 控制台执行此脚本，或使用 Supabase CLI
supabase db reset
# 或直接在 Supabase SQL Editor 中执行
```

## 注意事项

- 执行前请备份现有数据
- 确保数据库连接配置正确
- 生产环境执行前请仔细检查脚本内容
