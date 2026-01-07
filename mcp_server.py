#!/usr/bin/env python3
# coding=utf-8
"""
MCP服务器 - 热点新闻爬虫
使用标准MCP Python SDK实现SSE长连接
"""

import os
import requests
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from dotenv import load_dotenv
from typing import Any
import uvicorn

# 加载环境变量
load_dotenv()

# 后端 API 地址
API_BASE_URL = "http://localhost:5000"
API_KEY = os.getenv('API_KEY', '')

def _get_headers():
    """获取请求头"""
    return {"X-API-Key": API_KEY}

# 创建 MCP 服务器实例
server = Server("hotnews-crawler")

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """列出所有可用工具"""
    return [
        Tool(
            name="get_recent_news",
            description="获取最近几小时的新闻",
            inputSchema={
                "type": "object",
                "properties": {
                    "hours": {
                        "type": "integer",
                        "description": "最近多少小时(默认2小时)",
                        "default": 2,
                        "minimum": 1
                    }
                }
            }
        ),
        Tool(
            name="decrease_news_popularity",
            description="降低指定新闻的关注度(用于标记不感兴趣的新闻)",
            inputSchema={
                "type": "object",
                "properties": {
                    "news_id": {
                        "type": "integer",
                        "description": "新闻ID"
                    },
                    "decrease_amount": {
                        "type": "integer",
                        "description": "降低的数值(默认为1)",
                        "default": 1,
                        "minimum": 1
                    }
                },
                "required": ["news_id"]
            }
        ),
        Tool(
            name="batch_decrease_popularity",
            description="批量降低多条新闻的关注度",
            inputSchema={
                "type": "object",
                "properties": {
                    "news_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "新闻ID列表"
                    },
                    "decrease_amount": {
                        "type": "integer",
                        "description": "每条新闻降低的数值(默认为1)",
                        "default": 1,
                        "minimum": 1
                    }
                },
                "required": ["news_ids"]
            }
        ),
        Tool(
            name="get_high_popularity_news",
            description="获取高关注度新闻列表",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "返回条数(默认20条)",
                        "default": 20,
                        "minimum": 1,
                        "maximum": 100
                    },
                    "min_popularity": {
                        "type": "integer",
                        "description": "最低关注度(默认3)",
                        "default": 3,
                        "minimum": 1
                    }
                }
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """处理工具调用"""
    try:
        if name == "get_recent_news":
            hours = arguments.get("hours", 2)
            url = f"{API_BASE_URL}/api/recent_news"
            resp = requests.get(url, params={"hours": hours}, timeout=10)
            resp.raise_for_status()
            return [TextContent(type="text", text=str(resp.json()))]

        elif name == "decrease_news_popularity":
            news_id = arguments.get("news_id")
            decrease_amount = arguments.get("decrease_amount", 1)
            url = f"{API_BASE_URL}/api/news/{news_id}/decrease_popularity"
            payload = {"decrease_amount": decrease_amount}
            resp = requests.post(url, json=payload, headers=_get_headers(), timeout=10)
            return [TextContent(type="text", text=str(resp.json()))]

        elif name == "batch_decrease_popularity":
            news_ids = arguments.get("news_ids", [])
            decrease_amount = arguments.get("decrease_amount", 1)
            url = f"{API_BASE_URL}/api/news/batch_decrease_popularity"
            payload = {"news_ids": news_ids, "decrease_amount": decrease_amount}
            resp = requests.post(url, json=payload, headers=_get_headers(), timeout=30)
            return [TextContent(type="text", text=str(resp.json()))]

        elif name == "get_high_popularity_news":
            limit = arguments.get("limit", 20)
            min_popularity = arguments.get("min_popularity", 3)
            url = f"{API_BASE_URL}/api/news/high_popularity"
            params = {"limit": limit, "min_popularity": min_popularity}
            resp = requests.get(url, params=params, timeout=10)
            return [TextContent(type="text", text=str(resp.json()))]

        else:
            return [TextContent(type="text", text=f"未知工具: {name}")]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]

async def main():
    """启动服务器"""
    # 导入必要的库
    from mcp.server.sse import SseServerTransport
    from starlette.applications import Starlette
    from starlette.routing import Route
    from starlette.requests import Request

    # 1. 创建 SSE 传输实例
    # 注意：这里的 /messages 是告诉客户端(n8n)往哪里发送指令的地址
    sse_transport = SseServerTransport("/messages")

    # 2. 定义 SSE 连接处理函数 (GET /sse)
    async def handle_sse(request: Request):
        async with sse_transport.connect_sse(
            request.scope, request.receive, request._send
        ) as streams:
            await server.run(
                streams[0], streams[1], InitializationOptions(
                    server_name="hotnews-crawler",
                    server_version="1.0.0",
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={}
                    )
                )
            )

    # 3. 定义消息处理函数 (POST /messages)
    # 必须添加这个，否则 n8n 只能看不能动
    async def handle_messages(request: Request):
        await sse_transport.handle_post_message(
            request.scope, request.receive, request._send
        )

    # 4. 创建 Starlette 应用，注册两个路由
    app = Starlette(
        routes=[
            Route("/sse", endpoint=handle_sse),
            Route("/messages", endpoint=handle_messages, methods=["POST"])
        ]
    )

    # 5. 启动服务器
    config = uvicorn.Config(app, host="::", port=3001, log_level="info")
    server_instance = uvicorn.Server(config)
    await server_instance.serve()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
