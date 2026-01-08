# API参考文档 - 一次性获取所有AI精选新闻

## ⚠️ 重要说明：API密钥配置

**所有需要修改数据的API（POST/PUT/DELETE）都需要API密钥认证！**

### API密钥位置
```bash
# 项目根目录的 .env 文件
API_KEY="8f4b2e1a9c3d5f7082e6d1b4a9c8f3e27d6b5a1c9e8d2f4b3a6c9e1d8f7b2a5c"
```

### 认证方式
在HTTP请求头中添加：
```
X-API-Key: your_api_key_here
```

### 是否需要认证

| API端点 | 方法 | 需要认证 |
|---------|------|---------|
| /api/curated_news | GET | ❌ 不需要 |
| /api/curated_news/{id} | GET | ❌ 不需要 |
| /api/curated_news/active | GET | ❌ 不需要 |
| /api/curated_news | POST | ✅ **需要** |
| /api/curated_news/batch | POST | ✅ **需要** |
| /api/curated_news/{id}/summary | PUT | ✅ **需要** |
| /api/curated_news/{id} | DELETE | ✅ **需要** |
| /api/curated_news/check | POST | ✅ **需要** |
| /api/curated_news/merge | POST | ✅ **需要** |

**简单记忆**：
- 📖 **读取数据** (GET) → 无需认证
- ✏️ **修改数据** (POST/PUT/DELETE) → 必须认证

---

## 📌 获取所有AI精选新闻

### 方法1: 通过MCP工具 (推荐用于n8n)
*注意：MCP工具会自动处理API密钥，无需手动配置*

**工具名称**: `get_curated_news`

**参数**:
```json
{
  "limit": "all",    // 或 "0" 或不传参数，都表示获取所有记录
  "offset": 0        // 可选，偏移量，默认0
}
```

**使用示例**:
```json
{
  "limit": "all"
}
```

**返回格式**:
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "title": "【AI大模型】AI搜索战局生变...",
      "summary": "摘要内容",
      "source_news_id": 24,
      "created_at": "2025-01-09 10:00:00",
      "updated_at": "2025-01-09 10:00:00",
      "original_title": "原始新闻标题",
      "source": "36氪-热榜",
      "url": "https://...",
      "crawled_at": "2025-01-09 09:00:00"
    }
  ],
  "total": 15
}
```

---

### 方法2: 通过HTTP REST API

#### 2.1 获取所有AI精选新闻

**端点**: `GET /api/curated_news`

**基础URL**: `http://[2409:8a28:2580:9e81::7d7]:5000`

**请求参数**:
```
limit=all          // 获取所有记录
offset=0           // 可选，偏移量
```

**完整示例**:
```bash
curl -X GET "http://[2409:8a28:2580:9e81::7d7]:5000/api/curated_news?limit=all"
```

**使用cURL**:
```bash
# 获取所有记录
curl "http://[2409:8a28:2580:9e81::7d7]:5000/api/curated_news?limit=all"

# 获取前20条
curl "http://[2409:8a28:2580:9e81::7d7]:5000/api/curated_news?limit=20"

# 分页获取，从第21条开始，获取20条
curl "http://[2409:8a28:2580:9e81::7d7]:5000/api/curated_news?limit=20&offset=20"
```

**使用Python requests**:
```python
import requests

# 获取所有AI精选新闻
response = requests.get(
    "http://[2409:8a28:2580:9e81::7d7]:5000/api/curated_news",
    params={"limit": "all"}
)

data = response.json()
if data['success']:
    curated_news = data['data']
    total = data['total']
    print(f"共获取 {total} 条AI精选新闻")

    for news in curated_news:
        print(f"ID: {news['id']}")
        print(f"标题: {news['title']}")
        print(f"摘要: {news['summary']}")
        print(f"来源: {news['source']}")
        print("-" * 50)
```

**使用JavaScript/fetch**:
```javascript
// 获取所有AI精选新闻
fetch('http://[2409:8a28:2580:9e81::7d7]:5000/api/curated_news?limit=all')
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      console.log(`共获取 ${data.total} 条AI精选新闻`);
      data.data.forEach(news => {
        console.log(`ID: ${news.id}`);
        console.log(`标题: ${news.title}`);
        console.log(`摘要: ${news.summary}`);
        console.log('---');
      });
    }
  });
```

#### 2.2 获取单条AI精选新闻详情

**端点**: `GET /api/curated_news/{curated_id}`

**示例**:
```bash
curl "http://[2409:8a28:2580:9e81::7d7]:5000/api/curated_news/1"
```

---

### 方法3: 获取未被合并的AI精选新闻

用于获取所有未被标记为"已合并"的新闻（适合新闻合并场景）。

**MCP工具**: `get_active_curated_news`

**HTTP端点**: `GET /api/curated_news/active`

**参数**:
```json
{
  "limit": 100    // 默认100，可调整
}
```

**cURL示例**:
```bash
curl "http://[2409:8a28:2580:9e81::7d7]:5000/api/curated_news/active?limit=100"
```

---

## 📊 返回数据结构说明

```json
{
  "success": true,          // 请求是否成功
  "data": [                 // AI精选新闻列表
    {
      "id": 1,              // AI精选新闻ID
      "title": "新闻标题",   // AI生成的标题
      "summary": "摘要",     // AI生成的摘要
      "source_news_id": 24, // 原始新闻ID
      "created_at": "时间",  // 创建时间
      "updated_at": "时间",  // 更新时间
      "original_title": "",  // 原始新闻标题
      "source": "来源",      // 原始新闻来源
      "url": "链接",         // 原始新闻URL
      "crawled_at": "时间"   // 原始新闻爬取时间
    }
  ],
  "total": 15              // 总记录数
}
```

---

## 🔒 API认证详细说明

### 如何获取API密钥

查看项目根目录的 `.env` 文件：
```bash
cat .env
```

您会看到类似这样的内容：
```
API_KEY="8f4b2e1a9c3d5f7082e6d1b4a9c8f3e27d6b5a1c9e8d2f4b3a6c9e1d8f7b2a5c"
```

### 使用API密钥的示例

#### cURL示例（需要认证的API）
```bash
# 1. 创建AI精选新闻 (需要API密钥)
curl -X POST "http://[2409:8a28:2580:9e81::7d7]:5000/api/curated_news" \
  -H "X-API-Key: 8f4b2e1a9c3d5f7082e6d1b4a9c8f3e27d6b5a1c9e8d2f4b3a6c9e1d8f7b2a5c" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "测试新闻",
    "source_news_id": 1,
    "summary": "测试摘要"
  }'

# 2. 批量添加AI精选新闻 (需要API密钥)
curl -X POST "http://[2409:8a28:2580:9e81::7d7]:5000/api/curated_news/batch" \
  -H "X-API-Key: 8f4b2e1a9c3d5f7082e6d1b4a9c8f3e27d6b5a1c9e8d2f4b3a6c9e1d8f7b2a5c" \
  -H "Content-Type: application/json" \
  -d '{
    "news_list": [
      {"title": "新闻1", "source_news_id": 1, "summary": "摘要1"},
      {"title": "新闻2", "source_news_id": 2, "summary": "摘要2"}
    ]
  }'

# 3. 合并新闻 (需要API密钥)
curl -X POST "http://[2409:8a28:2580:9e81::7d7]:5000/api/curated_news/merge" \
  -H "X-API-Key: 8f4b2e1a9c3d5f7082e6d1b4a9c8f3e27d6b5a1c9e8d2f4b3a6c9e1d8f7b2a5c" \
  -H "Content-Type: application/json" \
  -d '{
    "keep_id": 1,
    "merge_ids": [2, 3],
    "merged_title": "合并后的标题",
    "merged_summary": "合并后的摘要"
  }'
```

#### Python示例（需要认证的API）
```python
import requests

API_KEY = "8f4b2e1a9c3d5f7082e6d1b4a9c8f3e27d6b5a1c9e8d2f4b3a6c9e1d8f7b2a5c"
headers = {"X-API-Key": API_KEY}

# 创建AI精选新闻
response = requests.post(
    "http://[2409:8a28:2580:9e81::7d7]:5000/api/curated_news",
    headers=headers,
    json={
        "title": "测试新闻",
        "source_news_id": 1,
        "summary": "测试摘要"
    }
)
print(response.json())

# 批量添加
response = requests.post(
    "http://[2409:8a28:2580:9e81::7d7]:5000/api/curated_news/batch",
    headers=headers,
    json={
        "news_list": [
            {"title": "新闻1", "source_news_id": 1},
            {"title": "新闻2", "source_news_id": 2}
        ]
    }
)
print(response.json())
```

#### JavaScript示例（需要认证的API）
```javascript
const API_KEY = "8f4b2e1a9c3d5f7082e6d1b4a9c8f3e27d6b5a1c9e8d2f4b3a6c9e1d8f7b2a5c";

// 创建AI精选新闻
fetch('http://[2409:8a28:2580:9e81::7d7]:5000/api/curated_news', {
  method: 'POST',
  headers: {
    'X-API-Key': API_KEY,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    title: "测试新闻",
    source_news_id: 1,
    summary: "测试摘要"
  })
})
.then(res => res.json())
.then(data => console.log(data));
```

#### 不需要认证的API（读取数据）
```bash
# ✅ 无需API密钥 - 获取所有AI精选新闻
curl "http://[2409:8a28:2580:9e81::7d7]:5000/api/curated_news?limit=all"

# ✅ 无需API密钥 - 获取单条新闻
curl "http://[2409:8a28:2580:9e81::7d7]:5000/api/curated_news/1"

# ✅ 无需API密钥 - 获取未合并的新闻
curl "http://[2409:8a28:2580:9e81::7d7]:5000/api/curated_news/active"
```

---

## 🎯 快速参考

| 需求 | HTTP方法 | 端点 | 参数 |
|------|---------|------|------|
| 获取所有AI精选 | GET | /api/curated_news | limit=all |
| 获取前N条 | GET | /api/curated_news | limit=N |
| 分页获取 | GET | /api/curated_news | limit=N&offset=M |
| 获取单条详情 | GET | /api/curated_news/{id} | - |
| 获取未合并的 | GET | /api/curated_news/active | limit=N |

---

## 💡 使用建议

1. **一次性获取所有数据**: 使用 `limit=all`
2. **大数据量分页**: 使用 `limit` 和 `offset` 组合
3. **新闻合并场景**: 使用 `/api/curated_news/active` 获取未合并的新闻
4. **n8n集成**: 使用MCP工具 `get_curated_news`，参数设为 `{"limit": "all"}`
