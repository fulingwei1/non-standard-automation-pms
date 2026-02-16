#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 slowapi 与 FastAPI response_model 冲突

这个脚本重现问题，帮助分析冲突原因
"""
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel

# 创建测试应用
app = FastAPI()

# 创建速率限制器
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# 定义响应模型
class ResponseModel(BaseModel):
    code: int
    message: str
    data: dict = {}


# 测试1: 使用dict作为response_model
@app.post("/test1/dict")
@limiter.limit("5/minute")
def test_dict(request: Request):
    return {"access_token": "test_token", "token_type": "bearer"}


# 测试2: 使用Pydantic模型作为response_model
@app.post("/test2/pydantic", response_model=ResponseModel)
@limiter.limit("5/minute")
def test_pydantic(request: Request):
    return ResponseModel(code=200, message="成功", data={"token": "test"})


# 测试3: dict + response_model=dict
@app.post("/test3/dict-model", response_model=dict)
@limiter.limit("5/minute")
def test_dict_model(request: Request):
    return {"access_token": "test_token", "token_type": "bearer"}


# 测试4: 不使用response_model
@app.post("/test4/no-model")
@limiter.limit("5/minute")
def test_no_model(request: Request):
    return {"access_token": "test_token", "token_type": "bearer"}


def run_tests():
    """运行所有测试用例"""
    client = TestClient(app)
    
    print("=" * 80)
    print("slowapi 与 FastAPI response_model 兼容性测试")
    print("=" * 80)
    
    tests = [
        ("测试1: dict (无 response_model)", "/test1/dict"),
        ("测试2: Pydantic 模型", "/test2/pydantic"),
        ("测试3: dict + response_model=dict", "/test3/dict-model"),
        ("测试4: 不使用 response_model", "/test4/no-model"),
    ]
    
    for test_name, endpoint in tests:
        print(f"\n{test_name}")
        print("-" * 80)
        try:
            response = client.post(endpoint)
            print(f"✓ 状态码: {response.status_code}")
            print(f"✓ 响应: {response.json()}")
            print(f"✓ Headers: {dict(response.headers)}")
        except Exception as e:
            print(f"✗ 错误: {type(e).__name__}: {e}")
    
    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)


if __name__ == "__main__":
    run_tests()
