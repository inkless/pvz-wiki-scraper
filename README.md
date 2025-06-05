# 植物大战僵尸植物图鉴

一个从植物大战僵尸中文维基抓取植物信息并生成静态网站的工具。

## 🌟 特性

- 🌱 自动抓取最新的植物信息
- 🎨 美观的响应式界面
- 🔍 实时搜索功能
- 📱 移动端优化
- 🚀 GitHub Pages 部署支持
- 📊 动态植物统计

## 🚀 部署到 GitHub Pages

### 1. 仓库设置

1. Fork 或 clone 此仓库到你的 GitHub 账户
2. 确保仓库是公开的（GitHub Pages 免费版需要公开仓库）

### 2. 生成网站内容

```bash
# 运行完整的抓取和生成流程
uv run python main.py
```

这将：

- 抓取所有植物信息到 `docs/` 目录
- 自动生成索引页面
- 准备好所有 GitHub Pages 需要的文件

## 🛠️ 本地开发

### 环境要求

- Python 3.11+
- uv（现代 Python 包管理器）

### 安装依赖

```bash
# 使用 uv 安装依赖（自动创建虚拟环境）
uv sync
```

### 运行完整流程

```bash
# 运行主脚本（包含抓取和索引生成）
uv run python main.py
```

### 单独运行组件

```bash
# 仅运行爬虫
uv run python scraper.py --all

# 仅生成索引页面
uv run python generate_index.py
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
├── docs/                   # GitHub Pages 部署目录
│   ├── index.html         # 动态生成的主页
│   ├── *.html             # 植物详情页面
│   ├── styles/            # CSS 样式文件
│   └── images/            # 植物图片
├── templates/             # HTML 模板
│   └── index_template.html # 索引页面模板
├── utils/                 # 工具模块
├── config/                # 配置文件
├── scraper.py             # 主爬虫脚本
├── generate_index.py      # 索引页面生成器
├── main.py               # 入口脚本
├── pyproject.toml        # uv 项目配置
└── uv.lock              # uv 依赖锁定文件
```

## 🔧 配置选项

### 修改抓取设置

编辑 `config/settings.py` 来调整：

- 输出目录
- 请求延迟
- 图片处理选项

### 自定义样式

编辑 `docs/styles/style.css` 来自定义网站外观。

### 自定义模板

修改 `templates/index_template.html` 来调整主页布局。

## 🔄 更新网站

要更新网站内容：

1. 运行 `uv run python main.py` 生成最新内容
2. 提交更改到 Git
3. 推送到 GitHub
4. GitHub Pages 会自动更新

## 🤝 贡献

欢迎提交 Issues 和 Pull Requests！

## 📄 许可证

此项目采用 MIT 许可证。

## 🙏 致谢

- 数据来源：[植物大战僵尸中文维基](https://plantsvszombies.fandom.com/zh/wiki/)
- 托管服务：[GitHub Pages](https://pages.github.com/)
