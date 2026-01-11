#!/usr/bin/env python3
"""
工具调用错误可视化分析（仅评估有工具调用的轮次）
"""

import json
from collections import Counter

# 10个评估轮次的详细信息
evaluations = [
    # 正确的3个
    {"id": 1, "sample": 3, "turn": 4, "result": "correct", "actual": ["ImageCaptioning"], "gt": ["ImageCaptioning", "ImageCaptioning"], "task": "描述两张图"},
    {"id": 2, "sample": 4, "turn": 4, "result": "correct", "actual": ["ImageCaptioning"], "gt": ["ImageCaptioning"], "task": "描述图片"},
    {"id": 3, "sample": 5, "turn": 4, "result": "correct", "actual": ["EdgeDetection"], "gt": ["EdgeDetection"], "task": "边缘检测"},
    
    # 错误的7个
    {"id": 4, "sample": 1, "turn": 4, "result": "error", "type": "Agent过度主动", "actual": ["SceneClassification"], "gt": [], "description": "GT期望不调用工具", "core_correct": False},
    {"id": 5, "sample": 1, "turn": 6, "result": "error", "type": "Agent过度主动", "actual": ["SceneClassification"], "gt": [], "description": "用户问清晰度，不需要场景分类", "core_correct": False},
    {"id": 6, "sample": 2, "turn": 4, "result": "error", "type": "时机判断错误", "actual": ["ChangeDetection"], "gt": [], "description": "只有一张图就调用变化检测", "core_correct": False},
    {"id": 7, "sample": 2, "turn": 6, "result": "error", "type": "额外工具调用", "actual": ["ImageCaptioning", "ChangeDetection"], "gt": ["ChangeDetection"], "description": "ChangeDetection正确，但额外调用ImageCaptioning", "core_correct": True},
    {"id": 8, "sample": 3, "turn": 2, "result": "error", "type": "Agent过度主动", "actual": ["ChangeDetection"], "gt": [], "description": "看到两张图自动做变化检测", "core_correct": False},
    {"id": 9, "sample": 5, "turn": 6, "result": "error", "type": "额外工具调用", "actual": ["ObjectCounting", "ObjectDetection", "ImageCaptioning"], "gt": ["ObjectCounting"], "description": "ObjectCounting正确，但额外调用其他工具", "core_correct": True},
    {"id": 10, "sample": 5, "turn": 8, "result": "error", "type": "任务理解歧义", "actual": ["ImageCaptioning"], "gt": ["ObjectDetection"], "description": "图里有什么 - ImageCaptioning vs ObjectDetection", "core_correct": False},
]

def print_section(title, char="="):
    print(f"\n{char * 80}")
    print(f"{title:^80}")
    print(f"{char * 80}\n")

def analyze():
    print_section("工具调用测试分析（仅评估有工具调用的轮次）", "=")
    
    correct = [e for e in evaluations if e["result"] == "correct"]
    errors = [e for e in evaluations if e["result"] == "error"]
    
    print(f"📊 总体统计:")
    print(f"  评估轮次: {len(evaluations)}")
    print(f"  ✅ 正确: {len(correct)} ({len(correct)/len(evaluations)*100:.1f}%)")
    print(f"  ❌ 错误: {len(errors)} ({len(errors)/len(evaluations)*100:.1f}%)")
    print(f"  准确率: {len(correct)/len(evaluations)*100:.2f}%")
    
    # 错误类型统计
    print_section("错误类型分布", "-")
    error_types = Counter([e["type"] for e in errors])
    for error_type, count in error_types.most_common():
        percentage = (count / len(errors)) * 100
        bar = "█" * int(percentage / 5)
        print(f"{error_type:20s} | {count:2d} ({percentage:5.1f}%) | {bar}")
    
    # 核心任务正确的错误
    print_section("核心任务正确但有额外调用", "-")
    core_correct = [e for e in errors if e.get("core_correct", False)]
    print(f"✅ 核心任务正确数量: {len(core_correct)}/{len(errors)}")
    print(f"   核心任务准确率: {(len(correct) + len(core_correct))/len(evaluations)*100:.1f}%")
    print("\n详情:")
    for e in core_correct:
        print(f"  - 样本{e['sample']} Turn{e['turn']}: {e['description']}")
    
    # 各样本表现
    print_section("各样本表现", "-")
    sample_stats = {}
    for e in evaluations:
        sample = e["sample"]
        if sample not in sample_stats:
            sample_stats[sample] = {"correct": 0, "error": 0, "total": 0}
        sample_stats[sample]["total"] += 1
        if e["result"] == "correct":
            sample_stats[sample]["correct"] += 1
        else:
            sample_stats[sample]["error"] += 1
    
    for sample in sorted(sample_stats.keys()):
        stats = sample_stats[sample]
        accuracy = stats["correct"] / stats["total"] * 100 if stats["total"] > 0 else 0
        emoji = "✅" if accuracy == 100 else "⚠️" if accuracy >= 50 else "❌"
        print(f"{emoji} 样本{sample}: {stats['correct']}/{stats['total']} ({accuracy:.0f}%)")
    
    # 改进建议
    print_section("改进建议优先级", "=")
    
    print("🎯 优先级1 - 减少过度主动 (影响42.9%错误)")
    print("-" * 80)
    overactive = [e for e in errors if e.get("type") == "Agent过度主动"]
    print(f"影响: {len(overactive)} 个错误")
    print("建议:")
    print("  1. 在Prompt中明确'只在必要时使用工具'")
    print("  2. 区分'打招呼/确认'和'任务请求'")
    print("  3. 看到两张图不要自动做变化检测，先询问意图")
    print()
    
    print("🎯 优先级2 - 避免额外工具调用 (影响28.6%错误)")
    print("-" * 80)
    extra = [e for e in errors if e.get("type") == "额外工具调用"]
    print(f"影响: {len(extra)} 个错误（但核心任务都正确！）")
    print("建议:")
    print("  1. 添加'只使用必要的工具'的Prompt")
    print("  2. 完成核心任务后不要调用额外工具")
    print("  3. 使用更强的推理模型(GPT-4)")
    print()
    
    print("🎯 优先级3 - 改进时机判断 (影响14.3%错误)")
    print("-" * 80)
    timing = [e for e in errors if e.get("type") == "时机判断错误"]
    print(f"影响: {len(timing)} 个错误")
    print("建议:")
    print("  1. 变化检测前检查是否有两张图")
    print("  2. 只有一张图时，先要求用户提供第二张")
    print()
    
    # 预期改进效果
    print_section("预期改进效果", "=")
    
    current = len(correct) / len(evaluations) * 100
    
    print(f"当前准确率（严格匹配）: {current:.2f}%")
    print(f"当前准确率（核心任务）: {(len(correct) + len(core_correct))/len(evaluations)*100:.2f}%")
    print()
    
    # 如果解决过度主动
    if_fix_overactive = (len(correct) + len(overactive)) / len(evaluations) * 100
    print(f"✅ 如果解决'过度主动': {if_fix_overactive:.2f}%")
    
    # 如果避免额外调用
    if_fix_extra = (len(correct) + len(overactive) + len(extra)) / len(evaluations) * 100
    print(f"✅ 如果避免'额外调用': {if_fix_extra:.2f}%")
    
    # 如果解决所有问题
    ideal = (len(correct) + len(errors) - len([e for e in errors if e.get("type") == "任务理解歧义"])) / len(evaluations) * 100
    print(f"✅ 理想情况（除歧义外）: {ideal:.2f}%")
    
    print()
    print("=" * 80)
    print("🎉 重大进步: 变化检测任务成功！多轮上下文理解有效！")
    print("=" * 80)
    
    # 详细错误列表
    print_section("详细错误列表", "=")
    for e in errors:
        emoji = "⚠️" if e.get("core_correct") else "❌"
        core_mark = " [核心正确]" if e.get("core_correct") else ""
        print(f"\n{emoji} 错误#{e['id']-3}: 样本{e['sample']}-Turn{e['turn']}{core_mark}")
        print(f"   类型: {e['type']}")
        print(f"   实际: {e['actual']}")
        print(f"   GT: {e['gt'] if e['gt'] else '无'}")
        print(f"   说明: {e['description']}")

if __name__ == "__main__":
    analyze()

