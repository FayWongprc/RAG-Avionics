## RAG-Avionics
基于 `data/Avionics_standards/` 内的航空/机载标准 PDF（例如 DO-178C、ARP4754A、IEEE 829），实现：
- **需求原子化分解**（把一段需求拆成可验证的原子需求）
- **RAG 证据检索**（从标准/规范中检索支撑片段）
- **IEEE 829 风格测试用例生成**（带 trace 与证据引用，便于展示“可追溯性”）
- **Streamlit UI** 一键演示


### 1) 安装依赖

在项目根目录执行：

```bash
pip install -r requirements.txt
```
### 2) 配置 API Key

在 `.env`（或直接设置系统环境变量），填写你的 Key：

```text
DEEPSEEK_API_KEY=xxxxxxxx
```

> 注意：本仓库出于安全策略不创建/提交 `.env` 文件。

### 3) 启动 UI

```bash
streamlit run streamlit_app.py
```

首次运行建议在侧边栏勾选 **重建向量库**。向量库会持久化到 `storage/qdrant/`。

