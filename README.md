# 🎪 Hajimi King 🏆

人人都是哈基米大王 👑，注意项目核心的核心是query.txt的表达式 ✨

## 🚀 核心功能

1. **GitHub搜索Gemini Key** 🔍 - 基于自定义查询表达式搜索GitHub代码中的API密钥
2. **代理支持** 🌐 - 支持多代理轮换，提高访问稳定性和成功率
3. **增量扫描** 📊 - 支持断点续传，避免重复扫描已处理的文件
4. **智能过滤** 🚫 - 自动过滤文档、示例、测试文件，专注有效代码
5. **外部同步** 🔄 - 支持向Gemini-Balancer和GPT-Load同步发现的密钥

## 📋 目录 🗂️

- [本地部署](#-本地部署) 🏠
- [Docker部署](#-docker部署) 🐳
- [配置变量说明](#-配置变量说明) ⚙️

---

## 🖥️ 本地部署 🚀

### 1. 环境准备 🔧

```bash
# 确保已安装Python
python --version

# 安装uv包管理器（如果未安装）
pip install uv
```

### 2. 项目设置 📁

```bash
# 克隆项目
git clone <repository-url>
cd hajimi-king

# 复制配置文件
cp env.example .env

# 复制查询文件
cp queries.example queries.txt
```

### 3. 配置环境变量 🔑

编辑 `.env` 文件，**必须**配置GitHub Token：

```bash
# 必填：GitHub访问令牌
GITHUB_TOKENS=ghp1,ghp2,ghp3

# 可选：其他配置保持默认值即可
```

> 💡 **获取GitHub Token**：访问 [GitHub Settings > Tokens](https://github.com/settings/tokens)，创建具有 `public_repo` 权限的访问令牌 🎫

### 4. 安装依赖并运行 ⚡

```bash
# 安装项目依赖
uv pip install -r pyproject.toml

# 创建数据目录
mkdir -p data

# 运行程序
python app/hajimi_king.py
```

### 5. 本地运行管理 🎮

```bash
# 查看日志文件
tail -f data/keys/keys_valid_detail_*.log

# 查看找到的有效密钥
cat data/keys/keys_valid_*.txt

# 停止程序
Ctrl + C
```

---

## 🐳 Docker部署 🌊

### 1. 准备部署脚本 📜

```bash
# 将deploy.sh复制到父目录
cd ${deploy_directory}

git clone <repository-url>

cp hajimi-king/first_deploy.sh ./

# 或者直接下载项目到某个目录，确保目录结构如下：
# deploy_directory/
# ├── first_deploy.sh
# └── hajimi-king/
#     ├── app
#     └── ...
```

### 2. 一键部署 🚀

```bash
# 运行部署脚本
chmod +x first_deploy.sh

./first_deploy.sh
```

部署脚本会自动完成以下步骤：
1. ✅ 检查Docker环境 🔍
2. ✅ 创建data目录 📁
3. ✅ 复制配置文件（.env, queries.txt）📄
4. ✅ 交互式配置GitHub Token 🎛️
5. ✅ 构建Docker镜像 🏗️
6. ✅ 启动服务 🎉

### 3. 使用预构建镜像 🏗️

项目已配置GitHub Actions自动构建，可直接使用预构建镜像：

```bash
# 拉取最新镜像（main分支）
docker pull ghcr.io/your-username/hajimi-king:latest

# 拉取开发版本（dev分支）
docker pull ghcr.io/your-username/hajimi-king:dev

# 拉取特定版本
docker pull ghcr.io/your-username/hajimi-king:v1.0.0
```

> 💡 **自动构建触发条件**：
> - 推送到 `main` 或 `dev` 分支时自动构建
> - 创建版本标签（如 `v1.0.0`）时自动构建
> - 支持 `linux/amd64` 和 `linux/arm64` 架构

### 4. 文件位置 🗺️

部署后的文件结构：
```
deploy_directory/
├── .env                    # 环境配置
├── docker-compose.yml      # Docker编排配置
├── data/                   # 数据目录
│   ├── keys/               # 密钥文件目录
│   │   ├── keys_valid_*.txt      # 有效密钥
│   │   ├── key_429_*.txt         # 限流密钥
│   │   └── keys_send_*.txt       # 发送记录
│   ├── logs/               # 日志文件目录
│   │   ├── keys_valid_detail_*.log    # 详细日志
│   │   ├── key_429_detail_*.log       # 限流详细日志
│   │   └── keys_send_detail_*.log     # 发送详细日志
│   ├── queries.txt         # 搜索查询配置
│   ├── checkpoint.json     # 扫描进度
│   └── scanned_shas.txt    # 已扫描文件记录
└── hajimi-king/            # 源码目录
```

---

## ⚙️ 配置变量说明 📖

以下是所有可配置的环境变量，在 `.env` 文件中设置：

### 🔴 必填配置 ⚠️

| 变量名 | 说明 | 示例值 |
|--------|------|--------|
| `GITHUB_TOKENS` | GitHub API访问令牌，多个用逗号分隔 🎫 | `ghp_token1,ghp_token2` |

### 🟡 重要配置（建议了解）🤓

| 变量名 | 默认值                | 说明                        |
|--------|--------------------|---------------------------|
| `DATA_PATH` | `/app/data`        | 数据存储目录路径 📂                  |
| `DATE_RANGE_DAYS` | `730`              | 仓库年龄过滤（天数），只扫描指定天数内的仓库 📅    |
| `QUERIES_FILE` | `queries.txt`      | 搜索查询配置文件路径（表达式严重影响搜索的高效性) 🎯 |
| `HAJIMI_CHECK_MODEL` | `gemini-2.5-flash` | 用于验证key有效的模型 🤖              |

### 🟢 可选配置（不懂就别动）😅

| 变量名                              | 默认值                                | 说明 |
|----------------------------------|------------------------------------|------|
| `PROXY`                          | 空                                  | 代理服务器地址，格式：`http://proxy:port` 🌐 |
| `VALID_KEY_PREFIX`               | `keys/keys_valid_`                 | 有效密钥文件名前缀 🗝️ |
| `RATE_LIMITED_KEY_PREFIX`        | `keys/key_429_`                    | 频率限制密钥文件名前缀 ⏰ |
| `KEYS_SEND_PREFIX`               | `keys/keys_send_`                  | 发送到外部应用的密钥文件名前缀 🚀 |
| `VALID_KEY_DETAIL_PREFIX`        | `logs/keys_valid_detail_`          | 详细日志文件名前缀 📝 |
| `RATE_LIMITED_KEY_DETAIL_PREFIX` | `logs/key_429_detail_`             | 频率限制详细日志文件名前缀 📊 |
| `VALID_KEY_DETAIL_PREFIX`        | `logs/keys_valid_detail_`          | 有效密钥文件名前缀 🗝️ |
| `SCANNED_SHAS_FILE`              | `scanned_shas.txt`                 | 已扫描文件SHA记录文件名 📋 |
| `FILE_PATH_BLACKLIST`            | `readme,docs,doc/,.md,example,...` | 文件路径黑名单，逗号分隔 🚫 |

### 配置文件示例 💫

完整的 `.env` 文件示例：

```bash
# 必填配置
GITHUB_TOKENS=ghp_your_token_here_1,ghp_your_token_here_2

# 重要配置（可选修改）
DATA_PATH=/app/data
DATE_RANGE_DAYS=730
QUERIES_FILE=queries.txt
HAJIMI_CHECK_MODEL=gemini-2.5-flash
PROXY=

# 高级配置（建议保持默认）
VALID_KEY_PREFIX=keys/keys_valid_
RATE_LIMITED_KEY_PREFIX=keys/key_429_
KEYS_SEND_PREFIX=keys/keys_send_
VALID_KEY_DETAIL_PREFIX=logs/keys_valid_detail_
RATE_LIMITED_KEY_DETAIL_PREFIX=logs/key_429_detail_
KEYS_SEND_DETAIL_PREFIX=logs/keys_send_detail_
SCANNED_SHAS_FILE=scanned_shas.txt
FILE_PATH_BLACKLIST=readme,docs,doc/,.md,example,sample,tutorial,test,spec,demo,mock
```

### 查询配置文件 🔍

编辑 `queries.txt` 文件自定义搜索规则：

⚠️ **重要提醒**：query 是本项目的核心！好的表达式可以让搜索更高效，需要发挥自己的想象力！🧠💡

```bash
# GitHub搜索查询配置文件
# 每行一个查询语句，支持GitHub搜索语法
# 以#开头的行为注释，空行会被忽略

# 基础搜索
AIzaSy in:file
AizaSy in:file filename:.env
```

> 📖 **搜索语法参考**：[GitHub Code Search Syntax](https://docs.github.com/en/search-github/searching-on-github/searching-code) 📚  
> 🎯 **核心提示**：创造性的查询表达式是成功的关键，多尝试不同的组合！

---

## 🔒 安全注意事项 🛡️

- ✅ GitHub Token权限最小化（只需`public_repo`读取权限）🔐
- ✅ 定期轮换GitHub Token 🔄
- ✅ 不要将真实的API密钥提交到版本控制 🙈
- ✅ 定期检查和清理发现的密钥文件 🧹
- ✅ 运行在安全的网络环境中 🏠

💖 **享受使用 Hajimi King 的快乐时光！** 🎉✨🎊

