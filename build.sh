#!/bin/bash
# Docker 构建脚本 - 使用 BuildKit 和 uv 优化构建速度

set -e

echo "=========================================="
echo "HotNews Crawler - Docker 构建脚本"
echo "=========================================="
echo ""

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查 Docker 版本
echo -e "${YELLOW}检查 Docker 版本...${NC}"
docker --version
docker compose version

# 确保 BuildKit 已启用
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

echo ""
echo -e "${GREEN}✓ BuildKit 已启用${NC}"
echo ""

# 解析命令行参数
COMMAND=${1:-"build"}

case "$COMMAND" in
  build)
    echo -e "${YELLOW}开始构建镜像...${NC}"
    echo ""
    docker compose build --parallel
    echo ""
    echo -e "${GREEN}✓ 构建完成!${NC}"
    echo ""
    echo "提示："
    echo "  - 首次构建可能需要几分钟（下载依赖）"
    echo "  - 后续构建将利用缓存，速度极快"
    echo "  - 使用 './build.sh push' 推送镜像到仓库"
    ;;

  build-no-cache)
    echo -e "${YELLOW}开始构建镜像（无缓存）...${NC}"
    echo ""
    docker compose build --no-cache --parallel
    echo ""
    echo -e "${GREEN}✓ 构建完成!${NC}"
    ;;

  up)
    echo -e "${YELLOW}构建并启动服务...${NC}"
    echo ""
    docker compose up -d --build
    echo ""
    echo -e "${GREEN}✓ 服务已启动!${NC}"
    echo ""
    echo "查看日志: docker compose logs -f"
    echo "查看状态: docker compose ps"
    ;;

  down)
    echo -e "${YELLOW}停止并删除容器...${NC}"
    docker compose down
    echo ""
    echo -e "${GREEN}✓ 容器已停止${NC}"
    ;;

  restart)
    echo -e "${YELLOW}重启服务...${NC}"
    docker compose restart
    echo ""
    echo -e "${GREEN}✓ 服务已重启${NC}"
    ;;

  logs)
    echo -e "${YELLOW}查看日志（Ctrl+C 退出）...${NC}"
    docker compose logs -f
    ;;

  ps)
    echo -e "${YELLOW}容器状态:${NC}"
    docker compose ps
    ;;

  clean)
    echo -e "${YELLOW}清理未使用的镜像和容器...${NC}"
    docker system prune -f
    echo ""
    echo -e "${GREEN}✓ 清理完成${NC}"
    ;;

  rebuild)
    echo -e "${YELLOW}强制重新构建（不使用缓存）...${NC}"
    docker compose build --no-cache
    echo ""
    echo -e "${GREEN}✓ 重新构建完成${NC}"
    ;;

  *)
    echo "用法: ./build.sh [命令]"
    echo ""
    echo "可用命令:"
    echo "  build           构建镜像（默认，使用缓存）"
    echo "  build-no-cache  构建镜像（不使用缓存）"
    echo "  up              构建并启动所有服务"
    echo "  down            停止并删除容器"
    echo "  restart         重启服务"
    echo "  logs            查看日志（实时）"
    echo "  ps              查看容器状态"
    echo "  clean           清理未使用的 Docker 资源"
    echo "  rebuild         强制重新构建（无缓存）"
    echo ""
    exit 1
    ;;
esac
