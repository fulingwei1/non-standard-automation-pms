#!/usr/bin/env python3
"""
系统全面扫描工具
扫描代码库中的所有潜在问题
"""

import os
import re
from pathlib import Path
from collections import defaultdict

class SystemScanner:
    def __init__(self, root_dir):
        self.root_dir = Path(root_dir)
        self.issues = defaultdict(list)
        self.stats = {}
        
    def scan_all(self):
        """执行所有扫描"""
        print("=" * 70)
        print("🔍 系统全面扫描开始...")
        print("=" * 70)
        
        self.scan_imports()
        self.scan_fixmes()
        self.scan_disabled_code()
        self.scan_models()
        self.scan_circular_deps()
        self.scan_code_smells()
        self.generate_report()
        
    def scan_imports(self):
        """扫描导入问题"""
        print("\n📦 扫描导入问题...")
        
        py_files = list(self.root_dir.glob("app/**/*.py"))
        self.stats['total_files'] = len(py_files)
        
        for file_path in py_files:
            try:
                content = file_path.read_text(encoding='utf-8')
                
                # 检查循环导入风险
                if 'from app.models' in content and 'from app.schemas' in content:
                    self.issues['import_mixing'].append(str(file_path))
                
                # 检查注释掉的导入
                commented_imports = re.findall(r'#\s*from .* import', content)
                if commented_imports:
                    self.issues['commented_imports'].append(f"{file_path}: {len(commented_imports)}个")
                    
            except Exception as e:
                self.issues['scan_errors'].append(f"{file_path}: {e}")
                
        print(f"✓ 扫描了 {len(py_files)} 个Python文件")
        
    def scan_fixmes(self):
        """扫描FIXME和TODO"""
        print("\n🔧 扫描临时修复...")
        
        fixme_patterns = [
            r'#\s*FIXME',
            r'#\s*TODO',
            r'#\s*HACK',
            r'#\s*XXX',
            r'#\s*临时',
            r'#\s*Temporarily disabled',
        ]
        
        py_files = list(self.root_dir.glob("app/**/*.py"))
        fixme_count = 0
        
        for file_path in py_files:
            try:
                content = file_path.read_text(encoding='utf-8')
                for pattern in fixme_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    if matches:
                        fixme_count += len(matches)
                        self.issues['fixmes'].append(f"{file_path.relative_to(self.root_dir)}: {len(matches)}个")
            except:
                pass
                
        self.stats['fixme_count'] = fixme_count
        print(f"✓ 发现 {fixme_count} 处临时修复标记")
        
    def scan_disabled_code(self):
        """扫描被禁用的代码"""
        print("\n🚫 扫描被禁用的代码...")
        
        disabled_patterns = [
            r'#\s*(from .* import|import .*)',  # 注释掉的导入
            r'#\s*(def |class |async def )',      # 注释掉的函数/类
            r'#\s*router\.include_router',       # 注释掉的路由
        ]
        
        py_files = list(self.root_dir.glob("app/**/*.py"))
        disabled_count = 0
        
        for file_path in py_files:
            try:
                content = file_path.read_text(encoding='utf-8')
                for pattern in disabled_patterns:
                    matches = re.findall(pattern, content)
                    if matches:
                        disabled_count += len(matches)
                        if len(matches) > 3:  # 只报告超过3处的文件
                            self.issues['disabled_code'].append(
                                f"{file_path.relative_to(self.root_dir)}: {len(matches)}处"
                            )
            except:
                pass
                
        self.stats['disabled_count'] = disabled_count
        print(f"✓ 发现 {disabled_count} 处被注释的代码")
        
    def scan_models(self):
        """扫描模型定义问题"""
        print("\n🗄️  扫描数据模型...")
        
        model_files = list(self.root_dir.glob("app/models/**/*.py"))
        self.stats['model_count'] = len(model_files)
        
        for file_path in model_files:
            try:
                content = file_path.read_text(encoding='utf-8')
                
                # 检查 relationship 定义
                relationships = re.findall(r'relationship\s*\(\s*["\'](\w+)["\']', content)
                if relationships:
                    # 检查是否有字符串形式的引用（可能导致延迟加载问题）
                    for rel in relationships:
                        if rel[0].isupper():  # 类名
                            # 检查该类是否在文件中导入
                            if f'from .* import.*{rel}' not in content and f'class {rel}' not in content:
                                self.issues['lazy_relationships'].append(
                                    f"{file_path.relative_to(self.root_dir)}: relationship('{rel}')"
                                )
            except:
                pass
                
        print(f"✓ 扫描了 {len(model_files)} 个模型文件")
        
    def scan_circular_deps(self):
        """扫描可能的循环依赖"""
        print("\n🔄 扫描循环依赖风险...")
        
        import_graph = defaultdict(set)
        py_files = list(self.root_dir.glob("app/**/*.py"))
        
        for file_path in py_files:
            try:
                content = file_path.read_text(encoding='utf-8')
                module_name = str(file_path.relative_to(self.root_dir)).replace('/', '.').replace('.py', '')
                
                # 提取所有 app 内部导入
                imports = re.findall(r'from (app\.[^\s]+) import', content)
                imports += re.findall(r'import (app\.[^\s]+)', content)
                
                for imp in imports:
                    import_graph[module_name].add(imp)
            except:
                pass
        
        # 简单的循环检测（A→B且B→A）
        circular = []
        checked = set()
        
        for mod_a, deps in import_graph.items():
            for mod_b in deps:
                if (mod_a, mod_b) not in checked and (mod_b, mod_a) not in checked:
                    checked.add((mod_a, mod_b))
                    if mod_a in import_graph.get(mod_b, set()):
                        circular.append(f"{mod_a} ↔ {mod_b}")
        
        self.issues['circular_deps'] = circular
        self.stats['circular_count'] = len(circular)
        print(f"✓ 发现 {len(circular)} 对可能的循环依赖")
        
    def scan_code_smells(self):
        """扫描代码异味"""
        print("\n👃 扫描代码质量问题...")
        
        py_files = list(self.root_dir.glob("app/**/*.py"))
        
        long_files = []
        long_functions = []
        
        for file_path in py_files:
            try:
                content = file_path.read_text(encoding='utf-8')
                lines = content.split('\n')
                
                # 检查超长文件（>500行）
                if len(lines) > 500:
                    long_files.append(f"{file_path.relative_to(self.root_dir)}: {len(lines)}行")
                
                # 检查超长函数（>100行）
                in_function = False
                func_start = 0
                func_name = ""
                
                for i, line in enumerate(lines):
                    if re.match(r'\s*(def|async def) \w+', line):
                        if in_function and (i - func_start) > 100:
                            long_functions.append(
                                f"{file_path.relative_to(self.root_dir)}:{func_start} {func_name} ({i-func_start}行)"
                            )
                        in_function = True
                        func_start = i
                        func_name = line.strip()
                    elif in_function and not line.strip().startswith((' ', '\t', '#')):
                        if line.strip() and (i - func_start) > 100:
                            long_functions.append(
                                f"{file_path.relative_to(self.root_dir)}:{func_start} {func_name} ({i-func_start}行)"
                            )
                        in_function = False
                        
            except:
                pass
        
        self.issues['long_files'] = long_files
        self.issues['long_functions'] = long_functions[:20]  # 只列出前20个
        self.stats['long_files_count'] = len(long_files)
        self.stats['long_functions_count'] = len(long_functions)
        
        print(f"✓ 发现 {len(long_files)} 个超长文件")
        print(f"✓ 发现 {len(long_functions)} 个超长函数")
        
    def generate_report(self):
        """生成扫描报告"""
        print("\n" + "=" * 70)
        print("📊 扫描报告")
        print("=" * 70)
        
        print(f"\n📈 统计数据:")
        print(f"  - 总文件数: {self.stats.get('total_files', 0)}")
        print(f"  - 模型文件: {self.stats.get('model_count', 0)}")
        print(f"  - FIXME标记: {self.stats.get('fixme_count', 0)}")
        print(f"  - 注释代码: {self.stats.get('disabled_count', 0)}")
        print(f"  - 循环依赖: {self.stats.get('circular_count', 0)}")
        print(f"  - 超长文件: {self.stats.get('long_files_count', 0)}")
        print(f"  - 超长函数: {self.stats.get('long_functions_count', 0)}")
        
        print(f"\n🚨 问题分类:")
        for category, items in sorted(self.issues.items()):
            if items:
                print(f"\n  {category.upper()} ({len(items)}个):")
                for item in items[:10]:  # 只显示前10个
                    print(f"    - {item}")
                if len(items) > 10:
                    print(f"    ... 还有 {len(items)-10} 个")

if __name__ == "__main__":
    scanner = SystemScanner("/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms")
    scanner.scan_all()
    
    print("\n" + "=" * 70)
    print("✅ 扫描完成")
    print("=" * 70)
