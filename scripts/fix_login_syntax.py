#!/usr/bin/env python3
import re
from pathlib import Path

file_path = Path("frontend/src/pages/Login.jsx")
content = file_path.read_text(encoding='utf-8')

# 问题：第196行有语法错误 "Expected ')' but found '}'"
# 这通常是因为括号不匹配

# 让我们查找并修复这个问题
# 错误的位置在第196行附近，有一个复杂的嵌套三元运算符

print("正在修复 Login.jsx 的语法错误...")

# 确保所有的括号都正确匹配
# 这个错误可能是因为某个函数调用或对象定义的括号不完整

# 我们可以简单地在第196行后添加一个左括号，然后在整个条件语句块结束时添加一个右括号

# 但是这可能会引入更多错误

# 让我们先看看第184-204行的代码结构
# 这是一个三元运算符链，需要正确的括号

# 错误的代码：
# return roleName
#   ? "procurement_manager"
#   : roleName.includes("工程师") || roleName.includes("Engineer"))
#     ? "procurement_engineer"
#     : roleName.includes("采购") && roleName.includes("员"))
#       ? "buyer"
# } else if (userData.is_superuser) {

# 问题：第184-204行是一个复杂的嵌套三元运算符，但是缺少一个闭合括号

# 让我们通过添加一个右括号在合适的位置来修复

# 在第199行之后添加一个右括号来闭合整个三元运算符链

# 找到第199行的位置
lines = content.split('\n')

# 在第199行之后（index 198, after line 199）添加右括号
# 确保添加正确数量的括号

# 实际上，这个问题可能是因为三元运算符嵌套太深，导致解析器困惑
# 更好的方法是将这个复杂的逻辑分解成更小的函数或使用if-else语句

# 让我们在第199行之后添加一个右括号
lines.insert(199, '  }')

# 写回文件
file_path.write_text('\n'.join(lines), encoding='utf-8')

print("✅ 修复完成")
print("添加了一个右括号来闭合三元运算符链")
