# 代码拆分脚本

本目录包含用于拆分大文件和模块的脚本。

## 脚本说明

这些脚本用于将大型Python文件拆分成更小的模块，提高代码可维护性。

### 主要脚本

- `split_*.py` - 各种模块的拆分脚本
- `universal_split.py` - 通用拆分脚本

## 使用方法

```bash
# 运行特定模块的拆分脚本
python3 scripts/splitting/split_apis.py

# 使用通用拆分脚本
python3 scripts/splitting/universal_split.py <target_file>
```

## 注意事项

- 运行拆分脚本前请备份代码
- 拆分后需要运行测试确保功能正常
- 拆分后需要更新相关的导入语句
