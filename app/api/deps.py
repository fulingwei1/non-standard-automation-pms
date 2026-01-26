from typing import Generator

from fastapi import HTTPException, Request, status

from app.core import security
from app.models.base import get_db as get_db_session
from app.models.user import User


def get_db() -> Generator:
    """
    Get database session
    """
    yield from get_db_session()


def get_current_user_from_state(request: Request) -> User:
    """
    从 request.state 获取已验证的用户

    此函数用于从全局认证中间件已验证的用户信息中获取当前用户。
    中间件会将验证通过的用户存储在 request.state.user 中。

    Args:
        request: FastAPI Request对象

    Returns:
        User: 当前已认证的用户

    Raises:
        HTTPException: 如果用户未认证（401）

    使用示例：
        @router.get("/my-data")
        async def get_my_data(
            request: Request,
            current_user: User = Depends(get_current_user_from_state)
        ):
            # current_user已经被中间件验证过了
            pass
    """
    if not hasattr(request.state, "user"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户未认证，请先登录",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return request.state.user


# Re-export authentication dependencies
get_current_user = security.get_current_user
get_current_active_user = security.get_current_active_user
get_current_active_superuser = security.get_current_active_superuser
