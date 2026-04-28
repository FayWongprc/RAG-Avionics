"""
评估与验证模块

提供四个核心评估维度：
1. 需求覆盖完整度评估
2. 用例结构规范性评估
3. 测试方法与逻辑合理性评估
4. 追溯链路与证据完整性评估
"""

from .evaluator import (
    evaluate_excel,
    EvaluationResult,
    CoverageEvaluation,
    StructureEvaluation,
    LogicEvaluation,
    TraceabilityEvaluation,
)

__all__ = [
    "evaluate_excel",
    "EvaluationResult",
    "CoverageEvaluation",
    "StructureEvaluation",
    "LogicEvaluation",
    "TraceabilityEvaluation",
]
