"""
评估功能完整测试（包含 LLM 盲评）

演示如何使用真实的 LLM 进行评估维度3的盲评
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from io import BytesIO
import pandas as pd
from rag_avionics.evaluation import evaluate_excel
from rag_avionics.settings import load_settings
from rag_avionics.llm import make_llm


def create_test_excel() -> bytes:
    """创建测试用的 Excel 文件"""
    
    # 原子需求
    df_atomic = pd.DataFrame([
        {
            "source_req_id": "REQ-001",
            "atomic_req_id": "AR-001",
            "category": "功能",
            "atomic_statement": "系统应在收到启动命令后 100ms 内完成自检",
            "source_text": "系统启动要求",
        },
        {
            "source_req_id": "REQ-001",
            "atomic_req_id": "AR-002",
            "category": "性能",
            "atomic_statement": "输入信号范围为 0-100，超出范围应触发告警",
            "source_text": "输入范围要求",
        },
    ])
    
    # 测试用例（包含一些逻辑问题，用于测试 LLM 评分）
    df_test_cases = pd.DataFrame([
        {
            "tc_id": "TC-001",
            "title": "正常启动测试",
            "objective": "验证系统正常启动流程",
            "test_method": "正常范围测试",
            "design_rationale": "验证基本功能",
            "trace_to_source_req": "REQ-001",
            "trace_to_atomic_req": "AR-001",
            "preconditions": "系统处于关闭状态",
            "inputs": "发送启动命令",
            "steps": "1. 发送启动命令\n2. 等待自检完成\n3. 检查自检时间",
            "expected_results": "系统在 100ms 内完成自检并进入运行状态",
            "postconditions": "系统运行中",
            "evidence_refs": "DO-178C 6.3.1",
        },
        {
            "tc_id": "TC-002",
            "title": "启动超时测试",
            "objective": "验证启动超时处理",
            "test_method": "健壮性测试",
            "design_rationale": "验证异常处理",
            "trace_to_source_req": "REQ-001",
            "trace_to_atomic_req": "AR-001",
            "preconditions": "系统处于关闭状态",
            "inputs": "发送启动命令，模拟自检延迟 200ms",
            "steps": "1. 发送启动命令\n2. 模拟自检延迟\n3. 检查系统响应",
            "expected_results": "系统检测到超时，触发告警，进入安全状态",
            "postconditions": "系统处于错误状态",
            "evidence_refs": "DO-178C 6.3.2",
        },
        {
            "tc_id": "TC-003",
            "title": "正常输入测试",
            "objective": "验证正常输入处理",
            "test_method": "正常范围测试",
            "design_rationale": "验证正常工况",
            "trace_to_source_req": "REQ-001",
            "trace_to_atomic_req": "AR-002",
            "preconditions": "系统运行中",
            "inputs": "输入值 50（范围内）",
            "steps": "1. 输入值 50\n2. 检查系统响应",
            "expected_results": "系统正常处理输入，无告警",
            "postconditions": "系统继续运行",
            "evidence_refs": "DO-178C 6.4.1",
        },
        {
            "tc_id": "TC-004",
            "title": "超限输入测试（逻辑错误示例）",
            "objective": "验证超限输入处理",
            "test_method": "正常范围测试",  # ❌ 错误：应该是"健壮性测试"
            "design_rationale": "验证正常工况",  # ❌ 错误：应该是"验证异常处理"
            "trace_to_source_req": "REQ-001",
            "trace_to_atomic_req": "AR-002",
            "preconditions": "系统运行中",
            "inputs": "输入值 150（超出范围 0-100）",  # ✓ 输入是异常的
            "steps": "1. 输入值 150\n2. 检查系统响应",
            "expected_results": "系统触发告警，拒绝处理",  # ✓ 预期结果是异常处理
            "postconditions": "系统继续运行",
            "evidence_refs": "DO-178C 6.4.2",
        },
    ])
    
    # 追溯矩阵
    df_traceability = pd.DataFrame([
        {
            "source_req_id": "REQ-001",
            "atomic_req_id": "AR-001",
            "atomic_statement": "系统应在收到启动命令后 100ms 内完成自检",
            "tc_id": "TC-001",
            "tc_title": "正常启动测试",
            "evidence_refs": "DO-178C 6.3.1",
        },
        {
            "source_req_id": "REQ-001",
            "atomic_req_id": "AR-001",
            "atomic_statement": "系统应在收到启动命令后 100ms 内完成自检",
            "tc_id": "TC-002",
            "tc_title": "启动超时测试",
            "evidence_refs": "DO-178C 6.3.2",
        },
        {
            "source_req_id": "REQ-001",
            "atomic_req_id": "AR-002",
            "atomic_statement": "输入信号范围为 0-100，超出范围应触发告警",
            "tc_id": "TC-003",
            "tc_title": "正常输入测试",
            "evidence_refs": "DO-178C 6.4.1",
        },
        {
            "source_req_id": "REQ-001",
            "atomic_req_id": "AR-002",
            "atomic_statement": "输入信号范围为 0-100，超出范围应触发告警",
            "tc_id": "TC-004",
            "tc_title": "超限输入测试（逻辑错误示例）",
            "evidence_refs": "DO-178C 6.4.2",
        },
    ])
    
    # 生成 Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df_atomic.to_excel(writer, index=False, sheet_name="AtomicRequirements")
        df_test_cases.to_excel(writer, index=False, sheet_name="TestCases")
        df_traceability.to_excel(writer, index=False, sheet_name="TraceabilityMatrix")
    
    return output.getvalue()


def main():
    """运行完整测试"""
    print("=" * 80)
    print("评估功能完整测试（包含 LLM 盲评）")
    print("=" * 80)
    
    # 创建测试数据
    print("\n📝 创建测试 Excel 数据...")
    excel_bytes = create_test_excel()
    print(f"✅ 测试数据创建完成 ({len(excel_bytes)} 字节)")
    
    # 第一步：不启用 LLM 的快速评估
    print("\n" + "=" * 80)
    print("第一步：快速评估（不启用 LLM）")
    print("=" * 80)
    
    result_quick = evaluate_excel(excel_bytes, enable_llm=False)
    
    print(f"\n需求覆盖率: {result_quick.coverage.coverage_rate * 100:.2f}%")
    print(f"结构合格率: {result_quick.structure.structure_compliance_rate * 100:.2f}%")
    print(f"方法覆盖率: {result_quick.logic.method_coverage_rate * 100:.2f}%")
    print(f"链路有效率: {result_quick.traceability.link_validity_rate * 100:.2f}%")
    
    # 第二步：启用 LLM 的深度评估
    print("\n" + "=" * 80)
    print("第二步：深度评估（启用 LLM 盲评）")
    print("=" * 80)
    
    try:
        # 加载配置
        paths, ms = load_settings()
        
        # 创建 LLM 实例（使用较低的温度以获得稳定评分）
        print(f"\n🤖 创建 LLM 实例...")
        print(f"  提供商: {ms.llm_provider}")
        print(f"  模型: {ms.qwen_model if ms.llm_provider == 'qwen' else ms.deepseek_model if ms.llm_provider == 'deepseek' else ms.zhipu_model}")
        
        llm = make_llm(ms, temperature=0.1)
        
        # 执行评估
        print(f"\n📊 开始 LLM 盲评...")
        result_deep = evaluate_excel(excel_bytes, enable_llm=True, llm=llm)
        
        # 显示 LLM 评分结果
        print("\n" + "=" * 80)
        print("🤖 LLM 逻辑合理性评分结果")
        print("=" * 80)
        
        logic = result_deep.logic
        print(f"\n平均分: {logic.average_llm_score:.2f} / 5.0")
        print(f"\n详细评分:")
        
        for score_info in logic.llm_scores:
            print(f"\n{'=' * 60}")
            print(f"测试用例: {score_info['tc_id']}")
            print(f"评分: {score_info['score']}/5")
            print(f"理由: {score_info['reasoning']}")
            
            if score_info.get('issues'):
                print(f"具体问题:")
                for issue in score_info['issues']:
                    print(f"  - {issue}")
            else:
                print(f"✅ 无问题")
        
        print("\n" + "=" * 80)
        print("✅ 完整测试完成！")
        print("=" * 80)
        
        # 验证 TC-004 应该得到较低分数（因为它有逻辑错误）
        tc004_score = next((s for s in logic.llm_scores if s['tc_id'] == 'TC-004'), None)
        if tc004_score:
            print(f"\n🔍 验证结果:")
            print(f"TC-004（故意设计的逻辑错误用例）得分: {tc004_score['score']}/5")
            if tc004_score['score'] < 4:
                print("✅ LLM 成功识别出逻辑错误！")
            else:
                print("⚠️  LLM 未能识别出逻辑错误")
        
    except Exception as e:
        print(f"\n❌ LLM 评估失败: {e}")
        print("\n可能的原因:")
        print("1. 未配置 API 密钥（检查 .env 文件）")
        print("2. 网络连接问题")
        print("3. API 配额不足")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
