#!/usr/bin/env python3
"""
使用 Python 内置追踪来找出循环依赖
"""
import sys

# 记录导入的模块
imported_modules = []
current_module = None

def trace_imports(frame, event, arg):
    """追踪导入事件"""
    if event == 'call':
        code = frame.f_code
        filename = code.co_filename
        func_name = code.co_name
        
        # 只追踪 app 模块的导入
        if '/app/' in filename and filename.endswith('.py'):
            # 提取模块路径
            if '/non-standard-automation-pms/app/' in filename:
                module_path = filename.split('/non-standard-automation-pms/app/')[-1]
                module_path = module_path.replace('/', '.').replace('.py', '')
                
                if module_path not in imported_modules:
                    imported_modules.append(module_path)
                    indent = "  " * (len(imported_modules) - 1)
                    print(f"{indent}→ {module_path} ({func_name})")
                    
                    # 检测深度
                    if len(imported_modules) > 50:
                        print(f"\n⚠️  导入深度超过50，可能有循环依赖!")
                        print(f"最近20个导入:")
                        for i, mod in enumerate(imported_modules[-20:], 1):
                            print(f"  {i}. {mod}")
                        sys.exit(1)
    
    return trace_imports

print("=" * 60)
print("开始追踪导入...")
print("=" * 60)

# 设置追踪
sys.settrace(trace_imports)

try:
    import app.main
    print("\n✅ 导入成功!")
except RecursionError as e:
    print(f"\n❌ RecursionError at depth {len(imported_modules)}")
    print(f"最近导入的20个模块:")
    for i, mod in enumerate(imported_modules[-20:], 1):
        print(f"  {i}. {mod}")
except Exception as e:
    print(f"\n❌ {type(e).__name__}: {str(e)[:100]}")
finally:
    sys.settrace(None)
