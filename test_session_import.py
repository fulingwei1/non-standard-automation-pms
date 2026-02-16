#!/usr/bin/env python3
"""测试session相关导入"""

import sys
import traceback

# 测试导入UserSession模型
try:
    from app.models.session import UserSession
    print("✓ UserSession模型导入成功")
    print(f"  表名: {UserSession.__tablename__}")
except Exception as e:
    print(f"✗ UserSession模型导入失败: {e}")
    traceback.print_exc()

# 测试导入SessionService
try:
    from app.services.session_service import SessionService
    print("✓ SessionService导入成功")
except Exception as e:
    print(f"✗ SessionService导入失败: {e}")
    traceback.print_exc()

# 测试创建数据库会话
try:
    from app.dependencies import get_db
    print("✓ get_db导入成功")
except Exception as e:
    print(f"✗ get_db导入失败: {e}")
    traceback.print_exc()

# 测试查询UserSession
try:
    from app.dependencies import get_db
    from app.models.session import UserSession
    from sqlalchemy.orm import Session
    
    db_gen = get_db()
    db: Session = next(db_gen)
    
    print("✓ 数据库会话创建成功")
    
    # 尝试查询
    result = db.query(UserSession).first()
    print(f"✓ UserSession查询成功, 结果: {result}")
    
    db.close()
except Exception as e:
    print(f"✗ UserSession查询失败: {e}")
    traceback.print_exc()
