# -*- coding: utf-8 -*-
"""
会话管理服务
负责用户会话的创建、查询、管理和安全控制
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

try:
    from user_agents import parse as parse_user_agent
except ImportError:
    # Fallback if user-agents not installed
    def parse_user_agent(ua_string):
        return type('UserAgent', (), {'browser': type('Browser', (), {'family': 'Unknown', 'version_string': ''})(), 'os': type('OS', (), {'family': 'Unknown', 'version_string': ''})(), 'device': type('Device', (), {'family': 'Unknown'})()})()

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.models.session import UserSession

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)


class SessionService:
    """会话管理服务类"""
    
    # Redis键前缀
    SESSION_KEY_PREFIX = "session:"
    BLACKLIST_KEY_PREFIX = "jwt:blacklist:"
    LOCATION_CACHE_PREFIX = "ip:location:"
    
    # 配置
    ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24小时
    REFRESH_TOKEN_EXPIRE_DAYS = 7  # 7天
    SESSION_EXPIRE_DAYS = 7  # 会话7天过期
    MAX_SESSIONS_PER_USER = 5  # 每个用户最多5个活跃会话
    
    # 风险评分阈值
    RISK_SCORE_THRESHOLD = 50
    
    @classmethod
    def create_session(
        cls,
        db: Session,
        user_id: int,
        access_token_jti: str,
        refresh_token_jti: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        device_info: Optional[Dict] = None,
    ) -> UserSession:
        """
        创建新会话
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            access_token_jti: Access Token的JTI
            refresh_token_jti: Refresh Token的JTI
            ip_address: 登录IP地址
            user_agent: User-Agent字符串
            device_info: 设备信息字典
        
        Returns:
            创建的会话对象
        """
        now = datetime.utcnow()
        
        # 解析User-Agent
        browser_info = cls._parse_user_agent(user_agent) if user_agent else {}
        
        # 获取地理位置
        location = cls._get_location(ip_address) if ip_address else None
        
        # 检测是否为可疑登录
        is_suspicious, risk_score = cls._assess_risk(
            db, user_id, ip_address, device_info, location
        )
        
        # 创建会话对象
        session = UserSession(
            user_id=user_id,
            access_token_jti=access_token_jti,
            refresh_token_jti=refresh_token_jti,
            device_id=device_info.get("device_id") if device_info else None,
            device_name=device_info.get("device_name") if device_info else None,
            device_type=device_info.get("device_type", "desktop") if device_info else "desktop",
            ip_address=ip_address,
            location=location,
            user_agent=user_agent,
            browser=browser_info.get("browser"),
            os=browser_info.get("os"),
            is_active=True,
            login_at=now,
            last_activity_at=now,
            expires_at=now + timedelta(days=cls.SESSION_EXPIRE_DAYS),
            is_suspicious=is_suspicious,
            risk_score=risk_score,
        )
        
        db.add(session)
        
        # 清理旧会话（保留最近的MAX_SESSIONS_PER_USER个）
        cls._cleanup_old_sessions(db, user_id)
        
        db.commit()
        db.refresh(session)
        
        # 缓存到Redis
        cls._cache_session(session)
        
        logger.info(
            f"创建会话成功: user_id={user_id}, session_id={session.id}, "
            f"ip={ip_address}, suspicious={is_suspicious}, risk={risk_score}"
        )
        
        return session
    
    @classmethod
    def get_user_sessions(
        cls,
        db: Session,
        user_id: int,
        active_only: bool = True,
        current_jti: Optional[str] = None,
    ) -> List[UserSession]:
        """
        获取用户的所有会话
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            active_only: 是否只返回活跃会话
            current_jti: 当前会话的JTI（用于标记当前会话）
        
        Returns:
            会话列表
        """
        query = db.query(UserSession).filter(UserSession.user_id == user_id)
        
        if active_only:
            query = query.filter(UserSession.is_active == True)
        
        sessions = query.order_by(UserSession.last_activity_at.desc()).all()
        
        # 标记当前会话
        if current_jti:
            for session in sessions:
                session.is_current = (session.access_token_jti == current_jti)
        
        return sessions
    
    @classmethod
    def get_session_by_jti(
        cls,
        db: Session,
        jti: str,
        token_type: str = "access",
    ) -> Optional[UserSession]:
        """
        根据JTI获取会话
        
        Args:
            db: 数据库会话
            jti: JWT ID
            token_type: token类型，'access'或'refresh'
        
        Returns:
            会话对象或None
        """
        if token_type == "access":
            return db.query(UserSession).filter(
                UserSession.access_token_jti == jti
            ).first()
        else:
            return db.query(UserSession).filter(
                UserSession.refresh_token_jti == jti
            ).first()
    
    @classmethod
    def update_session_activity(
        cls,
        db: Session,
        jti: str,
        new_access_jti: Optional[str] = None,
    ) -> Optional[UserSession]:
        """
        更新会话活动时间
        
        Args:
            db: 数据库会话
            jti: 当前的JWT ID
            new_access_jti: 新的Access Token JTI（刷新token时使用）
        
        Returns:
            更新后的会话对象或None
        """
        session = cls.get_session_by_jti(db, jti, token_type="refresh")
        
        if not session:
            session = cls.get_session_by_jti(db, jti, token_type="access")
        
        if session:
            session.last_activity_at = datetime.utcnow()
            
            if new_access_jti:
                # 刷新token时，更新access_token_jti
                session.access_token_jti = new_access_jti
            
            db.commit()
            db.refresh(session)
            
            # 更新Redis缓存
            cls._cache_session(session)
        
        return session
    
    @classmethod
    def revoke_session(
        cls,
        db: Session,
        session_id: int,
        user_id: int,
    ) -> bool:
        """
        撤销会话（强制下线）
        
        Args:
            db: 数据库会话
            session_id: 要撤销的会话ID
            user_id: 用户ID（用于权限验证）
        
        Returns:
            是否成功撤销
        """
        session = db.query(UserSession).filter(
            and_(
                UserSession.id == session_id,
                UserSession.user_id == user_id,
            )
        ).first()
        
        if not session:
            return False
        
        # 标记会话为非活跃
        session.is_active = False
        session.logout_at = datetime.utcnow()
        db.commit()
        
        # 将tokens加入黑名单
        cls._add_to_blacklist(
            session.access_token_jti,
            cls.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        cls._add_to_blacklist(
            session.refresh_token_jti,
            cls.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600
        )
        
        # 从Redis删除会话缓存
        cls._remove_session_cache(session.id)
        
        logger.info(f"撤销会话成功: session_id={session_id}, user_id={user_id}")
        return True
    
    @classmethod
    def revoke_all_sessions(
        cls,
        db: Session,
        user_id: int,
        except_jti: Optional[str] = None,
    ) -> int:
        """
        撤销用户的所有会话
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            except_jti: 要排除的JTI（通常是当前会话）
        
        Returns:
            撤销的会话数量
        """
        query = db.query(UserSession).filter(
            and_(
                UserSession.user_id == user_id,
                UserSession.is_active == True,
            )
        )
        
        if except_jti:
            query = query.filter(
                and_(
                    UserSession.access_token_jti != except_jti,
                    UserSession.refresh_token_jti != except_jti,
                )
            )
        
        sessions = query.all()
        count = 0
        
        for session in sessions:
            session.is_active = False
            session.logout_at = datetime.utcnow()
            
            # 加入黑名单
            cls._add_to_blacklist(
                session.access_token_jti,
                cls.ACCESS_TOKEN_EXPIRE_MINUTES * 60
            )
            cls._add_to_blacklist(
                session.refresh_token_jti,
                cls.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600
            )
            
            # 删除缓存
            cls._remove_session_cache(session.id)
            count += 1
        
        db.commit()
        
        logger.info(f"撤销所有会话: user_id={user_id}, count={count}")
        return count
    
    @classmethod
    def cleanup_expired_sessions(cls, db: Session) -> int:
        """
        清理过期会话（定时任务）
        
        Args:
            db: 数据库会话
        
        Returns:
            清理的会话数量
        """
        now = datetime.utcnow()
        
        expired_sessions = db.query(UserSession).filter(
            and_(
                UserSession.is_active == True,
                UserSession.expires_at < now,
            )
        ).all()
        
        count = 0
        for session in expired_sessions:
            session.is_active = False
            session.logout_at = now
            cls._remove_session_cache(session.id)
            count += 1
        
        db.commit()
        
        logger.info(f"清理过期会话: count={count}")
        return count
    
    # ========================================================================
    # 私有辅助方法
    # ========================================================================
    
    @classmethod
    def _parse_user_agent(cls, user_agent: str) -> Dict:
        """解析User-Agent字符串"""
        try:
            ua = parse_user_agent(user_agent)
            return {
                "browser": f"{ua.browser.family} {ua.browser.version_string}",
                "os": f"{ua.os.family} {ua.os.version_string}",
                "device": ua.device.family,
            }
        except Exception as e:
            logger.warning(f"解析User-Agent失败: {e}")
            return {}
    
    @classmethod
    def _get_location(cls, ip_address: str) -> Optional[str]:
        """
        获取IP地址的地理位置
        
        简化版本：从Redis缓存读取，实际应调用IP地理位置API
        """
        if not ip_address:
            return None
        
        try:
            from app.utils.redis_client import get_redis_client
            redis_client = get_redis_client()
        except Exception:
            redis_client = None
        if redis_client:
            cache_key = f"{cls.LOCATION_CACHE_PREFIX}{ip_address}"
            try:
                location = redis_client.get(cache_key)
                if location:
                    return location
            except Exception as e:
                logger.warning(f"读取位置缓存失败: {e}")
        
        # TODO: 调用IP地理位置API（如GeoIP2）
        # 这里返回简单的示例
        return "未知位置"
    
    @classmethod
    def _assess_risk(
        cls,
        db: Session,
        user_id: int,
        ip_address: Optional[str],
        device_info: Optional[Dict],
        location: Optional[str],
    ) -> Tuple[bool, int]:
        """
        评估登录风险
        
        Returns:
            (is_suspicious, risk_score)
        """
        risk_score = 0
        
        # 获取用户最近的会话
        recent_sessions = db.query(UserSession).filter(
            and_(
                UserSession.user_id == user_id,
                UserSession.login_at > datetime.utcnow() - timedelta(days=30),
            )
        ).order_by(UserSession.login_at.desc()).limit(10).all()
        
        if not recent_sessions:
            # 新用户，无历史记录
            return False, 0
        
        # 检查IP地址是否异常
        if ip_address:
            known_ips = {s.ip_address for s in recent_sessions if s.ip_address}
            if ip_address not in known_ips:
                risk_score += 30
                logger.info(f"检测到新IP登录: user_id={user_id}, ip={ip_address}")
        
        # 检查设备是否异常
        if device_info and device_info.get("device_id"):
            known_devices = {
                s.device_id for s in recent_sessions if s.device_id
            }
            if device_info["device_id"] not in known_devices:
                risk_score += 20
                logger.info(
                    f"检测到新设备登录: user_id={user_id}, "
                    f"device={device_info.get('device_name')}"
                )
        
        # 检查地理位置是否异常
        if location:
            known_locations = {s.location for s in recent_sessions if s.location}
            if location not in known_locations and "未知" not in location:
                risk_score += 25
                logger.info(f"检测到异地登录: user_id={user_id}, location={location}")
        
        # 检查登录频率（防止暴力破解）
        recent_logins = [
            s for s in recent_sessions
            if s.login_at > datetime.utcnow() - timedelta(hours=1)
        ]
        if len(recent_logins) > 5:
            risk_score += 25
            logger.warning(f"检测到频繁登录: user_id={user_id}, count={len(recent_logins)}")
        
        is_suspicious = risk_score >= cls.RISK_SCORE_THRESHOLD
        
        return is_suspicious, min(risk_score, 100)
    
    @classmethod
    def _cleanup_old_sessions(cls, db: Session, user_id: int):
        """清理旧会话，保留最近的几个"""
        # 获取所有活跃会话
        active_sessions = db.query(UserSession).filter(
            and_(
                UserSession.user_id == user_id,
                UserSession.is_active == True,
            )
        ).order_by(UserSession.last_activity_at.desc()).all()
        
        # 如果超过限制，关闭最旧的会话
        if len(active_sessions) >= cls.MAX_SESSIONS_PER_USER:
            sessions_to_revoke = active_sessions[cls.MAX_SESSIONS_PER_USER - 1:]
            for session in sessions_to_revoke:
                session.is_active = False
                session.logout_at = datetime.utcnow()
                cls._add_to_blacklist(
                    session.access_token_jti,
                    cls.ACCESS_TOKEN_EXPIRE_MINUTES * 60
                )
                cls._add_to_blacklist(
                    session.refresh_token_jti,
                    cls.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600
                )
                logger.info(f"自动关闭旧会话: session_id={session.id}")
    
    @classmethod
    def _cache_session(cls, session: UserSession):
        """缓存会话到Redis"""
        try:
            from app.utils.redis_client import get_redis_client
            redis_client = get_redis_client()
        except Exception:
            redis_client = None
        if not redis_client:
            return
        
        try:
            key = f"{cls.SESSION_KEY_PREFIX}{session.id}"
            # 简化缓存，只存储必要信息
            data = {
                "user_id": session.user_id,
                "is_active": int(session.is_active),
                "access_jti": session.access_token_jti,
                "refresh_jti": session.refresh_token_jti,
            }
            redis_client.hmset(key, data)
            redis_client.expire(key, cls.SESSION_EXPIRE_DAYS * 24 * 3600)
        except Exception as e:
            logger.warning(f"缓存会话失败: {e}")
    
    @classmethod
    def _remove_session_cache(cls, session_id: int):
        """从Redis删除会话缓存"""
        try:
            from app.utils.redis_client import get_redis_client
            redis_client = get_redis_client()
        except Exception:
            redis_client = None
        if not redis_client:
            return
        
        try:
            key = f"{cls.SESSION_KEY_PREFIX}{session_id}"
            redis_client.delete(key)
        except Exception as e:
            logger.warning(f"删除会话缓存失败: {e}")
    
    @classmethod
    def _add_to_blacklist(cls, jti: str, ttl: int):
        """将JTI加入黑名单"""
        try:
            from app.utils.redis_client import get_redis_client
            redis_client = get_redis_client()
        except Exception:
            redis_client = None
        if not redis_client:
            logger.warning("Redis不可用，无法加入黑名单")
            return
        
        try:
            key = f"{cls.BLACKLIST_KEY_PREFIX}{jti}"
            redis_client.setex(key, ttl, "1")
        except Exception as e:
            logger.warning(f"加入黑名单失败: {e}")


# 便捷函数导出
get_user_sessions = SessionService.get_user_sessions
create_session = SessionService.create_session
revoke_session = SessionService.revoke_session
update_session_activity = SessionService.update_session_activity
