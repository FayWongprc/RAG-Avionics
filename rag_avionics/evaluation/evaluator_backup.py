"""
评估器核心实现

基于生成的 Excel 文件进行四个维度的评估分析
"""

from __future__ import annotations
from typing import Any, Optional
from dataclasses import dataclass, field
from io import BytesIO
import pandas as pd
import numpy as np


@dataclass
class CoverageEvaluation:
    """需求覆盖完整度评估结果"""
    total_requirements: int
    covered_requirements: int
    coverage_rate: float
    uncovered_requirements: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "total_requirements": self.total_requirements,
            "covered_requirements": self.covered_requirements,
            "coverage_rate": round(self.coverage_rate, 4),
            "uncovered_requirements": self.uncovered_requirements,
        }


@dataclass
class StructureEvaluation:
    """用例结构规范性评估结果"""
    total_test_cases: int
    valid_test_cases: int
    structure_compliance_rate: float
    invalid_test_cases: list[dict] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "total_test_cases": self.total_test_cases,
            "valid_test_cases": self.valid_test_cases,
            "structure_compliance_rate": round(self.structure_compliance_rate, 4),
            "invalid_test_cases": self.invalid_test_cases,
        }


@dataclass
class LogicEvaluation:
    """测试方法与逻辑合理性评估结果"""
    total_requirements: int
    requirements_with_normal_test: int
    requirements_with_robustness_test: int
    requirements_with_both: int
    method_coverage_rate: float
    requirements_missing_robustness: list[str] = field(default_factory=list)
    llm_scores: list[dict] = field(default_factory=list)
    average_llm_score: float = 0.0
    requirement_coverage_analysis: list[dict] = field(default_factory=list)  # 新增：每个需求的覆盖分析
    
    def to_dict(self) -> dict:
        return {
            "total_requirements": self.total_requirements,
            "requirements_with_normal_test": self.requirements_with_normal_test,
            "requirements_with_robustness_test": self.requirements_with_robustness_test,
            "requirements_with_both": self.requirements_with_both,
            "method_coverage_rate": round(self.method_coverage_rate, 4),
            "requirements_missing_robustness": self.requirements_missing_robustness,
            "llm_scores": [
                {
                    "tc_id": score["tc_id"],
                    "score": score["score"],
                    "reasoning": score["reasoning"],
                    "issues": score.get("issues", [])
                }
                for score in self.llm_scores
            ],
            "average_llm_score": round(self.average_llm_score, 2),
            "requirement_coverage_analysis": self.requirement_coverage_analysis,
        }


@dataclass
class TraceabilityEvaluation:
    """追溯链路与证据完整性评估结果"""
    total_traceability_links: int
    valid_links: int
    broken_links: int
    link_validity_rate: float
    total_test_cases: int
    test_cases_with_evidence: int
    evidence_rate: float
    broken_link_details: list[dict] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "total_traceability_links": self.total_traceability_links,
            "valid_links": self.valid_links,
            "broken_links": self.broken_links,
            "link_validity_rate": round(self.link_validity_rate, 4),
            "broken_link_details": self.broken_link_details,
            "total_test_cases": self.total_test_cases,
            "test_cases_with_evidence": self.test_cases_with_evidence,
            "evidence_rate": round(self.evidence_rate, 4),
        }


@dataclass
class EvaluationResult:
    """完整的评估结果"""
    coverage: CoverageEvaluation
    structure: StructureEvaluation
    logic: LogicEvaluation
    traceability: TraceabilityEvaluation
    
    def to_dict(self) -> dict:
        return {
            "coverage": self.coverage.to_dict(),
            "structure": self.structure.to_dict(),
            "logic": self.logic.to_dict(),
            "traceability": self.traceability.to_dict(),
        }


def _is_empty_value(value: Any) -> bool:
    """检查值是否为空（NaN、None、空字符串、空白字符串）"""
    if pd.isna(value):
        return True
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    return False


def _parse_test_method(method_str: str) -> set[str]:
    """
    解析测试方法字符串，提取方法类型
    
    正常范围测试的关键词：正常、正常范围、nominal
    健壮性/异常测试的关键词：健壮、健壮性、异常、边界、robustness、boundary、exception
    """
    if _is_empty_value(method_str):
        return set()
    
    method_str = str(method_str).lower()
    methods = set()
    
    # 正常范围测试
    if any(kw in method_str for kw in ["正常", "nominal", "normal"]):
        methods.add("normal")
    
    # 健壮性/异常测试
    if any(kw in method_str for kw in ["健壮", "异常", "边界", "robustness", "boundary", "exception"]):
        methods.add("robustness")
    
    return methods


def call_llm_judge(prompt: str, llm=None) -> dict:
    """
    使用大模型评估测试用例的逻辑合理性
    
    Args:
        prompt: 评估提示词
        llm: LLM 实例（如果为 None，则使用模拟评分）
    
    Returns:
        {"score": 1-5, "reasoning": "评分理由", "issues": ["具体问题1", "问题2"]}
    """
    if llm is None:
        # 模拟评分（用于测试）
        import random
        score = random.randint(3, 5)
        return {
            "score": score,
            "reasoning": "模拟评分：基于测试方法、步骤和预期结果的完整性评估",
            "issues": []
        }
    
    # 真实的 LLM 调用
    from langchain_core.messages import HumanMessage
    import json
    
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        result_text = getattr(response, "content", str(response)).strip()
        
        # 解析 JSON 响应
        result = json.loads(result_text)
        
        # 确保返回格式正确
        return {
            "score": int(result.get("score", 3)),
            "reasoning": result.get("reasoning", ""),
            "issues": result.get("issues", [])
        }
    except Exception as e:
        print(f"⚠️ LLM 评分失败: {e}")
        return {
            "score": 3,
            "reasoning": f"评分失败: {str(e)}",
            "issues": []
        }


def evaluate_coverage(
    df_atomic: pd.DataFrame,
    df_test_cases: pd.DataFrame
) -> CoverageEvaluation:
    """
    评估维度1：需求覆盖完整度
    
    检查所有原子需求是否都被测试用例覆盖
    """
    # 提取所有原子需求 ID
    all_atomic_req_ids = set(df_atomic["atomic_req_id"].dropna().unique())
    
    # 提取测试用例中关联的原子需求 ID
    covered_req_ids = set(df_test_cases["trace_to_atomic_req"].dropna().unique())
    
    # 计算未覆盖的需求
    uncovered = sorted(list(all_atomic_req_ids - covered_req_ids))
    
    total = len(all_atomic_req_ids)
    covered = len(covered_req_ids)
    coverage_rate = covered / total if total > 0 else 0.0
    
    return CoverageEvaluation(
        total_requirements=total,
        covered_requirements=covered,
        coverage_rate=coverage_rate,
        uncovered_requirements=uncovered,
    )


def evaluate_structure(df_test_cases: pd.DataFrame) -> StructureEvaluation:
    """
    评估维度2：用例结构规范性
    
    检查测试用例的核心字段是否完整（无空值）
    """
    # 定义核心必填字段
    core_fields = [
        "tc_id",
        "title",
        "objective",
        "test_method",
        "preconditions",
        "inputs",
        "steps",
        "expected_results",
        "trace_to_atomic_req",
    ]
    
    total_cases = len(df_test_cases)
    invalid_cases = []
    
    for idx, row in df_test_cases.iterrows():
        missing_fields = []
        for field in core_fields:
            if field not in row or _is_empty_value(row[field]):
                missing_fields.append(field)
        
        if missing_fields:
            invalid_cases.append({
                "tc_id": row.get("tc_id", f"Row-{idx}"),
                "missing_fields": missing_fields,
            })
    
    valid_cases = total_cases - len(invalid_cases)
    compliance_rate = valid_cases / total_cases if total_cases > 0 else 0.0
    
    return StructureEvaluation(
        total_test_cases=total_cases,
        valid_test_cases=valid_cases,
        structure_compliance_rate=compliance_rate,
        invalid_test_cases=invalid_cases,
    )


def evaluate_logic(
    df_atomic: pd.DataFrame,
    df_test_cases: pd.DataFrame,
    enable_llm: bool = False,
    llm=None
) -> LogicEvaluation:
    """
    评估维度3：测试方法与逻辑合理性
    
    第一步：静态分组检查每个需求是否同时包含正常测试和健壮性测试
    第二步：可选的 LLM 盲评，评估测试步骤与声明方法的一致性
    
    Args:
        df_atomic: 原子需求表
        df_test_cases: 测试用例表
        enable_llm: 是否启用 LLM 盲评
        llm: LLM 实例（如果为 None 且 enable_llm=True，会报错）
    """
    from .prompts import TEST_LOGIC_EVALUATION_PROMPT
    
    # 第一步：静态基线检查
    all_atomic_req_ids = set(df_atomic["atomic_req_id"].dropna().unique())
    
    req_method_coverage = {}
    for req_id in all_atomic_req_ids:
        req_method_coverage[req_id] = {"normal": False, "robustness": False}
    
    # 按需求分组，检查测试方法覆盖
    for _, row in df_test_cases.iterrows():
        req_id = row.get("trace_to_atomic_req")
        if pd.isna(req_id) or req_id not in req_method_coverage:
            continue
        
        methods = _parse_test_method(row.get("test_method", ""))
        if "normal" in methods:
            req_method_coverage[req_id]["normal"] = True
        if "robustness" in methods:
            req_method_coverage[req_id]["robustness"] = True
    
    # 统计覆盖情况
    reqs_with_normal = sum(1 for v in req_method_coverage.values() if v["normal"])
    reqs_with_robustness = sum(1 for v in req_method_coverage.values() if v["robustness"])
    reqs_with_both = sum(1 for v in req_method_coverage.values() if v["normal"] and v["robustness"])
    
    missing_robustness = sorted([
        req_id for req_id, coverage in req_method_coverage.items()
        if not coverage["robustness"]
    ])
    
    method_coverage_rate = reqs_with_both / len(all_atomic_req_ids) if len(all_atomic_req_ids) > 0 else 0.0
    
    # 第二步：LLM 盲评（可选）
    llm_scores = []
    if enable_llm:
        if llm is None:
            print("⚠️ 警告：enable_llm=True 但未提供 llm 实例，将使用模拟评分")
        
        print(f"🤖 开始 LLM 盲评 ({len(df_test_cases)} 个测试用例)...")
        
        for idx, row in df_test_cases.iterrows():
            tc_id = row.get("tc_id", "UNKNOWN")
            test_method = row.get("test_method", "")
            objective = row.get("objective", "")
            preconditions = row.get("preconditions", "")
            inputs = row.get("inputs", "")
            steps = row.get("steps", "")
            expected = row.get("expected_results", "")
            
            # 构建评估 prompt
            prompt = TEST_LOGIC_EVALUATION_PROMPT.format(
                tc_id=tc_id,
                test_method=test_method,
                objective=objective,
                preconditions=preconditions if preconditions else "无",
                inputs=inputs if inputs else "无",
                steps=steps if steps else "无",
                expected_results=expected if expected else "无"
            )
            
            # 调用 LLM 评分
            result = call_llm_judge(prompt, llm=llm)
            llm_scores.append({
                "tc_id": tc_id,
                "score": result["score"],
                "reasoning": result["reasoning"],
                "issues": result.get("issues", [])
            })
            
            print(f"  ✓ {tc_id}: {result['score']}/5 - {result['reasoning'][:50]}...")
    
    avg_llm_score = np.mean([s["score"] for s in llm_scores]) if llm_scores else 0.0
    
    return LogicEvaluation(
        total_requirements=len(all_atomic_req_ids),
        requirements_with_normal_test=reqs_with_normal,
        requirements_with_robustness_test=reqs_with_robustness,
        requirements_with_both=reqs_with_both,
        method_coverage_rate=method_coverage_rate,
        requirements_missing_robustness=missing_robustness,
        llm_scores=llm_scores,
        average_llm_score=avg_llm_score,
    )


def evaluate_traceability(
    df_atomic: pd.DataFrame,
    df_test_cases: pd.DataFrame,
    df_traceability: pd.DataFrame
) -> TraceabilityEvaluation:
    """
    评估维度4：追溯链路与证据完整性
    
    检查追溯矩阵中的引用 ID 是否合法，以及证据引用的完整性
    """
    # 构建合法 ID 集合
    valid_atomic_req_ids = set(df_atomic["atomic_req_id"].dropna().unique())
    valid_tc_ids = set(df_test_cases["tc_id"].dropna().unique())
    
    # 检查追溯矩阵中的链路有效性
    broken_links = []
    total_links = len(df_traceability)
    
    for idx, row in df_traceability.iterrows():
        atomic_req_id = row.get("atomic_req_id")
        tc_id = row.get("tc_id")
        
        issues = []
        
        # 检查原子需求 ID 是否存在
        if not pd.isna(atomic_req_id) and atomic_req_id not in valid_atomic_req_ids:
            issues.append(f"原子需求ID不存在: {atomic_req_id}")
        
        # 检查测试用例 ID 是否存在
        if not pd.isna(tc_id) and tc_id not in valid_tc_ids:
            issues.append(f"测试用例ID不存在: {tc_id}")
        
        if issues:
            broken_links.append({
                "row_index": int(idx),
                "atomic_req_id": atomic_req_id,
                "tc_id": tc_id,
                "issues": issues,
            })
    
    valid_links = total_links - len(broken_links)
    link_validity_rate = valid_links / total_links if total_links > 0 else 0.0
    
    # 统计证据引用率
    total_test_cases = len(df_test_cases)
    test_cases_with_evidence = 0
    
    for _, row in df_test_cases.iterrows():
        evidence_refs = row.get("evidence_refs", "")
        if not _is_empty_value(evidence_refs):
            # 检查是否有实际内容（不只是空白或换行）
            if isinstance(evidence_refs, str) and evidence_refs.strip():
                test_cases_with_evidence += 1
    
    evidence_rate = test_cases_with_evidence / total_test_cases if total_test_cases > 0 else 0.0
    
    return TraceabilityEvaluation(
        total_traceability_links=total_links,
        valid_links=valid_links,
        broken_links=len(broken_links),
        link_validity_rate=link_validity_rate,
        broken_link_details=broken_links,
        total_test_cases=total_test_cases,
        test_cases_with_evidence=test_cases_with_evidence,
        evidence_rate=evidence_rate,
    )


def evaluate_excel(
    excel_bytes: bytes,
    enable_llm: bool = False,
    llm=None
) -> EvaluationResult:
    """
    对生成的 Excel 文件进行完整的四维度评估
    
    Args:
        excel_bytes: Excel 文件的字节内容
        enable_llm: 是否启用 LLM 盲评（评估维度3的第二步）
        llm: LLM 实例（如果 enable_llm=True 但 llm=None，会使用模拟评分）
    
    Returns:
        EvaluationResult: 包含四个维度的完整评估结果
    """
    # 读取 Excel 文件
    excel_file = BytesIO(excel_bytes)
    
    try:
        df_atomic = pd.read_excel(excel_file, sheet_name="AtomicRequirements")
        df_test_cases = pd.read_excel(excel_file, sheet_name="TestCases")
        df_traceability = pd.read_excel(excel_file, sheet_name="TraceabilityMatrix")
    except Exception as e:
        raise ValueError(f"无法读取 Excel 文件: {e}")
    
    # 执行四个维度的评估
    coverage = evaluate_coverage(df_atomic, df_test_cases)
    structure = evaluate_structure(df_test_cases)
    logic = evaluate_logic(df_atomic, df_test_cases, enable_llm=enable_llm, llm=llm)
    traceability = evaluate_traceability(df_atomic, df_test_cases, df_traceability)
    
    return EvaluationResult(
        coverage=coverage,
        structure=structure,
        logic=logic,
        traceability=traceability,
    )


def evaluate_from_file(
    excel_path: str,
    enable_llm: bool = False,
    llm=None
) -> EvaluationResult:
    """
    从文件路径读取 Excel 并进行评估
    
    Args:
        excel_path: Excel 文件路径
        enable_llm: 是否启用 LLM 盲评
        llm: LLM 实例
    
    Returns:
        EvaluationResult: 完整评估结果
    """
    with open(excel_path, "rb") as f:
        excel_bytes = f.read()
    
    return evaluate_excel(excel_bytes, enable_llm=enable_llm, llm=llm)
