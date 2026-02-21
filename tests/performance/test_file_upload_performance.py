"""
文件上传性能测试
测试场景: Excel导入导出、PDF生成、大文件上传
"""
import pytest
import time
import statistics
import io
from typing import BinaryIO


class TestFileUploadPerformance:
    """文件处理性能测试"""
    
    @pytest.mark.performance
    def test_small_file_upload(self, client, auth_headers):
        """测试小文件上传性能 (<1MB)"""
        num_uploads = 50
        file_sizes = [10240, 51200, 102400, 512000]  # 10KB, 50KB, 100KB, 500KB
        
        for size in file_sizes:
            times = []
            file_data = b"x" * size
            
            for i in range(num_uploads):
                file = io.BytesIO(file_data)
                file.name = f"test_{i}.txt"
                
                start = time.time()
                response = client.post(
                    "/api/files/upload",
                    files={"file": (file.name, file, "text/plain")},
                    headers=auth_headers
                )
                elapsed = time.time() - start
                times.append(elapsed)
            
            avg_time = statistics.mean(times)
            throughput = (size * num_uploads) / sum(times) / 1024 / 1024  # MB/s
            
            print(f"\n小文件上传 ({size/1024:.0f}KB x {num_uploads}):")
            print(f"  平均时间: {avg_time*1000:.2f}ms")
            print(f"  吞吐量: {throughput:.2f}MB/s")
            
            assert avg_time < 0.5, f"上传{size/1024:.0f}KB应<500ms"
    
    @pytest.mark.performance
    def test_large_file_upload(self, client, auth_headers):
        """测试大文件上传性能 (>10MB)"""
        file_sizes = [10*1024*1024, 50*1024*1024]  # 10MB, 50MB
        
        for size in file_sizes:
            file_data = b"x" * size
            file = io.BytesIO(file_data)
            file.name = "large_file.bin"
            
            start = time.time()
            response = client.post(
                "/api/files/upload",
                files={"file": (file.name, file, "application/octet-stream")},
                headers=auth_headers
            )
            elapsed = time.time() - start
            
            throughput = size / elapsed / 1024 / 1024  # MB/s
            
            print(f"\n大文件上传 ({size/1024/1024:.0f}MB):")
            print(f"  时间: {elapsed:.2f}s")
            print(f"  吞吐量: {throughput:.2f}MB/s")
            
            assert throughput > 1.0, f"吞吐量应>1MB/s"
    
    @pytest.mark.performance
    def test_excel_import_performance(self, client, auth_headers):
        """测试Excel导入性能"""
        import openpyxl
        
        row_counts = [100, 500, 1000, 5000]
        
        for row_count in row_counts:
            # 创建Excel
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.append(['ID', 'Name', 'Email', 'Department'])
            
            for i in range(row_count):
                ws.append([i+1, f'User {i}', f'user{i}@test.com', 'IT'])
            
            excel_file = io.BytesIO()
            wb.save(excel_file)
            excel_file.seek(0)
            excel_file.name = f'import_{row_count}.xlsx'
            
            start = time.time()
            response = client.post(
                "/api/users/import",
                files={"file": (excel_file.name, excel_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
                headers=auth_headers
            )
            elapsed = time.time() - start
            
            per_row = (elapsed / row_count) * 1000
            
            print(f"\nExcel导入 ({row_count}行):")
            print(f"  总时间: {elapsed:.2f}s")
            print(f"  单行平均: {per_row:.2f}ms")
            
            assert per_row < 50, f"单行导入应<50ms"
    
    @pytest.mark.performance
    def test_excel_export_performance(self, client, auth_headers):
        """测试Excel导出性能"""
        record_counts = [100, 500, 1000]
        
        for count in record_counts:
            start = time.time()
            response = client.get(
                f"/api/projects/export?limit={count}",
                headers=auth_headers
            )
            elapsed = time.time() - start
            
            if response.status_code == 200:
                file_size = len(response.content)
                per_record = (elapsed / count) * 1000
                
                print(f"\nExcel导出 ({count}条):")
                print(f"  时间: {elapsed:.2f}s")
                print(f"  文件大小: {file_size/1024:.2f}KB")
                print(f"  单条平均: {per_record:.2f}ms")
                
                assert per_record < 30, f"单条导出应<30ms"
    
    @pytest.mark.performance
    def test_pdf_generation_performance(self, client, auth_headers):
        """测试PDF生成性能"""
        page_counts = [1, 5, 10, 20]
        
        for pages in page_counts:
            start = time.time()
            response = client.post(
                "/api/reports/pdf",
                json={"project_id": 1, "pages": pages},
                headers=auth_headers
            )
            elapsed = time.time() - start
            
            if response.status_code == 200:
                per_page = (elapsed / pages) * 1000
                
                print(f"\nPDF生成 ({pages}页):")
                print(f"  时间: {elapsed:.2f}s")
                print(f"  单页平均: {per_page:.2f}ms")
                
                assert per_page < 500, f"单页生成应<500ms"
    
    @pytest.mark.performance
    def test_concurrent_file_uploads(self, client, auth_headers):
        """测试并发文件上传"""
        from concurrent.futures import ThreadPoolExecutor
        
        num_concurrent = 20
        file_size = 1024 * 100  # 100KB
        
        def upload_file(index):
            file_data = b"x" * file_size
            file = io.BytesIO(file_data)
            file.name = f"concurrent_{index}.txt"
            
            start = time.time()
            response = client.post(
                "/api/files/upload",
                files={"file": (file.name, file, "text/plain")},
                headers=auth_headers
            )
            elapsed = time.time() - start
            return response.status_code, elapsed
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(upload_file, range(num_concurrent)))
        
        status_codes = [r[0] for r in results]
        times = [r[1] for r in results]
        
        success_rate = sum(1 for c in status_codes if c == 200) / num_concurrent
        avg_time = statistics.mean(times)
        
        print(f"\n并发上传 ({num_concurrent}个文件):")
        print(f"  成功率: {success_rate*100:.1f}%")
        print(f"  平均时间: {avg_time*1000:.2f}ms")
        
        assert success_rate >= 0.9, "成功率应>=90%"
    
    @pytest.mark.performance
    def test_file_download_performance(self, client, auth_headers):
        """测试文件下载性能"""
        file_ids = [1, 2, 3, 4, 5]
        times = []
        
        for file_id in file_ids:
            start = time.time()
            response = client.get(
                f"/api/files/{file_id}/download",
                headers=auth_headers
            )
            elapsed = time.time() - start
            times.append(elapsed)
            
            if response.status_code == 200:
                size = len(response.content)
                throughput = size / elapsed / 1024 / 1024 if elapsed > 0 else 0
                print(f"  文件{file_id}: {size/1024:.2f}KB, {elapsed*1000:.2f}ms, {throughput:.2f}MB/s")
        
        avg_time = statistics.mean(times)
        assert avg_time < 1.0, "平均下载时间应<1s"
    
    @pytest.mark.performance
    def test_image_processing_performance(self, client, auth_headers):
        """测试图片处理性能"""
        from PIL import Image
        
        sizes = [(800, 600), (1920, 1080), (3840, 2160)]
        
        for width, height in sizes:
            # 创建测试图片
            img = Image.new('RGB', (width, height), color='red')
            img_file = io.BytesIO()
            img.save(img_file, format='JPEG')
            img_file.seek(0)
            img_file.name = f'test_{width}x{height}.jpg'
            
            start = time.time()
            response = client.post(
                "/api/images/upload",
                files={"file": (img_file.name, img_file, "image/jpeg")},
                headers=auth_headers
            )
            elapsed = time.time() - start
            
            print(f"\n图片处理 ({width}x{height}):")
            print(f"  上传时间: {elapsed*1000:.2f}ms")
            
            assert elapsed < 2.0, f"{width}x{height}图片处理应<2s"
