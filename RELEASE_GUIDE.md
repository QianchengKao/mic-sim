# 🚀 发布指南 (Release Guide)

为了让没有安装 Python 的用户也能在 **Windows** 和 **macOS** 上运行您的仿真器，推荐以下三种发布方案：

---

## 方案 A：云端发布 (最推荐，零安装) 🌟
**适用场景**：需要通过链接分享给任何人，支持网页访问，无需用户安装任何东西。

1. **注册并登录**：在 [Streamlit Cloud](https://streamlit.io/cloud) 上注册账号。
2. **连接 GitHub**：将本项目上传到您的个人 GitHub 仓库。
3. **一键部署**：在 Streamlit Cloud 界面点击 "New App"，选择对应的仓库和 `app.py`。
4. **访问**：几分钟后，您会得到一个 URL（例如 `https://mic-sim-array.streamlit.app`），用户点击链接即可使用。

---

## 方案 B：本地 EXE/APP 可执行文件 (stlite-desktop) 💻
**适用场景**：完全离线运行，不需要用户本地有 Python 环境。

这是目前将 Streamlit 转化为本地应用最现代的方法（基于 WebAssembly 和 Electron）。

1. **准备资源**：
   在命令行运行：
   ```bash
   npx @stlite/desktop-cli@latest init
   ```
2. **打包**：
   它会基于您的 `app.py` 和 `requirements.txt` 自动生成一个打包项目。
3. **输出**：
   - 在 Windows 上生成 `.exe`。
   - 在 macOS 上生成 `.app`。
   - 用户**完全不需要安装 Python** 即可直接点开运行。

---

## 方案 C：便携版打包 (PyInstaller) 📦
**适用场景**：作为常规本地软件分发。

我已经为您准备了 `run_app.py`。您可以尝试以下步骤：

1. **安装打包工具**：
   ```bash
   pip install pyinstaller
   ```
2. **运行打包命令**：
   ```bash
   pyinstaller --onefile --additional-hooks-dir=. run_app.py
   ```
   *注意：打包 Streamlit 较为复杂，通常需要处理资源文件（`.streamlit`, `matplotlib` 数据等）。建议优先考虑 **方案 B (stlite)**。*

---

## 方案 D：简单的 "一键启动" 脚本 (Portable Python) 🏃
如果目标环境允许少量安装（如内网环境），您可以：
1. 下载 **WinPython** (Windows 便携版) 或 **Conda 便携版** 到 U 盘。
2. 在该环境下安装 `requirements.txt`。
3. 提供一个 `run.bat` 文件供用户双击运行命令行启动。

---

### 方案 E：VPS 自行托管 (Docker 部署) 🌐
**适用场景**：通过您自己的服务器 IP 或域名访问，完全私有可控。

如果您有自己的 VPS，使用 **Docker** 是最简单且能保证 Mac/Win 环境一致性的方法：

### 1. 准备工作
确保您的 VPS 已安装 `docker` 和 `docker-compose`。

### 2. 使用 Docker 一键运行
我已经为您生成了 `Dockerfile`。您在 VPS 上的项目目录下执行：
```bash
# 1. 构建镜像
docker build -t mic-sim-app .

# 2. 运行容器 (暴露 8501 端口)
docker run -d -p 8501:8501 --name mic-sim mic-sim-app
```
完成后，访问 `http://您的VPS服务器IP:8501` 即可运行。

### 3. 配置 Nginx 反向代理 (可选但推荐)
如果您想通过域名并加 HTTPS 访问，可以在 Nginx 配置文件中加入：
```nginx
server {
    listen 80;
    server_name mic.yourdomain.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 总结建议：
- 如果不想折腾服务器，**方案 A (Streamlit Cloud)** 只要传 GitHub 就能用。
- 如果不想依赖第三方平台或需要更高私密性，**方案 E (Docker on VPS)** 是您的首选。
