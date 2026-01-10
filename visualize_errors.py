#!/usr/bin/env python3
"""
错误可视化分析脚本
"""

import json
from collections import Counter

# 错误分类
errors = [
    {"id": 1, "sample": 1, "turn": 4, "type": "GT标注问题", "severity": "low", "description": "GT期望Agent假装没看到已上传的图片"},
    {"id": 2, "sample": 1, "turn": 6, "type": "Agent过度主动", "severity": "medium", "description": "用户问清晰度，Agent调用了SceneClassification"},
    {"id": 3, "sample": 2, "turn": 2, "type": "Agent过度主动", "severity": "medium", "description": "用户打招呼，Agent立即分析"},
    {"id": 4, "sample": 2, "turn": 4, "type": "执行策略问题", "severity": "medium", "description": "重复调用SceneClassification"},
    {"id": 5, "sample": 2, "turn": 6, "type": "额外工具调用", "severity": "low", "description": "ChangeDetection正确，但额外调用SceneClassification", "core_correct": True},
    {"id": 6, "sample": 3, "turn": 2, "type": "Agent过度主动", "severity": "low", "description": "看到两张图自动做变化检测"},
    {"id": 7, "sample": 5, "turn": 2, "type": "Agent过度主动", "severity": "medium", "description": "用户说看不懂，Agent立即分析"},
    {"id": 8, "sample": 5, "turn": 6, "type": "额外工具调用", "severity": "low", "description": "ObjectCounting正确，但额外调用其他工具", "core_correct": True},
    {"id": 9, "sample": 5, "turn": 8, "type": "任务理解歧义", "severity": "medium", "description": "图里有什么 - ImageCaptioning vs ObjectDetection"},
]

def print_section(title, char="="):
    print(f"\n{char * 80}")
    print(f"{title:^80}")
    print(f"{char * 80}\n")

def analyze_errors():
    print_section("错误分析统计报告", "=")
    
    # 按类型统计
    type_counter = Counter([e["type"] for e in errors])
    print("📊 错误类型分布:")
    print("-" * 80)
    for error_type, count in type_counter.most_common():
        percentage = (count / len(errors)) * 100
        bar = "█" * int(percentage / 5)
        print(f"{error_type:20s} | {count:2d} ({percentage:5.1f}%) | {bar}")
    
    # 按严重程度统计
    print_section("严重程度分布", "-")
    severity_counter = Counter([e["severity"] for e in errors])
    severity_order = {"high": 3, "medium": 2, "low": 1}
    for severity in sorted(severity_counter.keys(), key=lambda x: severity_order.get(x, 0), reverse=True):
        count = severity_counter[severity]
        percentage = (count / len(errors)) * 100
        emoji = "🔴" if severity == "high" else "🟡" if severity == "medium" else "🟢"
        print(f"{emoji} {severity.upper():8s} | {count:2d} ({percentage:5.1f}%)")
    
    # 核心任务正确的错误
    print_section("核心任务正确但有额外调用", "-")
    core_correct = [e for e in errors if e.get("core_correct", False)]
    print(f"✅ 核心任务正确数量: {len(core_correct)}/{len(errors)}")
    print(f"   如果只看核心任务，准确率可提升: {len(core_correct)/len(errors)*100:.1f}%")
    print("\n详情:")
    for e in core_correct:
        print(f"  - 错误#{e['id']}: 样本{e['sample']} Turn{e['turn']} - {e['description']}")
    
    # 按样本统计
    print_section("各样本错误分布", "-")
    sample_errors = {}
    for e in errors:
        sample = e["sample"]
        if sample not in sample_errors:
            sample_errors[sample] = []
        sample_errors[sample].append(e)
    
    for sample in sorted(sample_errors.keys()):
        errors_list = sample_errors[sample]
        print(f"\n样本 {sample}: {len(errors_list)} 个错误")
        for e in errors_list:
            severity_emoji = "🔴" if e["severity"] == "high" else "🟡" if e["severity"] == "medium" else "🟢"
            core_mark = " ✅核心正确" if e.get("core_correct") else ""
            print(f"  {severity_emoji} Turn {e['turn']}: [{e['type']}] {e['description']}{core_mark}")
    
    # 改进建议优先级
    print_section("改进建议优先级", "=")
    
    print("🎯 优先级1 - 高优先级 (解决44.4%的错误)")
    print("-" * 80)
    print("问题: Agent过度主动 - 在用户打招呼或确认时就立即调用工具")
    print("影响: 4个错误 (#2, #3, #6, #7)")
    print("解决方案:")
    print("  1. 优化Prompt，明确区分'打招呼'和'任务请求'")
    print("  2. 添加'只在必要时使用工具'的指导")
    print("  3. 当用户说'能帮我看看'时，先确认具体需求")
    print()
    
    print("🎯 优先级2 - 中优先级 (解决22.2%的错误)")
    print("-" * 80)
    print("问题: 额外工具调用 - 核心任务正确但调用了多余工具")
    print("影响: 2个错误 (#5, #8)")
    print("解决方案:")
    print("  1. 添加'避免冗余调用'的Prompt")
    print("  2. 在调用工具前检查是否已有足够信息")
    print("  3. 使用更强的推理模型(GPT-4)")
    print()
    
    print("🎯 优先级3 - 低优先级 (改进GT标注)")
    print("-" * 80)
    print("问题: GT标注策略问题")
    print("影响: 1个错误 (#1)")
    print("解决方案:")
    print("  1. 采用'宽松匹配'策略")
    print("  2. 只要核心任务正确即可")
    print("  3. 允许Agent合理的主动性")
    print()
    
    # 预期改进效果
    print_section("预期改进效果", "=")
    
    current_accuracy = 35.71
    
    print(f"当前准确率: {current_accuracy:.2f}%")
    print()
    
    # 如果解决过度主动问题
    if_fix_overactive = (5 + 4) / 14 * 100  # 5个正确 + 4个过度主动
    print(f"✅ 如果解决'过度主动'问题: {if_fix_overactive:.2f}%")
    
    # 如果采用宽松匹配
    if_lenient = (5 + 4 + 2) / 14 * 100  # 5个正确 + 4个过度主动 + 2个核心正确
    print(f"✅ 如果采用'宽松匹配'(核心任务正确): {if_lenient:.2f}%")
    
    # 理想情况
    ideal = (5 + 4 + 2 + 1) / 14 * 100  # 再加上GT标注问题
    print(f"✅ 理想情况(所有改进): {ideal:.2f}%")
    
    print()
    print("=" * 80)
    print("结论: 通过Prompt优化，准确率有望从35.71%提升到64.29%以上")
    print("=" * 80)

if __name__ == "__main__":
    analyze_errors()

