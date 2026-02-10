"""
用户认证与权限模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# 用户-角色关联表
user_role = Table(
    'sys_user_role',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('sys_user.user_id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('sys_role.role_id'), primary_key=True)
)

# 角色-权限关联表
role_permission = Table(
    'sys_role_permission',
    Base.metadata,
    Column('role_id', Integer, ForeignKey('sys_role.role_id'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('sys_permission.permission_id'), primary_key=True)
)

# 角色-菜单关联表
role_menu = Table(
    'sys_role_menu',
    Base.metadata,
    Column('role_id', Integer, ForeignKey('sys_role.role_id'), primary_key=True),
    Column('menu_id', Integer, ForeignKey('sys_menu.menu_id'), primary_key=True)
)


class SysUser(Base):
    """系统用户表"""
    __tablename__ = 'sys_user'
    
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, comment='用户名')
    password_hash = Column(String(128), nullable=False, comment='密码哈希')
    employee_code = Column(String(20), comment='工号')
    real_name = Column(String(50), comment='真实姓名')
    email = Column(String(100), comment='邮箱')
    mobile = Column(String(20), comment='手机')
    avatar = Column(String(255), comment='头像URL')
    dept_id = Column(Integer, ForeignKey('sys_dept.dept_id'), comment='部门ID')
    position = Column(String(50), comment='岗位')
    wechat_userid = Column(String(50), comment='企微用户ID')
    status = Column(String(10), default='正常', comment='状态：正常/禁用/锁定')
    last_login_time = Column(DateTime, comment='最后登录时间')
    last_login_ip = Column(String(50), comment='最后登录IP')
    login_fail_count = Column(Integer, default=0, comment='登录失败次数')
    password_update_time = Column(DateTime, comment='密码更新时间')
    is_deleted = Column(Boolean, default=False, comment='是否删除')
    created_time = Column(DateTime, default=datetime.now)
    updated_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    created_by = Column(Integer, comment='创建人')
    
    # 关联
    roles = relationship('SysRole', secondary=user_role, back_populates='users')
    dept = relationship('SysDept', back_populates='users')
    tokens = relationship('SysUserToken', back_populates='user')
    login_logs = relationship('SysLoginLog', back_populates='user')


class SysRole(Base):
    """系统角色表"""
    __tablename__ = 'sys_role'
    
    role_id = Column(Integer, primary_key=True, autoincrement=True)
    role_code = Column(String(50), unique=True, nullable=False, comment='角色编码')
    role_name = Column(String(50), nullable=False, comment='角色名称')
    description = Column(String(200), comment='角色描述')
    data_scope = Column(String(20), default='self', comment='数据权限范围：all/dept/dept_and_child/self')
    sort_order = Column(Integer, default=0, comment='排序')
    status = Column(String(10), default='正常', comment='状态：正常/禁用')
    is_system = Column(Boolean, default=False, comment='是否系统内置角色')
    is_deleted = Column(Boolean, default=False)
    created_time = Column(DateTime, default=datetime.now)
    updated_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关联
    users = relationship('SysUser', secondary=user_role, back_populates='roles')
    permissions = relationship('SysPermission', secondary=role_permission, back_populates='roles')
    menus = relationship('SysMenu', secondary=role_menu, back_populates='roles')


class SysPermission(Base):
    """系统权限表"""
    __tablename__ = 'sys_permission'
    
    permission_id = Column(Integer, primary_key=True, autoincrement=True)
    permission_code = Column(String(100), unique=True, nullable=False, comment='权限编码')
    permission_name = Column(String(50), nullable=False, comment='权限名称')
    resource_type = Column(String(20), comment='资源类型：menu/button/api')
    parent_id = Column(Integer, default=0, comment='父权限ID')
    path = Column(String(200), comment='权限路径')
    method = Column(String(10), comment='请求方法：GET/POST/PUT/DELETE')
    description = Column(String(200), comment='描述')
    sort_order = Column(Integer, default=0)
    status = Column(String(10), default='正常')
    created_time = Column(DateTime, default=datetime.now)
    
    # 关联
    roles = relationship('SysRole', secondary=role_permission, back_populates='permissions')


class SysMenu(Base):
    """系统菜单表"""
    __tablename__ = 'sys_menu'
    
    menu_id = Column(Integer, primary_key=True, autoincrement=True)
    menu_code = Column(String(50), unique=True, comment='菜单编码')
    menu_name = Column(String(50), nullable=False, comment='菜单名称')
    parent_id = Column(Integer, default=0, comment='父菜单ID')
    menu_type = Column(String(10), comment='菜单类型：directory/menu/button')
    path = Column(String(200), comment='路由路径')
    component = Column(String(200), comment='组件路径')
    icon = Column(String(50), comment='图标')
    sort_order = Column(Integer, default=0, comment='排序')
    is_visible = Column(Boolean, default=True, comment='是否显示')
    is_cache = Column(Boolean, default=True, comment='是否缓存')
    is_external = Column(Boolean, default=False, comment='是否外链')
    permission_code = Column(String(100), comment='权限标识')
    status = Column(String(10), default='正常')
    created_time = Column(DateTime, default=datetime.now)
    
    # 关联
    roles = relationship('SysRole', secondary=role_menu, back_populates='menus')


class SysDept(Base):
    """部门表"""
    __tablename__ = 'sys_dept'
    
    dept_id = Column(Integer, primary_key=True, autoincrement=True)
    dept_code = Column(String(50), comment='部门编码')
    dept_name = Column(String(50), nullable=False, comment='部门名称')
    parent_id = Column(Integer, default=0, comment='父部门ID')
    leader_id = Column(Integer, comment='部门负责人ID')
    sort_order = Column(Integer, default=0)
    status = Column(String(10), default='正常')
    is_deleted = Column(Boolean, default=False)
    created_time = Column(DateTime, default=datetime.now)
    
    # 关联
    users = relationship('SysUser', back_populates='dept')


class SysUserToken(Base):
    """用户Token表"""
    __tablename__ = 'sys_user_token'
    
    token_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('sys_user.user_id'), nullable=False)
    access_token = Column(String(500), nullable=False, comment='访问令牌')
    refresh_token = Column(String(500), comment='刷新令牌')
    token_type = Column(String(20), default='Bearer')
    device_type = Column(String(20), comment='设备类型：web/mobile/api')
    device_info = Column(String(200), comment='设备信息')
    ip_address = Column(String(50), comment='IP地址')
    expires_at = Column(DateTime, nullable=False, comment='过期时间')
    refresh_expires_at = Column(DateTime, comment='刷新令牌过期时间')
    is_revoked = Column(Boolean, default=False, comment='是否已撤销')
    created_time = Column(DateTime, default=datetime.now)
    
    # 关联
    user = relationship('SysUser', back_populates='tokens')


class SysLoginLog(Base):
    """登录日志表"""
    __tablename__ = 'sys_login_log'
    
    log_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('sys_user.user_id'))
    username = Column(String(50), comment='用户名')
    login_type = Column(String(20), comment='登录方式：password/wechat/sso')
    ip_address = Column(String(50), comment='IP地址')
    location = Column(String(100), comment='登录地点')
    browser = Column(String(50), comment='浏览器')
    os = Column(String(50), comment='操作系统')
    status = Column(String(10), comment='状态：成功/失败')
    message = Column(String(200), comment='消息')
    login_time = Column(DateTime, default=datetime.now)
    
    # 关联
    user = relationship('SysUser', back_populates='login_logs')


class SysOperationLog(Base):
    """操作日志表"""
    __tablename__ = 'sys_operation_log'
    
    log_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, comment='操作用户ID')
    username = Column(String(50), comment='用户名')
    module = Column(String(50), comment='模块')
    operation = Column(String(50), comment='操作类型')
    method = Column(String(10), comment='请求方法')
    request_url = Column(String(500), comment='请求URL')
    request_params = Column(Text, comment='请求参数')
    response_data = Column(Text, comment='响应数据')
    ip_address = Column(String(50), comment='IP地址')
    execution_time = Column(Integer, comment='执行时间(ms)')
    status = Column(String(10), comment='状态：成功/失败')
    error_message = Column(Text, comment='错误信息')
    created_time = Column(DateTime, default=datetime.now)
