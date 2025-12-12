#!/bin/bash

# 应用快速部署脚本

set -e  # 遇到错误立即退出

echo "开始部署通讯录应用..."

# 1. 检查 Python 版本
echo "检查 Python 版本..."
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 python3，请先安装 Python 3.7 或更高版本"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "Python 版本: $(python3 --version)"

# 2. 安装系统依赖（默认适配 CentOS/RHEL，保持已安装的 nginx，不强制覆盖）
echo "安装系统依赖..."
NGINX_CONFIG_DIR="/etc/nginx/conf.d"
sudo yum install -y python3-pip || true
sudo yum install -y nginx || true

# 3. 创建虚拟环境
echo "创建 Python 虚拟环境..."
if [ ! -d "venv" ]; then
    python3 -m venv venv 2>/dev/null || (pip3 install virtualenv && virtualenv venv)
fi
source venv/bin/activate

# 4. 安装 Python 依赖
echo "安装 Python 依赖..."
pip install --upgrade pip
pip install Flask Flask-CORS pandas openpyxl gunicorn

# 5. 创建必要的目录
echo "创建必要的目录..."
mkdir -p logs
mkdir -p /var/www/contacts-frontend

# 6. 复制前端文件到 Nginx 目录
echo "复制前端文件..."
sudo cp -r frontend/* /var/www/contacts-frontend/
sudo chown -R nginx:nginx /var/www/contacts-frontend

# 7. 创建 Gunicorn 服务文件
echo "创建 Gunicorn systemd 服务..."
sudo tee /etc/systemd/system/contacts-backend.service > /dev/null <<EOF
[Unit]
Description=Contacts Application Backend (Gunicorn)
After=network.target

[Service]
User=$USER
Group=$USER
WorkingDirectory=$(pwd)
Environment="PATH=$(pwd)/venv/bin"
ExecStart=$(pwd)/venv/bin/gunicorn --bind 127.0.0.1:5000 --workers 2 --timeout 120 --access-logfile $(pwd)/logs/access.log --error-logfile $(pwd)/logs/error.log app:application

[Install]
WantedBy=multi-user.target
EOF

# 8. 创建 Nginx 配置文件（使用新文件名，避免覆盖现有站点）
echo "创建 Nginx 配置文件..."
SERVER_NAME="${SERVER_NAME:-121.43.230.249}"  # 如有域名可改为 contacts.yourdomain.com

# 创建配置文件（不覆盖现有 contacts-app.conf）
NGINX_CONFIG_FILE="$NGINX_CONFIG_DIR/contacts-app-new.conf"
sudo tee "$NGINX_CONFIG_FILE" > /dev/null <<EOF
server {
    listen 80;
    server_name ${SERVER_NAME};

    # 保留已有根站点：如需，请在此追加或保持其它配置文件不变

    # 通讯录前端（子路径 /contacts）
    location /contacts {
        alias /var/www/contacts-frontend;
        try_files \$uri \$uri/ /contacts/index.html;
        index index.html;
    }

    # 通讯录后端 API（子路径 /contacts/api）
    location /contacts/api/ {
        rewrite ^/contacts/api/(.*) /$1 break;
        proxy_pass http://127.0.0.1:5000/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# 9. 测试并加载 Nginx 配置
sudo nginx -t  # 测试 Nginx 配置

# 10. 启动服务
echo "启动服务..."
sudo systemctl daemon-reload
sudo systemctl enable contacts-backend
sudo systemctl start contacts-backend
sudo systemctl restart nginx

# 11. 检查服务状态
echo "检查服务状态..."
sleep 2
sudo systemctl status contacts-backend --no-pager -l

echo ""
echo "部署完成！"
echo "后端服务运行在: http://127.0.0.1:5000"
echo "前端服务运行在: http://您的服务器IP/contacts/"
echo ""
echo "查看日志:"
echo "  后端日志: tail -f logs/error.log"
echo "  服务状态: sudo systemctl status contacts-backend"
echo "  Nginx状态: sudo systemctl status nginx"


