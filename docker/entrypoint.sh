#!/bin/bash
# 容器启动脚本

set -e

echo "=========================================="
echo "容器启动中..."
echo "=========================================="

# 清理旧数据库（每次启动都重新创建）
if [ -f "/app/data/hotnews.db" ]; then
    echo "清理旧数据库文件..."
    rm -f /app/data/hotnews.db
    echo "✓ 旧数据库已删除"
fi

# 确保必要的目录存在
mkdir -p /app/data /app/logs

echo "✓ 环境准备完成"
echo ""

# 执行传入的命令
exec "$@"
