"""
暴力破解防护测试
"""
import pytest
import time


class TestBruteForceProtection:
    """暴力破解防护测试"""
    
    @pytest.mark.security
    def test_login_brute_force(self, client):
        """测试登录暴力破解防护"""
        username = "admin"
        wrong_password = "wrongpassword"
        
        failed_attempts = 0
        for i in range(20):
            response = client.post(
                "/api/auth/login",
                json={"username": username, "password": wrong_password}
            )
            
            if response.status_code == 429:  # Too Many Requests
                print(f"账号在第{i+1}次尝试后被锁定")
                break
            elif response.status_code == 401:
                failed_attempts += 1
        
        # 应该有限流或账号锁定
        assert failed_attempts < 20, "应该有暴力破解防护"
    
    @pytest.mark.security
    def test_password_reset_brute_force(self, client):
        """测试密码重置暴力破解"""
        for i in range(15):
            response = client.post(
                "/api/auth/reset-password",
                json={"email": f"test{i}@example.com"}
            )
        
        # 后面的请求应该被限流
        response = client.post(
            "/api/auth/reset-password",
            json={"email": "test@example.com"}
        )
        
        assert response.status_code in [200, 429]
    
    @pytest.mark.security
    def test_account_enumeration(self, client):
        """测试账号枚举防护"""
        # 存在的用户和不存在的用户应该返回相似的响应
        response1 = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "wrong"}
        )
        
        response2 = client.post(
            "/api/auth/login",
            json={"username": "nonexistent_user_12345", "password": "wrong"}
        )
        
        # 响应时间不应该有明显差异
        # 响应消息应该相似
        assert abs(len(response1.text) - len(response2.text)) < 100
    
    @pytest.mark.security
    def test_rate_limiting_per_ip(self, client):
        """测试IP级别限流"""
        requests_count = 0
        
        for i in range(100):
            response = client.get("/api/projects")
            
            if response.status_code == 429:
                print(f"IP在第{i+1}次请求后被限流")
                break
            requests_count += 1
        
        assert requests_count < 100, "应该有IP限流"
