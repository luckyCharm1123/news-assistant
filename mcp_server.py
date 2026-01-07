#!/usr/bin/env python3
# coding=utf-8
"""
MCP服务器 - 热点新闻爬虫
提供基于HTTP Streamable的MCP服务，供n8n使用
"""

import json
import logging
import os
from typing import Any, Dict, List
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import requests
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 获取API密钥
API_KEY = os.getenv('API_KEY', '')

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# API基础URL
API_BASE_URL = "http://localhost:5000"


class MCPRequestHandler(BaseHTTPRequestHandler):
    """MCP请求处理器"""

    def _set_headers(self, status_code=200, content_type='application/json'):
        """设置响应头"""
        self.send_response(status_code)
        self.send_header('Content-Type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-API-Key, Authorization')
        self.end_headers()

    def _verify_auth(self):
        """验证请求鉴权"""
        # 从请求中获取API密钥
        api_key = self.headers.get('X-API-Key')
        if not api_key and self.headers.get('Authorization', '').startswith('Bearer '):
            api_key = self.headers.get('Authorization')[7:]

        # 验证密钥
        if not api_key:
            return False
        return api_key == API_KEY

    def do_OPTIONS(self):
        """处理OPTIONS请求（CORS预检）"""
        self._set_headers(204)

    def do_GET(self):
        """处理GET请求"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        try:
            if path == '/mcp':
                # MCP服务器信息
                self._handle_mcp_info()
            elif path == '/tools':
                # 获取可用工具列表
                self._handle_tools_list()
            elif path == '/health':
                # 健康检查
                self._handle_health()
            else:
                self._set_headers(404)
                self.wfile.write(json.dumps({"error": "Not Found"}).encode())

        except Exception as e:
            logger.error(f"处理GET请求失败: {e}")
            self._set_headers(500)
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def do_POST(self):
        """处理POST请求"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        try:
            # 对于需要鉴权的端点，验证API密钥
            if path in ['/tools/call']:
                if not self._verify_auth():
                    self._set_headers(401)
                    self.wfile.write(json.dumps({
                        "success": False,
                        "error": "未授权：缺少或无效的API密钥"
                    }).encode())
                    return

            # 读取请求体
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body.decode()) if body else {}

            if path == '/tools/call':
                # 调用工具
                self._handle_tool_call(data)
            else:
                self._set_headers(404)
                self.wfile.write(json.dumps({"error": "Not Found"}).encode())

        except Exception as e:
            logger.error(f"处理POST请求失败: {e}")
            self._set_headers(500)
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def _handle_mcp_info(self):
        """处理MCP服务器信息请求"""
        info = {
            "name": "hotnews-crawler",
            "version": "1.0.0",
            "description": "热点新闻爬虫MCP服务器 - 提供新闻管理和关注度控制功能",
            "baseUrl": API_BASE_URL,
            "capabilities": {
                "tools": True
            }
        }
        self._set_headers(200)
        self.wfile.write(json.dumps(info, ensure_ascii=False).encode())

    def _handle_tools_list(self):
        """处理工具列表请求"""
        tools = [
            {
                "name": "decrease_news_popularity",
                "description": "降低指定新闻的关注度（用于标记不感兴趣的新闻）",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "news_id": {
                            "type": "integer",
                            "description": "新闻ID"
                        },
                        "decrease_amount": {
                            "type": "integer",
                            "description": "降低的数值（默认为1）",
                            "default": 1,
                            "minimum": 1
                        }
                    },
                    "required": ["news_id"]
                }
            },
            {
                "name": "batch_decrease_popularity",
                "description": "批量降低多条新闻的关注度",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "news_ids": {
                            "type": "array",
                            "items": {
                                "type": "integer"
                            },
                            "description": "新闻ID列表"
                        },
                        "decrease_amount": {
                            "type": "integer",
                            "description": "每条新闻降低的数值（默认为1）",
                            "default": 1,
                            "minimum": 1
                        }
                    },
                    "required": ["news_ids"]
                }
            },
            {
                "name": "get_recent_news",
                "description": "获取最近新增的新闻",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "hours": {
                            "type": "integer",
                            "description": "最近多少小时（默认2小时）",
                            "default": 2,
                            "minimum": 1
                        }
                    }
                }
            },
            {
                "name": "get_high_popularity_news",
                "description": "获取高关注度新闻列表",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "返回条数（默认20条）",
                            "default": 20,
                            "minimum": 1,
                            "maximum": 100
                        },
                        "min_popularity": {
                            "type": "integer",
                            "description": "最低关注度（默认3）",
                            "default": 3,
                            "minimum": 1
                        }
                    }
                }
            }
        ]

        self._set_headers(200)
        self.wfile.write(json.dumps(tools, ensure_ascii=False).encode())

    def _handle_tool_call(self, data):
        """处理工具调用请求"""
        tool_name = data.get('name')
        arguments = data.get('arguments', {})

        logger.info(f"调用工具: {tool_name}, 参数: {arguments}")

        try:
            if tool_name == 'decrease_news_popularity':
                result = self._tool_decrease_popularity(arguments)
            elif tool_name == 'batch_decrease_popularity':
                result = self._tool_batch_decrease_popularity(arguments)
            elif tool_name == 'get_recent_news':
                result = self._tool_get_recent_news(arguments)
            elif tool_name == 'get_high_popularity_news':
                result = self._tool_get_high_popularity_news(arguments)
            else:
                result = {
                    "success": False,
                    "error": f"未知工具: {tool_name}"
                }

            self._set_headers(200)
            self.wfile.write(json.dumps(result, ensure_ascii=False).encode())

        except Exception as e:
            logger.error(f"工具调用失败: {e}")
            self._set_headers(500)
            self.wfile.write(json.dumps({
                "success": False,
                "error": str(e)
            }, ensure_ascii=False).encode())

    def _tool_decrease_popularity(self, args):
        """降低新闻关注度"""
        news_id = args.get('news_id')
        decrease_amount = args.get('decrease_amount', 1)

        if not news_id:
            return {
                "success": False,
                "error": "缺少必需参数: news_id"
            }

        # 调用后端API，传递API密钥
        url = f"{API_BASE_URL}/api/news/{news_id}/decrease_popularity"
        payload = {"decrease_amount": decrease_amount}
        headers = {"X-API-Key": API_KEY}

        response = requests.post(url, json=payload, headers=headers, timeout=10)
        return response.json()

    def _tool_batch_decrease_popularity(self, args):
        """批量降低新闻关注度"""
        news_ids = args.get('news_ids', [])
        decrease_amount = args.get('decrease_amount', 1)

        if not news_ids:
            return {
                "success": False,
                "error": "缺少必需参数: news_ids"
            }

        # 调用后端API，传递API密钥
        url = f"{API_BASE_URL}/api/news/batch_decrease_popularity"
        payload = {
            "news_ids": news_ids,
            "decrease_amount": decrease_amount
        }
        headers = {"X-API-Key": API_KEY}

        response = requests.post(url, json=payload, headers=headers, timeout=30)
        return response.json()

    def _tool_get_recent_news(self, args):
        """获取最近新闻"""
        hours = args.get('hours', 2)

        # 调用后端API
        url = f"{API_BASE_URL}/api/recent_news?hours={hours}"
        response = requests.get(url, timeout=10)
        return response.json()

    def _tool_get_high_popularity_news(self, args):
        """获取高关注度新闻"""
        limit = args.get('limit', 20)
        min_popularity = args.get('min_popularity', 3)

        # 调用后端API
        url = f"{API_BASE_URL}/api/news/high_popularity?limit={limit}&min_popularity={min_popularity}"
        response = requests.get(url, timeout=10)
        return response.json()

    def _handle_health(self):
        """健康检查"""
        self._set_headers(200)
        self.wfile.write(json.dumps({
            "status": "ok",
            "service": "hotnews-crawler-mcp"
        }).encode())

    def log_message(self, format, *args):
        """自定义日志格式"""
        logger.info(f"{self.address_string()} - {format % args}")


def run_server(port=3001):
    """启动MCP服务器"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, MCPRequestHandler)

    logger.info(f"MCP服务器启动在端口 {port}")
    logger.info(f"服务器信息: http://localhost:{port}/mcp")
    logger.info(f"工具列表: http://localhost:{port}/tools")
    logger.info(f"健康检查: http://localhost:{port}/health")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("服务器正在关闭...")
        httpd.shutdown()


if __name__ == '__main__':
    run_server()
