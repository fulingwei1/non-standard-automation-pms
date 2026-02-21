"""
数据库查询性能测试
测试场景: 复杂查询、索引效率、批量操作
"""
import pytest
import time
import statistics
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import Session
from app.models.project import Project
from app.models.user import User
from app.models.project_member import ProjectMember


class TestDatabaseQueryPerformance:
    """数据库查询性能测试"""
    
    @pytest.fixture(autouse=True)
    def setup_test_data(self, test_db: Session):
        """准备测试数据 - 创建大量数据"""
        # 创建1000个项目用于测试
        if test_db.query(Project).count() < 1000:
            projects = []
            for i in range(1000):
                project = Project(
                    name=f"Performance Test Project {i}",
                    code=f"PTP{i:04d}",
                    status="active" if i % 3 == 0 else "pending",
                    budget=100000 + (i * 1000),
                    description=f"Test project for performance testing {i}" * 10
                )
                projects.append(project)
            
            test_db.bulk_save_objects(projects)
            test_db.commit()
    
    @pytest.mark.performance
    def test_simple_query_performance(self, test_db: Session):
        """测试简单查询性能"""
        iterations = 100
        times = []
        
        for _ in range(iterations):
            start = time.time()
            projects = test_db.query(Project).filter(Project.status == "active").all()
            elapsed = time.time() - start
            times.append(elapsed)
        
        avg_time = statistics.mean(times)
        p95_time = statistics.quantiles(times, n=20)[18] if len(times) > 1 else times[0]
        
        assert avg_time < 0.05, f"简单查询平均时间应小于50ms, 实际: {avg_time*1000:.2f}ms"
        assert p95_time < 0.1, f"P95应小于100ms, 实际: {p95_time*1000:.2f}ms"
        
        print(f"\n简单查询性能:")
        print(f"  平均时间: {avg_time*1000:.2f}ms")
        print(f"  P95时间: {p95_time*1000:.2f}ms")
    
    @pytest.mark.performance
    def test_complex_join_query_performance(self, test_db: Session):
        """测试复杂JOIN查询性能"""
        iterations = 50
        times = []
        
        for _ in range(iterations):
            start = time.time()
            
            # 复杂查询: 项目 + 成员 + 用户信息
            results = test_db.query(
                Project.id,
                Project.name,
                func.count(ProjectMember.id).label('member_count')
            ).outerjoin(
                ProjectMember, Project.id == ProjectMember.project_id
            ).group_by(
                Project.id, Project.name
            ).having(
                func.count(ProjectMember.id) > 0
            ).limit(100).all()
            
            elapsed = time.time() - start
            times.append(elapsed)
        
        avg_time = statistics.mean(times)
        assert avg_time < 0.2, f"复杂JOIN查询应小于200ms, 实际: {avg_time*1000:.2f}ms"
        
        print(f"\n复杂JOIN查询性能: {avg_time*1000:.2f}ms")
    
    @pytest.mark.performance
    def test_aggregation_query_performance(self, test_db: Session):
        """测试聚合查询性能"""
        iterations = 50
        times = []
        
        for _ in range(iterations):
            start = time.time()
            
            # 聚合查询
            stats = test_db.query(
                func.count(Project.id).label('total'),
                func.sum(Project.budget).label('total_budget'),
                func.avg(Project.budget).label('avg_budget'),
                func.max(Project.budget).label('max_budget'),
                func.min(Project.budget).label('min_budget')
            ).filter(
                Project.status.in_(['active', 'pending'])
            ).first()
            
            elapsed = time.time() - start
            times.append(elapsed)
        
        avg_time = statistics.mean(times)
        assert avg_time < 0.1, f"聚合查询应小于100ms, 实际: {avg_time*1000:.2f}ms"
        
        print(f"\n聚合查询性能: {avg_time*1000:.2f}ms")
    
    @pytest.mark.performance
    def test_pagination_query_performance(self, test_db: Session):
        """测试分页查询性能 - 测试深分页问题"""
        page_sizes = [10, 50, 100]
        page_numbers = [1, 10, 50, 100]
        
        results = {}
        
        for page_size in page_sizes:
            results[page_size] = {}
            for page_num in page_numbers:
                start = time.time()
                
                offset = (page_num - 1) * page_size
                projects = test_db.query(Project)\
                    .order_by(Project.id)\
                    .limit(page_size)\
                    .offset(offset)\
                    .all()
                
                elapsed = time.time() - start
                results[page_size][page_num] = elapsed
        
        # 检查深分页性能
        for page_size, page_results in results.items():
            for page_num, elapsed in page_results.items():
                assert elapsed < 0.15, \
                    f"分页查询(size={page_size}, page={page_num})应小于150ms, 实际: {elapsed*1000:.2f}ms"
        
        # 打印结果
        print("\n分页性能测试:")
        for page_size, page_results in results.items():
            print(f"  页大小 {page_size}:")
            for page_num, elapsed in page_results.items():
                print(f"    第{page_num}页: {elapsed*1000:.2f}ms")
    
    @pytest.mark.performance
    def test_index_efficiency(self, test_db: Session):
        """测试索引效率 - 对比有无索引的查询"""
        iterations = 100
        
        # 测试索引字段查询 (假设 code 有索引)
        indexed_times = []
        for _ in range(iterations):
            start = time.time()
            project = test_db.query(Project).filter(Project.code == "PTP0500").first()
            elapsed = time.time() - start
            indexed_times.append(elapsed)
        
        # 测试非索引字段查询 (description 可能没索引)
        non_indexed_times = []
        for _ in range(iterations):
            start = time.time()
            projects = test_db.query(Project)\
                .filter(Project.description.like("%500%"))\
                .limit(10)\
                .all()
            elapsed = time.time() - start
            non_indexed_times.append(elapsed)
        
        avg_indexed = statistics.mean(indexed_times)
        avg_non_indexed = statistics.mean(non_indexed_times)
        
        print(f"\n索引效率测试:")
        print(f"  索引字段查询: {avg_indexed*1000:.2f}ms")
        print(f"  非索引字段查询: {avg_non_indexed*1000:.2f}ms")
        print(f"  性能差异: {avg_non_indexed/avg_indexed:.1f}x")
        
        assert avg_indexed < 0.01, f"索引查询应小于10ms, 实际: {avg_indexed*1000:.2f}ms"
    
    @pytest.mark.performance
    def test_bulk_insert_performance(self, test_db: Session):
        """测试批量插入性能"""
        batch_sizes = [100, 500, 1000]
        
        for batch_size in batch_sizes:
            projects = []
            for i in range(batch_size):
                project = Project(
                    name=f"Bulk Test Project {i}",
                    code=f"BTP{i:06d}",
                    status="active",
                    budget=100000
                )
                projects.append(project)
            
            start = time.time()
            test_db.bulk_save_objects(projects)
            test_db.commit()
            elapsed = time.time() - start
            
            per_record = (elapsed / batch_size) * 1000
            
            print(f"\n批量插入 {batch_size} 条:")
            print(f"  总时间: {elapsed*1000:.2f}ms")
            print(f"  单条平均: {per_record:.2f}ms")
            
            assert elapsed < batch_size * 0.01, \
                f"批量插入{batch_size}条应小于{batch_size*10}ms, 实际: {elapsed*1000:.2f}ms"
            
            # 清理
            test_db.query(Project).filter(Project.code.like("BTP%")).delete()
            test_db.commit()
    
    @pytest.mark.performance
    def test_bulk_update_performance(self, test_db: Session):
        """测试批量更新性能"""
        # 准备数据
        project_ids = [p.id for p in test_db.query(Project).limit(500).all()]
        
        start = time.time()
        
        # 批量更新
        test_db.query(Project)\
            .filter(Project.id.in_(project_ids))\
            .update({"status": "updated"}, synchronize_session=False)
        test_db.commit()
        
        elapsed = time.time() - start
        per_record = (elapsed / len(project_ids)) * 1000
        
        print(f"\n批量更新 {len(project_ids)} 条:")
        print(f"  总时间: {elapsed*1000:.2f}ms")
        print(f"  单条平均: {per_record:.2f}ms")
        
        assert elapsed < 1.0, f"批量更新应小于1s, 实际: {elapsed*1000:.2f}ms"
    
    @pytest.mark.performance
    def test_transaction_performance(self, test_db: Session):
        """测试事务性能"""
        iterations = 50
        times = []
        
        for i in range(iterations):
            start = time.time()
            
            try:
                # 开始事务
                project = Project(
                    name=f"Transaction Test {i}",
                    code=f"TTP{i:04d}",
                    status="active",
                    budget=100000
                )
                test_db.add(project)
                test_db.flush()
                
                # 更新
                project.status = "updated"
                test_db.flush()
                
                # 提交
                test_db.commit()
                
            except Exception:
                test_db.rollback()
                raise
            
            elapsed = time.time() - start
            times.append(elapsed)
        
        avg_time = statistics.mean(times)
        assert avg_time < 0.05, f"事务平均时间应小于50ms, 实际: {avg_time*1000:.2f}ms"
        
        print(f"\n事务性能: {avg_time*1000:.2f}ms")
