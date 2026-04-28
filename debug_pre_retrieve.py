"""诊断预检索（Pre-retrieve）功能 - 测试完整流程"""
import sys
import time
import json
from dataclasses import replace
from pathlib import Path
from rag_avionics.settings import load_settings
from rag_avionics.llm import make_llm
from rag_avionics.prompts import DOMAIN_QUERY_PROMPT
from langchain_core.messages import HumanMessage


def load_avionics_terms_dict(dict_path: str = "data/avionics_terms.json") -> dict:
    """加载航空术语词典（与 pipeline.py 中的函数相同）"""
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


def _safe_json_loads(text: str):
    """容错 JSON 解析（与 pipeline.py 中的函数相同）"""
    import orjson
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
    # 兜底：尝试修复被截断的 JSON
    try:
        patched = text.rstrip().rstrip(",")
        open_braces = patched.count("{") - patched.count("}")
        open_brackets = patched.count("[") - patched.count("]")
        patched += "]" * max(open_brackets, 0)
        patched += "}" * max(open_braces, 0)
        return json.loads(patched)
    except Exception as e:
        raise ValueError(f"无法解析 LLM 输出的 JSON: {e}\n原文前500字符: {text[:500]}")


def test_pre_retrieve(provider: str, model: str, requirement_text: str):
    """测试预检索完整流程"""
    print(f"\n{'='*70}")
    print(f"测试预检索功能 - {provider} / {model}")
    print('='*70)
    
    try:
        # 1. 加载配置
        print("\n[步骤 1/5] 加载配置...")
        paths, ms = load_settings()
        
        if provider == "deepseek":
            ms = replace(ms, llm_provider="deepseek", deepseek_model=model)
        elif provider == "zhipu":
            ms = replace(ms, llm_provider="zhipu", zhipu_model=model)
        else:  # qwen
            ms = replace(ms, llm_provider="qwen", qwen_model=model)
        
        print(f"✓ 配置加载成功")
        print(f"  提供商: {ms.llm_provider}")
        print(f"  模型: {model}")
        
        # 2. 创建 LLM
        print("\n[步骤 2/5] 创建 LLM 实例...")
        llm = make_llm(ms, temperature=0.2)
        print(f"✓ LLM 实例创建成功")
        
        # 3. 调用 LLM 提取术语
        print("\n[步骤 3/5] 调用 LLM 提取术语...")
        print(f"需求文本: {requirement_text[:100]}...")
        
        prompt = DOMAIN_QUERY_PROMPT.format(requirement_text=requirement_text)
        print(f"提示词长度: {len(prompt)} 字符")
        
        start_time = time.time()
        resp = llm.invoke([HumanMessage(content=prompt)])
        elapsed_llm = time.time() - start_time
        
        raw_output = getattr(resp, "content", str(resp)).strip()
        
        print(f"✓ LLM 调用成功 (耗时: {elapsed_llm:.2f}秒)")
        print(f"原始输出: {raw_output[:200]}...")
        
        # 4. 解析 JSON
        print("\n[步骤 4/5] 解析 JSON 输出...")
        try:
            extracted_terms = _safe_json_loads(raw_output)
            if not isinstance(extracted_terms, list):
                print(f"✗ LLM 输出不是数组格式")
                print(f"  类型: {type(extracted_terms)}")
                print(f"  内容: {extracted_terms}")
                return False, elapsed_llm
            
            if not extracted_terms:
                print("⚠️ LLM 返回空数组，未提取到任何术语")
                return True, elapsed_llm  # 空数组也算成功
            
            print(f"✓ JSON 解析成功")
            print(f"  提取到的术语: {extracted_terms}")
            
        except Exception as e:
            print(f"✗ JSON 解析失败: {e}")
            print(f"  原始输出: {raw_output[:300]}")
            return False, elapsed_llm
        
        # 5. 加载术语词典并匹配
        print("\n[步骤 5/5] 加载术语词典并匹配...")
        start_time = time.time()
        
        terms_dict = load_avionics_terms_dict()
        if not terms_dict:
            print("⚠️ 术语词典为空，跳过匹配")
            return True, elapsed_llm
        
        print(f"✓ 术语词典加载成功")
        print(f"  词典大小: {len(terms_dict)} 条")
        
        # 精确哈希匹配
        domain_context = []
        for term in extracted_terms:
            if not isinstance(term, str):
                continue
            
            # 尝试多种匹配策略
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
                        "score": 1.0,
                        "metadata": {"source": "avionics_terms.json"}
                    })
                    print(f"  ✓ 命中词典: {term} -> {variant}")
                    matched = True
                    break
            
            if not matched:
                print(f"  ✗ 词典未收录: {term}")
        
        elapsed_match = time.time() - start_time
        
        if not domain_context:
            print("\n⚠️ 未匹配到任何术语定义")
        else:
            print(f"\n✓ 成功匹配 {len(domain_context)} 个术语")
            print("\n匹配结果:")
            for i, ctx in enumerate(domain_context, 1):
                print(f"  [{i}] {ctx['matched_term']}")
                print(f"      {ctx['text'][:80]}...")
        
        total_time = elapsed_llm + elapsed_match
        print(f"\n总耗时: {total_time:.2f}秒 (LLM: {elapsed_llm:.2f}秒, 匹配: {elapsed_match:.2f}秒)")
        
        return True, total_time
        
    except Exception as e:
        print(f"\n✗ 测试失败")
        print(f"错误类型: {type(e).__name__}")
        print(f"错误信息: {str(e)}")
        
        import traceback
        print(f"\n完整错误堆栈:")
        traceback.print_exc()
        
        return False, 0


def run_tests():
    """运行所有测试"""
    print("\n" + "="*70)
    print("预检索功能诊断工具")
    print("="*70)
    
    # 测试需求文本
    test_requirements = [
        {
            "name": "起落架控制需求（包含多个术语）",
            "text": """
需求编号：REQ-LG-001
功能描述：起落架控制逻辑。
具体规约：当且仅当起落架控制手柄（Gear Handle）处于"DOWN"位置，且飞行速度（Airspeed）低于 250 节时，
FSECU 系统应通过 ARINC 429 总线在 3 秒内发送放下（Deploy）指令。
若速度超过 250 节，即使手柄在"DOWN"位，也不允许执行放下动作，并需触发 WOW（Weight on Wheels）告警。
            """.strip()
        },
        {
            "name": "简单需求（少量术语）",
            "text": "FSECU 硬件应支持 ARINC 429 通信协议。"
        },
        {
            "name": "无专业术语需求",
            "text": "系统应在正常工作条件下保持稳定运行。"
        }
    ]
    
    # 选择测试需求
    print("\n选择测试需求:")
    for i, req in enumerate(test_requirements, 1):
        print(f"{i}. {req['name']}")
    
    choice = input("\n请输入 (1-3): ").strip()
    try:
        req_index = int(choice) - 1
        if req_index < 0 or req_index >= len(test_requirements):
            raise ValueError()
        requirement_text = test_requirements[req_index]["text"]
    except:
        print("无效选择，使用默认需求")
        requirement_text = test_requirements[0]["text"]
    
    print(f"\n使用需求: {test_requirements[req_index]['name']}")
    print(f"需求内容:\n{requirement_text}\n")
    
    # 测试所有模型
    print("\n" + "="*70)
    print("开始测试所有模型...")
    print("="*70)
    
    results = {}
    timings = {}
    
    models_to_test = [
        ("deepseek", "deepseek-reasoner"),
        ("deepseek", "deepseek-chat"),
        ("zhipu", "glm-5"),
        ("zhipu", "glm-4-plus"),
        ("zhipu", "glm-4-flash"),
        ("qwen", "qwen3-max"),
        ("qwen", "qwen3.5-plus"),
        ("qwen", "qwen3.5-flash"),
    ]
    
    for provider, model in models_to_test:
        success, elapsed = test_pre_retrieve(provider, model, requirement_text)
        key = f"{provider}/{model}"
        results[key] = success
        timings[key] = elapsed
    
    # 总结
    print("\n" + "="*70)
    print("测试总结")
    print("="*70)
    
    print("\n模型状态:")
    for key, success in results.items():
        status = "✓ 正常" if success else "✗ 失败"
        timing = f"{timings[key]:.2f}秒" if success else "N/A"
        print(f"  {key:30s}: {status:8s} (耗时: {timing})")
    
    # 性能排名
    if any(results.values()):
        print("\n性能排名（从快到慢）:")
        sorted_models = sorted(
            [(key, time) for key, time in timings.items() if results[key]],
            key=lambda x: x[1]
        )
        for i, (key, elapsed) in enumerate(sorted_models, 1):
            print(f"  {i}. {key:30s}: {elapsed:.2f} 秒")
    
    # 建议
    print("\n推荐:")
    if any(results.values()):
        fastest = min(
            [(key, time) for key, time in timings.items() if results[key]],
            key=lambda x: x[1]
        )
        print(f"  - 最快: {fastest[0]} ({fastest[1]:.2f}秒)")
    else:
        print("  ⚠️ 所有模型都失败，请检查配置和网络连接")


def quick_test():
    """快速测试单个模型"""
    print("\n快速测试模式")
    print("="*70)
    
    provider = input("选择提供商 (deepseek/zhipu/qwen): ").strip().lower()
    
    if provider == "deepseek":
        model = input("选择模型 (deepseek-v4-flash/deepseek-v4-pro): ").strip()
    elif provider == "zhipu":
        model = input("选择模型 (glm-5.1/glm-5/glm-4.7/glm-4.7-FlashX): ").strip()
    elif provider == "qwen":
        model = input("选择模型 (qwen3-max/qwen3.5-plus/qwen3.5-flash): ").strip()
    else:
        print("无效的提供商")
        return
    
    # 使用默认测试需求
    requirement_text = """
需求编号：REQ-LG-001
功能描述：起落架控制逻辑。
具体规约：当且仅当起落架控制手柄（Gear Handle）处于"DOWN"位置，且飞行速度（Airspeed）低于 250 节时，
FSECU 系统应通过 ARINC 429 总线在 3 秒内发送放下（Deploy）指令。
    """.strip()
    
    test_pre_retrieve(provider, model, requirement_text)


if __name__ == "__main__":
    print("\n" + "="*70)
    print("预检索功能诊断工具")
    print("="*70)
    print("\n选择测试模式:")
    print("1. 完整测试（测试所有模型 + 多个需求）")
    print("2. 快速测试（测试单个模型）")
    
    choice = input("\n请输入 (1/2): ").strip()
    
    if choice == "1":
        run_tests()
    elif choice == "2":
        quick_test()
    else:
        print("无效选择")
        sys.exit(1)
