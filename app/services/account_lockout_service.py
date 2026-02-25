# -*- coding: utf-8 -*-
"""
账户锁定服务
用于防止暴力破解攻击的账户锁定机制
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List

from sqlalchemy.orm import Session

from app.models.login_attempt import LoginAttempt
from app.utils.redis_client import get_redis_client

logger = logging.getLogger(__name__)


class AccountLockoutService:
    """账户锁定服务"""
    
    # 配置常量
    LOCKOUT_THRESHOLD = 5  # 失败次数阈值
    LOCKOUT_DURATION_MINUTES = 15  # 锁定时长（分钟）
    ATTEMPT_WINDOW_MINUTES = 15  # 失败次数统计窗口（分钟）
    CAPTCHA_THRESHOLD = 3  # 需要验证码的失败次数阈值
    IP_BLACKLIST_THRESHOLD = 20  # IP黑名单阈值（15分钟内）
    
    @staticmethod
    def check_lockout(username: str, db: Session = None) -> Dict:
        """
        检查账户是否被锁定
        
        Args:
            username: 用户名
            db: 数据库会话（可选，用于降级）
            
        Returns:
            {
                "locked": bool,  # 是否锁定
                "locked_until": str,  # 锁定到何时（ISO格式）
                "remaining_attempts": int,  # 剩余尝试次数
                "requires_captcha": bool,  # 是否需要验证码
                "message": str  # 提示消息
            }
        """
        redis = get_redis_client()
        
        # 检查锁定状态
        if redis:
            locked_until_str = redis.get(f"lockout:{username}")
            if locked_until_str:
                try:
                    locked_until = datetime.fromisoformat(locked_until_str)
                    return {
                        "locked": True,
                        "locked_until": locked_until_str,
                        "remaining_attempts": 0,
                        "requires_captcha": False,
                        "message": f"账户已锁定，请在{locked_until.strftime('%H:%M')}后重试"
                    }
                except Exception as e:
                    logger.error(f"解析锁定时间失败: {e}")
        
        # 检查失败次数
        attempts = AccountLockoutService._get_attempt_count(username, redis, db)
        remaining = max(0, AccountLockoutService.LOCKOUT_THRESHOLD - attempts)
        requires_captcha = attempts >= AccountLockoutService.CAPTCHA_THRESHOLD
        
        return {
            "locked": False,
            "locked_until": None,
            "remaining_attempts": remaining,
            "requires_captcha": requires_captcha,
            "message": f"剩余尝试次数: {remaining}" if attempts > 0 else ""
        }
    
    @staticmethod
    def _get_attempt_count(username: str, redis, db: Session = None) -> int:
        """获取登录失败次数"""
        if redis:
            try:
                attempts = redis.get(f"login_attempts:{username}")
                return int(attempts) if attempts else 0
            except Exception as e:
                logger.warning(f"从Redis获取失败次数失败: {e}")
        
        # 降级到数据库
        if db:
            try:
                cutoff_time = datetime.now() - timedelta(minutes=AccountLockoutService.ATTEMPT_WINDOW_MINUTES)
                count = db.query(LoginAttempt).filter(
                    LoginAttempt.username == username,
                    LoginAttempt.success == False,
                    LoginAttempt.created_at >= cutoff_time
                ).count()
                return count
            except Exception as e:
                logger.error(f"从数据库获取失败次数失败: {e}")
        
        return 0
    
    @staticmethod
    def record_failed_login(
        username: str,
        ip: str,
        user_agent: str = None,
        reason: str = "wrong_password",
        db: Session = None
    ) -> Dict:
        """
        记录登录失败
        
        Args:
            username: 用户名
            ip: IP地址
            user_agent: 用户代理
            reason: 失败原因
            db: 数据库会话
            
        Returns:
            {
                "attempts": int,  # 当前失败次数
                "locked": bool,  # 是否已锁定
                "locked_until": str,  # 锁定到何时
                "ip_blacklisted": bool  # IP是否被拉黑
            }
        """
        redis = get_redis_client()
        attempts = 0
        locked = False
        locked_until = None
        ip_blacklisted = False
        
        # 记录到Redis
        if redis:
            try:
                # 增加失败次数
                attempt_key = f"login_attempts:{username}"
                attempts = redis.incr(attempt_key)
                redis.expire(attempt_key, AccountLockoutService.ATTEMPT_WINDOW_MINUTES * 60)
                
                # 达到阈值，锁定账户
                if attempts >= AccountLockoutService.LOCKOUT_THRESHOLD:
                    locked = True
                    locked_until = datetime.now() + timedelta(minutes=AccountLockoutService.LOCKOUT_DURATION_MINUTES)
                    lockout_key = f"lockout:{username}"
                    redis.setex(
                        lockout_key,
                        AccountLockoutService.LOCKOUT_DURATION_MINUTES * 60,
                        locked_until.isoformat()
                    )
                    logger.warning(f"账户已锁定: {username}, IP: {ip}, 失败次数: {attempts}")
                
                # 检查IP是否需要拉黑
                ip_blacklisted = AccountLockoutService._check_ip_blacklist(ip, redis)
                
            except Exception as e:
                logger.error(f"Redis记录失败: {e}")
        
        # 持久化到数据库（异步，不影响主流程）
        if db:
            try:
                login_attempt = LoginAttempt(
                    username=username,
                    ip_address=ip,
                    user_agent=user_agent,
                    success=False,
                    failure_reason=reason,
                    locked=locked
                )
                db.add(login_attempt)
                db.commit()
            except Exception as e:
                logger.error(f"记录登录失败到数据库失败: {e}")
                db.rollback()
        
        return {
            "attempts": attempts,
            "locked": locked,
            "locked_until": locked_until.isoformat() if locked_until else None,
            "ip_blacklisted": ip_blacklisted
        }
    
    @staticmethod
    def _check_ip_blacklist(ip: str, redis) -> bool:
        """检查IP是否需要拉黑"""
        try:
            ip_attempt_key = f"ip_attempts:{ip}"
            ip_attempts = redis.incr(ip_attempt_key)
            redis.expire(ip_attempt_key, AccountLockoutService.ATTEMPT_WINDOW_MINUTES * 60)
            
            if ip_attempts >= AccountLockoutService.IP_BLACKLIST_THRESHOLD:
                # 永久拉黑
                blacklist_key = f"ip_blacklist:{ip}"
                redis.set(blacklist_key, "1")
                logger.critical(f"IP已被拉黑: {ip}, 失败次数: {ip_attempts}")
                return True
        except Exception as e:
            logger.error(f"检查IP黑名单失败: {e}")
        
        return False
    
    @staticmethod
    def is_ip_blacklisted(ip: str) -> bool:
        """检查IP是否在黑名单中"""
        redis = get_redis_client()
        if redis:
            try:
                return redis.exists(f"ip_blacklist:{ip}") > 0
            except Exception as e:
                logger.error(f"检查IP黑名单失败: {e}")
        return False
    
    @staticmethod
    def record_successful_login(username: str, ip: str, user_agent: str = None, db: Session = None):
        """
        记录成功登录，重置失败次数
        
        Args:
            username: 用户名
            ip: IP地址
            user_agent: 用户代理
            db: 数据库会话
        """
        redis = get_redis_client()
        
        # 清除Redis中的失败记录
        if redis:
            try:
                redis.delete(f"login_attempts:{username}")
                redis.delete(f"lockout:{username}")
            except Exception as e:
                logger.error(f"清除失败记录失败: {e}")
        
        # 记录到数据库
        if db:
            try:
                login_attempt = LoginAttempt(
                    username=username,
                    ip_address=ip,
                    user_agent=user_agent,
                    success=True,
                    failure_reason=None,
                    locked=False
                )
                db.add(login_attempt)
                db.commit()
            except Exception as e:
                logger.error(f"记录成功登录到数据库失败: {e}")
                db.rollback()
    
    @staticmethod
    def unlock_account(username: str, admin_user: str = None, db: Session = None) -> bool:
        """
        手动解锁账户（管理员功能）
        
        Args:
            username: 要解锁的用户名
            admin_user: 执行解锁的管理员
            db: 数据库会话
            
        Returns:
            是否成功解锁
        """
        redis = get_redis_client()
        
        if redis:
            try:
                redis.delete(f"login_attempts:{username}")
                redis.delete(f"lockout:{username}")
                logger.info(f"管理员 {admin_user} 解锁账户: {username}")
                return True
            except Exception as e:
                logger.error(f"解锁账户失败: {e}")
                return False
        
        return False
    
    @staticmethod
    def get_locked_accounts(db: Session) -> List[Dict]:
        """
        获取所有被锁定的账户列表
        
        Returns:
            [
                {
                    "username": str,
                    "locked_until": str,
                    "attempts": int
                }
            ]
        """
        redis = get_redis_client()
        locked_accounts = []
        
        if redis:
            try:
                # 扫描所有锁定键
                for key in redis.scan_iter("lockout:*"):
                    username = key.split(":", 1)[1]
                    locked_until = redis.get(key)
                    attempts_key = f"login_attempts:{username}"
                    attempts = redis.get(attempts_key)
                    
                    locked_accounts.append({
                        "username": username,
                        "locked_until": locked_until,
                        "attempts": int(attempts) if attempts else 0
                    })
            except Exception as e:
                logger.error(f"获取锁定账户列表失败: {e}")
        
        return locked_accounts
    
    @staticmethod
    def get_login_history(username: str, limit: int = 50, db: Session = None) -> List[Dict]:
        """
        获取登录历史记录
        
        Args:
            username: 用户名
            limit: 返回记录数
            db: 数据库会话
            
        Returns:
            登录历史列表
        """
        if not db:
            return []
        
        try:
            attempts = db.query(LoginAttempt).filter(
                LoginAttempt.username == username
            ).order_by(
                LoginAttempt.created_at.desc()
            ).limit(limit).all()
            
            return [
                {
                    "id": attempt.id,
                    "username": attempt.username,
                    "ip_address": attempt.ip_address,
                    "user_agent": attempt.user_agent,
                    "success": attempt.success,
                    "failure_reason": attempt.failure_reason,
                    "locked": attempt.locked,
                    "created_at": attempt.created_at.isoformat() if attempt.created_at else None
                }
                for attempt in attempts
            ]
        except Exception as e:
            logger.error(f"获取登录历史失败: {e}")
            return []
    
    @staticmethod
    def remove_ip_from_blacklist(ip: str, admin_user: str = None) -> bool:
        """
        从黑名单中移除IP（管理员功能）
        
        Args:
            ip: IP地址
            admin_user: 执行操作的管理员
            
        Returns:
            是否成功
        """
        redis = get_redis_client()
        
        if redis:
            try:
                redis.delete(f"ip_blacklist:{ip}")
                redis.delete(f"ip_attempts:{ip}")
                logger.info(f"管理员 {admin_user} 从黑名单移除IP: {ip}")
                return True
            except Exception as e:
                logger.error(f"移除IP黑名单失败: {e}")
                return False
        
        return False
    
    @staticmethod
    def get_blacklisted_ips() -> List[Dict]:
        """
        获取所有黑名单IP
        
        Returns:
            [{"ip": str, "created_at": str}]
        """
        redis = get_redis_client()
        blacklisted_ips = []
        
        if redis:
            try:
                for key in redis.scan_iter("ip_blacklist:*"):
                    ip = key.split(":", 1)[1]
                    blacklisted_ips.append({
                        "ip": ip,
                        "created_at": None  # Redis不存储时间戳
                    })
            except Exception as e:
                logger.error(f"获取IP黑名单失败: {e}")
        
        return blacklisted_ips
