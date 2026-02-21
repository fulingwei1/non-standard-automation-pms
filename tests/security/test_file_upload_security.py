"""
文件上传安全测试
"""
import pytest
import io


class TestFileUploadSecurity:
    """文件上传安全测试"""
    
    @pytest.mark.security
    def test_executable_file_upload(self, client, auth_headers):
        """测试可执行文件上传防护"""
        malicious_files = [
            ("malware.exe", b"MZ\x90\x00", "application/x-msdownload"),
            ("script.sh", b"#!/bin/bash\nrm -rf /", "application/x-sh"),
            ("virus.bat", b"@echo off\ndel *.*", "application/x-bat"),
        ]
        
        for filename, content, mime_type in malicious_files:
            file = io.BytesIO(content)
            file.name = filename
            
            response = client.post(
                "/api/files/upload",
                files={"file": (filename, file, mime_type)},
                headers=auth_headers
            )
            
            assert response.status_code in [400, 415], \
                f"应该拒绝可执行文件: {filename}"
    
    @pytest.mark.security
    def test_file_size_limit(self, client, auth_headers):
        """测试文件大小限制"""
        # 超大文件 (100MB)
        large_file = io.BytesIO(b"x" * (100 * 1024 * 1024))
        large_file.name = "large.txt"
        
        response = client.post(
            "/api/files/upload",
            files={"file": (large_file.name, large_file, "text/plain")},
            headers=auth_headers
        )
        
        assert response.status_code in [400, 413], "应该拒绝超大文件"
    
    @pytest.mark.security
    def test_file_extension_validation(self, client, auth_headers):
        """测试文件扩展名验证"""
        # 双扩展名攻击
        file = io.BytesIO(b"test content")
        file.name = "image.jpg.php"
        
        response = client.post(
            "/api/files/upload",
            files={"file": (file.name, file, "image/jpeg")},
            headers=auth_headers
        )
        
        assert response.status_code in [400, 415]
    
    @pytest.mark.security
    def test_path_traversal_in_filename(self, client, auth_headers):
        """测试文件名路径遍历"""
        malicious_filenames = [
            "../../etc/passwd",
            "..\\..\\windows\\system32\\config\\sam",
            "....//....//etc/passwd",
        ]
        
        for filename in malicious_filenames:
            file = io.BytesIO(b"test")
            file.name = filename
            
            response = client.post(
                "/api/files/upload",
                files={"file": (filename, file, "text/plain")},
                headers=auth_headers
            )
            
            assert response.status_code in [400, 404]
    
    @pytest.mark.security
    def test_null_byte_injection(self, client, auth_headers):
        """测试空字节注入"""
        file = io.BytesIO(b"test")
        file.name = "test.txt\x00.php"
        
        response = client.post(
            "/api/files/upload",
            files={"file": (file.name, file, "text/plain")},
            headers=auth_headers
        )
        
        assert response.status_code in [400, 415]
