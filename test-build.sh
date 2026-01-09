#!/bin/bash
# Docker 构建性能测试脚本

set -e

echo "=========================================="
echo "Docker 构建性能测试"
echo "=========================================="
echo ""

# 颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 记录时间
start_time=$(date +%s)

# 清理旧镜像（可选）
echo -e "${YELLOW}1. 清理旧构建缓存...${NC}"
docker builder prune -f --filter type=regular

echo ""
echo -e "${YELLOW}2. 首次构建（无缓存）...${NC}"
echo "----------------------------------------"

# 首次构建
first_build_start=$(date +%s)
DOCKER_BUILDKIT=1 docker-compose build --no-cache --progress=plain | tee /tmp/build1.log
first_build_end=$(date +%s)
first_build_time=$((first_build_end - first_build_start))

echo ""
echo -e "${YELLOW}3. 二次构建（有缓存）...${NC}"
echo "----------------------------------------"

# 触发小改动（修改文件时间戳）
touch docker-compose.yml

# 二次构建
second_build_start=$(date +%s)
DOCKER_BUILDKIT=1 docker-compose build --progress=plain | tee /tmp/build2.log
second_build_end=$(date +%s)
second_build_time=$((second_build_end - second_build_start))

# 获取镜像大小
echo ""
echo -e "${YELLOW}4. 分析镜像大小...${NC}"
echo "----------------------------------------"
docker images | grep hotnews-crawler

# 输出结果
end_time=$(date +%s)
total_time=$((end_time - start_time))

echo ""
echo "=========================================="
echo -e "${GREEN}性能测试结果${NC}"
echo "=========================================="
echo ""
echo -e "${BLUE}首次构建时间${NC}: ${first_build_time} 秒"
echo -e "${BLUE}二次构建时间${NC}: ${second_build_time} 秒"
echo -e "${BLUE}速度提升${NC}: $(echo "scale=1; $first_build_time / $second_build_time" | bc)x 倍"
echo -e "${BLUE}总测试时间${NC}: ${total_time} 秒"
echo ""

# 分析缓存命中率
if grep -q "CACHED" /tmp/build2.log; then
    cache_hits=$(grep -c "CACHED" /tmp/build2.log || echo "0")
    echo -e "${GREEN}✓ 缓存命中${NC}: ${cache_hits} 层"
fi

echo ""
echo "详细日志已保存到："
echo "  - /tmp/build1.log (首次构建)"
echo "  - /tmp/build2.log (二次构建)"
echo ""
echo -e "${GREEN}测试完成!${NC}"
