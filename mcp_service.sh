#!/bin/bash
# MCP服务管理脚本

MCP_PID_FILE="/tmp/mcp_server.pid"
MCP_LOG_FILE="/tmp/mcp_server.log"

case "$1" in
    start)
        if [ -f "$MCP_PID_FILE" ]; then
            PID=$(cat "$MCP_PID_FILE")
            if ps -p $PID > /dev/null 2>&1; then
                echo "MCP服务已在运行 (PID: $PID)"
                exit 1
            fi
        fi

        echo "启动MCP服务..."
        nohup python3 mcp_server.py > "$MCP_LOG_FILE" 2>&1 &
        echo $! > "$MCP_PID_FILE"
        sleep 2

        if ps -p $(cat "$MCP_PID_FILE") > /dev/null 2>&1; then
            echo "✓ MCP服务启动成功 (PID: $(cat $MCP_PID_FILE))"
            echo "  端口: 3001"
            echo "  日志: $MCP_LOG_FILE"
        else
            echo "✗ MCP服务启动失败"
            rm -f "$MCP_PID_FILE"
            exit 1
        fi
        ;;

    stop)
        if [ ! -f "$MCP_PID_FILE" ]; then
            echo "MCP服务未运行"
            exit 1
        fi

        PID=$(cat "$MCP_PID_FILE")
        echo "停止MCP服务 (PID: $PID)..."
        kill $PID 2>/dev/null
        rm -f "$MCP_PID_FILE"
        echo "✓ MCP服务已停止"
        ;;

    restart)
        $0 stop
        sleep 1
        $0 start
        ;;

    status)
        if [ -f "$MCP_PID_FILE" ]; then
            PID=$(cat "$MCP_PID_FILE")
            if ps -p $PID > /dev/null 2>&1; then
                echo "✓ MCP服务运行中 (PID: $PID)"
                echo "  健康检查: http://localhost:3001/health"
                echo "  工具列表: http://localhost:3001/tools"
            else
                echo "✗ MCP服务未运行 (PID文件存在但进程不存在)"
                rm -f "$MCP_PID_FILE"
            fi
        else
            echo "✗ MCP服务未运行"
        fi
        ;;

    logs)
        if [ -f "$MCP_LOG_FILE" ]; then
            tail -f "$MCP_LOG_FILE"
        else
            echo "日志文件不存在: $MCP_LOG_FILE"
        fi
        ;;

    *)
        echo "用法: $0 {start|stop|restart|status|logs}"
        exit 1
        ;;
esac
