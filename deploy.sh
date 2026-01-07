#!/bin/bash
# 热点新闻爬虫 - 快速部署脚本（一键启动所有服务）

echo "=================================="
echo "热点新闻爬虫 - 快速部署"
echo "=================================="

# 检测 docker-compose 命令（兼容 V1 和 V2）
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
elif docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    echo "❌ 错误: 未找到 docker-compose"
    echo ""
    echo "请先安装 Docker Compose："
    echo ""
    echo "方法1 - 安装 docker-compose V1："
    echo "  sudo curl -L \"https://github.com/docker/compose/releases/latest/download/docker-compose-\$(uname -s)-\$(uname -m)\" -o /usr/local/bin/docker-compose"
    echo "  sudo chmod +x /usr/local/bin/docker-compose"
    echo ""
    echo "方法2 - 使用 Docker Compose V2（Docker 自带）："
    echo "  sudo apt-get update"
    echo "  sudo apt-get install docker-compose-plugin"
    echo ""
    exit 1
fi

echo "✓ 检测到 Docker Compose: $DOCKER_COMPOSE"
echo ""

# 1. 检查.env文件
if [ ! -f .env ]; then
    echo "⚠️  警告: .env文件不存在，正在从.env.example创建..."
    cp .env.example .env
    echo "✓ 已创建.env文件，请修改API_KEY为强密码！"
    echo ""
fi

# 2. 停止并删除旧容器
echo "1. 停止旧服务..."
$DOCKER_COMPOSE down

# 3. 重新构建镜像
echo "2. 构建Docker镜像..."
$DOCKER_COMPOSE build --no-cache

# 4. 启动所有服务（Web + MCP）
echo "3. 启动所有服务（Web服务 + MCP服务）..."
$DOCKER_COMPOSE up -d

# 5. 等待服务启动
echo "4. 等待服务启动..."
sleep 8

# 6. 检查服务状态
echo "5. 检查服务状态..."
$DOCKER_COMPOSE ps

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
echo "  查看日志: $DOCKER_COMPOSE logs -f"
echo "  查看状态: $DOCKER_COMPOSE ps"
echo "  停止服务: $DOCKER_COMPOSE down"
echo "  重启服务: $DOCKER_COMPOSE restart"
echo "  查看MCP日志: $DOCKER_COMPOSE logs -f mcp-server"
echo "=================================="
