"""
评估功能使用示例

演示如何对生成的 Excel 文件进行评估
"""

import json
from pathlib import Path
from .evaluator import evaluate_from_file


def main():
    """运行评估示例"""
    
    # 假设 Excel 文件路径
    excel_path = "output/traceability_report.xlsx"
    
    if not Path(excel_path).exists():
        print(f"❌ 文件不存在: {excel_path}")
        print("请先运行 RAG pipeline 生成 Excel 文件")
        return
    
    print("=" * 80)
    print("开始评估 Excel 文件...")
    print("=" * 80)
    
    # 执行评估（不启用 LLM 盲评以加快速度）
    result = evaluate_from_file(excel_path, enable_llm=False)
    
    # 打印评估结果
    print("\n" + "=" * 80)
    print("📊 评估维度1：需求覆盖完整度")
    print("=" * 80)
    cov = result.coverage
    print(f"总需求数: {cov.total_requirements}")
    print(f"已覆盖需求数: {cov.covered_requirements}")
    print(f"覆盖率: {cov.coverage_rate * 100:.2f}%")
    if cov.uncovered_requirements:
        print(f"\n⚠️  未覆盖的需求 ({len(cov.uncovered_requirements)} 个):")
        for req_id in cov.uncovered_requirements[:10]:  # 只显示前10个
            print(f"  - {req_id}")
        if len(cov.uncovered_requirements) > 10:
            print(f"  ... 还有 {len(cov.uncovered_requirements) - 10} 个")
    else:
        print("✅ 所有需求都已被测试用例覆盖")
    
    print("\n" + "=" * 80)
    print("📋 评估维度2：用例结构规范性")
    print("=" * 80)
    struct = result.structure
    print(f"总测试用例数: {struct.total_test_cases}")
    print(f"结构完整的用例数: {struct.valid_test_cases}")
    print(f"结构合格率: {struct.structure_compliance_rate * 100:.2f}%")
    if struct.invalid_test_cases:
        print(f"\n⚠️  结构不完整的用例 ({len(struct.invalid_test_cases)} 个):")
        for case in struct.invalid_test_cases[:5]:  # 只显示前5个
            print(f"  - {case['tc_id']}: 缺失字段 {case['missing_fields']}")
        if len(struct.invalid_test_cases) > 5:
            print(f"  ... 还有 {len(struct.invalid_test_cases) - 5} 个")
    else:
        print("✅ 所有测试用例结构完整")
    
    print("\n" + "=" * 80)
    print("🧪 评估维度3：测试方法与逻辑合理性")
    print("=" * 80)
    logic = result.logic
    print(f"总需求数: {logic.total_requirements}")
    print(f"包含正常测试的需求数: {logic.requirements_with_normal_test}")
    print(f"包含健壮性测试的需求数: {logic.requirements_with_robustness_test}")
    print(f"同时包含两者的需求数: {logic.requirements_with_both}")
    print(f"方法覆盖率: {logic.method_coverage_rate * 100:.2f}%")
    if logic.requirements_missing_robustness:
        print(f"\n⚠️  缺少健壮性测试的需求 ({len(logic.requirements_missing_robustness)} 个):")
        for req_id in logic.requirements_missing_robustness[:10]:
            print(f"  - {req_id}")
        if len(logic.requirements_missing_robustness) > 10:
            print(f"  ... 还有 {len(logic.requirements_missing_robustness) - 10} 个")
    else:
        print("✅ 所有需求都包含健壮性测试")
    
    if logic.llm_scores:
        print(f"\n🤖 LLM 盲评平均分: {logic.average_llm_score:.2f} / 5.0")
    
    print("\n" + "=" * 80)
    print("🔗 评估维度4：追溯链路与证据完整性")
    print("=" * 80)
    trace = result.traceability
    print(f"总追溯链路数: {trace.total_traceability_links}")
    print(f"有效链路数: {trace.valid_links}")
    print(f"断链数: {trace.broken_links}")
    print(f"链路有效率: {trace.link_validity_rate * 100:.2f}%")
    if trace.broken_link_details:
        print(f"\n⚠️  断链详情 ({len(trace.broken_link_details)} 个):")
        for link in trace.broken_link_details[:5]:
            print(f"  - 行 {link['row_index']}: {', '.join(link['issues'])}")
        if len(trace.broken_link_details) > 5:
            print(f"  ... 还有 {len(trace.broken_link_details) - 5} 个")
    else:
        print("✅ 所有追溯链路有效")
    
    print(f"\n📄 证据引用统计:")
    print(f"总测试用例数: {trace.total_test_cases}")
    print(f"包含证据引用的用例数: {trace.test_cases_with_evidence}")
    print(f"证据引用率: {trace.evidence_rate * 100:.2f}%")
    
    # 导出 JSON 格式的评估结果
    output_json = "output/evaluation_result.json"
    Path(output_json).parent.mkdir(parents=True, exist_ok=True)
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 80)
    print(f"✅ 评估完成！结果已保存到: {output_json}")
    print("=" * 80)


if __name__ == "__main__":
    main()
