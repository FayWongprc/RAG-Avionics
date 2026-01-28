from __future__ import annotations

import textwrap
from dataclasses import replace
import streamlit as st

from rag_avionics.indexing import build_or_load_index
from rag_avionics.pipeline import run_pipeline
from rag_avionics.settings import load_settings
from rag_avionics.export_excel import build_traceability_excel


st.set_page_config(page_title="基于RAG的机载软件需求解析与测试用例生成系统", layout="wide")

paths, ms = load_settings()


@st.cache_resource
def _get_index(rebuild: bool):
    return build_or_load_index(paths=paths, ms=ms, rebuild=rebuild)


def _render_evidence(ev: list[dict]):
    for i, e in enumerate(ev, start=1):
        meta = e.get("metadata", {})
        ref = e.get("ref", "KB")
        st.markdown(f"**[{i}] {ref}** | score={e.get('score', 0):.3f}")
        st.code((e.get("text") or "")[:2200], language=None)


st.title("基于RAG的机载软件需求解析与测试用例生成系统")

with st.sidebar:
    st.header("系统设置")
    st.caption("知识库目录：`data/Avionics_files`（PDF 标准/规范）")
    rebuild = st.checkbox("重建向量库（首次运行建议勾选）", value=False)
    top_k = st.slider("Top-K（每条原子需求检索证据数）", 2, 12, ms.top_k)
    st.divider()
    st.caption("需要环境变量：`DEEPSEEK_API_KEY`")

default_req = textwrap.dedent(
    """
    需求编号：REQ-LG-001
    功能描述：起落架控制逻辑。
    具体规约：当且仅当起落架控制手柄（Gear Handle）处于“DOWN”位置，且飞行速度（Airspeed）低于 250 节时，
    起落架执行机构应在 3 秒内接收到“放下（Deploy）”指令。
    若速度超过 250 节，即使手柄在“DOWN”位，也不允许执行放下动作，并需触发告警。
    """
).strip()

req_text = st.text_area("输入需求（支持一段/多段）", value=default_req, height=180)

col_a, col_b = st.columns([1, 2])
with col_a:
    go = st.button("生成：原子需求 + IEEE829 用例", type="primary", use_container_width=True)
with col_b:
    st.caption(
        "提示：首次运行请在侧边栏勾选“重建向量库”。"
    )

if go:
    ms_runtime = replace(ms, top_k=top_k)
    with st.spinner("加载/构建索引..."):
        index = _get_index(rebuild=rebuild)

    with st.spinner("运行 RAG 流程（分解→检索→生成）..."):
        out = run_pipeline(index=index, ms=ms_runtime, requirement_text=req_text)

    atomic_reqs = out.get("atomic_requirements", [])
    evidences = out.get("evidences", {})
    test_cases = out.get("test_cases", [])

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

    st.subheader("IEEE 829 测试用例（简化模板）")
    if not test_cases:
        st.warning("未生成测试用例；请检查 API Key、模型输出或输入质量。")
    else:
        for tc in test_cases:
            with st.expander(f"{tc.tc_id} | trace={tc.trace_to_atomic_req}", expanded=False):
                st.markdown(f"**标题**：{tc.title}")
                st.markdown(f"**目的**：{tc.objective}")
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
            on_click="ignore",  # 防止页面刷新
        )