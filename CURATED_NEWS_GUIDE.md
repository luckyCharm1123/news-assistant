# AI精选新闻功能使用指南

## 功能概述

AI精选新闻功能允许n8n工作流:
1. 获取最近2小时的原始新闻
2. 使用AI提炼出感兴趣的新闻(自动生成标题)
3. 对比并去重,只保留新的新闻
4. 后续工作流可以为这些新闻生成详细摘要

---

## 数据表结构

### `curated_news` 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键(自增) |
| title | TEXT | AI生成的标题(唯一) |
| source_news_id | INTEGER | 原始新闻ID(外键) |
| summary | TEXT | 新闻摘要内容 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

**去重逻辑**: 标题自动去重,如果标题已存在则更新记录

---

## Web API端点

### 1. 获取AI精选新闻列表
```
GET /api/curated_news?limit=100&offset=0
```

**响应示例**:
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "title": "GPT-5即将发布,性能提升10倍",
      "source_news_id": 123,
      "summary": "OpenAI宣布GPT-5将在下个月发布...",
      "created_at": "2026-01-08 10:00:00",
      "updated_at": "2026-01-08 10:00:00",
      "original_title": "OpenAI's GPT-5 Model Announcement",
      "source": "TechCrunch",
      "url": "https://techcrunch.com/..."
    }
  ],
  "total": 15
}
```

### 2. 创建/更新AI精选新闻
```
POST /api/curated_news
Content-Type: application/json
X-API-Key: your-api-key

{
  "title": "AI生成的新标题",
  "source_news_id": 123,
  "summary": "可选的摘要内容"
}
```

### 3. 批量创建/更新AI精选新闻
```
POST /api/curated_news/batch
Content-Type: application/json
X-API-Key: your-api-key

{
  "news_list": [
    {
      "title": "标题1",
      "source_news_id": 123,
      "summary": "摘要1"
    },
    {
      "title": "标题2",
      "source_news_id": 124
    }
  ]
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "批量操作完成: 新增10条, 更新5条",
  "data": {
    "inserted_count": 10,
    "updated_count": 5,
    "total_count": 15
  }
}
```

### 4. 更新新闻摘要
```
PUT /api/curated_news/{id}/summary
Content-Type: application/json
X-API-Key: your-api-key

{
  "summary": "AI生成的详细摘要内容"
}
```

### 5. 检查标题是否存在
```
POST /api/curated_news/check
Content-Type: application/json
X-API-Key: your-api-key

{
  "title": "标题内容"
}
```

**响应**:
```json
{
  "success": true,
  "exists": true,
  "data": {
    "id": 1,
    "title": "标题内容",
    "summary": "...",
    "source_news_id": 123
  }
}
```

---

## MCP工具

在n8n中可以使用以下MCP工具:

### 1. `add_curated_news`
添加或更新单条AI精选新闻(自动去重)

**参数**:
- `title` (string, 必需): AI生成的标题
- `source_news_id` (integer, 必需): 原始新闻ID
- `summary` (string, 可选): 新闻摘要

### 2. `batch_add_curated_news`
批量添加或更新AI精选新闻(自动去重)

**参数**:
- `news_list` (array, 必需): 新闻对象数组
  - 每个对象包含: `title`, `source_news_id`, `summary`(可选)

### 3. `get_curated_news`
获取所有AI精选新闻列表

**参数**:
- `limit` (integer, 默认100): 返回数量限制
- `offset` (integer, 默认0): 偏移量

### 4. `check_curated_news_exists`
检查标题是否已存在

**参数**:
- `title` (string, 必需): 要检查的标题

---

## n8n工作流示例

### 工作流1: 每2小时提炼并保存精选新闻

**步骤**:

1. **Schedule Trigger** (每2小时触发)
   - Interval: Hours = 2

2. **HTTP Request** (获取最近2小时新闻)
   - Method: GET
   - URL: `http://your-server:5000/api/recent_news?hours=2`
   - 获取原始新闻列表

3. **AI Agent** (分析并提炼新闻)
   - Model: GPT-4 / Claude 3.5
   - **提示词**:
   ```
   分析以下新闻列表,挑选出最感兴趣的15条新闻(AI、数码、新能源、国际政治、投资市场)。
   
   对每条选中的新闻:
   1. 生成一个简洁的标题(中文)
   2. 返回原始新闻ID
   
   输出JSON格式:
   [
     {
       "title": "AI生成的新标题",
       "source_news_id": 原始新闻ID
     }
   ]
   ```

4. **Loop Over Items** (遍历每条新闻)

5. **MCP Tool** (检查并添加精选新闻)
   - Tool: `check_curated_news_exists`
   - 检查标题是否存在
   
6. **IF** (条件判断)
   - 如果不存在,调用 `add_curated_news` 添加

### 工作流2: 为精选新闻生成摘要

**步骤**:

1. **Schedule Trigger** (每小时触发)
   - Interval: Hours = 1

2. **HTTP Request** (获取没有摘要的精选新闻)
   - Method: GET
   - URL: `http://your-server:5000/api/curated_news`
   - 过滤条件: `summary IS NULL`

3. **Loop Over Items** (遍历每条新闻)

4. **HTTP Request** (获取原始新闻内容)
   - 根据 `source_news_id` 获取原始新闻详情

5. **AI Agent** (生成摘要)
   - Model: GPT-4 / Claude 3.5
   - **提示词**:
   ```
   根据以下新闻内容,生成一段200字以内的摘要:
   
   标题: {{原始新闻标题}}
   内容: {{原始新闻内容}}
   
   要求:
   - 简洁明了
   - 突出关键信息
   - 使用中文
   ```

6. **HTTP Request** (更新摘要)
   - Method: PUT
   - URL: `http://your-server:5000/api/curated_news/{{id}}/summary`
   - Body: `{"summary": "AI生成的摘要"}`
   - Headers: `X-API-Key: your-api-key`

---

## 使用场景

### 场景1: 定时新闻过滤
- 每2小时自动获取最新新闻
- AI筛选出感兴趣的内容
- 自动去重并保存

### 场景2: 延迟摘要生成
- 先保存标题和来源ID
- 后续异步生成详细摘要
- 避免阻塞主流程

### 场景3: 个性化新闻推荐
- 根据用户兴趣定制筛选规则
- 持续积累用户感兴趣的内容
- 形成个人化的新闻库

---

## 数据库维护

### 查看AI精选新闻数量
```sql
SELECT COUNT(*) FROM curated_news;
```

### 查看最近添加的精选新闻
```sql
SELECT * FROM curated_news
ORDER BY created_at DESC
LIMIT 20;
```

### 查看没有摘要的新闻
```sql
SELECT id, title, source_news_id
FROM curated_news
WHERE summary IS NULL OR summary = '';
```

### 删除旧的精选新闻(可选)
```sql
DELETE FROM curated_news
WHERE created_at < datetime('now', '-30 days');
```

---

## API认证

所有POST/PUT/DELETE操作都需要在请求头中包含API密钥:

```http
X-API-Key: your-api-key
```

API密钥在 `.env` 文件中配置:

```env
API_KEY=your-secure-api-key-here
```

---

## 故障排查

### 问题1: 数据库表不存在
**解决**: 重启应用,数据库会自动创建 `curated_news` 表

### 问题2: 原始新闻ID不存在
**错误**: `原始新闻ID 123 不存在`
**解决**: 确保 `source_news_id` 在 `news` 表中存在

### 问题3: 标题重复
**行为**: 如果标题已存在,会自动更新记录而不是创建新记录
**原因**: 标题有唯一索引,用于去重

### 问题4: API认证失败
**错误**: `401 Unauthorized`
**解决**: 检查请求头是否包含正确的 `X-API-Key`

---

## 最佳实践

1. **标题生成**: 使用AI生成简洁、有吸引力的标题
2. **批量操作**: 使用批量API提高效率
3. **异步摘要**: 先保存标题,后续异步生成摘要
4. **定期清理**: 定期清理过期的精选新闻
5. **错误处理**: 在n8n工作流中添加错误处理节点

---

## 相关文件

- [src/database.py](src/database.py) - 数据库操作方法
- [src/web/app.py](src/web/app.py) - Web API端点
- [mcp_server.py](mcp_server.py) - MCP工具定义
- [API_AUTH.md](API_AUTH.md) - API认证说明

---

**最后更新**: 2026-01-08
