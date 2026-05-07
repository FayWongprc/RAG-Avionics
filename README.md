# 🚀 基于RAG的机载软件需求自动解析与测试用例生成系统

> **全新架构**: FastAPI + React | 前后端分离 | 现代化 UI | 智能质量评估

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.3+-61DAFB.svg)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-6.0+-646CFF.svg)](https://vitejs.dev/)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.4+-38B2AC.svg)](https://tailwindcss.com/)

基于 `data/Avionics_standards/` 内的航空/机载标准 PDF（例如 DO-178C、ARP4754A、IEEE 829），实现：

✨ **核心功能**
- 🔍 **需求原子化分解**：将复杂需求拆解为可验证的原子需求
- 📚 **RAG 证据检索**：从标准/规范中检索支撑片段（双路检索：标准文档 + SRD）
- 📝 **IEEE 829 测试用例生成**：自动生成带追溯性的测试用例
- 🎯 **术语词典匹配**：精确匹配航空专业术语定义
- 📊 **四维质量评估**：LLM-as-a-Judge 深度评估测试用例质量 ⭐ 新增
- 📄 **Excel 导出**：一键导出完整追溯矩阵

🎨 **技术亮点**
- 前后端分离架构，彻底解决 Qdrant 锁文件冲突
- 单例模式管理向量索引，后端只启动一次
- 标签页式现代化 React UI，响应式设计
- RESTful API，易于集成和扩展
- LocalStorage 状态持久化，刷新不丢失数据

---


## 完整运行步骤

### 前置要求
- Python 3.10 或更高版本
- Node.js 18 或更高版本
- Git（可选，也可以直接下载 ZIP）

### 详细步骤

**1. 下载项目**
```bash
# 打开命令行（CMD 或 PowerShell）
# 进入你想存放项目的目录
cd Desktop

# 克隆项目
git clone https://github.com/FayWongprc/RAG-Avionics.git

# 进入项目目录
cd RAG-Avionics
```

**2. 创建 Python 虚拟环境**
```bash
# 创建虚拟环境
python -m venv rag_venv

# 激活虚拟环境（Windows）
rag_venv\Scripts\activate

# 激活虚拟环境（Linux/Mac）
# source rag_venv/bin/activate

# 看到命令行前面出现 (rag_venv) 就说明激活成功
```

**3. 安装 Python 依赖**
```bash
# 确保虚拟环境已激活（命令行前面有 (rag_venv)）
pip install -r requirements.txt

# 等待安装完成（约 2-3 分钟）
```

**4. 安装前端依赖**
```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 等待安装完成（约 3-5 分钟）

# 返回项目根目录
cd ..
```

**5. 配置 API Key**
```bash
# 复制配置模板
copy .env.example .env

# 用记事本打开配置文件
notepad .env

# 填写你的 API Key（至少一个），保存并关闭
```

**6. 启动后端服务**
```bash
# 打开第一个命令行窗口
# 进入项目目录
cd RAG-Avionics

# 启动后端
start_backend.bat

# ⚠️ 首次启动会下载嵌入模型（2.3GB，5-10分钟）
# 看到 "Application startup complete" 就说明启动成功
# 不要关闭这个窗口！
```

**7. 启动前端服务**
```bash
# 打开第二个命令行窗口
# 进入项目目录
cd RAG-Avionics

# 启动前端
start_frontend.bat

# 看到 "Local: http://localhost:5173/" 就说明启动成功
# 不要关闭这个窗口！
```

**8. 使用系统**
1. 浏览器打开：http://localhost:5173
2. 点击左侧"重建向量索引"按钮（首次运行必须）
3. 等待索引构建完成（约 1-2 分钟）
4. 开始使用系统！

---

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
python backend/main.py

# 终端 2：前端
cd frontend
npm run dev
```

⚠️ **首次启动注意事项**：
- 后端首次启动会自动下载嵌入模型（BAAI/bge-m3，约 2.3GB）
- 下载位置：`~/.cache/huggingface/hub/`（Windows: `C:\Users\用户名\.cache\huggingface\hub\`）
- 下载时间：约 5-10 分钟（取决于网速）
- 只需下载一次，后续启动直接使用缓存
- 如果下载失败，可以手动下载：https://huggingface.co/BAAI/bge-m3

### 5. 访问应用

- **前端界面**: http://localhost:5173
- **API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/api/health

### 6. 首次使用

1. 打开前端界面 http://localhost:5173
2. 点击左侧"重建向量索引"按钮（首次运行必须）
3. 等待索引构建完成（约 1-2 分钟）
4. 输入需求文本，点击"开始分析"
5. 查看原子需求和测试用例
6. 切换到"质量评估"标签页，点击"开始质量评估"
7. 查看四个维度的评估结果和改进建议
8. 切换到"导出报告"标签页，下载 Excel 文件

---

## 🏗️ 项目结构

```
RAG-Avionics/
├── backend/                    # FastAPI 后端
│   └── main.py                # API 主入口（单例模式管理索引）
├── frontend/                   # React 前端
│   ├── src/
│   │   ├── components/        # React 组件
│   │   │   ├── TabNavigation.jsx      # 标签页导航
│   │   │   ├── InputTab.jsx           # 需求输入
│   │   │   ├── AtomicRequirementsTab.jsx  # 原子需求展示
│   │   │   ├── TestCasesTab.jsx       # 测试用例展示
│   │   │   ├── EvaluationTab.jsx      # 质量评估 ⭐
│   │   │   └── ExportTab.jsx          # 导出报告
│   │   ├── App.jsx            # 主应用组件
│   │   ├── main.jsx           # 入口文件
│   │   └── index.css          # 全局样式
│   ├── package.json
│   ├── vite.config.js         # Vite 配置（含 API 代理）
│   ├── tailwind.config.js     # Tailwind CSS 配置
│   └── FRONTEND_V2_README.md  # 前端详细文档
├── rag_avionics/              # 核心业务逻辑
│   ├── evaluation/            # 质量评估模块 ⭐
│   │   ├── evaluator.py       # 四维评估器
│   │   ├── prompts.py         # 评估 Prompt
│   │   └── README.md          # 评估模块文档
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
└── README.md                  # 本文档
```

---

## 🔧 技术栈

### 后端
- **FastAPI**: 现代 Python Web 框架，自动生成 API 文档
- **LlamaIndex**: RAG 框架，支持句子窗口检索
- **LangGraph**: 流程编排，状态管理
- **Qdrant**: 向量数据库（本地持久化）
- **HuggingFace**: 嵌入模型（bge-m3 多语言）
- **Pydantic**: 数据验证和序列化

### 前端
- **React 18.3**: 声明式 UI 框架，Hooks 状态管理
- **Vite 6.0**: 极速构建工具，HMR 热更新
- **Tailwind CSS 3.4**: 实用优先的 CSS 框架
- **Axios 1.7**: HTTP 客户端，API 通信
- **Lucide React**: 精美图标库（1000+ 图标）
- **LocalStorage**: 前端状态持久化

### LLM 支持
- **阿里千问（Qwen）**: qwen3-max, qwen3.6-plus, qwen3.5-plus, qwen3.6-flash
- **DeepSeek**: deepseek-v4-flash, deepseek-v4-pro
- **智谱AI（GLM）**: glm-5.1, glm-5, glm-4.7, glm-4.7-FlashX

---

## 📡 API 端点

### 健康检查
```http
GET /api/health

响应示例:
{
  "status": "healthy",
  "index_loaded": true,
  "message": "系统运行正常"
}
```

### 重建索引
```http
POST /api/rebuild-index

响应示例:
{
  "status": "success",
  "message": "索引重建完成"
}
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

响应示例:
{
  "atomic_requirements": [...],
  "test_cases": [...],
  "terms": {...},
  "traceability_matrix": [...]
}
```

### 质量评估 ⭐ 新增
```http
POST /api/evaluate
Content-Type: application/json

{
  "result": {
    "atomic_requirements": [...],
    "test_cases": [...]
  },
  "enable_llm": true,
  "llm_provider": "qwen",
  "llm_model": "qwen3-max"
}

响应示例:
{
  "coverage": {
    "coverage_rate": 1.0,
    "total_requirements": 5,
    "covered_requirements": 5,
    "uncovered_requirements": []
  },
  "structure": {
    "structure_compliance_rate": 0.95,
    "total_test_cases": 20,
    "valid_test_cases": 19,
    "invalid_test_cases": [...]
  },
  "logic": {
    "average_llm_score": 4.2,
    "llm_scores": [...],
    "requirements_missing_robustness": [...]
  },
  "traceability": {
    "link_validity_rate": 0.98,
    "evidence_rate": 0.85,
    "broken_links": 1
  }
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

响应: Excel 文件下载
```

完整 API 文档：http://localhost:8000/docs

---

## 🎯 核心特性

### 1. 标签页式工作流 ⭐ 新增
前端采用 5 步标签页设计，清晰引导用户完成整个流程：

```
① 需求输入 → ② 原子需求 → ③ 测试用例 → ④ 质量评估 → ⑤ 导出报告
```

- **需求输入**：配置 LLM 参数，输入需求文本
- **原子需求**：查看分解后的原子需求、术语解释、检索证据
- **测试用例**：查看生成的测试用例，支持按测试方法过滤
- **质量评估**：四维度评估测试用例质量，LLM 深度打分
- **导出报告**：一键下载 Excel 追溯矩阵

### 2. 四维质量评估 ⭐ 新增
基于 **LLM-as-a-Judge** 理念，从四个维度评估测试用例质量：

#### 维度1：需求覆盖完整度
- 检查所有原子需求是否都被测试用例覆盖
- 识别未覆盖的需求，避免遗漏

#### 维度2：用例结构规范性
- 检查测试用例的核心字段是否完整
- 验证 IEEE 829 标准的结构合规性

#### 维度3：测试方法与逻辑合理性
- **静态分析**：检查正常测试和健壮性测试的覆盖情况
- **LLM 评分**：每个测试用例获得 1-5 分评分和改进建议
- **测试方法完整性**：分析五种测试方法的覆盖情况

#### 维度4：追溯链路与证据完整性
- 检查追溯矩阵的有效性
- 验证证据引用的完整性

### 3. 双分块策略
- **标准文档**：句子窗口检索（精准匹配单句，扩展上下文）
- **SRD 文档**：固定大小分块（保证逻辑段落完整）

### 4. 双路检索
- **标准文档专线**：强制抓取标准证据（DO-178C, ARP4754A 等）
- **SRD 文档专线**：强制抓取 SRD 上下文
- 确保两类证据都被获取，避免单一来源偏差

### 5. 术语词典匹配
- O(1) 哈希查找，精确匹配航空专业术语
- 支持大小写不敏感、去空格等多种匹配策略
- 避免向量检索的语义漂移

### 6. 单例模式索引管理
- 后端启动时加载索引，全局唯一
- 彻底解决 Qdrant 多实例访问冲突
- 前端热重载不影响后端状态

### 7. 状态持久化
- 使用 LocalStorage 保存用户输入、配置和分析结果
- 刷新页面不丢失数据，支持断点续传
- 自动保存评估结果，避免重复计算

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
- Vite 代理配置是否正确（`frontend/vite.config.js`）

### Q3: 首次运行提示索引未加载
**解决方案**：
在前端界面点击"重建向量索引"按钮，等待构建完成（约 1-2 分钟）

### Q4: LLM 调用失败
**检查**：
- `.env` 文件中的 API Key 是否正确
- 网络是否能访问 LLM 服务
- API Key 是否有余额
- 选择的模型是否可用

### Q5: 质量评估失败或评分异常
**检查**：
- 是否已经生成了分析结果（原子需求 + 测试用例）
- LLM API 是否正常（评估需要调用 LLM）
- 浏览器控制台是否有错误信息
- 尝试禁用 LLM 评估，只运行静态分析

### Q6: 前端页面刷新后数据丢失
**说明**：
- 正常情况下数据会自动保存到 LocalStorage
- 如果数据丢失，检查浏览器是否禁用了 LocalStorage
- 可以在浏览器开发者工具 → Application → Local Storage 中查看

### Q7: Excel 导出失败
**检查**：
- 后端 API 是否正常
- 浏览器是否允许下载
- 磁盘空间是否充足

---

## 📚 相关文档

- [前端详细文档](frontend/FRONTEND_V2_README.md) - React 组件、UI 设计、使用流程
- [评估模块文档](rag_avionics/evaluation/README.md) - 四维评估详解
- [前端集成指南](rag_avionics/evaluation/FRONTEND_INTEGRATION.md) - 评估功能集成
- [双分块策略说明](双分块策略说明.md) - 向量索引构建策略
- [双路检索说明](双路检索说明.md) - 标准文档 + SRD 双路检索
- [句子窗口检索说明](句子窗口检索说明.md) - 精准检索技术

---

## 🎨 前端特性

### UI/UX 设计
- **渐变色导航栏**：蓝-靛-紫渐变，现代化视觉
- **颜色编码系统**：
  - 🟢 绿色：良好 (≥90%)
  - 🔵 蓝色：正常 (≥70%)
  - 🟡 黄色：警告 (≥50%)
  - 🔴 红色：问题 (<50%)
- **响应式设计**：适配桌面和平板设备
- **自定义滚动条**：优化滚动体验

### 交互特性
- 标签页智能禁用（未生成结果前）
- 加载动画和进度提示
- 折叠/展开面板
- 实时系统状态指示器
- 确认对话框（防止误操作）
- 自动切换标签页（分析完成后）

### 数据管理
- LocalStorage 自动持久化
- 支持断点续传
- 一键重置功能
- 评估结果缓存

---

## 🚀 性能优化

### 后端优化
- 单例模式管理索引，避免重复加载
- 异步 API 设计，支持并发请求
- 向量索引持久化，启动即可用

### 前端优化
- Vite HMR 热更新，开发体验极佳
- Tailwind CSS JIT 编译，按需生成样式
- LocalStorage 缓存，减少重复计算
- 组件化设计，代码复用率高

---

## 📊 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                        用户浏览器                            │
│                   http://localhost:5173                     │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/REST API
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI 后端服务                          │
│                   http://localhost:8000                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  API 路由    │  │  业务逻辑    │  │  评估模块    │     │
│  │  /api/*      │→ │  pipeline.py │→ │  evaluator   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         ↓               ↓               ↓
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│   Qdrant    │  │  LLM API    │  │  知识库     │
│  向量数据库  │  │  千问/DS/智谱│  │  PDF/JSON   │
└─────────────┘  └─────────────┘  └─────────────┘
```

---

## 📄 License

MIT License

---

## 🙏 致谢

- [LlamaIndex](https://www.llamaindex.ai/) - RAG 框架
- [FastAPI](https://fastapi.tiangolo.com/) - Web 框架
- [React](https://react.dev/) - UI 框架
- [Vite](https://vitejs.dev/) - 构建工具
- [Qdrant](https://qdrant.tech/) - 向量数据库
- [Tailwind CSS](https://tailwindcss.com/) - CSS 框架
- [Lucide](https://lucide.dev/) - 图标库

---

## 📈 更新日志

### v2.0.0 (2024-01)
- ✨ 新增四维质量评估功能（LLM-as-a-Judge）
- ✨ 新增标签页式工作流 UI
- ✨ 新增 LocalStorage 状态持久化
- ✨ 新增测试方法完整性分析
- 🎨 全新 React + Tailwind CSS UI
- 🔧 前后端完全分离架构
- 🐛 修复 Qdrant 锁文件冲突问题

### v1.0.0 (2023-12)
- 🎉 初始版本发布
- ✨ 需求原子化分解
- ✨ RAG 证据检索（双路检索）
- ✨ IEEE 829 测试用例生成
- ✨ Excel 追溯矩阵导出

---

**有问题？** 查看 [前端文档](frontend/FRONTEND_V2_README.md) 或 [评估模块文档](rag_avionics/evaluation/README.md)
