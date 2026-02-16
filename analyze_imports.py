#!/usr/bin/env python3
"""
分析模块导入关系，找出循环依赖
"""
import sys
import os

# 追踪导入路径
import_stack = []

class ImportTracer:
    def __init__(self):
        self.imports = []
        self.depth = 0
        
    def find_module(self, fullname, path=None):
        if fullname.startswith('app.'):
            return self
        return None
        
    def load_module(self, fullname):
        self.depth += 1
        indent = "  " * self.depth
        print(f"{indent}→ {fullname}")
        
        # 检测循环
        if fullname in import_stack:
            print(f"{indent}⚠️  循环检测到: {fullname}")
            print(f"{indent}路径: {' → '.join(import_stack + [fullname])}")
            self.depth -= 1
            raise ImportError(f"Circular import detected: {fullname}")
        
        import_stack.append(fullname)
        
        try:
            # 尝试导入
            if fullname in sys.modules:
                module = sys.modules[fullname]
            else:
                import importlib
                module = importlib.import_module(fullname)
            return module
        except RecursionError:
            print(f"{indent}⚠️  RecursionError at: {fullname}")
            print(f"{indent}导入栈 ({len(import_stack)} 深度):")
            for i, mod in enumerate(import_stack[-10:], 1):
                print(f"{indent}  {i}. {mod}")
            raise
        finally:
            if import_stack and import_stack[-1] == fullname:
                import_stack.pop()
            self.depth -= 1

# 安装追踪器
tracer = ImportTracer()
sys.meta_path.insert(0, tracer)

print("=" * 60)
print("开始追踪 app.main 导入...")
print("=" * 60)

try:
    import app.main
    print("\n✅ 导入成功!")
except RecursionError as e:
    print("\n❌ RecursionError: 循环导入检测到")
    print(f"导入栈深度: {len(import_stack)}")
    print("\n最近的导入路径:")
    for i, mod in enumerate(import_stack[-15:], 1):
        print(f"  {i}. {mod}")
except Exception as e:
    print(f"\n❌ {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
