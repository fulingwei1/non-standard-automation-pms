"""
SQL注入防护测试
测试场景: 各种SQL注入攻击模式
"""
import pytest


class TestSQLInjectionProtection:
    """SQL注入防护测试"""
    
    @pytest.mark.security
    def test_classic_sql_injection(self, client, auth_headers):
        """测试经典SQL注入攻击"""
        payloads = [
            "' OR '1'='1",
            "' OR 1=1--",
            "'; DROP TABLE users--",
            "admin'--",
            "' OR 'x'='x",
            "1' UNION SELECT NULL,NULL--",
        ]
        
        for payload in payloads:
            response = client.get(
                f"/api/users/search?q={payload}",
                headers=auth_headers
            )
            
            # 应该返回正常响应或400错误,不应该暴露数据库错误
            assert response.status_code in [200, 400, 404], \
                f"SQL注入防护失败: {payload}"
            
            if response.status_code == 200:
                # 不应该返回所有用户
                data = response.json()
                assert not (isinstance(data, list) and len(data) > 100), \
                    f"可能存在SQL注入: {payload}"
    
    @pytest.mark.security
    def test_union_based_injection(self, client, auth_headers):
        """测试UNION注入"""
        payloads = [
            "1' UNION SELECT username, password FROM users--",
            "1' UNION ALL SELECT NULL,NULL,NULL--",
            "' UNION SELECT table_name FROM information_schema.tables--",
        ]
        
        for payload in payloads:
            response = client.get(
                f"/api/projects/{payload}",
                headers=auth_headers
            )
            
            assert response.status_code in [400, 404], \
                f"UNION注入防护失败: {payload}"
    
    @pytest.mark.security
    def test_blind_sql_injection(self, client, auth_headers):
        """测试盲注"""
        payloads = [
            "1' AND '1'='1",
            "1' AND '1'='2",
            "1' AND SLEEP(5)--",
            "1' AND (SELECT COUNT(*) FROM users) > 0--",
        ]
        
        import time
        for payload in payloads:
            start = time.time()
            response = client.get(
                f"/api/projects/{payload}",
                headers=auth_headers
            )
            elapsed = time.time() - start
            
            # 不应该有明显延迟 (防止时间盲注)
            assert elapsed < 2.0, f"可能存在时间盲注: {payload}"
            assert response.status_code in [400, 404]
    
    @pytest.mark.security
    def test_error_based_injection(self, client, auth_headers):
        """测试报错注入"""
        payloads = [
            "1' AND (SELECT 1 FROM (SELECT COUNT(*),CONCAT((SELECT version()),FLOOR(RAND(0)*2))x FROM information_schema.tables GROUP BY x)a)--",
            "1' AND extractvalue(1,concat(0x7e,(SELECT @@version)))--",
        ]
        
        for payload in payloads:
            response = client.get(
                f"/api/users/{payload}",
                headers=auth_headers
            )
            
            # 不应该暴露数据库版本信息
            if response.status_code == 500:
                text = response.text.lower()
                assert 'mysql' not in text and 'postgres' not in text, \
                    "暴露了数据库信息"
    
    @pytest.mark.security
    def test_second_order_injection(self, client, admin_headers):
        """测试二次注入"""
        malicious_username = "admin' OR '1'='1'--"
        
        # 创建用户
        response = client.post(
            "/api/users",
            json={
                "username": malicious_username,
                "email": "test@example.com",
                "password": "Test@123"
            },
            headers=admin_headers
        )
        
        if response.status_code == 200:
            user_id = response.json().get('id')
            
            # 查询用户 - 应该安全处理
            response = client.get(
                f"/api/users/{user_id}",
                headers=admin_headers
            )
            assert response.status_code == 200
            
            # 更新用户 - 应该安全处理
            response = client.put(
                f"/api/users/{user_id}",
                json={"email": "updated@example.com"},
                headers=admin_headers
            )
            assert response.status_code in [200, 400]
    
    @pytest.mark.security
    def test_parameterized_queries(self, client, auth_headers):
        """测试参数化查询保护"""
        # 正常查询应该成功
        response = client.get(
            "/api/projects/search?q=test",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # 特殊字符应该被安全处理
        special_chars = ["'", '"', ';', '--', '/*', '*/', 'xp_', 'sp_']
        
        for char in special_chars:
            response = client.get(
                f"/api/projects/search?q={char}",
                headers=auth_headers
            )
            assert response.status_code in [200, 400], \
                f"未正确处理特殊字符: {char}"
    
    @pytest.mark.security
    def test_stored_procedure_injection(self, client, auth_headers):
        """测试存储过程注入"""
        payloads = [
            "'; EXEC xp_cmdshell('dir')--",
            "'; EXEC sp_executesql N'SELECT * FROM users'--",
        ]
        
        for payload in payloads:
            response = client.post(
                "/api/reports/generate",
                json={"filter": payload},
                headers=auth_headers
            )
            assert response.status_code in [400, 404]
    
    @pytest.mark.security
    def test_nosql_injection(self, client, auth_headers):
        """测试NoSQL注入 (MongoDB等)"""
        payloads = [
            {"$gt": ""},
            {"$ne": None},
            {"$regex": ".*"},
        ]
        
        for payload in payloads:
            response = client.post(
                "/api/users/search",
                json={"username": payload},
                headers=auth_headers
            )
            
            # 应该拒绝或安全处理
            assert response.status_code in [200, 400]
            if response.status_code == 200:
                data = response.json()
                # 不应该返回所有用户
                assert not (isinstance(data, list) and len(data) > 100)
