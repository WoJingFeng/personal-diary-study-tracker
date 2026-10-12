# 迹页 · 日记与学习

一个适合个人使用的日记与学习追踪网站，包含日记、学习记录、统计图表、搜索筛选和简单单用户登录。

公开演示地址：https://wojingfeng.github.io/personal-diary-study-tracker/

公开演示由 GitHub Pages 托管，数据保存在当前浏览器的 localStorage 中。它可以直接使用，但不同设备不会同步数据；Flask + SQLite 后端版尚未在线部署。

## 功能

- 每日日记：日期、标题、正文、心情标签。
- 学习追踪：日期、科目、学习时长、内容总结、完成度、是否完成。
- 首页看板：最近 7 天日记数量、累计学习时长、已完成学习记录、最近一周学习时长柱状图。
- 搜索筛选：按关键词、标签、科目、日期范围筛选。
- 简单登录：启动时自动创建一个默认用户。
- 后端版：Flask + SQLite 自动建表，可按需部署到带持久存储的平台。

## 项目结构

```text
personal-diary-study-tracker/
├─ app.py
├─ extensions.py
├─ models.py
├─ requirements.txt
├─ Procfile
├─ render.yaml
├─ .env.example
├─ README.md
├─ demo.html
├─ preview.html
├─ instance/
│  └─ app.db
├─ templates/
│  ├─ base.html
│  ├─ login.html
│  ├─ index.html
│  ├─ diary_form.html
│  ├─ diaries.html
│  ├─ study_form.html
│  ├─ study_logs.html
│  └─ search.html
└─ static/
   ├─ css/
   │  ├─ app.css
   │  └─ refresh.css
   └─ js/
      └─ dashboard.js
```

## 先看成品界面

直接访问上方公开演示地址，或双击打开 `demo.html`。演示版不需要安装 Python 依赖，可以新增、编辑、删除日记和学习记录，图表也会跟着变化。演示数据保存在当前浏览器的 localStorage 中。

也可以打开 `preview.html`。这是静态视觉预览页，只用于快速看整体界面。

真正运行 Flask 后，页面数据会来自 SQLite 数据库。

## Windows 本地运行

建议在普通 PowerShell 或 Windows Terminal 里执行，不要在权限受限的终端里执行。

1. 进入项目目录：

```powershell
cd personal-diary-study-tracker
```

2. 复制环境变量文件：

```powershell
copy .env.example .env
```

3. 打开 `.env`，至少修改密码：

```env
SECRET_KEY=replace-with-a-long-random-secret
APP_USERNAME=admin
APP_PASSWORD=your-own-password
DATABASE_URL=
```

4. 创建虚拟环境：

```powershell
python -m venv .venv
```

如果你的电脑使用 `py` 启动器，也可以用：

```powershell
py -3 -m venv .venv
```

5. 激活虚拟环境：

```powershell
.\.venv\Scripts\Activate.ps1
```

如果 PowerShell 阻止激活脚本，可临时允许当前窗口执行：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

6. 安装依赖：

```powershell
pip install -r requirements.txt
```

7. 启动网站：

```powershell
flask --app app run --debug
```

8. 打开浏览器访问：

```text
http://127.0.0.1:5000
```

默认登录账号由 `.env` 决定。若你没有修改 `.env`，默认是：

```text
用户名：admin
密码：change-me
```

数据库文件会自动生成在：

```text
instance/app.db
```

## 部署到 Render

项目已经包含 `Procfile` 和 `render.yaml`。Render 官方文档可参考：

- Flask 部署文档：https://render.com/docs/deploy-flask
- Blueprint 配置文档：https://render.com/docs/blueprint-spec
- 持久磁盘文档：https://render.com/docs/disks

### 方式一：使用 render.yaml Blueprint

1. 把整个项目推送到 GitHub。

2. 打开 Render Dashboard，选择：

```text
New > Blueprint
```

3. 连接你的 GitHub 仓库。

4. Render 会读取 `render.yaml`，创建免费 Web Service。

5. 在创建过程中设置 `APP_PASSWORD`。这是登录密码，不要留空。

6. 部署完成后，打开 Render 给你的域名。免费服务不带持久磁盘，因此当前配置只适合试运行，重启或重新部署后 SQLite 数据可能丢失。

`render.yaml` 当前配置：

```yaml
services:
  - type: web
    name: personal-diary-study-tracker
    runtime: python
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn app:app --bind 0.0.0.0:$PORT
    healthCheckPath: /health
    envVars:
      - key: SECRET_KEY
        generateValue: true
      - key: APP_USERNAME
        value: admin
      - key: APP_PASSWORD
        sync: false
```

### 方式二：手动创建 Web Service

1. Render Dashboard 选择：

```text
New > Web Service
```

2. 连接 GitHub 仓库。

3. 设置：

```text
Runtime: Python
Build Command: pip install -r requirements.txt
Start Command: gunicorn app:app --bind 0.0.0.0:$PORT
```

4. 添加环境变量：

```text
SECRET_KEY = 一串长随机字符
APP_USERNAME = admin
APP_PASSWORD = 你的登录密码
DATABASE_URL = sqlite:////var/data/app.db
```

5. 如果希望数据长期保存，需要升级到支持持久磁盘的实例，并添加持久磁盘：

```text
Name: diary-study-data
Mount Path: /var/data
Size: 1 GB
```

6. 部署并打开 Render 域名。

## 关于 SQLite 和 Render 的重要提醒

SQLite 是文件数据库。部署到 Render 时，如果数据库文件放在普通应用目录，服务重启或重新部署后可能丢失。

所以线上长期使用 SQLite 时，建议升级到支持持久磁盘的实例，设置：

```text
DATABASE_URL=sqlite:////var/data/app.db
```

并且必须配置持久磁盘挂载到：

```text
/var/data
```

如果你以后想做多人用户、备份、跨实例扩展，建议把数据库换成 PostgreSQL。

## 常见问题

### 修改密码后为什么旧用户还能登录？

应用启动时只会在数据库里没有默认用户时创建用户。已经创建过用户后，修改 `.env` 不会自动覆盖旧密码。

简单处理方式：本地删除 `instance/app.db`，再重新启动应用。线上不要随便删除数据库文件，除非你确认要清空数据。

### 能不能支持真正的 Markdown？

当前正文用纯文本换行显示，安全且简单。以后可以加 `markdown` 包，把正文渲染为 HTML，但需要额外做 XSS 安全处理。

### 数据如何备份？

本地备份 `instance/app.db`。

Render 上如果使用持久磁盘，数据库文件在 `/var/data/app.db`。可以后续加一个下载备份路由，或改用 PostgreSQL 后使用数据库备份工具。
