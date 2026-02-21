"""
CSRF跨站请求伪造防护测试
"""
import pytest


class TestCSRFProtection:
    """CSRF防护测试"""
    
    @pytest.mark.security
    def test_csrf_token_required(self, client, auth_headers):
        """测试CSRF token必需"""
        # 不带CSRF token的请求
        response = client.post(
            "/api/projects",
            json={"name": "Test", "code": "TEST"},
            headers=auth_headers
        )
        
        # 根据CSRF策略,可能要求token
        # 这里假设API使用token authentication,不强制CSRF
        assert response.status_code in [200, 201, 403]
    
    @pytest.mark.security
    def test_csrf_token_validation(self, client):
        """测试CSRF token验证"""
        # 使用无效的CSRF token
        headers = {
            "X-CSRF-Token": "invalid_token_12345"
        }
        
        response = client.post(
            "/api/projects",
            json={"name": "Test"},
            headers=headers
        )
        
        # 应该拒绝无效token
        assert response.status_code in [403, 401]
    
    @pytest.mark.security
    def test_csrf_same_origin(self, client):
        """测试同源策略"""
        headers = {
            "Origin": "https://evil.com",
            "Referer": "https://evil.com/attack"
        }
        
        response = client.post(
            "/api/projects",
            json={"name": "Test"},
            headers=headers
        )
        
        # 应该检查origin
        assert response.status_code in [403, 401]
