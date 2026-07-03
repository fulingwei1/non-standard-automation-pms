from typing import Any, Sequence

from fastapi import HTTPException


def reject_all_failed_submit(db: Any, successes: Sequence[Any], errors: Sequence[Any]) -> None:
    """Reject approval submit batches that produced no successful instance."""
    if successes or not errors:
        return

    rollback = getattr(db, "rollback", None)
    if callable(rollback):
        rollback()

    raise HTTPException(
        status_code=400,
        detail={
            "message": "审批提交失败",
            "errors": list(errors),
        },
    )
