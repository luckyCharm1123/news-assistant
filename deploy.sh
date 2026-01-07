#!/bin/bash
# 热点新闻爬虫 - 快速部署脚本（一键启动所有服务）

echo "=================================="
echo "热点新闻爬虫 - 快速部署"
echo "=================================="

# 1. 检查.env文件
if [ ! -f .env ]; then
    echo "⚠️  警告: .env文件不存在，正在从.env.example创建..."
    cp .env.example .env
    echo "✓ 已创建.env文件，请修改API_KEY为强密码！"
    echo ""
fi

# 2. 停止并删除旧容器
echo "1. 停止旧服务..."
docker-compose down

# 3. 重新构建镜像
echo "2. 构建Docker镜像..."
docker-compose build --no-cache

# 4. 启动所有服务（Web + MCP）
echo "3. 启动所有服务（Web服务 + MCP服务）..."
docker-compose up -d

# 5. 等待服务启动
echo "4. 等待服务启动..."
sleep 8

# 6. 检查服务状态
echo "5. 检查服务状态..."
docker-compose ps

# 7. 测试服务
echo ""
echo "6. 测试服务连接..."
echo -n "  Web服务 (http://localhost:5000/health): "
if curl -s http://localhost:5000/health > /dev/null; then
    echo "✓ 运行正常"
else
    echo "✗ 连接失败"
fi

echo -n "  MCP服务 (http://localhost:3001/health): "
if curl -s http://localhost:3001/health > /dev/null; then
    echo "✓ 运行正常"
else
    echo "✗ 连接失败"
fi

# 8. 显示访问信息
echo ""
echo "=================================="
echo "✓ 部署完成！"
echo "=================================="
echo "📊 Web服务: http://localhost:5000"
echo "🔧 MCP服务: http://localhost:3001"
echo ""
echo "📖 API文档: 见 API_AUTH.md 和 MCP_README.md"
echo ""
echo "常用命令:"
echo "  查看日志: docker-compose logs -f"
echo "  查看状态: docker-compose ps"
echo "  停止服务: docker-compose down"
echo "  重启服务: docker-compose restart"
echo "  查看MCP日志: docker-compose logs -f mcp-server"
echo "=================================="
