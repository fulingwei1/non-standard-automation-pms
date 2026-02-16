#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 slowapi 在生产环境配置下的行为

模拟实际项目的配置：
- 多个中间件
- 异常处理器
- response_model
- JWT认证
"""
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.testclient import TestClient
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel
from typing import Optional

# 创建测试应用（模拟生产配置）
app = FastAPI(
    title="Test App",
    version="1.0.0",
    openapi_url="/api/v1/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# 创建速率限制器
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS中间件（模拟生产）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 定义响应模型（模拟实际项目）
class ResponseModel(BaseModel):
    code: int
    message: str
    data: Optional[dict] = {}


class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


class RefreshTokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


# 模拟依赖项
def get_current_user():
    return {"id": 1, "username": "test"}


# 测试场景1: 完全模拟login endpoint
@app.post("/api/v1/auth/login", response_model=dict, status_code=status.HTTP_200_OK)
@limiter.limit("5/minute")
def login_exact_copy(request: Request):
    """完全复制实际的login endpoint"""
    return {
        "access_token": "test_token_123",
        "refresh_token": "refresh_token_456",
        "token_type": "bearer",
        "expires_in": 1800,
        "refresh_expires_in": 604800,
    }


# 测试场景2: 使用Pydantic模型
@app.post("/api/v1/auth/refresh", response_model=RefreshTokenResponse, status_code=status.HTTP_200_OK)
@limiter.limit("10/minute")
def refresh_token(request: Request):
    """使用Pydantic模型的endpoint"""
    return RefreshTokenResponse(
        access_token="new_token",
        token_type="bearer",
        expires_in=1800,
    )


# 测试场景3: ResponseModel包装
@app.post("/api/v1/auth/logout", response_model=ResponseModel, status_code=status.HTTP_200_OK)
@limiter.limit("20/minute")
def logout(request: Request):
    """使用ResponseModel包装的endpoint"""
    return ResponseModel(code=200, message="登出成功")


# 测试场景4: 带依赖项注入
@app.put("/api/v1/auth/password", response_model=ResponseModel, status_code=status.HTTP_200_OK)
@limiter.limit("5/hour")
def change_password(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """带依赖项注入的endpoint"""
    return ResponseModel(code=200, message="密码修改成功")


# 测试场景5: 多层装饰器
@app.get("/api/v1/test/complex")
@limiter.limit("10/minute")
def complex_endpoint(request: Request, user: dict = Depends(get_current_user)):
    """多层装饰器测试"""
    return {"status": "ok", "user": user}


def run_comprehensive_tests():
    """运行综合测试"""
    client = TestClient(app)
    
    print("=" * 100)
    print("slowapi 生产环境兼容性综合测试")
    print("=" * 100)
    
    tests = [
        {
            "name": "场景1: 完全模拟login (dict response_model)",
            "method": "POST",
            "url": "/api/v1/auth/login",
            "expected_fields": ["access_token", "refresh_token", "token_type"],
        },
        {
            "name": "场景2: Pydantic模型 (RefreshTokenResponse)",
            "method": "POST",
            "url": "/api/v1/auth/refresh",
            "expected_fields": ["access_token", "token_type", "expires_in"],
        },
        {
            "name": "场景3: ResponseModel包装",
            "method": "POST",
            "url": "/api/v1/auth/logout",
            "expected_fields": ["code", "message"],
        },
        {
            "name": "场景4: 带依赖项注入",
            "method": "PUT",
            "url": "/api/v1/auth/password",
            "expected_fields": ["code", "message"],
        },
        {
            "name": "场景5: 多层装饰器",
            "method": "GET",
            "url": "/api/v1/test/complex",
            "expected_fields": ["status", "user"],
        },
    ]
    
    for test in tests:
        print(f"\n{'=' * 100}")
        print(f"{test['name']}")
        print(f"{'=' * 100}")
        
        try:
            if test["method"] == "GET":
                response = client.get(test["url"])
            elif test["method"] == "POST":
                response = client.post(test["url"])
            elif test["method"] == "PUT":
                response = client.put(test["url"])
            
            print(f"✓ 状态码: {response.status_code}")
            
            # 检查响应
            json_data = response.json()
            print(f"✓ 响应JSON: {json_data}")
            
            # 验证字段
            for field in test["expected_fields"]:
                if field in json_data:
                    print(f"  ✓ 字段 '{field}' 存在")
                else:
                    print(f"  ✗ 字段 '{field}' 缺失")
            
            # 检查rate limit headers
            rate_headers = {k: v for k, v in response.headers.items() if "rate" in k.lower()}
            if rate_headers:
                print(f"✓ Rate Limit Headers: {rate_headers}")
            else:
                print("⚠ 未找到Rate Limit Headers")
                
        except Exception as e:
            print(f"✗ 错误: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
    
    # 测试速率限制
    print(f"\n{'=' * 100}")
    print("测试速率限制触发")
    print(f"{'=' * 100}")
    
    try:
        # 连续请求直到触发限制
        for i in range(10):
            response = client.post("/api/v1/auth/login")
            print(f"请求 #{i+1}: 状态码 {response.status_code}")
            if response.status_code == 429:
                print(f"✓ 速率限制在第 {i+1} 次请求时触发")
                print(f"✓ 响应: {response.json()}")
                break
    except Exception as e:
        print(f"✗ 速率限制测试错误: {e}")
    
    print(f"\n{'=' * 100}")
    print("测试完成")
    print(f"{'=' * 100}")


if __name__ == "__main__":
    run_comprehensive_tests()
