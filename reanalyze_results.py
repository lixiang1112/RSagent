#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重新分析测试日志，应用新的过滤规则
"""

import re
import json

# 读取日志文件
with open('multiturn_test.log', 'r', encoding='utf-8') as f:
    log_content = f.read()

# 解析每个样本
samples = log_content.split('='*100)[1:-1]  # 跳过开头和结尾

total_turns = 0
correct_turns = 0
errors = []

for sample in samples:
    if 'ID:' not in sample:
        continue
    
    # 提取样本信息
    sample_match = re.search(r'ID: (\d+)', sample)
    if not sample_match:
        continue
    sample_id = sample_match.group(1)
    
    # 查找所有assistant判断
    turns = re.split(r'--- Turn \d+ \(Assistant Ground Truth\) ---', sample)[1:]
    
    for turn_text in turns:
        # 提取turn number
        turn_match = re.search(r'Turn (\d+)', turn_text)
        if not turn_match:
            continue
        turn_num = turn_match.group(1)
        
        # 提取Ground Truth
        gt_match = re.search(r'GT Tool Calls: (.+)', turn_text)
        if not gt_match:
            continue
        gt_text = gt_match.group(1)
        
        # 解析GT
        gt_tools = []
        if gt_text != '无' and gt_text != 'None':
            try:
                gt_data = eval(gt_text)
                if isinstance(gt_data, list):
                    for item in gt_data:
                        if isinstance(item, dict) and 'tool' in item:
                            gt_tools.append(item['tool'])
            except:
                pass
        
        # 提取实际调用的工具
        actual_match = re.search(r'✗ 实际调用工具: (.+)', turn_text)
        if not actual_match:
            actual_match = re.search(r'✓ 实际调用工具: (.+)', turn_text)
        
        if not actual_match:
            continue
            
        actual_text = actual_match.group(1)
        actual_tools = []
        if actual_text != '无':
            try:
                actual_tools = eval(actual_text)
            except:
                pass
        
        # 判断是否正确
        total_turns += 1
        is_correct = (set(actual_tools) == set(gt_tools))
        
        if is_correct:
            correct_turns += 1
        else:
            errors.append({
                'sample_id': sample_id,
                'turn': turn_num,
                'gt': gt_tools,
                'actual': actual_tools
            })

print(f"="*80)
print(f"重新分析测试结果")
print(f"="*80)
print(f"总轮次数: {total_turns}")
print(f"正确轮次数: {correct_turns}")
print(f"错误轮次数: {total_turns - correct_turns}")
print(f"准确率: {(correct_turns/total_turns*100) if total_turns > 0 else 0:.2f}%")
print(f"\n错误详情:")
print(f"-"*80)
for error in errors:
    print(f"样本 {error['sample_id']} Turn {error['turn']}")
    print(f"  GT: {error['gt']}")
    print(f"  实际: {error['actual']}")
print(f"="*80)

