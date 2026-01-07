# 热点新闻爬虫 - 服务器部署指南

## 最快部署方式（2步完成）

### 前提条件
服务器已安装：
- Docker
- Docker Compose

### 步骤1：上传代码到服务器
```bash
# 方式1：使用scp上传
scp -r hotnews_crawler user@your-server:/path/to/deploy/

# 方式2：使用git克隆（如果代码在git仓库）
git clone https://github.com/luckyCharm1123/news_MCP.git
cd news_MCP
```

### 步骤2：一键部署（启动所有服务）
```bash
cd /path/to/news_MCP
./deploy.sh
```

**说明**：
- `deploy.sh` 会自动启动 Web服务（端口5000）和 MCP服务（端口3001）
- 如果 `.env` 文件不存在，会自动从 `.env.example` 创建
- 部署完成后，两个服务都会自动运行并支持开机自启动

---

## 验证部署

### 检查所有服务
```bash
# 检查容器状态
docker-compose ps

# 应该看到两个容器都在运行：
# - hotnews_crawler (Web服务)
# - hotnews_mcp_server (MCP服务)
```

### 检查Web服务
```bash
curl http://localhost:5000/health
```

### 检查MCP服务
```bash
curl http://localhost:3001/health
```

---

## 服务管理命令

### 所有服务（Docker Compose）
```bash
# 查看状态
docker-compose ps

# 查看所有服务日志
docker-compose logs -f

# 查看Web服务日志
docker-compose logs -f hotnews-crawler

# 查看MCP服务日志
docker-compose logs -f mcp-server

# 重启所有服务
docker-compose restart

# 重启单个服务
docker-compose restart hotnews-crawler
docker-compose restart mcp-server

# 停止所有服务
docker-compose down

# 重新构建并启动
docker-compose up -d --build
```

---

## 防火墙配置（如果需要从外网访问）

```bash
# 开放5000端口（Web服务）
sudo ufw allow 5000/tcp

# 开放3001端口（MCP服务，可选）
sudo ufw allow 3001/tcp

# 查看防火墙状态
sudo ufw status
```

---

## 设置开机自启动

Docker Compose已配置自动重启（`restart: unless-stopped`），服务会在系统重启后自动启动。

无需额外配置systemd服务。

---

## 单独管理MCP服务（可选）

虽然MCP服务已集成到Docker Compose，但如果需要单独运行：

```bash
# 停止Docker中的MCP服务
docker-compose stop mcp-server

# 手动运行MCP服务（用于开发调试）
python3 mcp_server.py

# 恢复Docker中的MCP服务
docker-compose start mcp-server
```

---

## 常见问题

### 问题1：端口被占用
```bash
# 检查端口占用
sudo netstat -tlnp | grep 5000
sudo netstat -tlnp | grep 3001

# 修改端口
# 编辑 docker-compose.yml 修改端口映射
```

### 问题2：权限问题
```bash
# 给脚本执行权限
chmod +x deploy.sh

# 数据目录权限
chmod -R 755 data logs
```

### 问题3：Docker服务未启动
```bash
sudo systemctl start docker
sudo systemctl enable docker
```

### 问题4：MCP服务无法连接Web服务
```bash
# 检查服务是否都在运行
docker-compose ps

# 检查网络连接
docker network inspect hotnews-network

# 查看MCP服务日志
docker-compose logs mcp-server
```

---

## 监控和维护

### 定期检查日志
```bash
# 查看所有服务日志
docker-compose logs -f

# 查看最近100行日志
docker-compose logs --tail=100

# 分别查看服务日志
docker-compose logs hotnews-crawler
docker-compose logs mcp-server
```

### 数据库备份（可选）
```bash
# 备份数据库
cp data/hotnews.db data/backup/hotnews_$(date +%Y%m%d_%H%M%S).db

# 定时备份（添加到crontab）
0 2 * * * cp /path/to/news_MCP/data/hotnews.db /path/to/backup/hotnews_$(date +\%Y\%m\%d).db
```

---

## 性能优化

### 调整爬取间隔
编辑 `config/config.yaml`:
```yaml
scheduler:
  crawl_interval: 1800  # 30分钟，可根据需要调整
```

### 调整数据保留期
```yaml
database:
  retention_days: 1  # 保留1天，可根据需要调整
```

---

## 服务地址

- **Web界面**: http://your-server-ip:5000
- **MCP服务**: http://your-server-ip:3001
- **API文档**: 见 [API_AUTH.md](API_AUTH.md) 和 [MCP_README.md](MCP_README.md)

