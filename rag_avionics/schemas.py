from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class AtomicRequirement(BaseModel):
    """原子需求（尽量一条需求一个可验证的断言/约束）。"""

    req_id: str = Field(description="原子需求ID，例如 AR-001")
    source_req: Optional[str] = Field(default=None, description="来源需求编号（若有）")
    source_text: Optional[str] = Field(
        default=None,
        description="从原始需求中截取的来源句/条款（用于解释与追溯）",
    )
    statement: str = Field(description="原子需求陈述（可测试、无歧义）")
    category: Optional[str] = Field(
        default=None, description="类别，例如 功能/性能/时序/安全/接口/告警"
    )


class IEEE829TestCase(BaseModel):
    """简化版 IEEE 829 用例结构（毕设展示友好）。"""

    tc_id: str = Field(description="测试用例ID，例如 TC-REQ-LG-001-01")
    title: str = Field(description="用例标题")
    objective: str = Field(description="测试目的")
    preconditions: list[str] = Field(default_factory=list, description="前置条件")
    inputs: list[str] = Field(default_factory=list, description="输入/刺激")
    steps: list[str] = Field(default_factory=list, description="测试步骤")
    expected_results: list[str] = Field(default_factory=list, description="期望结果")
    postconditions: list[str] = Field(default_factory=list, description="后置条件")
    trace_to_atomic_req: str = Field(description="追溯到的原子需求ID")
    trace_to_source_req: Optional[str] = Field(
        default=None, description="追溯到的原始需求编号（必须）"
    )
    evidence_refs: list[str] = Field(
        default_factory=list,
        description="引用的证据来源标识（例如文件名/页码/章节）",
    )


class DecomposeOutput(BaseModel):
    atomic_requirements: list[AtomicRequirement]


class GenerateOutput(BaseModel):
    test_cases: list[IEEE829TestCase]

