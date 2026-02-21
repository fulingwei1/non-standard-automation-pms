"""
XSS跨站脚本攻击防护测试
"""
import pytest
import html


class TestXSSProtection:
    """XSS防护测试"""
    
    @pytest.mark.security
    def test_reflected_xss(self, client, auth_headers):
        """测试反射型XSS"""
        payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "<svg onload=alert('XSS')>",
            "javascript:alert('XSS')",
            "<iframe src='javascript:alert(1)'>",
        ]
        
        for payload in payloads:
            response = client.get(
                f"/api/search?q={payload}",
                headers=auth_headers
            )
            
            if response.status_code == 200:
                content = response.text
                # 应该被转义或过滤
                assert payload not in content or html.escape(payload) in content
    
    @pytest.mark.security
    def test_stored_xss(self, client, auth_headers):
        """测试存储型XSS"""
        payload = "<script>document.cookie</script>"
        
        response = client.post(
            "/api/projects",
            json={"name": payload, "code": "XSS001"},
            headers=auth_headers
        )
        
        if response.status_code == 200:
            project_id = response.json().get('id')
            
            # 获取数据时应该被转义
            response = client.get(
                f"/api/projects/{project_id}",
                headers=auth_headers
            )
            
            if response.status_code == 200:
                data = response.json()
                name = data.get('name', '')
                # 应该被转义或过滤
                assert '<script>' not in name or html.escape(payload) in name
    
    @pytest.mark.security
    def test_dom_xss(self, client):
        """测试DOM型XSS"""
        payload = "#<img src=x onerror=alert('XSS')>"
        
        response = client.get(f"/projects{payload}")
        
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            assert '<img src=x onerror=' not in response.text
    
    @pytest.mark.security
    def test_xss_in_headers(self, client):
        """测试HTTP头XSS"""
        headers = {
            "X-Custom-Header": "<script>alert('XSS')</script>",
            "Referer": "javascript:alert(1)"
        }
        
        response = client.get("/api/projects", headers=headers)
        
        # 应该安全处理或拒绝
        assert response.status_code in [200, 400]
    
    @pytest.mark.security
    def test_content_security_policy(self, client):
        """测试内容安全策略"""
        response = client.get("/")
        
        # 应该有CSP头
        assert 'Content-Security-Policy' in response.headers or \
               'X-Content-Security-Policy' in response.headers
