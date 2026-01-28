from __future__ import annotations

import json
import re
from typing import Any, TypedDict, Optional

import orjson
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END

from llama_index.core import VectorStoreIndex

from .indexing import retrieve_context
from .llm import make_deepseek_chat
from .prompts import DECOMPOSE_PROMPT, GENERATE_TESTCASES_PROMPT
from .schemas import (
    AtomicRequirement,
    DecomposeOutput,
    GenerateOutput,
    IEEE829TestCase,
)
from .settings import ModelSettings


class RagState(TypedDict, total=False):
    requirement_id: str
    requirement_text: str
    atomic_requirements: list[AtomicRequirement]
    evidences: dict[str, list[dict]]  # key: atomic req_id
    test_cases: list[IEEE829TestCase]


def _safe_json_loads(text: str) -> Any:
    """尽量容错地从 LLM 输出中提取 JSON。"""
    text = text.strip()
    # 常见情况：模型会输出多余前后说明，这里简单截取第一个 { 到最后一个 }
    if "{" in text and "}" in text:
        text = text[text.find("{") : text.rfind("}") + 1]
    try:
        return orjson.loads(text)
    except Exception:
        return json.loads(text)


def build_graph(*, index: VectorStoreIndex, ms: ModelSettings):
    llm = make_deepseek_chat(ms, temperature=0.2)

    def decompose(state: RagState) -> RagState:
        prompt = DECOMPOSE_PROMPT.format(
            requirement_id=state.get("requirement_id", "UNKNOWN"),
            requirement_text=state["requirement_text"],
        )
        resp = llm.invoke([HumanMessage(content=prompt)])
        data = _safe_json_loads(getattr(resp, "content", str(resp)))
        parsed = DecomposeOutput.model_validate(data)
        # 兜底：确保每条原子需求都带 source_req
        rid = state.get("requirement_id", "UNKNOWN")
        atomic: list[AtomicRequirement] = []
        for ar in parsed.atomic_requirements:
            if not ar.source_req:
                ar.source_req = rid
            atomic.append(ar)
        return {"atomic_requirements": atomic}

    def retrieve(state: RagState) -> RagState:
        evidences: dict[str, list[dict]] = {}
        for ar in state.get("atomic_requirements", []):
            query = ar.statement
            evidences[ar.req_id] = retrieve_context(index, query, top_k=ms.top_k)
        return {"evidences": evidences}

    def generate(state: RagState) -> RagState:
        test_cases: list[IEEE829TestCase] = []
        evidences = state.get("evidences", {})
        rid = state.get("requirement_id", "UNKNOWN")
        used_tc_ids: set[str] = set()

        for ar in state.get("atomic_requirements", []):
            ev = evidences.get(ar.req_id, [])
            # 给 LLM 的证据文本尽量短一些，避免爆 token
            evidence_text = "\n\n".join(
                [
                    f"[{i+1}] ref={e.get('ref','KB')} score={e.get('score', 0):.3f}\n{e.get('text','')[:1200]}"
                    for i, e in enumerate(ev[: ms.top_k])
                ]
            )
            prompt = GENERATE_TESTCASES_PROMPT.format(
                atomic_requirement_json=ar.model_dump_json(ensure_ascii=False),
                requirement_text=state.get("requirement_text", ""),
                evidence_text=evidence_text,
            )
            resp = llm.invoke([HumanMessage(content=prompt)])
            data = _safe_json_loads(getattr(resp, "content", str(resp)))
            parsed = GenerateOutput.model_validate(data)
            # 补强 trace 字段（即使模型漏了）
            src_req = (ar.source_req or rid or "UNKNOWN").strip() or "UNKNOWN"
            for i, tc in enumerate(parsed.test_cases, start=1):
                if not tc.trace_to_atomic_req:
                    tc.trace_to_atomic_req = ar.req_id
                if not tc.trace_to_source_req:
                    tc.trace_to_source_req = ar.source_req or rid
                # 补强证据引用：若模型不给，就用检索 TopN 的 ref 兜底
                if not tc.evidence_refs and ev:
                    tc.evidence_refs = [e.get("ref", "KB") for e in ev[: min(2, len(ev))]]

                # 用例ID必须唯一：工程侧统一规范化（不依赖 LLM 随机生成）
                # 格式：TC-{原始需求编号}-{原子需求ID}-{两位序号}
                base = f"TC-{src_req}-{ar.req_id}-{i:02d}"
                tc_id = base
                bump = 2
                while tc_id in used_tc_ids:
                    tc_id = f"{base}-{bump}"
                    bump += 1
                tc.tc_id = tc_id
                used_tc_ids.add(tc_id)
            test_cases.extend(parsed.test_cases)

        return {"test_cases": test_cases}

    g = StateGraph(RagState)
    g.add_node("decompose", decompose)
    g.add_node("retrieve", retrieve)
    g.add_node("generate", generate)
    g.set_entry_point("decompose")
    g.add_edge("decompose", "retrieve")
    g.add_edge("retrieve", "generate")
    g.add_edge("generate", END)
    return g.compile()


def run_pipeline(
    *,
    index: VectorStoreIndex,
    ms: ModelSettings,
    requirement_text: str,
) -> RagState:
    graph = build_graph(index=index, ms=ms)
    rid = extract_requirement_id(requirement_text) or "UNKNOWN"
    return graph.invoke({"requirement_id": rid, "requirement_text": requirement_text})


def extract_requirement_id(text: str) -> Optional[str]:
    """从输入文本中尽量提取“需求编号”。"""
    # 常见格式：需求编号：REQ-LG-001 / 需求编号: REQ_XXX_01
    m = re.search(r"需求编号\s*[:：]\s*([A-Za-z0-9][A-Za-z0-9_\-\.]*)", text)
    if m:
        return m.group(1).strip()
    # 兜底：如果用户直接写 REQ-XXX-001
    m = re.search(r"\bREQ[^\s，。；;:：]{1,30}\b", text)
    if m:
        return m.group(0).strip()
    return None

