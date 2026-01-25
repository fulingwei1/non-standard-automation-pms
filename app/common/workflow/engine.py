# -*- coding: utf-8 -*-
"""
Workflow Engine for handling status transitions and side effects.
"""

from typing import Any, Callable, Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# Handler type: (db_session, model_instance, from_status, to_status) -> None
WorkflowHandler = Callable[[Any, Any, Optional[str], str], Any]


class WorkflowEngine:
    """
    Registry for workflow status transition handlers.
    """

    def __init__(self):
        # {(model_name, to_status): [handlers]}
        self._handlers: Dict[Tuple[str, str], List[WorkflowHandler]] = {}
        # {(model_name, from_status, to_status): [handlers]}
        self._transition_handlers: Dict[
            Tuple[str, Optional[str], str], List[WorkflowHandler]
        ] = {}

    def register(
        self,
        model_name: str,
        to_status: str,
        handler: WorkflowHandler,
        from_status: Optional[str] = None,
    ):
        """
        Register a handler for a status transition.
        """
        if from_status:
            key = (model_name, from_status, to_status)
            if key not in self._transition_handlers:
                self._transition_handlers[key] = []
            self._transition_handlers[key].append(handler)
        else:
            key = (model_name, to_status)
            if key not in self._handlers:
                self._handlers[key] = []
            self._handlers[key].append(handler)

        logger.debug(
            f"Registered workflow handler for {model_name}: {from_status} -> {to_status}"
        )

    def trigger(
        self, db: Any, instance: Any, from_status: Optional[str], to_status: str
    ):
        """
        Trigger handlers for a status transition.
        """
        model_name = instance.__class__.__name__

        # 1. Trigger general status reached handlers
        handlers = self._handlers.get((model_name, to_status), [])
        for handler in handlers:
            try:
                handler(db, instance, from_status, to_status)
            except Exception as e:
                logger.error(
                    f"Error in workflow handler {handler.__name__} for {model_name} reaching {to_status}: {e}",
                    exc_info=True,
                )

        # 2. Trigger specific transition handlers
        if from_status:
            t_handlers = self._transition_handlers.get(
                (model_name, from_status, to_status), []
            )
            for handler in t_handlers:
                try:
                    handler(db, instance, from_status, to_status)
                except Exception as e:
                    logger.error(
                        f"Error in workflow handler {handler.__name__} for {model_name} transition {from_status}->{to_status}: {e}",
                        exc_info=True,
                    )


# Global engine instance
workflow_engine = WorkflowEngine()
