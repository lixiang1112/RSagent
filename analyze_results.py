#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析测试结果，统计每个工具类别的正确率
"""

import csv
from collections import defaultdict

def analyze_results(csv_file='test_results.csv'):
    """分析CSV文件，统计每个工具的正确率"""
    
    # 统计数据
    tool_stats = defaultdict(lambda: {'total': 0, 'correct': 0})
    
    # 读取CSV文件
    with open(csv_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            ground_truth = row['Ground Truth Tool']
            is_correct = row['是否正确'] == '✓'
            
            tool_stats[ground_truth]['total'] += 1
            if is_correct:
                tool_stats[ground_truth]['correct'] += 1
    
    # 打印结果
    print("="*80)
    print("每个工具类别的正确率统计")
    print("="*80)
    print(f"{'工具名称':<30} {'总数':>8} {'正确':>8} {'错误':>8} {'正确率':>10}")
    print("-"*80)
    
    # 按工具名称排序
    total_all = 0
    correct_all = 0
    
    for tool in sorted(tool_stats.keys()):
        stats = tool_stats[tool]
        total = stats['total']
        correct = stats['correct']
        incorrect = total - correct
        accuracy = (correct / total * 100) if total > 0 else 0
        
        print(f"{tool:<30} {total:>8} {correct:>8} {incorrect:>8} {accuracy:>9.2f}%")
        
        total_all += total
        correct_all += correct
    
    print("-"*80)
    accuracy_all = (correct_all / total_all * 100) if total_all > 0 else 0
    print(f"{'总计':<30} {total_all:>8} {correct_all:>8} {total_all-correct_all:>8} {accuracy_all:>9.2f}%")
    print("="*80)
    
    return tool_stats

if __name__ == '__main__':
    analyze_results()

