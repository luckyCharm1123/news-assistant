# ==========================================
# 构建阶段 - 使用 uv 加速依赖安装
# ==========================================
# 使用国内镜像加速基础镜像拉取
FROM docker.m.daocloud.io/library/python:3.11-slim-bookworm AS builder

# 1. 使用国内 PyPI 镜像极速安装 uv（替代从 ghcr.io 拉取）
RUN pip install uv -i https://pypi.tuna.tsinghua.edu.cn/simple

# 2. 配置环境变量
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

WORKDIR /app

# 3. 配置 APT 使用国内镜像源（清华大学镜像）
RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources

# 4. 安装系统构建依赖（仅在需要编译 C 扩展时使用）
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 5. 创建虚拟环境
RUN uv venv /opt/venv
# 将虚拟环境加入 PATH
ENV PATH="/opt/venv/bin:$PATH"

# 6. 批量复制所有依赖文件
COPY requirements-*.txt ./

# 7. 安装基础依赖（变化频率低）
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install -r requirements-base.txt \
    -i https://pypi.tuna.tsinghua.edu.cn/simple

# 8. 批量安装其他依赖（uv 解析依赖极快，合并安装更高效）
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install -r requirements-web.txt \
                   -r requirements-crawler.txt \
                   -i https://pypi.tuna.tsinghua.edu.cn/simple


# ==========================================
# 运行阶段 - 最小化镜像
# ==========================================
# 使用国内镜像加速基础镜像拉取
FROM docker.m.daocloud.io/library/python:3.11-slim-bookworm

WORKDIR /app

# 1. 配置 APT 使用国内镜像源（清华大学镜像）
RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources

# 2. 安装运行时必需的系统包
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 3. 从构建阶段复制虚拟环境（体积优化的关键）
COPY --from=builder /opt/venv /opt/venv

# 4. 设置环境变量
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TZ=Asia/Shanghai

# 5. 设置时区
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 6. 复制项目代码（将变化最频繁的文件放在最后）
COPY config/ ./config/
COPY docker/entrypoint.sh /entrypoint.sh
COPY src/ ./src/
COPY main.py ./

# 7. 设置权限并创建目录
RUN chmod +x /entrypoint.sh && mkdir -p data logs

# 暴露端口
EXPOSE 5000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# 使用启动脚本
ENTRYPOINT ["/entrypoint.sh"]

# 默认启动命令（可通过 docker-compose 覆盖）
CMD ["python", "main.py", "all"]
