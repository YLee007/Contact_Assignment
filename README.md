# 通讯录应用 (Contact Management Application)

一个功能完整的通讯录管理系统，支持联系人的增删改查、收藏、导入导出等功能。

## 功能特性

-  **联系人管理**
  - 添加、编辑、删除联系人
  - 支持多个联系方式（电话、邮箱、社交媒体、地址等）
  - 收藏联系人功能
  - 筛选显示收藏的联系人

-  **数据导入导出**
  - 支持从 Excel (.xlsx) 文件导入联系人
  - 支持导出联系人到 Excel 文件
  - 自动处理多个同类型联系方式

-  **用户界面**
  - 简洁美观的现代化 UI
  - 响应式设计
  - 多个同类型联系方式的智能分组显示

## 技术栈

### 后端
- **Python 3.7+**
- **Flask** - Web 框架
- **Flask-CORS** - 跨域支持
- **pandas** - 数据处理
- **openpyxl** - Excel 文件处理
- **Gunicorn** - 生产环境 WSGI 服务器

### 前端
- **HTML5** - 页面结构
- **CSS3** - 样式设计（Flexbox 布局）
- **JavaScript (ES6+)** - 交互逻辑
- **Fetch API** - HTTP 请求

### 部署
- **Nginx** - Web 服务器和反向代理
- **systemd** - 服务管理

## 项目结构

```
Contact_Assignment/
├── backend/                 # 后端代码
│   └── app.py              # Flask 应用主文件
├── frontend/               # 前端代码
│   └── index.html          # 前端主页面
├── app.py                  # 应用启动入口（用于 flask run）
├── requirements.txt        # Python 依赖列表
├── deploy.sh              # 自动化部署脚本
├── README.md              # 项目说明文档
├── README_DEPLOY.md       # 部署详细文档
└── TROUBLESHOOTING.md     # 问题排查文档
```

## 快速开始

### 本地开发环境

#### 1. 克隆项目

```bash
git clone git@github.com:YLee007/Contact_Assignment.git
cd Contact_Assignment
```

#### 2. 安装依赖

```bash
# 创建虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装 Python 依赖
pip install -r requirements.txt
```

#### 3. 启动后端服务

```bash
# 方法1: 使用 flask run（推荐）
flask run

# 方法2: 直接运行 Python
python app.py
```

后端服务将在 `http://127.0.0.1:5000` 启动。

#### 4. 启动前端服务

打开新的终端窗口：

```bash
cd frontend
npx serve . -l 8000
```

前端服务将在 `http://localhost:8000` 启动。

#### 5. 访问应用

在浏览器中打开 `http://localhost:8000/index.html`

## API 文档

### 获取所有联系人
```
GET /contacts
```

### 创建联系人
```
POST /contacts
Content-Type: application/json

{
  "name": "张三",
  "contact_details": [
    {"type": "phone", "value": "13800138000"},
    {"type": "email", "value": "zhangsan@example.com"}
  ]
}
```

### 更新联系人
```
PUT /contacts/<contact_id>
Content-Type: application/json

{
  "name": "张三",
  "contact_details": [...]
}
```

### 删除联系人
```
DELETE /contacts/<contact_id>
```

### 更新收藏状态
```
PUT /contacts/<contact_id>/favorite
Content-Type: application/json

{
  "is_favorite": true
}
```

### 导入联系人
```
POST /import_contacts
Content-Type: multipart/form-data

file: <Excel文件>
```

### 导出联系人
```
GET /export_contacts
```

## 部署到生产环境

### 快速部署（推荐）

使用自动化部署脚本：

```bash
chmod +x deploy.sh
bash deploy.sh
```

### 手动部署

详细步骤请参考 [README_DEPLOY.md](README_DEPLOY.md)

### 部署后访问

- 前端: `http://您的服务器IP/`
- 后端 API: `http://您的服务器IP/api/`

## 数据格式

### 联系人数据结构

```json
{
  "id": 1,
  "name": "张三",
  "contact_details": [
    {"type": "phone", "value": "13800138000"},
    {"type": "email", "value": "zhangsan@example.com"},
    {"type": "social_media", "value": "@zhangsan"},
    {"type": "address", "value": "北京市朝阳区"},
    {"type": "other", "value": "备注信息"}
  ],
  "is_favorite": false
}
```

### 联系方式类型

- `phone` - 电话
- `email` - 邮箱
- `social_media` - 社交媒体
- `address` - 地址
- `other` - 其他

### Excel 导入格式

Excel 文件应包含以下列：
- `name` - 姓名（必需）
- `phone`, `phone_1`, `phone_2`, ... - 电话（可选，支持多列）
- `email`, `email_1`, `email_2`, ... - 邮箱（可选，支持多列）
- `social_media`, `social_media_1`, ... - 社交媒体（可选）
- `address`, `address_1`, ... - 地址（可选）
- `other`, `other_1`, ... - 其他（可选）
- `is_favorite` - 是否收藏（可选，布尔值）

## 常见问题

### 问题排查

遇到问题？请查看 [TROUBLESHOOTING.md](TROUBLESHOOTING.md) 获取详细的解决方案。

### 常见问题速查

1. **后端无法启动**
   - 检查 Python 版本（需要 3.7+）
   - 确认所有依赖已安装
   - 查看错误日志

2. **前端无法连接后端**
   - 确认后端服务正在运行
   - 检查 API 地址配置
   - 查看浏览器控制台错误信息

3. **导入 Excel 失败**
   - 确认文件格式正确
   - 检查列名是否匹配
   - 查看后端错误日志
