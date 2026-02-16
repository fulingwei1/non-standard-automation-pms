#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从FastAPI应用中直接提取所有routes
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import json


def extract_routes():
    """从FastAPI应用提取所有routes"""
    try:
        from app.main import app
        
        routes_info = []
        
        for route in app.routes:
            # 跳过非HTTP路由（如WebSocket等）
            if not hasattr(route, 'methods'):
                continue
            
            # 提取路由信息
            path = route.path
            methods = list(route.methods or [])
            name = getattr(route, 'name', '')
            tags = getattr(route, 'tags', [])
            
            # 获取路径参数
            path_params = []
            if hasattr(route, 'param_convertors'):
                path_params = list(route.param_convertors.keys())
            
            for method in methods:
                if method in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                    routes_info.append({
                        'path': path,
                        'method': method,
                        'name': name,
                        'tags': tags if tags else [],
                        'path_params': path_params,
                    })
        
        return routes_info
    
    except Exception as e:
        print(f"❌ 提取routes失败: {e}")
        import traceback
        traceback.print_exc()
        return []


def main():
    """主函数"""
    print("🔍 从FastAPI应用提取routes...")
    
    routes = extract_routes()
    
    if not routes:
        print("❌ 没有找到任何路由")
        return
    
    print(f"✅ 找到 {len(routes)} 个路由")
    
    # 保存到JSON文件
    output_file = project_root / "data" / "extracted_routes.json"
    output_file.parent.mkdir(exist_ok=True)
    
    output_file.write_text(
        json.dumps(routes, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    
    print(f"📄 路由列表已保存到: {output_file}")
    
    # 统计信息
    methods_count = {}
    for route in routes:
        method = route['method']
        methods_count[method] = methods_count.get(method, 0) + 1
    
    print("\n统计:")
    for method, count in sorted(methods_count.items()):
        print(f"  {method}: {count}")
    
    # 显示一些示例
    print("\n示例路由:")
    for route in routes[:10]:
        print(f"  {route['method']} {route['path']}")


if __name__ == "__main__":
    main()
