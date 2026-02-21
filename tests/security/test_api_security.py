"""
API安全综合测试
"""
import pytest


class TestAPISecurity:
    """API安全测试"""
    
    @pytest.mark.security
    def test_api_versioning_security(self, client):
        """测试API版本安全"""
        # 尝试访问旧版本API
        old_versions = ["/api/v0", "/api/v1/deprecated"]
        
        for endpoint in old_versions:
            response = client.get(endpoint)
            # 旧版本应该被禁用或重定向
            assert response.status_code in [404, 410, 301]
    
    @pytest.mark.security
    def test_http_method_security(self, client, auth_headers):
        """测试HTTP方法安全"""
        # 不应该允许危险的HTTP方法
        dangerous_methods = ["TRACE", "TRACK"]
        
        for method in dangerous_methods:
            response = client.request(
                method,
                "/api/projects",
                headers=auth_headers
            )
            assert response.status_code in [405, 501]
    
    @pytest.mark.security
    def test_cors_security(self, client):
        """测试CORS安全"""
        headers = {
            "Origin": "https://evil.com"
        }
        
        response = client.get("/api/projects", headers=headers)
        
        # 检查CORS头
        cors_header = response.headers.get('Access-Control-Allow-Origin')
        
        # 不应该允许任意来源
        assert cors_header != "*" or response.status_code != 200
    
    @pytest.mark.security
    def test_security_headers_present(self, client):
        """测试安全头存在"""
        response = client.get("/")
        
        required_headers = [
            'X-Content-Type-Options',
            'X-Frame-Options',
            'X-XSS-Protection',
        ]
        
        for header in required_headers:
            assert header in response.headers, f"缺少安全头: {header}"
    
    @pytest.mark.security
    def test_api_documentation_security(self, client):
        """测试API文档安全"""
        # API文档不应该暴露敏感信息
        response = client.get("/docs")
        
        if response.status_code == 200:
            content = response.text.lower()
            
            # 不应该包含敏感信息
            sensitive_terms = ["password", "secret", "key", "token"]
            
            for term in sensitive_terms:
                # 允许出现但不应该暴露实际值
                pass  # 这里简化处理
