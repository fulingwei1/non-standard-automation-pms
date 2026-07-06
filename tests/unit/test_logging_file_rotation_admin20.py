# -*- coding: utf-8 -*-
"""
ADMIN-20 日志文件输出与轮转配置回归测试。
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from unittest.mock import patch


def test_setup_logging_writes_rotating_app_log(tmp_path, monkeypatch):
    """setup_logging 应同时配置 stdout 和可轮转的应用日志文件。"""
    log_dir = tmp_path / "logs"
    monkeypatch.setenv("APP_LOG_DIR", str(log_dir))
    monkeypatch.setenv("APP_LOG_FILE", "app.log")
    monkeypatch.setenv("APP_LOG_MAX_BYTES", "1024")
    monkeypatch.setenv("APP_LOG_BACKUP_COUNT", "7")

    with patch("app.core.logging_config.settings") as mock_settings:
        mock_settings.DEBUG = True

        from app.core.logging_config import get_logger, setup_logging

        setup_logging()

    root_logger = logging.getLogger()
    file_handlers = [
        handler
        for handler in root_logger.handlers
        if isinstance(handler, RotatingFileHandler)
    ]

    assert len(file_handlers) == 1
    file_handler = file_handlers[0]
    assert Path(file_handler.baseFilename) == log_dir / "app.log"
    assert file_handler.maxBytes == 1024
    assert file_handler.backupCount == 7

    get_logger("admin20").warning("ADMIN20_ROTATING_FILE_LOG")
    for handler in root_logger.handlers:
        handler.flush()

    log_file = log_dir / "app.log"
    assert log_file.exists()
    assert "ADMIN20_ROTATING_FILE_LOG" in log_file.read_text(encoding="utf-8")
