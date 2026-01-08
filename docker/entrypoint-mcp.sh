#!/bin/bash
# MCP 服务启动脚本
# 设置 IPv6 双栈监听

# 禁用 IPv6 V6ONLY 标志，允许 IPv6 socket 同时接受 IPv4 连接
sysctl -w net.ipv6.bindv6only=0 2>/dev/null || echo "无法设置 net.ipv6.bindv6only（可能需要特权模式）"

# 启动 MCP 服务
exec python mcp_server.py
