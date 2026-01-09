# ==========================================
# 构建阶段 - 使用 uv 加速依赖安装
# ==========================================
FROM python:3.11-slim-bookworm AS builder

# 1. 安装 uv (极速包管理器，比 pip 快 10-100 倍)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# 2. 配置环境变量
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

WORKDIR /app

# 3. 安装系统构建依赖（仅在需要编译 C 扩展时使用）
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 4. 创建虚拟环境
RUN uv venv /opt/venv
# 将虚拟环境加入 PATH
ENV PATH="/opt/venv/bin:$PATH"

# 5. 批量复制所有依赖文件
COPY requirements-*.txt ./

# 6. 安装基础依赖（变化频率低）
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install -r requirements-base.txt \
    -i https://pypi.tuna.tsinghua.edu.cn/simple

# 7. 批量安装其他依赖（uv 解析依赖极快，合并安装更高效）
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install -r requirements-web.txt \
                   -r requirements-crawler.txt \
                   -r requirements-ai.txt \
                   -r requirements-mcp.txt \
                   -i https://pypi.tuna.tsinghua.edu.cn/simple


# ==========================================
# 运行阶段 - 最小化镜像
# ==========================================
FROM python:3.11-slim-bookworm

WORKDIR /app

# 1. 安装运行时必需的系统包
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 2. 从构建阶段复制虚拟环境（体积优化的关键）
COPY --from=builder /opt/venv /opt/venv

# 3. 设置环境变量
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TZ=Asia/Shanghai

# 4. 设置时区
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 5. 复制项目代码（将变化最频繁的文件放在最后）
COPY config/ ./config/
COPY docker/entrypoint.sh /entrypoint.sh
COPY src/ ./src/
COPY main.py mcp_server.py ./

# 6. 设置权限并创建目录
RUN chmod +x /entrypoint.sh && mkdir -p data logs

# 暴露端口
EXPOSE 5000 3001

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# 使用启动脚本
ENTRYPOINT ["/entrypoint.sh"]

# 默认启动命令（可通过 docker-compose 覆盖）
CMD ["python", "main.py", "all"]
