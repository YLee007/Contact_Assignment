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

# 2. 安装系统依赖
echo "安装系统依赖..."
if command -v apt-get &> /dev/null; then
    # Debian/Ubuntu
    sudo apt-get update
    sudo apt-get install -y python3-pip python3-venv nginx
elif command -v yum &> /dev/null; then
    # CentOS/RHEL
    sudo yum install -y python3-pip python3-venv nginx
else
    echo "警告: 未检测到包管理器，请手动安装 python3-pip, python3-venv 和 nginx"
fi

# 3. 创建虚拟环境
echo "创建 Python 虚拟环境..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
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
sudo chown -R www-data:www-data /var/www/contacts-frontend

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

# 8. 创建 Nginx 配置文件
echo "创建 Nginx 配置文件..."
sudo tee /etc/nginx/sites-available/contacts-app > /dev/null <<EOF
server {
    listen 80;
    server_name _;  # 替换为您的域名

    # 前端静态文件
    location / {
        root /var/www/contacts-frontend;
        try_files \$uri \$uri/ /index.html;
        index index.html;
    }

    # 后端 API 代理
    location /api/ {
        proxy_pass http://127.0.0.1:5000/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # CORS 处理（如果后端已启用 CORS，这些可能不需要）
        add_header 'Access-Control-Allow-Origin' '*' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS' always;
        add_header 'Access-Control-Allow-Headers' 'Content-Type, Authorization' always;
        
        if (\$request_method = 'OPTIONS') {
            return 204;
        }
    }
}
EOF

# 9. 启用 Nginx 站点
sudo ln -sf /etc/nginx/sites-available/contacts-app /etc/nginx/sites-enabled/
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
echo "前端服务运行在: http://您的服务器IP/"
echo ""
echo "查看日志:"
echo "  后端日志: tail -f logs/error.log"
echo "  服务状态: sudo systemctl status contacts-backend"
echo "  Nginx状态: sudo systemctl status nginx"


