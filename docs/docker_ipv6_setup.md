# Docker IPv6 访问问题排查

## 问题
通过 IPv6 地址 `http://[2409:8a28:2580:9e81::7d7]:3001/health` 无法访问 MCP 服务器

## 诊断结果

### 正常工作 ✅
- IPv4 访问：`http://localhost:3001/health` ✓
- IPv4 外部访问：`http://192.168.x.x:3001/health` ✓
- 容器内部访问：`http://localhost:3001/health` ✓
- Docker 端口映射：`0.0.0.0:3001` 和 `[::]:3001` ✓

### 问题 ❌
- IPv6 外部访问：`http://[2409:8a28:2580:9e81::7d7]:3001/health` ✗

## 可能的原因

1. **防火墙规则** - IPv6 防火墙可能阻止了外部访问
2. **Docker IPv6 NAT** - Docker 的 IPv6 端口映射可能有问题
3. **ISP 限制** - 运营商可能限制了 IPv6 入站连接

## 解决方案

### 方案 1：使用 IPv4（推荐）

大多数情况下，IPv4 完全够用：

```bash
# 本地访问
curl http://localhost:3001/health

# 局域网访问（如果需要）
curl http://192.168.1.4:3001/health
```

在 n8n 中配置 MCP 服务器时使用：
```
http://localhost:3001
```
或
```
http://127.0.0.1:3001
```

### 方案 2：修复 IPv6 访问

如果确实需要 IPv6 访问，尝试以下步骤：

#### 2.1 检查防火墙

```bash
# 查看 IPv6 防火墙状态
sudo ip6tables -L -n -v

# 如果需要，允许端口 3001
sudo ip6tables -A INPUT -p tcp --dport 3001 -j ACCEPT
```

#### 2.2 检查 Docker daemon 配置

编辑 `/etc/docker/daemon.json`：

```json
{
  "ipv6": true,
  "fixed-cidr-v6": "2001:db8:1::/64"
}
```

然后重启 Docker：

```bash
sudo systemctl restart docker
```

#### 2.3 使用 Docker 的 host 网络模式

修改 docker-compose.yml，为 MCP 服务器使用 host 网络：

```yaml
mcp-server:
  ...
  network_mode: "host"
  ...
```

这样容器将直接使用宿主机的网络栈。

### 方案 3：使用反向代理

如果外部访问需要 IPv6，可以设置 Nginx 反向代理：

```nginx
server {
    listen [::]:80 ipv6only=on;
    server_name example.com;

    location /mcp/ {
        proxy_pass http://localhost:3001/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 推荐配置

对于 n8n MCP 连接，推荐使用：

```
URL: http://localhost:3001
或
URL: http://127.0.0.1:3001
```

这避免了 IPv6 配置的复杂性，且完全够用。

## 验证脚本

```bash
# 测试 IPv4
curl -4 http://localhost:3001/health

# 测试 IPv6（如果需要）
curl -6 http://[::1]:3001/health

# 测试容器内部
docker exec hotnews_mcp_server curl http://localhost:3001/health
```
