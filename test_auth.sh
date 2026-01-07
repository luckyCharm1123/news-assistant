#!/bin/bash
# API鉴权测试脚本

# 读取API密钥
if [ -f .env ]; then
    API_KEY=$(grep API_KEY .env | cut -d'=' -f2)
else
    echo "错误: .env文件不存在"
    exit 1
fi

WEB_URL="http://localhost:5000"
MCP_URL="http://localhost:3001"

echo "=========================================="
echo "API鉴权测试"
echo "=========================================="
echo "API密钥: $API_KEY"
echo ""

# 测试1: 公开端点（无需鉴权）
echo "测试1: 公开端点 - 获取最近新闻"
echo "URL: GET ${WEB_URL}/api/recent_news"
curl -s "${WEB_URL}/api/recent_news?hours=2" | jq '.success'
echo ""

# 测试2: 受保护端点 - 无鉴权（应该失败）
echo "测试2: 受保护端点 - 无API密钥（应该返回401）"
echo "URL: POST ${WEB_URL}/api/news/1/decrease_popularity"
curl -s -X POST "${WEB_URL}/api/news/1/decrease_popularity" \
  -H "Content-Type: application/json" \
  -d '{"decrease_amount": 1}' | jq '.success, .error'
echo ""

# 测试3: 受保护端点 - 错误的API密钥（应该返回403）
echo "测试3: 受保护端点 - 错误的API密钥（应该返回403）"
echo "URL: POST ${WEB_URL}/api/news/1/decrease_popularity"
curl -s -X POST "${WEB_URL}/api/news/1/decrease_popularity" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: wrong_api_key" \
  -d '{"decrease_amount": 1}' | jq '.success, .error'
echo ""

# 测试4: 受保护端点 - 正确的API密钥（X-API-Key header）
echo "测试4: 受保护端点 - 正确的API密钥（X-API-Key header）"
echo "URL: POST ${WEB_URL}/api/news/1/decrease_popularity"
curl -s -X POST "${WEB_URL}/api/news/1/decrease_popularity" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${API_KEY}" \
  -d '{"decrease_amount": 1}' | jq '.success, .message'
echo ""

# 测试5: 受保护端点 - Bearer Token格式
echo "测试5: 受保护端点 - Bearer Token格式"
echo "URL: POST ${WEB_URL}/api/news/1/decrease_popularity"
curl -s -X POST "${WEB_URL}/api/news/1/decrease_popularity" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${API_KEY}" \
  -d '{"decrease_amount": 1}' | jq '.success, .message'
echo ""

# 测试6: MCP服务 - 获取工具列表（公开）
echo "测试6: MCP服务 - 获取工具列表（公开）"
echo "URL: GET ${MCP_URL}/tools"
curl -s "${MCP_URL}/tools" | jq 'length'
echo ""

# 测试7: MCP服务 - 调用工具需要鉴权
echo "测试7: MCP服务 - 调用工具（需要鉴权）"
echo "URL: POST ${MCP_URL}/tools/call"
curl -s -X POST "${MCP_URL}/tools/call" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${API_KEY}" \
  -d '{
    "name": "get_recent_news",
    "arguments": {"hours": 2}
  }' | jq '.success'
echo ""

# 测试8: MCP服务 - 无鉴权调用工具（应该失败）
echo "测试8: MCP服务 - 无鉴权调用工具（应该返回401）"
echo "URL: POST ${MCP_URL}/tools/call"
curl -s -X POST "${MCP_URL}/tools/call" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "get_recent_news",
    "arguments": {"hours": 2}
  }' | jq '.success, .error'
echo ""

echo "=========================================="
echo "测试完成"
echo "=========================================="
