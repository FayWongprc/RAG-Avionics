from __future__ import annotations
import json
import re
from typing import Any, TypedDict, Optional
from pathlib import Path
import orjson
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END
from llama_index.core import VectorStoreIndex
from .indexing import retrieve_context, retrieve_context_dual
from .llm import make_llm
from .prompts import (
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
    """尽量容错地从 LLM 输出中提取 JSON。"""
    text = text.strip()
    if "{" in text and "}" in text:
        text = text[text.find("{") : text.rfind("}") + 1]
    try:
        return orjson.loads(text)
    except Exception:
        pass
    try:
        return json.loads(text)
    except Exception:
        pass
    # 兜底：尝试修复被截断的 JSON（补齐缺失的括号）
    try:
        patched = text.rstrip().rstrip(",")
        # 数未闭合的括号
        open_braces = patched.count("{") - patched.count("}")
        open_brackets = patched.count("[") - patched.count("]")
        patched += "]" * max(open_brackets, 0)
        patched += "}" * max(open_braces, 0)
        return json.loads(patched)
    except Exception as e:
        raise ValueError(f"无法解析 LLM 输出的 JSON: {e}\n原文前500字符: {text[:500]}")


# 最低相似度阈值：低于此分数的结果视为无关噪声，直接丢弃
DOMAIN_SCORE_THRESHOLD = 0.35

# 用于支撑测试用例生成的严格阈值：确保喂给 LLM 的证据是高度相关的
EVIDENCE_SCORE_THRESHOLD = 0.45


def load_avionics_terms_dict(dict_path: str = "data/avionics_terms.json") -> dict:
    """加载航空术语词典（简单键值对格式）"""
    path = Path(dict_path)
    if not path.exists():
        print(f"⚠️ 未找到术语词典文件: {dict_path}")
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ 加载术语词典失败: {e}")
        return {}


def build_graph(*, index: VectorStoreIndex, ms: ModelSettings):
    llm = make_llm(ms, temperature=0.2)

    def pre_retrieve(state: RagState) -> RagState:
        """预检索节点：使用 LLM 提取术语，然后通过本地 JSON 词典进行 O(1) 哈希匹配。"""
        print("--- 正在执行预检索 (Pre-retrieve) ---")
        req_text = state["requirement_text"]

        # Step 1: 让 LLM 提取关键术语（严格 JSON 格式）
        prompt = DOMAIN_QUERY_PROMPT.format(requirement_text=req_text)
        resp = llm.invoke([HumanMessage(content=prompt)])
        raw_output = getattr(resp, "content", str(resp)).strip()

        # 解析 JSON 数组
        try:
            extracted_terms = _safe_json_loads(raw_output)
            if not isinstance(extracted_terms, list):
                print(f"  ⚠️ LLM 输出不是数组格式: {raw_output[:100]}")
                return {"domain_context": []}
            if not extracted_terms:
                print("  ⚠️ LLM 返回空数组，未提取到任何术语")
                return {"domain_context": []}
        except Exception as e:
            print(f"  ⚠️ 解析 LLM 输出失败: {e}")
            print(f"  原始输出: {raw_output[:200]}")
            return {"domain_context": []}

        print(f"  提取到的术语: {extracted_terms}")

        # Step 2: 加载本地术语词典
        terms_dict = load_avionics_terms_dict()
        if not terms_dict:
            print("  ⚠️ 术语词典为空，跳过匹配")
            return {"domain_context": []}

        # Step 3: 精确哈希匹配（O(1) 查找，大小写不敏感）
        domain_context = []
        for term in extracted_terms:
            if not isinstance(term, str):
                continue
            
            # 尝试多种匹配策略：原样、大写、去空格
            term_variants = [
                term,
                term.upper(),
                term.strip(),
                term.upper().strip(),
            ]
            
            matched = False
            for variant in term_variants:
                if variant in terms_dict:
                    definition = terms_dict[variant]
                    domain_context.append({
                        "matched_term": term,
                        "text": f"【{term}】: {definition}",
                        "ref": "术语词典",
                        "score": 1.0,  # 精确匹配，满分
                        "metadata": {"source": "avionics_terms.json"}
                    })
                    print(f"  ✓ 命中词典: {term} -> {variant}")
                    matched = True
                    break
            
            if not matched:
                print(f"  ✗ 词典未收录: {term} (已安全跳过)")

        if not domain_context:
            print("  ⚠️ 未匹配到任何术语定义")
        else:
            print(f"  ✓ 成功匹配 {len(domain_context)} 个术语")

        return {"domain_context": domain_context}

    # 旧的向量检索逻辑（已注释，保留备用）
    # def pre_retrieve_old(state: RagState) -> RagState:
    #     """用 LLM 从需求中提取关键术语，再检索知识库获取准确定义和约束。"""
    #     req_text = state["requirement_text"]
    #     prompt = DOMAIN_QUERY_PROMPT.format(requirement_text=req_text)
    #     resp = llm.invoke([HumanMessage(content=prompt)])
    #     raw_terms = getattr(resp, "content", str(resp)).strip()
    #     if raw_terms == "无" or not raw_terms:
    #         return {"domain_context": []}
    #     terms = [t.strip() for t in raw_terms.splitlines() if t.strip() and t.strip() != "无"]
    #     all_results: list[dict] = []
    #     seen_texts: set[str] = set()
    #     for term in terms[:4]:
    #         results = retrieve_context(index, term, top_k=2)
    #         for r in results:
    #             if r.get("score", 0) < DOMAIN_SCORE_THRESHOLD:
    #                 continue
    #             snippet = (r.get("text") or "")[:200]
    #             if snippet not in seen_texts:
    #                 seen_texts.add(snippet)
    #                 r["matched_term"] = term
    #                 all_results.append(r)
    #     all_results.sort(key=lambda x: x.get("score", 0), reverse=True)
    #     return {"domain_context": all_results[:5]}

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
        """双路检索：分别从标准文档和 SRD 文档中检索证据。"""
        evidences: dict[str, list[dict]] = {}
        for ar in state.get("atomic_requirements", []):
            query = ar.statement
            
            # 双路检索：标准文档 top_k 条 + SRD 文档 top_k 条
            # 总计最多 top_k * 2 条证据
            raw_results = retrieve_context_dual(
                index, 
                query, 
                standards_top_k=ms.top_k,  # 标准文档：top_k 条
                srd_top_k=ms.top_k         # SRD 文档：top_k 条
            )
            
            # 使用更严格的阈值过滤，确保找出的证据是高度相关的
            filtered_results = [r for r in raw_results if r.get("score", 0) >= EVIDENCE_SCORE_THRESHOLD]
            evidences[ar.req_id] = filtered_results
        
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
