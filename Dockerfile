# 使用轻量级 Python 镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装必要的系统依赖 (针对 matplotlib 和 pandas)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY . .

# 安装 Python 依赖
RUN pip3 install -r requirements.txt

# 暴露 Streamlit 默认端口
EXPOSE 8501

# 配置健康检查
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# 启动命令
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
