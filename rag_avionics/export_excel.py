from __future__ import annotations
from io import BytesIO
from typing import Any
import pandas as pd
from .schemas import AtomicRequirement, IEEE829TestCase


def build_traceability_excel(state: dict[str, Any]) -> bytes:
    """将 pipeline 输出打包为 Excel（追溯矩阵 + 证据 + 明细）。"""
    requirement_id = state.get("requirement_id", "UNKNOWN")
    requirement_text = state.get("requirement_text", "")
    atomic_reqs: list[AtomicRequirement] = state.get("atomic_requirements", []) or []
    test_cases: list[IEEE829TestCase] = state.get("test_cases", []) or []
    evidences: dict[str, list[dict]] = state.get("evidences", {}) or {}

    # Requirements sheet
    df_req = pd.DataFrame(
        [
            {
                "source_req_id": requirement_id,
                "source_req_text": requirement_text,
            }
        ]
    )

    # Atomic requirements sheet
    df_atomic = pd.DataFrame(
        [
            {
                "source_req_id": ar.source_req or requirement_id,
                "atomic_req_id": ar.req_id,
                "category": ar.category,
                "atomic_statement": ar.statement,
                "source_text": ar.source_text,
            }
            for ar in atomic_reqs
        ]
    )

    # Evidence sheet (flatten)
    ev_rows: list[dict] = []
    for ar in atomic_reqs:
        for idx, e in enumerate(evidences.get(ar.req_id, []) or [], start=1):
            ev_rows.append(
                {
                    "atomic_req_id": ar.req_id,
                    "evidence_rank": idx,
                    "evidence_ref": e.get("ref", "KB"),
                    "score": e.get("score", 0.0),
                    "metadata": str(e.get("metadata", {})),
                    "text_snippet": (e.get("text") or "")[:1500],
                }
            )
    df_evidence = pd.DataFrame(ev_rows)

    # Test cases sheet
    df_tc = pd.DataFrame(
        [
            {
                "tc_id": tc.tc_id,
                "title": tc.title,
                "objective": tc.objective,
                "test_method": getattr(tc, 'test_method', ''),
                "design_rationale": getattr(tc, 'design_rationale', ''),
                "trace_to_source_req": tc.trace_to_source_req or requirement_id,
                "trace_to_atomic_req": tc.trace_to_atomic_req,
                "preconditions": "\n".join(tc.preconditions or []),
                "inputs": "\n".join(tc.inputs or []),
                "steps": "\n".join(tc.steps or []),
                "expected_results": "\n".join(tc.expected_results or []),
                "postconditions": "\n".join(tc.postconditions or []),
                "evidence_refs": "\n".join(tc.evidence_refs or []),
            }
            for tc in test_cases
        ]
    )

    # Traceability matrix (一行=一条测试用例)
    atomic_by_id = {ar.req_id: ar for ar in atomic_reqs}
    tm_rows: list[dict] = []
    for tc in test_cases:
        ar = atomic_by_id.get(tc.trace_to_atomic_req)
        tm_rows.append(
            {
                "source_req_id": tc.trace_to_source_req or (ar.source_req if ar else requirement_id),
                "atomic_req_id": tc.trace_to_atomic_req,
                "atomic_statement": ar.statement if ar else None,
                "tc_id": tc.tc_id,
                "tc_title": tc.title,
                "evidence_refs": "; ".join(tc.evidence_refs or []),
            }
        )
    df_tm = pd.DataFrame(tm_rows)

    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df_req.to_excel(writer, index=False, sheet_name="Requirements")
        df_atomic.to_excel(writer, index=False, sheet_name="AtomicRequirements")
        df_tc.to_excel(writer, index=False, sheet_name="TestCases")
        df_tm.to_excel(writer, index=False, sheet_name="TraceabilityMatrix")
        df_evidence.to_excel(writer, index=False, sheet_name="Evidence")

        # 简单美化：冻结首行 + 自动列宽（保守）
        for sheet_name, df in [
            ("Requirements", df_req),
            ("AtomicRequirements", df_atomic),
            ("TestCases", df_tc),
            ("TraceabilityMatrix", df_tm),
            ("Evidence", df_evidence),
        ]:
            ws = writer.sheets[sheet_name]
            ws.freeze_panes(1, 0)
            for col_idx, col in enumerate(df.columns):
                max_len = max([len(str(col))] + [len(str(v)) for v in df[col].head(50).tolist()])
                ws.set_column(col_idx, col_idx, min(max(12, max_len + 2), 60))

    return output.getvalue()

