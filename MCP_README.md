# 热点新闻爬虫 - MCP服务使用指南

## 概述

本系统提供了一个基于HTTP的MCP (Model Context Protocol) 服务，可以与n8n等自动化工具集成，提供新闻管理和关注度控制功能。

## 服务端口

- **Web服务**: http://localhost:5000
- **MCP服务**: http://localhost:3001

## 启动服务

### 方式一：使用Docker Compose（推荐）

```bash
# 启动Web服务和爬虫
docker-compose up -d

# 启动MCP服务器
python3 mcp_server.py
```

### 方式二：手动启动

```bash
# 启动Web服务
python3 main.py all

# 启动MCP服务器（新终端）
python3 mcp_server.py
```

## MCP服务端点

### 1. 服务器信息
```
GET http://localhost:3001/mcp
```

响应示例：
```json
{
  "name": "hotnews-crawler",
  "version": "1.0.0",
  "description": "热点新闻爬虫MCP服务器",
  "baseUrl": "http://localhost:5000"
}
```

### 2. 获取可用工具列表
```
GET http://localhost:3001/tools
```

响应示例：
```json
[
  {
    "name": "decrease_news_popularity",
    "description": "降低指定新闻的关注度",
    "inputSchema": {
      "type": "object",
      "properties": {
        "news_id": {"type": "integer", "description": "新闻ID"},
        "decrease_amount": {"type": "integer", "default": 1}
      },
      "required": ["news_id"]
    }
  }
]
```

### 3. 调用工具
```
POST http://localhost:3001/tools/call
Content-Type: application/json

{
  "name": "decrease_news_popularity",
  "arguments": {
    "news_id": 123,
    "decrease_amount": 2
  }
}
```

### 4. 健康检查
```
GET http://localhost:3001/health
```

## 可用工具

### 1. decrease_news_popularity
降低指定新闻的关注度

**参数：**
- `news_id` (必需): 新闻ID
- `decrease_amount` (可选): 降低的数值，默认为1

**示例：**
```bash
curl -X POST http://localhost:3001/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "decrease_news_popularity",
    "arguments": {
      "news_id": 123,
      "decrease_amount": 2
    }
  }'
```

### 2. batch_decrease_popularity
批量降低多条新闻的关注度

**参数：**
- `news_ids` (必需): 新闻ID数组
- `decrease_amount` (可选): 每条新闻降低的数值，默认为1

**示例：**
```bash
curl -X POST http://localhost:3001/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "batch_decrease_popularity",
    "arguments": {
      "news_ids": [123, 456, 789],
      "decrease_amount": 1
    }
  }'
```

### 3. get_recent_news
获取最近新增的新闻

**参数：**
- `hours` (可选): 最近多少小时，默认为2

**示例：**
```bash
curl -X POST http://localhost:3001/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "get_recent_news",
    "arguments": {
      "hours": 2
    }
  }'
```

### 4. get_high_popularity_news
获取高关注度新闻列表

**参数：**
- `limit` (可选): 返回条数，默认为20
- `min_popularity` (可选): 最低关注度，默认为3

**示例：**
```bash
curl -X POST http://localhost:3001/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "get_high_popularity_news",
    "arguments": {
      "limit": 20,
      "min_popularity": 3
    }
  }'
```

## 在n8n中使用

### 1. HTTP Request节点配置

**调用工具示例：**
- **Method**: POST
- **URL**: http://localhost:3001/tools/call
- **Authentication**: None
- **Body** (JSON):
  ```json
  {
    "name": "decrease_news_popularity",
    "arguments": {
      "news_id": {{ $json.id }},
      "decrease_amount": 1
    }
  }
  ```

### 2. 典型工作流

#### 工作流1：获取新闻并降低不感兴趣的新闻关注度

```
1. HTTP Request (GET http://localhost:3001/tools/call)
   - 获取最近新闻列表

2. AI Agent
   - 分析新闻内容，识别不感兴趣的新闻

3. HTTP Request (POST http://localhost:3001/tools/call)
   - 批量降低不感兴趣新闻的关注度
```

#### 工作流2：定期获取高关注度新闻

```
1. Cron Node (每小时执行)
   ↓
2. HTTP Request
   - 调用 get_high_popularity_news
   ↓
3. Filter Node
   - 过滤特定类型的新闻
   ↓
4. Send to notification
```

## 直接API调用

如果不想通过MCP服务，也可以直接调用Web API：

### 降低新闻关注度
```bash
curl -X POST http://localhost:5000/api/news/123/decrease_popularity \
  -H "Content-Type: application/json" \
  -d '{"decrease_amount": 2}'
```

### 批量降低关注度
```bash
curl -X POST http://localhost:5000/api/news/batch_decrease_popularity \
  -H "Content-Type: application/json" \
  -d '{
    "news_ids": [123, 456, 789],
    "decrease_amount": 1
  }'
```

### 获取最近新闻
```bash
curl http://localhost:5000/api/recent_news?hours=2
```

### 获取高关注度新闻
```bash
curl http://localhost:5000/api/news/high_popularity?limit=20&min_popularity=3
```

## 数据结构

### 新闻对象
```json
{
  "id": 123,
  "title": "新闻标题",
  "source": "来源平台",
  "url": "新闻链接",
  "rank": 5,
  "popularity": 6,
  "crawled_at": "2026-01-07 21:18:08",
  "created_at": "2026-01-07 21:16:31"
}
```

### 工具响应
```json
{
  "success": true,
  "message": "新闻ID 123 关注度已降低 2",
  "data": {
    "id": 123,
    "title": "新闻标题",
    "current_popularity": 4,
    "decreased_by": 2
  }
}
```

## 注意事项

1. **关注度机制**：
   - 新新闻初始关注度 = 1
   - 每次爬取到重复新闻，关注度 +1
   - 降低关注度不会小于0

2. **数据保留**：
   - 系统默认保留1天的数据
   - 每天凌晨1点自动清理过期数据

3. **爬取间隔**：
   - 默认每30分钟爬取一次

4. **去重逻辑**：
   - URL去重（优先）
   - 标题去重（备用）
