#!/bin/bash
# 分批运行pytest收集覆盖率
cd ~/.openclaw/workspace/non-standard-automation-pms
source venv/bin/activate

# 清除旧覆盖率
coverage erase

# 分批运行，每批5个文件
batch_num=0
for f in tests/unit/test_*_auto.py; do
    batch_files="$batch_files $f"
    count=$((count + 1))
    
    if [ $count -ge 5 ]; then
        echo "=== Batch $batch_num ==="
        coverage run --append -m pytest $batch_files --tb=no -q 2>&1 | grep -E "passed|failed|error" | head -5 || true
        batch_num=$((batch_num + 1))
        count=0
        batch_files=""
    fi
done

# 最后一批
if [ -n "$batch_files" ]; then
    coverage run --append -m pytest $batch_files --tb=no -q 2>&1 | tail -5 || true
fi

echo "=== Coverage report ==="
coverage report 2>&1 | tail -5