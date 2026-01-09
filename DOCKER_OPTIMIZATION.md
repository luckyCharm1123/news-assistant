# Docker 构建优化说明

## 优化概览

本次优化采用现代化的 Docker 多阶段构建方案，通过以下技术显著提升构建速度和减小镜像体积：

### 核心优化点

1. **引入 uv 包管理器**
   - 比 pip 快 10-100 倍的依赖安装速度
   - 更高效的依赖解析算法
   - 更好的缓存处理机制

2. **BuildKit 缓存挂载**
   - 使用 `--mount=type=cache` 持久化下载缓存
   - 即使 requirements 文件变更，已下载的包也能复用
   - 显著减少网络下载时间

3. **虚拟环境隔离**
   - 在构建阶段使用独立虚拟环境 `/opt/venv`
   - 运行阶段只复制虚拟环境，路径更清晰
   - 避免复制系统库中的无用文件

4. **优化镜像层级**
   - 合并 COPY 指令减少层数
   - 将变化频繁的文件放在后面 COPY
   - 更好利用 Docker 层缓存

5. **完善的 .dockerignore**
   - 排除不必要的文件（如 .git、__pycache__ 等）
   - 减少构建上下文大小
   - 加快构建启动速度

## 性能对比

### 原方案 vs 优化方案

| 优化项 | 原方案 | 优化方案 | 收益 |
|--------|--------|----------|------|
| 包管理器 | pip | uv | 安装速度提升 10-100 倍 |
| 依赖缓存 | 无 | BuildKit Cache Mount | 二次构建极快，无需重复下载 |
| 运行环境 | 复制系统库 | 复制虚拟环境 | 路径清晰，避免无用文件 |
| 镜像层数 | 多层 | 精简层 | 减小镜像体积 |
| 构建上下文 | 全量上传 | .dockerignore 过滤 | 构建启动速度提升 |

### 预期效果

- **首次构建**: 约 2-3 分钟（取决于网络速度）
- **二次构建**: 约 10-30 秒（利用缓存）
- **镜像体积**: 约 100-200 MB（基础镜像 + 依赖）

## 使用方法

### 1. 快速开始

```bash
# 赋予脚本执行权限（首次运行）
chmod +x build.sh

# 构建镜像
./build.sh build

# 构建并启动服务
./build.sh up

# 查看日志
./build.sh logs
```

### 2. 高级用法

```bash
# 强制重新构建（不使用缓存）
./build.sh rebuild

# 查看容器状态
./build.sh ps

# 重启服务
./build.sh restart

# 停止服务
./build.sh down

# 清理未使用的 Docker 资源
./build.sh clean
```

### 3. 使用 Docker Compose 直接构建

```bash
# 确保 BuildKit 已启用
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# 构建并启动
docker-compose up -d --build

# 或分步操作
docker-compose build
docker-compose up -d
```

## 关键优化详解

### 1. uv 包管理器

```dockerfile
# 从官方镜像复制 uv 二进制文件
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# 配置 uv 环境
ENV UV_COMPILE_BYTECODE=1 \    # 预编译字节码，加快启动
    UV_LINK_MODE=copy          # 复制模式，避免链接问题
```

**优势**:
- 用 Rust 编写，性能极佳
- 并行下载和安装依赖
- 智能依赖解析

### 2. BuildKit 缓存挂载

```dockerfile
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install -r requirements-base.txt \
    -i https://pypi.tuna.tsinghua.edu.cn/simple
```

**优势**:
- 缓存持久化到 Docker 守护进程
- 跨构建共享下载的包
- 即使 Dockerfile 修改，缓存仍可用

### 3. 虚拟环境隔离

```dockerfile
# 构建阶段
RUN uv venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 运行阶段
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
```

**优势**:
- 清晰的环境边界
- 只复制必要的依赖
- 更容易排查问题

### 4. 层级优化

```dockerfile
# 变化频率低的文件先复制
COPY config/ ./config/
COPY docker/entrypoint.sh /entrypoint.sh

# 变化频率高的文件后复制
COPY src/ ./src/
COPY main.py mcp_server.py ./
```

**优势**:
- 代码修改不会导致依赖重新安装
- 最大化利用 Docker 层缓存
- 加快增量构建速度

## 故障排查

### 构建失败

1. **uv 安装失败**
   ```bash
   # 检查网络连接
   # 确保 Docker 能访问 ghcr.io
   ```

2. **依赖安装失败**
   ```bash
   # 查看详细错误日志
   docker-compose build --no-cache

   # 手动测试依赖安装
   docker run --rm python:3.11-slim-bookworm \
     pip install <package-name>
   ```

### 运行时问题

1. **模块找不到**
   ```bash
   # 检查虚拟环境路径
   docker exec -it hotnews_crawler \
     ls -la /opt/venv/lib/python3.11/site-packages/
   ```

2. **权限问题**
   ```bash
   # 确保数据目录有正确权限
   chmod -R 755 data logs
   ```

## 进一步优化建议

### 1. 如果使用 PyTorch/TensorFlow

在 `requirements-ai.txt` 中指定 CPU 版本：

```txt
torch --index-url https://download.pytorch.org/whl/cpu
torchvision --index-url https://download.pytorch.org/whl/cpu
```

这可以将镜像体积从 3GB 减少到 500MB 左右。

### 2. 使用多阶段构建优化

对于编译型依赖，可以考虑：
- 预编译 wheels
- 使用 musllinux 镜像
- 分离编译和运行环境

### 3. CI/CD 集成

```yaml
# .github/workflows/docker.yml
- name: Build and push
  run: |
    echo "DOCKER_BUILDKIT=1" >> $GITHUB_ENV
    docker-compose build
    docker push your-registry/hotnews-crawler:latest
```

## 参考资料

- [uv 官方文档](https://github.com/astral-sh/uv)
- [Docker BuildKit 文档](https://docs.docker.com/build/buildkit/)
- [多阶段构建最佳实践](https://docs.docker.com/build/building/multi-stage/)
- [Dockerfile 优化指南](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)
