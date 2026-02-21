"""
权限和授权测试
"""
import pytest


class TestAuthorization:
    """授权测试"""
    
    @pytest.mark.security
    def test_horizontal_privilege_escalation(self, client, user_headers):
        """测试水平越权 - 访问其他用户数据"""
        # 尝试访问其他用户的数据
        other_user_id = 999
        
        response = client.get(
            f"/api/users/{other_user_id}/profile",
            headers=user_headers
        )
        
        # 应该返回403或404
        assert response.status_code in [403, 404]
    
    @pytest.mark.security
    def test_vertical_privilege_escalation(self, client, user_headers):
        """测试垂直越权 - 普通用户执行管理操作"""
        # 普通用户尝试创建用户
        response = client.post(
            "/api/users",
            json={
                "username": "hacker",
                "email": "hacker@test.com",
                "password": "Test@123"
            },
            headers=user_headers
        )
        
        # 应该返回403
        assert response.status_code == 403
    
    @pytest.mark.security
    def test_missing_authentication(self, client):
        """测试缺少认证"""
        endpoints = [
            "/api/projects",
            "/api/users",
            "/api/reports",
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            # 应该返回401
            assert response.status_code == 401
    
    @pytest.mark.security
    def test_token_manipulation(self, client, auth_headers):
        """测试Token篡改"""
        # 篡改token
        manipulated_headers = auth_headers.copy()
        token = manipulated_headers.get('Authorization', '').replace('Bearer ', '')
        
        if token:
            # 修改token的一部分
            manipulated_token = token[:-5] + "XXXXX"
            manipulated_headers['Authorization'] = f'Bearer {manipulated_token}'
            
            response = client.get("/api/projects", headers=manipulated_headers)
            
            # 应该返回401
            assert response.status_code == 401
    
    @pytest.mark.security
    def test_expired_token(self, client):
        """测试过期Token"""
        expired_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE2MDAwMDAwMDB9.XXXXX"
        
        headers = {"Authorization": f"Bearer {expired_token}"}
        response = client.get("/api/projects", headers=headers)
        
        assert response.status_code == 401
    
    @pytest.mark.security
    def test_resource_ownership(self, client, user_headers):
        """测试资源所有权验证"""
        # 尝试删除不属于自己的项目
        response = client.delete(
            "/api/projects/999",
            headers=user_headers
        )
        
        assert response.status_code in [403, 404]
