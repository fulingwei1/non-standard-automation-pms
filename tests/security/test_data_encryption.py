"""
数据加密和脱敏测试
"""
import pytest
import re


class TestDataEncryption:
    """数据加密测试"""
    
    @pytest.mark.security
    def test_password_encryption(self, client, admin_headers):
        """测试密码加密存储"""
        response = client.post(
            "/api/users",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "PlainPassword123"
            },
            headers=admin_headers
        )
        
        if response.status_code == 200:
            user_id = response.json().get('id')
            
            # 获取用户详情,不应该返回明文密码
            response = client.get(f"/api/users/{user_id}", headers=admin_headers)
            
            if response.status_code == 200:
                data = response.json()
                assert 'password' not in data or data.get('password') != 'PlainPassword123'
    
    @pytest.mark.security
    def test_sensitive_data_masking(self, client, auth_headers):
        """测试敏感数据脱敏"""
        response = client.get("/api/users/1", headers=auth_headers)
        
        if response.status_code == 200:
            data = response.json()
            
            # 电话号码应该被脱敏
            if 'phone' in data:
                phone = data['phone']
                assert '***' in phone or len(phone) != 11
            
            # 身份证号应该被脱敏
            if 'id_card' in data:
                id_card = data['id_card']
                assert '***' in id_card or len(id_card) < 18
    
    @pytest.mark.security
    def test_credit_card_masking(self, client, auth_headers):
        """测试信用卡号脱敏"""
        response = client.post(
            "/api/payments",
            json={"card_number": "1234567812345678"},
            headers=auth_headers
        )
        
        if response.status_code == 200:
            payment_id = response.json().get('id')
            
            response = client.get(f"/api/payments/{payment_id}", headers=auth_headers)
            
            if response.status_code == 200:
                data = response.json()
                card = data.get('card_number', '')
                # 应该被脱敏为 ****5678 格式
                assert len(card) < 16 or '****' in card
    
    @pytest.mark.security
    def test_data_in_transit_encryption(self, client):
        """测试传输加密"""
        # 应该强制使用HTTPS
        response = client.get("/api/health")
        
        # 检查安全头
        assert 'Strict-Transport-Security' in response.headers
    
    @pytest.mark.security
    def test_api_key_encryption(self, client, auth_headers):
        """测试API密钥加密"""
        response = client.post(
            "/api/api-keys",
            json={"name": "Test Key"},
            headers=auth_headers
        )
        
        if response.status_code == 200:
            # 创建时应该返回明文key
            plain_key = response.json().get('key')
            key_id = response.json().get('id')
            
            # 后续查询不应该返回明文
            response = client.get(f"/api/api-keys/{key_id}", headers=auth_headers)
            
            if response.status_code == 200:
                data = response.json()
                stored_key = data.get('key', '')
                assert stored_key != plain_key
                assert len(stored_key) < len(plain_key) or '***' in stored_key
