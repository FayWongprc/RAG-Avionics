DECOMPOSE_PROMPT = """
你是机载软件需求工程与测试工程专家。请把用户给出的“需求段落”拆分为若干条“原子需求”：
- 每条原子需求必须可测试、可验证、表达清晰
- 避免把两个条件/动作/告警混在一条
- 需要保留关键约束（阈值、单位、时序、触发条件、禁止条件、告警条件）

追溯要求（必须满足）：
- 每条原子需求必须填写 source_req（原始需求编号），若输入中能识别出需求编号则使用它，否则写 "UNKNOWN"
- 每条原子需求必须填写 source_text：从原始需求段落中截取的“直接来源句/条款”（尽量原文拷贝）

输出必须是严格 JSON（不要使用 markdown 代码块），格式如下：
{{
  "atomic_requirements": [
    {{
      "req_id": "AR-001",
      "source_req": "REQ-XXX-001",
      "source_text": "……原文片段……",
      "statement": "...",
      "category": "功能/性能/时序/安全/接口/告警"
    }}
  ]
}}

已识别的原始需求编号（可能为 UNKNOWN）：
{requirement_id}

需求段落：
{requirement_text}
""".strip()


GENERATE_TESTCASES_PROMPT = """
你是航空软件测试工程师。你将获得：
1) 一条“原子需求”（包含 source_req/source_text）
2) 从标准/规范文档检索到的“证据片段”（用于引用与支撑）

请基于 IEEE 829 风格生成测试用例，要求：
- 用例要能覆盖该原子需求的正向/反向/边界（若适用）
- 步骤可执行，期望结果可观察
- 必须给出 trace_to_atomic_req 与 trace_to_source_req（原始需求编号）
- 在 evidence_refs 里引用证据来源（可用文件名/页码/章节等），若证据为空则可为空列表

输出必须是严格 JSON（不要使用 markdown 代码块），格式如下：
{{
  "test_cases": [
    {{
      "tc_id": "TC-...",
      "title": "...",
      "objective": "...",
      "preconditions": ["..."],
      "inputs": ["..."],
      "steps": ["..."],
      "expected_results": ["..."],
      "postconditions": ["..."],
      "trace_to_atomic_req": "AR-001",
      "trace_to_source_req": "REQ-XXX-001",
      "evidence_refs": ["..."]
    }}
  ]
}}

原子需求：
{atomic_requirement_json}

原始需求段落（用于补足追溯语义，但不要发散）：
{requirement_text}

证据片段（可能为空）：
{evidence_text}
""".strip()

