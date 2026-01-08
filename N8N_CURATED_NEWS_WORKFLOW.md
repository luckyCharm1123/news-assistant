# n8n工作流配置 - AI精选新闻系统

## 概述

这个工作流每2小时自动运行一次,从原始新闻中筛选出用户最感兴趣的15条新闻,并保存到 `curated_news` 表中供后续使用。

---

## 工作流1: 新闻筛选与保存

### 节点配置

#### 1. Schedule Trigger (定时触发)
- **触发间隔**: 每2小时
- **配置**:
  ```
  Interval: Hours = 2
  ```

#### 2. HTTP Request (获取最近新闻)
- **Method**: GET
- **URL**: `http://192.168.1.4:5000/api/recent_news`
- **Query Parameters**:
  - `hours`: `2`
- **Response Format**: JSON

#### 3. MCP Tool (调用get_recent_news)
或者直接使用MCP工具获取:
- **Tool**: `get_recent_news`
- **Parameters**:
  ```json
  {
    "hours": 2
  }
  ```

#### 4. AI Agent (智能筛选)
- **Model**: GPT-4 / Claude 3.5 Sonnet
- **Temperature**: 0.7
- **Prompt**: 使用 [n8n_agent_prompt.md](n8n_agent_prompt.md) 中的完整提示词

**关键配置**:
- 确保AI输出纯JSON格式
- 设置输出变量名为 `ai_result`

#### 5. Code (解析JSON结果)
将AI的输出解析为n8n可用的格式:

```javascript
// 解析AI输出的JSON
const aiOutput = $input.first().json;
let newsList = [];

try {
  // 如果AI输出是纯文本JSON
  const textContent = aiOutput.text || aiOutput.output || JSON.stringify(aiOutput);
  
  // 提取JSON部分
  const jsonMatch = textContent.match(/\{[\s\S]*\}/);
  if (jsonMatch) {
    const parsed = JSON.parse(jsonMatch[0]);
    newsList = parsed.news_list || [];
  }
} catch (error) {
  console.error('JSON解析失败:', error);
}

return newsList.map(item => ({
  json: item
}));
```

#### 6. Loop Over Items (遍历每条新闻)
- **Mode**: Each Item
- **Settings**: 默认配置

#### 7. MCP Tool (批量保存到数据库)
- **Tool**: `batch_add_curated_news`
- **Parameters**:
  ```json
  {
    "news_list": {{ $json.items }}
  }
  ```

**或者使用HTTP Request**:
- **Method**: POST
- **URL**: `http://192.168.1.4:5000/api/curated_news/batch`
- **Headers**:
  - `Content-Type`: `application/json`
  - `X-API-Key`: `your-api-key-here`
- **Body**:
  ```json
  {
    "news_list": {{ $json }}
  }
  ```

#### 8. Set (处理结果)
记录成功/失败信息:
```json
{
  "status": "completed",
  "timestamp": {{ $now }},
  "message": "精选新闻已保存"
}
```

---

## 工作流2: 为精选新闻生成摘要

### 节点配置

#### 1. Schedule Trigger (定时触发)
- **触发间隔**: 每小时
- **配置**:
  ```
  Interval: Hours = 1
  ```

#### 2. HTTP Request (获取没有摘要的精选新闻)
- **Method**: GET
- **URL**: `http://192.168.1.4:5000/api/curated_news`
- **Query Parameters**:
  - `limit`: `50`

#### 3. Code (过滤没有摘要的新闻)
```javascript
// 过滤出summary为空的新闻
const allNews = $input.all();
const noSummaryNews = allNews.filter(item => {
  const summary = item.json.summary;
  return !summary || summary.trim() === '' || summary === 'null';
});

return noSummaryNews;
```

#### 4. IF (检查是否有新闻需要处理)
- **Condition**: 长度大于0
- **配置**: `{{ $json.length > 0 }}`

#### 5. Loop Over Items (遍历每条新闻)

#### 6. HTTP Request (获取原始新闻详情)
根据 `source_news_id` 获取原始新闻:
- **Method**: GET
- **URL**: `http://192.168.1.4:5000/api/news/{{ $json.source_news_id }}`

#### 7. AI Agent (生成摘要)
- **Model**: GPT-4 / Claude 3.5
- **Temperature**: 0.5
- **Prompt**:
```
根据以下新闻内容,生成一段200字以内的中文摘要:

标题: {{ $json.title }}
来源: {{ $json.source }}
原始内容: {{ $json.url }}

要求:
- 简洁明了,突出关键信息
- 使用中文
- 200字以内
- 不要添加主观评价
```

#### 8. HTTP Request (更新摘要)
- **Method**: PUT
- **URL**: `http://192.168.1.4:5000/api/curated_news/{{ $json.id }}/summary`
- **Headers**:
  - `Content-Type`: `application/json`
  - `X-API-Key`: `your-api-key-here`
- **Body**:
  ```json
  {
    "summary": {{ $json.ai_summary }}
  }
  ```

---

## n8n工作流JSON导出

### 工作流1: 筛选并保存精选新闻

```json
{
  "name": "AI精选新闻-每2小时筛选",
  "nodes": [
    {
      "parameters": {
        "rule": {
          "interval": [{ "field": "hours", "hoursInterval": 2 }]
        }
      },
      "name": "Schedule Trigger",
      "type": "n8n-nodes-base.scheduleTrigger",
      "position": [250, 300]
    },
    {
      "parameters": {
        "method": "GET",
        "url": "http://192.168.1.4:5000/api/recent_news",
        "queryParameters": {
          "parameters": [{ "name": "hours", "value": "2" }]
        }
      },
      "name": "获取最近新闻",
      "type": "n8n-nodes-base.httpRequest",
      "position": [450, 300]
    },
    {
      "parameters": {
        "model": "gpt-4",
        "prompt": "=$node['获取最近新闻'].json",
        "options": {
          "temperature": 0.7,
          "systemMessage": "你是【热点情报员】...\n(完整提示词见 n8n_agent_prompt.md)"
        }
      },
      "name": "AI Agent",
      "type": "@n8n/n8n-nodes-langchain.lmChat",
      "position": [650, 300]
    },
    {
      "parameters": {
        "jsCode": "// 解析AI输出的JSON\nconst aiOutput = $input.first().json;\nlet newsList = [];\n\ntry {\n  const textContent = aiOutput.text || JSON.stringify(aiOutput);\n  const jsonMatch = textContent.match(/\\{[\\s\\S]*\\}/);\n  if (jsonMatch) {\n    const parsed = JSON.parse(jsonMatch[0]);\n    newsList = parsed.news_list || [];\n  }\n} catch (error) {\n  console.error('JSON解析失败:', error);\n}\n\nreturn newsList.map(item => ({ json: item }));"
      },
      "name": "解析JSON",
      "type": "n8n-nodes-base.code",
      "position": [850, 300]
    },
    {
      "parameters": {
        "method": "POST",
        "url": "http://192.168.1.4:5000/api/curated_news/batch",
        "authentication": "genericCredentialType",
        "genericAuthType": "httpHeaderAuth",
        "headerParameters": {
          "parameters": [
            { "name": "Content-Type", "value": "application/json" },
            { "name": "X-API-Key", "value": "your-api-key" }
          ]
        },
        "jsonParameters": true,
        "bodyParametersJson": "={{ $json }}"
      },
      "name": "保存到数据库",
      "type": "n8n-nodes-base.httpRequest",
      "position": [1050, 300]
    }
  ],
  "connections": {
    "Schedule Trigger": {
      "main": [[{ "node": "获取最近新闻", "type": "main", "index": 0 }]]
    },
    "获取最近新闻": {
      "main": [[{ "node": "AI Agent", "type": "main", "index": 0 }]]
    },
    "AI Agent": {
      "main": [[{ "node": "解析JSON", "type": "main", "index": 0 }]]
    },
    "解析JSON": {
      "main": [[{ "node": "保存到数据库", "type": "main", "index": 0 }]]
    }
  }
}
```

---

## API密钥配置

### 在.env文件中设置

```env
API_KEY=your-secure-api-key-here
```

### 在n8n中使用

创建HTTP Header Auth凭证:
- **Name**: `X-API-Key`
- **Value**: 你的API密钥

---

## 测试工作流

### 手动测试步骤

1. **测试获取新闻**:
   ```bash
   curl http://192.168.1.4:5000/api/recent_news?hours=2
   ```

2. **测试保存精选新闻**:
   ```bash
   curl -X POST http://192.168.1.4:5000/api/curated_news/batch \
     -H "Content-Type: application/json" \
     -H "X-API-Key: your-api-key" \
     -d '{
       "news_list": [
         {
           "title": "【测试】这是一条测试新闻",
           "source_news_id": 1
         }
       ]
     }'
   ```

3. **验证保存结果**:
   ```bash
   curl http://192.168.1.4:5000/api/curated_news
   ```

---

## 常见问题

### Q1: AI输出格式不正确
**解决方案**:
- 在Prompt中明确要求输出纯JSON
- 使用Code节点解析和清理JSON
- 添加错误处理和重试机制

### Q2: 标题重复
**原因**: 数据库会自动去重,重复的标题会更新而不是新增
**解决方案**: 这是预期行为,确保每条精选新闻的标题唯一

### Q3: source_news_id不存在
**错误**: `原始新闻ID xxx 不存在`
**原因**: 原始新闻可能已被清理
**解决方案**: 
- 检查数据保留期配置
- 确保在原始新闻被清理前完成精选

### Q4: API认证失败
**错误**: `401 Unauthorized`
**解决方案**:
- 检查 `.env` 文件中的 API_KEY
- 确保n8n的HTTP请求头包含正确的密钥

---

## 性能优化建议

1. **批量操作**: 使用 `batch_add_curated_news` 而不是循环调用 `add_curated_news`
2. **异步处理**: 将摘要生成放在单独的工作流中异步执行
3. **错误处理**: 添加错误捕获和重试逻辑
4. **日志记录**: 记录每次运行的结果和统计信息

---

## 相关文档

- [n8n_agent_prompt.md](n8n_agent_prompt.md) - AI Agent提示词
- [CURATED_NEWS_GUIDE.md](CURATED_NEWS_GUIDE.md) - API文档
- [N8N_MCP_SETUP.md](N8N_MCP_SETUP.md) - MCP配置指南

---

**最后更新**: 2026-01-08
