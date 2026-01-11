# 🔥 热点新闻爬虫 + MCP服务

一个自动化的热点新闻聚合与分析工具，支持多平台抓取、数据统计分析、Web查询界面和MCP服务集成。

## ✨ 功能特性

- **自动爬取**：每30分钟自动抓取各大平台热点新闻
- **智能去重**：基于URL和标题的双重去重机制，带关注度跟踪
- **定时清理**：自动清理1天前的过期数据（每天凌晨1点）
- **Web界面**：提供直观的Web查询界面和REST API
- **统计分析**：热词统计、趋势分析、来源分布等
- **MCP服务**：基于HTTP的MCP服务器，可供n8n等工具调用
- **API鉴权**：完整的API密钥认证系统，保护敏感操作
- **Docker部署**：一键启动所有服务（Web + MCP）

## 📦 支持的新闻平台

- 今日头条
- 百度热搜
- 微博热搜
- 知乎热榜
- 抖音热点
- B站热搜
- 华尔街见闻
- 更多平台可配置...

## 🚀 快速开始

### 方式一：Docker一键部署（推荐）⭐

```bash
# 1. 克隆项目
git clone https://github.com/luckyCharm1123/news_MCP.git
cd news_MCP

# 2. 一键部署（启动Web服务 + MCP服务）
./deploy.sh
```

**部署完成后可访问**：
- 📊 Web界面: http://localhost:5000
- 🔧 MCP服务: http://localhost:3001

**服务管理**：
```bash
# 查看状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down

# 重启服务
docker-compose restart
```

### 方式二：本地运行

#### 1. 安装依赖

```bash
# Python 3.11+
pip install -r requirements.txt
```

#### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑.env，设置API_KEY
nano .env
```

#### 3. 运行程序

```bash
# 同时运行调度器和Web服务
python main.py all

# 仅运行调度器
python main.py scheduler

# 仅运行Web服务
python main.py web

# 单次爬取（测试用）
python main.py crawl

# 运行MCP服务
python mcp_server.py
```

## 📁 项目结构

```
news_MCP/
├── config/
│   ├── config.yaml          # 主配置文件
│   └── platforms.yaml       # 平台配置
├── src/
│   ├── __init__.py
│   ├── crawler.py           # 爬虫模块
│   ├── database.py          # 数据库模块
│   ├── scheduler.py         # 调度器模块
│   ├── analyzer.py          # 统计分析模块
│   └── web/
│       ├── app.py           # Flask应用
│       └── templates/       # HTML模板
├── data/
│   └── hotnews.db           # SQLite数据库
├── logs/                    # 日志目录
├── main.py                  # 主程序入口
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── requirements.txt
└── README.md
```

## ⚙️ 配置说明

### 主配置文件 (config/config.yaml)

```yaml
# 数据库配置
database:
  path: "data/hotnews.db"      # 数据库路径
  retention_days: 7            # 数据保留天数

# 爬虫配置
crawler:
  api_url: "https://newsnow.busiyi.world/api/s"
  request_interval: 1          # 请求间隔（秒）
  max_retries: 2               # 最大重试次数
  timeout: 10                  # 请求超时（秒）

# 调度配置
scheduler:
  crawl_interval: 300          # 爬取间隔（秒），5分钟
  cleanup_time: "01:00"        # 每天清理时间

# Web配置
web:
  host: "0.0.0.0"
  port: 5000
  debug: false

# 日志配置
logging:
  level: "INFO"
  file: "logs/crawler.log"
```

### 平台配置 (config/platforms.yaml)

```yaml
platforms:
  - id: "toutiao"
    name: "今日头条"
    enabled: true              # 是否启用

  - id: "baidu"
    name: "百度热搜"
    enabled: true
```

## 🎯 使用指南

### Web界面

访问 `http://localhost:5000`：

1. **首页**：查看最近24小时的热点新闻
2. **搜索**：按关键词、来源、时间范围搜索新闻
3. **统计**：查看热词排行、趋势分析、来源分布等

### API接口

```bash
# 获取新闻列表
GET /api/news?limit=50&source=今日头条&keyword=xxx

# 获取新闻详情
GET /api/news/{id}

# 获取热词统计
GET /api/stats/hotwords?days=1&top_n=50

# 获取趋势数据
GET /api/stats/trend?days=7

# 按来源统计
GET /api/stats/by_source?days=7

# 汇总统计
GET /api/stats/summary?days=7

# 每小时分布
GET /api/stats/hourly?days=1

# 热门新闻
GET /api/top_news?limit=20&source=xxx
```

## 📊 数据库结构

### news 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| title | TEXT | 新闻标题 |
| source | TEXT | 来源平台 |
| url | TEXT | 新闻链接（用于去重） |
| rank | INTEGER | 排名 |
| crawled_at | TIMESTAMP | 爬取时间 |
| created_at | TIMESTAMP | 创建时间 |

### 去重机制

- **主要方式**：基于 `source + url` 的唯一索引
- **备用方式**：如果URL为空，使用 `source + title` 去重

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
  crawl_interval: 300  # 修改为需要的秒数
```

### 调整数据保留期

编辑 `config/config.yaml`：

```yaml
database:
  retention_days: 7  # 修改为需要的天数
```

## 🛠️ 技术栈

- **Python 3.11+**
- **Flask** - Web框架
- **SQLite** - 数据库
- **APScheduler** - 定时任务
- **Jieba** - 中文分词
- **Bootstrap 5** - 前端框架
- **ECharts** - 数据可视化

## 📝 注意事项

1. **时区设置**：默认使用 Asia/Shanghai 时区，可在环境变量中修改
2. **数据备份**：重要数据请定期备份 `data/hotnews.db`
3. **日志管理**：日志文件会自动轮转，保留最近5个文件
4. **API限流**：请合理设置请求间隔，避免对目标网站造成压力

## 🐛 常见问题

### Q: 如何查看日志？

```bash
# Docker部署
docker-compose logs -f

# 本地运行
tail -f logs/crawler.log
```

### Q: 数据库文件太大怎么办？

1. 减少保留天数：修改 `config.yaml` 中的 `retention_days`
2. 手动清理：删除 `data/hotnews.db`，程序会自动重建

### Q: 如何停止服务？

```bash
# Docker部署
docker-compose down

# 本地运行
按 Ctrl+C
```

## 📄 许可证

GNU General Public License v3.0

## 🙏 致谢

- 数据来源：NewsNow API
- 参考项目：TrendRadar

---

**Enjoy!** 🎉
