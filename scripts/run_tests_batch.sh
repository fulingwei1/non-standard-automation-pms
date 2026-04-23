#!/bin/bash
# 分批运行pytest，每批10个文件
cd ~/.openclaw/workspace/non-standard-automation-pms
source venv/bin/activate

# 清除旧覆盖率
coverage erase

# 获取所有测试文件
files=$(find tests/unit -name "test_*_auto.py" | sort)

# 分批运行
batch=0
count=0
batch_files=""

for f in $files; do
    batch_files="$batch_files $f"
    count=$((count + 1))

    if [ $count -ge 10 ]; then
        echo "=== Batch $batch ==="
        python -m pytest $batch_files --cov=app --cov-append --tb=no -q --maxfail=5 2>&1 | tail -5 || true
        batch=$((batch + 1))
        count=0
        batch_files=""
    fi
done

# 最后一批
if [ -n "$batch_files" ]; then
    echo "=== Final batch ==="
    python -m pytest $batch_files --cov=app --cov-append --tb=no -q --maxfail=5 2>&1 | tail -5 || true
fi

echo "=== Final coverage ==="
coverage report 2>&1 | tail -5