# n8n MCP 工具调用故障排除指南

## 问题现象
AI Agent 输出了正确的分析结果和工具调用描述，但没有实际调用 MCP 工具。

## 诊断步骤

### 1. 检查 n8n AI Agent 节点配置

#### 1.1 确认 MCP 服务器连接
在 n8n AI Agent 节点中：
- 找到 "MCP Servers" 或 "Tools" 配置项
- 确认 MCP 服务器地址：`http://localhost:3001` 或 `http://hotnews_mcp_server:3001`
- 测试连接是否成功

#### 1.2 确认 AI 模型配置
- 使用支持 function calling 的模型：
  - ✅ OpenAI GPT-3.5-turbo-0613 或更新版本
  - ✅ OpenAI GPT-4 或 GPT-4-turbo
  - ✅ Claude 3.5 Sonnet (通过 API)
  - ❌ 旧版 GPT-3.5-turbo（不支持 function calling）

#### 1.3 启用工具调用功能
在 AI Agent 节点设置中：
- 确保 "Tool Calling" 或 "Function Calling" 已启用
- 检查 "Tool Choice" 设置：
  - 设置为 `auto` 或 `required`（而不是 `none`）

### 2. 检查 MCP 工具定义

确认 MCP 工具在 n8n 中正确注册：

```bash
# 测试 MCP 服务器是否返回工具列表
curl http://localhost:3001/sse -H "Accept: text/event-stream"
```

预期结果：应该看到 `merge_curated_news` 工具在工具列表中。

### 3. 查看 n8n 执行日志

在 n8n 工作流执行后，查看执行日志：

**正常情况应该看到：**
```
AI Agent
  ├─ Thinking: 分析新闻...
  ├─ Tool Call: merge_curated_news
  │   ├─ keep_id: 27
  │   ├─ merge_ids: [23, 31]
  │   └─ merged_title: ...
  └─ Response: 合并成功
```

**当前情况（异常）：**
```
AI Agent
  ├─ Thinking: 分析新闻...
  ├─ Text: 调用 merge_curated_news 工具...
  └─ [没有实际调用工具]
```

### 4. 解决方案

#### 方案 A：修改 n8n 配置（推荐）
1. 打开 AI Agent 节点编辑
2. 找到 "Tool Choice" 配置
3. 从 `auto` 改为 `required`（强制使用工具）
4. 或者在 "Tools" 中手动添加 MCP 工具

#### 方案 B：使用 HTTP Request 节点（备用）
如果 n8n 的 AI Agent 确实不支持 MCP 工具调用，可以改用 HTTP Request 节点：

```
AI Agent → 提取参数 → HTTP Request → API 端点
```

工作流示例：
1. AI Agent：分析新闻，输出 JSON 格式的合并参数
2. Code 节点：解析 AI 输出，提取参数
3. HTTP Request：调用 `/api/curated_news/merge` 端点

#### 方案 C：使用 n8n Script
在 AI Agent 后添加一个 JavaScript 节点：

```javascript
// 解析 AI 输出并调用 API
const aiOutput = $input.first().json;

// 提取合并参数
const mergeParams = extractMergeParams(aiOutput.text);

// 调用 API
for (const params of mergeParams) {
  await $http.post({
    url: 'http://localhost:5000/api/curated_news/merge',
    headers: { 'X-API-Key': $env.API_KEY },
    body: params
  });
}

return { merged: mergeParams.length };
```

### 5. 快速测试

创建一个简单的测试工作流：

**测试工作流 1：获取新闻**
```
AI Agent
  Prompt: "调用 get_curated_news 工具获取所有精选新闻"
```

如果这个也不工作，说明 n8n 完全不支持 MCP 工具调用。

**测试工作流 2：直接调用 API**
```
HTTP Request
  Method: POST
  URL: http://localhost:5000/api/curated_news/merge
  Body:
    {
      "keep_id": 1,
      "merge_ids": [2, 4],
      "merged_title": "测试合并"
    }
```

如果这个工作，说明 API 端点正常，问题在 AI Agent 配置。

## 常见配置错误

### ❌ 错误配置 1：Tool Choice 设置为 none
**修复**：改为 `auto` 或 `required`

### ❌ 错误配置 2：使用旧版 AI 模型
**修复**：升级到 GPT-3.5-turbo-0613 或更新版本

### ❌ 错误配置 3：MCP 服务器未连接
**修复**：检查 MCP 服务器地址和端口

### ❌ 错误配置 4：AI 模型 API Key 错误
**修复**：确认 OpenAI API Key 有效且有足够额度

## 推荐的 n8n 配置

```json
{
  "modelName": "gpt-4-turbo-preview",
  "toolChoice": "auto",
  "temperature": 0.3,
  "mcpServers": [
    {
      "name": "hotnews-crawler",
      "url": "http://localhost:3001"
    }
  ]
}
```

## 联系支持

如果以上方案都不工作，可能需要：
1. 检查 n8n 版本（建议 1.0+）
2. 查看 n8n 官方文档关于 MCP 的说明
3. 在 n8n 社区提问

## 临时解决方案

在修复之前，可以使用 **手动触发**的方式：

1. 让 AI Agent 输出 JSON 格式的合并参数
2. 复制参数
3. 使用 curl 或 Postman 手动调用 API

```bash
curl -X POST http://localhost:5000/api/curated_news/merge \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "keep_id": 27,
    "merge_ids": [23, 31],
    "merged_title": "【AI大模型】英伟达H200芯片要求中国客户预付全款"
  }'
```
