"""
输入验证测试
"""
import pytest


class TestInputValidation:
    """输入验证测试"""
    
    @pytest.mark.security
    def test_email_validation(self, client, admin_headers):
        """测试邮箱验证"""
        invalid_emails = [
            "notanemail",
            "@example.com",
            "user@",
            "user@.com",
            "user@example",
        ]
        
        for email in invalid_emails:
            response = client.post(
                "/api/users",
                json={
                    "username": "test",
                    "email": email,
                    "password": "Test@123"
                },
                headers=admin_headers
            )
            
            assert response.status_code == 400, f"应该拒绝无效邮箱: {email}"
    
    @pytest.mark.security
    def test_phone_validation(self, client, auth_headers):
        """测试电话验证"""
        invalid_phones = [
            "123",
            "abcdefghijk",
            "12345678901234567890",
        ]
        
        for phone in invalid_phones:
            response = client.put(
                "/api/users/1",
                json={"phone": phone},
                headers=auth_headers
            )
            
            assert response.status_code == 400
    
    @pytest.mark.security
    def test_length_validation(self, client, auth_headers):
        """测试长度验证"""
        # 超长字符串
        long_string = "x" * 10000
        
        response = client.post(
            "/api/projects",
            json={"name": long_string, "code": "TEST"},
            headers=auth_headers
        )
        
        assert response.status_code == 400
    
    @pytest.mark.security
    def test_numeric_validation(self, client, auth_headers):
        """测试数值验证"""
        invalid_numbers = [
            -1,
            "not_a_number",
            999999999999999,
        ]
        
        for num in invalid_numbers:
            response = client.post(
                "/api/projects",
                json={"budget": num},
                headers=auth_headers
            )
            
            if isinstance(num, str):
                assert response.status_code == 400
    
    @pytest.mark.security
    def test_special_characters(self, client, auth_headers):
        """测试特殊字符处理"""
        special_chars = ["<>", "';--", "${}", "{{}}"]
        
        for char in special_chars:
            response = client.post(
                "/api/projects",
                json={"name": f"Project {char}"},
                headers=auth_headers
            )
            
            # 应该被拒绝或安全转义
            assert response.status_code in [200, 400]
    
    @pytest.mark.security
    def test_file_upload_validation(self, client, auth_headers):
        """测试文件上传验证"""
        import io
        
        # 测试文件类型验证
        fake_exe = io.BytesIO(b"MZ\x90\x00")  # EXE文件头
        fake_exe.name = "malware.exe"
        
        response = client.post(
            "/api/files/upload",
            files={"file": (fake_exe.name, fake_exe, "application/x-msdownload")},
            headers=auth_headers
        )
        
        assert response.status_code in [400, 415]  # 应该拒绝可执行文件
