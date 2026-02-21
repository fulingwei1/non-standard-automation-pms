"""
邮件发送性能测试
"""
import pytest
import time
import statistics


class TestEmailPerformance:
    """邮件发送性能测试"""
    
    @pytest.mark.performance
    def test_single_email_send_time(self, client, auth_headers):
        """测试单封邮件发送时间"""
        times = []
        
        for i in range(10):
            start = time.time()
            response = client.post(
                "/api/emails/send",
                json={
                    "to": f"test{i}@example.com",
                    "subject": "Test",
                    "body": "Test email"
                },
                headers=auth_headers
            )
            elapsed = time.time() - start
            times.append(elapsed)
        
        avg_time = statistics.mean(times)
        print(f"\n单封邮件发送: {avg_time*1000:.2f}ms")
        
        assert avg_time < 2.0, "单封邮件应<2s"
    
    @pytest.mark.performance
    def test_bulk_email_performance(self, client, auth_headers):
        """测试批量邮件性能"""
        recipients = [f"test{i}@example.com" for i in range(100)]
        
        start = time.time()
        response = client.post(
            "/api/emails/bulk-send",
            json={
                "recipients": recipients,
                "subject": "Bulk Test",
                "body": "Bulk email test"
            },
            headers=auth_headers
        )
        elapsed = time.time() - start
        
        per_email = (elapsed / len(recipients)) * 1000
        
        print(f"\n批量邮件 ({len(recipients)}封):")
        print(f"  总时间: {elapsed:.2f}s")
        print(f"  单封平均: {per_email:.2f}ms")
        
        assert per_email < 100, "单封应<100ms"
