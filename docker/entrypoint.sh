#!/bin/bash
# 容器启动脚本

set -e

echo "=========================================="
echo "容器启动中..."
echo "=========================================="

# 确保必要的目录存在
mkdir -p /app/data /app/logs

# 仅在开发模式下清理数据库（通过环境变量控制）
if [ "$CLEAR_DB_ON_START" = "true" ] && [ -f "/app/data/hotnews.db" ]; then
    echo "清理旧数据库文件..."
    rm -f /app/data/hotnews.db
    echo "✓ 旧数据库已删除"
fi

echo "✓ 环境准备完成"
echo ""

# 执行传入的命令
exec "$@"
