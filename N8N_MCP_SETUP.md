# n8n MCP 节点配置指南

## 问题说明

原有的MCP服务器存在两个问题：
1. **缺少 session_id 验证**：服务器没有检查必需的 `sessionId` 参数
2. **响应重复发送**：`handle_post_message` 已发送响应后，又返回了 JSONResponse

## 解决方案

已修复上述问题，现在需要在 n8n MCP 节点中正确配置 URL。

## n8n MCP 节点配置

### 1. 基本配置

在 n8n 的 MCP 节点中，需要提供以下信息：

- **Server URL**: `http://192.168.1.4:3001/sse`
- **Session ID**: 任意唯一字符串（例如：`n8n-session-001`）

### 2. 完整的 URL 格式

实际请求的 URL 应该是：
```
http://192.168.1.4:3001/sse?sessionId=n8n-session-001
```

### 3. n8n 配置示例

如果 n8n MCP 节点允许分别配置：

```yaml
Transport Type: SSE
Server URL: http://192.168.1.4:3001/sse
Session ID: n8n-session-001
```

如果需要手动拼接 URL：

```yaml
Server URL: http://192.168.1.4:3001/sse?sessionId=n8n-session-001
```

### 4. 验证连接

服务器启动后，你应该看到类似的日志：

```
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:3001 (Press CTRL+C to quit)
```

当 n8n 连接时，会看到：

```
INFO:__main__:SSE connection established with session_id: n8n-session-001
```

### 5. 健康检查

可以先测试健康检查端点：

```bash
curl http://192.168.1.4:3001/health
```

应该返回：
```json
{"status": "ok"}
```

## 可用工具

连接成功后，可以使用以下工具：

1. **get_recent_news** - 获取最近几小时的新闻
   - 参数: `hours` (默认: 2)

2. **decrease_news_popularity** - 降低新闻关注度
   - 参数: `news_id`, `decrease_amount` (默认: 1)

3. **batch_decrease_popularity** - 批量降低关注度
   - 参数: `news_ids`, `decrease_amount` (默认: 1)

4. **get_high_popularity_news** - 获取高关注度新闻
   - 参数: `limit` (默认: 20), `min_popularity` (默认: 3)

## 故障排查

### 错误: "Received request without session_id"

**原因**: URL 中缺少 `sessionId` 参数

**解决**: 确保 URL 格式为 `http://192.168.1.4:3001/sse?sessionId=YOUR_SESSION_ID`

### 错误: "RuntimeError: Unexpected ASGI message"

**原因**: 响应被发送了两次（已修复）

**解决**: 使用最新版本的 `mcp_server.py`

### 连接超时

**检查项**:
1. 确认服务器正在运行：`curl http://192.168.1.4:3001/health`
2. 检查防火墙设置
3. 确认 n8n 和 MCP 服务器网络互通

## 重启服务

```bash
# 停止现有服务
pkill -f mcp_server.py

# 启动服务
cd /home/ubuntu22/Desktop/new/hotnews_crawler
python mcp_server.py
```

或使用 systemd 服务：

```bash
sudo systemctl restart mcp_server
```

## 日志查看

实时查看日志：

```bash
# 如果直接运行
# 日志会直接显示在终端

# 如果使用 systemd
sudo journalctl -u mcp_server -f
```
