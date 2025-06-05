# 植物大战僵尸植物图鉴

一个从植物大战僵尸中文维基抓取植物信息并生成静态网站的工具。

## 🌟 特性

- 🌱 自动抓取最新的植物信息
- 🎨 美观的响应式界面
- 🔍 实时搜索功能
- 📱 移动端优化
- 🚀 GitHub Pages 自动部署
- 📊 动态植物统计

## 🚀 部署到 GitHub Pages

### 1. 仓库设置

1. Fork 或 clone 此仓库到你的 GitHub 账户
2. 确保仓库是公开的（GitHub Pages 免费版需要公开仓库）

### 2. 启用 GitHub Pages

1. 进入仓库的 **Settings** 页面
2. 在左侧菜单中点击 **Pages**
3. 在 **Source** 部分选择 **GitHub Actions**

### 3. 自动部署配置

项目已配置了 GitHub Actions 工作流程 (`.github/workflows/deploy.yml`)，会在以下情况自动运行：

- 📝 推送到 `main` 分支时
- 🕕 每天早上 6 点 UTC（北京时间下午 2 点）
- 🔄 手动触发（在 Actions 页面点击"Run workflow"）

### 4. 访问网站

部署完成后，你的网站将在以下地址可用：

```
https://[你的用户名].github.io/[仓库名]
```

## 🛠️ 本地开发

### 环境要求

- Python 3.11+
- uv（Python 包管理器）

### 安装依赖

```bash
# 使用 uv 安装依赖
uv sync
```

### 运行爬虫

```bash
# 运行主要的爬虫脚本
uv run python main.py
```

### 生成索引页面

```bash
# 生成动态索引页面
python generate_index.py
```

### 本地预览

```bash
# 在 docs 目录启动本地服务器
cd docs
python -m http.server 8000
```

然后在浏览器中访问 http://localhost:8000

## 📁 项目结构

```
pvz-wiki-scraper/
├── .github/workflows/
│   └── deploy.yml          # GitHub Actions 部署配置
├── docs/                   # GitHub Pages 输出目录
│   ├── index.html         # 动态生成的主页
│   ├── *.html             # 植物详情页面
│   ├── styles/            # CSS 样式文件
│   └── images/            # 植物图片
├── output/                # 爬虫输出目录
├── utils/                 # 工具模块
├── templates/             # HTML 模板
├── styles/                # 原始样式文件
├── scraper.py             # 主爬虫脚本
├── generate_index.py      # 索引页面生成器
└── main.py               # 入口脚本
```

## 🔧 自定义配置

### 修改爬取频率

编辑 `.github/workflows/deploy.yml` 中的 cron 表达式：

```yaml
schedule:
  - cron: "0 6 * * *" # 每天 6:00 UTC
```

### 自定义域名

1. 在仓库设置的 Pages 部分添加自定义域名
2. 在 `docs/` 目录下创建 `CNAME` 文件，内容为你的域名

### 修改样式

编辑 `styles/style.css` 来自定义网站外观。

## 🤝 贡献

欢迎提交 Issues 和 Pull Requests！

## 📄 许可证

此项目采用 MIT 许可证。

## 🙏 致谢

- 数据来源：[植物大战僵尸中文维基](https://plantsvszombies.fandom.com/zh/wiki/)
- 托管服务：[GitHub Pages](https://pages.github.com/)
