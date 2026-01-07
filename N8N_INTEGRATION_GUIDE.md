# n8n集成配置指南

## 快速配置步骤

### 步骤1：获取API密钥

在服务器上执行：
```bash
cd ~/hotnews_crawler
cat .env
```

你会看到类似这样的输出：
```
API_KEY=your_secure_api_key_here_please_change_this_to_a_strong_password_2024
```

复制这个API密钥值。

---

### 步骤2：在n8n中配置HTTP Request节点

#### 基本配置

| 字段 | 值 |
|------|-----|
| **Method** | POST |
| **URL** | `http://192.168.1.132:3001/tools/call` |

#### Authentication配置（重要！）

有两种方式配置API密钥：

**方式A：使用Headers（推荐）**

在 **Headers** 部分点击 **Add Header**，添加两个header：

| Name | Value |
|------|-------|
| `Content-Type` | `application/json` |
| `X-API-Key` | `your_secure_api_key_here_please_change_this_to_a_strong_password_2024` |

**方式B：使用Generic Credential Type**

1. **Authentication** 选择：`Generic Credential Type`
2. **Generic Auth Type** 选择：`Header Auth`
3. **Header Name** 输入：`X-API-Key`
4. **Header Value** 输入：你的API密钥

然后还需要在Headers中添加：
| Name | Value |
|------|-------|
| `Content-Type` | `application/json` |

#### Body配置

**Body Type**: `JSON`

**JSON Body** 输入：
```json
{
  "name": "get_recent_news",
  "arguments": {
    "hours": 2
  }
}
```

---

## 完整的JSON配置示例

你可以直接在n8n的HTTP Request节点中粘贴以下配置：

### 示例1：获取最近2小时新闻

```json
{
  "method": "POST",
  "url": "http://192.168.1.132:3001/tools/call",
  "authentication": "none",
  "sendHeaders": true,
  "headerParameters": {
    "parameters": [
      {
        "name": "Content-Type",
        "value": "application/json"
      },
      {
        "name": "X-API-Key",
        "value": "your_secure_api_key_here_please_change_this_to_a_strong_password_2024"
      }
    ]
  },
  "sendBody": true,
  "bodyParameters": {
    "parameters": []
  },
  "jsonBody": "={\n  \"name\": \"get_recent_news\",\n  \"arguments\": {\n    \"hours\": 2\n  }\n}",
  "options": {}
}
```

### 示例2：获取高关注度新闻

```json
{
  "name": "get_high_popularity_news",
  "arguments": {
    "limit": 20,
    "min_popularity": 3
  }
}
```

### 示例3：降低新闻关注度

```json
{
  "name": "decrease_news_popularity",
  "arguments": {
    "news_id": 123,
    "decrease_amount": 1
  }
}
```

---

## 测试步骤

### 1. 在服务器上测试API

首先确保MCP服务正常运行：

```bash
# 检查服务状态
docker compose ps

# 应该看到两个容器都在运行
```

测试API（在服务器上执行）：

```bash
# 获取API密钥
export API_KEY=$(cat ~/hotnews_crawler/.env | grep API_KEY | cut -d'=' -f2)

# 测试MCP服务
curl -X POST http://localhost:3001/tools/call \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "name": "get_recent_news",
    "arguments": {"hours": 2}
  }'
```

如果成功，应该返回类似：
```json
{
  "success": true,
  "data": [...],
  "count": 10,
  "hours": 2
}
```

### 2. 从外部测试

在你的电脑上（不是服务器）：

```bash
# 替换为你的服务器IP
curl -X POST http://192.168.1.132:3001/tools/call \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_secure_api_key_here_please_change_this_to_a_strong_password_2024" \
  -d '{
    "name": "get_recent_news",
    "arguments": {"hours": 2}
  }'
```

### 3. 在n8n中测试

1. 打开n8n
2. 创建一个新的Workflow
3. 添加 **HTTP Request** 节点
4. 按照上面的配置填写
5. 点击 **Test Step** 测试节点

---

## 故障排查

### 问题1：401 Unauthorized

**原因**：API密钥缺失或错误

**解决方案**：
1. 检查服务器上的API密钥：`cat ~/hotnews_crawler/.env`
2. 确保n8n中的X-API-Key header值完全一致
3. 检查header名称是否正确：`X-API-Key`（大小写敏感）

### 问题2：连接被拒绝

**原因**：MCP服务未运行或端口未开放

**解决方案**：
```bash
# 检查MCP服务状态
docker compose ps
docker compose logs mcp-server

# 确保端口3001已开放
sudo ufw allow 3001/tcp

# 如果使用云服务器，检查安全组
```

### 问题3：返回"未授权"

**错误信息**：
```json
{
  "success": false,
  "error": "未授权：缺少或无效的API密钥"
}
```

**解决方案**：
1. 确认在Headers中添加了 `X-API-Key`
2. 检查API密钥值是否正确
3. 检查是否有拼写错误

### 问题4：返回"未知工具"

**错误信息**：
```json
{
  "success": false,
  "error": "未知工具: xxx"
}
```

**解决方案**：
检查工具名称是否正确，可用的工具有：
- `get_recent_news`
- `get_high_popularity_news`
- `decrease_news_popularity`
- `batch_decrease_popularity`

---

## 可用的MCP工具详解

### 1. get_recent_news（获取最近新闻）

**参数**：
- `hours`（可选）: 最近多少小时，默认2，最小1

**请求示例**：
```json
{
  "name": "get_recent_news",
  "arguments": {
    "hours": 2
  }
}
```

**响应示例**：
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "title": "新闻标题",
      "source": "微博",
      "url": "https://...",
      "popularity": 5,
      "crawled_at": "2026-01-07 20:00:00"
    }
  ],
  "count": 10,
  "hours": 2
}
```

### 2. get_high_popularity_news（获取高关注度新闻）

**参数**：
- `limit`（可选）: 返回条数，默认20，最大100
- `min_popularity`（可选）: 最低关注度，默认3

**请求示例**：
```json
{
  "name": "get_high_popularity_news",
  "arguments": {
    "limit": 20,
    "min_popularity": 3
  }
}
```

### 3. decrease_news_popularity（降低新闻关注度）

**参数**：
- `news_id`（必需）: 新闻ID
- `decrease_amount`（可选）: 降低数值，默认1

**请求示例**：
```json
{
  "name": "decrease_news_popularity",
  "arguments": {
    "news_id": 123,
    "decrease_amount": 1
  }
}
```

**响应示例**：
```json
{
  "success": true,
  "message": "新闻ID 123 关注度已降低 1",
  "data": {
    "id": 123,
    "title": "新闻标题",
    "current_popularity": 4,
    "decreased_by": 1
  }
}
```

### 4. batch_decrease_popularity（批量降低关注度）

**参数**：
- `news_ids`（必需）: 新闻ID数组
- `decrease_amount`（可选）: 每条新闻降低的数值，默认1

**请求示例**：
```json
{
  "name": "batch_decrease_popularity",
  "arguments": {
    "news_ids": [1, 2, 3],
    "decrease_amount": 1
  }
}
```

---

## n8n Workflow示例

### 完整工作流：获取新闻并发送到Telegram

```json
{
  "name": "获取热点新闻并发送",
  "nodes": [
    {
      "name": "获取最近新闻",
      "type": "n8n-nodes-base.httpRequest",
      "position": [250, 300],
      "parameters": {
        "method": "POST",
        "url": "http://192.168.1.132:3001/tools/call",
        "sendHeaders": true,
        "headerParameters": {
          "parameters": [
            {
              "name": "Content-Type",
              "value": "application/json"
            },
            {
              "name": "X-API-Key",
              "value": "your_api_key_here"
            }
          ]
        },
        "sendBody": true,
        "jsonBody": "={\n  \"name\": \"get_recent_news\",\n  \"arguments\": {\n    \"hours\": 2\n  }\n}"
      }
    },
    {
      "name": "Telegram",
      "type": "n8n-nodes-base.telegram",
      "position": [450, 300],
      "parameters": {
        "chatId": "your_chat_id",
        "text": "=={{ $json.data.map(n => n.title).join('\\n') }}",
        "additionalFields": {}
      }
    }
  ],
  "connections": {
    "获取最近新闻": {
      "main": [[
        {
          "node": "Telegram",
          "type": "main",
          "index": 0
        }
      ]]
    }
  }
}
```

---

## 安全建议

1. **修改默认API密钥**：
   ```bash
   nano ~/hotnews_crawler/.env
   # 修改API_KEY为强密码
   docker compose restart
   ```

2. **使用HTTPS**（生产环境）：
   配置反向代理（Nginx）并启用SSL证书

3. **限制访问**：
   在防火墙中只允许n8n服务器的IP访问3001端口

4. **定期轮换密钥**：
   每月更换API密钥

---

## 总结

✅ **关键配置点**：
1. URL: `http://192.168.1.132:3001/tools/call`
2. Method: `POST`
3. Header: `X-API-Key: [你的API密钥]`
4. Content-Type: `application/json`
5. Body: JSON格式，包含 `name` 和 `arguments`

🔍 **调试技巧**：
- 先用curl测试API是否正常
- 查看MCP服务日志：`docker compose logs -f mcp-server`
- 在n8n中启用详细日志

📚 **相关文档**：
- [API_AUTH.md](API_AUTH.md) - API鉴权详解
- [MCP_README.md](MCP_README.md) - MCP服务文档
