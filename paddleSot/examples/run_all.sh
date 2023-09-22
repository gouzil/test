# 遍历目录下的所有 Python 文件
export PYTHONPATH=$PYTHONPATH:../
export STRICT_MODE=1
export MIN_GRAPH_SIZE=-1

for file in ./*.py; do
    # 检查文件是否为 Python 文件
    if [ -f "$file" ]; then
        if [[ -n "$GITHUB_ACTIONS" ]]; then
            echo ::group::example Running: LOG_LEVEL=3 PYTHONPATH=$PYTHONPATH " STRICT_MODE=1 python " $file
        else
            echo Running: LOG_LEVEL=3 PYTHONPATH=$PYTHONPATH " STRICT_MODE=1 python " $file
        fi
        # 执行文件
        python "$file"
        if [ $? -ne 0 ]; then
            echo "run $file failed"
            exit 1
        fi
        if [[ -n "$GITHUB_ACTIONS" ]]; then
            echo "::endgroup::"
        fi
    fi
done
