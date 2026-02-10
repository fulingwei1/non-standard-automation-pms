"""Diagnostic: check in-memory SQLite + NullPool behavior"""
import sys
from unittest.mock import MagicMock
sys.modules['redis'] = MagicMock()
sys.modules['redis.exceptions'] = MagicMock()

import os
os.environ['SQLITE_DB_PATH'] = ':memory:'
os.environ['REDIS_URL'] = ''
os.environ.setdefault('ENABLE_SCHEDULER', 'false')

from app.models.base import Base, get_engine
from sqlalchemy import inspect

engine = get_engine()
print('Pool class:', type(engine.pool).__name__)

# create_all uses its own connection internally
Base.metadata.create_all(bind=engine)

# Check with a fresh connection
insp = inspect(engine)
tables = insp.get_table_names()
print(f'Tables visible after create_all: {len(tables)}')
print('Has api_permissions:', 'api_permissions' in tables)
print('Has users:', 'users' in tables)

# Also try StaticPool approach
from sqlalchemy import create_engine, event
from sqlalchemy.pool import StaticPool

engine2 = create_engine(
 "sqlite:///:memory:",
 connect_args={"check_same_thread": False},
  poolclass=StaticPool,
)

@event.listens_for(engine2, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
 cursor = dbapi_connection.cursor()
 cursor.execute("PRAGMA foreign_keys=ON")
 cursor.close()

Base.metadata.create_all(bind=engine2)
insp2 = inspect(engine2)
tables2 = insp2.get_table_names()
print('\nWith StaticPool:')
print(f'Tables visible: {len(tables2)}')
print('Has api_permissions:', 'api_permissions' in tables2)
print('Has users:', 'users' in tables2)
