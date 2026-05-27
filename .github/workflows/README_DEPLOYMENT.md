# GitHub Actions 自动部署指南

## 概述
本项目配置了 GitHub Actions 自动部署流程，当代码推送到 `main` 或 `master` 分支时，会自动构建并部署到生产服务器。

## 生产服务器信息
- **IP 地址**: 43.159.33.138
- **SSH 端口**: 10022
- **SSH 用户**: lighthouse
- **工作目录**: /data/miaoxiang_web
- **域名**: https://finance-skills.acquirecord.top
- **后端端口**: 8001

## GitHub Secrets 配置

在 GitHub 仓库中配置以下 Secrets：

1. 进入仓库 Settings → Secrets and variables → Actions
2. 点击 "New repository secret"
3. 添加以下 Secret：

| Name | Value |
|------|-------|
| `SSH_PRIVATE_KEY` | 你的 SSH 私钥内容（对应服务器上的 ~/.ssh/authorized_keys） |

### 生成 SSH 密钥对（如果没有）

```bash
# 在本地生成 SSH 密钥对
ssh-keygen -t rsa -b 4096 -f github_actions_key -N ""

# 将公钥添加到服务器的 authorized_keys
cat github_actions_key.pub | ssh -p 10022 lighthouse@43.159.33.138 "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"

# 将私钥内容添加到 GitHub Secrets
cat github_actions_key | pbcopy  # macOS
# 或
cat github_actions_key | xclip -selection clipboard  # Linux
```

## 部署流程

1. **触发条件**: 推送代码到 `main` 或 `master` 分支
2. **构建步骤**:
   - 安装 Node.js 20 和 Python 3.11
   - 构建前端项目 (Vite + React)
   - 安装后端依赖 (FastAPI + Uvicorn)
3. **部署步骤**:
   - 通过 SSH 连接到生产服务器
   - 备份现有部署
   - 部署新版本
   - 重启后端服务

## Nginx 配置

在生产服务器上配置 Nginx 反向代理：

1. 将 `.github/workflows/nginx.conf` 文件内容复制到服务器
2. 根据实际 SSL 证书路径修改配置文件
3. 启用配置并重启 Nginx：

```bash
# 在服务器上执行
sudo cp nginx.conf /etc/nginx/sites-available/finance-skills
sudo ln -s /etc/nginx/sites-available/finance-skills /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 服务架构

```
用户请求
    ↓
https://finance-skills.acquirecord.top (Nginx, 443)
    ↓
    ├─→ 静态文件: /data/miaoxiang_web/frontend/dist
    └─→ API 代理: http://127.0.0.1:8001 (FastAPI/Uvicorn)
```

## 手动部署（可选）

如果需要手动部署：

```bash
# 1. 构建前端
cd frontend
npm install
npm run build

# 2. 复制文件到服务器
scp -P 10022 -r dist backend lighthouse@43.159.33.138:/tmp/miaoxiang_deploy/

# 3. 在服务器上执行部署脚本
ssh -p 10022 lighthouse@43.159.33.138
bash /tmp/miaoxiang_deploy/deploy_script.sh
```

## 验证部署

1. 访问 https://finance-skills.acquirecord.top 检查前端
2. 检查 API 健康状态：`curl https://finance-skills.acquirecord.top/api/health`
3. 查看后端日志：`tail -f /data/miaoxiang_web/backend.log`

## 故障排查

### 后端服务未启动
```bash
# 检查进程
ps aux | grep uvicorn

# 手动启动
cd /data/miaoxiang_web/backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

### Nginx 配置问题
```bash
# 测试配置
sudo nginx -t

# 查看错误日志
sudo tail -f /var/log/nginx/error.log
```

### SSH 连接问题
```bash
# 测试 SSH 连接
ssh -v -p 10022 lighthouse@43.159.33.138
```
