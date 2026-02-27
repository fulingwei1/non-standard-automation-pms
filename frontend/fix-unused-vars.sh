#!/bin/bash
# 修复未使用的变量和catch错误

# 修复所有未使用的 catch 错误 (e -> _e)
find src/pages -name "*.jsx" -type f -exec sed -i '' 's/} catch (e) {/} catch (_e) {/g' {} \;

# 修复特定文件中的未使用变量
sed -i '' 's/const \[warehouse_id, location_code\]/const [_warehouse_id, _location_code]/' src/pages/warehouse/LocationManagement.jsx

# 移除空的 catch 块（添加注释）
find src/pages -name "*.jsx" -type f -exec sed -i '' 's/catch (_e) {}/catch (_e) { \/* ignore *\/ }/g' {} \;

echo "Fixed!"
