#!/usr/bin/env python3
"""
快速对比测试：使用小数据集测试 Promptomatix 优化效果
支持断点续测：每个测试结果实时保存，中断后可继续
"""
import json
import sys
import re
import io
import os
import importlib.util
from contextlib import redirect_stdout

# 导入 RSChatGPT
spec = importlib.util.spec_from_file_location("rschatgpt", "RSChatGPT-shell.py")
rschatgpt_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rschatgpt_module)
RSChatGPT = rschatgpt_module.RSChatGPT

# 工具名称到内部名称的映射
TOOL_NAME_MAPPING = {
    'Get Photo Description': 'ImageCaptioning',
    'Scene Classification for Remote Sensing Image': 'SceneClassification',
    'Detect the given object': 'ObjectDetection',
    'Count object': 'ObjectCounting',
    'Edge Detection On Image': 'EdgeDetection',
    'Change Detection On Image Pair': 'ChangeDetection',
    'Cloud Removal On Image': 'CloudRemoval',
    'Super Resolution On Image': 'SuperResolution',
    'Denoising On Image': 'Denoising',
    'Horizontal Detection On Image': 'HorizontalDetection',
    'Rotated Detection On Image': 'RotatedDetection'
}

def remove_ansi_codes(text):
    """移除ANSI颜色代码"""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

def extract_tools_from_text(text):
    """从文本中解析工具调用"""
    if not text:
        return []
    
    text = remove_ansi_codes(text)
    tools_found = []
    
    action_patterns = [
        r'Action:\s*([^\n\r]+)',
        r'Action\s*:\s*([^\n\r]+)',
        r'"action":\s*"([^"]+)"',
    ]
    
    for pattern in action_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            tool_name = match.strip().strip('"\'`').strip()
            if 'Observation' in tool_name:
                tool_name = tool_name.split('Observation')[0].strip()
            
            if tool_name in TOOL_NAME_MAPPING:
                mapped_tool = TOOL_NAME_MAPPING[tool_name]
                if mapped_tool not in tools_found:
                    tools_found.append(mapped_tool)
    
    for tool_display_name, internal_name in TOOL_NAME_MAPPING.items():
        if f"Action: {tool_display_name}" in text or f"Action:{tool_display_name}" in text:
            if internal_name not in tools_found:
                tools_found.append(internal_name)
    
    return tools_found

def extract_tools_from_response(res, tool_mapping):
    """从Agent响应中提取工具调用"""
    actual_tools_called = []
    
    if 'intermediate_steps' in res and res['intermediate_steps']:
        for step in res['intermediate_steps']:
            if len(step) >= 1:
                agent_action = step[0]
                tool_name = str(agent_action.tool) if hasattr(agent_action, 'tool') else str(agent_action)
                if tool_name in tool_mapping:
                    mapped_tool = tool_mapping[tool_name]
                    if mapped_tool not in actual_tools_called:
                        actual_tools_called.append(mapped_tool)
                
                if hasattr(agent_action, 'log') and agent_action.log:
                    text_tools = extract_tools_from_text(agent_action.log)
                    for tool in text_tools:
                        if tool not in actual_tools_called:
                            actual_tools_called.append(tool)
    
    if '_captured_stdout' in res and res['_captured_stdout']:
        text_tools = extract_tools_from_text(res['_captured_stdout'])
        for tool in text_tools:
            if tool not in actual_tools_called:
                actual_tools_called.append(tool)
    
    if 'output' in res and res['output']:
        text_tools = extract_tools_from_text(res['output'])
        for tool in text_tools:
            if tool not in actual_tools_called:
                actual_tools_called.append(tool)
    
    if isinstance(res, dict) and res.get('log'):
        text_tools = extract_tools_from_text(res['log'])
        for tool in text_tools:
            if tool not in actual_tools_called:
                actual_tools_called.append(tool)
    
    try:
        res_str = str(res)
        text_tools = extract_tools_from_text(res_str)
        for tool in text_tools:
            if tool not in actual_tools_called:
                actual_tools_called.append(tool)
    except:
        pass
    
    return actual_tools_called


def load_checkpoint(checkpoint_file):
    """加载检查点文件"""
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def save_checkpoint(checkpoint_file, data):
    """保存检查点文件"""
    with open(checkpoint_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def run_quick_test(enable_optimization=False, sample_limit=5, test_file='multiturn_qa_samples.json', checkpoint_file=None, gpt_name="gpt-3.5-turbo"):
    """
    快速测试（支持断点续测）
    
    Args:
        enable_optimization: 是否启用优化
        sample_limit: 测试样本数量限制
        test_file: 测试数据文件
        checkpoint_file: 检查点文件路径（用于断点续测）
        gpt_name: 使用的模型名称
    """
    # 加载测试样本
    with open(test_file, 'r', encoding='utf-8') as f:
        samples = json.load(f)
    
    samples = samples[:sample_limit]
    is_singleturn = 'turns' not in samples[0] if samples else False
    
    # 加载检查点（如果存在）
    checkpoint = load_checkpoint(checkpoint_file) if checkpoint_file else None
    start_idx = 0
    results = []
    tool_stats = {}
    
    if checkpoint:
        start_idx = checkpoint.get('last_completed_idx', -1) + 1
        results = checkpoint.get('results', [])
        tool_stats = checkpoint.get('tool_stats', {})
        print(f"✓ 从检查点恢复，从第 {start_idx + 1} 个样本继续...")
    
    # 初始化模型
    load_dict = {
        'ImageCaptioning': 'cuda:0',
        'SceneClassification': 'cuda:0',
        'ObjectDetection': 'cuda:0',
        'ObjectCounting': 'cuda:0',
        'EdgeDetection': 'cpu',
        'ChangeDetection': 'cuda:0',
        'CloudRemoval': 'cpu',
        'SuperResolution': 'cpu',
        'Denoising': 'cpu',
        'HorizontalDetection': 'cpu',
        'RotatedDetection': 'cpu'
    }
    
    openai_key = "sk-SPp8PGpzob5k1pcSI2cRORgdeEDoB3QsndvRzIYnUVeKt2jd"
    proxy_url = "https://api.chatanywhere.tech"
    
    mode = "优化模式" if enable_optimization else "基线模式"
    
    print(f"\n{'='*60}")
    print(f"开始测试 - {mode} - 模型: {gpt_name}")
    print(f"测试样本数: {len(samples)} (从第 {start_idx + 1} 个开始)")
    print(f"{'='*60}\n")
    
    bot = RSChatGPT(
        gpt_name=gpt_name,
        load_dict=load_dict,
        openai_key=openai_key,
        proxy_url=proxy_url,
        enable_query_optimization=enable_optimization
    )
    bot.initialize()
    
    tool_mapping = TOOL_NAME_MAPPING
    
    # 处理单轮数据
    if is_singleturn:
        for sample_idx in range(start_idx, len(samples)):
            sample = samples[sample_idx]
            sample_id = sample['id']
            query = sample['query']
            expected_tool = sample['tool']
            image = sample.get('image', '')
            
            print(f"\n[样本 {sample_idx + 1}/{len(samples)}] ID={sample_id}")
            print(f"  Query: {query[:50]}...")
            
            # 重新初始化
            bot.initialize()
            
            result = {
                'sample_id': sample_id,
                'sample_idx': sample_idx,
                'query': query,
                'expected_tool': expected_tool,
                'actual_tools': [],
                'is_correct': False,
                'error': None
            }
            
            try:
                # 处理图片
                if image:
                    if isinstance(image, list):
                        for img_path in image:
                            description = bot.models['ImageCaptioning'].inference(img_path)
                            Human_prompt = f'Provide a remote sensing image named {img_path}. The description is: {description}. This information helps you to understand this image, but you should use tools to finish following tasks, rather than directly imagine from my description. If you understand, say "Received".'
                            AI_prompt = "Received."
                            bot.memory.chat_memory.add_user_message(Human_prompt)
                            bot.memory.chat_memory.add_ai_message(AI_prompt)
                        image_str = ','.join(image)
                    else:
                        description = bot.models['ImageCaptioning'].inference(image)
                        Human_prompt = f'Provide a remote sensing image named {image}. The description is: {description}. This information helps you to understand this image, but you should use tools to finish following tasks, rather than directly imagine from my description. If you understand, say "Received".'
                        AI_prompt = "Received."
                        bot.memory.chat_memory.add_user_message(Human_prompt)
                        bot.memory.chat_memory.add_ai_message(AI_prompt)
                        image_str = image
                
                agent_input = f"{query} {image_str}" if image else query
                
                if hasattr(bot, 'query_optimizer') and bot.query_optimizer and bot.query_optimizer.enabled:
                    agent_input = bot.query_optimizer.optimize_if_ambiguous(agent_input)
                
                # 捕获stdout
                captured_output = io.StringIO()
                import sys as _sys
                old_stdout = _sys.stdout
                
                class Tee:
                    def __init__(self, *files):
                        self.files = files
                    def write(self, data):
                        for f in self.files:
                            f.write(data)
                    def flush(self):
                        for f in self.files:
                            f.flush()
                
                _sys.stdout = Tee(old_stdout, captured_output)
                try:
                    res = bot.agent({"input": agent_input})
                finally:
                    _sys.stdout = old_stdout
                
                res['_captured_stdout'] = captured_output.getvalue()
                
                actual_tools_called = extract_tools_from_response(res, tool_mapping)
                is_correct = (expected_tool in actual_tools_called) if actual_tools_called else False
                
                result['actual_tools'] = actual_tools_called
                result['is_correct'] = is_correct
                
                # 更新工具统计
                if expected_tool not in tool_stats:
                    tool_stats[expected_tool] = {'total': 0, 'correct': 0}
                tool_stats[expected_tool]['total'] += 1
                if is_correct:
                    tool_stats[expected_tool]['correct'] += 1
                
                if is_correct:
                    print(f"  ✓ 正确 - 调用: {actual_tools_called}")
                else:
                    print(f"  ✗ 错误 - 实际: {actual_tools_called}, 期望: {expected_tool}")
                    
            except Exception as e:
                result['error'] = str(e)
                print(f"  ✗ 异常: {e}")
                
                # 更新工具统计（异常也算错误）
                if expected_tool not in tool_stats:
                    tool_stats[expected_tool] = {'total': 0, 'correct': 0}
                tool_stats[expected_tool]['total'] += 1
            
            # 保存结果
            results.append(result)
            
            # 实时保存检查点
            if checkpoint_file:
                save_checkpoint(checkpoint_file, {
                    'mode': mode,
                    'enable_optimization': enable_optimization,
                    'test_file': test_file,
                    'sample_limit': sample_limit,
                    'last_completed_idx': sample_idx,
                    'results': results,
                    'tool_stats': tool_stats,
                    'completed': sample_idx == len(samples) - 1
                })
        
        # 计算统计
        total_turns = len(results)
        correct_turns = sum(1 for r in results if r['is_correct'])
        accuracy = (correct_turns / total_turns * 100) if total_turns > 0 else 0
        
        print(f"\n{'='*60}")
        print(f"测试完成 - {mode}")
        print(f"{'='*60}")
        print(f"总样本: {total_turns}")
        print(f"正确: {correct_turns}")
        print(f"错误: {total_turns - correct_turns}")
        print(f"准确率: {accuracy:.2f}%")
        
        print(f"\n各工具准确率:")
        print(f"{'工具名称':<25} {'正确/总数':<12} {'准确率':<10}")
        print("-" * 50)
        for tool_name in sorted(tool_stats.keys()):
            stats = tool_stats[tool_name]
            tool_acc = (stats['correct'] / stats['total'] * 100) if stats['total'] > 0 else 0
            print(f"{tool_name:<25} {stats['correct']}/{stats['total']:<10} {tool_acc:.2f}%")
        
        if enable_optimization and hasattr(bot, 'query_optimizer') and bot.query_optimizer:
            opt_stats = bot.query_optimizer.get_stats()
            print(f"\n优化统计:")
            print(f"  优化次数: {opt_stats['optimization_count']}")
            print(f"  跳过次数: {opt_stats['skip_count']}")
            print(f"  缓存大小: {opt_stats['cache_size']}")
        
        print(f"{'='*60}\n")
        
        return accuracy, tool_stats, results
    
    # 处理多轮数据
    for sample_idx in range(start_idx, len(samples)):
        sample = samples[sample_idx]
        sample_id = sample['id']
        print(f"\n[样本 {sample_idx + 1}/{len(samples)}] ID={sample_id}")
        
        bot.initialize()
        last_turn_uploaded_image = False
        sample_results = []
        
        for turn in sample['turns']:
            turn_num = turn['turn']
            role = turn['role']
            content = turn['content']
            images = turn.get('images', [])
            tool_calls = turn.get('tool_calls', None)
            
            if role == 'user':
                print(f"  Turn {turn_num} (User): {content[:50]}...")
                
                if images:
                    last_turn_uploaded_image = True
                    for img_path in images:
                        try:
                            description = bot.models['ImageCaptioning'].inference(img_path)
                            Human_prompt = f'Provide a remote sensing image named {img_path}. The description is: {description}. This information helps you to understand this image, but you should use tools to finish following tasks, rather than directly imagine from my description. If you understand, say "Received".'
                            AI_prompt = "Received."
                            bot.memory.chat_memory.add_user_message(Human_prompt)
                            bot.memory.chat_memory.add_ai_message(AI_prompt)
                        except Exception as e:
                            print(f"    图片处理失败: {e}")
                else:
                    last_turn_uploaded_image = False
                
                try:
                    agent_input = f"{content} {','.join(images)}" if images else content
                    
                    if hasattr(bot, 'query_optimizer') and bot.query_optimizer and bot.query_optimizer.enabled:
                        agent_input = bot.query_optimizer.optimize_if_ambiguous(agent_input)
                    
                    captured_output = io.StringIO()
                    import sys as _sys
                    old_stdout = _sys.stdout
                    
                    class Tee:
                        def __init__(self, *files):
                            self.files = files
                        def write(self, data):
                            for f in self.files:
                                f.write(data)
                        def flush(self):
                            for f in self.files:
                                f.flush()
                    
                    _sys.stdout = Tee(old_stdout, captured_output)
                    try:
                        res = bot.agent({"input": agent_input})
                    finally:
                        _sys.stdout = old_stdout
                    
                    res['_captured_stdout'] = captured_output.getvalue()
                    
                except Exception as e:
                    print(f"    Agent执行失败: {e}")
                    res = {'intermediate_steps': [], '_captured_stdout': ''}
            
            elif role == 'assistant':
                actual_tools_called = extract_tools_from_response(res, tool_mapping)
                
                if last_turn_uploaded_image and actual_tools_called == ['ImageCaptioning']:
                    actual_tools_called = []
                
                gt_tools = []
                if tool_calls:
                    for tc in tool_calls:
                        if 'tool' in tc:
                            tool = tc['tool']
                            if tool not in gt_tools:
                                gt_tools.append(tool)
                
                if gt_tools or actual_tools_called:
                    is_correct = all(tool in actual_tools_called for tool in gt_tools) if gt_tools else (not actual_tools_called)
                    
                    for expected_tool in gt_tools:
                        if expected_tool not in tool_stats:
                            tool_stats[expected_tool] = {'total': 0, 'correct': 0}
                        tool_stats[expected_tool]['total'] += 1
                        if expected_tool in actual_tools_called:
                            tool_stats[expected_tool]['correct'] += 1
                    
                    sample_results.append({
                        'turn': turn_num,
                        'expected_tools': gt_tools,
                        'actual_tools': actual_tools_called,
                        'is_correct': is_correct
                    })
                    
                    if is_correct:
                        print(f"  Turn {turn_num} (Assistant): ✓ 正确")
                        if actual_tools_called != gt_tools:
                            print(f"    实际: {actual_tools_called} (包含期望: {gt_tools})")
                    else:
                        print(f"  Turn {turn_num} (Assistant): ✗ 错误")
                        print(f"    实际: {actual_tools_called}")
                        print(f"    期望: {gt_tools}")
        
        results.append({
            'sample_id': sample_id,
            'sample_idx': sample_idx,
            'turns': sample_results
        })
        
        # 实时保存检查点
        if checkpoint_file:
            save_checkpoint(checkpoint_file, {
                'mode': mode,
                'enable_optimization': enable_optimization,
                'test_file': test_file,
                'sample_limit': sample_limit,
                'last_completed_idx': sample_idx,
                'results': results,
                'tool_stats': tool_stats,
                'completed': sample_idx == len(samples) - 1
            })
    
    # 计算统计
    total_turns = sum(len(r.get('turns', [])) for r in results)
    correct_turns = sum(1 for r in results for t in r.get('turns', []) if t.get('is_correct', False))
    accuracy = (correct_turns / total_turns * 100) if total_turns > 0 else 0
    
    print(f"\n{'='*60}")
    print(f"测试完成 - {mode}")
    print(f"{'='*60}")
    print(f"总轮次: {total_turns}")
    print(f"正确: {correct_turns}")
    print(f"错误: {total_turns - correct_turns}")
    print(f"准确率: {accuracy:.2f}%")
    
    if tool_stats:
        print(f"\n各工具准确率:")
        print(f"{'工具名称':<25} {'正确/总数':<12} {'准确率':<10}")
        print("-" * 50)
        for tool_name in sorted(tool_stats.keys()):
            stats = tool_stats[tool_name]
            tool_acc = (stats['correct'] / stats['total'] * 100) if stats['total'] > 0 else 0
            print(f"{tool_name:<25} {stats['correct']}/{stats['total']:<10} {tool_acc:.2f}%")
    
    if enable_optimization and hasattr(bot, 'query_optimizer') and bot.query_optimizer:
        opt_stats = bot.query_optimizer.get_stats()
        print(f"\n优化统计:")
        print(f"  优化次数: {opt_stats['optimization_count']}")
        print(f"  跳过次数: {opt_stats['skip_count']}")
        print(f"  缓存大小: {opt_stats['cache_size']}")
    
    print(f"{'='*60}\n")
    
    return accuracy, tool_stats, results


def main():
    """运行对比测试"""
    import sys
    
    sample_limit = 5
    test_file = 'multiturn_qa_samples.json'
    gpt_name = 'gpt-3.5-turbo'
    
    if len(sys.argv) > 1:
        try:
            sample_limit = int(sys.argv[1])
        except:
            pass
    
    if len(sys.argv) > 2:
        test_file = sys.argv[2]
    
    if len(sys.argv) > 3:
        gpt_name = sys.argv[3]
    
    print("\n" + "="*60)
    print("快速对比测试（支持断点续测）")
    print(f"测试文件: {test_file}")
    print(f"测试样本数: {sample_limit}")
    print(f"模型名称: {gpt_name}")
    print("="*60)
    
    test_name = os.path.splitext(os.path.basename(test_file))[0]
    # 模型名称简化（用于文件名）
    model_short = gpt_name.replace('/', '_').replace('-', '_')
    
    # 日志目录
    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True)
    
    # 检查点文件（用于断点续测）- 包含模型名称
    checkpoint_baseline = os.path.join(log_dir, f'checkpoint_{test_name}_{sample_limit}_{model_short}_baseline.json')
    checkpoint_optimized = os.path.join(log_dir, f'checkpoint_{test_name}_{sample_limit}_{model_short}_optimized.json')
    
    # 检查是否有未完成的测试
    baseline_checkpoint = load_checkpoint(checkpoint_baseline)
    optimized_checkpoint = load_checkpoint(checkpoint_optimized)
    
    # 测试基线
    if baseline_checkpoint and baseline_checkpoint.get('completed'):
        print(f"\n[1/2] 基线测试已完成，跳过...")
        accuracy_baseline = (sum(1 for r in baseline_checkpoint['results'] if r.get('is_correct', False)) / 
                            len(baseline_checkpoint['results']) * 100) if baseline_checkpoint['results'] else 0
        tool_stats_baseline = baseline_checkpoint['tool_stats']
    else:
        print("\n[1/2] 测试基线（无优化）...")
        accuracy_baseline, tool_stats_baseline, _ = run_quick_test(
            enable_optimization=False, 
            sample_limit=sample_limit, 
            test_file=test_file, 
            checkpoint_file=checkpoint_baseline,
            gpt_name=gpt_name
        )
    
    # 测试优化版本
    if optimized_checkpoint and optimized_checkpoint.get('completed'):
        print(f"\n[2/2] 优化测试已完成，跳过...")
        accuracy_optimized = (sum(1 for r in optimized_checkpoint['results'] if r.get('is_correct', False)) / 
                             len(optimized_checkpoint['results']) * 100) if optimized_checkpoint['results'] else 0
        tool_stats_optimized = optimized_checkpoint['tool_stats']
    else:
        print("\n[2/2] 测试优化版本...")
        accuracy_optimized, tool_stats_optimized, _ = run_quick_test(
            enable_optimization=True, 
            sample_limit=sample_limit, 
            test_file=test_file, 
            checkpoint_file=checkpoint_optimized,
            gpt_name=gpt_name
        )
    
    # 输出对比
    improvement = accuracy_optimized - accuracy_baseline
    
    print("\n" + "="*60)
    print("对比结果")
    print("="*60)
    print(f"基线准确率:   {accuracy_baseline:.2f}%")
    print(f"优化准确率:   {accuracy_optimized:.2f}%")
    print(f"准确率变化:   {improvement:+.2f}%")
    
    if improvement > 0:
        print(f"结果: ✓ 提升了 {improvement:.2f}%")
    elif improvement < 0:
        print(f"结果: ✗ 下降了 {abs(improvement):.2f}%")
    else:
        print(f"结果: = 持平")
    
    # 打印各工具对比
    all_tools = set(tool_stats_baseline.keys()) | set(tool_stats_optimized.keys())
    if all_tools:
        print(f"\n各工具准确率对比:")
        print(f"{'工具名称':<25} {'基线':<15} {'优化':<15} {'变化':<10}")
        print("-" * 70)
        for tool_name in sorted(all_tools):
            baseline_stats = tool_stats_baseline.get(tool_name, {'total': 0, 'correct': 0})
            optimized_stats = tool_stats_optimized.get(tool_name, {'total': 0, 'correct': 0})
            
            baseline_acc = (baseline_stats['correct'] / baseline_stats['total'] * 100) if baseline_stats['total'] > 0 else 0
            optimized_acc = (optimized_stats['correct'] / optimized_stats['total'] * 100) if optimized_stats['total'] > 0 else 0
            change = optimized_acc - baseline_acc
            
            baseline_str = f"{baseline_stats['correct']}/{baseline_stats['total']} ({baseline_acc:.1f}%)"
            optimized_str = f"{optimized_stats['correct']}/{optimized_stats['total']} ({optimized_acc:.1f}%)"
            change_str = f"{change:+.1f}%"
            
            print(f"{tool_name:<25} {baseline_str:<15} {optimized_str:<15} {change_str:<10}")
    
    print(f"\n检查点文件:")
    print(f"  基线测试: {checkpoint_baseline}")
    print(f"  优化测试: {checkpoint_optimized}")
    print("="*60 + "\n")
    
    # 保存最终汇总到检查点文件
    summary = {
        'test_file': test_file,
        'sample_limit': sample_limit,
        'gpt_name': gpt_name,
        'baseline_accuracy': accuracy_baseline,
        'optimized_accuracy': accuracy_optimized,
        'improvement': improvement,
        'tool_comparison': {}
    }
    
    for tool_name in all_tools:
        baseline_stats = tool_stats_baseline.get(tool_name, {'total': 0, 'correct': 0})
        optimized_stats = tool_stats_optimized.get(tool_name, {'total': 0, 'correct': 0})
        summary['tool_comparison'][tool_name] = {
            'baseline': baseline_stats,
            'optimized': optimized_stats
        }
    
    # 更新检查点文件添加汇总
    if os.path.exists(checkpoint_baseline):
        baseline_data = load_checkpoint(checkpoint_baseline)
        baseline_data['summary'] = summary
        save_checkpoint(checkpoint_baseline, baseline_data)
    
    if os.path.exists(checkpoint_optimized):
        optimized_data = load_checkpoint(checkpoint_optimized)
        optimized_data['summary'] = summary
        save_checkpoint(checkpoint_optimized, optimized_data)
    
    print(f"测试完成！结果已保存到检查点文件。\n")


if __name__ == '__main__':
    main()
