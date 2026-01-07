#!/bin/bash
# 热点新闻爬虫 - 快速部署脚本

echo "=================================="
echo "热点新闻爬虫 - 快速部署"
echo "=================================="

# 1. 停止并删除旧容器
echo "1. 停止旧服务..."
docker-compose down

# 2. 重新构建镜像
echo "2. 构建Docker镜像..."
docker-compose build

# 3. 启动服务
echo "3. 启动服务..."
docker-compose up -d

# 4. 等待服务启动
echo "4. 等待服务启动..."
sleep 5

# 5. 检查服务状态
echo "5. 检查服务状态..."
docker-compose ps

# 6. 显示日志
echo ""
echo "=================================="
echo "部署完成！"
echo "=================================="
echo "Web服务: http://localhost:5000"
echo "MCP服务: 需要单独启动 (python3 mcp_server.py)"
echo ""
echo "查看日志: docker-compose logs -f"
echo "停止服务: docker-compose down"
echo "重启服务: docker-compose restart"
echo "=================================="
