"""
关键路径计算服务 (CPM - Critical Path Method)
"""
from datetime import date, timedelta
from collections import defaultdict, deque
from typing import List, Dict, Set, Optional
from sqlalchemy.orm import Session

from app.models.models import WbsTask, TaskDependency, Project


class CpmService:
    """关键路径计算服务"""
    
    def __init__(self, db: Session):
        self.db = db
        # 中国法定节假日（需要定期更新）
        self.holidays: Set[date] = set()
    
    def calculate_critical_path(self, project_id: int) -> Dict:
        """
        计算关键路径
        
        Args:
            project_id: 项目ID
            
        Returns:
            Dict: {
                'critical_path': [task_ids],
                'project_duration': days,
                'tasks': [{task_id, es, ef, ls, lf, float_days, is_critical}]
            }
        """
        # 1. 获取项目信息
        project = self.db.query(Project).filter(
            Project.project_id == project_id
        ).first()
        
        if not project:
            raise ValueError(f"项目不存在: {project_id}")
        
        # 2. 获取所有叶子任务（非阶段）
        tasks = self.db.query(WbsTask).filter(
            WbsTask.project_id == project_id,
            WbsTask.is_deleted == 0,
            WbsTask.level > 1
        ).all()
        
        if not tasks:
            return {'critical_path': [], 'project_duration': 0, 'tasks': []}
        
        # 3. 获取依赖关系
        dependencies = self.db.query(TaskDependency).filter(
            TaskDependency.project_id == project_id
        ).all()
        
        # 4. 构建图结构
        task_map = {t.task_id: t for t in tasks}
        predecessors = defaultdict(list)  # task_id -> [(pred_id, lag_days, type)]
        successors = defaultdict(list)
        in_degree = defaultdict(int)
        
        for dep in dependencies:
            if dep.task_id in task_map and dep.predecessor_id in task_map:
                predecessors[dep.task_id].append(
                    (dep.predecessor_id, dep.lag_days, dep.depend_type)
                )
                successors[dep.predecessor_id].append(
                    (dep.task_id, dep.lag_days, dep.depend_type)
                )
                in_degree[dep.task_id] += 1
        
        # 5. 拓扑排序
        sorted_task_ids = self._topological_sort(
            [t.task_id for t in tasks], 
            in_degree, 
            predecessors
        )
        
        if sorted_task_ids is None:
            raise ValueError("任务依赖关系存在循环，无法计算关键路径")
        
        # 6. 前向遍历：计算ES(最早开始)和EF(最早完成)
        es = {}  # Earliest Start
        ef = {}  # Earliest Finish
        
        project_start = project.plan_start_date
        
        for task_id in sorted_task_ids:
            task = task_map[task_id]
            
            if not predecessors[task_id]:
                # 没有前置任务，从项目开始日期开始
                es[task_id] = project_start
            else:
                # ES = MAX(所有前置任务的完成时间 + lag)
                max_date = project_start
                for pred_id, lag_days, dep_type in predecessors[task_id]:
                    if pred_id in ef:
                        pred_finish = self._apply_dependency(
                            ef[pred_id], lag_days, dep_type, 'forward'
                        )
                        if pred_finish > max_date:
                            max_date = pred_finish
                es[task_id] = max_date
            
            # EF = ES + duration - 1 (工作日)
            ef[task_id] = self._add_workdays(es[task_id], task.plan_duration - 1)
        
        # 7. 计算项目结束日期
        project_end = max(ef.values()) if ef else project_start
        
        # 8. 后向遍历：计算LF(最迟完成)和LS(最迟开始)
        ls = {}  # Latest Start
        lf = {}  # Latest Finish
        
        for task_id in reversed(sorted_task_ids):
            task = task_map[task_id]
            
            if not successors[task_id]:
                # 没有后置任务，最迟完成=项目结束
                lf[task_id] = project_end
            else:
                # LF = MIN(所有后置任务的开始时间 - lag)
                min_date = project_end
                for succ_id, lag_days, dep_type in successors[task_id]:
                    if succ_id in ls:
                        succ_start = self._apply_dependency(
                            ls[succ_id], lag_days, dep_type, 'backward'
                        )
                        if succ_start < min_date:
                            min_date = succ_start
                lf[task_id] = min_date
            
            # LS = LF - duration + 1
            ls[task_id] = self._sub_workdays(lf[task_id], task.plan_duration - 1)
        
        # 9. 计算浮动时间，标记关键路径
        critical_path = []
        task_results = []
        
        for task in tasks:
            tid = task.task_id
            if tid in es and tid in ls:
                float_days = self._workdays_between(es[tid], ls[tid])
                is_critical = float_days == 0
                
                # 更新数据库
                task.float_days = float_days
                task.earliest_start = es[tid]
                task.latest_finish = lf[tid]
                task.is_critical = 1 if is_critical else 0
                
                if is_critical:
                    critical_path.append(tid)
                
                task_results.append({
                    'task_id': tid,
                    'task_name': task.task_name,
                    'wbs_code': task.wbs_code,
                    'duration': task.plan_duration,
                    'es': str(es[tid]),
                    'ef': str(ef[tid]),
                    'ls': str(ls[tid]),
                    'lf': str(lf[tid]),
                    'float_days': float_days,
                    'is_critical': is_critical
                })
        
        # 10. 提交更新
        self.db.commit()
        
        # 按关键路径排序
        critical_path_sorted = sorted(
            critical_path,
            key=lambda x: es.get(x, project_start)
        )
        
        return {
            'critical_path': critical_path_sorted,
            'project_duration': self._workdays_between(project_start, project_end),
            'project_start': str(project_start),
            'project_end': str(project_end),
            'tasks': task_results
        }
    
    def _topological_sort(
        self, 
        task_ids: List[int],
        in_degree: Dict[int, int],
        predecessors: Dict[int, List]
    ) -> Optional[List[int]]:
        """
        拓扑排序（Kahn算法）
        返回None表示存在环路
        """
        # 复制入度字典
        in_deg = {tid: in_degree.get(tid, 0) for tid in task_ids}
        
        # 入度为0的任务入队
        queue = deque([tid for tid in task_ids if in_deg[tid] == 0])
        result = []
        
        while queue:
            tid = queue.popleft()
            result.append(tid)
            
            # 找到所有以该任务为前置的任务
            for other_tid in task_ids:
                for pred_id, _, _ in predecessors.get(other_tid, []):
                    if pred_id == tid:
                        in_deg[other_tid] -= 1
                        if in_deg[other_tid] == 0:
                            queue.append(other_tid)
        
        # 如果结果数量不等于任务数量，说明有环
        if len(result) != len(task_ids):
            return None
        
        return result
    
    def _apply_dependency(
        self, 
        base_date: date, 
        lag_days: int, 
        dep_type: str,
        direction: str
    ) -> date:
        """
        应用依赖关系计算日期
        
        Args:
            base_date: 基准日期
            lag_days: 延迟天数
            dep_type: 依赖类型 (FS/SS/FF/SF)
            direction: 计算方向 (forward/backward)
        """
        if direction == 'forward':
            # 前向计算：计算后置任务的开始时间
            if dep_type == 'FS':  # Finish-to-Start
                return self._add_workdays(base_date, lag_days + 1)
            elif dep_type == 'SS':  # Start-to-Start
                return self._add_workdays(base_date, lag_days)
            elif dep_type == 'FF':  # Finish-to-Finish
                return self._add_workdays(base_date, lag_days)
            elif dep_type == 'SF':  # Start-to-Finish
                return self._add_workdays(base_date, lag_days)
        else:
            # 后向计算：计算前置任务的完成时间
            if dep_type == 'FS':
                return self._sub_workdays(base_date, lag_days + 1)
            elif dep_type == 'SS':
                return self._sub_workdays(base_date, lag_days)
            elif dep_type == 'FF':
                return self._sub_workdays(base_date, lag_days)
            elif dep_type == 'SF':
                return self._sub_workdays(base_date, lag_days)
        
        return base_date
    
    def _add_workdays(self, start_date: date, days: int) -> date:
        """添加工作日（跳过周末和节假日）"""
        if days <= 0:
            return start_date
        
        current = start_date
        added = 0
        
        while added < days:
            current += timedelta(days=1)
            if self._is_workday(current):
                added += 1
        
        return current
    
    def _sub_workdays(self, end_date: date, days: int) -> date:
        """减去工作日"""
        if days <= 0:
            return end_date
        
        current = end_date
        subtracted = 0
        
        while subtracted < days:
            current -= timedelta(days=1)
            if self._is_workday(current):
                subtracted += 1
        
        return current
    
    def _workdays_between(self, start_date: date, end_date: date) -> int:
        """计算两个日期之间的工作日数"""
        if start_date >= end_date:
            return 0
        
        count = 0
        current = start_date
        
        while current < end_date:
            current += timedelta(days=1)
            if self._is_workday(current):
                count += 1
        
        return count
    
    def _is_workday(self, d: date) -> bool:
        """判断是否是工作日"""
        # 周末
        if d.weekday() >= 5:
            return False
        # 节假日
        if d in self.holidays:
            return False
        return True
    
    def check_dependency_cycle(
        self, 
        project_id: int, 
        new_task_id: int, 
        new_predecessor_id: int
    ) -> bool:
        """
        检查添加依赖后是否会产生环路
        
        Returns:
            True: 存在环路（不能添加）
            False: 不存在环路（可以添加）
        """
        # 获取所有依赖关系
        dependencies = self.db.query(TaskDependency).filter(
            TaskDependency.project_id == project_id
        ).all()
        
        # 构建邻接表
        graph = defaultdict(set)
        for dep in dependencies:
            graph[dep.predecessor_id].add(dep.task_id)
        
        # 添加新的依赖
        graph[new_predecessor_id].add(new_task_id)
        
        # DFS检测环路
        visited = set()
        rec_stack = set()
        
        def has_cycle(node):
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in graph[node]:
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node)
            return False
        
        # 从新的前置任务开始检测
        return has_cycle(new_predecessor_id)
    
    def auto_schedule(self, project_id: int) -> Dict:
        """
        自动排程：根据依赖关系和工期自动计算任务日期
        
        Returns:
            Dict: 更新后的任务日期列表
        """
        result = self.calculate_critical_path(project_id)
        
        # 更新任务的计划日期
        for task_info in result['tasks']:
            task = self.db.query(WbsTask).filter(
                WbsTask.task_id == task_info['task_id']
            ).first()
            
            if task:
                task.plan_start_date = date.fromisoformat(task_info['es'])
                task.plan_end_date = date.fromisoformat(task_info['ef'])
        
        self.db.commit()
        
        return result
