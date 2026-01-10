#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多轮对话工具调用正确率评估脚本
"""

import json
from typing import List, Dict, Any
from collections import defaultdict


def load_data(file_path: str) -> List[Dict[str, Any]]:
    """加载多轮对话数据"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_predicted_tools(turn: Dict[str, Any]) -> List[str]:
    """从一轮对话中提取预测的工具列表"""
    if turn.get('tool_calls') is None:
        return []
    
    tools = []
    for tool_call in turn['tool_calls']:
        if 'tool' in tool_call:
            tools.append(tool_call['tool'])
    return tools


def evaluate_turn_accuracy(sample: Dict[str, Any]) -> Dict[str, Any]:
    """评估单个样本中每轮对话的工具调用准确率
    
    使用tool_calls字段作为ground truth：
    - 如果tool_calls为null，ground truth就是"不调用工具"（空集合）
    - 如果tool_calls有内容，提取其中的工具作为ground truth
    """
    sample_level_gt = set(sample.get('ground_truth_tools', []))
    
    # 收集所有预测的工具和ground truth工具
    all_predicted_tools = set()
    all_gt_tools = set()
    turn_results = []
    all_turns_correct = True
    
    for turn in sample['turns']:
        if turn['role'] == 'assistant':
            # 提取预测的工具（实际调用的工具）
            predicted_tools = extract_predicted_tools(turn)
            turn_tools_set = set(predicted_tools)
            all_predicted_tools.update(turn_tools_set)
            
            # Ground Truth就是tool_calls字段中的工具
            # 如果tool_calls为null或空列表，ground truth就是空集合（不调用工具）
            turn_gt = set()
            if turn.get('tool_calls') is not None and turn.get('tool_calls'):
                for tool_call in turn['tool_calls']:
                    if 'tool' in tool_call:
                        turn_gt.add(tool_call['tool'])
            
            all_gt_tools.update(turn_gt)
            
            # 计算该轮次的准确性
            correct_tools = turn_tools_set & turn_gt
            turn_correct = (turn_tools_set == turn_gt)
            
            if not turn_correct:
                all_turns_correct = False
            
            # 计算精确率和召回率
            if turn_tools_set:
                precision = len(correct_tools) / len(turn_tools_set)
            else:
                precision = 1.0 if not turn_gt else 0.0
            
            if turn_gt:
                recall = len(correct_tools) / len(turn_gt)
            else:
                recall = 1.0 if not turn_tools_set else 0.0
            
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            
            turn_results.append({
                'turn': turn['turn'],
                'predicted': list(turn_tools_set),
                'ground_truth': list(turn_gt),
                'correct': list(correct_tools),
                'is_correct': turn_correct,
                'precision': precision,
                'recall': recall,
                'f1': f1
            })
    
    # 判断整个对话是否完全正确（所有轮次都正确）
    conversation_correct = all_turns_correct
    
    # 检查是否与样本级别的ground_truth一致（如果有的话）
    sample_level_match = (all_gt_tools == sample_level_gt) if sample_level_gt else True
    
    return {
        'sample_id': sample['id'],
        'dataset': sample['dataset'],
        'image_name': sample['image_name'],
        'ground_truth_tools': list(sample_level_gt),
        'predicted_tools': list(all_predicted_tools),
        'actual_gt_from_turns': list(all_gt_tools),
        'turn_results': turn_results,
        'all_correct': conversation_correct,
        'sample_level_match': sample_level_match,
        'no_tool_needed': len(all_gt_tools) == 0,
        'evaluation_mode': 'turn_level_from_tool_calls'
    }


def calculate_statistics(evaluation_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """计算总体统计数据"""
    total_samples = len(evaluation_results)
    samples_with_tools = sum(1 for r in evaluation_results if not r['no_tool_needed'])
    samples_without_tools = total_samples - samples_with_tools
    
    # 整个对话级别的准确率（所有轮次都正确）
    all_correct_count = sum(1 for r in evaluation_results if r['all_correct'])
    conversation_accuracy = all_correct_count / total_samples if total_samples > 0 else 0
    
    # 样本级别匹配（实际调用的工具集合与样本级ground_truth是否匹配）
    sample_level_match_count = sum(1 for r in evaluation_results if r.get('sample_level_match', True))
    
    # 轮次级别的统计
    total_turns = 0
    correct_turns = 0
    total_precision = 0
    total_recall = 0
    total_f1 = 0
    
    tool_usage_from_turns = defaultdict(lambda: {'correct': 0, 'predicted': 0, 'ground_truth': 0})
    
    for result in evaluation_results:
        # 统计轮次级别的准确率
        for turn_result in result['turn_results']:
            total_turns += 1
            if turn_result['is_correct']:
                correct_turns += 1
            total_precision += turn_result['precision']
            total_recall += turn_result['recall']
            total_f1 += turn_result.get('f1', 0)
            
            # 统计工具使用（基于每轮的ground truth和预测）
            for tool in turn_result['ground_truth']:
                tool_usage_from_turns[tool]['ground_truth'] += 1
            
            for tool in turn_result['predicted']:
                tool_usage_from_turns[tool]['predicted'] += 1
                if tool in turn_result['ground_truth']:
                    tool_usage_from_turns[tool]['correct'] += 1
    
    turn_accuracy = correct_turns / total_turns if total_turns > 0 else 0
    avg_precision = total_precision / total_turns if total_turns > 0 else 0
    avg_recall = total_recall / total_turns if total_turns > 0 else 0
    avg_f1 = total_f1 / total_turns if total_turns > 0 else 0
    
    return {
        'total_samples': total_samples,
        'samples_with_tools': samples_with_tools,
        'samples_without_tools': samples_without_tools,
        'conversation_level': {
            'correct_count': all_correct_count,
            'accuracy': conversation_accuracy,
            'description': '整个对话中所有轮次的工具调用都正确的样本比例'
        },
        'sample_level_match': {
            'match_count': sample_level_match_count,
            'accuracy': sample_level_match_count / total_samples if total_samples > 0 else 0,
            'description': '实际调用的工具集合与样本级ground_truth_tools匹配的样本比例'
        },
        'turn_level': {
            'total_turns': total_turns,
            'correct_turns': correct_turns,
            'accuracy': turn_accuracy,
            'avg_precision': avg_precision,
            'avg_recall': avg_recall,
            'avg_f1': avg_f1,
            'description': '单轮对话中工具调用完全正确的比例（每轮的预测与该轮tool_calls完全匹配）'
        },
        'tool_statistics': dict(tool_usage_from_turns)
    }


def print_detailed_report(evaluation_results: List[Dict[str, Any]], statistics: Dict[str, Any]):
    """打印详细的评估报告"""
    print("=" * 80)
    print("多轮对话工具调用正确率评估报告")
    print("=" * 80)
    print()
    
    # 总体统计
    print("【总体统计】")
    print(f"总样本数: {statistics['total_samples']}")
    print(f"需要调用工具的样本数: {statistics['samples_with_tools']}")
    print(f"不需要调用工具的样本数: {statistics['samples_without_tools']}")
    print()
    
    print("【评估说明】")
    print("Ground Truth来源: 每轮assistant的tool_calls字段")
    print("  - 如果tool_calls为null，该轮ground truth为空（不调用工具）")
    print("  - 如果tool_calls有内容，提取其中的工具作为ground truth")
    print()
    
    # 对话级别准确率
    print("【对话级别准确率】")
    print(f"描述: {statistics['conversation_level']['description']}")
    print(f"完全正确的对话数: {statistics['conversation_level']['correct_count']}/{statistics['total_samples']}")
    print(f"准确率: {statistics['conversation_level']['accuracy']:.2%}")
    print()
    
    # 样本级别匹配
    if 'sample_level_match' in statistics:
        print("【样本级别匹配度】")
        print(f"描述: {statistics['sample_level_match']['description']}")
        print(f"匹配的样本数: {statistics['sample_level_match']['match_count']}/{statistics['total_samples']}")
        print(f"匹配率: {statistics['sample_level_match']['accuracy']:.2%}")
        print()
    
    # 轮次级别准确率
    print("【轮次级别准确率】")
    print(f"描述: {statistics['turn_level']['description']}")
    print(f"完全正确的轮次数: {statistics['turn_level']['correct_turns']}/{statistics['turn_level']['total_turns']}")
    print(f"准确率: {statistics['turn_level']['accuracy']:.2%}")
    print(f"平均精确率 (Precision): {statistics['turn_level']['avg_precision']:.2%}")
    print(f"平均召回率 (Recall): {statistics['turn_level']['avg_recall']:.2%}")
    print(f"平均F1分数: {statistics['turn_level']['avg_f1']:.2%}")
    print()
    
    # 工具使用统计
    if statistics['tool_statistics']:
        print("【工具使用统计】")
        print(f"{'工具名称':<20} {'GT出现次数':<15} {'预测次数':<12} {'正确次数':<12} {'准确率':<10}")
        print("-" * 80)
        for tool, stats in sorted(statistics['tool_statistics'].items()):
            accuracy = stats['correct'] / stats['predicted'] if stats['predicted'] > 0 else 0
            print(f"{tool:<20} {stats['ground_truth']:<15} {stats['predicted']:<12} {stats['correct']:<12} {accuracy:.2%}")
        print()
    
    # 详细的样本结果
    print("【详细样本结果】")
    print("-" * 80)
    for result in evaluation_results:
        status = "✓" if result['all_correct'] else "✗"
        print(f"\n样本 {result['sample_id']} [{result['dataset']}] - {result['image_name']} {status}")
        print(f"  样本级Ground Truth: {result['ground_truth_tools'] if result['ground_truth_tools'] else '无'}")
        print(f"  实际调用的工具: {result.get('actual_gt_from_turns', result['predicted_tools'])}")
        
        if result['turn_results']:
            print(f"  轮次详情:")
            for turn in result['turn_results']:
                turn_status = "✓" if turn['is_correct'] else "✗"
                print(f"    Turn {turn['turn']} {turn_status}: GT={turn['ground_truth']}, 预测={turn['predicted']}, "
                      f"P={turn['precision']:.2f}, R={turn['recall']:.2f}, F1={turn.get('f1', 0):.2f}")
    
    print()
    print("=" * 80)


def save_results(evaluation_results: List[Dict[str, Any]], 
                statistics: Dict[str, Any], 
                output_file: str):
    """保存评估结果到JSON文件"""
    output_data = {
        'statistics': statistics,
        'detailed_results': evaluation_results
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"评估结果已保存到: {output_file}")


def main():
    # 加载数据
    input_file = '/root/rschatgpt/multiturn_qa_samples.json'
    output_file = '/root/rschatgpt/evaluation_results.json'
    
    print(f"正在加载数据: {input_file}")
    data = load_data(input_file)
    print(f"成功加载 {len(data)} 个样本")
    print()
    
    # 评估每个样本
    evaluation_results = []
    for sample in data:
        result = evaluate_turn_accuracy(sample)
        evaluation_results.append(result)
    
    # 计算统计数据
    statistics = calculate_statistics(evaluation_results)
    
    # 打印报告
    print_detailed_report(evaluation_results, statistics)
    
    # 保存结果
    save_results(evaluation_results, statistics, output_file)


if __name__ == '__main__':
    main()

