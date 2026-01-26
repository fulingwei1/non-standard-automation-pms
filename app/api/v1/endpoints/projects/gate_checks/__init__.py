# -*- coding: utf-8 -*-
"""
项目阶段门检查模块统一导出

模块结构:
 ├── gate_s1_s2.py  # S1→S2 阶段门检查
 ├── gate_s2_s3.py  # S2→S3 阶段门检查
 ├── gate_s3_s4.py  # S3→S4 阶段门检查
 ├── gate_s4_s5.py  # S4→S5 阶段门检查
 ├── gate_s5_s6.py  # S5→S6 阶段门检查
 ├── gate_s6_s7.py  # S6→S7 阶段门检查
 ├── gate_s7_s8.py  # S7→S8 阶段门检查
 ├── gate_s8_s9.py  # S8→S9 阶段门检查
 └── gate_common.py # 通用门检查函数
"""

from .gate_common import (
    check_gate,
    check_gate_detailed,
)
from .gate_s1_s2 import (
    check_gate_s1_to_s2,
)
from .gate_s2_s3 import (
    check_gate_s2_to_s3,
)
from .gate_s3_s4 import (
    check_gate_s3_to_s4,
)
from .gate_s4_s5 import (
    check_gate_s4_to_s5,
)
from .gate_s5_s6 import (
    check_gate_s5_to_s6,
)
from .gate_s6_s7 import (
    check_gate_s6_to_s7,
)
from .gate_s7_s8 import (
    check_gate_s7_to_s8,
)
from .gate_s8_s9 import (
    check_gate_s8_to_s9,
)

__all__ = [
    "check_gate_s1_to_s2",
    "check_gate_s2_to_s3",
    "check_gate_s3_to_s4",
    "check_gate_s4_to_s5",
    "check_gate_s5_to_s6",
    "check_gate_s6_to_s7",
    "check_gate_s7_to_s8",
    "check_gate_s8_to_s9",
    "check_gate",
    "check_gate_detailed",
]
