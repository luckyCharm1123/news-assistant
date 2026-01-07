# API鉴权使用指南

## 概述

系统的所有敏感API操作都需要API密钥鉴权，以确保安全性。

## 配置API密钥

### 步骤1：修改.env文件

在项目根目录下的 `.env` 文件中设置强密码：

```bash
# 复制示例文件
cp .env.example .env

# 编辑.env文件，修改API_KEY为一个强密码
# 建议使用32位以上，包含大小写字母、数字和特殊字符
API_KEY=YourSecureApiKeyHere!@#$%^&*()_+2024
```

### 步骤2：重启服务

修改API密钥后需要重启服务：

```bash
# 重启Web服务
docker-compose restart

# 重启MCP服务
./mcp_service.sh restart
```

## API鉴权方式

支持3种方式提供API密钥：

### 方式1：使用 X-API-Key Header（推荐）

```bash
curl -X POST http://localhost:5000/api/news/123/decrease_popularity \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YourSecureApiKeyHere!@#$%^&*()_+2024" \
  -d '{"decrease_amount": 1}'
```

### 方式2：使用 Authorization Bearer Token

```bash
curl -X POST http://localhost:5000/api/news/123/decrease_popularity \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YourSecureApiKeyHere!@#$%^&*()_+2024" \
  -d '{"decrease_amount": 1}'
```

### 方式3：使用Query Parameter（不推荐，仅用于测试）

```bash
curl -X POST "http://localhost:5000/api/news/123/decrease_popularity?api_key=YourSecureApiKeyHere!@#$%^&*()_+2024" \
  -H "Content-Type: application/json" \
  -d '{"decrease_amount": 1}'
```

## 需要鉴权的API

以下API端点需要鉴权：

### 1. 降低单条新闻关注度
- **端点**: `POST /api/news/<id>/decrease_popularity`
- **需要鉴权**: ✅ 是

### 2. 批量降低新闻关注度
- **端点**: `POST /api/news/batch_decrease_popularity`
- **需要鉴权**: ✅ 是

## 无需鉴权的API

以下API端点公开访问：

### 1. 获取最近新闻
- **端点**: `GET /api/recent_news`
- **需要鉴权**: ❌ 否

### 2. 获取高关注度新闻
- **端点**: `GET /api/news/high_popularity`
- **需要鉴权**: ❌ 否

### 3. 首页
- **端点**: `GET /`
- **需要鉴权**: ❌ 否

### 4. 健康检查
- **端点**: `GET /health`
- **需要鉴权**: ❌ 否

## MCP服务鉴权

MCP服务的工具调用也需要鉴权：

### 通过MCP调用工具（需要鉴权的工具）

```bash
curl -X POST http://localhost:3001/tools/call \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YourSecureApiKeyHere!@#$%^&*()_+2024" \
  -d '{
    "name": "decrease_news_popularity",
    "arguments": {
      "news_id": 123,
      "decrease_amount": 1
    }
  }'
```

### 需要鉴权的MCP工具

1. `decrease_news_popularity` - 降低新闻关注度
2. `batch_decrease_popularity` - 批量降低关注度

### 无需鉴权的MCP工具

1. `get_recent_news` - 获取最近新闻
2. `get_high_popularity_news` - 获取高关注度新闻

## 错误响应

### 缺少API密钥

```json
{
  "success": false,
  "error": "缺少API密钥，请在请求头中提供 X-API-Key 或 Authorization: Bearer <token>"
}
```

**HTTP状态码**: 401 Unauthorized

### API密钥无效

```json
{
  "success": false,
  "error": "API密钥无效"
}
```

**HTTP状态码**: 403 Forbidden

## 在n8n中配置

### HTTP Request节点配置

**方法1：使用Headers**

在HTTP Request节点的Headers部分添加：
```
X-API-Key: YourSecureApiKeyHere!@#$%^&*()_+2024
```

**方法2：使用Authentication**

1. 选择 `Generic Credential Type`
2. 选择 `Header Auth`
3. Header Name: `X-API-Key`
4. Header Value: 你的API密钥

### 完整示例

降低新闻关注度：

```json
{
  "method": "POST",
  "url": "http://localhost:5000/api/news/123/decrease_popularity",
  "authentication": "genericCredentialType",
  "genericAuthType": {
    "name": "Header Auth",
    "id": "your-credential-id"
  },
  "sendHeaders": true,
  "headerParameters": {
    "parameters": [
      {
        "name": "Content-Type",
        "value": "application/json"
      },
      {
        "name": "X-API-Key",
        "value": "YourSecureApiKeyHere!@#$%^&*()_+2024"
      }
    ]
  },
  "sendBody": true,
  "bodyParameters": {
    "parameters": [
      {
        "name": "decrease_amount",
        "value": 1
      }
    ]
  },
  "jsonParameters": true
}
```

## 安全建议

1. **使用强密码**: 至少32位，包含大小写字母、数字和特殊字符
2. **定期更换**: 建议每月更换API密钥
3. **保密**: 不要将API密钥提交到公开的代码仓库
4. **环境变量**: 使用 `.env` 文件，并将其添加到 `.gitignore`
5. **传输加密**: 在生产环境使用HTTPS协议
6. **访问控制**: 配置防火墙规则，限制API访问来源IP

## 生成强密码示例

```bash
# 使用openssl生成32位随机密钥
openssl rand -base64 32

# 或使用python生成
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```
