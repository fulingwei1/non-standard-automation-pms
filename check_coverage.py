#!/usr/bin/env python3
"""独立运行覆盖率检查脚本，避免pytest配置干扰"""
import subprocess
import sys
import os

# 清理旧的coverage文件
os.system("python3 -m coverage erase")
os.system("find . -maxdepth 1 -name '.coverage*' -type f -delete 2>/dev/null || true")

# 运行coverage
cmd = [
    "python3", "-m", "coverage", "run",
    "--source=app/services/approval_engine/engine/actions",
    "--branch",
    "-m", "pytest",
    "tests/unit/test_actions_rewrite.py",
    "-v", "--no-header", "-p", "no:cacheprovider", "--tb=no"
]

print("运行测试并收集覆盖率...")
result = subprocess.run(cmd, capture_output=True, text=True)

if result.returncode != 0 and "passed" not in result.stdout:
    print("测试失败!")
    print(result.stdout)
    print(result.stderr)
    sys.exit(1)

# 生成覆盖率报告
print("\n生成覆盖率报告...")
report_cmd = [
    "python3", "-m", "coverage", "report",
    "--include=app/services/approval_engine/engine/actions.py"
]

report_result = subprocess.run(report_cmd, capture_output=True, text=True)
print(report_result.stdout)

if report_result.returncode != 0:
    print("生成报告失败:")
    print(report_result.stderr)
    sys.exit(1)

# 提取覆盖率百分比
lines = report_result.stdout.split('\n')
for line in lines:
    if 'actions.py' in line:
        parts = line.split()
        coverage_pct = parts[-1].rstrip('%')
        print(f"\n✅ actions.py 覆盖率: {coverage_pct}%")
        if float(coverage_pct) >= 70:
            print("✅ 达到目标覆盖率 70%+")
            sys.exit(0)
        else:
            print(f"❌ 未达到目标覆盖率 70% (当前: {coverage_pct}%)")
            sys.exit(1)

print("❌ 未能找到覆盖率信息")
sys.exit(1)
