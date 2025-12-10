# 后端与前端部署调试复盘

本文档总结了在部署过程中遇到的主要错误及其解决方案，旨在帮助理解和避免类似问题。

## 1. 初始网络错误 / CORS 问题 (本地前端 -> 远程后端)

**错误现象：**
- 前端本地运行 (`http://localhost:3000` 或 `http://localhost:3001`) 访问远程后端 (`http://121.43.230.249:3000/api`) 时出现“网络错误”或 `CORS policy blocked` 错误。

**问题原因与解决方案：**

### 1.1 Vite 代理配置错误 (`vite.config.ts`)

- **问题：** `vite.config.ts` 中的 `/api` 代理目标指向了错误的本地地址 (`http://localhost:5000`)，导致前端请求无法正确转发到远程后端。
- **解决方案：** 修改 `frontend/vite.config.ts` 中的代理目标为远程后端地址。
  ```diff
  --- a/frontend/vite.config.ts
  +++ b/frontend/vite.config.ts
  @@ -19,7 +19,7 @@
     server: {
       port: 3000,
       host: true,
  -    proxy: {
  -      '/api': {
  -        target: 'http://localhost:3000',
  +    proxy: { // 修改代理目标为远程后端
  +      '/api': {
  +        target: 'http://121.43.230.249:3000',
           changeOrigin: true,
           rewrite: (path) => path.replace(/^\/api/, ''),
         },
  ```

### 1.2 前端 API 基路径配置不当 (`contactApi.ts`)

- **问题：** `frontend/src/services/contactApi.ts` 中，`API_BASE_URL` 在开发模式下没有正确设置为相对路径 `/api`，导致前端直接构建完整的 URL，绕过 Vite 代理。
- **解决方案：** 修改 `frontend/src/services/contactApi.ts`，确保开发模式下使用 `/api`。
  ```diff
  --- a/frontend/src/services/contactApi.ts
  +++ b/frontend/src/services/contactApi.ts
  @@ -1,6 +1,6 @@
   import axios, { AxiosInstance, AxiosResponse, AxiosError } from 'axios';
   import { Contact, ContactCreate, ContactUpdate, ApiResponse, ContactListResponse, ContactQueryParams } from '../types/contact';
   
  -const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:3000/api';
  +const API_BASE_URL = import.meta.env.MODE === 'development' ? '/api' : import.meta.env.VITE_API_BASE_URL || '/api';
   
   const axiosInstance: AxiosInstance = axios.create({
     baseURL: API_BASE_URL,
  ```

### 1.3 后端 CORS 策略未允许本地前端来源 (`backend/src/index.ts`)

- **问题：** 当本地前端运行在 `http://localhost:3001` 时，后端 `backend/src/index.ts` 中的 CORS 配置只允许 `http://localhost:3000`，导致 `CORS policy blocked` 错误。
- **解决方案：** 修改 `backend/src/index.ts`，在 CORS 配置中允许所有需要的本地前端来源。
  ```diff
  --- a/backend/src/index.ts
  +++ b/backend/src/index.ts
  @@ -12,7 +12,7 @@
   const PORT = process.env.PORT || 3000;
   
   app.use(cors({
  -  origin: 'http://localhost:3000',
  +  origin: ['http://localhost:3000', 'http://localhost:3001'], // 允许所有本地开发端口
     methods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'],
     allowedHeaders: ['Content-Type', 'Authorization'],
     credentials: true,
  ```

## 2. 前端部署在云服务器后绕过 Nginx 代理

**错误现象：**
- 前端部署在云服务器 (`http://121.43.230.249/`)，但 API 请求仍然发往 `http://121.43.230.249:3000/api/...` (带端口)，绕过了 Nginx 代理。

**问题原因与解决方案：**

### 2.1 前端 `authApi.ts` 中的硬编码 API 基路径

- **问题：** `frontend/src/services/authApi.ts` 中，`API_BASE_URL` 的回退值被硬编码为远程后端带端口的完整地址，导致生产构建时绕过 Nginx 代理。
- **解决方案：** 修改 `frontend/src/services/authApi.ts`，将回退地址改为相对路径 `/api`。
  ```diff
  --- a/frontend/src/services/authApi.ts
  +++ b/frontend/src/services/authApi.ts
  @@ -2,7 +2,7 @@
   import { LoginCredentials, RegisterCredentials, AuthResponse, User } from '../types/user';
   import { ApiResponse } from '../types'; // 从 index.ts 或其他公共类型文件导入 ApiResponse
   
  -const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://121.43.230.249/:3000/api';
  +const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';
   
   const axiosInstance: AxiosInstance = axios.create({
     baseURL: API_BASE_URL,
  ```

## 3. 后端 `ERR_MODULE_NOT_FOUND` 导致服务崩溃 / `502 Bad Gateway`

**错误现象：**
- 后端服务在 PM2 管理下启动时，反复报告 `ERR_MODULE_NOT_FOUND` 错误并崩溃。
- 前端访问时收到 `502 Bad Gateway` 错误（Nginx 无法从后端获取响应）。

**问题原因与解决方案：**

### 3.1 `tsconfig.json` 模块解析配置不当

- **问题：** `tsconfig.json` 中的 `moduleResolution` 和 `module` 配置不符合 Node.js ES Module 规范，导致 TypeScript 编译器无法正确生成或解析模块。
- **解决方案：** 修改 `backend/tsconfig.json`，将 `module` 和 `moduleResolution` 都设置为 `NodeNext`。
  ```diff
  --- a/backend/tsconfig.json
  +++ b/backend/tsconfig.json
  @@ -2,8 +2,8 @@
   {
     "compilerOptions": {
       "target": "ES2020",
  -    "module": "ESNext",
  +    "module": "NodeNext",
       "lib": ["ES2020"],
  -    "moduleResolution": "node",
  +    "moduleResolution": "NodeNext",
       "rootDir": "./src",
       "outDir": "./dist",
       "strict": true,
  ```

### 3.2 源代码中相对导入路径缺少 `.js` 扩展名

- **问题：** 即使 `tsconfig.json` 配置正确，Node.js ES Module 模式要求本地导入路径显式包含 `.js` 扩展名，而 `.ts` 源代码中缺少这些扩展名，导致编译后 JavaScript 文件仍有问题。
- **解决方案：** 批量修改 `backend/src` 目录下所有相关 `.ts` 文件中的相对导入路径，添加 `.js` 扩展名。
  - `backend/src/index.ts`:
    ```diff
    --- a/backend/src/index.ts
    +++ b/backend/src/index.ts
    @@ -1,6 +1,6 @@
     import express from 'express';
     import dotenv from 'dotenv';
     import cors from 'cors';
    -import contactRoutes from './routes/contactRoutes';
    -import authRoutes from './routes/authRoutes'; // 导入认证路由
    -import { errorHandler } from './middleware/errorHandler';
    +import contactRoutes from './routes/contactRoutes.js';
    +import authRoutes from './routes/authRoutes.js'; // 导入认证路由
    +import { errorHandler } from './middleware/errorHandler.js';
     
     dotenv.config();
    ```
  - `backend/src/routes/authRoutes.ts`:
    ```diff
    --- a/backend/src/routes/authRoutes.ts
    +++ b/backend/src/routes/authRoutes.ts
    @@ -1,6 +1,6 @@
     import { Router } from 'express';
    -import { login, register, logout } from '../controllers/authController';
    +import { login, register, logout } from '../controllers/authController.js';
     
     const router: Router = Router();
     
    ```
  - `backend/src/routes/contactRoutes.ts`:
    ```diff
    --- a/backend/src/routes/contactRoutes.ts
    +++ b/backend/src/routes/contactRoutes.ts
    @@ -1,7 +1,7 @@
     import { Router } from 'express';
    -import { createContact, getContacts, getContactById, updateContact, deleteContact, toggleFavoriteContact } from '../controllers/contactController';
    -import { validate } from '../middleware/validation';
    -import { createContactSchema, updateContactSchema, getContactByIdSchema, deleteContactSchema, getContactsSchema } from '../schemas/contactSchemas';
    +import { createContact, getContacts, getContactById, updateContact, deleteContact, toggleFavoriteContact } from '../controllers/contactController.js';
    +import { validate } from '../middleware/validation.js';
    +import { createContactSchema, updateContactSchema, getContactByIdSchema, deleteContactSchema, getContactsSchema } from '../schemas/contactSchemas.js';
     
     const router: Router = Router();
     
    ```
  - `backend/src/controllers/authController.ts`:
    ```diff
    --- a/backend/src/controllers/authController.ts
    +++ b/backend/src/controllers/authController.ts
    @@ -1,6 +1,6 @@
     import { Request, Response, NextFunction } from 'express';
    -import prisma from '../utils/prisma';
    +import prisma from '../utils/prisma.js';
     
     export const register = async (req: Request, res: Response, next: NextFunction) => {
       try {
    ```
  - `backend/src/controllers/contactController.ts`:
    ```diff
    --- a/backend/src/controllers/contactController.ts
    +++ b/backend/src/controllers/contactController.ts
    @@ -1,6 +1,6 @@
     import { Request, Response, NextFunction } from 'express';
    -import prisma from '../utils/prisma';
    +import prisma from '../utils/prisma.js';
     
     // 获取所有联系人
     export const getContacts = async (req: Request, res: Response, next: NextFunction) => {
    ```
    - **注意**: `backend/src/utils/prisma.ts` 的导入 `import { PrismaClient } from '@prisma/client';` 通常不需要修改，因为它是一个 npm 包的导入。

### 3.3 `TS2305: Module '..."@prisma/client"' has no exported member 'PrismaClient'.`

- **问题：** `PrismaClient` 无法从 `@prisma/client` 模块中导入。
- **解决方案：** 运行 `prisma generate` 命令来重新生成 `PrismaClient`。
  ```bash
  pnpm run prisma:generate
  ```

### 3.4 PM2 模块解析问题 (`ecosystem.config.js` 作为 ES Module)

- **问题：** `ecosystem.config.js` 使用 CommonJS 语法，但在 `package.json` 设置 `"type": "module"` 的项目中被当做 ES Module 解析，导致 `ReferenceError: module is not defined`。
- **解决方案：** 将 `ecosystem.config.js` 重命名为 `ecosystem.config.cjs`，明确告诉 Node.js 这是一个 CommonJS 模块。
  ```bash
  mv /home/admin/contacts-backend/ecosystem.config.js /home/admin/contacts-backend/ecosystem.config.cjs
  pm2 start ecosystem.config.cjs
  ```

### 3.5 PM2 未正确加载最新代码 / 缓存问题

- **问题：** 即使代码和配置都已更新，PM2 仍然报告旧的错误或未加载最新代码。
- **解决方案：** 执行彻底的 PM2 清理和重启。
  ```bash
  pm2 stop all
  pm2 delete all
  pm2 save --force
  pm2 kill
  pm2 start ecosystem.config.cjs # 或者 pm2 start dist/index.js --name contacts-backend
  ```

## 4. Nginx `500 Internal Server Error` (前端文件无法提供)

**错误现象：**
- 访问云服务器 IP 时收到 `500 Internal Server Error`。

**问题原因与解决方案：**

### 4.1 `/home/admin` 目录权限问题

- **问题：** Nginx 运行用户（通常是 `nginx` 或 `www-data`）没有 `root` 路径 `/home/admin` 目录的执行（`x`）权限，导致无法遍历到前端 `dist` 目录。
- **解决方案：** 为 `/home/admin` 目录添加“其他用户”的执行权限。
  ```bash
  sudo chmod o+x /home/admin
  ```

## 5. 网站名称修改

- **问题：** 网站名称显示为“通讯录管理系统”，需要修改。
- **解决方案：** 修改 `frontend/index.html` 文件中的 `<title>` 标签。
  ```diff
  --- a/frontend/index.html
  +++ b/frontend/index.html
  @@ -3,4 +3,4 @@
       <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  -    <title>通讯录管理系统</title>
  +    <title>无敌leecontacts</title>
     </head>
     <body>
  ```

## 经验总结与教训

1.  **明确区分开发环境与生产环境配置**：前端的 `VITE_API_BASE_URL` 在开发时应使用 `/api` 配合 Vite 代理，生产时应与 Nginx 代理配置一致。
2.  **细致检查 `.env` 文件**： `.env` 或 `.env.production` 文件中的变量设置很容易影响构建结果。
3.  **理解 Node.js ES Module 规范**：当 `package.json` 设置 `"type": "module"` 时，本地导入必须包含 `.js` 扩展名。`tsconfig.json` 的 `module` 和 `moduleResolution` 选项（例如 `NodeNext`）至关重要。
4.  **PM2 管理与 Node.js 模块兼容性**：PM2 在 ES Module 项目中可能需要通过 `ecosystem.config.cjs` 进行明确配置，或者进行彻底的停止和重启（`pm2 delete` 后 `pm2 start`）以确保加载最新代码。
5.  **Nginx 配置与目录权限**：Nginx `root` 路径必须正确，且 Nginx 运行用户需要有访问所有父目录的执行权限。
6.  **耐心与系统性调试**：遇到复杂问题时，需要一步步排除，从小范围测试开始，逐步扩大，并仔细分析每一步的错误日志。

希望这份复盘对你有所帮助！
