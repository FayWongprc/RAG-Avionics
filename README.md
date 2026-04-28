# 🚀 基于RAG的机载软件需求自动解析与测试用例生成系统

> **全新架构**: FastAPI + React | 前后端分离 | 现代化 UI

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.3+-61DAFB.svg)](https://react.dev/)

基于 `data/Avionics_standards/` 内的航空/机载标准 PDF（例如 DO-178C、ARP4754A、IEEE 829），实现：

✨ **核心功能**
- 🔍 **需求原子化分解**：将复杂需求拆解为可验证的原子需求
- 📚 **RAG 证据检索**：从标准/规范中检索支撑片段（双路检索：标准文档 + SRD）
- 📝 **IEEE 829 测试用例生成**：自动生成带追溯性的测试用例
- 🎯 **术语词典匹配**：精确匹配航空专业术语定义
- 📊 **Excel 导出**：一键导出追溯矩阵

🎨 **技术亮点**
- 前后端分离架构，彻底解决 Qdrant 锁文件冲突
- 单例模式管理向量索引，后端只启动一次
- 现代化 React UI，响应式设计
- RESTful API，易于集成和扩展

---

## 📦 快速开始

### 1. 安装后端依赖

```bash
# 激活虚拟环境（如果有）
rag_venv\Scripts\activate

# 安装 Python 依赖
pip install -r requirements.txt
```

### 2. 安装前端依赖

```bash
cd frontend
npm install
cd ..
```

### 3. 配置 API Key

在项目根目录创建 `.env` 文件，填写至少一个 LLM API Key：

```env
# 千问（推荐）
DASHSCOPE_API_KEY=your_qwen_api_key

# DeepSeek
DEEPSEEK_API_KEY=your_deepseek_api_key

# 智谱AI
ZHIPU_API_KEY=your_zhipu_api_key
```

### 4. 启动服务

**方式一：使用批处理脚本（推荐）**

打开两个终端窗口：

```bash
# 终端 1：启动后端
start_backend.bat

# 终端 2：启动前端
start_frontend.bat
```

**方式二：手动启动**

```bash
# 终端 1：后端
cd backend
python main.py

# 终端 2：前端
cd frontend
npm run dev
```

### 5. 访问应用

- **前端界面**: http://localhost:5173
- **API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/api/health

### 6. 首次使用

1. 打开前端界面
2. 点击左侧"重建向量库"按钮（首次运行必须）
3. 等待索引构建完成（约 1-2 分钟）
4. 输入需求文本，点击"生成原子需求 + 测试用例"

---

## 🏗️ 项目结构

```
RAG-Avionics/
├── backend/                    # FastAPI 后端
│   └── main.py                # API 主入口（单例模式管理索引）
├── frontend/                   # React 前端
│   ├── src/
│   │   ├── App.jsx            # 主应用组件
│   │   ├── main.jsx           # 入口文件
│   │   └── index.css          # 全局样式
│   ├── package.json
│   └── vite.config.js
├── rag_avionics/              # 核心业务逻辑
│   ├── indexing.py            # 向量索引构建（双分块策略）
│   ├── pipeline.py            # RAG 流程编排（LangGraph）
│   ├── llm.py                 # LLM 调用封装
│   ├── prompts.py             # Prompt 模板
│   ├── schemas.py             # 数据模型
│   ├── settings.py            # 配置管理
│   └── export_excel.py        # Excel 导出
├── data/                      # 知识库数据
│   ├── Avionics_standards/    # 标准文档（DO-178C, ARP4754A 等）
│   ├── Avionics_srd/          # 软件需求文档
│   └── avionics_terms.json    # 航空术语词典
├── storage/                   # 向量存储（Qdrant 本地持久化）
├── start_backend.bat          # 后端启动脚本
├── start_frontend.bat         # 前端启动脚本
├── requirements.txt           # Python 依赖
└── MIGRATION_GUIDE.md         # 迁移指南
```

---

## 🔧 技术栈

### 后端
- **FastAPI**: 现代 Python Web 框架，自动生成 API 文档
- **LlamaIndex**: RAG 框架，支持句子窗口检索
- **LangGraph**: 流程编排，状态管理
- **Qdrant**: 向量数据库（本地持久化）
- **HuggingFace**: 嵌入模型（bge-m3 多语言）

### 前端
- **React 18**: 声明式 UI 框架
- **Vite**: 极速构建工具
- **Tailwind CSS**: 实用优先的 CSS 框架
- **Axios**: HTTP 客户端
- **Lucide React**: 精美图标库

### LLM 支持
- 阿里千问（Qwen）
- DeepSeek
- 智谱AI（GLM）

---

## 📡 API 端点

### 健康检查
```http
GET /api/health
```

### 重建索引
```http
POST /api/rebuild-index
```

### 分析需求
```http
POST /api/analyze
Content-Type: application/json

{
  "requirement_text": "需求编号：REQ-LG-001...",
  "llm_provider": "qwen",
  "llm_model": "qwen3-max",
  "top_k": 3,
  "window_size": 4
}
```

### 导出 Excel
```http
POST /api/export-excel
Content-Type: application/json

{
  "requirement_text": "需求编号：REQ-LG-001...",
  "llm_provider": "qwen",
  "llm_model": "qwen3-max",
  "top_k": 3,
  "window_size": 4
}
```

完整 API 文档：http://localhost:8000/docs

---

## 🎯 核心特性

### 1. 双分块策略
- **标准文档**：句子窗口检索（精准匹配单句，扩展上下文）
- **SRD 文档**：固定大小分块（保证逻辑段落完整）

### 2. 双路检索
- **标准文档专线**：强制抓取标准证据（DO-178C, ARP4754A 等）
- **SRD 文档专线**：强制抓取 SRD 上下文
- 确保两类证据都被获取，避免单一来源偏差

### 3. 术语词典匹配
- O(1) 哈希查找，精确匹配航空专业术语
- 支持大小写不敏感、去空格等多种匹配策略
- 避免向量检索的语义漂移

### 4. 单例模式索引管理
- 后端启动时加载索引，全局唯一
- 彻底解决 Qdrant 多实例访问冲突
- 前端热重载不影响后端状态

---

## 🐛 常见问题

### Q1: 后端启动失败，提示 Qdrant 锁文件冲突
**解决方案**：
1. 关闭所有 Python 进程
2. 删除 `storage/qdrant/.lock`
3. 重新启动后端

### Q2: 前端无法连接后端
**检查**：
- 后端是否在 http://localhost:8000 运行
- 浏览器控制台是否有 CORS 错误
- 防火墙是否阻止了端口 8000

### Q3: 首次运行提示索引未加载
**解决方案**：
在前端界面点击"重建向量库"按钮，等待构建完成

### Q4: LLM 调用失败
**检查**：
- `.env` 文件中的 API Key 是否正确
- 网络是否能访问 LLM 服务
- API Key 是否有余额

---

## 📚 相关文档

- [迁移指南](MIGRATION_GUIDE.md) - 从 Streamlit 迁移到 FastAPI + React
- [双分块策略说明](双分块策略说明.md)
- [双路检索说明](双路检索说明.md)
- [句子窗口检索说明](句子窗口检索说明.md)

---

## 📄 License

MIT License

---

## 🙏 致谢

- [LlamaIndex](https://www.llamaindex.ai/) - RAG 框架
- [FastAPI](https://fastapi.tiangolo.com/) - Web 框架
- [React](https://react.dev/) - UI 框架
- [Qdrant](https://qdrant.tech/) - 向量数据库
- [Tailwind CSS](https://tailwindcss.com/) - CSS 框架

---

**有问题？** 查看 [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) 或提交 Issue
