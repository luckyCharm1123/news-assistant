import os
import requests
import uvicorn
import logging
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.sse import SseServerTransport
from mcp.types import Tool, TextContent
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from dotenv import load_dotenv
from typing import Any

class NoOpResponse(Response):
    async def __call__(self, scope, receive, send):
        return

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
API_BASE_URL = "http://192.168.1.4:5000"
API_KEY = os.getenv('API_KEY', '')

def _get_headers():
    return {"X-API-Key": API_KEY}

server = Server("hotnews-crawler")

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_recent_news",
            description="获取最近几小时的新闻",
            title="获取最近新闻",
            inputSchema={"type": "object", "properties": {"hours": {"type": "integer", "default": 2, "description": "获取最近几小时的新闻"}}}
        ),
        Tool(
            name="decrease_news_popularity",
            description="降低新闻关注度",
            title="降低新闻关注度",
            inputSchema={
                "type": "object",
                "properties": {
                    "news_id": {"type": "integer", "description": "新闻ID"},
                    "decrease_amount": {"type": "integer", "default": 1, "description": "降低的数量"}
                },
                "required": ["news_id"]
            }
        ),
        Tool(
            name="batch_decrease_popularity",
            description="批量降低关注度",
            title="批量降低关注度",
            inputSchema={
                "type": "object",
                "properties": {
                    "news_ids": {"type": "array", "items": {"type": "integer"}, "description": "新闻ID列表"},
                    "decrease_amount": {"type": "integer", "default": 1, "description": "降低的数量"}
                },
                "required": ["news_ids"]
            }
        ),
        Tool(
            name="get_high_popularity_news",
            description="获取高关注度新闻",
            title="获取高关注度新闻",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "default": 20, "description": "返回数量限制"},
                    "min_popularity": {"type": "integer", "default": 3, "description": "最小关注度"}
                }
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    try:
        if name == "get_recent_news":
            hours = arguments.get("hours", 2)
            resp = requests.get(f"{API_BASE_URL}/api/recent_news", params={"hours": hours}, timeout=10)
            return [TextContent(type="text", text=str(resp.json()))]
        elif name == "decrease_news_popularity":
            url = f"{API_BASE_URL}/api/news/{arguments['news_id']}/decrease_popularity"
            payload = {"decrease_amount": arguments.get("decrease_amount", 1)}
            resp = requests.post(url, json=payload, headers=_get_headers(), timeout=10)
            return [TextContent(type="text", text=str(resp.json()))]
        elif name == "batch_decrease_popularity":
            url = f"{API_BASE_URL}/api/news/batch_decrease_popularity"
            payload = {"news_ids": arguments["news_ids"], "decrease_amount": arguments.get("decrease_amount", 1)}
            resp = requests.post(url, json=payload, headers=_get_headers(), timeout=30)
            return [TextContent(type="text", text=str(resp.json()))]
        elif name == "get_high_popularity_news":
            params = {"limit": arguments.get("limit", 20), "min_popularity": arguments.get("min_popularity", 3)}
            resp = requests.get(f"{API_BASE_URL}/api/news/high_popularity", params=params, timeout=10)
            return [TextContent(type="text", text=str(resp.json()))]
        return [TextContent(type="text", text=f"未知工具: {name}")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]

async def main():
    sse_transport = SseServerTransport("/messages")

    # 存储活跃的session
    active_sessions = {}

    async def handle_sse(request: Request):
        # 检查是否包含session_id查询参数（支持 sessionId 和 session_id）
        session_id = request.query_params.get("sessionId") or request.query_params.get("session_id")

        if not session_id:
            # 生成一个默认的session_id，而不是拒绝连接
            session_id = f"n8n-{request.client.host}-{id(request)}"
            logger.info(f"Generated session_id for client: {session_id}")

        logger.info(f"SSE connection established with session_id: {session_id}")
        async with sse_transport.connect_sse(request.scope, request.receive, request._send) as streams:
            # 存储session以便后续POST请求使用
            active_sessions[session_id] = streams
            try:
                await server.run(streams[0], streams[1], InitializationOptions(
                    server_name="hotnews", server_version="1.0",
                    capabilities=server.get_capabilities(notification_options=NotificationOptions(), experimental_capabilities={})
                ))
            finally:
                # 清理session
                active_sessions.pop(session_id, None)

    async def handle_messages(request: Request):
        """处理 POST 消息请求"""
        logger.info(f"Received POST message from {request.client.host}")

        # 修复：n8n 发送 sessionId，但 mcp 库可能期望 session_id
        # 我们需要在 query_string 中修正它
        qs = request.scope.get("query_string", b"").decode("utf-8")

        # 如果完全没有session_id参数，尝试从路径中提取或创建临时session
        if "sessionId=" not in qs and "session_id=" not in qs:
            # 检查是否是n8n的请求，如果是则创建一个临时session
            # 对于没有预先建立SSE连接的POST请求，我们需要特殊处理
            logger.info(f"No session_id found, creating temporary session for POST request")

            import json

            try:
                # 尝试直接解析请求体并处理
                body = await request.body()
                data = json.loads(body.decode()) if body else {}

                logger.info(f"Processing POST request with data: {data}")

                # 处理MCP协议请求
                method = data.get("method")
                request_id = data.get("id")

                if method == "initialize":
                    # 响应初始化请求
                    return JSONResponse({
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "protocolVersion": "2025-06-18",
                            "serverInfo": {
                                "name": "hotnews-crawler",
                                "version": "1.0"
                            },
                            "capabilities": {
                                "tools": {}
                            }
                        }
                    })
                elif method == "notifications/initialized":
                    # 客户端通知初始化完成，不需要响应
                    logger.info("Client initialized successfully")
                    return JSONResponse({"status": "ok"})
                elif method == "tools/list":
                    # 返回可用工具列表
                    tools = await handle_list_tools()
                    tool_list = []
                    for tool in tools:
                        # 确保inputSchema格式正确
                        input_schema = tool.inputSchema if isinstance(tool.inputSchema, dict) else {}

                        tool_dict = {
                            "name": tool.name,
                            "description": tool.description,
                            "inputSchema": input_schema,
                            "inputType": "json"  # 添加inputType字段
                        }

                        # 添加可选字段
                        if hasattr(tool, 'title') and tool.title:
                            tool_dict["title"] = tool.title
                        else:
                            tool_dict["title"] = tool.name

                        tool_list.append(tool_dict)

                    logger.info(f"Returning {len(tool_list)} tools")
                    logger.info(f"Tool response structure: {tool_list[0] if tool_list else 'empty'}")

                    response_data = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "tools": tool_list
                        }
                    }
                    logger.info(f"Full response: {response_data}")
                    return JSONResponse(response_data)
                elif method == "tools/call":
                    # 调用工具
                    params = data.get("params", {})
                    tool_name = params.get("name")
                    arguments = params.get("arguments", {})
                    result = await handle_call_tool(tool_name, arguments)
                    return JSONResponse({
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "content": [content.model_dump() for content in result]
                        }
                    })
                else:
                    return JSONResponse({
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32601,
                            "message": f"Method not found: {method}"
                        }
                    }, status_code=404)

            except Exception as e:
                logger.error(f"Error processing request: {e}", exc_info=True)
                return JSONResponse({"error": str(e)}, status_code=500)

        elif "sessionId=" in qs and "session_id=" not in qs:
            # 将sessionId转换为session_id
            new_qs = qs.replace("sessionId=", "session_id=")
            request.scope["query_string"] = new_qs.encode("utf-8")
            logger.info(f"Rewrote query string for compatibility: {qs} -> {new_qs}")

        # 创建一个标志来跟踪响应是否已发送
        response_sent = False
        original_send = request._send

        async def tracking_send(message):
            nonlocal response_sent
            if message["type"] == "http.response.start":
                response_sent = True
            await original_send(message)

        try:
            # 使用跟踪的 send 函数
            await sse_transport.handle_post_message(request.scope, request.receive, tracking_send)

            # 如果 handle_post_message 没有发送响应，我们需要返回一个
            if not response_sent:
                return JSONResponse({"status": "ok"})
            # 如果响应已发送，返回 NoOpResponse（Starlette 会调用它但什么也不做）
            return NoOpResponse()

        except ValueError as exc:
            logger.error(f"Message handling ValueError: {exc}")
            if not response_sent:
                return JSONResponse({"error": str(exc)}, status_code=400)
            return NoOpResponse()

        except Exception as exc:
            logger.error(f"Unexpected error in message handling: {exc}", exc_info=True)
            if not response_sent:
                return JSONResponse({"error": f"internal error: {exc}"}, status_code=500)
            return NoOpResponse()

    async def handle_health(request: Request):
        return JSONResponse({"status": "ok"})

    app = Starlette(routes=[
        # Allow both GET (SSE stream) and POST (incoming messages) on /sse to match clients that reuse the same path
        Route("/sse", endpoint=handle_sse, methods=["GET"]),
        Route("/sse", endpoint=handle_messages, methods=["POST"]),
        Route("/messages", endpoint=handle_messages, methods=["POST"]),
        Route("/health", endpoint=handle_health)
    ])

    # IPv6双栈监听 (同时支持IPv4和IPv6)
    config = uvicorn.Config(app, host="::", port=3001, log_level="info")
    await uvicorn.Server(config).serve()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
