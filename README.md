# 🔥 新闻收集小助手

**一个自动化的热点新闻聚合，支持多平台抓取、智能去重。**
- PS：本项目仅供学习参考，请勿用于非法用途。
- PS：写这个项目主要是学习n8n时，想做一个新闻的MCP服务，后面改学习skill了，就把MCP去掉了，只保留了数据库部分和对应的API接口。
- PS：对应的skill还在制作优化，后续也会开源。

## 🙏 致谢

### 数据来源：NewsNow API
- 爬取间隔为30分钟
- 可以关注一下大佬的[newsnow](https://github.com/ourongxing/newsnow)
- 再次感谢大佬的贡献者，感谢他们提供的数据源。
### 参考项目：TrendRadar
- 项目参考[TrendRadar](https://github.com/sansan0/TrendRadar)
- 感谢大佬的开源
## ✨ 功能特性

- **自动爬取**：每30分钟自动抓取各大平台热点新闻
- **智能去重**：基于URL和标题的双重去重机制
- **定时清理**：自动清理1天前的过期数据（每天凌晨1点）
- **Web界面**：提供REST API
- **Docker部署**：支持 Docker Compose 一键部署
- **IPv6支持**：原生支持 IPv4 和 IPv6 双栈监听
- **健康检查**：内置容器健康检查机制

## 📦 支持的新闻平台

- 华尔街见闻（新闻/热点/快讯）
- 澎湃新闻
- 财联社（电报/热门/深度）
- 36氪（快讯/热榜）
- IT之家
- V2EX 分享
- 凤凰网
- 卫星通讯社
- 参考消息
- Solidot
- 靠谱新闻
- MK新闻

> 可通过 `config/platforms.yaml` 轻松添加更多平台
> 配置参考新闻源[pinyin.json](https://github.com/ourongxing/newsnow/blob/main/shared/pinyin.json)
## 🚀 快速开始

### 方式一：Docker 部署（推荐）⭐

```bash
# 1. 克隆项目
git clone https://github.com/luckyCharm1123/news_MCP.git
cd news_MCP

# 2. 配置环境变量（可选）
cp .env.example .env
# 编辑 .env 文件设置必要的环境变量

# 3. 启动服务
docker compose up -d

# 或者使用传统命令（需启用 BuildKit）
DOCKER_BUILDKIT=1 docker-compose build
docker-compose up -d
```

**部署完成后可访问**：
- 📊 Web界面: http://localhost:5000
- 📊 健康检查: http://localhost:5000/health

**服务管理**：
```bash
# 查看状态
docker compose ps

# 查看日志
docker compose logs -f

# 停止服务
docker compose down

# 重启服务
docker compose restart

# 重新构建并启动
docker compose up -d --build
```

### 方式二：本地运行

#### 1. 环境要求

- Python 3.11+

#### 2. 安装依赖

```bash
pip install -r requirements.txt
```

#### 3. 配置环境变量（可选）

```bash
# 复制环境变量模板
cp .env.example .env

# 根据需要编辑 .env 文件
nano .env
```

#### 4. 运行程序

```bash
# 同时运行调度器和Web服务（推荐）
python main.py

# 仅运行调度器
python main.py scheduler

# 仅运行Web服务
python main.py web

# 单次爬取（测试用）
python main.py crawl
```

## 📁 项目结构

```
hotnews_crawler/
├── config/
│   ├── config.yaml          # 主配置文件
│   └── platforms.yaml       # 平台配置
├── docker/
│   ├── Dockerfile           # Docker 镜像构建文件
│   └── entrypoint.sh        # 容器启动脚本
├── src/
│   ├── crawler.py           # 爬虫模块
│   ├── database.py          # 数据库操作模块
│   ├── scheduler.py         # 定时调度模块
│   └── web/
│       └── app.py           # Flask Web 应用
├── data/
│   └── hotnews.db           # SQLite 数据库（自动生成）
├── logs/                    # 日志目录（自动生成）
├── main.py                  # 主程序入口
├── docker-compose.yml       # Docker Compose 配置
├── requirements.txt         # Python 依赖
├── .env.example             # 环境变量模板
└── README.md
```

## ⚙️ 配置说明

### 主配置文件 (config/config.yaml)

```yaml
# 数据库配置
database:
  path: "data/hotnews.db"      # 数据库路径
  retention_days: 1            # 数据保留天数（保留今天，清理昨天的数据）

# 爬虫配置
crawler:
  api_url: "https://newsnow.busiyi.world/api/s"
  request_interval: 1          # 请求间隔（秒）
  max_retries: 2               # 最大重试次数
  retry_wait_min: 3            # 最小重试等待时间（秒）
  retry_wait_max: 5            # 最大重试等待时间（秒）
  timeout: 10                  # 请求超时（秒）

# 调度配置
scheduler:
  crawl_interval: 1800         # 爬取间隔（秒），30分钟
  cleanup_time: "01:00"        # 每天清理时间

# Web配置
web:
  host: "::"                   # IPv6双栈监听 (同时支持IPv4和IPv6)
  port: 5000
  debug: false

# 日志配置
logging:
  level: "INFO"                # DEBUG, INFO, WARNING, ERROR
  file: "logs/crawler.log"
  max_bytes: 10485760          # 10MB
  backup_count: 5

# 时区配置
timezone: "Asia/Shanghai"
```

### 平台配置 (config/platforms.yaml)

```yaml
platforms:
  - id: "wallstreetcn-news"    # 平台唯一标识（勿修改）
    name: "华尔街见闻"         # 显示名称（可自定义）
    enabled: true              # 是否启用该平台

  - id: "36kr-quick"
    name: "36氪-快讯"
    enabled: true

  # 添加更多平台...
```

## 🎯 使用指南


### API 接口

```bash
# 获取新闻列表
GET /api/news?limit=50&source=华尔街见闻&keyword=xxx

# 获取新闻详情
GET /api/news/{id}

```


### 去重机制

- **主要方式**：基于 `source + url` 的唯一索引
- **备用方式**：如果 URL 为空，使用 `source + title` 去重

## 🔧 开发说明

### 添加新平台

编辑 `config/platforms.yaml`：

```yaml
platforms:
  - id: "new_platform_id"
    name: "新平台名称"
    enabled: true
```

### 修改爬取间隔

编辑 `config/config.yaml`：

```yaml
scheduler:
  crawl_interval: 1800  # 修改为需要的秒数（默认30分钟）
```

### 调整数据保留期

编辑 `config/config.yaml`：

```yaml
database:
  retention_days: 1  # 修改为需要的天数（默认保留1天）
```

## 🛠️ 技术栈

- **Python 3.11+**
- **SQLite** - 数据库
- **APScheduler** - 定时任务调度
- **PyYAML** - 配置文件解析
- **Docker** - 容器化部署

## 📝 注意事项

1. **时区设置**：默认使用 `Asia/Shanghai` 时区
2. **数据备份**：重要数据请定期备份 `data/hotnews.db`
3. **日志管理**：日志文件会自动轮转，保留最近 5 个文件，每个文件最大 10MB
4. **IPv6 支持**：默认使用 `::` 监听，同时支持 IPv4 和 IPv6 访问
5. **数据清理**：默认只保留当天数据，每天凌晨 1 点自动清理过期数据

## 🐛 常见问题

### Q: 如何查看日志？

```bash
# Docker 部署
docker compose logs -f

# 本地运行
tail -f logs/crawler.log
```

### Q: 数据库文件太大怎么办？

1. 减少保留天数：修改 `config/config.yaml` 中的 `retention_days`
2. 手动清理：删除 `data/hotnews.db`，程序会自动重建

### Q: 如何停止服务？

```bash
# Docker 部署
docker compose down

# 本地运行
按 Ctrl+C
```

### Q: 容器健康检查失败怎么办？

```bash
# 检查容器状态
docker compose ps

# 查看健康检查日志
docker compose logs hotnews-crawler | grep health

# 手动测试健康检查端点
curl http://localhost:5000/health
```

## 📄 许可证

GNU General Public License v3.0


---

**Enjoy!** 🎉
