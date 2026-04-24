from __future__ import annotations
import textwrap
from dataclasses import replace
import streamlit as st

from rag_avionics.indexing import build_or_load_index
from rag_avionics.pipeline import run_pipeline
from rag_avionics.settings import load_settings
from rag_avionics.export_excel import build_traceability_excel


def _render_evidence(ev: list[dict]):
    for i, e in enumerate(ev, start=1):
        ref = e.get("ref", "KB")
        category = e.get("category", "Unknown")
        category_label = "📘 标准" if category == "Standards" else "📄 SRD"
        st.markdown(f"**[{i}] {category_label} | {ref}** | score={e.get('score', 0):.3f}")
        st.code((e.get("text") or "")[:2200], language=None)


def _render_domain_context(domain_context: list[dict]):
    """显示匹配到的术语定义（来自本地词典）。"""
    if not domain_context:
        return
    
    for e in domain_context:
        term = e.get("matched_term", "未知术语")
        text = (e.get("text") or "").strip()
        ref = e.get("ref", "术语词典")
        
        with st.expander(f"术语：{term}", expanded=False):
            st.caption(f"来源：{ref}")
            st.markdown(text)


st.set_page_config(page_title="基于RAG的机载软件需求解析与测试用例生成系统", layout="wide")

paths, ms = load_settings()


@st.cache_resource
def _get_index(rebuild: bool):
    return build_or_load_index(paths=paths, ms=ms, rebuild=rebuild)


st.title("基于RAG的机载软件需求解析与测试用例生成系统")

with st.sidebar:
    st.header("系统设置")
    
    # LLM 模型选择
    st.subheader("🤖 LLM 模型")
    llm_provider = st.selectbox(
        "选择模型提供商",
        options=["qwen","deepseek", "zhipu"],
        format_func=lambda x: {"qwen": "阿里千问 (Qwen)","deepseek": "DeepSeek", "zhipu": "智谱AI (GLM)" }[x],
        index=0,  # 默认选择 qwen
        help="选择用于需求分解和测试用例生成的大语言模型"
    )
    
    # 根据选择的提供商显示不同的模型选项
    if llm_provider == "deepseek":
        llm_model = st.selectbox(
            "DeepSeek 模型",
            options=["deepseek-v4-flash", "deepseek-v4-pro"],
            index=0,
            help="💡 2026/4/24 DeepSeek-V4 的预览版本正式上线并同步开源"
        )
        api_key_hint = "DEEPSEEK_API_KEY"
    elif llm_provider == "zhipu":
        llm_model = st.selectbox(
            "智谱 GLM 模型",
            options=["glm-5.1", "glm-5", "glm-4.7", "glm-4.7-FlashX"],
            index=0,
            help="GLM-5.1 是最新旗舰模型"
        )
        api_key_hint = "ZHIPU_API_KEY"
    else:  # qwen
        llm_model = st.selectbox(
            "千问模型",
            options=["qwen3-max","qwen3.6-plus","qwen3.5-plus","qwen3.6-flash"],
            index=0,
            help="max为最强模型，plus能力均衡，flash速度最快"
        )
        api_key_hint = "DASHSCOPE_API_KEY"
    
    st.caption(f"需要环境变量：`{api_key_hint}`")
    
    st.divider()
    
    # 知识库设置
    st.subheader("📚 知识库")
    st.caption("知识库目录（PDF 标准/规范）")
    rebuild = st.checkbox("重建向量库（首次运行建议勾选）", value=False)
    top_k = st.slider("Top-K（原子需求双路检索证据数）", 2, 8, ms.top_k)
    window_size = st.slider("Window（句子窗口大小）", 2, 8, ms.sentence_window_size)
    
    st.divider()
    st.caption("✨ 使用句子窗口检索：精准匹配单句，扩展上下文")

default_req = textwrap.dedent(
    """
    需求编号：REQ-LG-001
    功能描述：起落架控制逻辑。
    具体规约：当且仅当起落架控制手柄（Gear Handle）处于"DOWN"位置，且飞行速度（Airspeed）低于 250 节时，
    起落架执行机构应在 3 秒内接收到"放下（Deploy）"指令。
    若速度超过 250 节，即使手柄在"DOWN"位，也不允许执行放下动作，并需触发告警。
    """
).strip()

req_text = st.text_area("输入需求（支持一段/多段）", value=default_req, height=180)

col_a, col_b = st.columns([1, 2])
with col_a:
    go = st.button("生成：原子需求 + IEEE829 用例", type="primary", use_container_width=True)
with col_b:
    st.caption('提示：首次运行请在侧边栏勾选"重建向量库"。')

if go:
    # 根据用户选择动态更新模型配置
    if llm_provider == "deepseek":
        ms_runtime = replace(
            ms, 
            llm_provider="deepseek",
            deepseek_model=llm_model,
            top_k=top_k, 
            sentence_window_size=window_size
        )
    elif llm_provider == "zhipu":
        ms_runtime = replace(
            ms, 
            llm_provider="zhipu",
            zhipu_model=llm_model,
            top_k=top_k, 
            sentence_window_size=window_size
        )
    else:  # qwen
        ms_runtime = replace(
            ms, 
            llm_provider="qwen",
            qwen_model=llm_model,
            top_k=top_k, 
            sentence_window_size=window_size
        )
    
    with st.spinner("加载/构建索引..."):
        index = _get_index(rebuild=rebuild)

    with st.spinner(f"运行 RAG 流程（使用 {llm_model}）..."):
        out = run_pipeline(index=index, ms=ms_runtime, requirement_text=req_text)

    domain_context = out.get("domain_context", [])
    atomic_reqs = out.get("atomic_requirements", [])
    evidences = out.get("evidences", {})
    test_cases = out.get("test_cases", [])

    st.subheader("领域术语解释")

    if domain_context:
        st.caption("从本地术语词典匹配到的专业术语定义，用于确保需求分解时术语准确无误：")
        _render_domain_context(domain_context)
    else:
        st.info("无相关术语解释（未匹配到词典中的专业术语）。")

    st.subheader("原子需求")

    if not atomic_reqs:
        st.warning("未得到原子需求结果；请检查模型输出或降低 temperature/简化输入。")
    else:
        for ar in atomic_reqs:
            with st.expander(f"{ar.req_id} | {ar.category or '未分类'}", expanded=False):
                st.write(ar.statement)
                if ar.source_req:
                    st.caption(f"来源需求：{ar.source_req}")
                if ar.source_text:
                    st.caption(f"来源文本片段：{ar.source_text[:200]}...")

                ev = evidences.get(ar.req_id, [])
                if ev:
                    st.markdown("**证据片段（检索结果）**")
                    _render_evidence(ev)
                else:
                    st.info("该原子需求没有检索到证据片段（可能是向量库为空或 top_k 太小）。")

    st.subheader("IEEE 829 测试用例生成")
    if not test_cases:
        st.warning("未生成测试用例；请检查 API Key、模型输出或输入质量。")
    else:
        for tc in test_cases:
            with st.expander(f"{tc.tc_id} | trace={tc.trace_to_atomic_req}", expanded=False):
                # 推导逻辑放在最上面
                if hasattr(tc, 'design_rationale') and tc.design_rationale:
                    st.info(f"💡 **推导逻辑**：{tc.design_rationale}")
                
                st.markdown(f"**标题**：{tc.title}")
                st.markdown(f"**目的**：{tc.objective}")
                if hasattr(tc, 'test_method') and tc.test_method:
                    st.markdown(f"**测试方法**：{tc.test_method}")
                if tc.preconditions:
                    st.markdown("**前置条件**")
                    st.write(tc.preconditions)
                if tc.inputs:
                    st.markdown("**输入/刺激**")
                    st.write(tc.inputs)
                if tc.steps:
                    st.markdown("**步骤**")
                    st.write(tc.steps)
                if tc.expected_results:
                    st.markdown("**期望结果**")
                    st.write(tc.expected_results)
                if tc.evidence_refs:
                    st.markdown("**证据引用**")
                    st.write(tc.evidence_refs)

    # Excel 导出
    if atomic_reqs and test_cases:
        st.divider()
        st.subheader("导出追溯矩阵（Excel）")
        excel_bytes = build_traceability_excel(out)
        req_id = out.get("requirement_id", "UNKNOWN")
        filename = f"traceability_{req_id}.xlsx"
        st.download_button(
            label="下载 Excel",
            data=excel_bytes,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            on_click="ignore",
        )
