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
from .prompts import (
    DECOMPOSE_PROMPT,
    DECOMPOSE_WITH_GUIDANCE_PROMPT,
    DOMAIN_QUERY_PROMPT,
    ATOMIC_REQ_GOLDEN_RULES,
    GENERATE_TESTCASES_PROMPT,
)
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
    domain_context: list[dict]
    atomic_requirements: list[AtomicRequirement]
    evidences: dict[str, list[dict]]
    test_cases: list[IEEE829TestCase]


def _safe_json_loads(text: str) -> Any:
    text = text.strip()
    if "{" in text and "}" in text:
        text = text[text.find("{") : text.rfind("}") + 1]
    try:
        return orjson.loads(text)
    except Exception:
        return json.loads(text)


# 最低相似度阈值：低于此分数的结果视为无关噪声，直接丢弃
DOMAIN_SCORE_THRESHOLD = 0.35


def build_graph(*, index: VectorStoreIndex, ms: ModelSettings):
    llm = make_deepseek_chat(ms, temperature=0.2)

    def pre_retrieve(state: RagState) -> RagState:
        """用 LLM 从需求中提取关键术语，再检索知识库获取准确定义和约束。"""
        req_text = state["requirement_text"]

        # Step 1: 让 LLM 提取关键术语
        prompt = DOMAIN_QUERY_PROMPT.format(requirement_text=req_text)
        resp = llm.invoke([HumanMessage(content=prompt)])
        raw_terms = getattr(resp, "content", str(resp)).strip()

        if raw_terms == "无" or not raw_terms:
            return {"domain_context": []}

        # Step 2: 每个术语检索知识库，带分数阈值过滤
        terms = [t.strip() for t in raw_terms.splitlines() if t.strip() and t.strip() != "无"]
        all_results: list[dict] = []
        seen_texts: set[str] = set()
        for term in terms[:4]:
            results = retrieve_context(index, term, top_k=2)
            for r in results:
                if r.get("score", 0) < DOMAIN_SCORE_THRESHOLD:
                    continue
                snippet = (r.get("text") or "")[:200]
                if snippet not in seen_texts:
                    seen_texts.add(snippet)
                    r["matched_term"] = term
                    all_results.append(r)

        all_results.sort(key=lambda x: x.get("score", 0), reverse=True)
        return {"domain_context": all_results[:5]}

    def decompose(state: RagState) -> RagState:
        domain_ctx = state.get("domain_context", [])

        if domain_ctx:
            domain_text = "\n\n".join(
                [
                    f"[{i+1}] ref={e.get('ref','KB')} score={e.get('score',0):.3f}\n{e.get('text','')[:800]}"
                    for i, e in enumerate(domain_ctx[:8])
                ]
            )
            prompt = DECOMPOSE_WITH_GUIDANCE_PROMPT.format(
                golden_rules=ATOMIC_REQ_GOLDEN_RULES,
                domain_text=domain_text,
                requirement_id=state.get("requirement_id", "UNKNOWN"),
                requirement_text=state["requirement_text"],
            )
        else:
            prompt = DECOMPOSE_WITH_GUIDANCE_PROMPT.format(
                golden_rules=ATOMIC_REQ_GOLDEN_RULES,
                domain_text="（未检索到相关领域术语，请根据需求文本和黄金准则进行分解）",
                requirement_id=state.get("requirement_id", "UNKNOWN"),
                requirement_text=state["requirement_text"],
            )

        resp = llm.invoke([HumanMessage(content=prompt)])
        data = _safe_json_loads(getattr(resp, "content", str(resp)))
        parsed = DecomposeOutput.model_validate(data)
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
            src_req = (ar.source_req or rid or "UNKNOWN").strip() or "UNKNOWN"
            for i, tc in enumerate(parsed.test_cases, start=1):
                if not tc.trace_to_atomic_req:
                    tc.trace_to_atomic_req = ar.req_id
                if not tc.trace_to_source_req:
                    tc.trace_to_source_req = ar.source_req or rid
                if not tc.evidence_refs and ev:
                    tc.evidence_refs = [e.get("ref", "KB") for e in ev[: min(2, len(ev))]]
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
    g.add_node("pre_retrieve", pre_retrieve)
    g.add_node("decompose", decompose)
    g.add_node("retrieve", retrieve)
    g.add_node("generate", generate)
    g.set_entry_point("pre_retrieve")
    g.add_edge("pre_retrieve", "decompose")
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
    m = re.search(r"需求编号\s*[:：]\s*([A-Za-z0-9][A-Za-z0-9_\-\.]*)", text)
    if m:
        return m.group(1).strip()
    m = re.search(r"\bREQ[^\s，。；;:：]{1,30}\b", text)
    if m:
        return m.group(0).strip()
    return None
