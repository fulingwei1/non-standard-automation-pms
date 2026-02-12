# -*- coding: utf-8 -*-
"""
通用批量操作框架

提供统一的批量操作接口，减少代码重复，提高开发效率。

使用示例：
    from app.utils.batch_operations import BatchOperationExecutor
    
    executor = BatchOperationExecutor(
        model=TaskUnified,
        db=db,
        current_user=current_user
    )
    
    result = executor.execute(
        entity_ids=[1, 2, 3],
        operation_func=lambda task: setattr(task, 'status', 'COMPLETED'),
        validator_func=lambda task: task.status != 'COMPLETED',
        error_message="任务已完成"
    )
"""

from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Type,
    TypeVar,
)
from sqlalchemy.orm import Session

from app.models.user import User

# 类型变量
ModelType = TypeVar("ModelType")


class BatchOperationResult:
    """批量操作结果"""
    
    def __init__(self):
        self.success_count = 0
        self.failed_count = 0
        self.failed_items: List[Dict[str, Any]] = []
    
    def add_success(self):
        """记录成功"""
        self.success_count += 1
    
    def add_failure(self, entity_id: Any, reason: str, id_field: str = "id"):
        """记录失败"""
        self.failed_count += 1
        self.failed_items.append({
            id_field: entity_id,
            "reason": reason
        })
    
    def to_dict(self, id_field: str = "id") -> Dict[str, Any]:
        """转换为字典，支持自定义ID字段名"""
        return {
            "success_count": self.success_count,
            "failed_count": self.failed_count,
            "failed_items": [
                {id_field: item.get("id") or item.get(id_field), "reason": item.get("reason")}
                if isinstance(item, dict) else item
                for item in self.failed_items
            ]
        }
    


class BatchOperationExecutor(Generic[ModelType]):
    """
    批量操作执行器
    
    提供统一的批量操作接口，支持：
    - 自定义验证逻辑
    - 自定义操作逻辑
    - 自定义日志记录
    - 数据范围过滤
    - 事务管理
    """
    
    def __init__(
        self,
        model: Type[ModelType],
        db: Session,
        current_user: User,
        id_field: str = "id",
        scope_filter_func: Optional[Callable[[Session, List[Any], User], List[ModelType]]] = None,
    ):
        """
        初始化批量操作执行器
        
        Args:
            model: SQLAlchemy 模型类
            db: 数据库会话
            current_user: 当前用户
            id_field: ID字段名，默认为 "id"
            scope_filter_func: 数据范围过滤函数，用于过滤用户有权限访问的数据
        """
        self.model = model
        self.db = db
        self.current_user = current_user
        self.id_field = id_field
        self.scope_filter_func = scope_filter_func
    
    def execute(
        self,
        entity_ids: List[Any],
        operation_func: Callable[[ModelType], None],
        validator_func: Optional[Callable[[ModelType], bool]] = None,
        error_message: Optional[str] = None,
        log_func: Optional[Callable[[ModelType, str], None]] = None,
        operation_type: Optional[str] = None,
        pre_filter_func: Optional[Callable[[Session, List[Any]], List[ModelType]]] = None,
    ) -> BatchOperationResult:
        """
        执行批量操作
        
        Args:
            entity_ids: 实体ID列表
            operation_func: 操作函数，接收实体对象，执行具体操作
            validator_func: 验证函数，返回True表示可以操作，False表示跳过
            error_message: 验证失败时的错误消息
            log_func: 日志记录函数，接收实体对象和操作类型
            operation_type: 操作类型，用于日志记录
            pre_filter_func: 预过滤函数，用于在操作前过滤实体列表
        
        Returns:
            BatchOperationResult: 批量操作结果
        """
        if not entity_ids:
            return BatchOperationResult()
        
        result = BatchOperationResult()
        
        # 步骤1: 获取实体对象
        if pre_filter_func:
            entities = pre_filter_func(self.db, entity_ids)
        elif self.scope_filter_func:
            entities = self.scope_filter_func(self.db, entity_ids, self.current_user)
        else:
            # 默认查询
            id_column = getattr(self.model, self.id_field)
            entities = self.db.query(self.model).filter(
                id_column.in_(entity_ids)
            ).all()
        
        # 创建ID到实体的映射
        entity_map = {getattr(entity, self.id_field): entity for entity in entities}
        
        # 步骤2: 循环处理每个实体
        for entity_id in entity_ids:
            entity = entity_map.get(entity_id)
            
            # 检查实体是否存在
            if not entity:
                # 使用模型特定的ID字段名
                id_field_name = f"{self.model.__tablename__.rstrip('s')}_id" if hasattr(self.model, '__tablename__') else "id"
                result.add_failure(entity_id, "实体不存在或无访问权限", id_field=id_field_name)
                continue
            
            try:
                # 步骤3: 验证（如果提供了验证函数）
                if validator_func:
                    if not validator_func(entity):
                        reason = error_message or "验证失败"
                        id_field_name = f"{self.model.__tablename__.rstrip('s')}_id" if hasattr(self.model, '__tablename__') else "id"
                        result.add_failure(entity_id, reason, id_field=id_field_name)
                        continue
                
                # 步骤4: 执行操作
                operation_func(entity)
                
                # 步骤5: 记录日志（如果提供了日志函数）
                if log_func:
                    log_func(entity, operation_type or "BATCH_OPERATION")
                elif operation_type:
                    # 默认日志记录（如果模型有updated_by字段）
                    if hasattr(entity, 'updated_by'):
                        setattr(entity, 'updated_by', self.current_user.id)
                
                # 步骤6: 添加到会话
                self.db.add(entity)
                
                result.add_success()
                
            except Exception as e:
                id_field_name = f"{self.model.__tablename__.rstrip('s')}_id" if hasattr(self.model, '__tablename__') else "id"
                result.add_failure(entity_id, str(e), id_field=id_field_name)
        
        # 步骤7: 提交事务
        try:
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            # 如果提交失败，将所有成功项标记为失败
            id_field_name = f"{self.model.__tablename__.rstrip('s')}_id" if hasattr(self.model, '__tablename__') else "id"
            for item in result.failed_items:
                item_id = item.get("id") or item.get(id_field_name)
                if item_id and item_id not in entity_ids:
                    result.add_failure(item_id, f"事务提交失败: {str(e)}", id_field=id_field_name)
        
        return result
    
    def batch_update(
        self,
        entity_ids: List[Any],
        update_func: Callable[[ModelType], None],
        validator_func: Optional[Callable[[ModelType], bool]] = None,
        error_message: Optional[str] = None,
        log_func: Optional[Callable[[ModelType, str], None]] = None,
        operation_type: str = "BATCH_UPDATE",
    ) -> BatchOperationResult:
        """
        批量更新
        
        Args:
            entity_ids: 实体ID列表
            update_func: 更新函数，接收实体对象，执行更新操作
            validator_func: 验证函数
            error_message: 验证失败时的错误消息
            log_func: 日志记录函数
            operation_type: 操作类型
        
        Returns:
            BatchOperationResult: 批量操作结果
        """
        return self.execute(
            entity_ids=entity_ids,
            operation_func=update_func,
            validator_func=validator_func,
            error_message=error_message,
            log_func=log_func,
            operation_type=operation_type,
        )
    
    def batch_delete(
        self,
        entity_ids: List[Any],
        validator_func: Optional[Callable[[ModelType], bool]] = None,
        error_message: Optional[str] = None,
        log_func: Optional[Callable[[ModelType, str], None]] = None,
        soft_delete: bool = True,
        soft_delete_field: str = "is_active",
    ) -> BatchOperationResult:
        """
        批量删除
        
        Args:
            entity_ids: 实体ID列表
            validator_func: 验证函数
            error_message: 验证失败时的错误消息
            log_func: 日志记录函数
            soft_delete: 是否软删除，默认为True
            soft_delete_field: 软删除字段名，默认为 "is_active"
        
        Returns:
            BatchOperationResult: 批量操作结果
        """
        def delete_func(entity: ModelType):
            if soft_delete:
                if hasattr(entity, soft_delete_field):
                    setattr(entity, soft_delete_field, False)
                else:
                    raise ValueError(f"实体不支持软删除，缺少字段: {soft_delete_field}")
            else:
                self.db.delete(entity)
        
        return self.execute(
            entity_ids=entity_ids,
            operation_func=delete_func,
            validator_func=validator_func,
            error_message=error_message,
            log_func=log_func,
            operation_type="BATCH_DELETE",
        )
    
    def batch_status_update(
        self,
        entity_ids: List[Any],
        new_status: str,
        status_field: str = "status",
        validator_func: Optional[Callable[[ModelType], bool]] = None,
        error_message: Optional[str] = None,
        log_func: Optional[Callable[[ModelType, str], None]] = None,
    ) -> BatchOperationResult:
        """
        批量状态更新
        
        Args:
            entity_ids: 实体ID列表
            new_status: 新状态值
            status_field: 状态字段名，默认为 "status"
            validator_func: 验证函数
            error_message: 验证失败时的错误消息
            log_func: 日志记录函数
        
        Returns:
            BatchOperationResult: 批量操作结果
        """
        def update_status_func(entity: ModelType):
            if not hasattr(entity, status_field):
                raise ValueError(f"实体缺少状态字段: {status_field}")
            setattr(entity, status_field, new_status)
        
        return self.execute(
            entity_ids=entity_ids,
            operation_func=update_status_func,
            validator_func=validator_func,
            error_message=error_message,
            log_func=log_func,
            operation_type="BATCH_STATUS_UPDATE",
        )


def create_scope_filter(
    model: Type[ModelType],
    scope_service: Any,
    filter_method: str,
) -> Callable[[Session, List[Any], User], List[ModelType]]:
    """
    创建数据范围过滤函数
    
    Args:
        model: SQLAlchemy 模型类
        scope_service: 数据范围服务实例
        filter_method: 过滤方法名，如 "filter_projects_by_scope"
    
    Returns:
        过滤函数
    """
    def filter_func(db: Session, entity_ids: List[Any], current_user: User) -> List[ModelType]:
        id_column = getattr(model, "id")
        query = db.query(model).filter(id_column.in_(entity_ids))
        filter_method_func = getattr(scope_service, filter_method)
        query = filter_method_func(db, query, current_user)
        return query.all()
    
    return filter_func
