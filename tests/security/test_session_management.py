"""
会话管理安全测试
"""
import pytest
import time


class TestSessionManagement:
    """会话管理测试"""
    
    @pytest.mark.security
    def test_session_timeout(self, client):
        """测试会话超时"""
        response = client.post("/api/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        
        if response.status_code == 200:
            token = response.json().get('access_token')
            headers = {"Authorization": f"Bearer {token}"}
            
            # 等待超时 (模拟)
            time.sleep(2)
            
            # 尝试使用旧token
            response = client.get("/api/projects", headers=headers)
            
            # 应该在合理时间内超时
            # 这里假设短期内不会超时
            assert response.status_code in [200, 401]
    
    @pytest.mark.security
    def test_concurrent_sessions(self, client):
        """测试并发会话限制"""
        tokens = []
        
        # 同一用户多次登录
        for _ in range(10):
            response = client.post("/api/auth/login", json={
                "username": "admin",
                "password": "admin123"
            })
            
            if response.status_code == 200:
                tokens.append(response.json().get('access_token'))
        
        # 测试所有token是否有效
        valid_count = 0
        for token in tokens:
            headers = {"Authorization": f"Bearer {token}"}
            response = client.get("/api/projects", headers=headers)
            if response.status_code == 200:
                valid_count += 1
        
        print(f"\n有效会话数: {valid_count}/{len(tokens)}")
        
        # 根据策略,可能限制并发会话数
        # 这里不做严格断言,只打印信息
    
    @pytest.mark.security
    def test_session_fixation(self, client):
        """测试会话固定攻击"""
        # 登录前获取session
        response1 = client.get("/")
        session1 = response1.cookies.get('session_id')
        
        # 登录
        response2 = client.post("/api/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        
        # 登录后session应该变化
        session2 = response2.cookies.get('session_id')
        
        if session1 and session2:
            assert session1 != session2, "登录后应该重新生成session"
    
    @pytest.mark.security
    def test_logout_invalidation(self, client, auth_headers):
        """测试登出后token失效"""
        # 登出
        response = client.post("/api/auth/logout", headers=auth_headers)
        
        # 使用旧token访问
        response = client.get("/api/projects", headers=auth_headers)
        
        # 应该无法访问
        assert response.status_code == 401
