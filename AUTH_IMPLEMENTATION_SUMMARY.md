# API鉴权实现总结

## 实现完成时间
2026-01-07

## 实现概述
为热点新闻爬虫系统的所有敏感API操作添加了API密钥鉴权机制，确保系统安全性。

---

## 核心文件

### 1. 环境配置文件

#### `.env` - 实际配置文件（不提交到git）
```bash
API_KEY=your_secure_api_key_here_please_change_this_to_a_strong_password_2024
```

#### `.env.example` - 配置模板（提交到git）
```bash
API_KEY=your_secure_api_key_here_please_change_this_to_a_strong_password_2024
```

**注意**：部署时需要修改为强密码！

### 2. 鉴权模块
**文件**: [src/auth.py](src/auth.py)

**主要组件**：
- `AuthManager` 类：管理API密钥验证
  - `verify_key()`: 验证密钥有效性
  - `extract_key_from_request()`: 从请求中提取密钥（支持3种方式）

- `@require_auth` 装饰器：强制鉴权
- `@check_auth_optional` 装饰器：可选鉴权

**支持的鉴权方式**（按优先级）：
1. `X-API-Key` header（推荐）
2. `Authorization: Bearer <token>` header
3. Query parameter `?api_key=<token>`（不推荐，仅用于测试）

### 3. Web API（Flask）
**文件**: [src/web/app.py](src/web/app.py)

**需要鉴权的端点**：
- `POST /api/news/<id>/decrease_popularity` - 降低单条新闻关注度
- `POST /api/news/batch_decrease_popularity` - 批量降低关注度

**公开端点**：
- `GET /api/recent_news` - 获取最近新闻
- `GET /api/news/high_popularity` - 获取高关注度新闻
- `GET /api/news` - 获取新闻列表
- `GET /api/stats/*` - 所有统计API
- `GET /` - 首页
- `GET /health` - 健康检查

### 4. MCP服务
**文件**: [mcp_server.py](mcp_server.py)

**需要鉴权的工具**：
- `decrease_news_popularity` - 降低新闻关注度
- `batch_decrease_popularity` - 批量降低关注度

**无需鉴权的工具**：
- `get_recent_news` - 获取最近新闻
- `get_high_popularity_news` - 获取高关注度新闻

**鉴权实现**：
- 在 `do_POST()` 方法中调用 `_verify_auth()` 验证请求
- 调用后端API时，通过 `X-API-Key` header 传递密钥

---

## 配置文件变更

### [requirements.txt](requirements.txt)
添加了依赖：
```
python-dotenv>=1.0.0
```

### [docker-compose.yml](docker-compose.yml)
添加了环境变量文件挂载：
```yaml
volumes:
  - ./.env:/app/.env
```

### [.gitignore](.gitignore)（新建）
确保 `.env` 文件不被提交到git仓库：
```
# 环境变量文件（包含敏感信息）
.env
```

---

## 文档

### [API_AUTH.md](API_AUTH.md)（新建）
完整的API鉴权使用指南，包含：
- 配置步骤
- 3种鉴权方式示例
- 需要鉴权和公开的API列表
- 错误响应说明
- n8n集成配置示例
- 安全建议

---

## 测试

### [test_auth.sh](test_auth.sh)（新建）
自动化测试脚本，测试8个场景：
1. ✅ 公开端点访问
2. ❌ 受保护端点无鉴权（期望401）
3. ❌ 受保护端点错误密钥（期望403）
4. ✅ 受保护端点正确密钥（X-API-Key）
5. ✅ 受保护端点Bearer Token
6. ✅ MCP服务获取工具列表
7. ✅ MCP服务调用工具（带鉴权）
8. ❌ MCP服务调用工具无鉴权（期望401）

**运行测试**：
```bash
# 确保服务已启动
docker-compose ps
./mcp_service.sh status

# 运行测试
./test_auth.sh
```

---

## 部署步骤

### 1. 修改API密钥
```bash
# 编辑 .env 文件，修改为强密码
nano .env

# 建议使用以下命令生成32位随机密钥
openssl rand -base64 32
```

### 2. 重启服务
```bash
# 重启Web服务（Docker）
docker-compose restart

# 重启MCP服务
./mcp_service.sh restart
```

### 3. 验证部署
```bash
# 运行测试脚本
./test_auth.sh

# 或手动测试
curl http://localhost:5000/health
curl http://localhost:3001/health
```

---

## 安全特性

### ✅ 已实现
1. **环境变量隔离**：API密钥存储在 `.env` 文件中
2. **多方式鉴权**：支持X-API-Key、Bearer Token、Query参数
3. **选择性保护**：只保护写操作，读操作公开
4. **密钥验证警告**：检测默认密钥并警告
5. **Git安全**：`.env` 文件被 `.gitignore` 排除
6. **CORS支持**：MCP服务支持跨域请求
7. **错误处理**：返回清晰的401/403错误信息

### 🔒 安全建议
1. **使用强密码**：至少32位，包含大小写字母、数字和特殊字符
2. **定期更换**：建议每月更换API密钥
3. **HTTPS传输**：生产环境使用HTTPS协议
4. **访问控制**：配置防火墙规则，限制API访问来源IP
5. **日志监控**：定期检查访问日志，发现异常请求

---

## 使用示例

### 通过curl调用API

**使用X-API-Key（推荐）**：
```bash
curl -X POST http://localhost:5000/api/news/123/decrease_popularity \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key_here" \
  -d '{"decrease_amount": 1}'
```

**使用Bearer Token**：
```bash
curl -X POST http://localhost:5000/api/news/123/decrease_popularity \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_api_key_here" \
  -d '{"decrease_amount": 1}'
```

### 通过MCP服务调用

```bash
curl -X POST http://localhost:3001/tools/call \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key_here" \
  -d '{
    "name": "decrease_news_popularity",
    "arguments": {
      "news_id": 123,
      "decrease_amount": 1
    }
  }'
```

---

## 错误处理

### 401 Unauthorized - 缺少API密钥
```json
{
  "success": false,
  "error": "缺少API密钥，请在请求头中提供 X-API-Key 或 Authorization: Bearer <token>"
}
```

### 403 Forbidden - API密钥无效
```json
{
  "success": false,
  "error": "API密钥无效"
}
```

---

## 故障排查

### 问题1：服务启动失败
```bash
# 检查.env文件是否存在
ls -la .env

# 检查.env文件格式
cat .env

# 查看服务日志
docker-compose logs
./mcp_service.sh logs
```

### 问题2：鉴权失败
```bash
# 确认API密钥正确
grep API_KEY .env

# 测试API密钥
export API_KEY=$(grep API_KEY .env | cut -d'=' -f2)
curl -H "X-API-Key: $API_KEY" http://localhost:5000/health
```

### 问题3：Docker容器无法读取.env
```bash
# 检查文件权限
ls -la .env

# 确保docker-compose.yml包含volume挂载
grep ".env" docker-compose.yml

# 重新构建容器
docker-compose down
docker-compose up -d --build
```

---

## 下一步优化（可选）

1. **添加IP白名单**：限制API访问来源IP
2. **添加速率限制**：防止API滥用
3. **添加日志审计**：记录所有敏感操作
4. **添加密钥轮换**：支持多个API密钥同时有效
5. **添加JWT Token**：支持有时效性的访问令牌

---

## 总结

API鉴权系统已完全实现并集成到以下组件：
- ✅ Flask Web API（需要鉴权的端点）
- ✅ MCP服务（需要鉴权的工具）
- ✅ Docker部署配置
- ✅ 完整的文档和测试脚本

**下一步行动**：
1. 修改 `.env` 文件中的API密钥为强密码
2. 重启服务使配置生效
3. 运行 `test_auth.sh` 验证鉴权功能
