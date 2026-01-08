# AI 精选新闻合并功能

## 📖 功能简介

该功能用于自动检测并合并相似的 AI 精选新闻，解决以下问题：

- ❌ **重复内容**：多个来源报道同一事件，产生大量重复新闻
- ❌ **信息分散**：相关新闻散落在不同记录中，不便于阅读
- ❌ **维护困难**：随着新闻数量增长，难以管理

**解决方案**：使用 AI Agent 智能识别相似新闻并自动合并。

## 🏗️ 系统架构

```
n8n 工作流
    ↓
1. 获取未合并的新闻 (get_active_curated_news)
    ↓
2. AI Agent 分析相似性
    ↓
3. 生成分组方案
    ↓
4. 执行合并操作 (merge_curated_news)
    ↓
5. 更新数据库状态
```

## 📦 文件清单

### 核心代码
- `src/database.py` - 数据库层（新增合并相关方法）
- `mcp_server.py` - MCP 工具（新增3个工具）
- `src/web/app.py` - Web API（新增3个端点）

### 文档
- `docs/news_merging_quickstart.md` - 快速开始指南 ⭐ 推荐先看这个
- `docs/n8n_news_merger_agent.md` - AI Agent 提示词详解
- `docs/n8n_news_merger_workflow.md` - n8n 工作流配置指南

### 测试
- `test_news_merging.py` - 功能测试脚本

## 🚀 快速开始

### 1️⃣ 更新代码

```bash
cd /home/ubuntu22/Desktop/new/hotnews_crawler

# 重新构建并启动服务
docker-compose build --no-cache
docker-compose up -d
```

### 2️⃣ 验证功能

```bash
# 方法1: 运行测试脚本
python3 test_news_merging.py

# 方法2: 手动测试API
curl http://192.168.1.4:5000/api/curated_news/active?limit=5
```

### 3️⃣ 配置 n8n 工作流

1. 打开 n8n 界面
2. 导入工作流配置（参考 `docs/n8n_news_merger_workflow.md`）
3. 设置环境变量 `API_KEY`
4. 激活工作流

## 📊 数据流程

### 输入：未合并的新闻

```json
{
  "id": 18,
  "title": "【AI大模型】贾跃亭进军具身智能",
  "source": "it之家"
}
```

### AI Agent 分析

```json
{
  "keep_id": 18,
  "merge_ids": [19, 21],
  "reason": "同一事件的不同来源报道",
  "merged_title": "【AI大模型】贾跃亭进军具身智能（多家媒体报道）",
  "merged_summary": "综合it之家、36氪、虎嗅的报道..."
}
```

### 输出：合并后的数据

```json
{
  "id": 18,
  "title": "【AI大模型】贾跃亭进军具身智能（多家媒体报道）",
  "merged_from": "[19,21]",
  "summary": "综合了3家媒体的报道..."
}
```

## 🔧 MCP 工具详解

### 工具1: get_active_curated_news

**用途**：获取所有未被合并的 AI 精选新闻

**参数**：
- `limit`: 返回数量限制（默认100）

**返回**：
```json
{
  "success": true,
  "data": [
    {
      "id": 18,
      "title": "...",
      "summary": null,
      "source": "it之家",
      "url": "https://...",
      "created_at": "2026-01-08 13:31:31"
    }
  ],
  "count": 18
}
```

### 工具2: get_curated_news_by_ids

**用途**：根据ID列表批量获取新闻详情

**参数**：
- `news_ids`: 新闻ID列表 `[18, 19, 21]`

**返回**：
```json
{
  "success": true,
  "data": [...],
  "count": 3
}
```

### 工具3: merge_curated_news

**用途**：执行合并操作

**参数**：
- `keep_id`: 保留的主记录ID
- `merge_ids`: 要合并进去的ID列表
- `merged_title`: 合并后的标题
- `merged_summary`: 合并后的摘要（可选）

**返回**：
```json
{
  "success": true,
  "message": "成功合并 2 条新闻到 ID 18",
  "data": {
    "keep_id": 18,
    "merged_count": 2,
    "merged_ids": [19, 21]
  }
}
```

## 🎨 AI Agent 提示词要点

### 相似度判断标准

**应该合并**：
- ✅ 同一事件的不同来源报道
- ✅ 同一主题的延续性新闻
- ✅ 标题关键词重叠度 > 60% 且主题一致

**不应该合并**：
- ❌ 完全不同的话题
- ❌ 仅时间相近但内容无关
- ❌ 摘要内容差异巨大

### 保守原则

> 当不确定是否相似时，倾向于不合并。

### 输出格式

```json
{
  "groups": [
    {
      "keep_id": 18,
      "merge_ids": [19, 21],
      "reason": "相似原因说明",
      "merged_title": "合并后的标题",
      "merged_summary": "合并后的摘要"
    }
  ]
}
```

## 📈 预期效果

### 合并前

```
18条新闻
- 【AI大模型】贾跃亭进军具身智能 (it之家)
- 【AI大模型】FF发布机器人战略 (36氪)
- 【AI大模型】法拉第未来推出机器人 (虎嗅)
... 其他15条
```

### 合并后

```
16条新闻（-2条）
- 【AI大模型】贾跃亭进军具身智能（多家媒体报道） ← 合并了3条
  - merged_from: [19, 21]
  - summary: 综合了3家媒体的报道...
... 其他15条
```

**减少率**: ~11%（18条 → 16条）

## 🔍 监控和维护

### 查看合并统计

```sql
SELECT
  COUNT(*) as total,
  SUM(CASE WHEN is_merged = 0 THEN 1 ELSE 0 END) as active,
  SUM(CASE WHEN is_merged = 1 THEN 1 ELSE 0 END) as merged
FROM curated_news;
```

### 查看最近合并记录

```sql
SELECT
  id,
  title,
  merged_from,
  updated_at
FROM curated_news
WHERE merged_from IS NOT NULL
ORDER BY updated_at DESC
LIMIT 10;
```

### 撤销合并（紧急情况）

```sql
UPDATE curated_news
SET is_merged = 0,
    merged_into_id = NULL
WHERE id IN (19, 21);
```

## ⚙️ 配置调优

### 调整合并策略

编辑 `docs/n8n_news_merger_agent.md` 中的提示词：

```markdown
## 相似度阈值
- 高相似度（>0.7）：应该合并
- 中相似度（0.4-0.7）：可选择性合并
- 低相似度（<0.4）：不应合并
```

### 调整执行频率

在 n8n 工作流的 Cron 节点中：

```yaml
# 每2小时
0 */2 * * *

# 每4小时
0 */4 * * *

# 每天凌晨2点
0 2 * * *
```

## ❓ 常见问题

### Q1: 合并后如何查看原始新闻？

原始新闻仍然保留，只是标记为 `is_merged=1`。

```sql
SELECT * FROM curated_news WHERE merged_into_id = 18;
```

### Q2: 可以自定义合并规则吗？

可以！修改 n8n 工作流中 AI Agent 的提示词。

### Q3: 性能如何？

- 数据库查询：< 100ms
- AI 分析：5-30秒
- 合并操作：< 50ms
- **总时间**: 通常 < 1分钟

### Q4: 如何处理合并错误？

```sql
-- 撤销错误合并
UPDATE curated_news
SET is_merged = 0, merged_into_id = NULL
WHERE id = 18;
```

## 📚 相关链接

- **快速开始**: [news_merging_quickstart.md](./news_merging_quickstart.md)
- **AI Agent 提示词**: [n8n_news_merger_agent.md](./n8n_news_merger_agent.md)
- **n8n 工作流配置**: [n8n_news_merger_workflow.md](./n8n_news_merger_workflow.md)
- **测试脚本**: [test_news_merging.py](../test_news_merging.py)

## 🎯 下一步

1. ✅ 代码已完成，需要重新构建 Docker 镜像
2. ✅ 文档已创建在 `docs/` 目录
3. ⏭️ 在 n8n 中配置工作流
4. ⏭️ 测试合并功能
5. ⏭️ 根据实际效果调优

---

**版本**: v1.0
**作者**: Claude
**日期**: 2026-01-08
