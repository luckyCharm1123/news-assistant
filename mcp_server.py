import os
import json
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
API_BASE_URL = "http://[2409:8a28:2580:9e81::7d7]:5000"
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
            name="batch_add_curated_news",
            description="批量添加或更新AI精选新闻（自动去重）",
            title="批量添加AI精选新闻",
            inputSchema={
                "type": "object",
                "properties": {
                    "news_list": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "source_news_id": {"type": "integer"},
                                "summary": {"type": "string"}
                            },
                            "required": ["title", "source_news_id"]
                        },
                        "description": "AI精选新闻列表"
                    }
                },
                "required": ["news_list"]
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

        elif name == "batch_add_curated_news":
            url = f"{API_BASE_URL}/api/curated_news/batch"
            # 处理 news_list 参数 - 可能是 JSON 字符串或列表
            news_list = arguments["news_list"]
            if isinstance(news_list, str):
                # 如果是字符串，尝试解析为 JSON
                try:
                    news_list = json.loads(news_list)
                except json.JSONDecodeError as e:
                    # 尝试修复 JSON 格式问题（未转义的引号）
                    try:
                        cleaned = news_list
                        logger.info(f"原始数据: {cleaned[:200]}")

                        # 使用状态机修复 title 字段中的未转义引号
                        result = []
                        i = 0
                        while i < len(cleaned):
                            # 查找 "title": " 模式（允许空格变化）
                            if cleaned[i] == '"' and cleaned[i:i+7].startswith('"title"'):
                                # 找到 "title"，现在查找 ": "
                                colon_pos = cleaned.find(':', i)
                                if colon_pos > 0:
                                    # 找到冒号，跳过空格找到引号
                                    quote_pos = colon_pos + 1
                                    while quote_pos < len(cleaned) and cleaned[quote_pos] == ' ':
                                        quote_pos += 1

                                    if quote_pos < len(cleaned) and cleaned[quote_pos] == '"':
                                        # 找到 "title": " 模式
                                        start_pos = i
                                        value_start = quote_pos + 1  # title 值开始位置
                                        result.append(cleaned[start_pos:value_start])  # 添加 "title": "
                                        i = value_start

                                        # 收集 title 内容，直到找到未转义的 " 后跟 , 或 }
                                        title_chars = []
                                        while i < len(cleaned):
                                            c = cleaned[i]

                                            # 检查是否到达结尾
                                            if c == '"' and (i + 1 >= len(cleaned) or cleaned[i+1] in ',}'):
                                                # 找到结尾引号
                                                title_str = ''.join(title_chars).replace('"', '\\"')
                                                result.append(title_str)
                                                result.append('"')
                                                i += 1
                                                break

                                            # 否则添加字符
                                            title_chars.append(c)
                                            i += 1
                            else:
                                result.append(cleaned[i])
                                i += 1

                        cleaned = ''.join(result)
                        logger.info(f"清理后数据: {cleaned[:200]}")

                        news_list = json.loads(cleaned)
                        logger.warning(f"JSON 解析成功，但使用了修复模式（转义了 title 中的引号）")
                    except Exception as fix_error:
                        # 提供更详细的错误信息以便调试
                        error_msg = f"Error: news_list JSON 解析失败: {str(e)}\n"
                        error_msg += f"收到的数据类型: {type(news_list)}\n"
                        error_msg += f"数据长度: {len(news_list)} 字符\n"
                        error_msg += f"数据前500字符: {news_list[:500]}\n\n"
                        error_msg += f"建议：请检查 n8n 工作流中的 JSON 序列化配置\n"
                        error_msg += f"确保使用 JSON.stringify() 或等效方法正确序列化数据\n"
                        error_msg += f"修复尝试也失败: {fix_error}"
                        logger.error(error_msg)
                        return [TextContent(type="text", text=error_msg)]
            payload = {"news_list": news_list}
            logger.info(f"准备发送批量添加请求，共 {len(news_list)} 条新闻")
            resp = requests.post(url, json=payload, headers=_get_headers(), timeout=30)
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

    # IPv4/IPv6双栈监听
    # uvicorn 的 :: 绑定默认不启用 IPv4 映射
    # 需要创建多个服务器或使用配置来启用双栈
    # 方法：创建自定义配置来监听所有接口
    import socket
    from uvicorn.config import Config
    from uvicorn.server import Server

    # 创建 socket 并设置 IPV6_V6ONLY=0
    sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('::', 3001))

    config = Config(app, host="::", port=3001, log_level="info")
    server = Server(config)

    logger.info("启动服务器，监听地址: :::3001 (同时支持 IPv4 和 IPv6)")

    # 使用自定义 socket
    async def serve():
        await server.serve(sockets=[sock])

    await serve()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
