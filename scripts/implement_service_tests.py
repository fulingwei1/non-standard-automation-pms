#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
辅助脚本：为服务文件实现基础测试用例
提供测试用例模板和实现建议
"""

import ast
import json
from pathlib import Path
from typing import List, Dict, Set


def analyze_service_methods(service_file: Path) -> Dict:
    """分析服务文件的方法"""
    try:
        with open(service_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        methods = []
        classes = []
        
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                class_methods = []
                for item in node.body:
                    if isinstance(node, ast.FunctionDef):
                        class_methods.append({
                            'name': item.name,
                            'args': [arg.arg for arg in item.args.args],
                            'is_private': item.name.startswith('_')
                        })
                classes.append({
                    'name': node.name,
                    'methods': class_methods
                })
            elif isinstance(node, ast.FunctionDef):
                methods.append({
                    'name': node.name,
                    'args': [arg.arg for arg in node.args.args]
                })
        
        return {
            'classes': classes,
            'functions': methods
        }
    except Exception as e:
        return {'error': str(e)}


def generate_test_implementation_guide(service_name: str, service_file: Path) -> str:
    """生成测试实现指南"""
    analysis = analyze_service_methods(service_file)
    
    guide = f"""# {service_name} 测试实现指南

## 服务文件分析

"""
    
    if 'error' in analysis:
        guide += f"⚠️ 分析失败: {analysis['error']}\n"
        return guide
    
    if analysis.get('classes'):
        guide += "### 服务类\n\n"
        for cls in analysis['classes']:
            guide += f"**类名**: `{cls['name']}`\n\n"
            guide += "**公共方法**:\n"
            for method in cls['methods']:
                if not method['is_private']:
                    guide += f"- `{method['name']}({', '.join(method['args'])})`\n"
            guide += "\n"
    
    if analysis.get('functions'):
        guide += "### 独立函数\n\n"
        for func in analysis['functions']:
            guide += f"- `{func['name']}({', '.join(func['args'])})`\n"
        guide += "\n"
    
    guide += """
## 测试用例建议

### 1. 初始化测试
```python
def test_init(self, db_session):
    service = ServiceClass(db_session)
    assert service is not None
    assert service.db == db_session
```

### 2. 正常流程测试
```python
def test_method_success(self, service):
    # Arrange
    test_data = create_test_data()
    
    # Act
    result = service.method(test_data)
    
    # Assert
    assert result is not None
    assert result.status == "success"
```

### 3. 边界条件测试
```python
def test_method_empty_input(self, service):
    result = service.method([])
    assert result == []
```

### 4. 异常处理测试
```python
def test_method_invalid_input(self, service):
    with pytest.raises(ValueError):
        service.method(None)
```

### 5. Mock 依赖测试
```python
def test_method_with_mock(self, service):
    with patch('app.services.service.ExternalAPI') as mock:
        mock.return_value = "mocked"
        result = service.method({})
        assert result == "mocked"
```

## 实现步骤

1. 阅读服务代码，理解业务逻辑
2. 识别依赖项（数据库、外部服务等）
3. 准备测试数据（使用 fixtures）
4. 实现正常流程测试
5. 实现边界条件测试
6. 实现异常处理测试
7. 运行测试验证覆盖率

## 覆盖率目标

- 至少 60% 覆盖率
- 核心业务逻辑 100% 覆盖
- 异常处理路径必须测试

"""
    
    return guide


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="生成服务测试实现指南")
    parser.add_argument('service_name', help='服务名称（不含.py）')
    parser.add_argument('--output', help='输出文件路径', default=None)
    
    args = parser.parse_args()
    
    service_file = Path(f"app/services/{args.service_name}.py")
    if not service_file.exists():
        print(f"❌ 服务文件不存在: {service_file}")
        return
    
    guide = generate_test_implementation_guide(args.service_name, service_file)
    
    if args.output:
        output_file = Path(args.output)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(guide)
        print(f"✅ 指南已保存到: {output_file}")
    else:
        print(guide)


if __name__ == "__main__":
    main()
