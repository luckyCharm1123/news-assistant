# 热点新闻爬虫 - 服务器部署指南

## 最快部署方式（3步完成）

### 前提条件
服务器已安装：
- Docker
- Docker Compose
- Python 3.10+

### 步骤1：上传代码到服务器
```bash
# 方式1：使用scp上传
scp -r hotnews_crawler user@your-server:/path/to/deploy/

# 方式2：使用git克隆（如果代码在git仓库）
git clone your-repo-url
cd hotnews_crawler
```

### 步骤2：一键部署
```bash
cd /path/to/hotnews_crawler
./deploy.sh
```

### 步骤3：启动MCP服务
```bash
./mcp_service.sh start
```

---

## 验证部署

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

### Web服务（Docker）
```bash
# 查看状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 重启服务
docker-compose restart

# 停止服务
docker-compose down

# 重新构建并启动
docker-compose up -d --build
```

### MCP服务
```bash
# 启动
./mcp_service.sh start

# 停止
./mcp_service.sh stop

# 重启
./mcp_service.sh restart

# 查看状态
./mcp_service.sh status

# 查看日志
./mcp_service.sh logs
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

### Web服务（Docker）
Docker Compose默认会自动重启容器（已在docker-compose.yml中配置）

### MCP服务（使用systemd）
```bash
# 创建systemd服务文件
sudo tee /etc/systemd/system/hotnews-mcp.service > /dev/null <<EOF
[Unit]
Description=Hotnews MCP Server
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/hotnews_crawler
ExecStart=/usr/bin/python3 /path/to/hotnews_crawler/mcp_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 启用服务
sudo systemctl daemon-reload
sudo systemctl enable hotnews-mcp
sudo systemctl start hotnews-mcp

# 检查状态
sudo systemctl status hotnews-mcp
```

---

## 常见问题

### 问题1：端口被占用
```bash
# 检查端口占用
sudo netstat -tlnp | grep 5000
sudo netstat -tlnp | grep 3001

# 修改端口
# 编辑 config/config.yaml 修改 web.port
# 编辑 mcp_server.py 修改 run_server(port=3001)
```

### 问题2：权限问题
```bash
# 给脚本执行权限
chmod +x deploy.sh
chmod +x mcp_service.sh

# 数据目录权限
chmod -R 755 data logs
```

### 问题3：Docker服务未启动
```bash
sudo systemctl start docker
sudo systemctl enable docker
```

---

## 监控和维护

### 定期检查日志
```bash
# Web服务日志
docker-compose logs --tail=100

# MCP服务日志
./mcp_service.sh logs
```

### 数据库备份（可选）
```bash
# 备份数据库
cp data/hotnews.db data/backup/hotnews_$(date +%Y%m%d_%H%M%S).db

# 定时备份（添加到crontab）
0 2 * * * cp /path/to/hotnews_crawler/data/hotnews.db /path/to/backup/hotnews_$(date +\%Y\%m\%d).db
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
- **API文档**: 见 MCP_README.md
