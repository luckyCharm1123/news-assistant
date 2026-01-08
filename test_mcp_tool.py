#!/usr/bin/env python3
"""
测试 MCP 工具是否正常工作
"""

import requests
import json

# MCP 服务器地址
MCP_URL = "http://127.0.0.1:3001/sse"

def test_mcp_connection():
    """测试MCP连接"""
    print("1. 测试 MCP 健康检查...")
    try:
        resp = requests.get("http://127.0.0.1:3001/health", timeout=5)
        print(f"   ✓ 健康检查: {resp.json()}")
    except Exception as e:
        print(f"   ✗ 健康检查失败: {e}")
        return False

    print("\n2. 测试获取精选新闻...")
    try:
        # 模拟 MCP 工具调用
        resp = requests.get("http://127.0.0.1:5000/api/curated_news", params={"limit": "5"}, timeout=5)
        data = resp.json()
        print(f"   ✓ 获取到 {len(data.get('data', []))} 条精选新闻")
        if data.get('data'):
            print(f"   示例: ID={data['data'][0]['id']} {data['data'][0]['title']}")
    except Exception as e:
        print(f"   ✗ 获取新闻失败: {e}")
        return False

    return True

if __name__ == "__main__":
    print("="*50)
    print("MCP 工具测试")
    print("="*50)

    if test_mcp_connection():
        print("\n✓ MCP 服务正常")
        print("\n提示：如果 n8n 中大模型不调用工具，请检查：")
        print("1. n8n MCP Agent Tool 节点配置")
        print("2. 确保提示词中明确要求实际调用工具")
        print("3. 检查 n8n 日志查看工具调用详情")
    else:
        print("\n✗ MCP 服务异常")
