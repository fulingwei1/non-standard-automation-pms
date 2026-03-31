# -*- coding: utf-8 -*-
"""
生产管理可配置参数
可通过环境变量覆盖默认值
"""
import os

# 工作时间配置
WORK_START_HOUR = int(os.getenv("PRODUCTION_WORK_START_HOUR", "8"))
WORK_END_HOUR = int(os.getenv("PRODUCTION_WORK_END_HOUR", "18"))
WORK_HOURS_PER_DAY = int(os.getenv("PRODUCTION_WORK_HOURS_PER_DAY", "8"))

# 瓶颈阈值配置
BOTTLENECK_LEVEL1_THRESHOLD = float(os.getenv("PRODUCTION_BOTTLENECK_L1", "0.90"))
BOTTLENECK_LEVEL2_THRESHOLD = float(os.getenv("PRODUCTION_BOTTLENECK_L2", "0.95"))
BOTTLENECK_LEVEL3_THRESHOLD = float(os.getenv("PRODUCTION_BOTTLENECK_L3", "0.98"))
