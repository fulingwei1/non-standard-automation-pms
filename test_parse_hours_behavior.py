#!/usr/bin/env python3
"""Test ImportBase.parse_hours behavior"""

from app.services.unified_import.base import ImportBase

result = ImportBase.parse_hours("invalid")
print(f"Result: {result}")
print(f"Type: {type(result)}")
