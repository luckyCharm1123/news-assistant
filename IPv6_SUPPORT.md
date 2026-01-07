# IPv6 支持配置指南

## 概述

Docker Compose 配置已更新，支持 IPv6 双栈网络（IPv4 + IPv6）。

---

## 配置变更

### docker-compose.yml

**端口映射**：
```yaml
ports:
  - "5000:5000"      # IPv4
  - ":::5000:5000"   # IPv6 (绑定所有IPv6地址)
```

**网络配置**：
```yaml
networks:
  hotnews-network:
    driver: bridge
    enable_ipv6: true          # 启用IPv6
    ipam:
      driver: default
      config:
        - subnet: "172.20.0.0/16"           # IPv4子网
        - subnet: "fd00:dead:beef::/64"     # IPv6子网 (ULA)
```

---

## 前置要求

### 1. 系统支持IPv6

检查系统是否启用IPv6：
```bash
# 检查IPv6是否启用
ip -6 addr show

# 或
cat /proc/sys/net/ipv6/conf/all/disable_ipv6
# 输出 0 表示已启用，1 表示已禁用
```

### 2. Docker IPv6支持

检查Docker是否支持IPv6：
```bash
# 检查Docker守护进程配置
docker info | grep -i ipv6

# 查看现有网络
docker network ls
docker network inspect bridge | grep -i ipv6
```

---

## 启用Docker IPv6支持

### 方法1：修改Docker守护进程配置（推荐）

编辑 `/etc/docker/daemon.json`：
```bash
sudo nano /etc/docker/daemon.json
```

添加以下配置：
```json
{
  "ipv6": true,
  "fixed-cidr-v6": "fd00:dead:beef::/64",
  "experimental": true,
  "ip6tables": true
}
```

重启Docker：
```bash
sudo systemctl restart docker
sudo systemctl status docker
```

### 方法2：使用daemon.json（如果不存在）

```bash
sudo tee /etc/docker/daemon.json > /dev/null <<EOF
{
  "ipv6": true,
  "fixed-cidr-v6": "fd00:dead:beef::/64",
  "experimental": true,
  "ip6tables": true
}
EOF

sudo systemctl restart docker
```

---

## 验证IPv6配置

### 1. 检查Docker网络
```bash
# 查看bridge网络的IPv6配置
docker network inspect bridge | grep -A 10 IPv6

# 应该看到类似输出：
# "IPv6": true,
# "EnableIPv6": true
```

### 2. 部署服务
```bash
cd ~/hotnews_crawler
docker compose up -d
```

### 3. 检查容器网络
```bash
# 查看容器的IPv6地址
docker exec hotnews_crawler ip -6 addr

# 查看容器网络配置
docker inspect hotnews_crawler | grep -A 20 "Networks"
```

### 4. 测试IPv6访问

**获取服务器的IPv6地址**：
```bash
# 查看所有IPv6地址
ip -6 addr show | grep inet6

# 或使用curl测试
curl -6 http://[::1]:5000/health
curl -6 http://[::1]:3001/health
```

**从外部访问**：
```bash
# 替换 [你的IPv6地址] 为服务器的公网IPv6地址
curl -6 http://[2001:db8::1]:5000/health
curl -6 http://[2001:db8::1]:3001/health
```

---

## 常见问题

### 问题1：容器没有获取到IPv6地址

**症状**：
```bash
docker exec hotnews_crawler ip -6 addr
# 没有显示IPv6地址
```

**解决方案**：
```bash
# 1. 检查Docker守护进程配置
cat /etc/docker/daemon.json

# 2. 确保 "ipv6": true 已设置
# 3. 重启Docker
sudo systemctl restart docker

# 4. 删除并重新创建容器
docker compose down
docker compose up -d
```

### 问题2：无法从外部访问IPv6

**可能原因**：
1. 服务器没有公网IPv6地址
2. 防火墙阻止了IPv6连接
3. 路由器/云服务器未配置IPv6转发

**解决方案**：

**检查防火墙**：
```bash
# UFW防火墙
sudo ufw status
sudo ufw allow from any to any port 5000 proto ipv6
sudo ufw allow from any to any port 3001 proto ipv6

# 或使用ip6tables
sudo ip6tables -A INPUT -p tcp --dport 5000 -j ACCEPT
sudo ip6tables -A INPUT -p tcp --dport 3001 -j ACCEPT
```

**检查云服务器安全组**：
- 登录云服务器控制台
- 配置安全组允许IPv6访问：
  - TCP 5000（Web服务）
  - TCP 3001（MCP服务）

### 问题3：Docker Compose警告IPv6

**症状**：
```
WARN[0000] IPv6 forwarding is disabled.
```

**解决方案**：
```bash
# 启用系统IPv6转发
echo "net.ipv6.conf.all.forwarding=1" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p

# 验证
cat /proc/sys/net/ipv6/conf/all/forwarding
# 应该输出 1
```

### 问题4：端口绑定失败

**症状**：
```
Error: bind: address already in use
```

**解决方案**：
```bash
# 检查端口占用
sudo netstat -tlnp | grep :5000
sudo netstat -tlnp | grep :3001

# 或使用ss
sudo ss -tlnp | grep :5000
sudo ss -tlnp | grep :3001

# 停止占用端口的服务
docker compose down
```

---

## IPv6 地址格式

### 本地回环
```bash
http://[::1]:5000/health
http://[::1]:3001/health
```

### 链路本地地址
```bash
# 需要指定网络接口
http://[fe80::1%eth0]:5000/health
```

### 全局地址（公网）
```bash
# 替换为实际的IPv6地址
http://[2001:db8::1234]:5000/health
http://[2001:db8::1234]:3001/health
```

### ULA地址（唯一本地地址）
```bash
# fd00::/8 范围，类似IPv4的私有地址
http://[fd00:dead:beef::1]:5000/health
```

---

## 防火墙配置

### UFW（Uncomplicated Firewall）
```bash
# 允许IPv6访问
sudo ufw allow 5000/tcp
sudo ufw allow 3001/tcp

# 查看状态
sudo ufw status numbered

# 重新加载
sudo ufw reload
```

### iptables / ip6tables
```bash
# IPv6规则
sudo ip6tables -A INPUT -p tcp --dport 5000 -j ACCEPT
sudo ip6tables -A INPUT -p tcp --dport 3001 -j ACCEPT
sudo ip6tables -A INPUT -p tcp --dport 5000 -s 2001:db8::/32 -j ACCEPT  # 限制特定前缀

# 保存规则
sudo ip6tables-save > /etc/ip6tables/rules.v4

# 查看规则
sudo ip6tables -L -n -v
```

---

## 测试IPv6连接

### 从服务器本地测试
```bash
# 测试Web服务
curl -6 http://[::1]:5000/health

# 测试MCP服务
curl -6 http://[::1]:3001/health

# 测试API
curl -6 http://[::1]:5000/api/recent_news?hours=2
```

### 从其他机器测试
```bash
# 替换为服务器的IPv6地址
curl -6 http://[服务器IPv6地址]:5000/health
curl -6 http://[服务器IPv6地址]:3001/health
```

### 使用浏览器访问
```
http://[你的IPv6地址]:5000
```

---

## 兼容性说明

### 自动降级

如果系统不支持IPv6，Docker Compose会自动降级到IPv4：
- IPv4端口映射仍然正常工作
- 服务继续正常运行
- 不影响现有功能

### 检查是否使用IPv6

```bash
# 查看容器网络栈
docker inspect hotnews_crawler | grep -A 5 "Networks"

# 查看路由
docker exec hotnews_crawler ip -6 route

# 查看连接
docker exec hotnews_crawler netstat -tuln | grep :
```

---

## 性能优化

### IPv6优先级

如果系统同时有IPv4和IPv6，可以配置优先级：

```bash
# 修改 /etc/gai.conf（如果存在）
# 或在应用中指定使用IPv6
```

### DNS解析

确保DNS正确返回AAAA记录（IPv6）：
```bash
# 检查DNS解析
dig AAAA your-domain.com

# 或使用nslookup
nslookup -type=AAAA your-domain.com
```

---

## 监控和日志

### 查看IPv6连接日志
```bash
# 容器内
docker exec hotnews_crawler netstat -an | grep :5000

# 主机上
sudo netstat -an | grep :5000
sudo ss -tuln | grep :5000
```

### 查看Docker网络日志
```bash
docker compose logs
journalctl -u docker -f
```

---

## 总结

✅ **已启用功能**：
- Docker Compose 支持 IPv6
- 端口映射同时监听 IPv4 和 IPv6
- 网络配置支持双栈

🔧 **配置要求**：
1. Docker 守护进程启用 IPv6
2. 系统内核支持 IPv6
3. 防火墙允许 IPv6 连接

📝 **测试步骤**：
1. 配置 `/etc/docker/daemon.json`
2. 重启 Docker 服务
3. 运行 `docker compose up -d`
4. 测试 IPv6 连接

🌐 **访问方式**：
- IPv4: `http://服务器IP:5000`
- IPv6: `http://[服务器IPv6]:5000`
