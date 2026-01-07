# Docker集成MCP服务更新说明

## 更新时间
2026-01-07

## 更新概述
将MCP服务集成到Docker Compose中，实现一键启动所有服务（Web服务 + MCP服务）。

---

## 主要变更

### 1. docker-compose.yml
**新增 `mcp-server` 服务**：
- 容器名：`hotnews_mcp_server`
- 端口映射：`3001:3001`
- 启动命令：`python mcp_server.py`
- 依赖：`hotnews-crawler`（Web服务先启动）
- 健康检查：每30秒检查 `/health` 端点
- 自动重启：`restart: unless-stopped`

**网络配置**：
- 两个服务都在 `hotnews-network` 网络中
- MCP服务通过容器间网络访问Web服务（`http://hotnews-crawler:5000`）

### 2. docker/Dockerfile
**新增内容**：
- 安装 `curl`（用于健康检查）
- 暴露端口：`5000` 和 `3001`

### 3. deploy.sh
**改进功能**：
- ✅ 自动检查 `.env` 文件是否存在
- ✅ 如果不存在，从 `.env.example` 自动创建
- ✅ 启动后自动测试两个服务的健康状态
- ✅ 显示更友好的部署完成信息

### 4. DEPLOY.md
**更新内容**：
- 部署步骤从3步简化为2步
- 移除了systemd服务配置（不再需要）
- 更新服务管理命令
- 添加MCP服务Docker管理说明
- 添加故障排查章节

### 5. README.md
**更新内容**：
- 标题改为"热点新闻爬虫 + MCP服务"
- 更新功能特性列表
- 强调Docker一键部署
- 添加MCP服务访问地址

---

## 部署方式对比

### 旧方式（3步）
1. 上传代码
2. 运行 `./deploy.sh`（仅启动Web服务）
3. 运行 `./mcp_service.sh start`（手动启动MCP服务）

### 新方式（2步）✨
1. 上传代码
2. 运行 `./deploy.sh`（自动启动Web + MCP服务）

---

## 优势

### 1. 简化部署
- **一键启动**：单个命令启动所有服务
- **自动依赖**：MCP服务自动等待Web服务启动
- **健康检查**：自动监控服务状态

### 2. 统一管理
- **统一日志**：通过 `docker-compose logs` 查看所有服务日志
- **统一启停**：通过 `docker-compose` 管理所有服务
- **自动重启**：两个服务都配置了自动重启

### 3. 更好的可靠性
- **容器编排**：Docker Compose管理服务依赖关系
- **网络隔离**：服务间通过专用网络通信
- **健康监控**：定期检查服务健康状态

---

## 兼容性说明

### 保留的功能
- ✅ `mcp_service.sh` 脚本仍然可用（用于本地开发）
- ✅ 所有API端点保持不变
- ✅ MCP服务接口保持不变
- ✅ 环境变量配置保持不变

### 变化的内容
- 🔄 MCP服务默认在Docker中运行（而非独立进程）
- 🔄 MCP服务通过容器网络访问Web服务
- 🔄 日志位置从 `/tmp/mcp_server.log` 改为 `docker-compose logs`

---

## 迁移指南

### 从旧版本升级

如果你之前使用的是独立MCP服务（`./mcp_service.sh`），按以下步骤迁移：

1. **停止旧服务**：
   ```bash
   ./mcp_service.sh stop
   ```

2. **更新代码**：
   ```bash
   git pull
   ```

3. **重新部署**：
   ```bash
   docker-compose down
   ./deploy.sh
   ```

4. **验证服务**：
   ```bash
   docker-compose ps
   curl http://localhost:5000/health
   curl http://localhost:3001/health
   ```

### 回滚到旧方式

如果需要回滚到独立MCP服务：

1. **停止Docker中的MCP服务**：
   ```bash
   docker-compose stop mcp-server
   ```

2. **手动启动MCP服务**：
   ```bash
   ./mcp_service.sh start
   ```

3. **永久禁用Docker中的MCP服务**：
   编辑 `docker-compose.yml`，注释或删除 `mcp-server` 服务定义

---

## 测试验证

### 自动测试
`deploy.sh` 脚本会自动测试：
- ✅ Web服务健康状态（`http://localhost:5000/health`）
- ✅ MCP服务健康状态（`http://localhost:3001/health`）

### 手动测试

**测试Web服务**：
```bash
# 健康检查
curl http://localhost:5000/health

# 获取最近新闻
curl http://localhost:5000/api/recent_news?hours=2
```

**测试MCP服务**：
```bash
# 健康检查
curl http://localhost:3001/health

# 获取工具列表
curl http://localhost:3001/tools

# 调用工具（需要API密钥）
export API_KEY=$(grep API_KEY .env | cut -d'=' -f2)
curl -X POST http://localhost:3001/tools/call \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "name": "get_recent_news",
    "arguments": {"hours": 2}
  }'
```

---

## 故障排查

### 问题1：MCP服务无法连接Web服务

**症状**：MCP服务日志显示连接失败

**解决方案**：
```bash
# 检查服务是否都在运行
docker-compose ps

# 检查网络连接
docker network inspect hotnews-network

# 查看MCP服务日志
docker-compose logs mcp-server

# 重启MCP服务
docker-compose restart mcp-server
```

### 问题2：端口冲突

**症状**：服务启动失败，提示端口已被占用

**解决方案**：
```bash
# 检查端口占用
sudo netstat -tlnp | grep 5000
sudo netstat -tlnp | grep 3001

# 修改端口（编辑docker-compose.yml）
# ports:
#   - "5001:5000"  # Web服务改为5001
#   - "3002:3001"  # MCP服务改为3002
```

### 问题3：服务启动顺序问题

**症状**：MCP服务启动失败，因为Web服务还未就绪

**解决方案**：
- Docker Compose已配置 `depends_on`，但MCP服务可能仍需等待
- 使用健康检查确保Web服务完全启动
- MCP服务会自动重试连接

---

## 性能优化

### 资源限制

如果需要限制服务资源使用，编辑 `docker-compose.yml`：

```yaml
services:
  hotnews-crawler:
    # ... 其他配置
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M

  mcp-server:
    # ... 其他配置
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 256M
        reservations:
          cpus: '0.25'
          memory: 128M
```

### 日志管理

限制日志文件大小：

```yaml
services:
  hotnews-crawler:
    # ... 其他配置
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  mcp-server:
    # ... 其他配置
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

---

## 下一步计划

可能的未来改进：

1. **添加Nginx反向代理**：统一入口，支持HTTPS
2. **添加监控面板**：Grafana + Prometheus
3. **添加自动伸缩**：根据负载自动调整容器数量
4. **添加负载均衡**：多实例部署
5. **添加备份服务**：自动备份数据库

---

## 总结

✅ **Docker Compose集成完成**
- Web服务和MCP服务统一管理
- 一键部署，简化运维
- 自动重启，提高可靠性
- 健康检查，及时发现问题

📚 **相关文档**：
- [DEPLOY.md](DEPLOY.md) - 完整部署指南
- [API_AUTH.md](API_AUTH.md) - API鉴权文档
- [MCP_README.md](MCP_README.md) - MCP服务文档

🎉 **开始使用**：
```bash
git clone https://github.com/luckyCharm1123/news_MCP.git
cd news_MCP
./deploy.sh
```
